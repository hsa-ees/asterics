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
# @ingroup automatics_helpers
# @author Philip Manke
# @brief Implements some helper functions used in as_automatics.
# -----------------------------------------------------------------------------

from math import ceil, log2
from typing import Sequence
from copy import copy
from collections import namedtuple

from as_automatics_port import Port
from as_automatics_interface import Interface
from as_automatics_module import AsModule
from as_automatics_generic import Generic


import as_automatics_helpers as as_help
import as_automatics_logging as as_log

LOG = as_log.get_log()


##
# @addtogroup automatics_helpers
# @{


def get_max_regs_per_module(modules: Sequence[AsModule]) -> int:
    """! @brief Determines the value to use for 'max_regs_per_module'.
    Picks the highest amount of registers in any register interfaces of
    this processing chain. Then rounds up to the next highest power of
    two. Also sets the attribute for all register interfaces.
    @param modules: iterable of all modules to analyse.
    @return the determined value for 'max_regs_per_module'."""
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
    """! @brief Generate and set a (hopefully) unique name for the interface 'inter'.
    Sets inter.unique_name
    @param inter: Interface to give a unique name to.
    @param module: inter's parent module, or the module to use for the unique name
    """
    inter.unique_name = "{}_{}{}{}_{}".format(
        module.name,
        inter.name_prefix,
        inter.type,
        inter.name_suffix,
        inter.direction,
    )


