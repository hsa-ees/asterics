# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_automatics_builder.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Functions that handle common tasks when building a hardware processing chain.
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
# @file as_automatics_builder.py
# @author Philip Manke
# @brief Functions handling common tasks when building processing chains.
# -----------------------------------------------------------------------------

import os
from shutil import copy, rmtree
from datetime import datetime

from as_automatics_proc_chain import AsProcessingChain
from as_automatics_module import AsModule
from as_automatics_exceptions import AsFileError, AsModuleError
from as_automatics_helpers import append_to_path
import as_automatics_logging as as_log
import as_automatics_helpers as as_help

LOG = as_log.get_log()


IPCORE_FOLDER = "vivado_cores/"


def copytree(src: str, dst: str, clobber: bool = True):
    """Copy a directory with all files and subdirectories.
    Not using shutil.copytree, as it raises an error when the destination
    folder already exists. This function uses shutil.copy to copy files."""
    for item in os.listdir(src):
        source = os.path.join(src, item)
        dest = os.path.join(dst, item)
        if os.path.isdir(source):
            os.makedirs(dest, 0o755, exist_ok=True)
            copytree(source, dest)
        else:
            try:
                copy(source, dest, follow_symlinks=True)
            except FileExistsError:
                if clobber:
                    os.remove(dest)
                    copy(source, dest, follow_symlinks=True)
                else:
                    pass


def get_unique_modules(chain: AsProcessingChain) -> list:
    """This function returns a list containing all entity names of modules
    that are included and depended on by the passed processing chain.
    The returned list is free of duplicates."""

    unique_modules = []
    # Collect all module entity names
    for module in chain.modules:
        if module.entity_name not in unique_modules:
            unique_modules.append(module.entity_name)
            get_dependencies(chain, module, unique_modules)
    return unique_modules


def get_dependencies(chain: AsProcessingChain, module: AsModule,
                     module_list: list):
    """Recursively determine the dependencies on other AsModules of 'module',
    as stored in the attribute AsModule.dependencies.
    Adds any new dependencies found to the parameter 'module_list'.
    Parameters:
      chain: The current AsProcessingChain. Used to retrieve AsModule templates.
      module: The module to analyse the dependencies of.
      module_list: Where to store additional dependencies.
    """
    # For all direct dependencies of 'module'
    for dep in module.dependencies:
        # Filter new dependencies
        if dep not in module_list:
            # Add to the list ...
            module_list.append(dep)
            # ... and determine further dependencies of the new dependency
            dep_mod = chain.library.get_module_template(dep)
            if dep_mod is None:
                dep_mod = chain.library.get_module_template(dep,
                                                            window_module=True)
                if dep_mod is None:
                    LOG.error("Module '%s' not found! Required by '%s'.", dep,
                            module.entity_name)
                    raise AsModuleError(dep, "Module not found!", 
                            "Required by '{}'.".format(module.entity_name))
            # Let's go down the rabbit hole! Recursion time!
            get_dependencies(chain, dep_mod, module_list)



def prepare_output_path(source_path: str, output_path: str,
                        allow_deletion: bool = False):
    """Copy the template directory tree for a blank system to output_path.
    Parameters:
      source_path: path to the folder to copy.
      output_path: Where to copy source_path to.
      allow_deletion: If output_path is not empty delete the contents if
                      allow_deletion is True, else throw an error."""
    LOG.info("Preparing output project directory...")
    if os.path.isdir(output_path) and os.listdir(output_path):
        if allow_deletion:
            LOG.info("Directory already exists! Cleaning...")
            try:
                rmtree(output_path)
            except Exception as err:
                LOG.error(
                    "Could not clean project output directory '%s'! '%s'",
                    output_path,
                    str(err))
                raise AsFileError(
                    output_path,
                    detail=str(err),
                    msg="'shutil.rmtree' failed to remove output directory!")
        else:
            raise AsFileError(output_path, "Output directory not empty!",
                              "Output generation not started!")
    if source_path is not None:
        LOG.info("Copying template project directory to output path...")
        try:
            copytree(source_path, output_path)
        except Exception as err:
            LOG.error("Could not create system output tree in '%s'! '%s'",
                      output_path, str(err))
            raise AsFileError(
                output_path,
                detail=str(err),
                msg="Could not copy project template to output path!")


