# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2020 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_automatics_vhdl_writer_helpers.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Implements some helper functions used by as_automatics' VHDL Writer class.
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
# @file as_automatics_vhdl_writer_helpers.py
# @ingroup automatics_helpers
# @ingroup automatics_generate
# @author Philip Manke
# @brief Implements some helper functions used in as_automatics' VHDL Writer.
# -----------------------------------------------------------------------------

import copy

from typing import Sequence

from as_automatics_generic import Generic
from as_automatics_signal import GenericSignal
from as_automatics_port import Port
from as_automatics_exceptions import AsConnectionError
from as_automatics_helpers import get_printable_datatype
from as_automatics_vhdl_static import COMPONENT_DECLARATION_TEMPLATE


##
# @addtogroup automatics_generate
# @{


def generate_vector_assignments(signal: GenericSignal) -> list:
    def get_target_width(a: int, sep: str, b: int = None):
        if sep == "to":
            return "{} to {}".format(a, b)
        elif sep == "downto":
            return "{} downto {}".format(b, a)
        else:
            return str(a)

    out = ["\n  -- Assign to signal {}:".format(signal.code_name)]
    assignment_template = "  {signal}({target}) <= {source};"

    # Iterate over the vector map starting from the lowest bit
    for idx in sorted(signal.vector_map_incoming.keys()):
        source = signal.vector_map_incoming[idx]
        if source is signal:
            return []
        source_bit_width = source.data_width.get_bit_width()
        sep = source.data_width.sep
        # Generate the assignment string for this source
        target = get_target_width(idx, sep, idx + source_bit_width - 1)

        out.append(
            assignment_template.format(
                signal=signal.code_name,
                target=target,
                source=source.code_name,
            )
        )
    from_idx = idx + source_bit_width
    if from_idx < signal.data_width.get_bit_width() - 1:
        target = get_target_width(
            from_idx,
            signal.data_width.sep,
            signal.data_width.get_bit_width() - 1,
        )
        out.append(
            assignment_template.format(
                signal=signal.code_name,
                target=target,
                source="(others => '0')",
            )
        )
    out.append("")
    return out


def generate_from_vector_assignment_strings(signal: GenericSignal) -> list:
    """! @brief Generate a string assigning to vector signal 'signal'
    from its vector map dictionary."""
    # Comment and empty line for readability
    out = ["\n  -- Assign from signal {}:".format(signal.code_name)]
    # Iterate over the vector map starting from the lowest bit
    for idx in sorted(signal.vector_map_outgoing.keys()):
        target = signal.vector_map_outgoing[idx]
        sep = target.data_width.sep
        # Get the target signal
        if isinstance(target, GenericSignal):
            pass
        elif isinstance(target, Port):
            if target.glue_signal:
                target = target.glue_signal
            else:
                raise AsConnectionError(
                    target,
                    "Port '{}' does not have a glue signal assigned!".format(
                        target
                    ),
                )
        target_bit_width = target.data_width.get_bit_width()
        # Generate the assignment string for this target
        width = ""
        if sep == "to":
            width = "{} to {}".format(idx, idx + target_bit_width - 1)
        elif sep == "downto":
            width = "{} downto {}".format(idx + target_bit_width - 1, idx)
        else:
            width = str(idx)
        out.append(
            "  {} <= {}({});".format(target.code_name, signal.code_name, width)
        )
    # Leave an empty line after assignment for readability
    out.append("")
    return out


def bundle_signals(bundle_list: list, bundle_type: str) -> list:
    """! @brief Generate VHDL code to bundle the signals in the bundle list.
    The type of bundling (and / or) is determined by 'bundle_type'.
    Returns a list of VHDL statements."""
    if not bundle_list:
        return None  # No action on empty list
    out = []
    crt_name = ""
    crt_stmt = ""
    local_list = copy.copy(bundle_list)
    local_list.sort(key=lambda sig: sig.code_name)

    # While there are unprocessed ports in the bundle list
    while local_list:
        # Filter by the name of the first port item
        crt_name = local_list[0].code_name
        # Initialize the statement
        crt_stmt = "{} <= ".format(crt_name)
        # Add all ports with the same name to the statement
        for nport in (
            port for port in bundle_list if port.code_name == crt_name
        ):
            # Find the connection of the current port:
            target = nport.glue_signal
            # Use the connections sink and the bundle type to append
            crt_stmt += "{} {} ".format(target.code_name, bundle_type)
            local_list.remove(nport)  # And remove them from the local list
        # Append the statement to the return list
        # The '[:-4]' removes the last superfluous bundle operand.
        out.append("  {};".format(crt_stmt[:-4].strip()))
    return out


def convert_generic_entity_list(generics: Sequence[Generic]):
    """! @brief Convert a list of Generic objects to the string representation
    in the format for a VHDL entity."""
    out = []
    for gen in generics:
        # Grab the default value
        gval = gen.default_value
        # Add quotes if it is a string (not boolean or numeric)
        if not (gval == "True" or gval == "False" or str(gval).isnumeric()):
            gval = '"{}"'.format(gval)
        # Set the format string (last generic "closes" the generic section)
        if generics.index(gen) == len(generics) - 1:
            format_str = "    {} : {} := {}\n  );"
        else:
            format_str = "    {} : {} := {};"
        # Insert the generic name, data type and default value
        # and add the result to the return list
        out.append(format_str.format(gen.code_name, gen.data_type, gval))
    return out


def convert_port_entity_list(ports: Sequence[Port]):
    """! @brief Convert a list of port objects to the string representation
    in the format for a VHDL entity."""
    out = []
    in_entity = []
    for port in ports:
        # Skip specifically excluded ports
        if not port.in_entity:
            continue
        # Skip ports of excluded interfaces
        if port.port_type == "interface":
            if (
                port.parent.to_external or port.parent.instantiate_in_top
            ) and port.parent.in_entity:
                # For external interfaces
                pass
            elif port.parent.parent.modlevel > 2 and port.parent.in_entity:
                # For interfaces of module groups within as_main
                pass
        # inlcude only external type single ports
        elif port.port_type in ("external", "single"):
            pass
        else:
            continue
        in_entity.append(port)

    for port in in_entity:
        # Generate string parts of the entity port declaration
        port_data = get_printable_datatype(port)
        port_dir = port.get_direction_normalized()
        # Generate and add string for entity
        if in_entity.index(port) == len(in_entity) - 1:
            out.append(
                "    {} : {} {}\n  );".format(
                    port.get_print_name(), port_dir, port_data
                )
            )
        else:
            out.append(
                "    {} : {} {};".format(
                    port.get_print_name(), port_dir, port_data
                )
            )
    return out


def write_list_to_file(wlist: Sequence[str], file, prefix_line: str = ""):
    file.write(prefix_line)
    file.write("\n".join(wlist))


def generate_component_declaration(module) -> str:
    if module.generics:
        gen_list_str = ["generic("]
        gen_list_str.extend(convert_generic_entity_list(module.generics))
        gen_list_str = "\n".join(gen_list_str) + "\n"
    else:
        gen_list_str = ""
    port_list = module.get_full_port_list(include_signals=False)
    port_list_str = ["port("]
    port_list_str.extend(convert_port_entity_list(port_list))
    port_list_str = "\n".join(port_list_str) + "\n"
    return COMPONENT_DECLARATION_TEMPLATE.format(
        module_name=module.name,
        entity_name=module.entity_name,
        port_list=port_list_str,
        generic_list=gen_list_str,
    )


## @}
