# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_automatics_port.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Implements the class 'Port' for Automatics.
"""
# --------------------- LICENSE -----------------------------------------------
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>
# or write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# --------------------- DOXYGEN -----------------------------------------------
##
# @file as_automatics_port.py
# @ingroup automatics_intrep
# @author Philip Manke
# @brief Implements the class 'Port' for Automatics.
# -----------------------------------------------------------------------------

import copy

from collections import namedtuple, deque
from typing import Sequence

from as_automatics_exceptions import AsAssignError
from as_automatics_helpers import get_printable_datatype

import as_automatics_logging as as_log

LOG = as_log.get_log()


## @ingroup automatics_intrep
class Port:
    """! @brief Class representing a VHDL Port.
    Description of a single port (^= signal interfacing with a hardware
    module within an ASTERICS processing chain), along with some
    meta-information for Automatics (the processing chain generator)"""

    ## @ingroup automatics_intrep
    class DataWidth(namedtuple("DataWidth", "a sep b")):
        """! @brief Describes a VHDL range: (a [down]to b) as a namedtuple (a, sep, b).
        Non-vector types (e.g. std_logic) are described by (1, None, None)."""

        def __str__(self):
            if self.sep is not None:
                return "({} {} {})".format(*self)
            else:
                return str(self.a)

        def is_resolved(self):
            """! @brief Quick check to see if the data width is resolved.
            IE: minimum complexity, no generic names in expressions."""
            if self.sep is None:
                return True
            if isinstance(self.a, int) and isinstance(self.b, int):
                return True
            return False

        def get_bit_width(self):
            """! @brief Returns an integer value representing this data widths bit width.
            Only works on fully resolved data widths, else returns None."""
            if self.is_resolved():
                if self.sep is None:
                    return 1
                elif self.sep == "to":
                    return self.b - self.a + 1
                elif self.sep == "downto":
                    return self.a - self.b + 1
            return None

        def __add__(self, other):
            if not type(other) is type(self):
                raise TypeError(
                    "DataWidth cannot be added to type '{}'".format(type(other))
                )
            if self.sep is None or other.sep is None:
                raise ValueError(
                    "DataWidths of non-vector data types cannot be added!"
                )
            if self.sep != other.sep:
                raise ValueError(
                    "Cannot add DataWidths of differing endianess!"
                )
            bit_width = self.get_bit_width() + other.get_bit_width() - 1
            if self.sep == "downto":
                return self.__class__(bit_width, "downto", 0)
            return self.__class__(0, "to", bit_width)

        def __eq__(self, other):
            if not type(other) is type(self):
                raise TypeError(
                    "DataWidth cannot be compared with type '{}'".format(
                        type(other)
                    )
                )
            if self.sep is None and other.sep is None:
                return True
            if self.sep != other.sep:
                return False
            if self.a != other.a or self.b != other.b:
                return False
            return True

        def __ne__(self, other):
            return not self == other

        def __gt__(self, other):
            if not type(other) is type(self):
                raise TypeError(
                    "DataWidth cannot be compared with type '{}'".format(
                        type(other)
                    )
                )
            return self.get_bit_width() > other.get_bit_width()

        def __ge__(self, other):
            if self == other:
                return True
            else:
                return self > other

        def __lt__(self, other):
            return not self > other

        def __le__(self, other):
            return not self >= other

    # __ END class DataWidth __

    Rule = namedtuple("Rule", "condition action")
    WindowReference = namedtuple("WindowReference", "x y intername")

    directions = ("in", "out", "inout")
    port_types = (
        "external",
        "single",
        "interface",
        "signal",
        "glue_signal",
    )
    necessity_types = ("mandatory", "optional")
    rule_conditions = (
        "any_missing",
        "any_present",
        "both_missing",
        "both_present",
        "sink_present",
        "sink_missing",
        "source_present",
        "source_missing",
        "single_port",
        "external_port",
        "type_signal",
    )
    rule_actions = (
        "connect",
        "make_external",
        "error",
        "warning",
        "note",
        "set_value(<value>)",
        "bundle_and",
        "bundle_or",
        "fallback_port(<port name>)",
        "none",
        "forceconnect",
        "fallback_signal(<signal_name>)",
    )

    rule_condition_eval = {
        "any_missing": lambda src, sink: src is None or sink is None,
        "any_present": lambda src, sink: not (src is None and sink is None),
        "both_missing": lambda src, sink: src is None and sink is None,
        "both_present": lambda src, sink: not (src is None or sink is None),
        "sink_present": lambda src, sink: sink is not None,
        "sink_missing": lambda src, sink: sink is None,
        "source_present": lambda src, sink: src is not None,
        "source_missing": lambda src, sink: src is None,
        "single_port": lambda src, sink: src.port_type == "single",
        "external_port": lambda src, sink: src.port_type == "external",
        "type_signal": lambda src, sink: src.port_type == "signal",
    }

    # Default rules applied to all ports initially
    default_rules = [
        Rule("both_present", "connect"),
        Rule("sink_missing", "note"),
    ]

    def __init__(
        self,
        name: str = "",
        code_name: str = "",
        direction: str = "in",
        port_type: str = "single",
        data_type: str = "std_logic",
        optional: bool = False,
        data_width=DataWidth(1, None, None),
    ):

        # This ruleset describes how this port is going to be connected
        self.ruleset = deque(self.default_rules)

        # Actual data type of this VHDL port (eg: bit, std_logic, integer, ...)
        self.data_type = data_type
        self.optional = optional  # Is this port optional (for interfaces)
        self.data_width = data_width  # VHDL data vector width
        self.parent = None
        self.name = name  # "Base" name of this port
        self.code_name = code_name  # Name in VHDL of this port

        self.direction = "in"  # Data direction
        self.port_type = "interface"
        self.set_direction(direction)
        self.set_port_type(port_type)
        self.connected = False
        self.glue_signal = None
        self.in_entity = True

        self.incoming = None
        self.outgoing = []
        self.generics = []

        self.window_config = None

        if not self.code_name:
            self.code_name = self.name
        if not self.name:
            self.name = self.code_name

    ## @ingroup automatics_cds
    def connect(self, other):
        """! @brief Connect this Port to another Port, Interface, AsModule."""
        if self.port_type == "interface":
            self.parent.parent.chain.connect(self, other)
        else:
            self.parent.chain.connect(self, other)

    ## @ingroup automatics_connection
    def clear_connections(self):
        self.incoming = None
        self.outgoing.clear()
        self.glue_signal = None

    def add_generic(self, gen) -> bool:
        """! @brief Associate a Generic with this Port.
        This should happen automatically. Automatics will extract Generic names
        from the port's data width declaration.
        @param gen: Generic object reference
        @return  True on success, else False (if Generic already associated)"""
        if gen not in self.generics:
            self.generics.append(gen)
            return True
        return False

    def remove_generic(self, gen) -> bool:
        """! @brief Remove a Generic association from this port.
        @param gen: Generic to remove
        @return  True on success, else False (if Generic isn't associated)"""
        try:
            self.generics.remove(gen)
        except ValueError:
            LOG.warning(
                (
                    "Could not remove Generic reference for '%s' from "
                    "port '%s', Generic not assigned to this port!"
                ),
                gen.code_name,
                self.code_name,
            )
            return False
        return True

    def set_port_type(self, port_type: str):
        """! @brief Define what type of port this is."""
        if port_type in Port.port_types:
            self.port_type = port_type
        else:
            LOG.warning(
                "Port type '%s' of port '%s' is not valid!",
                port_type,
                self.code_name,
            )

    def set_direction(self, direction: str):
        """! @brief Set the direction of the dataflow for this port.
        Valid values are in 'port.directions'
        (normally 'in', 'out', 'inout')"""
        if direction in Port.directions:
            self.direction = direction
        else:
            LOG.warning("Direction '%s' is not valid!", direction)

    def set_value(self, value: str) -> bool:
        """! @brief Set a static value for this port.
        Uses the port rule system."""
        return self.add_rule(
            "any_present", "set_value({})".format(value), priority=True
        )

    def set_glue_signal(self, signal):
        """! @brief Set this port's glue signal"""
        self.glue_signal = signal

    def get_direction_normalized(self) -> str:
        """! @brief Get the 'normalized' data direction of this port.
        This is the direction defined in VHDL source code,
        not modified by the interface direction."""
        direction = self.direction
        if self.port_type == "interface":
            if self.parent.direction == "out":
                direction = "out" if self.direction == "in" else "in"
        return direction

    def __str__(self) -> str:
        """! @brief Print the configuration of this port instance."""
        return (
            "{name}('{code}'): {necessity}, {direction} as "
            "{data_type}, type: {port_type}"
        ).format(
            name=self.name,
            necessity=("optional" if self.optional else "mandatory"),
            direction=self.direction,
            data_type=get_printable_datatype(self),
            port_type=self.port_type,
            code=self.code_name,
        )

    def __repr__(self) -> str:
        return self.code_name

    def set_window_reference(self, tags: iter):
        """! @brief Set the reference data required for ports of the 2D Window Pipeline
        interface."""
        self.window_config = self.WindowReference(*tags)

    @classmethod
    def list_possible_rules(cls):
        """! @brief List all possible rule conditions and rule effects."""
        print("List of all possible rule conditions: ")
        print(cls.rule_conditions)
        print("List of all possible rule effects:")
        print(cls.rule_actions)

    ## @ingroup automatics_connection
    def set_connected(self, value: bool = True):
        """! @brief Set this ports 'connected' attribute.
        @param value: Boolean value to set [Default: True]"""
        self.connected = value

    ## @ingroup automatics_connection
    def add_rule(
        self, rule_condition: str, rule_action: str, priority: bool = True
    ) -> bool:
        """! @brief Add a rule to this port.
        Rules define how Automatics will handle this
        port when building the processing chain.
        @param rule_condition: Define when this rule will be applied.
        @param rule_action: Define what should happen when this rule is applied.
        @param priority: Boolean value: Should this rule be the first to be applied?
                             Default value 'True'.
        @return  True on success, else False
        """
        if priority:
            position = 0
        else:
            position = len(self.ruleset) - 1

        rule = self.Rule(rule_condition, rule_action)
        if self.__check_rule__(rule):
            self.ruleset.insert(position, rule)
            return True
        return False

    ## @ingroup automatics_connection
    def __check_rule__(self, rule: namedtuple) -> bool:
        """! @brief Make sure the passed rule has a valid condition and action."""
        if self.port_type == "interface":
            mod = self.parent
            mod = getattr(mod, "parent", None)
        else:
            mod = self.parent

        modname = getattr(mod, "name", "Unknown")

        if rule.condition not in self.rule_conditions:
            LOG.error(
                (
                    "Tried to set an invalid rule condition '%s' "
                    "to port '%s' of module '%s'."
                ),
                rule.condition,
                self.code_name,
                modname,
            )
            return False
        if (rule.action not in self.rule_actions) and not (
            any(
                act in rule.action
                for act in ("set_value", "fallback_port", "fallback_signal")
            )
        ):
            LOG.error(
                (
                    "Tried to set an invalid rule action '%s' ",
                    "to port '%s' of module '%s'.",
                ),
                rule.action,
                self.code_name,
                modname,
            )
            return False
        return True

    def get_rule_actions(self, rule_condition: str) -> Sequence[str]:
        """! @brief Return a list of all actions set for 'rule_contition'."""
        return [
            rule.action
            for rule in self.ruleset
            if rule.condition == rule_condition
        ]

    def reset_ruleset(self):
        """! @brief Sets the ruleset to the default rules."""
        self.ruleset = copy.copy(self.default_rules)

    def get_rule_conditions(self) -> Sequence[str]:
        """! @brief Return the conditions that are part of this Port's ruleset.
        Return a list of all rule conditions that have an action set for this port.
        """
        conditions = []
        for rule in self.ruleset:
            if rule.condition not in conditions:
                conditions.append(rule.condition)
        return conditions

    def overwrite_rule(self, rule_condition: str, new_action: str) -> bool:
        """! @brief Replaces the rule actions of an existing rule condition.
        If that rule condition doesn't already exist, it is added."""
        new_ruleset = deque()
        overwrite = False
        ovw_rule = self.Rule(rule_condition, new_action)

        if not self.__check_rule__(ovw_rule):
            return False

        for rule in self.ruleset:
            if rule.condition == rule_condition:
                if not overwrite:
                    overwrite = True
                    new_ruleset.append(ovw_rule)
            else:
                new_ruleset.append(rule)
        self.ruleset = new_ruleset
        return True

    ## @ingroup automatics_connection
    def remove_rule(self, condition: str, action: str) -> bool:
        """! @brief Remove a specific port rule, defined by both condition and action."""
        rule = [
            rule
            for rule in self.ruleset
            if (action in rule.action) and rule.condition == condition
        ]
        if len(rule) > 1:
            LOG.warning(
                (
                    "Found multiple rules to remove for port '%s'! "
                    "Removing only rule ('%s' -> '%s')."
                ),
                self.code_name,
                rule.condition,
                rule.action,
            )
        if not rule:
            LOG.warning(
                (
                    "Could not remove rule ('%s' -> '%s') for port '%s'."
                    " Rule does not exist."
                ),
                condition,
                action,
                self.code_name,
            )
            return False
        else:
            rule = rule[0]
            self.ruleset.remove(rule)
        return True

    def remove_condition(self, rule_condition: str) -> list:
        """! @brief Remove all rules using a provided condition.
        Remove 'rule_condition' from the ruleset
        along with all rule actions that were defined.
        Returns all removed rules."""
        new_ruleset = deque()
        out = []
        for rule in self.ruleset:
            if rule.condition != rule_condition:
                new_ruleset.append(rule)
            else:
                out.append(rule)
        return out

    def remove_rule_action(self, rule_action: str) -> list:
        """! @brief Remove all rules with the action 'rule_action'.
        Returns all removed rules."""
        out = []
        for rule in self.ruleset:
            if rule_action in rule.action:
                out.append(copy.copy(rule))
        for rule in out:
            self.remove_rule(rule.condition, rule.action)
        return out

    def update_ruleset(self, rules: list, priority: bool = False):
        """! @brief Merge a list of rules into the current ruleset.
        Duplicates are ignored.
        @param rules: Iterable containing rules of the type 'Port.Rule'
        @param priority: If True all new rules are evaluated first."""
        for rule in rules:
            if not self.__check_rule__(rule):
                continue
            if rule not in self.ruleset:
                if priority:
                    self.ruleset.appendleft(rule)
                else:
                    self.ruleset.append(rule)

    def set_ruleset(self, new_ruleset: list) -> bool:
        """! @brief Overwrites the current ruleset with the provided list of rules.
        The provided list must contain elements of the type 'Port.Rule'."""
        t_ruleset = []
        try:
            # Else ->
            for rule in new_ruleset:
                if self.__check_rule__(rule):
                    t_ruleset.append(rule)
        except TypeError:
            raise AsAssignError(
                self, "Parameter passed to 'set_ruleset' is not iterable!"
            )
        self.ruleset = deque(t_ruleset)
        return True

    def list_ruleset(self) -> int:
        """! @brief Print this Port's ruleset to the console.
        Print a list of all defined rule conditions together with all rule
        actions. Returns the number of rule conditions.
        Returns a count of rules for this port."""
        # If ruleset is empty
        if not self.ruleset:
            print("No rules defined for port '{}'.".format(self.name))
            return 0

        print(
            "Listing {} rule(s) for port '{}':".format(
                len(self.ruleset), self.name
            )
        )
        idx = 0
        for rule in self.ruleset:
            print(
                "Rule {}: {} -> {}".format(
                    str(idx), rule.condition, rule.action
                )
            )
            idx += 1
        return idx

    def get_print_name(self) -> str:
        """! @brief Returns the 'code_name' attribute"""
        return self.code_name

    ## @ingroup automatics_connection
    def assign_to(self, parent: object):
        """! @brief Assigns this instance as part of/linked to 'parent'"""
        self.parent = parent

    ## @ingroup automatics_generate
    def get_neutral_value(self) -> str:
        """! @brief Return the 'neutral' value of this port.
        This method takes the VHDL data type and data width into account."""
        if self.data_width.sep is None:
            if self.data_type in ("std_logic", "bit", "std_ulogic"):
                return "'0'"
            if self.data_type == "string":
                return '""'
            if self.data_type == "boolean":
                return "False"
            # Else ->
            return "0"
        # Else ->
        if self.data_type in (
            "std_logic_vector",
            "std_ulogic_vector",
            "bit_vector",
        ):
            return "(others => '0')"
        # Else ->
        return "0"

    ## @ingroup automatics_connection
    def is_same_port(self, comp_port) -> bool:
        """! @brief Check if the provided Port is the functionally the same as this Port.
        Detailed comparison between two ports to decide whether they are
        identical, but separate python objects."""
        try:
            if self.code_name != comp_port.code_name:
                return False
            if self.port_type != comp_port.port_type:
                return False
            if self.parent.name == comp_port.parent.name:
                if self.port_type == "interface":
                    if self.parent.unique_name != comp_port.parent.unique_name:
                        return False
                    if self.parent.parent.name != comp_port.parent.parent.name:
                        return False
            else:
                return False
            if self.direction != comp_port.direction:
                return False
            if self.data_width == comp_port.data_width:
                return True
        except AttributeError:
            pass
        return False

    ## @ingroup automatics_connection
    def make_external(self, value: bool = True) -> bool:
        """! @brief Propagate this Port to the interface of the generated IP-Core.
        Set the required port rule and port type to have Automatics
        make this port external."""
        if self.port_type == "interface":
            self.direction = self.get_direction_normalized()
        if value:
            self.port_type = "external"
            return self.set_ruleset(
                [self.Rule("external_port", "make_external")]
            )
        else:
            if self.port_type == "external":
                self.port_type = "single"
            self.remove_condition("external_port")
            return True

    def duplicate(self):
        """! @brief Get a copy of this port.
        This method resets attributes describing the connections of the port
        ('incoming, outgoing, connected and glue_signal).
        Returns the duplicate port object."""
        dupe = copy.copy(self)
        dupe.ruleset = copy.copy(self.ruleset)
        dupe.incoming = None
        dupe.outgoing = []
        dupe.connected = False
        dupe.glue_signal = None
        return dupe


## @ingroup automatics_intrep
class StandardPort(Port):
    """! @brief Slight variation of the regular Port class.
    Has a different default ruleset and serves as a way to differentiate
    between "normal" and "standard" ports."""

    def __init__(
        self,
        name: str = "",
        code_name: str = "",
        direction: str = "in",
        port_type: str = "single",
        data_type: str = "std_logic",
        optional: bool = False,
        data_width=Port.DataWidth(1, None, None),
        extra_rules: list = None,
        extra_rules_priority: bool = False,
        overwrite_ruleset: bool = False,
    ):
        super().__init__(
            name,
            code_name,
            direction,
            port_type,
            data_type,
            optional,
            data_width,
        )

        self.remove_condition("sink_missing")
        self.remove_condition("source_missing")
        self.add_rule("external_port", "make_external")
        if extra_rules is not None:
            self.update_ruleset(extra_rules, extra_rules_priority)
        if overwrite_ruleset and extra_rules is not None:
            self.set_ruleset(extra_rules)
