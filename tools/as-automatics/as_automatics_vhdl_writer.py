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
# @ingroup automatics_generate
# @author Philip Manke
# @brief File writer for the infrastructure VHDL files of ASTERICS.
# -----------------------------------------------------------------------------

import copy
import itertools as ittls

from typing import Sequence
from math import ceil, log2

from as_automatics_generic import Generic
from as_automatics_port import Port
from as_automatics_signal import GlueSignal, GenericSignal
from as_automatics_module import AsModule
from as_automatics_module_group import AsModuleGroup
from as_automatics_register import SlaveRegisterInterface
from as_automatics_exceptions import AsFileError, AsConnectionError
from as_automatics_connection_helper import get_parent_module
from as_automatics_2d_pipeline import As2DWindowPipeline
from as_automatics_module_wrapper import AsModuleWrapper

import as_automatics_vhdl_writer_helpers as vhdl_write

import as_automatics_helpers as as_help
import as_automatics_logging as as_log
import as_automatics_vhdl_static as as_static


LOG = as_log.get_log()


##
# @addtogroup automatics_generate
# @{


class VHDLWriter:
    """! @brief Contains methods to write simple VHDL code.
    Can write entities, signal declarations, component generic and port maps.
    Used in Automatics to write the VHDL file describing
    the image processing chain by connecting processing components
    and the toplevel file."""

    def __init__(self, chain):
        # AsProcessingChain reference
        self.chain = chain
        # List of signals of the file currently generating
        self.signal_list = []
        # Architecture body of the file currently generating
        self.arch_body = []

    def clear_lists(self):
        """! @brief Reset to init state"""
        self.signal_list.clear()
        self.arch_body.clear()

    def write_module_group_vhd(self, folder: str, module_group: AsModuleGroup):
        """! @brief Generate the VHDL file for a module group (AsModuleGroup)"""
        LOG.info("Writing ASTERICS module group file '%s'.", module_group.name)
        filename = "{}.vhd".format(module_group.name)
        outfile = as_help.append_to_path(
            folder, filename, add_trailing_slash=False
        )

        # Generate the list of glue signals
        self.generate_glue_signal_strings(module_group.signals)

        header = self._generate_header_and_library_string(module_group)
        vhdl_list = []
        # Generate the module's entity declaration
        vhdl_list.extend(self._generate_entity(module_group, None))
        # Generate the toplevel architecture
        vhdl_list.extend(
            self._generate_module_group_architecture(module_group, None)
        )
        # Open the output file
        with open(outfile, "w") as ofile:
            # Make sure we can write to the file
            if not ofile.writable():
                raise AsFileError(msg="File not writable", filename=filename)
            ofile.write(header)
            vhdl_write.write_list_to_file(vhdl_list, ofile)

        # Reset to init state
        self.clear_lists()

    def _generate_entity(self, module: AsModule, file) -> list:
        """! @brief Generate and write the entity description of a given module
        to the output file."""
        # "Start" the entity description
        out_list = ["entity {} is".format(module.entity_name)]
        # Check if there are generics
        if module.generics:
            out_list.append("  generic(")
            # Generate the generic list
            out_list.extend(
                vhdl_write.convert_generic_entity_list(module.generics)
            )

        out_list.append("  port(")
        # Generate the port list
        out_list.extend(
            vhdl_write.convert_port_entity_list(
                module.get_full_port_list(include_signals=False)
            )
        )
        out_list.append("end entity {};\n".format(module.entity_name))
        return out_list

    def _generate_module_group_architecture(
        self, group_module: AsModuleGroup, file
    ) -> list:

        # Add static code
        self.signal_list.extend(group_module.static_code["signals"])
        self.arch_body.extend(group_module.static_code["body"])

        # Generate constant declaration strings
        constant_list = []
        for con in group_module.constants:
            constant_list.append(
                "  constant {} : {} := {};".format(
                    con.code_name,
                    as_help.get_printable_datatype(con),
                    con.value,
                )
            )

        # Run dynamic code generation functions of the group module
        code_dict = {"signals": [], "body": []}
        for gen in group_module.dynamic_code_generators:
            gen(self.chain, code_dict)
        self.signal_list.extend(code_dict["signals"])
        self.arch_body.extend(code_dict["body"])

        if not isinstance(group_module, AsModuleWrapper):
            self._architecture_port_assignements(group_module)
            self._architecture_port_bundles(group_module)
        self._architecture_signal_assignements(group_module)

        self.arch_body.extend(["  ", "  -- Components:"])

        for mod in group_module.modules:
            # Generate VHDL instantiation
            ret = self._instantiate_module(mod)
            if not ret:
                raise Exception(
                    "Problem instantiating module {}!".format(mod.name)
                )
            self.arch_body.append(ret)  # And add to the architecture body

        out_list = []

        out_list.append(
            "\narchitecture RTL of {} is".format(group_module.entity_name)
        )
        if constant_list:
            out_list.append("  -- Constant declarations:")
            out_list.extend(constant_list)
        if self.signal_list:
            out_list.append("\n  -- Signal declarations:")
            out_list.extend(self.signal_list)
        out_list.append("\nbegin")
        out_list.extend(self.arch_body)
        out_list.append("\nend architecture RTL;\n")
        return out_list

    def _architecture_port_assignements(self, group_module: AsModuleGroup):
        # External port assignments
        self.arch_body.extend(["  ", "  -- Port assignments:"])
        portlist = group_module.get_full_port_list(include_signals=False)
        for port in portlist:
            target = None
            # Skip register ports
            if isinstance(port.parent, SlaveRegisterInterface):
                continue
            # Special exception for as_main's read data axi slave signal
            # (managed in static code)
            if (
                group_module is self.chain.as_main
                and port.code_name == "axi_slv_reg_read_data"
            ):
                continue
            if port.get_direction_normalized() == "out":
                if port.in_entity and port.incoming:
                    continue
                else:
                    # No neutral value assignments for toplevel!
                    if port.parent is self.chain.top:
                        continue
                    target = port.get_neutral_value()
                self.arch_body.append(
                    as_static.ASSIGNMENT_TEMPL.format(port.code_name, target)
                )
            elif port.get_direction_normalized() == "in":
                for target in port.outgoing:
                    if (
                        isinstance(target, GenericSignal)
                        and not isinstance(target, GlueSignal)
                        and (port in target.incoming)
                    ):
                        try:
                            if port in target.vector_map_incoming.values():
                                continue
                        except AttributeError:
                            pass
                        if target.code_name == port.code_name:
                            continue
                        self.arch_body.append(
                            as_static.ASSIGNMENT_TEMPL.format(
                                target.code_name, port.code_name
                            )
                        )

    def _architecture_port_bundles(self, group_module: AsModuleGroup):
        if len(group_module.bundles.values()) > 0:
            self.arch_body.extend(["  \n", "  -- Bundled signals:"])
        # Generate the signal bundle logic:
        for btype in group_module.bundles:
            # For each bundling type, call the bundle method
            # and add the results to the architecture body
            ret = vhdl_write.bundle_signals(group_module.bundles[btype], btype)
            if ret:
                self.arch_body.extend(ret)
                self.arch_body.append("")

    def _architecture_signal_assignements(self, group_module: AsModuleGroup):
        # Add signal assignments to the architecture body
        self.arch_body.extend(["  ", "  -- Signal assignments:"])
        for signal in group_module.signals:
            # Add the signal declaration
            if signal.port_type == "signal":
                self._handle_module_group_signal(group_module, signal)

    def _handle_module_group_signal(
        self, group_module: AsModuleGroup, signal: GenericSignal
    ):
        self.signal_list.append(
            "  signal {} : {};".format(
                signal.code_name, as_help.get_printable_datatype(signal)
            )
        )
        in_done = False
        try:
            # If the signal has a vector map with content, generate
            # the vector assignment string stored in a glue signal

            if signal.vector_map_incoming:
                self.arch_body.extend(
                    vhdl_write.generate_vector_assignments(signal)
                )
                in_done = True
            if signal.vector_map_outgoing:
                self.arch_body.extend(
                    vhdl_write.generate_from_vector_assignment_strings(signal)
                )
                return None
        except AttributeError:
            pass
        for target in signal.outgoing:
            try:
                if signal in target.vector_map_incoming.values():
                    continue
            except AttributeError:
                pass
            # If target
            if (
                not isinstance(target, GenericSignal)
                and get_parent_module(target) is not group_module
            ):
                continue
            try:
                target_str = target.code_name
            except AttributeError:
                target_str = str(target)
            if target_str == signal.code_name:
                continue
            add_str = as_static.ASSIGNMENT_TEMPL.format(
                target_str, signal.code_name
            )
            if add_str not in self.arch_body:
                self.arch_body.append(add_str)
        for source in signal.incoming:
            if in_done:
                break
            try:
                # If the signal was already assigned to
                # in a vector map of the source,
                # this would generate a wrong assignment
                if signal in source.vector_map_outgoing.values():
                    break
            except AttributeError:
                # If the source doesn't have a vector map
                pass
            # If the signal was already assigned to in a port map,
            # this would generate a wrong assignment
            if get_parent_module(source) in group_module.modules:
                break
            try:
                source_str = source.code_name
            except AttributeError:
                source_str = str(source)
            if source_str == signal.code_name:
                continue
            add_str = as_static.ASSIGNMENT_TEMPL.format(
                signal.code_name, source_str
            )
            if add_str not in self.arch_body:
                self.arch_body.append(add_str)

    def _instantiate_module(self, module: AsModule) -> str:
        """! @brief Generate VHDL code as a list of strings to instantiate 'module'.
        Handles generic assignment and port mapping."""

        # -> Generating the generic map <-
        gen_str = []
        if module.generics:
            gen_str.append("  generic map(")
            for tgen in module.generics:
                # If the generic was set by the user in the generator,
                # use that value
                if isinstance(tgen.value, Generic):
                    ret = tgen.value.code_name
                else:
                    ret = tgen.get_value()
                    # Skip generics that use the default value
                    if ret == tgen.default_value:
                        continue
                gen_str.append("    {} => {},".format(tgen.code_name, ret))
        if len(gen_str) > 1:
            # Remove the last comma "," and add a closing bracket
            gen_str[-1] = gen_str[-1].strip(",")
            gen_str.append("  )\n")
            gen_str = "\n".join(gen_str)
        else:
            gen_str = ""

        # -> Generating the port map <-
        port_str = ["  port map("]
        full_port_list = module.get_full_port_list(include_signals=False)
        # For every port of this module:
        for port in full_port_list:
            # Target of the port map
            target = None

            # Determine the format for this ports port map line
            if full_port_list.index(port) < len(full_port_list) - 1:
                templ_str = "    {} => {},"
            else:
                templ_str = "    {} => {}\n  );"

            # -> Has glue signal <-
            # Port mapping target is the port's glue signal
            if port.glue_signal:
                glue = port.glue_signal
                try:
                    target = glue if isinstance(glue, str) else glue.code_name
                except AttributeError:
                    raise AsConnectionError(
                        port,
                        "Unsuitable object assigned as glue signal of port! "
                        "'{}: {}'".format(type(glue), str(glue)),
                    )
                # If this glue signal should be included in the signal list
                if isinstance(glue, GlueSignal) and glue.is_signal:
                    # Add the glue signal to the signal list
                    # Assemble vhdl signal declaration string
                    glue_signal_str = "  signal {} : {};".format(
                        glue.code_name, as_help.get_printable_datatype(glue)
                    )
                    # Make sure the same glue signal is not declared twice
                    if glue_signal_str not in self.signal_list:
                        self.signal_list.append(glue_signal_str)

            else:  # -> No glue signal present <-
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

                if not target:  # -> No target <-
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
                            get_parent_module(port).name,
                            target,
                        )
                    else:
                        LOG.info(
                            (
                                "Port '%s' of module '%s' was left "
                                "unconnected, automatically set to [%s]!"
                            ),
                            port.code_name,
                            get_parent_module(port).name,
                            target,
                        )
            # Insert the values in the format string and add to the return list
            port_str.append(templ_str.format(port.code_name, target))
        port_str = "\n".join(port_str)

        # --> OUT
        entity_keyword_str = (
            "" if isinstance(module, AsModuleWrapper) else " entity"
        )
        out_str = as_static.MODULE_INSTANTIATION_TEMPLATE.format(
            module_name=module.name,
            entity_name=module.entity_name,
            entity_keyword=entity_keyword_str,
            port_map=port_str,
            generic_map=gen_str,
        )
        return out_str

    def generate_glue_signal_strings(self, signals: Sequence[GenericSignal]):
        """! @brief Convert a list of glue signal objects to a string representation
        in the format for VHDL signals in an architecture section."""
        for glue in signals:
            # We only process GlueSignals here...
            if not isinstance(glue, GlueSignal):
                continue
            # Insert values to format string
            glue_signal_str = "  signal {} : {};".format(
                glue.code_name, as_help.get_printable_datatype(glue)
            )
            # Filter duplicate signals
            if glue_signal_str not in self.signal_list:
                self.signal_list.append(glue_signal_str)

    # Can't outsource to vhdl_writer_helpers as it needs access to
    # AsModuleWrapper class
    @staticmethod
    def _generate_header_and_library_string(module_group: AsModuleGroup) -> str:
        out_str = ""
        filename = "{}.vhd".format(module_group.name)
        description = module_group.description

        # Generate the library use strings
        library_use_str = ""
        lib_use_template_packages = "use asterics.{}.all;\n"
        lib_use_template_entities = "use asterics.{};\n"
        for pkg in module_group.vhdl_libraries:
            library_use_str += lib_use_template_packages.format(pkg)
        module_entities = set()
        for mod in module_group.modules:
            if isinstance(mod, AsModuleWrapper):
                continue
            module_entities.add(mod.entity_name)
        for entity in sorted(module_entities):
            library_use_str += lib_use_template_entities.format(entity)

        out_str += as_static.HEADER.format(
            entity_name=module_group.name,
            filename=filename,
            longdesc=description,
            briefdesc=description,
        )

        # and the basic library 'use' declarations
        out_str += "\n{}{}{}\n".format(
            as_static.LIBS_IEEE,
            as_static.LIBS_ASTERICS,
            library_use_str,
        )
        return out_str


## @}