VEARS_REL_PATH = "ipcores/VEARS/"


def add_vears_core(output_path: str, asterics_path: str,
                   use_symlinks: bool = True, force: bool = False):
    """Link or copy the VEARS IP-Core from the ASTERICS installation
    to the output path.
    Parameters:
      output_path: Directory to link/copy VEARS to.
      asterics_path: Toplevel folder of the ASTERICS installation.
      use_symlinks: If True, VEARS will be linked, else copied.
      force: If True, the link or folder will be deleted if already present."""
    vears_path = append_to_path(asterics_path, VEARS_REL_PATH)
    vears_path = os.path.realpath(vears_path)
    target = append_to_path(output_path, "VEARS", add_trailing_slash=False)

    if force and os.path.exists(target):
        if os.path.islink(target) or os.path.isfile(target):
            try:
                os.remove(target)
            except IOError as err:
                LOG.error("Could not remove file '%s'! VEARS not added!",
                        target)
                raise AsFileError(target,
                    "Could not remove file to link/copy VEARS!", str(err))
        else:
            try:
                rmtree(target)
            except IOError as err:
                LOG.error("Could not remove folder '%s'! VEARS not added!",
                        target)
                raise AsFileError(target,
                    "Could not remove folder to link/copy VEARS!", str(err))
        
    if use_symlinks:
        if not os.path.exists(output_path):
            try:
                os.makedirs(output_path, mode=0o755, exist_ok=True)
            except IOError as err:
                LOG.error("Could not create directory for VEARS: '%s'! - '%s'",
                          output_path, str(err))
                raise AsFileError(output_path, 
                        "Could not create directory for VEARS!", str(err))
        try:
            target = os.path.realpath(target)
            os.symlink(vears_path, target, target_is_directory=True)
        except IOError as err:
            LOG.error("Could not create a link to the VEARS IP-Core! - '%s'",
                      str(err))
            raise AsFileError(target, "Could not create link to VEARS!",
                              str(err))
    else:
        try:
            os.makedirs(target, mode=0o755, exist_ok=True)
            target = os.path.realpath(target)
            copytree(vears_path, target)
        except IOError as err:
            LOG.error("Could not copy the VEARS IP-Core!")
            raise AsFileError(output_path, "Could not copy VEARS!", str(err))


def write_config_c(output_path: str):
    """Write the file 'as_config.c', containing the build date
    and version string. Version string is currently not implemented!"""
    LOG.info("Generating as_config.c source file...")
    config_c_name = "as_config.c"
    config_c_template = ('const char *buildVersion = "{version}";\n'
                         'const char *buildDate = "{date}";\n')
    # Fetch and format todays date
    date_string = datetime.today().strftime("%Y-%m-%d")
    version_string = "TEMPORARY"

    try:
        with open(output_path + config_c_name, "w") as file:
            file.write(config_c_template.format(date=date_string,
                                                version=version_string))
    except IOError as err:
        LOG.error("Could not write 'as_config.c'! '%s'", str(err))
        raise AsFileError(output_path + config_c_name, detail=str(err),
                          msg="Could not write to file")


