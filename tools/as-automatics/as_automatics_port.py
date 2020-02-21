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
Implements the class 'Port' for as_automatics.
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
# @author Philip Manke
# @brief Implements the class 'Port' for as_automatics.
# -----------------------------------------------------------------------------

import copy
from collections import namedtuple, deque
from typing import Sequence
import as_automatics_logging as as_log

LOG = as_log.get_log()


class Port:
    """Description of a single port (^= signal interfacing with a hardware
       module within an ASTERICS processing chain), along with some
       meta-information for as_automatics (the processing chain generator)"""

    DataWidth = namedtuple("DataWidth", "a sep b")
    Rule = namedtuple("Rule", "condition action")
    WindowReference = namedtuple("WindowReference", "x y intername")

    directions = ("in", "out", "inout")
    port_types = (
        "external",
        "single",
        "interface",
        "register",
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
    # The ruleset describes how this port is going to be connected
    default_rules = [Rule("both_present", "connect"), Rule("sink_missing", "note")]

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

        self.ruleset = deque(self.default_rules)

        # Actual data type of this VHDL port (eg: bit, std_logic, integer, ...)
        self.data_type = data_type
        self.optional = optional
        self.data_width = data_width
        self.parent = None
        self.name = name
        self.code_name = code_name

        self.direction = "in"
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

    def connect(self, other):
        if self.port_type == "interface":
            self.parent.parent.chain.connect(self, other)
        else:
            self.parent.chain.connect(self, other)

    def add_generic(self, gen) -> bool:
        """Associate a Generic with this Port.
        This should happen automatically. Automatics will extract Generic names
        from the port's data width declaration.
        Parameters:
        gen: Generic object reference
        Returns True on success, else False (if Generic already associated)"""
        if gen not in self.generics:
            self.generics.append(gen)
            return True
        return False

    def remove_generic(self, gen) -> bool:
        """Remove a Generic association from this port.
        Parameters:
        gen: Generic to remove
        Returns True on success, else False (if Generic isn't associated)"""
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
        """Define what type of port this is."""
        if port_type in Port.port_types:
            self.port_type = port_type
        else:
            LOG.warning(
                "Port type '%s' of port '%s' is not valid!", port_type, self.code_name
            )

    def set_direction(self, direction: str):
        """Set the direction of the dataflow for this port.
           Valid values are in 'port.directions'
           (normally 'in', 'out', 'inout')"""
        if direction in Port.directions:
            self.direction = direction
        else:
            LOG.warning("Direction '%s' is not valid!", direction)

    def set_value(self, value: str) -> bool:
        """Set a static value for this port.
        Uses the port rule system."""
        return self.add_rule("any_present", "set_value({})".format(value))

    def set_glue_signal(self, signal):
        """Set this port's glue signal"""
        self.glue_signal = signal

    def get_direction_normalized(self) -> str:
        """Get the 'normalized' data direction of this port.
        This is the direction defined in VHDL source code,
        not modified by the interface direction."""
        direction = self.direction
        if self.port_type == "interface":
            if self.parent.direction == "out":
                direction = "out" if self.direction == "in" else "in"
        return direction

    def __str__(self) -> str:
        """Print the configuration of this port instance."""
        return (
            "{name}('{code}'): {necessity}, {direction} as "
            "{data_type}({data_width}), type: {port_type}"
        ).format(
            name=self.name,
            necessity=("optional" if self.optional else "mandatory"),
            direction=self.direction,
            data_type=self.data_type,
            data_width=self.data_width_to_string(self.data_width),
            port_type=self.port_type,
            code=self.code_name,
        )

    def __repr__(self) -> str:
        return self.code_name

    def set_window_reference(self, tags: iter):
        """Set the reference data required for ports of the 2D Window Pipeline
        interface.
        Parameters:
          tags (iterable): Three elements: X position, Y position,
                           Layer name (interface association)"""
        self.window_config = self.WindowReference(*tags)

    @staticmethod
    def data_width_to_string(data_width: namedtuple) -> str:
        """Return a string representation of the ports data width"""
        if data_width.sep is None:
            return str(data_width.a)
        return "{} {} {}".format(*data_width)

    @classmethod
    def list_possible_rules(cls):
        """List all possible rule conditions and rule effects."""
        print("List of all possible rule conditions: ")
        print(cls.rule_conditions)
        print("List of all possible rule effects:")
        print(cls.rule_actions)

    def set_connected(self, value: bool = True):
        """Set this ports 'connected' attribute. Convenience method.
        Parameters:
        value: Boolean value to set [Default: True]"""
        self.connected = value

    def add_rule(
        self, rule_condition: str, rule_action: str, priority: bool = True
    ) -> bool:
        """Add a rule to this port, defining how Automatics will handle this
        port when building the processing chain.
        Parameters:
        rule_condition: Define when this rule will be applied.
        rule_action: Define what should happen when this rule is applied.
        priority: Boolean value: Should this rule be the first to be applied?
                  Default value 'True'.
        Returns True on success, else False"""

        if priority:
            position = 0
        else:
            position = len(self.ruleset) - 1

        rule = self.Rule(rule_condition, rule_action)
        if self.__check_rule__(rule):
            self.ruleset.insert(position, rule)
            return True
        return False

    def __check_rule__(self, rule: namedtuple) -> bool:
        """Make sure the passed rule has a valid condition and action."""
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
            "set_value" in rule.action or "fallback_port" in rule.action
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
        """Return a list of all actions set for 'rule_contition'."""
        return [
            rule.action for rule in self.ruleset if rule.condition == rule_condition
        ]

    def get_rule_conditions(self) -> Sequence[str]:
        """Return a list of all rule conditions
        that have an action set for this port."""
        conditions = []
        for rule in self.ruleset:
            if rule.condition not in conditions:
                conditions.append(rule.condition)
        return conditions

    def overwrite_rule(self, rule_condition: str, new_action: str) -> bool:
        """Replaces the rule actions of an existing rule condition.
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

    def remove_rule(self, condition: str, action: str) -> bool:
        """Remove a specific port rule, defined by both condition and action."""
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
        """Remove 'rule_condition' from the ruleset
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
        """Remove all rules with the action 'rule_action'.
        Returns all removed rules."""
        out = []
        for rule in self.ruleset:
            if rule_action in rule.action:
                out.append(copy.copy(rule))
        for rule in out:
            self.remove_rule(rule.condition, rule.action)
        return out

    def update_ruleset(self, rules: list):
        """Merge a list of rules into the current ruleset.
        Duplicates are ignored.
        Parameters:
        rules: Iterable containing rules of the type 'Port.Rule'"""
        for rule in rules:
            if not self.__check_rule__(rule):
                continue
            if rule not in self.ruleset:
                self.ruleset.append(rule)

    def set_ruleset(self, new_ruleset: list) -> bool:
        """Overwrites the current ruleset with the provided list of rules.
        The provided list must contain elements of the type 'Port.Rule'."""
        t_ruleset = []
        if not isinstance(new_ruleset, list):
            LOG.error("'set_ruleset' got a non-iterable new ruleset!")
            return False
        # Else ->
        for rule in new_ruleset:
            if self.__check_rule__(rule):
                t_ruleset.append(rule)
        self.ruleset = deque(t_ruleset)
        return True

    def list_ruleset(self) -> int:
        """Print a list of all defined rule conditions together with all rule
        actions. Returns the number of rule conditions.
        Returns a count of rules for this port."""
        # If ruleset is empty
        if not self.ruleset:
            print("No rules defined for port '{}'.".format(self.name))
            return 0

        print("Listing {} rule(s) for port '{}':".format(len(self.ruleset), self.name))
        idx = 0
        for rule in self.ruleset:
            print("Rule {}: {} -> {}".format(str(idx), rule.condition, rule.action))
            idx += 1
        return idx

    def get_print_name(self) -> str:
        """Returns the 'code_name' attribute"""
        return self.code_name

    def assign_to(self, parent: object):
        """Assigns this instance as part of/linked to 'parent'"""
        self.parent = parent

    def get_neutral_value(self) -> str:
        """Return the 'neutral' value of this port.
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
        if self.data_type in ("std_logic_vector", "std_ulogic_vector", "bit_vector"):
            return "(others => '0')"
        # Else ->
        return "0"

    def is_same_port(self, comp_port) -> bool:
        """Detailed comparison between two ports to decide whether they are
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

    def make_external(self, value: bool = True) -> bool:
        """Set the required port rule and port type to have Automatics
        make this port external."""
        if self.port_type == "interface":
            self.direction = self.get_direction_normalized()
        if value:
            self.port_type = "external"
            return self.set_ruleset([self.Rule("external_port", "make_external")])
        else:
            if self.port_type == "external":
                self.port_type = "single"
            self.remove_condition("external_port")
            return True

    def duplicate(self):
        """Get a copy of this port.
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


class StandardPort(Port):
    """Slight variation of the regular Port class.
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
    ):
        super().__init__(
            name, code_name, direction, port_type, data_type, optional, data_width
        )

        self.remove_condition("sink_missing")
        self.remove_condition("source_missing")
        self.add_rule("external_port", "make_external")
        if extra_rules is not None:
            self.update_ruleset(extra_rules)


