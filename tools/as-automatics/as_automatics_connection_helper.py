# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_automatics_connection_helper.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Implements some helper functions used in as_automatics to help during the
connection phase when building/generating a processing chain.
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
# @file as_automatics_connection_helper.py
# @author Philip Manke
# @brief Implements some helper functions used in as_automatics.
# -----------------------------------------------------------------------------

from math import ceil, log2
from typing import Sequence
from copy import copy

from as_automatics_port import Port
from as_automatics_interface import Interface
from as_automatics_module import AsModule
import as_automatics_helpers as as_help
import as_automatics_logging as as_log

LOG = as_log.get_log()


def get_max_regs_per_module(modules: Sequence[AsModule]) -> int:
    """Determines the value to use for 'max_regs_per_module'.
    Picks the highest amount of registers in any register interfaces of
    this processing chain. Then rounds up to the next highest power of
    two. Also sets the attribute for all register interfaces.
    Parameters: modules: iterable of all modules to analyse.
    Returns the determined value for 'max_regs_per_module'."""
    regifs = []
    # Collect all register interfaces
    for mod in modules:
        regifs.extend(mod.register_ifs)
    # Determine the highest number of registers in any of the interfaces
    max_reg_count = max([regif.get_reg_count() for regif in regifs], default=2)
    # Round up to the next higher power of two
    max_reg_count = 2 ** ceil(log2(max_reg_count))
    # Set the max_regs-attribute for the interfaces
    for regif in regifs:
        regif.max_regs_per_module = max_reg_count
    return max_reg_count


def set_unique_name(inter: Interface, module: AsModule):
    """Generate and set a (hopefully) unique name for the interface 'inter'.
    Sets inter.unique_name
    Parameters:
    inter: Interface to give a unique name to.
    module: inter's parent module, or the module to use for the unique name
    No return value."""
    inter.unique_name = "{}_{}{}{}_{}".format(
        module.name, inter.name_prefix, inter.type, inter.name_suffix, inter.direction
    )


def list_address_space(
    address_space: dict, addr_per_reg: int, max_regs_per_module: int
):
    """List the address space for the AXI slave register interface
        for this processing chain."""
    for key in address_space:
        # For every register interface: Gather some basic infos
        regif = address_space[key]
        base_addr = regif.base_address
        offset = 0
        # Retrieve the list of single registers
        reg_table = regif.get_reg_list()
        if len(reg_table) > max_regs_per_module:
            # If the register list is overlong: Error!
            LOG.error("Too many registers in '%s'", str(regif.parent))
            raise Exception(
                "Too many registers per module in {}".format(str(regif.parent))
            )
        # For every allocated register: Print address and register type
        for reg in reg_table:
            if reg != "None":
                print(
                    "{:#8X}: {}: {}".format(base_addr + offset, regif.parent.name, reg)
                )
            else:
                print(
                    "{:#8X}: {}: {}".format(
                        base_addr + offset, regif.parent.name, "Inactive"
                    )
                )
            offset += addr_per_reg


def resolve_data_width(port: Port) -> tuple:
    """Analyse the data width of port and replace generics
    in the data width with the value of matching generics
    found in the module the port belongs to."""
    # Is it already resolved?
    if is_data_width_resolved(port.data_width):
        return port.data_width
    # "Variable" dictionary for 'eval_data_width'
    gvals = {}
    for gen in port.generics:
        # Get value
        val = gen.get_value(top_default=False)
        # If no static value is available,
        # use the code name of the linked generic
        if val is None:
            val = getattr(gen.value, "code_name", None)
            # If that couldn't be fetched, skip this generic
            if val is None:
                continue
        gvals[gen.code_name] = val
    # Evaluate the data width
    new_data_width = as_help.eval_data_width(port, gvals)
    # If the evaluation could not complete
    if not is_data_width_resolved(new_data_width):
        LOG.info(
            (
                "Can't automatically resolve data width of '%s' in '%s'. "
                "Generic(-s) in '%s' have no value set or is(are) external!"
            ),
            port.code_name,
            port.parent.name,
            port.data_width_to_string(port.data_width),
        )
        return port.data_width
    return new_data_width


def is_data_width_resolved(data_width) -> bool:
    """Returns True if the data width has a static value (no VHDL Generics)."""
    return as_help.is_data_width_resolved(data_width)


