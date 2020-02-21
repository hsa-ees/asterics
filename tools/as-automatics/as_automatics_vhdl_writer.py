# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_automatics_vhdl_writer.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Class capable of writing all the VHDL files necessary to define the
infrastructure required by any ASTERICS processing chain.
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
# @file as_automatics_vhdl_writer.py
# @author Philip Manke
# @brief File writer for the infrastructure VHDL files of ASTERICS.
# -----------------------------------------------------------------------------
import copy
from typing import Sequence
from math import ceil, log2

from as_automatics_generic import Generic
from as_automatics_port import Port, GlueSignal, GenericSignal
from as_automatics_module import AsModule, AsModuleGroup
from as_automatics_register import SlaveRegisterInterface
from as_automatics_exceptions import AsFileError

import as_automatics_helpers as as_help
import as_automatics_logging as as_log
import as_automatics_vhdl_static as as_static


LOG = as_log.get_log()


class VHDLWriter:
    """Contains methods to write simple VHDL code.
    Can write entities, signal declarations, component generic and port maps.
    Used in Automatics to write the VHDL file describing
    the image processing chain by connecting processing components
    and the toplevel file."""

    vhdl_out_path = "vivado_cores/ASTERICS/hw/hdl/vhdl/"

    def __init__(self, chain):
        self.chain = chain  # AsProcessingChain reference
        self.port_list = []  # List of ports of the file currently generating
        self.generic_list = []  # List of generics of the    ^
        self.signal_list = []  # List of local signals of the ^
        self.arch_body = []  # Architecture body of the       ^

    def clear_lists(self):
        """Reset to init state"""
        self.port_list = []
        self.generic_list = []
        self.signal_list = []
        self.arch_body = []

    def write_asterics_vhd(self, folder: str):
        """Generate the Toplevel ASTERICS VHDL file"""
        LOG.info("Writing ASTERICS toplevel VHDL file...")
        # Generate path to the output file
        outfile = as_help.append_to_path(folder, as_static.AS_TOP_FILENAME, False)

        # Generate the list of glue signals
        self.generate_glue_signal_strings(self.chain.top.signals)

        library_use_str = ""
        lib_use_template = "use asterics.{};\n"
        module_entities = []
        for mod in self.chain.top.modules:
            if mod.entity_name not in module_entities:
                module_entities.append(mod.entity_name)
        for entity in module_entities:
            library_use_str += lib_use_template.format(entity)

        # Open the output file
        with open(outfile, "w") as ofile:
            # Make sure we can write to the file
            if not ofile.writable():
                raise AsFileError(
                    msg="File not writable", filename=as_static.AS_TOP_FILENAME
                )
            # Write the header
            ofile.write(
                as_static.HEADER.format(
                    entity_name=as_static.AS_TOP_ENTITY,
                    filename=as_static.AS_TOP_FILENAME,
                    longdesc=as_static.AS_TOP_DESC,
                    briefdesc=as_static.AS_TOP_DESC,
                )
            )
            # and the basic library 'use' declaration
            ofile.write(
                "\n{}{}{}\n".format(
                    as_static.LIBS_IEEE, as_static.LIBS_ASTERICS, library_use_str
                )
            )
            # Generate and write the entity descritpion
            self.__write_entity__(self.chain.top, ofile)
            # Generate and write the toplevel architecture
            self.__write_module_group_architecture__(self.chain.top, ofile)
            # Done writing to file
        # Reset to init state
        self.clear_lists()

    def write_as_main_vhd(self, folder):
        """Generate the 'as_main' intermediary VHDL file"""
        LOG.info("Writing ASTERICS module connection VHDL file...")
        # Generate path to the output file
        outfile = as_help.append_to_path(folder, as_static.AS_MAIN_FILENAME, False)

        library_use_str = ""
        lib_use_template = "use asterics.{};\n"
        module_entities = ["as_regmgr"]
        for mod in self.chain.as_main.modules:
            if mod.entity_name not in module_entities:
                module_entities.append(mod.entity_name)
        for entity in module_entities:
            library_use_str += lib_use_template.format(entity)

        # Generate the list of glue signals
        self.generate_glue_signal_strings(self.chain.as_main.signals)

        # Open the output file
        with open(outfile, "w") as ofile:
            # Make sure we can write to the file
            if not ofile.writable():
                raise AsFileError(
                    msg="File not writable", filename=as_static.AS_MAIN_FILENAME
                )
            # Write the file header
            ofile.write(
                as_static.HEADER.format(
                    entity_name=as_static.AS_MAIN_ENTITY,
                    filename=as_static.AS_MAIN_FILENAME,
                    longdesc=as_static.AS_MAIN_DESC,
                    briefdesc=as_static.AS_MAIN_DESC,
                )
            )
            # and baisc library 'use' declarations
            ofile.write(
                "\n{}{}{}\n".format(
                    as_static.LIBS_IEEE, as_static.LIBS_ASTERICS, library_use_str
                )
            )
            # Generate and write the entity descritpion
            self.__write_entity__(self.chain.as_main, ofile)
            # Generate and write the toplevel architecture
            self.__write_module_group_architecture__(self.chain.as_main, ofile)
            # Done writing to file
        # Reset to init state
        self.clear_lists()

    def __write_entity__(self, module: AsModule, file):
        """Generate and write the entity description of a given module
        to the output file."""
        # "Start" the entity description
        file.write("entity {} is\n".format(module.entity_name))
        # Generate the generic list
        self.generic_list = self.__convert_generic_entity_list__(module.generics)
        # Generate the port list
        self.port_list = self.__convert_port_entity_list__(module.get_full_port_list())
        # Write both lists to the file
        # Check if there are generics
        if self.generic_list:
            self.__write_list_to_file__(self.generic_list, file, "  generic(\n")
        self.__write_list_to_file__(self.port_list, file, "  port(\n")
        # "End" the entity description
        file.write("end entity {};\n".format(module.entity_name))

    def __write_module_group_architecture__(self, group_module: AsModuleGroup, file):

        self.signal_list.extend(group_module.static_code["signals"])
        self.arch_body.extend(group_module.static_code["body"])
        code_dict = {"signals": [], "body": []}
        if group_module.dynamic_code_generator:
            group_module.dynamic_code_generator(self.chain, code_dict)
            self.signal_list.extend(code_dict["signals"])
            self.arch_body.extend(code_dict["body"])

        self.arch_body.extend(["  \n", "  -- Port assignments:\n"])
        for port in group_module.ports:
            if port.port_type == "external" and port.glue_signal is not None:
                try:
                    target = port.glue_signal.code_name
                except AttributeError:
                    target = port.glue_signal
                if str(target) == port.code_name:
                    continue
                self.arch_body.append(
                    as_static.ASSIGNMENT_TEMPL.format(port.code_name, target)
                )

        # Add signal assignments to the architecture body
        self.arch_body.extend(["  \n", "  -- Signal assignments:\n"])
        for signal in group_module.signals:
            if signal.port_type == "signal":
                self.signal_list.append(
                    "  signal {} : {};\n".format(
                        signal.code_name, as_help.get_printable_datatype(signal)
                    )
                )
                if signal.glue_signal:
                    try:
                        target_str = signal.glue_signal.code_name
                    except AttributeError:
                        target_str = str(signal.glue_signal)
                    self.arch_body.append(
                        as_static.ASSIGNMENT_TEMPL.format(signal.code_name, target_str)
                    )
                    continue
                for target in signal.outgoing:
                    try:
                        target_str = target.code_name
                    except AttributeError:
                        target_str = str(target)
                    self.arch_body.append(
                        as_static.ASSIGNMENT_TEMPL.format(target_str, signal.code_name)
                    )
                for source in signal.incoming:
                    try:
                        source_str = source.code_name
                    except AttributeError:
                        source_str = str(source)
                    self.arch_body.append(
                        as_static.ASSIGNMENT_TEMPL.format(signal.code_name, source_str)
                    )

        self.arch_body.extend(["  \n", "  -- Components:\n"])

        for mod in group_module.modules:
            # Generate VHDL instantiation
            ret = self.__instantiate_module__(mod)
            if not ret:
                raise Exception("Problem instantiating module {}!".format(mod.name))
            self.arch_body.extend(ret)  # And add to the architecture body

        # Write to the output file
        file.write("\narchitecture RTL of {} is\n".format(group_module.entity_name))
        self.__write_list_to_file__(self.signal_list, file, "  -- Glue signals:\n")
        file.write("\nbegin\n")
        self.__write_list_to_file__(self.arch_body, file, "\n")
        file.write("end architecture RTL;\n")

    @staticmethod
    def __convert_generic_entity_list__(generics: Sequence[Generic]):
        """Convert a list of Generic objects to the string representation
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
                format_str = "    {} : {} := {}\n  );\n"
            else:
                format_str = "    {} : {} := {};\n"
            # Insert the generic name, data type and default value
            # and add the result to the return list
            out.append(format_str.format(gen.code_name, gen.data_type, gval))
        return out

    @staticmethod
    def __convert_port_entity_list__(ports: Sequence[Port]):
        """Convert a list of port objects to the string representation
        in the format for a VHDL entity."""
        out = []
        in_entity = []
        for port in ports:
            # Skip specifically excluded ports
            if not port.in_entity:
                continue
            # Skip ports of excluded interfaces
            if port.port_type == "interface" and (
                (port.parent.to_external or port.parent.instantiate_in_top)
                and port.parent.in_entity
            ):
                pass
            # inlcude only external type single ports
            elif port.port_type == "external":
                pass
            else:
                continue
            in_entity.append(port)

        for port in in_entity:
            # Generate string parts of the entity port declaration
            port_data = as_help.get_printable_datatype(port)
            port_dir = port.get_direction_normalized()
            # Generate and add string for entity
            if in_entity.index(port) == len(in_entity) - 1:
                out.append(
                    "    {} : {} {}\n  );\n".format(
                        port.get_print_name(), port_dir, port_data
                    )
                )
            else:
                out.append(
                    "    {} : {} {};\n".format(
                        port.get_print_name(), port_dir, port_data
                    )
                )
        return out

    def __instantiate_module__(self, module: AsModule) -> Sequence[str]:
        """Generate VHDL code as a list of strings to instantiate 'module'.
        Handles generic assignment and port mapping."""
        out = [
            "\n  -- Instantiate module {}:\n".format(module.name),
            "  {} : entity {}\n".format(
                "as_main_impl" if module.name == "as_main" else module.name,
                module.entity_name,
            ),
        ]
        gen_str = []
        if module.generics:
            gen_str.append("  generic map(\n")
            for tgen in module.generics:
                # If the generic was set by the user in the generator,
                # use that value
                if isinstance(tgen.value, Generic):
                    ret = tgen.value.code_name
                else:
                    ret = self.__get_printable_generic_value__(tgen)
                    # Skip generics that use the default value
                    if ret == tgen.default_value:
                        continue
                gen_str.append("    {} => {},\n".format(tgen.code_name, ret))
        if len(gen_str) > 1:
            # Replace the comma in the last generic mapping with a brace ')'
            gen_str[-1] = ")".join(gen_str[-1].rsplit(",", maxsplit=1))
            out.extend(gen_str)
        out.append("  port map(\n")

        full_port_list = module.get_full_port_list(include_signals=False)
        # For every port of this module:
        for port in full_port_list:
            # Target of the port map
            target = None

            # Determine the format for this ports port map line
            if full_port_list.index(port) < len(full_port_list) - 1:
                templ_str = "    {} => {},\n"
            else:
                templ_str = "    {} => {});\n"

            # Port mapping target is the port's glue signal
            if port.glue_signal and isinstance(port.glue_signal, GlueSignal):
                glue = port.glue_signal
                target = glue.code_name

                # If this glue signal should be included in the signal list
                if glue.is_signal:
                    # Add the glue signal to the signal list
                    # Assemble vhdl signal declaration string
                    glue_signal_str = "  signal {} : {};\n".format(
                        glue.code_name, as_help.get_printable_datatype(glue)
                    )
                    # Make sure the same glue signal is not declared twice
                    if glue_signal_str not in self.signal_list:
                        self.signal_list.append(glue_signal_str)
            else:  # If no glue signal present:
                # Port mapping target is one of the connected ports,
                # depending on port direction
                target = (
                    port.incoming
                    if port.get_direction_normalized() == "in"
                    else port.outgoing[0]
                    if port.outgoing
                    else None
                )
                # If the target is a Port object: use the code_name as target
                if isinstance(target, Port):
                    target = target.code_name
                # For strings: use the string as is (eg. for static values)
                elif isinstance(target, str):
                    target = target
                else:
                    target = None

                if not target:
                    # If the target is 'None': get neutral value
                    if port.get_direction_normalized() == "in":
                        target = port.get_neutral_value()
                    else:
                        target = "open"
                    # And warn the user of an unconnected port
                    if port.optional:
                        LOG.debug(
                            (
                                "Optional port '%s' of module '%s' was "
                                "left unconnected, automatically set to [%s]!"
                            ),
                            port.code_name,
                            AsModule.get_parent_module(port).name,
                            target,
                        )
                    else:
                        LOG.info(
                            (
                                "Port '%s' of module '%s' was left "
                                "unconnected, automatically set to [%s]!"
                            ),
                            port.code_name,
                            AsModule.get_parent_module(port).name,
                            target,
                        )
            # Insert the values in the format string and add to the return list
            out.append(templ_str.format(port.code_name, target))
        return out

    def generate_glue_signal_strings(self, signals: Sequence[GenericSignal]):
        """Convert a list of glue signal objects to a string representation
        in the format for VHDL signals in an architecture section."""
        for glue in signals:
            # We only process GlueSignals here...
            if not isinstance(glue, GlueSignal):
                continue
            # Insert values to format string
            glue_signal_str = "  signal {} : {};\n".format(
                glue.code_name, as_help.get_printable_datatype(glue)
            )
            # Filter duplicate signals
            if glue_signal_str not in self.signal_list:
                self.signal_list.append(glue_signal_str)

    @classmethod
    def __get_printable_generic_value__(cls, gen: Generic):
        return gen.get_value()

    @staticmethod
    def __write_list_to_file__(wlist: Sequence[str], file, prefix_line: str = ""):
        file.write(prefix_line)
        for string in wlist:
            file.write(string)