def list_address_space(
    address_space: dict, addr_per_reg: int, max_regs_per_module: int
):
    """! @brief List the address space for the AXI slave register interface
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
                    "{:#8X}: {}: {}".format(
                        base_addr + offset, regif.parent.name, reg
                    )
                )
            else:
                print(
                    "{:#8X}: {}: {}".format(
                        base_addr + offset, regif.parent.name, "Inactive"
                    )
                )
            offset += addr_per_reg


def resolve_data_width(port: Port):
    """! @brief Resolves any equations and generic values in port's data width.
    Analyse the data width of port and replace generics
    in the data width with the value of matching generics
    found in the module the port belongs to."""
    if isinstance(port.data_width, list):
        return [__resolve_data_width__(dw, port) for dw in port.data_width]

    if getattr(port, "line_width", False):
        port.line_dw = __resolve_data_width__(port.line_width, port)

    return __resolve_data_width__(port.data_width, port)


def __resolve_data_width__(data_width, port) -> tuple:
    # Is it already resolved?
    if data_width.is_resolved():
        return data_width
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
    new_data_width = as_help.__eval_data_width__(data_width, gvals, port)
    # If the evaluation could not complete
    if not new_data_width.is_resolved():
        LOG.info(
            (
                "Cannot automatically resolve data width of '%s' in '%s'. "
                "Generic(-s) in '%s' have no value set or is(are) external!"
            ),
            port.code_name,
            port.parent.name,
            str(data_width),
        )
        return data_width
    return new_data_width


def is_same_modlevel(a, b):
    return get_parent_module(a).modlevel == get_parent_module(b).modlevel


def swap_if_necessary(source, sink) -> tuple:
    """! @brief Swap source and sink to preserve data flow direction."""
    # Return the data direction of an object if applicable, else return ""
    def get_dir(obj):
        if isinstance(obj, Port):
            return obj.get_direction_normalized()
        try:
            return obj.direction
        except AttributeError:
            if obj is None:
                raise ValueError()
            return ""

    def get_modlevel(obj):
        if isinstance(obj, AsModule):
            return obj.modlevel
        else:
            try:
                return get_parent_module(obj).modlevel
            except AttributeError:
                return -1

    # Get data directions of source and sink
    src_dir = get_dir(source)
    try:
        snk_dir = get_dir(sink)
    except ValueError:
        return (source, sink)

    src_ml = get_modlevel(source)
    snk_ml = get_modlevel(sink)

    src_parent = get_parent_module(source)
    snk_parent = get_parent_module(sink)

    # Check if source and sink need to be swapped
    # Data direction does not match with source and sink designation
    # source needs to be "out" and sink "in"
    # Explicit directions take precedence over "inout" and ""
    # Exception for following situation:
    # Signal connecting to outgoing port of a module group
    # The port (even though its direction "out") needs to be the data sink
    if src_parent is snk_parent and src_dir == "out" and snk_dir == "inout":
        return (sink, source)
    elif src_parent is snk_parent and src_dir == "inout" and snk_dir == "out":
        return (source, sink)
    elif any(
        (
            src_dir == "in" and snk_dir in ("out", "inout", ""),
            src_dir in ("inout", "") and snk_dir == "out",
            src_dir == "in" and snk_dir == "in" and src_ml > snk_ml,
        )
    ):
        return (sink, source)  # Return in swapped order
    return (source, sink)  # Return as received


def manage_data_widths(source: Port, sink: Port) -> bool:
    """! @brief This function checks if the data widths of both ports are compatible.
    It resolves the data widths by replacing the generics with their respective
    values and compares the resolved versions. The port objects aren't modified.
    Exception: For toplevel modules an automatic propagation of generics is
    attempted if the specific case is clear cut.
    Parameters:
    source and sink: Both Port objects to compare and adjust.
    @return Boolean value: True on success, else False.
    """
    # Determine data flow direction
    pin, pout = swap_if_necessary(source, sink)

    # Get "state" of data widths (are they fixed?)
    # If fixed and matching -> OK
    if pin.data_width.is_resolved() and pout.data_width.is_resolved():
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
    pin_mod = get_parent_module(pin)
    pout_mod = get_parent_module(pout)

    try:
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
    except AttributeError:
        pass

    # If either port's module is directly instantiated in toplevel
    # if (pin_mod.modlevel < 2) or (pout_mod.modlevel < 2):
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
    # Gather involved Generic names to generate a useful user message
    all_gens = []
    all_gens.extend(pout.generics)
    all_gens.extend(pin.generics)
    all_gens = [gen.code_name for gen in all_gens]

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
        pout_mod.name,
        pin_mod.name,
        pout.code_name,
        str(pout.data_width),
        str(pout_rdw),
        pin.code_name,
        str(pin.data_width),
        str(pin_rdw),
        all_gens,
    )

    return False


def update_interface_connected(inter: Interface):
    """! @brief Update the 'connected' attribute.
    Update according to the interface's direction and registered connections."""
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
    """! @brief Get first port from 'module' matching the name fragment.
    Return the first port from 'module' with 'name_fragment'
    in its 'code_name' attribute."""
    for port in module.get_full_port_list():
        if name_fragment in port.code_name:
            return port
    return None


def remove_port_connection(source: Port, sink: Port):
    """! @brief Remove/Undo a connection between two Ports."""
    source.outgoing.remove(sink)
    sink.incoming = None
    source.glue_signal = None
    sink.glue_signal = None
    sink.set_connected(False)