# Template for the ASTERICS toplevel C header file
ASTERICS_H_TEMPLATE = \
    """
/*------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework.
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
--------------------------------------------------------------------------------
-- File:           asterics.h
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Author:         ASTERICS Automatics
--
-- Description:    Driver (header file) for the ASTERICS IP core.
--                 This header file
--                  a) incorporates drivers of implemented ASTERICS modules and
--                  b) defines register mapping for low level hardware access.
--------------------------------------------------------------------------------
--  This program is free software; you can redistribute it and/or
--  modify it under the terms of the GNU Lesser General Public
--  License as published by the Free Software Foundation; either
--  version 3 of the License, or (at your option) any later version.
--  
--  This program is distributed in the hope that it will be useful,
--  but WITHOUT ANY WARRANTY; without even the implied warranty of
--  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
--  Lesser General Public License for more details.
--  
--  You should have received a copy of the GNU Lesser General Public License
--  along with this program; if not, see <http://www.gnu.org/licenses/>
--  or write to the Free Software Foundation, Inc.,
--  51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
------------------------------------------------------------------------------*/

/**
 * @file  asterics.h
 * @brief Incorporating drivers for ASTERICS IP core modules and register mapping definition.
 *
 * \\defgroup asterics_mod ASTERICS modules
 *
 */

#ifndef ASTERICS_H
#define ASTERICS_H

#ifdef __cplusplus
extern "C"
{{
#endif

#include "as_support.h"


/************************** Integrated Modules ***************************/

{module_driver_includes}

/************************** ASTERICS IP-Core Base Address ***************************/
#define ASTERICS_BASEADDR {base_addr:#8X}

#define AS_REGISTERS_PER_MODULE {regs_per_mod}

/************************** Module Register Mapping ***************************/

{base_regs}

/************************** Module Address Mapping ***************************/

{addr_map}


{module_additions}

#ifdef __cplusplus
}}
#endif

#endif /** ASTERICS_H */
"""

ASTERICS_H_NAME = "asterics.h"


def write_asterics_h(chain: AsProcessingChain, output_path: str):
    """Write the toplevel ASTERICS driver header containing include
    statements for all driver header files and the definition of the register
    ranges and base addresses."""
    LOG.info("Generating ASTERICS main software driver header file...")
    asterics_h_path = append_to_path(output_path, "/")
    include_list = ""
    include_template = '#include "{}" \n'

    module_base_reg_template = "#define AS_MODULE_BASEREG_{modname} {offset}\n"
    module_base_addr_template = (
        "#define AS_MODULE_BASEADDR_{modname} ((uint32_t*)(ASTERICS_BASEADDR + "
        "(AS_MODULE_BASEREG_{modname} * 4 * AS_REGISTERS_PER_MODULE)))\n")

    # Build a list of module additions to asterics.h
    # Additions should be unique 
    # (two HW instances of an ASTERICS module use the same driver)
    module_additions = set()
    for module in chain.modules:
        module_additions.update(module.get_software_additions())
    # Format module additions: One line per additional string
    module_additions = "\n".join(module_additions)
    module_additions = ("/************************** Module Defines and "
                        "Additions ***************************/\n\n") \
                       + module_additions

    # Get list of modules
    unique_modules = get_unique_modules(chain)

    # Collect driver header files that need to be included
    for entity in unique_modules:
        module = chain.library.get_module_template(entity)
        driver_path = module.module_dir + "software/driver/"
        if not os.path.isdir(driver_path):
            continue
        for file in os.listdir(driver_path):
            if file[-2:] == ".h":
                if not any(file in include for include in include_list):
                    include_list += include_template.format(file)

    # Register base definition list and register range order
    reg_bases = ""
    reg_addrs = ""
    # Generate register definitions
    for addr in chain.address_space:
        # Get register interface object
        regif = chain.address_space[addr]
        # Build register interface module name
        regif_modname = regif.parent.name
        if regif.name_suffix:
            regif_modname += regif.name_suffix
        reg_bases += module_base_reg_template.format(
            modname=regif_modname.upper(),
            offset=regif.regif_num)
        reg_addrs += module_base_addr_template.format(
            modname=regif_modname.upper())

    try:
        with open(asterics_h_path + ASTERICS_H_NAME, "w") as file:
            # Write asterics.h
            file.write(ASTERICS_H_TEMPLATE.format(
                base_addr=chain.asterics_base_addr,
                regs_per_mod=chain.max_regs_per_module,
                module_driver_includes=include_list,
                base_regs=reg_bases, addr_map=reg_addrs,
                module_additions=module_additions))

    except IOError as err:
        print("Couldn't write {}: '{}'".format(
            asterics_h_path + ASTERICS_H_NAME, err))
        raise AsFileError(asterics_h_path + ASTERICS_H_NAME, detail=str(err),
                          msg="Could not write to file")