class GenericSignal(Port):
    """Variation of the regular Port class.
    Has additional attributes and may have multiple incoming data sources.
    The 'direction' and 'connected' attribute are ignored for this class.
    Models a generic VHDL signal in an architecture."""

    def __init__(
        self,
        name: str = "",
        code_name: str = "",
        port_type: str = "signal",
        data_type: str = "std_logic",
        optional: bool = False,
        data_width=Port.DataWidth(1, None, None),
    ):
        super().__init__(
            name, code_name, "inout", port_type, data_type, optional, data_width
        )
        self.incoming = []
        self.is_signal = True

    def get_direction_normalized(self):
        """GlueSignals don't have a direction. Returns 'inout'."""
        return "inout"

    def set_connected(self, value: bool = True):
        """Set the 'connected' attribute"""
        self.connected = False


class GlueSignal(GenericSignal):
    """Variation of the regular Port class.
    Has additional attributes and may have multiple incoming data sources.
    The 'direction' and 'connected' attribute are ignored for this class.
    Used only to connect a port to a VHDL component in a port map."""

    def __init__(
        self,
        name: str = "",
        code_name: str = "",
        port_type: str = "glue_signal",
        data_type: str = "std_logic",
        optional: bool = False,
        data_width=Port.DataWidth(1, None, None),
    ):
        super().__init__(name, code_name, port_type, data_type, optional, data_width)