## @ingroup automatics_connection
def connect_generics(module: AsModule):
    """! @brief Connect the generics of 'module' to linked generics or to external"""
    # We process every Generic of the module
    for gen in module.generics:
        LOG.debug(
            "Handling Generic '%s' of '%s'...", gen.code_name, module.name
        )
        # Only Generics that have no value set need to be handled
        if gen.value:
            LOG.debug("No action needed, value is set to '%s'", gen.value)
            continue

        # link_to attribute has higher priority
        if gen.link_to and isinstance(gen.link_to, str):
            # For this we'll traverse to toplevel from this module
            # looking at for a Generic with the name == gen.link_to
            LOG.debug("'link_to' set to '%s'", gen.link_to)
            higher_mod = module.parent
            module_path = [higher_mod]
            while higher_mod:
                # This will return the matching generic, if it exists
                fgen = higher_mod.get_generic(gen.link_to, suppress_error=True)
                if fgen:
                    LOG.debug(
                        "Found matching generic '%s' in '%s'",
                        fgen.code_name,
                        fgen.parent.name,
                    )
                    break  # Exit loop if found
                # Not found, go to next higher module
                higher_mod = getattr(higher_mod, "parent", None)
                module_path.append(higher_mod)
            if fgen:  # If we found a matching generic, set this
                LOG.debug("Processing module path: '%s'", str(module_path))
                # Reorder modules: top to bottom
                module_path.reverse()
                for mod in module_path:
                    LOG.debug(
                        "Adding '%s' to module '%s'",
                        gen.code_name,
                        mod.name,
                    )
                    # Add a copy of the generic to every module
                    tgen = copy(gen)
                    mod.add_generic(tgen)
                    # Link the modules via their value attribute
                    tgen.value = fgen
                    fgen = tgen
                # Finally, set the original generics value
                gen.value = fgen
                continue
            else:
                LOG.warning(
                    (
                        "Could not find the link Generic '%s'"
                        " specified for '%s' in module '%s'!"
                    ),
                    gen.link_to,
                    gen.code_name,
                    module.name,
                )

        # Default behaviour (can be switched off)
        if gen.to_external:
            # For .to_external we need to make the generic accessible from
            # toplevel. Similar process as with gen.link_to
            LOG.debug("Making '%s' external...", gen.code_name)
            # Helper structure: AsModule and Generic pair
            ModGenPair = namedtuple("ModGenPair", "mod gen")

            higher_mod = module.parent
            module_path = []
            ext_name = "{}_{}".format(module.name, gen.code_name)
            ext_name = ext_name.upper()

            while higher_mod:
                # This will return the matching generic, if it exists
                fgen = higher_mod.get_generic(ext_name, suppress_error=True)
                # Add the module - generic pair to the list
                module_path.append(ModGenPair(higher_mod, fgen))
                # Next higher module
                higher_mod = getattr(higher_mod, "parent", None)
            LOG.debug("Processing module path: '%s'", str(module_path))
            # Reorder modules: top to bottom
            module_path.reverse()
            # Create the template external Generic
            ext_gen = copy(gen)
            ext_gen.code_name = ext_name
            # Temporary Generic reference variable
            tgen = None
            for mgp in module_path:
                if mgp.gen:  # No need to add a generic
                    LOG.info(
                        (
                            "Generic '%s' found in module '%s' while"
                            " making '%s' of '%s' external. Connecting"
                            " the generics..."
                        ),
                        mgp.gen.code_name,
                        mgp.mod.name,
                        gen.code_name,
                        module.name,
                    )
                else:  # Add a copy of the external generic
                    LOG.debug(
                        "Adding a copy of '%s' to module '%s'...",
                        ext_name,
                        mgp.mod.name,
                    )
                    mgp = ModGenPair(mgp.mod, copy(ext_gen))
                    mgp.mod.add_generic(mgp.gen)
                # Link this generic to the generic of the higher module
                mgp.gen.value = tgen
                tgen = mgp.gen
            # Finally, link to the source generic
            gen.value = tgen


## @ingroup automatics_connection
def resolve_generic(port: Port) -> bool:
    """! @brief Make sure Generics within port's data width exist in its parent module.
    This method makes sure that the Generics in port's data width
    exist in the VDHL entity of port's entity. Port may also be a GlueSignal
    Process: 1. Extract Generic strings from port's data width
    2. Match those strings to Generic objects in Port and the parent module
    3. Check if the Generic value is set; Check for and match linked Generic
    4. If necessary, substitute the Generic(s) with a match in group module
    5. If possible, use the defined value of the Generic
    6. Update port's data width and try to evaluate it.
    @param port: The data width attribute of this port will be resolved.
    @return True if the resolve function ran, False if nothing was done."""
    port.data_width = __resolve_generic__(port.data_width, port)
    try:
        port.line_width = __resolve_generic__(port.line_width, port)
        return all(
            (dw.is_resolved() for dw in (port.data_width, port.line_width))
        )
    except AttributeError:
        pass
    return port.data_width.is_resolved()


