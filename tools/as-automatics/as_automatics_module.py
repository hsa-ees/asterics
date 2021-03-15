# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_automatics_module.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Class representing an ASTERICS module part of an ASTERICS processing chain.
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
# @file as_automatics_module.py
# @ingroup automatics_intrep
# @author Philip Manke
# @brief Class representing a module of an ASTERICS processing chain.
# -----------------------------------------------------------------------------

import copy
import itertools as ittls

from typing import Sequence
from os.path import realpath
from collections import namedtuple

import as_automatics_logging as as_log

from as_automatics_helpers import foreach
from as_automatics_vhdl_reader import VHDLReader
from as_automatics_port import Port, StandardPort
from as_automatics_generic import Generic
from as_automatics_interface import Interface
from as_automatics_register import SlaveRegisterInterface
from as_automatics_exceptions import AsNameError, AsModuleError

LOG = as_log.get_log()


status_comment_tuple = namedtuple("status_comment", ("status", "comment"))

## @ingroup automatics_intrep
class AsModule:
    """! @brief Represents an ASTERICS hardware and/or software module.
    Contains all information about an ASTERICS module with the methods
    necessary to generate a module description from the entity description
    in the modules top-level VHDL file. Uses the class as_vhdl_reader
    to configure itself from top-level files."""

    interface_templates_cls = []
    standard_port_templates = [
        StandardPort(name="clk", port_type="external"),
        StandardPort(
            name="reset",
            port_type="single",
        ),
        StandardPort(name="reset_n", port_type="external"),
        StandardPort(name="rst", port_type="external"),
        StandardPort(name="rst_n", port_type="external"),
        StandardPort(
            name="ready",
            direction="out",
            port_type="single",
            extra_rules=[Port.Rule("single_port", "bundle_and")],
        ),
        StandardPort(
            name="flush",
            port_type="single",
            extra_rules=[Port.Rule("sink_missing", "note")],
        ),
        StandardPort(
            name="sync_error_out",
            port_type="single",
            direction="out",
            extra_rules=[Port.Rule("single_port", "bundle_or")],
        ),
        StandardPort(name="sync_error_in", port_type="single", direction="in"),
    ]

    class ModuleTypes:
        string = ""
        string += "{}: {}\n".format("UNSPECIFIED", "No type specified")
        string += "{}: {}\n".format(
            "HARDWARE", "Main ASTERICS hardware processing module"
        )
        string += "{}: {}\n".format(
            "SOFTWARE", "Main ASTERICS software processing module"
        )
        string += "{}: {}\n".format(
            "LIBRARY",
            "Library submodule not fur use by the user (automatically inserted)",
        )
        string += "{}: {}\n".format(
            "HARDWARE_SOFTWARE",
            "Main ASTERICS module processing both in software and hardware",
        )
        string += "{}: {}\n".format(
            "HARDWARE_SW_CTRL",
            "Main ASTERICS hardware processing module with a software driver",
        )
        STR = string
        UNSPECIFIED = status_comment_tuple(
            status="UNSPECIFIED", comment="No type specified"
        )
        HARDWARE = status_comment_tuple(
            status="HARDWARE",
            comment="Main ASTERICS hardware processing module",
        )
        HARDWARE_SW_CTRL = status_comment_tuple(
            status="HARDWARE_SW_CTRL",
            comment="Main ASTERICS hardware processing module with a software driver",
        )
        SOFTWARE = status_comment_tuple(
            status="SOFTWARE",
            comment="Main ASTERICS software processing module",
        )
        HARDWARE_SOFTWARE = status_comment_tuple(
            status="HARDWARE_SOFTWARE",
            comment="Main ASTERICS module processing both in software and hardware",
        )
        LIBRARY = status_comment_tuple(
            status="LIBRARY",
            comment="Library submodule not fur use by the user (automatically inserted)",
        )

    class DevStatus:
        string = "{}: {}\n".format("UNKNOWN", "No state specified")
        string += "{}: {}\n".format("WORK_IN_PROGRESS", "Code in development")
        string += "{}: {}\n".format("STABLE", "In working condition and tested")
        string += "{}: {}\n".format(
            "ALPHA", "Code in development, some features work"
        )
        string += "{}: {}\n".format(
            "UNMAINTAINED",
            "No longer maintained, not tested in current codebase",
        )
        string += "{}: {}\n".format(
            "LEGACY",
            "In working condition and maintained, but not longer up to date",
        )
        string += "{}: {}\n".format(
            "BETA",
            "Code works, but no tested completly and not necessarily feature complete",
        )
        STR = string
        UNKNOWN = status_comment_tuple(
            status="UNKNOWN", comment="No state specified"
        )
        STABLE = status_comment_tuple(
            status="STABLE", comment=" In working condition and tested"
        )
        BETA = status_comment_tuple(
            status="BETA",
            comment="Code works, but no tested completly and not necessarily feature complete",
        )
        ALPHA = status_comment_tuple(
            status="ALPHA", comment="Code in development, some features work"
        )
        WORK_IN_PROGRESS = status_comment_tuple(
            status="WORK_IN_PROGRESS", comment="Code in development"
        )
        LEGACY = status_comment_tuple(
            status="LEGACY",
            comment="In working condition and maintained, but no longer up to date",
        )
        UNMAINTAINED = status_comment_tuple(
            status="UNMAINTAINED",
            comment="No longer maintained, not tested in current codebase",
        )
        # Additional states?

    def __init__(self, name: str = ""):
        self.interface_templates = []
        self.ports = []
        self.interfaces = []
        self.generics = []
        self.register_ifs = []
        self.standard_ports = []
        self.name = name
        self.entity_name = ""
        self.module_dir = ""
        self.repository_name = ""
        self.entity_ports = []
        self.entity_generics = []
        self.entity_constants = []
        self.connected = False
        self.description = ""
        self.files = []
        self.driver_files = []
        self.dependencies = []
        self.parent = None
        self.modlevel = 0
        self.module_connections = []
        self.chain = None

        self.defgroup = ""
        self.addtogroup = ""
        self.description = ""
        self.brief_description = ""
        self.show_in_browser = True
        self.module_category = "Unspecified"
        self.dev_status = self.DevStatus.UNKNOWN
        self.module_type = self.ModuleTypes.UNSPECIFIED

    def __str__(self) -> str:
        if self.name:
            return "ASTERICS Module '{}' ({})".format(
                self.name, self.entity_name
            )
        else:
            return "ASTERICS Module '{}'".format(self.entity_name)

    def __repr__(self) -> str:
        if self.name:
            return self.name
        return self.entity_name

    ##
    # @addtogroup automatics_cds
    # @{

    def get_port(
        self,
        port_name: str,
        *,
        suppress_error: bool = False,
        by_code_name: bool = True
    ) -> Port:
        """! @brief Return the port matching the name 'port_name'.
        Returns the port part of this module matching the name 'port_name'
        in it's 'code_name' as read from VHDL code.
        Returns None if no matching port was found."""
        pname = port_name.lower()
        if by_code_name:
            ret = self.__get_port_by_code_name__(pname)
        else:
            ret = self.__get_port_by_name__(pname)
        if ret is None and not suppress_error:
            LOG.error(
                "get_port: Port '%s' not found in module '%s'!",
                pname,
                str(self),
            )
            raise NameError("No port {} found in {}!".format(pname, self.name))
        return ret

    def get(self, name: str, direction: str = "", if_type: str = ""):
        """! @brief Generic interface and port search method.
        @param name       The interface or port name to search for.
        @param direction  The interface's direction. ! Does not apply for ports !
        @param if_type    The type of interface to search for. ! Does not apply for ports !

        @return An interface or port of this AsModule searching by the object
        name and, for interfaces, also the direction.

        @note This method searches the interface list first. Consider using
              the method 'get_port()' when searching for ports
              to prevent possible false positives.
        @note Check the ASTERICS manual for Automatics interface naming rules.
        """
        out = None
        try:
            out = self.get_interface(name, direction, if_type)
        except AsNameError as err:
            self.chain.err_mgr.clear_error(err)
        if out is not None:
            return out
        try:
            out = self.__get_port__(name)
        except AsNameError:
            LOG.error(
                "Could not find port or interface '%s' in '%s'!",
                name,
                str(self),
            )
            raise AsNameError(
                name,
                self,
                msg="No port or interface '{}' found in '{}'!".format(
                    name, self.name
                ),
            )
        return out

    def make_port_external(self, port_name: str, value: bool = True) -> bool:
        """! @brief Make a port of this module external (to toplevel).
        This method modifies the port's rules.
        The port will be connected through to ASTERICS IP-Core toplevel.
        Parameters:
            port_name: The name of the port to make external
            value: Wether to make the port external (default), or make an external port
                   no longer external."""
        port = self.__get_port__(port_name)
        if not port:
            raise NameError(
                (
                    "Could not find a port with name '{}' " "in AsModule '{}'!"
                ).format(port_name, self.name)
            )
        return port.make_external(value)

    def make_interface_external(
        self,
        inter_name: str,
        direction: str = "",
        if_type: str = "",
        value: bool = True,
    ):
        """! @brief Make an interface of this module external (to toplevel).
        All ports of the interface will be made available as ports
        of the ASTERICS IP-Core.
        Parameters:
        @param inter_name  Name of the interface to modify.
        @param direction   Interface direction to differentiate, if necessary.
        @param if_type     Interface type to differentiate, if necessary.
        @param value       Wether to make the interface external (default), or
                           make external interfaces no longer external."""
        inter = self.get_interface(inter_name, direction, if_type)
        inter.make_external(value)

    def make_generic_external(self, generic_name: str):
        """! @brief Propagate 'generic_name' up to the systems toplevel.
        Propagate the Generic 'generic_name' of this module to toplevel,
        to enable editing it's value in the synthesis tool
        via the resulting IP-Core."""
        gen = self.get_generic(generic_name)
        gen.value = None
        gen.to_external = True
        return True

    ## @ingroup automatics_cds
    def link_generics(self, generic_name: str, link_to_generic: str):
        """! @brief Link 'generic_name' to 'link_to_generic' synchronizing their values.
        Set the 'link_to' attribute of generic
        'generic_name' to 'link_to_generic', causing it to to take the value of
        the linked generic, if it exists."""
        gen = self.get_generic(generic_name)
        gen.link_to_generic(link_to_generic)

    ## @ingroup automatics_cds
    def set_port_fixed_value(self, port_name: str, value: str) -> bool:
        """! @brief Set a fixed value for port 'port_name'
        The value of the parameter 'value' will be directly inserted into VHDL
        code, so make sure it is syntactically valid.
        Eg.: use "'0'" instead of "0" to assign to a std_logic port.
        You can use constants, expressions and signal/port names."""
        port = self.__get_port__(port_name)
        if not port:
            raise NameError(
                (
                    "Could not find a port with name '{}' " "in AsModule '{}'!"
                ).format(port_name, self.name)
            )
        return port.set_value(value)

    def port_rule_add(
        self, port_name: str, condition: str, action: str
    ) -> bool:
        """! @brief Add a rule to the specified port.
        The rule: 'condition' -> 'action' will be added to the port 'port_name'.
        Use Port.list_possible_rules() to get a list of all valid conditions
        and actions used in port rules."""
        port = self.__get_port__(port_name)
        if not port:
            raise NameError(
                (
                    "Could not find a port with name '{}' " "in AsModule '{}'!"
                ).format(port_name, self.name)
            )
        return port.add_rule(condition, action)

    def port_rule_remove(
        self, port_name: str, condition: str, action: str
    ) -> bool:
        """! @brief Remove a rule to the specified port.
        The rule: 'condition' -> 'action' will be removed from the port
        'port_name'."""
        port = self.__get_port__(port_name)
        if not port:
            raise NameError(
                (
                    "Could not find a port with name '{}' " "in AsModule '{}'!"
                ).format(port_name, self.name)
            )
        return port.remove_rule(condition, action)

    def port_rule_overwrite(
        self, port_name: str, condition: str, action: str
    ) -> bool:
        """! @brief Remove all rules with 'condition' and add 'condition' -> 'action'.
        Method for use in user script: Replace all 'actions' associated with
        'condition' leaving the rule 'condition' -> 'action'.
        Use Port.list_possible_rules() to get a list of all valid conditions
        and actions used in port rules."""
        port = self.__get_port__(port_name)
        if not port:
            raise NameError(
                (
                    "Could not find a port with name '{}' " "in AsModule '{}'!"
                ).format(port_name, self.name)
            )
        return port.overwrite_rule(condition, action)

    ## @ingroup automatics_cds
    def port_rule_list(self, port_name: str):
        """! @brief Print the port "port_name"s ruleset to the console.
        Method for use in user script or interactive mode: List all rules
        associated with the port 'port_name'."""
        port = self.__get_port__(port_name)
        if not port:
            raise NameError(
                (
                    "Could not find a port with name '{}' " "in AsModule '{}'!"
                ).format(port_name, self.name)
            )
        port.list_ruleset()

    def connect(self, connect_to, *, top=None):
        """! @brief Connect this module to another module.
        All compatible ports and interfaces will be connected.
        This method is data direction aware and expects the data flow direction
        to be from this module to the module passed to the method.
        Eg: camera.connect(writer)
        Expected data flow: From module 'camera' to module 'writer'.
        Not following the data flow will most likely result in missing or wrong
        connections!
        """
        self.chain.connect(source=self, sink=connect_to, top=top)

    def add_software_driver_files(self, driver_file_path_list: list):
        """! @brief Add multiple files to this module's software driver.
        All files in the directory 'modules/this_module/software/driver'
        are automatically part of this module's software driver."""
        foreach(driver_file_path_list, self.add_software_driver_file)

    def add_software_driver_file(self, driver_file_path: str):
        """! @brief Add a file to this module's software driver.
        All files in the directory 'modules/this_module/software/driver'
        are automatically part of this module's software driver."""
        self.driver_files.append(realpath(driver_file_path))

    def get_interfaces_filtered(self, direction: str = "", if_type: str = ""):
        """! @brief Get a list of interfaces filtered by type and direction.
        This function returns a list of interfaces of this module matching
        the specified criteria - either interface direction,
        interface type or both.
        If no criteria are passed, an empty list is returned."""

        if direction and if_type:
            return [
                inter
                for inter in self.interfaces
                if inter.type == if_type and inter.direction == direction
            ]
        elif direction:
            return [
                inter
                for inter in self.interfaces
                if inter.direction == direction
            ]
        elif if_type:
            return [inter for inter in self.interfaces if inter.type == if_type]
        # Else ->
        return []

    def get_interface(
        self,
        interface_name: str,
        direction: str = "",
        if_type: str = "",
        *,
        suppress_error: bool = False
    ) -> Interface:
        """! @brief Return an interface instance of name 'interface_name'.
        This method supports filters in cases where multiple interfaces with
        the same name exist. Throws an error if no matching interface is found.
        Parameters:
            interface_name: This is the name to search for. NOT the interface's type.
            direction: The data direction of the interface to find.
            if_type: The type of the interface. Eg.: as_stream
            suppress_error: For internal use. Method will not throw errors.
        Returns 'None' if no interface with the specified name exists."""
        # If both direction and type are unspedified
        if direction == "" and if_type == "":
            found = next(
                (
                    inter
                    for inter in self.interfaces
                    if str(inter) == interface_name
                ),
                None,
            )
        else:  # Filtered search
            # Filter by name
            found = [
                inter
                for inter in self.interfaces
                if str(inter) == interface_name
            ]
            # Filter by direction, if type unspecified
            if found and if_type == "":
                found = next(
                    (inter for inter in found if inter.direction == direction),
                    None,
                )
            # Filter by type, if direction unspecified
            elif found and direction == "":
                found = next(
                    (inter for inter in found if inter.type == if_type), None
                )
            # Filter by both type and direction
            elif found:
                found = next(
                    (
                        inter
                        for inter in found
                        if inter.type == if_type
                        and inter.direction == direction
                    ),
                    None,
                )
        # "Interface not found" error report
        if not found and not suppress_error:
            raise AsNameError(interface_name, self, "Could not find interface!")
        return found

    def get_slave_register_interface(
        self, if_name: str = ""
    ) -> SlaveRegisterInterface:
        """! @brief Returns a slave register interface object of this module.
        If none exist, returns None.
        Returns the first interface if 'if_name' is omitted."""
        if self.register_ifs:
            if len(self.register_ifs) == 1:
                return self.register_ifs[0]
            else:
                return next(
                    (reg for reg in self.register_ifs if reg.name == if_name),
                    None,
                )
        return None

    def get_generic(
        self, generic_name: str, *, suppress_error: bool = False
    ) -> Generic:
        """! @brief Return the Generic of this module that matches 'generic_name'.
        Using the generics '.code_name' as read from VHDL code to match.
        Returns None if no matching generic is found."""
        genname = generic_name.upper()
        found = next(
            (gen for gen in self.generics if gen.code_name == genname), None
        )
        if not found:
            found = next(
                (gen for gen in self.generics if gen.name == genname), None
            )
        if not found and not suppress_error:
            LOG.error(
                "Could not find generic '%s' in module '%s'!",
                generic_name,
                self.name,
            )
            raise NameError(
                "Could not find generic '{}' in module '{}'!".format(
                    generic_name, self.name
                )
            )
        return found

    ## @ingroup automatics_cds
    def set_generic_value(self, generic_name: str, value) -> bool:
        """! @brief Sets the generic value to 'value'.
        Uses the value check function to validate the passed value.
        Returns True if successful."""
        # Find the referenced generic
        try:
            gen = self.get_generic(generic_name.upper())
        except NameError:
            LOG.warning(
                "Generic '%s' not found in module '%s'; value not set",
                generic_name,
                self.name,
            )
            raise AsNameError(
                generic_name, self, "Generic with this name not found!"
            )
        # Validate the passed value
        if not gen.run_value_check(value):
            LOG.warning(
                "The value '%s' is invalid for generic '%s'",
                str(value),
                generic_name,
            )
            raise AsModuleError(
                self.name,
                "Generic '{}' set to an invalid value '{}'!".format(
                    generic_name, str(value)
                ),
            )
        gen.value = value
        return True

    def list_module(self, verbosity: int = 0):
        """! @brief List the configuration of this module on the console."""
        print("\n{}:".format(self))
        print("From repository '{}'".format(self.repository_name))
        print("\nBrief description:\n", self.brief_description)
        if self.generics:
            print("\nGenerics:")
            for gen in self.generics:
                if verbosity == 0:
                    print(gen.code_name)
                else:
                    print(gen)

        if verbosity > 0 and self.standard_ports:
            print("\n~~~\nStandard per module ports:")
            for port in self.standard_ports:
                if verbosity > 1:
                    print(port)
                else:
                    print(port.code_name)

        if self.interfaces:
            print("\n~~~\nInterfaces:")
            for inter in self.interfaces:
                # Skip register interfaces, listed separately
                if isinstance(inter, SlaveRegisterInterface):
                    continue
                if verbosity > 0:
                    inter.print_interface(verbosity > 1)
                else:
                    print(
                        str(inter)
                        + (" ->" if inter.direction == "in" else " <-")
                    )
                print("")

        if self.ports:
            print("\n~~~\nLone ports:")
            for port in self.ports:
                if verbosity > 0:
                    print(port)
                else:
                    print(port.code_name)

        if self.register_ifs:
            if verbosity == 0:
                if len(self.register_ifs) == 1:
                    print("\n1 register interface")
                else:
                    print(
                        "\n{} register interfaces".format(
                            len(self.register_ifs)
                        )
                    )
            else:
                print("\n~~~\nRegister interface(s):")
                for reg_if in self.register_ifs:
                    reg_if.print_interface(verbosity > 1)
                    print("")

    def list_generics(self):
        """! @brief Prints all generics of this module to the console."""
        for gen in self.generics:
            print(
                "{} value: '{}', default: '{}'".format(
                    gen.code_name, gen.value, gen.default_value
                )
            )

    ## @}

    ##
    # @addtogroup automatics_connection
    # @{

    def register_connection(self, module):
        """! @brief Add 'module' to this module's list of module connections."""
        if module not in self.module_connections:
            self.module_connections.append(module)

    ## @ingroup automatics_connection
    def is_connect_complete(self) -> bool:
        """! Returns True if this module does not have any unconnected
        interfaces or ports. Register interfaces are ignored."""
        for inter in self.interfaces:
            if not inter.is_connect_complete():
                return False
        for port in self.ports:
            if not port.connected:
                return False
        return True

    def __update_connections__(self):
        for port in self.get_full_port_list(include_signals=False):
            con = False
            if port.glue_signal:
                con = True
            elif port.get_direction_normalized() == "in":
                con = port.incoming is not None
            elif port.get_direction_normalized() == "out":
                con = bool(port.outgoing)
            port.set_connected(con)

    def assign_to(self, parent):
        """! @brief Set the 'parent' and 'modlevel' attribute of this module."""
        if parent is not None:
            self.parent = parent
            self.modlevel = parent.modlevel + 1

    def set_connected(self, value: bool = True):
        """! @brief Set the 'connected' parameter"""
        self.connected = value

    ## @}

    @classmethod
    def add_global_interface_template(cls, inter_template: Interface) -> bool:
        """! @brief Add a class-wide interface template for AsModule."""
        if not isinstance(inter_template, Interface):
            LOG.error(
                (
                    "Attempted to add '%s' as an interface template! "
                    "Not an Interface object!"
                ),
                str(inter_template),
            )
            return False
        compare = [repr(inter) for inter in cls.interface_templates_cls]
        if repr(inter_template) in compare:
            LOG.debug(
                (
                    "Couldn't add template '%s' to AsModule class, "
                    "already present."
                ),
                str(inter_template),
            )
            return False
        cls.interface_templates_cls.append(inter_template)
        return True

    def add_local_interface_template(self, inter_template: Interface) -> bool:
        """! @brief Add an interface template for this AsModule."""
        if not isinstance(inter_template, Interface):
            LOG.error(
                (
                    "Attempted to add '%s' as an interface template! "
                    "Not an Interface object!"
                ),
                str(inter_template),
            )
            return False
        compare = [repr(inter) for inter in self.__get_interface_templates__()]
        if repr(inter_template) in compare:
            LOG.debug(
                (
                    "Couldn't add template '%s' to AsModule class, "
                    "already present."
                ),
                str(inter_template),
            )
            return False
        self.interface_templates.append(inter_template)
        return True

    def __get_interface_templates__(self) -> Sequence[Interface]:
        out = copy.copy(self.interface_templates_cls)
        out.extend(self.interface_templates)
        return out

    def add_interface(self, interface: Interface) -> bool:
        """! @brief Add an interface instance to this AsModule."""
        inter_temp = copy.copy(interface)
        ports = [port.code_name for port in self.get_full_port_list()]
        if isinstance(interface, Interface):
            for port in inter_temp.ports:
                if port.code_name in ports:
                    interface.remove_port(port.code_name)
            interface.assign_to(self)
            self.interfaces.append(interface)
        else:
            LOG.warning(
                (
                    "Couldn't add interface '%s', "
                    "not a valid as_interface object."
                ),
                interface.name,
            )

    def add_port(self, port_obj: Port) -> bool:
        """! @brief Add a module specific port to this module.
        Returns True on success."""
        # Make sure parameter is a Port object
        if not isinstance(port_obj, Port):
            LOG.error(
                "AsModule: Couldn't add port '%s'. Not a Port object!",
                repr(port_obj),
            )
            return False
        # Check if it is already present in this module
        if port_obj.code_name in [port.code_name for port in self.ports]:
            LOG.debug(
                "Couldn't add port '%s' to module '%s', already present",
                str(port_obj),
                str(self),
            )
            return False
        # Add the port
        self.ports.append(port_obj)
        port_obj.assign_to(self)
        return True

    def add_standard_port(self, port_obj: Port) -> bool:
        """! @brief Add 'port_obj' as a StandardPort port to this module.
        Note: This method creates a new Port object using the data of the
        provided object!
        Returns False if the port could not be added (it already exists)."""
        if not isinstance(port_obj, Port):
            LOG.error("Object passed to 'add_standard_port' is not a Port!")
            return False

        for tport in self.standard_port_templates:
            # Check if the port name matches the template name
            if port_obj.name != tport.name:
                continue
            # Check if the port directions match
            if tport.direction != port_obj.direction:
                continue
            # Check if the ports data types match
            if tport.data_type != port_obj.data_type:
                continue
            # Check if template port is already present
            if any([tport.name == port.name for port in self.standard_ports]):
                continue

            # Build a new standard port object
            std_port = StandardPort(
                name=tport.name,
                code_name=port_obj.code_name,
                direction=port_obj.direction,
                port_type=tport.port_type,
                data_type=port_obj.data_type,
                data_width=port_obj.data_width,
            )
            std_port.glue_signal = port_obj.glue_signal
            std_port.in_entity = port_obj.in_entity
            std_port.set_ruleset(tport.ruleset)
            std_port.assign_to(self)
            self.standard_ports.append(std_port)
            LOG.debug(
                "Added '%s' as standard port '%s'",
                port_obj.code_name,
                std_port.name,
            )
            return True

        LOG.debug(
            "Couldn't add standard port '%s' already present!", str(port_obj)
        )
        return False

    def add_generic(self, generic_obj: Generic) -> bool:
        """! @brief Add generic 'generic_obj' to this module."""
        # Make sure the parameter is actually a Generic object
        if not isinstance(generic_obj, Generic):
            LOG.error(
                (
                    "AsModule: Couldn't add generic '%s': "
                    "Not a Generic object!"
                ),
                repr(generic_obj),
            )
            return False
        # Check if the parameter is already assigned to this module
        if generic_obj.code_name in [gen.code_name for gen in self.generics]:
            LOG.debug(
                "Generic '%s' already in module '%s'.",
                str(generic_obj),
                str(self),
            )
            return False
        # If both checks pass, add the generic
        self.generics.append(generic_obj)
        generic_obj.assign_to(self)
        return True

    def add_register_if(self, register_obj: SlaveRegisterInterface) -> bool:
        """! @brief Add register interface 'register_obj' to this module."""
        if not isinstance(register_obj, SlaveRegisterInterface):
            LOG.error(
                (
                    "AsModule: Couldn't add generic '%s': "
                    "Not a Generic object!"
                ),
                repr(register_obj),
            )
            return False
        self.register_ifs.append(register_obj)
        register_obj.assign_to(self)
        return True

    def remove_generic(self, generic_name: str) -> bool:
        """! @brief Remove a generic from this module by name 'generic_name'.
        Uses the generics '.code_name' to match. Returns True if successful."""
        generic_name = generic_name.upper()
        to_remove = [gen for gen in self.generics if gen.name == generic_name]
        if not to_remove:
            LOG.error(
                (
                    "Couldn't remove '%s' from interface '%s', generic "
                    "not found"
                ),
                generic_name,
                str(self),
            )
            return False

        if len(to_remove) > 1:
            # This shouldn't happen, 'add_generic' prohibits copies of
            # generics, the generics-list could be modified directly though
            LOG.warning(
                ("Found multiple generics to remove: %s - " "removing all!"),
                str(to_remove),
            )
        else:
            LOG.debug(
                "Removing generic '%s' from interface '%s'",
                generic_name,
                str(self),
            )
        for rem_gen in to_remove:
            self.generics.remove(rem_gen)
        return True

    def get_interface_type_count(self, inter_name: str) -> int:
        """! @brief Return the number of different interface types with name 'inter_name'.
        Multiple interfaces of the same type count as one."""
        return sum([1 for itf in self.interfaces if inter_name == itf.type])

    def __get_port_by_code_name__(self, port_name: str) -> Port:
        return next(
            (
                port
                for port in self.get_full_port_list()
                if port.code_name == port_name
            ),
            None,
        )

    def __get_port_by_name__(self, port_name: str) -> Port:
        return next(
            (
                port
                for port in self.get_full_port_list()
                if port.name == port_name
            ),
            None,
        )

    def __get_port__(self, port_name: str) -> Port:
        """! @brief Internal 'get_port' function. Does not raise errors.
        Tries to match the provided name with both 'code_name'
        and the abstract 'name'. Returns the found Port object or 'None'."""
        pname = port_name.lower()
        port = self.__get_port_by_code_name__(pname)
        if not port:
            return self.__get_port_by_name__(pname)
        return port

    def get_full_port_list(
        self, include_signals: bool = True
    ) -> Sequence[Port]:
        """! @brief Return a list containing every port of this module"""
        lists = [self.ports, self.standard_ports]
        for inter in self.interfaces:
            lists.append(inter.ports)
        if include_signals:
            try:
                lists.append(self.signals)
            except AttributeError:
                pass
        return list(ittls.chain(*lists))

    def __get_interface_by_un_fuzzy__(self, if_unique_name: str):
        """! Return first matching interface object for provided unique name."""
        return next(
            (
                inter
                for inter in self.interfaces
                if if_unique_name in inter.unique_name
            ),
            None,
        )

    def get_software_additions(self) -> list:
        return []

    def _set_generic(self, generic_name: str, value) -> bool:
        """! @brief Wrapper for 'set_generic_value' with additional functionality.
        Sets the generic to a value, using the value check function to
        validate the passed value. Creates the generic if it doesn't exist.
        Returns True if successful."""
        generic_name = generic_name.upper()
        if self.get_generic(generic_name, suppress_error=True) is None:
            gen = Generic(generic_name)
            gen.value = value
            return self.add_generic(gen)
        return self.set_generic_value(generic_name, value)

    def get_unconnected_ports(self) -> Sequence[Port]:
        """! Return all unconnected ports part of this module,
        except for ports part of a register interface."""
        self.__update_connections__()
        out = []
        for port in self.ports:
            if not port.connected:
                out.append(port)
        for port in self.standard_ports:
            if not port.connected:
                out.append(port)
        for inter in self.interfaces:
            uncon = inter.get_unconnected_ports()
            if uncon:
                out.extend(uncon)
        return out

    ##
    # @addtogroup automatics_analyze
    # @{

    def discover_module(
        self, file: str, window_module: bool = False, extra_function=None
    ):
        """! @brief Analyze and parse a VHDL toplevel file creating an AsModule.
        Extracts the generic, port, interface and register interface definitions
        to configure this AsModule object."""
        file = file.replace("//", "/")
        # Get a VHDLReader instance
        reader = VHDLReader(file, window_module)
        self.files.append(file)
        # Get the results from the reader
        # (the parsing is triggered implicitely)
        self.entity_name = reader.get_entity_name()
        self.entity_ports = reader.get_port_list()
        self.entity_generics = reader.get_generic_list()
        self.entity_constants = reader.get_constant_list()
        self.defgroup = reader.defgroup
        self.addtogroup = reader.addtogroup
        self.description = reader.description
        self.brief_description = reader.brief_description

        if extra_function is not None:
            extra_function()

        LOG.debug("Now assigning interfaces...")
        self.__assign_interfaces__()
        self.__name_interfaces__()

    def __name_interfaces__(self):
        """! @brief Names interfaces of this module.
        Names are chosen according to the following rules:
        If the interface has a unique prefix and/or suffix,
        only the prefix and/or suffix are used as the name.
        If multiple interfaces with no prefix and or suffix
        but different types are present, the type is added as a prefix.
        Interfaces of the same type and direction cannot exist witht he same
        prefix and suffix, as their VHDL names would be identical.
        If no prefix and suffix and only one interface maximum per direction
        is present, only the data direction is used as a name ("in", "out").
        Slave register interfaces always use the type in their name and are
        handled by a different function.
        """

        # Helper function to left-rotate a list by a fixed number of items
        def rotate(l: list, n: int) -> list:
            return l[n:] + l[:n]

        # "Worker" function for the naming function. Names a single interface
        # Uses a list of all remaining interfaces to make the decision
        # If the choice for the current interface is ambiguos, the interface is
        # not named, instead 'None' is returned and the interface list rotated
        # left by one, leaving the interface as the last to handle
        # All interfaces *should* always be able to be named deterministically.
        def handler(interfaces: list) -> list:
            crt_if = interfaces[0]  # First interface in list will be named
            # Unique names through suffix and/or prefix
            # Both suffix and prefix
            if crt_if.name_prefix != "" and crt_if.name_suffix != "":
                crt_if.name = (
                    crt_if.name_prefix.rsplit("_", maxsplit=1)[0]
                    + "_"
                    + crt_if.name_suffix.split("_", maxsplit=1)[-1]
                )
                return [crt_if]
            # Only prefix
            if crt_if.name_prefix != "":
                crt_if.name = crt_if.name_prefix.rsplit("_", maxsplit=1)[0]
                return [crt_if]
            # Only suffix
            if crt_if.name_suffix != "":
                crt_if.name = crt_if.name_suffix.split("_", maxsplit=1)[-1]
                return [crt_if]

            # Neither prefix nor suffix are present
            # Determine number of interfaces with the same type
            others = [
                inter for inter in interfaces if inter.type == crt_if.type
            ]
            if len(others) > 2:  # More than two: Filter by direction
                others = [
                    inter
                    for inter in others
                    if inter.direction == crt_if.direction
                ]
            if len(others) == 1:  # Exactly one: name using direction
                crt_if.name = crt_if.direction
                return [crt_if]
            if len(others) == 2:  # Exactly two:
                other_if = interfaces[
                    1
                ]  # Use the next interface for comparison
                # If direction differs: name both by their direction
                if crt_if.direction != other_if.direction:
                    crt_if.name = crt_if.direction
                    other_if.name = other_if.direction
                elif other_if.name_prefix != "" or other_if.name_suffix != "":
                    crt_if.name = crt_if.direction
                    other_if.name = other_if.name_prefix + other_if.name_suffix
                    other_if.name = other_if.name.replace("__", "_").strip("_")
                    other_if.name += "_" + other_if.direction
                else:  # Add the type
                    crt_if.name = crt_if.type + "_" + crt_if.direction
                    other_if.name = other_if.type + "_" + other_if.direction
                return [crt_if, other_if]
            return None

        # Working copy of interface list
        interfaces = copy.copy(self.interfaces)
        while interfaces:  # Run until all interfaces have been named
            to_remove = handler(interfaces)  # Name zero to two interfaces
            if to_remove is None:  # No interface named
                # Move current (first) interface to back of list
                interfaces = rotate(interfaces, 1)
                continue
            # Otherwise, remove the named interfaces from the list
            for inter in to_remove:
                interfaces.remove(inter)

    ## @ingroup automatics_analyze
    def __assign_interfaces__(self):
        """! For all ports discovered in the VHDL files entity
        Either add a new interface that the port might be a part of,
        add the port to an existing interface or as a lone port of
        the module"""
        for port in self.entity_ports:
            if not isinstance(port, Port):
                LOG.error("Skipping '%s'; not a port object.", str(port))
                continue

            LOG.debug("Fitting port '%s'", port.code_name)
            # Try first to assign the port to an existing or new interface
            self.__fit_port__(port)

        # List of ports found in the entity declaration is not needed anymore
        self.entity_ports.clear()

        LOG.debug(
            "There are %i interfaces present before consistency check.",
            len(self.interfaces),
        )

        # Check if all added interfaces have all mandatory ports
        to_remove = [
            inter for inter in self.interfaces if not inter.is_complete()
        ]
        LOG.debug("To Remove: %s", str([repr(inter) for inter in to_remove]))
        LOG.debug(
            "Interface list: %s",
            str([repr(inter) for inter in self.interfaces]),
        )

        for inter in to_remove:
            LOG.debug(
                ("Assigning all ports of interface '%s'" " to module '%s'."),
                repr(inter),
                self.name,
            )
            # If the interface is missing mandatory ports,
            # fit all ports of that interface again, not allowing new interfaces
            # as they would re-create this incomplete interface
            to_refit = copy.copy(inter.ports)
            self.interfaces.remove(inter)
            for port in to_refit:
                port.name = port.code_name
                port.direction = inter.get_port_direction_normalized(port.name)
                port.optional = False
                port.port_type = "single"
                self.__fit_port__(port, new_ifs_allowed=False)
        for inter in self.interfaces:
            if isinstance(inter, SlaveRegisterInterface):
                self.register_ifs.append(inter)

        LOG.debug("Now fitting generics...")
        # Assign matching generics to interfaces
        for gen in self.entity_generics:
            self.__assign_generic__(gen)

        # Assign matching constants to register interfaces:
        for const in self.entity_constants:
            LOG.debug("Now checking constant '%s' for regif.", const.code_name)
            # Check if the constant could match with a register interface
            if SlaveRegisterInterface.CONST_NAME in const.code_name:
                const.name = SlaveRegisterInterface.CONST_NAME
                # Check existing interfaces
                for reg_if in self.register_ifs:
                    if reg_if.set_config_constant(const):
                        break

    def __fit_port__(
        self, port_obj: Port, new_ifs_allowed: bool = True
    ) -> bool:
        """! Assign 'port_obj' either to an existing interface
        of, if not possible, create a new interface for this port.
        If no matching port exists in the interface templates,
        add this port as a lone port specific to this module."""
        # Try to fit/assign the port to an existing interface
        LOG.debug("Checking existing interfaces...")
        if self.__fit_port_to_existing_interface__(port_obj):
            return True

        if new_ifs_allowed:
            # Try to match the port to an interface template (new interface)
            LOG.debug(
                (
                    "Port didn't fit with existing interfaces. "
                    "Checking against interface templates..."
                )
            )
            if self.__fit_port_to_new_interface__(port_obj):
                return True

        # If the port is not part of a known interface:
        # Check if it's a standard port (ie. clk, reset, ...)
        LOG.debug(
            (
                "Port didn't match anything in interface templates. "
                "Checking for standard port."
            )
        )
        if any(
            [
                port_obj.code_name.find(tport.name) > -1
                for tport in self.standard_port_templates
            ]
        ):
            LOG.debug("Attempting to add as standard port...")
            if self.add_standard_port(port_obj):
                return True

        # Port didn't match anywhere, add it as a "lone port" of the module
        LOG.debug("Port didn't fit anywhere, adding as lone port.")
        port_obj.name = port_obj.code_name
        port_obj.port_type = "single"
        port_obj.optional = False
        self.add_port(port_obj)
        return False

    ## @ingroup automatics_analyze
    def __fit_port_to_existing_interface__(self, port_obj: Port) -> bool:
        """! Attempts to assign 'port_obj' to an existing interface of this
        module. Returns 'True' if the port was assigned, else 'False'."""

        for inter in self.interfaces:
            LOG.debug("Looking at existing interface '%s'", inter.int_name())
            if inter.fit_and_add_port(port_obj):
                return True

        return False

    ## @ingroup automatics_analyze
    def __fit_port_to_new_interface__(self, port_obj: Port) -> bool:
        """! @brief Checks if 'port_obj' matches a port of the interface templates.
        Calls __new_interface_from_template__() to add the
        matching interface to this module."""
        matchlist = []
        for template in self.__get_interface_templates__():
            LOG.debug(
                "Checking interface template for '%s'", template.int_name()
            )
            for tport in template.ports:
                if (
                    tport.name in port_obj.code_name
                    and tport.data_type == port_obj.data_type
                ):
                    matchlist.append(tport)
        if matchlist:
            matchlist.sort(key=lambda prt: len(prt.name), reverse=True)
            tport = matchlist[0]
            LOG.debug("Matched! Adding new interface...")
            new_if = self.__new_interface_from_template__(
                tport.parent, tport, port_obj
            )
            if new_if is None:
                return False
            self.add_interface(new_if)
            return True
        return False

    ## @ingroup automatics_analyze
    def __assign_generic__(self, generic_obj: Generic):
        """! Assigns the generic to interfaces that use it to define the data
        width of one or more of their ports."""
        LOG.debug("Now matching generic '%s'.", generic_obj.code_name)
        # Find existing interfaces using this generic:
        inter_list = copy.copy(self.interfaces)
        inter_list.extend(self.register_ifs)
        for inter in inter_list:
            LOG.debug("Checking interface '%s'.", inter.int_name())
            # For all ports of the interface:
            for port in inter.ports:
                try:
                    # Check if the generic name appears in port's data width
                    if generic_obj.code_name in str(port.data_width):
                        LOG.debug(
                            (
                                "Found generic '%s' in data width of port "
                                "'%s' of interface '%s'. Assigning..."
                            ),
                            generic_obj.code_name,
                            port.code_name,
                            inter.int_name(),
                        )
                        # If yes, assign it to the interface
                        inter.add_generic(generic_obj)
                except TypeError:
                    # If a TypeError is generated, the port width is an integer
                    # We're only interested in strings, as the generic name
                    # could be present
                    pass
        # Add the generic to this module
        generic_obj.name = generic_obj.code_name
        self.add_generic(generic_obj)

    def __new_interface_from_template__(
        self, template: Interface, t_port: Port, port_obj: Port
    ) -> Interface:
        """! Copies 'template' interface, configures 'port_obj',
        assigns it to the new interface and
        adds the interface to this module."""
        if (template.type == SlaveRegisterInterface.DEFAULT_NAME) and (
            self.entity_name != "as_regmgr"
        ):
            new_interface = SlaveRegisterInterface()
        else:
            new_interface = copy.copy(template)
            # Blank interface (only keeping name, direction, ...)
            new_interface.clear()
        new_interface.template = template
        new_interface.direction = "in"

        # If necessary, flip interface direction
        if t_port.direction == port_obj.direction:
            new_interface.direction = "in"
        else:
            new_interface.direction = "out"
        LOG.debug(
            "Direction of new interface set to '%s'", new_interface.direction
        )

        port_obj.name = t_port.name
        port_obj.optional = t_port.optional
        port_obj.port_type = "interface"
        if not new_interface.fit_and_add_port(port_obj):
            LOG.error(
                (
                    "Port '%s' didn't fit in interface '%s' in function "
                    "new_interface_from_template, which shouldn't happen!"
                ),
                port_obj.code_name,
                new_interface.int_name(),
            )
            return None
        new_interface.assign_to(self)
        return new_interface

    ## @}