# Generic file header, adapted for TCL files
TCL_HEADER = \
    """
#------------------------------------------------------------------------------
#-  This file is part of the ASTERICS Framework.
#-  (C) 2019 Hochschule Augsburg, University of Applied Sciences
#-------------------------------------------------------------------------------
#- File:           {}
#-
#- Company:        University of Applied Sciences, Augsburg, Germany
#- Author:         ASTERICS Automatics
#-
#- Description:    {}
#-------------------------------------------------------------------------------
#- This program is free software; you can redistribute it and/or
#- modify it under the terms of the GNU Lesser General Public
#- License as published by the Free Software Foundation; either
#- version 3 of the License, or (at your option) any later version.
#- 
#- This program is distributed in the hope that it will be useful,
#- but WITHOUT ANY WARRANTY; without even the implied warranty of
#- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#- Lesser General Public License for more details.
#- 
#- You should have received a copy of the GNU Lesser General Public License
#- along with this program; if not, see <http://www.gnu.org/licenses/>
#- or write to the Free Software Foundation, Inc.,
#- 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#-----------------------------------------------------------------------------*/

"""

# Names for the TCL fragments
TCL1_NAME = "package_config.tcl"
TCL2_NAME = "package_interface_config.tcl"
# Path in the project directory to store the TCL fragments in
TCL_FOLDER = "vivado_cores/ASTERICS/"


