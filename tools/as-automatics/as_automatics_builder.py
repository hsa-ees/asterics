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
# @ingroup automatics_generate
# @author Philip Manke
# @brief Functions handling common tasks when building processing chains.
# -----------------------------------------------------------------------------

import os
import itertools as ittls

from shutil import copy, rmtree
from datetime import datetime

from asterics import asterics_home, automatics_home
from as_automatics_proc_chain import AsProcessingChain
from as_automatics_module import AsModule
from as_automatics_module_group import AsModuleGroup
from as_automatics_module_wrapper import AsModuleWrapper
from as_automatics_exceptions import AsFileError, AsModuleError
from as_automatics_helpers import append_to_path, minimize_name
from as_automatics_builder_templates import *

import as_automatics_logging as as_log

LOG = as_log.get_log()


##
# @addtogroup automatics_helpers
# @{


def copytree(src: str, dst: str, clobber: bool = True):
    """! @brief Copy a directory with all files and subdirectories.
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
    """! @brief Returns a set of all module types in 'chain'.
    This function returns a list containing all entity names of modules
    that are included and depended on by the passed processing chain.
    The returned list is free of duplicates."""

    unique_modules = []
    # Collect all module entity names
    for module in chain.modules:
        if module.entity_name not in unique_modules and not isinstance(
            module, AsModuleGroup
        ):
            unique_modules.append(module.entity_name)
            get_dependencies(chain, module, unique_modules)
    return unique_modules


def get_dependencies(
    chain: AsProcessingChain, module: AsModule, module_list: list
):
    """! @brief Add module dependencies of 'module' to 'module_list'.
    Recursively determine the dependencies on other AsModules of 'module',
    as stored in the attribute AsModule.dependencies.
    Adds any new dependencies found to the parameter 'module_list'.
    @param chain: The current AsProcessingChain. Used to retrieve AsModule templates.
    @param module: The module to analyse the dependencies of.
    @param module_list: Where to store additional dependencies.
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
                dep_mod = chain.library.get_module_template(
                    dep, window_module=True
                )
                if dep_mod is None:
                    LOG.error(
                        "Module '%s' not found! Required by '%s'.",
                        dep,
                        module.entity_name,
                    )
                    raise AsModuleError(
                        dep,
                        "Module not found!",
                        "Required by '{}'.".format(module.entity_name),
                    )
            # Let's go down the rabbit hole! Recursion time!
            get_dependencies(chain, dep_mod, module_list)


## @}

##
# @addtogroup automatics_generate
# @{


