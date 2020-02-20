# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# Copyright (C) Hochschule Augsburg, University of Applied Sciences
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

from as_automatics_generic import Generic
from as_automatics_port import Port, GlueSignal
from as_automatics_module import AsModule
from as_automatics_register import SlaveRegisterInterface
from as_automatics_exceptions import AsFileError

import as_automatics_helpers as as_help
import as_automatics_logging as as_log
import as_automatics_vhdl_static as as_static


LOG = as_log.get_log()


class VHDLWriter():
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
        outfile = as_help.append_to_path(folder,
                                         as_static.AS_TOP_FILENAME, False)

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
                raise AsFileError(msg="File not writable",
                                  filename=as_static.AS_TOP_FILENAME)
            # Write the header
            ofile.write(as_static.HEADER
                        .format(entity_name=as_static.AS_TOP_ENTITY,
                                filename=as_static.AS_TOP_FILENAME,
                                longdesc=as_static.AS_TOP_DESC,
                                briefdesc=as_static.AS_TOP_DESC))
            # and the basic library 'use' declaration
            ofile.write("\n{}{}{}\n".format(as_static.LIBS_IEEE,
                                            as_static.LIBS_ASTERICS,
                                            library_use_str))
            # Generate and write the entity descritpion
            self.__write_entity__(self.chain.top, ofile)
            # Generate and write the toplevel architecture
            self.__write_architecture_as_top__(self.chain.top, ofile)
            # Done writing to file
        # Reset to init state
        self.clear_lists()

    def write_as_main_vhd(self, folder):
        """Generate the 'as_main' intermediary VHDL file"""
        LOG.info("Writing ASTERICS module connection VHDL file...")
        # Generate path to the output file
        outfile = as_help.append_to_path(folder,
                                         as_static.AS_MAIN_FILENAME, False)

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
                raise AsFileError(msg="File not writable",
                                  filename=as_static.AS_MAIN_FILENAME)
            # Write the file header
            ofile.write(as_static.HEADER
                        .format(entity_name=as_static.AS_MAIN_ENTITY,
                                filename=as_static.AS_MAIN_FILENAME,
                                longdesc=as_static.AS_MAIN_DESC,
                                briefdesc=as_static.AS_MAIN_DESC))
            # and baisc library 'use' declarations
            ofile.write("\n{}{}{}\n".format(as_static.LIBS_IEEE,
                                            as_static.LIBS_ASTERICS,
                                            library_use_str))
            # Generate and write the entity descritpion
            self.__write_entity__(self.chain.as_main, ofile)
            # Generate and write the toplevel architecture
            self.__write_architecture_as_main__(self.chain.as_main,
                                                self.chain.address_space,
                                                ofile)
            # Done writing to file
        # Reset to init state
        self.clear_lists()

    def __write_entity__(self, module: AsModule, file):
        """Generate and write the entity description of a given module
        to the output file."""
        # "Start" the entity description
        file.write("entity {} is\n".format(module.entity_name))
        # Generate the generic list
        self.generic_list = self.__convert_generic_entity_list__(
            module.generics)
        # Generate the port list
        self.port_list = self.__convert_port_entity_list__(
            module.get_full_port_list())
        # Write both lists to the file
        # Check if there are generics
        if self.generic_list:
            self.__write_list_to_file__(self.generic_list, file,
                                        "  generic(\n")
        self.__write_list_to_file__(self.port_list, file, "  port(\n")
        # "End" the entity description
        file.write("end entity {};\n".format(module.entity_name))

    def __write_architecture_as_top__(self, top: AsModule, file):
        """Generate and write the architecture portion
        of the ASTERICS toplevel VHDL file"""
        # Add the static part of the toplevel file
        self.arch_body.extend(as_static.AS_TOP_ARCH_BODY_STATIC)
        # Instantiate all modules included in toplevel
        for mod in top.modules:
            # Generate the module instantiation VHDL code
            ret = self.__instantiate_module__(mod)
            if not ret:
                raise Exception("Problem instantiating module {}!"
                                .format(mod.name))
            # Add it to the architecture body
            self.arch_body.extend(ret)
        # "Start" the architecture portion of the file
        file.write("\narchitecture RTL of {} is\n"
                   .format(as_static.AS_TOP_ENTITY))
        # Write the list of glue signals
        self.__write_list_to_file__(self.signal_list, file,
                                    "  -- Glue signals:\n")
        # Begin the functional part of the architecture
        file.write("\nbegin\n")
        # Write the architecture body to the file
        self.__write_list_to_file__(self.arch_body, file, "\n")
        # "End" the architecture description
        file.write("end architecture RTL;\n")

    def __write_architecture_as_main__(self, as_main: AsModule,
                                       address_space: dict, file):
        """Generate and write the architecture portion
        of the intermediate as_main VHDL file"""
        # Get the register manager module template for reference
        reg_mgr = self.chain.library.get_module_template("as_regmgr")
        # Generate some required signals and constants for register management:
        self.signal_list.extend(
            ["\n  -- Register interface constants and signals:\n",
             "  constant c_slave_reg_addr_width : integer := {};\n"
             .format(self.chain.mod_addr_width + self.chain.reg_addr_width),
             "  constant c_module_addr_width : integer := {};\n"
             .format(self.chain.mod_addr_width),
             "  constant c_reg_addr_width : integer := {};\n"
             .format(self.chain.reg_addr_width),
             "  constant c_reg_if_count : integer := {};\n"
             .format(sum([len(mod.register_ifs)
                          for mod in self.chain.modules])),
             ("  signal read_module_addr : integer;\n"),
             ("  signal sw_address : std_logic_vector"
              "(c_slave_reg_addr_width - 1 downto 0);\n"),
             ("  signal mod_read_data_arr : slv_reg_data"
              "(0 to c_reg_if_count - 1);\n")])
        # And add some static functional VHDL code for register management
        self.arch_body = [as_static.AS_MAIN_ARCH_BODY_STATIC, "\n"]

        # Generate the signal bundle logic:
        for btype in self.chain.bundles:
            # For each bundling type, call the bundle method
            # and add the results to the architecture body
            ret = self.__bundle_signals__(self.chain.bundles[btype], btype)
            if ret:
                self.arch_body.extend(ret)
                self.arch_body.append("\n")

        regif_num = 0
        # Generate the register manager instantiations:
        for addr in address_space:  # For each address space
            # Grab the register manager reference
            regif = address_space[addr]
            self.signal_list.extend(
                self.__get_register_glue_signals__(regif))
            self.signal_list.append(
                '  constant c_{}_base_addr{} : integer := 16#{:8X}#;\n'
                .format(regif.parent.name, regif.name_suffix,
                        regif.base_address))
            self.signal_list.append(
                "  constant c_{}_regif_num{} : integer := {};\n"
                .format(regif.parent.name, regif.name_suffix, regif_num))
            # Generate the instantiation code for the register manager
            ret = self.__instantiate_reg_mgr__(regif, reg_mgr)
            if not ret:
                # On error (empty list)
                raise Exception(("Problem instantiating register manager for "
                                 "module {}").format(regif.parent.name))
            self.arch_body.extend(ret)  # Add to architecture body
            regif_num += 1  # Count the register interfaces

        self.signal_list.append("\n")

        # Generate the module instantiation code for each module in as_main
        for mod in as_main.modules:
            if mod is self.chain.as_main:
                continue  # Skip as_main itself
            # Generate VHDL instantiation
            ret = self.__instantiate_module__(mod)
            if not ret:
                raise Exception("Problem instantiating module {}!"
                                .format(mod.name))
            self.arch_body.extend(ret)  # And add to the architecture body

        # Write to the output file
        file.write("\narchitecture RTL of {} is\n".format(as_main.entity_name))
        self.__write_list_to_file__(self.signal_list, file,
                                    "  -- Glue signals:\n")
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
            if not (gval == "True" or gval ==
                    "False" or str(gval).isnumeric()):
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
            if (port.port_type == "interface" and
                    ((port.parent.to_external or port.parent.instantiate_in_top) and
                     port.parent.in_entity)):
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
                out.append("    {} : {} {}\n  );\n"
                           .format(port.get_print_name(), port_dir, port_data))
            else:
                out.append("    {} : {} {};\n"
                           .format(port.get_print_name(), port_dir, port_data))
        return out

    @staticmethod
    def __get_register_glue_signals__(
            regif: SlaveRegisterInterface) -> Sequence[str]:
        """Generate a list of glue signal declarations
        for the passed register interface."""
        out = ["\n  -- Register interface signals for {}:\n"
               .format(regif.parent.name)]
        for port in regif.ports:
            out.append("  signal {}_{} : {};\n"
                       .format(regif.parent.name, port.get_print_name(),
                               as_help.get_printable_datatype(port)))
        return out

    def __instantiate_reg_mgr__(self, regif: SlaveRegisterInterface,
                                regmgr: AsModule) -> Sequence[str]:
        """Generate and write the VHDL instantiation for
        a register manager object and associated register interface and
        return the generated architecture body section."""
        # Add lead in comment
        out = ["\n  -- Register manager for {}:\n".format(regif.parent.name)]
        # Start instantiation
        out.append("  {}_reg_mgr_{} : entity {}\n"
                   .format(regif.parent.name,
                           regif.parent.register_ifs.index(regif),
                           regmgr.entity_name))
        # Generic section:
        out.append("  generic map(\n")
        for tgen in regmgr.generics:
            # For each generic: match with static code
            if tgen.name == "MODULE_ADDR_WIDTH":
                ret = str(self.chain.mod_addr_width)
            elif tgen.name == "REG_ADDR_WIDTH":
                ret = "c_slave_reg_addr_width"
            elif tgen.name == "REG_DATA_WIDTH":
                ret = "C_S_AXI_DATA_WIDTH"
            elif tgen.name == "MODULE_BASEADDR":
                ret = "c_{}_regif_num".format(regif.parent.name)
            elif tgen.name == "REG_COUNT":
                ret = str(regif.reg_count)
            else:
                LOG.error(
                    "Unknown generic found in as_regmgr: '%s'",
                    tgen.name)
                return []
            # Get format string and add to output list
            if regmgr.generics.index(tgen) < len(regmgr.generics) - 1:
                out.append("    {} => {},\n".format(tgen.name, ret))
            else:
                out.append("    {} => {})\n".format(tgen.name, ret))

        # Port mapping section
        out.append("  port map(\n")
        full_port_list = regmgr.get_full_port_list()
        for port in full_port_list:
            try:  # Try to match each port
                target = as_static.REGMGR_MATCH_LIST_PORTS[port.name]
            except KeyError:  # Report errors
                LOG.error("Could not match port '%s' of '%s' in '%s'!",
                          port.name, str(regif), regif.parent.name)
                return []
            if "{}" in target:  # If there's a placeholder in the result
                if target.strip("()").endswith("{}"):
                    # Insert the parent module name
                    # and register interface suffix
                    target = target.format(
                        regif.parent.name, regif.name_suffix)
                target = target.format(regif.parent.name)
            # Get format string, insert mapping and add to return list
            if (full_port_list.index(port) <
                    len(full_port_list) - 1):
                out.append("    {} => {},\n".format(port.name, target))
            else:
                out.append("    {} => {});\n".format(port.name, target))
        return out

    def __instantiate_module__(self, module: AsModule) -> Sequence[str]:
        """Generate VHDL code as a list of strings to instantiate 'module'.
        Handles generic assignment and port mapping."""
        out = [
            "\n  -- Instantiate module {}:\n".format(
                module.name),
            "  {} : entity {}\n".format(
                "as_main_impl" if module.name == "as_main" else module.name,
                module.entity_name)]
        if module.generics:
            out.append("  generic map(\n")
            for tgen in module.generics:
                # If the generic was set by the user in the generator,
                # use that value
                if isinstance(tgen.value, Generic):
                    ret = tgen.value.code_name
                else:
                    ret = self.__get_printable_generic_value__(tgen)

                if module.generics.index(tgen) < len(module.generics) - 1:
                    out.append("    {} => {},\n".format(tgen.code_name, ret))
                else:
                    out.append("    {} => {})\n".format(tgen.code_name, ret))
        out.append("  port map(\n")

        full_port_list = module.get_full_port_list()
        # For every port of this module:
        for port in full_port_list:
            # Target of the port map
            target = None

            # Determine the format for this ports port map line
            if (full_port_list.index(port) <
                    len(full_port_list) - 1):
                templ_str = "    {} => {},\n"
            else:
                templ_str = "    {} => {});\n"
            # If this port is part of a register interface
            if isinstance(port.parent, SlaveRegisterInterface):
                # Generate the target glue signal name
                target = "{}_{}{}".format(port.parent.parent.name, port.name,
                                          port.parent.name_suffix)
                out.append(templ_str.format(port.code_name, target))
                continue  # Done for this port

            # Port mapping target is the port's glue signal
            if port.glue_signal and isinstance(port.glue_signal, GlueSignal):
                glue = port.glue_signal
                target = glue.code_name

                # If this glue signal should be included in the signal list
                if glue.is_signal:
                    # Add the glue signal to the signal list
                    # Assemble vhdl signal declaration string
                    glue_signal_str = "  signal {} : {};\n".format(
                        glue.code_name, as_help.get_printable_datatype(glue))
                    # Make sure the same glue signal is not declared twice
                    if glue_signal_str not in self.signal_list:
                        self.signal_list.append(glue_signal_str)
            else:  # If no glue signal present:
                # Port mapping target is one of the connected ports,
                # depending on port direction
                target = port.incoming if \
                    port.get_direction_normalized() == "in" \
                    else port.outgoing[0] if port.outgoing else None
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
                        LOG.info(
                            ("Optional port '%s' of module '%s' was "
                             "left unconnected, automatically set to [%s]!"),
                            port.code_name,
                            AsModule.get_parent_module(port).name,
                            target)
                    else:
                        LOG.warning(
                            ("Port '%s' of module '%s' was left "
                             "unconnected, automatically set to [%s]!"),
                            port.code_name,
                            AsModule.get_parent_module(port).name,
                            target)
            # Insert the values in the format string and add to the return list
            out.append(templ_str.format(port.code_name, target))
        return out

    @staticmethod
    def __bundle_signals__(bundle_list: Sequence[Port],
                           bundle_type: str) -> Sequence[str]:
        """Generate VHDL code to bundle the signals in the bundle list.
        The type of bundling (and / or) is determined by 'bundle_type'.
        Returns a list of VHDL statements."""
        if not bundle_list:
            return None  # No action on empty list
        out = []
        crt_name = ""
        crt_stmt = ""
        local_list = copy.copy(bundle_list)

        # While there are unprocessed ports in the bundle list
        while local_list:
            # Filter by the name of the first port item
            crt_name = local_list[0].code_name
            # Initialize the statement
            crt_stmt = "{} <= ".format(crt_name)
            # Add all ports with the same name to the statement
            for nport in (port for port in bundle_list
                          if port.code_name == crt_name):
                # Find the connection of the current port:
                target = nport.glue_signal
                # Use the connections sink and the bundle type to append
                crt_stmt += "{} {} ".format(target.code_name, bundle_type)
                local_list.remove(nport)  # And remove them from the local list
            # Append the statement to the return list
            # The '[:-4]' removes the last superfluous bundle operand.
            out.append("  {};\n".format(crt_stmt[:-4].strip()))
        return out

    def generate_glue_signal_strings(self, signals: Sequence[GlueSignal]):
        """Convert a list of glue signal objects to a string representation
        in the format for VHDL signals in an architecture section."""
        for glue in signals:
            # Insert values to format string
            glue_signal_str = "  signal {} : {};\n".format(
                glue.code_name, as_help.get_printable_datatype(glue))
            # Filter duplicate signals
            if glue_signal_str not in self.signal_list:
                self.signal_list.append(glue_signal_str)

    @classmethod
    def __get_printable_generic_value__(cls, gen: Generic):
        val = gen.get_value()
        if isinstance(val, Generic):
            return cls.__get_printable_generic_value__(val)
        return val

    @staticmethod
    def __write_list_to_file__(wlist: Sequence[str], file,
                               prefix_line: str = ""):
        file.write(prefix_line)
        for string in wlist:
            file.write(string)