def write_vivado_package_tcl(chain: AsProcessingChain,
                             output_path: str, additions_c1: str = "") -> bool:
    """Write two TCL script fragments sourced by the packaging TCL script.
    This function generates Vivado-specific TCL commands!
    The first fragment is sourced very early in the packaging script and
    contains basic information like the project directory,
    source file directory, etc.
    The second fragment contains packaging commands setting up the
    AXI interface configuration.
    This function needs to access the toplevel modules in the current
    processing chain to generate the TCL code.

    Parameters:
    chain - AsProcessingChain: The current processing chain to build
    output_path - String: Toplevel folder of the current project
    Returns a boolean value: True on success, False otherwise"""

    as_iic_map_tcl_template = (
        "# Set up interface properties:\n"
        "ipx::add_bus_interface {iic_if_name} [ipx::current_core]\n"
        "set_property abstraction_type_vlnv xilinx.com:interface:iic_rtl:1.0 "
        "[ipx::get_bus_interfaces {iic_if_name} -of_objects [ipx::current_core]]\n"
        "set_property bus_type_vlnv xilinx.com:interface:iic:1.0 "
        "[ipx::get_bus_interfaces {iic_if_name} -of_objects [ipx::current_core]]\n"
        "set_property interface_mode master "
        "[ipx::get_bus_interfaces {iic_if_name} -of_objects [ipx::current_core]]\n"
        "set_property display_name asterics_{iic_if_name} "
        "[ipx::get_bus_interfaces {iic_if_name} -of_objects [ipx::current_core]]\n"
        "# IIC port mapping:\n"
        "ipx::add_port_map SCL_T [ipx::get_bus_interfaces {iic_if_name} "
        "-of_objects [ipx::current_core]]\n"
        "set_property physical_name {iic_signal_prefix}scl_out_enable "
        "[ipx::get_port_maps SCL_T -of_objects "
        "[ipx::get_bus_interfaces {iic_if_name} -of_objects [ipx::current_core]]]\n"
        "ipx::add_port_map SDA_O [ipx::get_bus_interfaces {iic_if_name} "
        "-of_objects [ipx::current_core]]\n"
        "set_property physical_name {iic_signal_prefix}sda_out "
        "[ipx::get_port_maps SDA_O -of_objects "
        "[ipx::get_bus_interfaces {iic_if_name} -of_objects [ipx::current_core]]]\n"
        "ipx::add_port_map SDA_I [ipx::get_bus_interfaces {iic_if_name} "
        "-of_objects [ipx::current_core]]\n"
        "set_property physical_name {iic_signal_prefix}sda_in "
        "[ipx::get_port_maps SDA_I -of_objects "
        "[ipx::get_bus_interfaces {iic_if_name} -of_objects [ipx::current_core]]]\n"
        "ipx::add_port_map SDA_T [ipx::get_bus_interfaces {iic_if_name} "
        "-of_objects [ipx::current_core]]\n"
        "set_property physical_name {iic_signal_prefix}sda_out_enable "
        "[ipx::get_port_maps SDA_T -of_objects "
        "[ipx::get_bus_interfaces {iic_if_name} -of_objects [ipx::current_core]]]\n"
        "ipx::add_port_map SCL_O [ipx::get_bus_interfaces {iic_if_name}"
        " -of_objects [ipx::current_core]]\n"
        "set_property physical_name {iic_signal_prefix}scl_out "
        "[ipx::get_port_maps SCL_O -of_objects "
        "[ipx::get_bus_interfaces {iic_if_name} -of_objects [ipx::current_core]]]\n"
        "ipx::add_port_map SCL_I [ipx::get_bus_interfaces {iic_if_name} "
        "-of_objects [ipx::current_core]]\n"
        "set_property physical_name {iic_signal_prefix}scl_in "
        "[ipx::get_port_maps SCL_I -of_objects "
        "[ipx::get_bus_interfaces {iic_if_name} -of_objects [ipx::current_core]]]\n")

    # Class to manage the AXI interface information for the TCL packaging
    # script
    class TCL_AXI_Interface():
        """'Private' class capsuling methods to write the TCL fragments
        required for the packaging script for Xilinx targets."""
        # TCL command templates:
        bus_if_association_tcl_template = (
            "ipx::associate_bus_interfaces -clock {clk} -busif {busif} -clear "
            "[ipx::current_core]\n"
            "# ^ Dissassociate any signals with this AXI interface"
            " (to be save)\n"
            "# Associate the correct clock and reset signals\n"
            "ipx::associate_bus_interfaces -clock {clk} -reset {rst} "
            "-busif {busif} [ipx::current_core]\n"
            "# Store the interface object in a variable with known name\n"
            "set {ref} [ipx::get_bus_interfaces -of_objects "
            "[ipx::current_core] {busif}]\n")
        memory_map_tcl_template = \
            ("ipx::remove_memory_map slave_s_axi [ipx::current_core]\n"
             "ipx::remove_memory_map {ref} [ipx::current_core]\n"
             "# ^ Remove any memory maps from the interface\n"
             "# (potentially) Re-add a memory map\n"
             "ipx::add_memory_map {mem_map_ref} [ipx::current_core]\n"
             "# Add a slave memory map reference\n"
             "set_property slave_memory_map_ref {mem_map_ref} ${ref}\n"
             "# Add an address block to the memory map "
             "using the above reference\n"
             "ipx::add_address_block {{{axi_type}}} [ipx::get_memory_maps "
             "{mem_map_ref} -of_objects [ipx::current_core]]\n"
             "# Set the address block range\n"
             "set_property range {{{mem_range}}} [ipx::get_address_blocks "
             "{{{axi_type}}} -of_objects [ipx::get_memory_maps "
             "{{{mem_map_ref}}}  -of_objects [ipx::current_core]]]\n")

        

        def __init__(self, axi_type: str):
            # Type of AXI interface ("AXI Slave" / "AXI Master")
            self.axi_type = axi_type
            self.refname = ""  # Variable name of this interface
            self.bus_if_name = ""  # Name of this bus interface in Vivado TCL
            self.clock_name = "_aclk"  # Name of the associated clock
            self.reset_name = "_aresetn"  # Name of the associated reset
            self.if_type = ""  # AXI slave register address block name (Slave)
            self.memory_range = 0  # Range of the address block (Slave)

        def update(self):
            """Update the clock and reset names
            after setting the bus interface name"""
            self.clock_name = self.bus_if_name + self.clock_name
            self.reset_name = self.bus_if_name + self.reset_name

        def get_tcl_bus_assoc_commands(self) -> str:
            """Generate the bus interface association TCL commands"""
            return self.bus_if_association_tcl_template \
                .format(busif=self.bus_if_name, clk=self.clock_name,
                        rst=self.reset_name, ref=self.refname)

        def get_tcl_mem_commands(self) -> str:
            """Generate the memory mapping TCL commands"""
            if any((not self.if_type, not self.memory_range)):
                LOG.debug(("Generating TCL packaging script: Interface type "
                           "of slave memory range not set for '%s'!"),
                          self.bus_if_name)
                return ""
            # Else ->
            return self.memory_map_tcl_template .format(
                ref=self.refname,
                axi_type=self.if_type,
                mem_range=self.memory_range,
                busif=self.bus_if_name,
                mem_map_ref=self.refname + "_mem_ref")

    LOG.info("Generating TCL packaging scripts...")
    # Generate the necessary paths:
    # IP-Core project directory
    project_dir = append_to_path(os.path.realpath(output_path), "/")
    # Subdirectory containing the HDL sources
    hdl_dir = append_to_path(project_dir, "/hw/hdl/vhdl/")

    # Populate the fragment files with a generic file header
    content1 = TCL_HEADER.format(
        TCL1_NAME, "TCL fragment (1) part of the IP packaging TCL script")
    content2 = TCL_HEADER.format(
        TCL2_NAME, "TCL fragment (2) part of the IP packaging TCL script")

    # Generate the commands for the first basic fragment
    content1 += "\nset projdir " + project_dir
    content1 += "\nset hdldir " + hdl_dir
    if additions_c1:
        content1 += "\n" + additions_c1 + "\n"

    # Possible AXI interface types
    templates = ("AXI_Slave", "AXI_Master")

    for inter in chain.top.interfaces:
        temp = None
        if inter.type.lower() in ("axi_slave_external", "axi_master_external"):
            slave = templates[0] in inter.type
            if slave:
                # For AXI slaves: Populate the TCL AXI class
                temp = TCL_AXI_Interface(templates[0])
                # And set parameters for the memory map (slave registers)
                temp.memory_range = 65536
                temp.if_type = "axi_lite"
            else:
                temp = TCL_AXI_Interface(templates[1])
            temp.refname = as_help.minimize_name(inter.name_prefix) \
                    .replace(temp.axi_type.lower(), "").strip("_")
            temp.bus_if_name = inter.ports[0].code_name.rsplit("_", 1)[0]
            

            # Set the reference name and update the clock and reset names
            temp.update()
            # Generate the bus association commands for all interfaces
            content2 += temp.get_tcl_bus_assoc_commands()
            if slave:
                # Only slaves have a memory map
                content2 += temp.get_tcl_mem_commands()
    
    # Build interface instantiation strings for as_iic modules
    iic_if_inst_str = ["\n"]
    for module in chain.modules:
        if module.entity_name == "as_iic":
            if_name = module.name
            top_if = chain.top.__get_interface_by_un_fuzzy__(
                module.get_interface("in", if_type="iic_interface").unique_name)
            if top_if is None:
                LOG.error(("Was not able to determine port names for IIC "
                           "interface '%s' - IIC interface not found!"),
                          if_name)
                mod_prefix = ""
            else:
                mod_prefix = as_help.minimize_name(top_if.name_prefix,
                        chain.NAME_FRAGMENTS_REMOVED_ON_TOPLEVEL)
            iic_if_inst_str.append("#Instantiate interface for {}\n"
                                   .format(if_name))
            iic_if_inst_str.append(
                as_iic_map_tcl_template.format(
                    iic_signal_prefix=mod_prefix,
                    iic_if_name=if_name))
            iic_if_inst_str.append("# END Instantiate interface for {}\n\n"
                                   .format(if_name))
    # Assemble the IIC interface string and add to the TCL fragment
    content2 += "\n".join(iic_if_inst_str)

    # Make sure both files are newline-terminated
    content1 += "\n"
    content2 += "\n"

    # Write fragment 1
    try:
        with open(project_dir + TCL1_NAME, "w") as file:
            file.write(content1)
    except IOError as err:
        LOG.error("Could not write '%s' in '%s'.", TCL1_NAME, project_dir)
        raise AsFileError(project_dir + TCL1_NAME, "Could not write file!",
                          str(err))

    # Write fragment 2
    try:
        with open(project_dir + TCL2_NAME, "w") as file:
            file.write(content2)
    except IOError as err:
        LOG.error("Could not write '%s' in '%s'.", TCL2_NAME, project_dir)
        raise AsFileError(project_dir + TCL2_NAME, "Could not write file!",
                          str(err))