def prepare_output_path(
    source_path: str, output_path: str, allow_deletion: bool = False
):
    """! @brief Copy the template directory tree for a blank system to output_path.
    @param source_path: path to the folder to copy.
    @param output_path: Where to copy source_path to.
    @param allow_deletion: If output_path is not empty delete the contents if
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
                    str(err),
                )
                raise AsFileError(
                    output_path,
                    detail=str(err),
                    msg="'shutil.rmtree' failed to remove output directory!",
                )
            os.makedirs(output_path)
        else:
            raise AsFileError(
                output_path,
                "Output directory not empty!",
                "Output generation not started!",
            )
    if source_path is not None:
        LOG.info("Copying template project directory to output path...")
        try:
            copytree(source_path, output_path)
        except Exception as err:
            LOG.error(
                "Could not create system output tree in '%s'! '%s'",
                output_path,
                str(err),
            )
            raise AsFileError(
                output_path,
                detail=str(err),
                msg="Could not copy project template to output path!",
            )


def add_vears_core(
    output_path: str,
    asterics_path: str,
    use_symlinks: bool = True,
    force: bool = False,
):
    """! @brief Link or copy the VEARS IP-Core.
    VEARS is copied/linked from the ASTERICS installation to the output path.
    @param output_path: Directory to link/copy VEARS to.
    @param asterics_path: Toplevel folder of the ASTERICS installation.
    @param use_symlinks: If True, VEARS will be linked, else copied.
    @param force: If True, the link or folder will be deleted if already present."""
    vears_path = append_to_path(asterics_path, VEARS_REL_PATH)
    vears_path = os.path.realpath(vears_path)
    target = append_to_path(output_path, "VEARS", add_trailing_slash=False)

    if force and os.path.exists(target):
        if os.path.islink(target) or os.path.isfile(target):
            try:
                os.remove(target)
            except IOError as err:
                LOG.error(
                    "Could not remove file '%s'! VEARS not added!", target
                )
                raise AsFileError(
                    target,
                    "Could not remove file to link/copy VEARS!",
                    str(err),
                )
        else:
            try:
                rmtree(target)
            except IOError as err:
                LOG.error(
                    "Could not remove folder '%s'! VEARS not added!", target
                )
                raise AsFileError(
                    target,
                    "Could not remove folder to link/copy VEARS!",
                    str(err),
                )

    if use_symlinks:
        if not os.path.exists(output_path):
            try:
                os.makedirs(output_path, mode=0o755, exist_ok=True)
            except IOError as err:
                LOG.error(
                    "Could not create directory for VEARS: '%s'! - '%s'",
                    output_path,
                    str(err),
                )
                raise AsFileError(
                    output_path,
                    "Could not create directory for VEARS!",
                    str(err),
                )
        try:
            target = os.path.realpath(target)
            os.symlink(vears_path, target, target_is_directory=True)
        except IOError as err:
            LOG.error(
                "Could not create a link to the VEARS IP-Core! - '%s'", str(err)
            )
            raise AsFileError(
                target, "Could not create link to VEARS!", str(err)
            )
    else:
        try:
            os.makedirs(target, mode=0o755, exist_ok=True)
            target = os.path.realpath(target)
            copytree(vears_path, target)
        except IOError as err:
            LOG.error("Could not copy the VEARS IP-Core!")
            raise AsFileError(output_path, "Could not copy VEARS!", str(err))


def write_config_hc(chain, output_path: str):
    """! @brief Write the files 'as_config.[hc]'
    The files contain the build date, version string and configuration macros."""
    LOG.info("Generating as_config.c source file...")
    # Fetch and format todays date
    date_string = datetime.today().strftime("%Y-%m-%d")
    version_string = chain.parent.version
    hashstr = "'" + "', '".join(chain.get_hash()) + "'"
    filepath = append_to_path(
        output_path, AS_CONFIG_C_NAME, add_trailing_slash=False
    )

    try:
        with open(filepath, "w") as file:
            file.write(
                AS_CONFIG_C_TEMPLATE.format(
                    header=ASTERICS_HEADER_SW.format(
                        filename=AS_CONFIG_C_NAME,
                        description=AS_CONFIG_C_DESCRIPTION,
                    ),
                    hashstr=hashstr,
                    date=date_string,
                    version=version_string,
                )
            )
    except IOError as err:
        LOG.error("Could not write '%s'! '%s'", AS_CONFIG_C_NAME, str(err))
        raise AsFileError(
            filepath,
            detail=str(err),
            msg="Could not write to file",
        )

    LOG.info("Generating as_config.h source file...")
    filepath = append_to_path(
        output_path, AS_CONFIG_H_NAME, add_trailing_slash=False
    )
    try:
        with open(filepath, "w") as file:
            file.write(
                AS_CONFIG_H_TEMPLATE.format(
                    header=ASTERICS_HEADER_SW.format(
                        filename=AS_CONFIG_H_NAME,
                        description=AS_CONFIG_H_DESCRIPTION,
                    )
                )
            )
    except IOError as err:
        LOG.error("Could not write '%s'! '%s'", AS_CONFIG_H_NAME, str(err))
        raise AsFileError(
            filepath,
            detail=str(err),
            msg="Could not write to file",
        )


def write_asterics_h(chain: AsProcessingChain, output_path: str):
    """! @brief Write the toplevel ASTERICS driver C header
    The header contains include statements for all driver header files
    and the definition of the register ranges and base addresses."""

    LOG.info("Generating ASTERICS main software driver header file...")
    asterics_h_path = append_to_path(output_path, "/")
    include_list = set()
    include_str = ""
    include_template = '#include "{}" \n'

    module_base_reg_template = "#define AS_MODULE_BASEREG_{modname} {offset}\n"
    module_base_addr_template = (
        "#define AS_MODULE_BASEADDR_{modname} ((uint32_t*)(ASTERICS_BASEADDR + "
        "(AS_MODULE_BASEREG_{modname} * 4 * AS_REGISTERS_PER_MODULE)))\n"
    )

    # Build a list of module additions to asterics.h
    # Additions should be unique
    # (two HW instances of an ASTERICS module use the same driver)
    module_additions = set()
    for module in chain.modules:
        module_additions.update(module.get_software_additions())
    # Format module additions: One line per additional string
    module_additions = "\n".join(module_additions)
    module_additions = (
        "/************************** Module Defines and "
        "Additions ***************************/\n\n"
    ) + module_additions

    # Get list of modules
    unique_modules = get_unique_modules(chain)

    # Collect driver header files that need to be included
    def add_header(mod: AsModule):
        for driver in mod.driver_files:
            if driver.endswith(".h"):
                include_list.add(driver.rsplit("/", maxsplit=1)[-1])

    for mod in list(ittls.chain(chain.modules, chain.pipelines)):
        add_header(mod)
    for entity in unique_modules:
        mod = chain.library.get_module_template(entity)
        if mod is not None:
            add_header(mod)
    # Build include list
    include_str = "".join(
        [include_template.format(i) for i in sorted(include_list)]
    )

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
            modname=regif_modname.upper(), offset=regif.regif_num
        )
        reg_addrs += module_base_addr_template.format(
            modname=regif_modname.upper()
        )

    try:
        with open(asterics_h_path + ASTERICS_H_NAME, "w") as file:
            # Write asterics.h
            file.write(
                ASTERICS_H_TEMPLATE.format(
                    header=ASTERICS_HEADER_SW.format(
                        filename=ASTERICS_H_NAME,
                        description=ASTERICS_H_DESCRIPTION,
                    ),
                    base_addr=chain.asterics_base_addr,
                    regs_per_mod=chain.max_regs_per_module,
                    module_driver_includes=include_str,
                    base_regs=reg_bases,
                    addr_map=reg_addrs,
                    module_additions=module_additions,
                )
            )

    except IOError as err:
        print(
            "Couldn't write {}: '{}'".format(
                asterics_h_path + ASTERICS_H_NAME, err
            )
        )
        raise AsFileError(
            asterics_h_path + ASTERICS_H_NAME,
            detail=str(err),
            msg="Could not write to file",
        )


def write_vivado_package_tcl(
    chain: AsProcessingChain, output_path: str, additions_c1: str = ""
) -> bool:
    """! @brief Write two TCL script fragments sourced by the packaging TCL script.
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

    # Class to manage the AXI interface information for the TCL packaging
    # script
    class TCL_AXI_Interface:
        """'Private' class capsuling methods to write the TCL fragments
        required for the packaging script for Xilinx targets."""

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
            return BUS_IF_ASSOCIATION_TCL_TEMPLATE.format(
                busif=self.bus_if_name,
                clk=self.clock_name,
                rst=self.reset_name,
                ref=self.refname,
            )

        def get_tcl_mem_commands(self) -> str:
            """Generate the memory mapping TCL commands"""
            if any((not self.if_type, not self.memory_range)):
                LOG.debug(
                    (
                        "Generating TCL packaging script: Interface type "
                        "of slave memory range not set for '%s'!"
                    ),
                    self.bus_if_name,
                )
                return ""
            # Else ->
            return MEMORY_MAP_TCL_TEMPLATE.format(
                ref=self.refname,
                axi_type=self.if_type,
                mem_range=self.memory_range,
                busif=self.bus_if_name,
                mem_map_ref=self.refname + "_mem_ref",
            )

    LOG.info("Generating TCL packaging scripts...")
    # Generate the necessary paths:
    # IP-Core project directory
    project_dir = append_to_path(os.path.realpath(output_path), "/")
    # Subdirectory containing the HDL sources
    hdl_dir = append_to_path(project_dir, "/hw/hdl/vhdl/")

    # Populate the fragment files with a generic file header
    content1 = TCL_HEADER.format(
        TCL1_NAME, "TCL fragment (1) part of the IP packaging TCL script"
    )
    content2 = TCL_HEADER.format(
        TCL2_NAME, "TCL fragment (2) part of the IP packaging TCL script"
    )
    content3 = TCL_HEADER.format(
        TCL3_NAME, "TCL fragment (2) part of the IP packaging TCL script"
    )

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
            temp.refname = (
                minimize_name(inter.name_prefix)
                .replace(temp.axi_type.lower(), "")
                .strip("_")
            )
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
                module.get_interface("in", if_type="iic_interface").unique_name
            )
            if top_if is None:
                LOG.error(
                    (
                        "Was not able to determine port names for IIC "
                        "interface '%s' - IIC interface not found!"
                    ),
                    if_name,
                )
                mod_prefix = ""
            else:
                mod_prefix = minimize_name(
                    top_if.name_prefix, chain.NAME_FRAGMENTS_REMOVED_ON_TOPLEVEL
                )
            iic_if_inst_str.append(
                "#Instantiate interface for {}\n".format(if_name)
            )
            iic_if_inst_str.append(
                AS_IIC_MAP_TCL_TEMPLATE.format(
                    iic_signal_prefix=mod_prefix, iic_if_name=if_name
                )
            )
            iic_if_inst_str.append(
                "# END Instantiate interface for {}\n\n".format(if_name)
            )
    # Assemble the IIC interface string and add to the TCL fragment
    content2 += "\n".join(iic_if_inst_str)

    tcl_ooc_remove_outsourced_template = "set_property is_enabled false -quiet [get_files -quiet -of_objects [get_filesets sources_1] {{{files}}}]\n"

    outsourced_files = []
    ooc_modules = [
        mod for mod in chain.modules if isinstance(mod, AsModuleWrapper)
    ]
    if ooc_modules:
        tcl_ooc_commands = [
            "# Create OOC blocks\n",
            'puts "Generating Out-of-Context Synthesis Runs..."\n',
        ]
    else:
        tcl_ooc_commands = []
    count = 1
    for mod in ooc_modules:
        source_files = set()
        modfilename = mod.name + ".vhd"
        source_files.add(modfilename)
        outsourced_files.append(modfilename)
        source_files.update(mod.modules[0].files)
        dep_mods = []
        get_dependencies(chain, mod.modules[0], dep_mods)
        if dep_mods:
            for dmod in dep_mods:
                modtemplate = chain.library.get_module_template(dmod)
                source_files.update(modtemplate.files)
        source_files = (
            sf.rsplit("/", maxsplit=1)[-1] for sf in sorted(source_files)
        )
        tcl_ooc_commands.append(
            TCL_OOC_TEMPLATE.format(
                ent_name=mod.entity_name,
                source_files=" ".join(source_files),
                top_source=mod.name + ".vhd",
                progress=str(count) + " of " + str(len(ooc_modules)),
            )
        )
        count += 1
    tcl_ooc_commands.append(
        tcl_ooc_remove_outsourced_template.format(
            files=" ".join(outsourced_files)
        )
    )

    content3 += "\n".join(tcl_ooc_commands)

    # Make sure all files are newline-terminated
    content1 += "\n"
    content2 += "\n"
    content3 += "\n"

    for name, content in zip(
        (TCL1_NAME, TCL2_NAME, TCL3_NAME), (content1, content2, content3)
    ):
        try:
            with open(project_dir + name, "w") as file:
                file.write(content)
        except IOError as err:
            LOG.error("Could not write '%s' in '%s'.", name, project_dir)
            raise AsFileError(
                project_dir + name, "Could not write file!", str(err)
            )