def manage_data_widths(source: Port, sink: Port) -> bool:
    """This function checks if the data widths of both ports are compatible.
    It resolves the data widths by replacing the generics with their respective
    values and compares the resolved versions. The port objects aren't modified.
    Exception: For toplevel modules an automatic propagation of generics is
    attempted if the specific case is clear cut.
    Parameters:
    source and sink: Both Port objects to compare and adjust.
    Returns: Boolean value: True on success, else False.
    """
    # Determine data flow direction
    if source.get_direction_normalized() == "in":
        pin = source
        pout = sink
    else:
        pin = sink
        pout = source

    # Get "state" of data widths (are they fixed?)
    pin_res = is_data_width_resolved(pin.data_width)
    pout_res = is_data_width_resolved(pout.data_width)

    # If fixed and matching -> OK
    if pin_res and pout_res:
        if pin.data_width == pout.data_width:
            return True

    LOG.debug(
        "Data widths of '%s' and '%s' not resolved, resolving...",
        pin.code_name,
        pout.code_name,
    )
    # Evaluate data widths
    pin_rdw = resolve_data_width(pin)
    pout_rdw = resolve_data_width(pout)

    # Do they match now? Yes -> OK
    if pin_rdw == pout_rdw:
        LOG.debug("Data widths resolved successfully!")
        return True
    # Else: Warn user; automatic adjustment requires more development!
    # The simple "beta" version caused more problems than it was worth...

    # For toplevel modules (AXI Master / Slave):
    # Attempt automatic management of the generics in very simple cases
    # as it is inconvenient for the user to manually resolve toplevel
    # problems (especially for auto-instantiated modules like AXI_Masters)
    pin_mod = AsModule.get_parent_module(pin)
    pout_mod = AsModule.get_parent_module(pout)
    # If either port's module is directly instantiated in toplevel
    if (pin_mod.modlevel < 2) or (pout_mod.modlevel < 2):
        igen = pin.generics
        ogen = pout.generics

        # If both ports have exactly one generic
        if len(igen) == 1 and len(ogen) == 1:
            igen = igen[0]
            ogen = ogen[0]
            # Store current values
            igen_v = igen.value
            ogen_v = ogen.value
            # Propagate the source generic to the sink port
            igen.value = ogen
            pin_rdw = resolve_data_width(pin)
            # Did that resolve the difference?
            if pin_rdw == pout_rdw:
                LOG.debug(
                    (
                        "Generic Auto-Propagation: For ports '%s' and "
                        "'%s' of modules '%s' and '%s': Set value of "
                        "generic '%s' to generic '%s' of module '%s'."
                    ),
                    pout.code_name,
                    pin.code_name,
                    pin_mod.name,
                    pout_mod.name,
                    igen.code_name,
                    ogen.code_name,
                    pout_mod.name,
                )
                return True
            # If not, reverse the propagation and try the other way around
            igen.value = igen_v
            ogen.value = igen
            pin_rdw = resolve_data_width(pin)
            pout_rdw = resolve_data_width(pout)
            # Did that work?
            if pin_rdw == pout_rdw:
                LOG.debug(
                    (
                        "Generic Auto-Propagation: For ports '%s' and "
                        "'%s' of modules '%s' and '%s': Set value of "
                        "generic '%s' to generic '%s' of module '%s'."
                    ),
                    pout.code_name,
                    pin.code_name,
                    pin_mod.name,
                    pout_mod.name,
                    ogen.code_name,
                    igen.code_name,
                    pin_mod.name,
                )
                return True
            # If not, reverse the propagation and print the user warning
            ogen.value = ogen_v
            pout_rdw = resolve_data_width(pout)
        # Gather some data to generate a useful user message
        # Involved Generic names
        all_gens = []
        all_gens.extend(pout.generics)
        all_gens.extend(pin.generics)
        all_gens = [gen.code_name for gen in all_gens]
        # Module names
        pout_mod = pout_mod.name
        pin_mod = pin_mod.name
        # Data width strings
        pout_dw = Port.data_width_to_string(pout.data_width)
        pout_rdw = Port.data_width_to_string(pout_rdw)
        pin_dw = Port.data_width_to_string(pin.data_width)
        pin_rdw = Port.data_width_to_string(pin_rdw)

        # User warning message
        LOG.error(
            (
                "Data widths between ports '%s' and '%s' of modules "
                "'%s' and '%s' differ and must be adjusted manually!\n"
                "Data widths: For port '%s': (%s) - resolved as (%s) | "
                "For port '%s': (%s) - resolved as (%s).\n"
                "Use generics '%s' of the respective modules."
            ),
            pout.code_name,
            pin.code_name,
            pout_mod,
            pin_mod,
            pout.code_name,
            pout_dw,
            pout_rdw,
            pin.code_name,
            pin_dw,
            pin_rdw,
            all_gens,
        )

    # Special case for "slv_reg_interface" connections to as_regmgr
    if (pin.parent.type == "slv_reg_interface") and (
        pout.parent.type == "slv_reg_interface"
    ):
        if pin_mod.entity_name == "as_regmgr":
            pin.data_width = copy(pout.data_width)
            return True
        if pout_mod.entity_name == "as_regmgr":
            pout.data_width = copy(pin.data_width)
            return True

    return False


def update_interface_connected(inter: Interface):
    """Update the 'connected' attribute according to the interface's direction
    and registered connections."""
    conlist = inter.incoming if inter.direction == "in" else inter.outgoing
    if any((isinstance(item, Interface) for item in conlist)):
        inter.connected = True
    else:
        inter.connected = inter.is_connect_complete()


def __get_port_rule_message__(source: Port) -> str:
    if isinstance(source.parent, Interface):
        return "For source port '{}' of interface '{}' in module '{}'".format(
            source.code_name, source.parent, source.parent.parent.name
        )
    if isinstance(source.parent, AsModule):
        return "For source port '{}' of module '{}'".format(
            source.code_name, source.parent
        )
    return "For source port '{}'".format(source.code_name)


def get_port_matching(module: AsModule, name_fragment: str) -> Port:
    """Return the first port from 'module' with 'name_fragment'
    in its 'code_name' attribute."""
    for port in module.get_full_port_list():
        if name_fragment in port.code_name:
            return port
    return None