VIVADO_TCL_COMMANDLINE_TEMPLATE = (
    'ees-vivado -mode tcl -source {}packaging.tcl '
    '-notrace -tclargs "{}package_config.tcl"')

HOUSE_CLEANING_LIST_VIVADO = ("package_interface_config.tcl",
                              "package_config.tcl",
                              "asterics.hw",
                              "asterics.cache",
                              "asterics.ip_user_files",
                              "asterics.xpr",
                              "asterics.zip",
                              "vivado.log",
                              "vivado.jou")


def run_vivado_packaging(chain: AsProcessingChain, output_path: str,
                         tcl_additions: str = ""):
    """Write the necessary TCL fragments and then run the TCL packaging script.
    Requires Vivado to be installed and in callable from the current terminal.
    Parameters:
    chain: The current processing chain.
    output_path: The root of the output folder structure.
    No return value."""
    # Write the necessary tcl fragments
    write_vivado_package_tcl(chain, output_path, tcl_additions)
    # Clean path
    path = append_to_path(os.path.realpath(output_path), "/")
    # Get automatics home directory
    auto_path = append_to_path(chain.library.asterics_dir,
                               "tools/as-automatics")
    # Input path to launch string
    launch_string = VIVADO_TCL_COMMANDLINE_TEMPLATE.format(auto_path, path)
    cwd = os.getcwd()

    LOG.info("Running Vivado IP-Core packaging...")
    try:
        # Move to output path
        os.chdir(output_path)
        # Launch Vivado there, packaging the IP Core
        os.system(launch_string)
        # Move back home
        os.chdir(cwd)
    except Exception as err:
        LOG.critical("Packaging via Vivado has failed!\nError: '%s'", str(err))
        raise err
    # Cleanup
    for target_suf in HOUSE_CLEANING_LIST_VIVADO:
        target = append_to_path(output_path, target_suf, False)
        # Choose remove function
        if os.path.isdir(target):
            rm_op = rmtree
        else:
            rm_op = os.unlink
        # Try to remove file/directory
        try:
            rm_op(target)
        except FileNotFoundError:
            pass  # This is fine, we wanted it gone anyways ;)
        except IOError as err:
            LOG.warning("Packaging: Can't remove temporary file(s) '%s' - %s.",
                        target, str(err))
    LOG.info("Packaging complete!")