def run_vivado_packaging(
    chain: AsProcessingChain, output_path: str, tcl_additions: str = ""
):
    """! @brief Write the necessary TCL fragments and run the TCL packaging script.
    Requires Vivado to be installed and in callable from the current terminal.
    Parameters:
    chain: The current processing chain.
    output_path: The root of the output folder structure.
    No return value."""
    # Write the necessary tcl fragments
    write_vivado_package_tcl(chain, output_path, tcl_additions)
    # Clean path
    path = append_to_path(os.path.realpath(output_path), "/")
    # Input path to launch string
    launch_string = VIVADO_TCL_COMMANDLINE_TEMPLATE.format(
        automatics_home + "/", path
    )
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
    ooc_runs_present = any(
        (isinstance(mod, AsModuleWrapper) for mod in chain.modules)
    )
    if not ooc_runs_present:
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
                LOG.warning(
                    "Packaging: Can't remove temporary file(s) '%s' - %s.",
                    target,
                    str(err),
                )
    else:
        LOG.warning(
            "Vivado Project including Out-of-Context runs generated to '{}'.".format(
                output_path
            )
        )
    LOG.info("Packaging complete!")


def gather_hw_files(
    chain: AsProcessingChain, output_folder: str, use_symlinks: bool = True
) -> bool:
    """! @brief Copy or link to module VHDL files of an ASTERICS chain.
    Collect all required hardware descriptive files
    for the current ASTERICS system. Mainly looks at the AsModule.files,
    .module_dir and .dependencies attributes to find required files.
    @param chain: current processing chain
    @param output_folder: The root of the output folder structure
    @param use_symlinks: Whether or not to link (True) or copy (False) files
    @return  True on success, else False"""

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
        if module is None:
            continue
        module_dir = os.path.realpath(module.module_dir)
        for hw_file in module.files:
            source = os.path.realpath(hw_file)
            if not hw_file.startswith("/"):
                comp = os.path.commonprefix([module_dir, source])
                if comp != module_dir:
                    # Append the file path to the module directory, cutting off '/'
                    source = append_to_path(
                        module_dir, hw_file, add_trailing_slash=False
                    )
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
                            (
                                "Could not link file '%s' of module '%s'!"
                                " - '%s'"
                            ),
                            filename,
                            entity,
                            str(err),
                        )
                        return False
                except IOError as err:
                    LOG.critical(
                        ("Could not link file '%s' of module '%s'! " "- '%s'"),
                        filename,
                        entity,
                        str(err),
                    )
                    return False
            else:
                try:
                    copy(source, dest)
                except IOError as err:
                    LOG.critical(
                        ("Could not copy file '%s' of module '%s'!" " - '%s'"),
                        filename,
                        entity,
                        str(err),
                    )
                    return False
    return True