## @ingroup automatics_connection
def __resolve_generic__(
    data_width: Port.DataWidth, port: Port
) -> Port.DataWidth:
    # If data_width.sep is not set, there can't be any generics
    if not data_width.sep:
        return data_width  # No vector? Nothing to do...
    # Grab some resources (port's parent module and generics)
    module = get_parent_module(port)
    gen_strs = as_help.extract_generics(data_width)
    if not gen_strs:
        return data_width  # No generics? Nothing to do...

    # Grab the module group (module's parent) (AsModule does not have signals)
    if getattr(module, "signals", None) is None:
        gmodule = module.parent
        if not gmodule:
            gmodule = module
    else:
        gmodule = module
    # Remove any associated generics that are not found in data_width
    to_remove = []
    for gen in port.generics:
        if gen.code_name not in gen_strs or gen.parent is not module:
            to_remove.append(gen)
    for gen in to_remove:
        port.remove_generic(gen)

    # Make sure all found generics are associated with port
    for gen_str in gen_strs:
        match = False
        # First search in port's generic list
        for gen in port.generics:
            if gen.code_name == gen_str:
                match = True
                break
        if match:
            continue
        # If not found there, search the parent module
        for gen in module.generics:
            if gen.code_name == gen_str:
                port.add_generic(gen)
                break

    # Unpack the data_width
    ndw_a = data_width.a
    ndw_sep = data_width.sep
    ndw_b = data_width.b

    # Substitute any generics with their linked generic in the group module
    to_remove = []
    todo = []  # Here we'll store generic tuples (current, replacement)
    for gen in port.generics:
        val = gen.value
        # Skip generics that have an explicit value set
        # if val and not isinstance(val, Generic):
        #    continue
        # If the linked generic is defined in the group module
        if isinstance(val, Generic) and val.parent is gmodule:
            # We'll need use that generic in place of the generic of the
            # parent module, as that is not available in the group module
            todo.append((gen, val))
        # Else: if this generic is not set in the group module
        elif not gmodule.get_generic(gen.code_name, suppress_error=True):
            # And the generic has a value set (not a linked generic)
            if val and not isinstance(val, Generic):
                # Replace the generic name with that value in data_width
                if not str(data_width.a).isnumeric():
                    ndw_a = ndw_a.replace(gen.code_name, str(val))
                if not str(data_width.b).isnumeric():
                    ndw_b = ndw_b.replace(gen.code_name, str(val))
                # Make sure to remove the generic reference from port
                to_remove.append(gen)
    for gen in to_remove:
        port.remove_generic(gen)

    # Perform the generic substitution
    for gpair in todo:
        # Swap references in port
        port.remove_generic(gpair[0])
        port.add_generic(gpair[1])
        # and generic name strings in data_width
        if not str(data_width.a).isnumeric():
            ndw_a = ndw_a.replace(gpair[0].code_name, gpair[1].code_name)
        if not str(data_width.b).isnumeric():
            ndw_b = ndw_b.replace(gpair[0].code_name, gpair[1].code_name)
    # Re-assemble the data_width tuple and update it for port
    data_width = Port.DataWidth(a=ndw_a, sep=ndw_sep, b=ndw_b)
    # Re-evaluate data_width (resolve math)
    return __resolve_data_width__(data_width, port)


def get_parent_module(obj):
    """! @brief Get the parent AsModule of 'obj'."""
    if isinstance(obj, AsModule):
        return obj
    parent = getattr(obj, "parent", None)
    if parent is None:
        return None
    if isinstance(parent, AsModule):
        return parent
    # Else ->
    return get_parent_module(parent)


## @}