def gather_hw_files(chain: AsProcessingChain, output_folder: str,
                    use_symlinks: bool = True) -> bool:
    """Collect all required hardware descriptive files
    for the current ASTERICS system. Mainly looks at the AsModule.files,
    .module_dir and .dependencies attributes to find required files.
    Parameters:
    chain: current processing chain
    output_folder: The root of the output folder structure
    Returns True on success, else False"""

    LOG.info("Gathering HDL source files...")
    out_path = os.path.realpath(output_folder)

    # Collect all module entity names
    unique_modules = get_unique_modules(chain)

    for entity in unique_modules:
        this_path = append_to_path(out_path, entity)
        try:
            os.makedirs(this_path, 0o755, exist_ok=True)
        except FileExistsError:
            pass
        module = chain.library.get_module_template(entity)
        module_dir = os.path.realpath(module.module_dir)
        for hw_file in module.files:
            source = os.path.realpath(hw_file)
            comp = os.path.commonprefix([module_dir, source])

            if comp != module_dir:
                # Append the file path to the module directory, cutting off '/'
                source = append_to_path(module_dir, hw_file)[:-1]
            if not os.path.isfile(source):
                raise AsFileError(source, "File not found!")
            filename = source.rsplit("/", maxsplit=1)[-1]
            dest = this_path + filename

            LOG.debug("Gather HW files: Link '%s' to '%s'", source, dest)

            if use_symlinks:
                # Try to create a symlink
                try:
                    os.symlink(source, dest)
                except FileExistsError:
                    # If a symlink already exists, delete it and retry
                    os.unlink(dest)
                    try:
                        os.symlink(source, dest)
                    except IOError as err:
                        LOG.critical(
                            ("Could not link file '%s' of module '%s'!"
                             " - '%s'"), filename, entity, str(err))
                        return False
                except IOError as err:
                    LOG.critical(("Could not link file '%s' of module '%s'! "
                                  "- '%s'"), filename, entity, str(err))
                    return False
            else:
                try:
                    copy(source, dest)
                except IOError as err:
                    LOG.critical(("Could not copy file '%s' of module '%s'!"
                                  " - '%s'"), filename, entity, str(err))
                    return False
    return True