def gather_sw_files(
    chain: AsProcessingChain,
    output_folder: str,
    use_symlinks: bool = True,
    sep_dirs: bool = False,
) -> bool:
    """! @brief Copy or link to software files for an ASTERICS chain.
    Collect all available software driver files in 'drivers' folders
    of the module source directories in the output folder structure.
    @param chain: The current AsProcessingChain. Source of the modules list.
    @param output_folder: The root of the output folder structure.
    @param use_symlinks: Whether or not to link (True) or copy (False) files
    @param sep_dirs: Whether or not to generate separate directories per module driver
    @return True on success, False otherwise."""

    LOG.info("Gathering ASTERICS module software driver source files...")
    out_path = os.path.realpath(output_folder)
    # We don't want the trailing slash if we're not using separate folders
    out_path = append_to_path(out_path, "/", sep_dirs)
    # Collect all module entity names
    unique_modules = get_unique_modules(chain)
    modules = list(ittls.chain(chain.modules, chain.pipelines))
    handled_entities = []

    # Initialize driver list with asterics support package drivers
    drivers = [
        (
            "as_support",
            list(
                asp_driver.format(asterics_root=asterics_home)
                for asp_driver in ASP_FILES
            ),
        )
    ]

    for mod in modules:
        if mod.entity_name not in handled_entities:
            drivers.append((mod.entity_name, mod.driver_files))
            handled_entities.append(mod.entity_name)

    for entity in filter(
        lambda ent: ent not in handled_entities, unique_modules
    ):
        module = chain.library.get_module_template(entity)
        drivers.append((module.entity_name, module.driver_files))

    driver_dir = {}
    for entity, paths in drivers:
        if not paths:
            continue
        try:
            driver_dir[entity].extend(paths)
        except KeyError:
            driver_dir[entity] = paths

    for entity in driver_dir:
        driverlist = driver_dir[entity]
        if sep_dirs:
            # Build destination path: out + entity name (cut off trailing '/')
            dest_path = append_to_path(out_path, entity, False)
        else:
            # If drivers should not be stored in separate directories
            dest_path = out_path
        # Linking / copying the driver files
        # Get mode of operation
        mode = "link" if use_symlinks else "copy"
        copy_op = os.symlink if use_symlinks else copy

        for driverfile in driverlist:
            filename = driverfile.rsplit("/", maxsplit=1)[-1]
            dest_file = append_to_path(dest_path, filename, False)
            if os.path.exists(dest_file):
                os.unlink(dest_file)
            try:
                copy_op(driverfile, dest_file)
            except IOError as err:
                LOG.critical(
                    ("Could not %s driver file '%s' of module '%s'!" " - '%s"),
                    mode,
                    filename,
                    entity,
                    str(err),
                )
                return False
    return True


## @}