# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_automatics_register.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Implements the class 'SlaveRegisterInterface' for as_automatics.
The SlaveRegisterInterface extends the Interface class by functionality to
manage registers and the required 'as_regmgr' module.
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
# @file as_automatics_register.py
# @author Philip Manke
# @brief Implements the class 'SlaveRegisterInterface' for as_automatics.
# -----------------------------------------------------------------------------

from collections import namedtuple
from typing import Sequence

from as_automatics_interface import Interface
from as_automatics_port import Port
from as_automatics_generic import Generic
from as_automatics_constant import Constant
import as_automatics_helpers as as_help
import as_automatics_logging as as_log

LOG = as_log.get_log()


class SlaveRegisterInterface(Interface):
    """Describes the interface between an ASTERICS hardware module
       and the systems software in the form of slave registers
       of an AXI interface."""

    CONST_NAME = "slave_register_configuration"
    DEFAULT_NAME = "slv_reg_interface"
    # Mapping for VHDL register type configuration <=> internal representation
    REG_DIR_MATCH = {
        "00": "None",
        "01": "HW -> SW",
        "10": "HW <- SW",
        "11": "HW <=> SW",
        "AS_REG_NONE": "None",
        "AS_REG_STATUS": "HW -> SW",
        "AS_REG_CONTROL": "HW <- SW",
        "AS_REG_BOTH": "HW <=> SW",
    }

    @classmethod
    def is_register_port(cls, port_name: str) -> bool:
        """Checks if 'port_name' is a defined port name
           of the defined register interface"""
        return port_name in cls.reg_names

    @classmethod
    def set_register_port_names(cls, new_names: Sequence[str]):
        """Overwrites the statically defined port names
           of the register interface."""
        cls.reg_names = new_names

    def __init__(self, parent=None, data_width: int = 32, address: int = 0):
        super().__init__(self.DEFAULT_NAME)
        self.parent = parent
        self.base_address = address
        self.data_width = data_width
        self.hwtosw_regs = 0
        self.swtohw_regs = 0
        self.bidirectional_regs = 0
        self.inactive_regs = 0
        self.reg_count = 0
        self.regif_num = 0
        self.register_table = []
        self.generics = [Generic("REG_COUNT"), Generic("MODULE_BASEADDR")]
        self.config = None
        self.config_applied = False
        self.instantiate_module("as_regmgr", "as_main")
        self.to_external = False

    def __str__(self) -> str:
        return self.name_prefix + self.name + self.name_suffix

    def set_module_base_addr(self, base_addr: int, regif_num: int):
        """Set the base address for this register interface
        (used for the as_regmgr)."""
        self.base_address = base_addr
        self.regif_num = regif_num
        self.get_generic("MODULE_BASEADDR").value = "c_{}_base_addr".format(
            self.parent.name
        )

    def set_config_constant(self, const: Constant) -> bool:
        """Set the configuration constant, defining the register types of
           this interface. This method expects a Constant object,
           defined in as_automatics_constant.py."""
        # Is the config constant already assigned?
        if self.config is None:
            # Check if the config constants prefix and suffix
            # match those of the ports
            this_prefix, this_suffix = as_help.get_prefix_suffix(
                const.name, const.code_name, []
            )
            if (this_suffix != self.name_suffix) or (this_prefix != self.name_prefix):
                LOG.debug(
                    ("Config constant '%s' didn't fit, " "prefix/suffix mismatch!"),
                    const.code_name,
                )
                return False
            # If the names match
            if const.name == self.CONST_NAME:
                # Log some data about the constant. Implicitely checks type
                try:
                    LOG.debug(
                        ("Check constant '%s': data type: '%s'," " value: '%s'"),
                        const.code_name,
                        const.data_type,
                        const.value,
                    )
                except AttributeError:
                    LOG.warning("set_config_constant was passed a wrong type!")
                    raise TypeError("set_config_constant")

                # If we get to here, the constant should be fine
                LOG.debug(
                    "Assigned config constant '%s' to '%s'",
                    const.code_name,
                    str(self.parent),
                )
                const.assign_to(self)
                self.config = const
                self.config_applied = False
                return True
        else:
            LOG.debug("Config constant already set!")
            return False
        return False

    def clear_config_const(self):
        """Remove the configuration constant
           and reset the internal register type configuration."""
        # Reset all attributes determined only by the register type config
        self.config_applied = False
        self.bidirectional_regs = 0
        self.hwtosw_regs = 0
        self.swtohw_regs = 0
        self.inactive_regs = 0
        self.register_table = []
        self.reg_count = 0
        self.config = None

    def get_reg_count(self) -> int:
        """Returns the number of registers of this register interface."""
        # Run the analysis of the config constant, if not already complete
        if not self.config_applied:
            if not self.__decode_slvreg_table__():
                return -1

        return self.reg_count

    def get_register_numbers(self) -> [int, int, int]:
        """Prints the numbers of different registers this
           interface has configured."""
        # Run the analysis of the config constant, if not already complete
        if not self.config_applied:
            if not self.__decode_slvreg_table__():
                return (-1, -1, -1)

        return self.bidirectional_regs, self.hwtosw_regs, self.swtohw_regs

    def get_reg_list(self) -> Sequence[str]:
        """Returns a string list for all registers. The register type is
           encoded in the string per register (None, SW->HW, HW->SW, HW<=>SW).
           """
        if not self.config_applied:
            if not self.__decode_slvreg_table__():
                return []
        return self.register_table

    def __decode_slvreg_table__(self) -> bool:
        """Decodes the value of the config Constant object. Assumes that the
           value is in the format: '('{'"XX"',}','' '['others => "XX"']')'
           Where the 'X's may be either '0' or '1'.
           Additionally, instead of "XX", the constants "AS_REG_X" may be used,
           where the 'X' can be any of: "NONE", "STATUS", "CONTROL" and "BOTH".
           """
        self.config_applied = False
        # Do we even have a config Constant assigned?
        if self.config is None:
            return False
        # Split the value into single register defines
        # (the comma delimited values).
        str_arr = self.config.value.split(",")
        # If the result is an empty list (evaluates to False), error!
        if not bool(str_arr):
            LOG.error(
                (
                    "The register interface configuration constant "
                    "'%s' could not be parsed!"
                ),
                self.config.code_name,
            )
            return False

        self.register_table = []
        for raw_string in str_arr:
            # For every string: First clean the string
            item = raw_string.strip(' ()",;\n')
            try:
                # try to use the string as a key to the constant register
                # mapping directory. This "translates" the VHDL-source-string
                current_reg = self.REG_DIR_MATCH[item]
            except KeyError:
                # If that didn't work (string is not a direct register descr.)
                if "OTHERS" in item:
                    # If it is an "others" directive, extract the register
                    # description string
                    temp = item.strip(' "()').split("=>")
                    # If the current string does not contain "=>", error!
                    if len(temp) < 2:
                        LOG.error(
                            (
                                "The 'others' directive '%s' in the config "
                                "constant '%s' is malformed!"
                            ),
                            raw_string,
                            str(self.config),
                        )
                        continue
                    # Else we can clean the result and match the register type
                    temp[1] = temp[1].strip(' "()')
                    try:
                        others_reg = self.REG_DIR_MATCH[temp[1]]
                    except KeyError:
                        # If that also doesn't work, error!
                        LOG.warning(
                            ("Unrecognized register config: " "'%s' in module '%s'"),
                            item,
                            str(self.parent),
                        )
                        return False
                    # Else, "fill up" the remaining empty slots of the register
                    # type list
                    LOG.debug("'others' found, with register type '%s'.", others_reg)
                    reg_count = self.ports[0].data_width.b + 1
                    while len(self.register_table) < reg_count:
                        self.register_table.append(others_reg)
                    break
                elif "0 =>" in item or "0=>" in item:
                    temp = item.strip(' "()').split("=>")
                    if len(temp) < 2:
                        LOG.error(
                            (
                                "The register configuration constant "
                                "assignemnt is malformed! - '%s'"
                            ),
                            raw_string,
                        )
                        continue
                    temp = temp[-1].strip('" ()')
                    try:
                        current_reg = self.REG_DIR_MATCH[temp]
                    except KeyError:
                        LOG.error(
                            ("Unrecognized register config " "assignment: '%s'"), temp
                        )
                        return False

                else:
                    LOG.error(
                        ("Unrecognized register config: " "'%s' in module '%s'"),
                        item,
                        str(self.parent),
                    )
                    return False
            # If the match succeeded, add this registers type to the list
            self.register_table.append(current_reg)

        self.config_applied = True
        # Update the register type count (count: HW->SW, SW->HW, HW<=>SW)
        self.__count_register_types__()
        self.get_generic("REG_COUNT").value = self.reg_count
        LOG.debug("Register configuration decoded as: '%s'", str(self.register_table))
        return True

    def __count_register_types__(self):
        """This method is used to update the attributes 'bidirectional_regs',
           'hwtosw_regs' and 'swtohw_regs'."""
        if not self.config_applied:
            self.__decode_slvreg_table__()
        self.bidirectional_regs = 0
        self.hwtosw_regs = 0
        self.swtohw_regs = 0
        self.inactive_regs = 0
        for reg in self.register_table:
            if reg == "HW <=> SW":
                self.bidirectional_regs += 1
            elif reg == "HW -> SW":
                self.hwtosw_regs += 1
            elif reg == "HW <- SW":
                self.swtohw_regs += 1
            elif reg == "None":
                self.inactive_regs += 1
        self.reg_count = (
            self.bidirectional_regs
            + self.hwtosw_regs
            + self.swtohw_regs
            + self.inactive_regs
        )

    def assign_to(self, parent):
        """Assigns this instance as part of/linked to 'parent'"""
        self.parent = parent

    def set_connected(self, value: bool = True):
        """Sets the 'connected' attribute of this interface."""
        self.connected = value
        for port in self.ports:
            port.set_connected(value)

    def print_interface(self, verbose: bool = False):
        """Print an exhaustive listing of information about this interface."""
        if not self.config_applied:
            self.__decode_slvreg_table__()

        print("Slave register interface: '{}'".format(self))
        if not self.is_complete():
            print("Interface is incomplete!")
        print("{} HW <=> SW registers,".format(self.bidirectional_regs))
        print("{} HW -> SW registers,".format(self.hwtosw_regs))
        print("{} HW <- SW registers.".format(self.swtohw_regs))
        print("{} Inactive registers.".format(self.inactive_regs))

        if verbose:
            print("Register table:\n{}".format(self.register_table))
            print("List of ports:")
            for port in self.ports:
                print(port)
            if bool(self.generics):
                print("List of generics:")
                for gen in self.generics:
                    print(gen)
            print("Register configuration constant:")
            print(self.config)

    def list_ports(self):
        """Print a simple string representation
           of all ports assigned to this interface."""
        print([port.code_name for port in self.ports])