def gather_sw_files(chain: AsProcessingChain, output_folder: str,
                    use_symlinks: bool = True, sep_dirs: bool = False) -> bool:
    """Collect all available software driver files in 'drivers' folders
    of the module source directories in the output folder structure.
    Parameters:
      chain: The current AsProcessingChain. Source of the modules list.
      output_folder: The root of the output folder structure.
    Returns True on success, False otherwise."""
    LOG.info("Gathering ASTERICS module software driver source files...")
    out_path = os.path.realpath(output_folder)
    # We don't want the trailing slash if we're not using separate folders
    out_path = append_to_path(out_path, "/", sep_dirs)
    # Collect all module entity names
    unique_modules = get_unique_modules(chain)

    for entity in unique_modules:
        module = chain.library.get_module_template(entity)
        source_path = os.path.realpath(append_to_path(module.module_dir,
                                                      "/software/driver/"))
        if not os.path.exists(source_path):
            # If driver folder not present:
            # This module doesn't need drivers -> skip
            LOG.debug(("Gather SW files: Skipped '%s' (%s): "
                       "Directory doesn't exist."), entity, source_path)
            continue

        if sep_dirs:
            # Build destination path: out + entity name (cut off trailing '/')
            dest_path = append_to_path(out_path, entity, False)
        else:
            # If drivers should not be stored in separate directories
            dest_path = out_path

        # Linking / copying the driver folders / files
        if use_symlinks and sep_dirs:
            LOG.debug("Gather SW files: Link '%s' to '%s'",
                      source_path, dest_path)
            try:
                os.symlink(source_path, dest_path, target_is_directory=True)
            except FileExistsError:
                os.unlink(dest_path)
                try:
                    os.symlink(source_path, dest_path,
                               target_is_directory=True)
                except IOError as err:
                    LOG.critical(
                        "Could not link drivers of module '%s'! - '%s",
                        entity,
                        str(err))
                    return False
            except IOError as err:
                LOG.critical("Could not link drivers of module '%s'! - '%s",
                             entity, str(err))
                return False
        elif not use_symlinks and sep_dirs:
            LOG.debug("Gather SW files: Copy '%s' to '%s'",
                      source_path, dest_path)
            try:
                os.makedirs(dest_path, 0o755)
            except FileExistsError:
                rmtree(dest_path)
                os.makedirs(dest_path, 0o755)
            try:
                copytree(source_path, dest_path)
            except IOError as err:
                LOG.critical("Could not copy drivers of module '%s'! - '%s",
                             entity, str(err))
                return False
        else:
            # Get mode of operation
            mode = "link" if use_symlinks else "copy"
            copy_op = os.symlink if use_symlinks else copy

            LOG.debug("Gather SW files: %sing drivers of module '%s'...",
                      mode.title(), entity)
            # For every drive file
            for sw_file in os.listdir(source_path):
                source_file = append_to_path(source_path, sw_file, False)
                if use_symlinks:
                    dest = append_to_path(dest_path, sw_file, False)
                else:
                    dest = dest_path
                # try to copy/link
                try:
                    copy_op(source_file, dest)
                # Remove existing files on error
                except FileExistsError:
                    os.unlink(append_to_path(dest_path, sw_file, False))
                    # Retry copy/link
                    try:
                        copy_op(source_file, dest)
                    except IOError as err:
                        LOG.critical(
                            ("Could not %s driver file '%s' of module '%s'!"
                             " - '%s"), mode, sw_file, entity, str(err))
                        return False
                except IOError as err:
                    LOG.critical(
                        ("Could not %s driver file '%s' of module '%s'"
                         "! - '%s"), mode, sw_file, entity, str(err))
                    return False
    return True
