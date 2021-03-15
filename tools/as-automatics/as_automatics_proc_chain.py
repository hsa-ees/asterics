# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_automatics_proc_chain.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Class representing an ASTERICS processing chain.
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
# @file as_automatics_proc_chain.py
# @ingroup automatics_mngmt
# @ingroup automatics_connection
# @author Philip Manke
# @brief Class representing an ASTERICS processing chain.
# -----------------------------------------------------------------------------

import time
import copy
import math
import itertools as ittls

from typing import Sequence
from collections import namedtuple
from hashlib import sha256

from asterics import is_vivado_available
from as_automatics_module import AsModule
from as_automatics_module_group import AsModuleGroup
from as_automatics_port import Port, StandardPort
from as_automatics_signal import GlueSignal, GenericSignal
from as_automatics_interface import Interface
from as_automatics_module_lib import AsModuleLibrary
from as_automatics_generic import Generic
from as_automatics_templates import AsMain, AsTop
from as_automatics_2d_pipeline import As2DWindowPipeline
from as_automatics_exceptions import (
    AsConnectionError,
    AsModuleError,
    AsTextError,
    AsError,
)
from as_automatics_helpers import extract_generics, foreach

import as_automatics_logging as as_log
import as_automatics_connection_helper as as_conh

# Get logging object reference
LOG = as_log.get_log()


## @ingroup automatics_intrep
class AsProcessingChain:
    """! @brief Class representing an entire ASTERICS processing chain.
    This class contains and handles all information
    necessary to fully define and generate an ASTERICS processing chain."""

    # namedtuple template for port-to-port connections
    Connection = namedtuple("Connection", "source sink")

    # Error manager:
    err_mgr = None

    # Addresses per register, determined by register size and addressing scheme
    addr_per_reg = 4
    asterics_base_addr = 0x43C10000

    NAME_FRAGMENTS_REMOVED_ON_TOPLEVEL = ("as", "main")

    def __init__(self, module_lib: AsModuleLibrary, parent):
        self.parent = parent
        self.library = module_lib
        self.top = AsTop(self)
        self.as_main = AsMain(self.top, self)
        self.module_groups = [self.as_main]
        self.modules = []
        self.user_cons = []
        self.address_space = {}
        self.max_regs_per_module = 0
        self.cur_addr = 0
        self.mod_addr_width = 0
        self.reg_addr_width = 0
        self.asterics_top_addr = self.asterics_base_addr + 0x0000FFFF
        self.auto_inst_done = False
        self.auto_connect_run = False
        self.auto_instantiated = None
        self.pipelines = []
        for module in [self.as_main, self.top]:
            for inter in module.interfaces:
                # Assign a unique name to all interfaces, so that two as_streams
                # for example, don't have the same name, append the module name
                as_conh.set_unique_name(inter, module)

    ##
    # @addtogroup automatics_cds
    # @{

    def set_asterics_base_address(
        self, base_address: int, address_space_size: int = 0xFFFF
    ):
        """! @brief Define the base address for ASTERICS to use.
        Allows setting of the base address and the address space size of
        ASTERICS in the user script."""
        self.asterics_base_addr = base_address
        self.asterics_top_addr = base_address + address_space_size

    def get_hash(self) -> str:
        """! @brief Provide a SHA256 hash based on the configuration of this processing chain.
        Can be used to identify this ASTERICS processing chain."""
        hashgen = sha256()
        string = [self.parent.version]
        for mod in self.modules:
            string.append(mod.name + mod.entity_name)
            for gen in mod.generics:
                string.append(gen.code_name + str(gen.get_value()))
        for modg in self.module_groups:
            for gen in mod.generics:
                string.append(gen.code_name + str(gen.get_value()))
            for sig in modg.signals:
                string.append(sig.code_name)
        for mod in self.top.modules:
            string.append(mod.name + mod.entity_name)
        string = "".join(string)
        hashgen.update(string.encode())
        return hashgen.hexdigest()

    ## @ingroup automatics_generate
    def write_hw(
        self, path: str, use_symlinks: bool = True, force: bool = False
    ):
        """! @brief Generate the VHDL hardware files of this ASTERICS chain.
        Wrapper function for AsAutomatics._write_hw.
        If necessary, auto_connect() is called before exporting the output.
        Generate the VHDL files and collect all VHDL source files
        of the ASTERICS hardware modules in this processing chain.
        @param path: String - Where to put the output. Relative or static path.
        @param use_symlinks: Whether to copy or link to source files.
        @param force: If 'True', deletes anything in the output directory.
        """
        if not self.auto_connect_run:
            try:
                self.auto_connect()
            except AsError:
                return False

        if self.err_mgr.has_errors():
            LOG.critical("Abort! Errors occurred during system build:")
            self.err_mgr.print_errors()
            return False
        return self.parent._write_hw(path, use_symlinks, allow_deletion=force)

    ## @ingroup automatics_generate
    def write_sw(
        self,
        path: str,
        use_symlinks: bool = True,
        force: bool = False,
        module_driver_dirs: bool = False,
    ):
        """! @brief Generate the C software files of this ASTERICS chain.
        Wrapper function for AsAutomatics._write_sw.
        If necessary, auto_connect() is cis_vivado_availablealled before exporting the output.
        Generate the C and header files and collect all driver source files
        of the ASTERICS hardware modules in this processing chain.
        @param path: String - Where to put the output. Relative or static path.
        @param use_symlinks: Whether to copy or link to source files.
        @param force: If 'True', deletes anything in the output directory.
        @param module_driver_dirs: Sort drivers into subfolders per module.
        """
        if not self.auto_connect_run:
            try:
                self.auto_connect()
            except AsError:
                return False

        if self.err_mgr.has_errors():
            LOG.critical("Abort! Errors occurred during system auto-connect:")
            self.err_mgr.print_errors()
            return False
        return self.parent._write_sw(
            path,
            use_symlinks,
            allow_deletion=force,
            module_driver_dirs=module_driver_dirs,
        )

    ## @ingroup automatics_generate
    def write_asterics_core(
        self,
        path: str,
        use_symlinks: bool = True,
        force: bool = False,
        module_driver_dirs: bool = False,
    ):
        """! @brief Generate the hardware and software files of this ASTERICS chain.
        Wrapper function for AsAutomatics._write_asterics_core.
        If necessary, auto_connect() is called before exporting the output.
        Generate and collect all source files that are necessary to build
        this ASTERICS IP core.
        @param path: String - Where to put the output. Relative or static path.
        @param use_symlinks: Whether to copy or link to source files.
        @param force: If 'True', deletes anything in the output directory.
        @param module_driver_dirs: Sort drivers into subfolders per module.
        """
        if not self.auto_connect_run:
            try:
                self.auto_connect()
            except AsError:
                self.err_mgr.print_errors()
                return False
        if self.err_mgr.has_errors():
            LOG.critical("Abort! Errors occurred during system auto-connect:")
            self.err_mgr.print_errors()
            return False
        try:
            return self.parent._write_asterics_core(
                path,
                use_symlinks,
                allow_deletion=force,
                module_driver_dirs=module_driver_dirs,
            )
        except AsError:
            LOG.critical("Abort! Errors occurred during system build:")
            self.err_mgr.print_errors()
        except IOError:
            LOG.critical("IO error occurred!")
        return False

    ## @ingroup automatics_generate
    def write_ip_core_xilinx(
        self,
        path: str,
        use_symlinks: bool = True,
        force: bool = False,
        module_driver_dirs: bool = False,
    ):
        """! @brief Generate this ASTERICS chain as a IP-XACT IP-Core.
        Wrapper function for AsAutomatics._write_ip_core_xilinx.
        If necessary, auto_connect() is called before exporting the output.
        Generate and collect all source files that are necessary to build
        this ASTERICS IP core.
        Uses a directory structure compatible with Vivado IP-Cores and
        runs Vivado to generate the meta-files, making it an IP-Core.
        @param path: String - Where to put the output. Relative or static path.
        @param use_symlinks: Whether to copy or link to source files.
        @param force: If 'True', deletes anything in the output directory.
        @param module_driver_dirs: Sort drivers into subfolders per module.
        """
        if not is_vivado_available:
            LOG.critical(
                (
                    "Vivado is not sourced!"
                    "Either source Vivado directly"
                    "or set the environment variable 'EES_VIVADO_SETTINGS'"
                    "to the path of Vivado's settings file."
                    "Aborting..."
                )
            )
            raise EnvironmentError("Vivado not in PATH!")
        if not self.auto_connect_run:
            try:
                self.auto_connect()
            except AsError:
                return False
        if self.err_mgr.has_errors():
            LOG.critical("Abort! Errors occurred during system auto-connect:")
            self.err_mgr.print_errors()
            return False
        return self.parent._write_ip_core_xilinx(
            path,
            use_symlinks,
            allow_deletion=force,
            module_driver_dirs=module_driver_dirs,
        )

    ## @ingroup automatics_generate
    def write_system(
        self,
        path: str,
        use_symlinks: bool = True,
        force: bool = False,
        module_driver_dirs: bool = False,
        add_vears: bool = False,
    ):
        """! @brief Generate this ASTERICS chain as a IP-XACT IP-Core in a system directory template.
        Wrapper function for AsAutomatics._write_system.
        If necessary, auto_connect() is called before exporting the output.
        Generate and package the ASTERICS IP-Core into an FPGA system
        directory template. Optionally add the VEARS IP-Core.
        @param path: String - Where to put the output. Relative or static path.
        @param use_symlinks: Whether to copy or link to source files.
        @param force: If 'True', deletes anything in the output directory.
        @param module_driver_dirs: Sort drivers into subfolders per module.
        @param add_vears: Link or copy VEARS (video output) into the system.
        """

        if not is_vivado_available:
            LOG.critical("Vivado is not sourced! Aborting...")
            raise EnvironmentError("Vivado not in PATH!")

        if not self.auto_connect_run:
            try:
                self.auto_connect()
            except AsError:
                return False

        if self.err_mgr.has_errors():
            LOG.critical("Abort! Errors occurred during system auto-connect:")
            self.err_mgr.print_errors()
            return False
        return self.parent._write_system(
            path,
            use_symlinks,
            allow_deletion=force,
            module_driver_dirs=module_driver_dirs,
            add_vears=add_vears,
        )

    ## @ingroup automatics_generate
    def write_system_graph(
        self,
        out_file: str = "asterics_graph",
        show_toplevels: bool = False,
        show_auto_inst: bool = False,
        show_ports: bool = False,
        show_unconnected: bool = False,
        show_line_buffers: bool = False,
    ):
        """! @brief Generate an SVG graph of this ASTERICS processing chain.
        Wraps as_automatics_visual::system_graph().
        Generates and writes a graph representation of the ASTERICS chain
        and, if present, the 2D Window Pipelines using GraphViz Dot.
        @param out_file: Path and filename of the graph to generate.
                         Default=[asterics_graph]
        @param show_toplevels: Include the toplevel module groups. [False]
        @param show_auto_inst: Include the automatically included modules. [False]
        @param show_ports: Add all ports to the interface edges. [False]
        @param show_unconnected: Write a list of unconnected ports into the module
                                 nodes. WARNING: Many false positives! [False]
        @param show_line_buffers  Add a representation for row buffers for
                2D Window Pipeline subsystems.
                Note: This feature is not tested / in alpha stage of development.
        """
        if not self.auto_connect_run:
            try:
                self.auto_connect()
            except AsError:
                return False

        if self.err_mgr.has_errors():
            LOG.critical("Abort! Errors occurred during system auto-connect:")
            self.err_mgr.print_errors()
            return False

        self.parent._write_system_graph(
            self,
            out_file,
            show_toplevels,
            show_auto_inst,
            show_ports,
            show_unconnected,
            show_line_buffers,
        )

    def add_module(
        self,
        entity_name: str,
        module_name: str = "",
        repo_name: str = "",
        *,
        group=None
    ) -> AsModule:
        """! @brief Add an ASTERICS module to this processing chain.
        Add a copy of an as_automatics_module::AsModule from the
        as_automatics_module_lib::AsModuleLibrary to this instance
        of the AsProcessingChain. A custom name can be given to the module.
        If none is provided, a consecutive number is appended to the
        standard module name (the name of the VHDL entity).
        @param entity_name  The entity name of the module to add
        @param module_name  The user name to assign to the new module (optional)
        @param repo_name  The repository to search for the module in (optional)
        @return  A reference to the newly added module.
        """
        LOG.debug(
            "Chain: Adding module '%s' to processing chain as '%s' ...",
            entity_name,
            module_name,
        )

        # TODO: Test support for module groups once that feature is implemented
        if group is None:
            group = self.as_main
        # group = self.as_main

        entity_name = entity_name.lower()
        # Get the reference for the module to add from the library
        module = self.library.get_module_instance(entity_name, repo_name)
        if not module:
            raise AsModuleError(
                module_name=entity_name,
                msg=(
                    "Could not find a module with "
                    "this name in the module library!"
                ),
            )
        # Give the module a name, if none was provided
        if module_name == "":
            module_list = self.modules
            # Naming scheme: module's entity_name + "_" + module type count
            module_name = "{}_{}".format(
                entity_name,
                sum(
                    [1 for mod in module_list if entity_name == mod.entity_name]
                ),
            )
        module.name = module_name
        # Add the module to this chains list of modules
        module.assign_to(group)
        module.chain = self
        group.modules.append(module)
        self.modules.append(module)

        for inter in module.interfaces:
            # Assign a unique name to all interfaces, so that two as_streams
            # for example, don't have the same name, append the module name
            as_conh.set_unique_name(inter, module)
        LOG.info(
            "Module '%s' added to chain as '%s'.", entity_name, module_name
        )
        return module

    def get_module(self, module_name: str) -> AsModule:
        """! @brief Search this ASTERICS chain for a module and return it.
        Return the first module of the current processing chain
        that matches the name 'module_name'. If none is found, returns None."""
        return next(
            (mod for mod in self.modules if mod.name == module_name), None
        )

    def get_module_group(self, module_name: str) -> AsModuleGroup:
        """! @brief Search this ASTERICS chain for a module group and return it.
        Return the first module group of the current processing chain
        that matches the name 'module_name'. If none is found, returns None."""
        return next(
            (mod for mod in self.module_groups if mod.name == module_name), None
        )

    ## @ingroup automatics_cds
    def list_address_space(self):
        """! @brief Prints the address space of slave registers to the console."""
        print(
            "{} registers per ASTERICS module.".format(self.max_regs_per_module)
        )
        as_conh.list_address_space(
            self.address_space, self.addr_per_reg, self.max_regs_per_module
        )

    ## @ingroup automatics_connection
    def auto_instantiate(self) -> Sequence[AsModule]:
        """! @brief Add modules to the processing chain defined by interfaces.
        Check all interfaces of all modules for the 'instantiate_in_top'
        attribute. Adds the modules referenced by this attribute to the
        system toplevel module group."""

        out = []
        if self.auto_inst_done:
            return out
        self.auto_inst_done = True

        # For all modules
        for module in ittls.chain(self.modules, self.pipelines, [self.as_main]):
            # Check each interface
            for inter in module.interfaces:
                # Is 'instantiate_in_top' set?
                if inter.instantiate_in_top is None:
                    continue
                # Get the referenced module group:
                gmod_name = inter.instantiate_in_top[1]
                if gmod_name == "":
                    gmod = self.top
                else:
                    gmod = self.get_module_group(gmod_name)
                    if gmod is None:
                        err = "Could not find module group '{}'!".format(
                            gmod_name
                        )
                        LOG.error(err)
                        raise AsModuleError(err)
                inst_mod = inter.instantiate_in_top[0]

                # If yes: Add the referenced module to the system toplevel
                ret = self.add_module(
                    inst_mod, "{}_{}".format(module.name, inst_mod), group=gmod
                )
                # Error message if the module wasn't found
                if ret is None:
                    LOG.error(
                        (
                            "Could not find module '%s' set as "
                            "automatic toplevel instantiation for "
                            "interface '%s' of module '%s'!"
                        ),
                        inst_mod,
                        inter.name,
                        module.name,
                    )
                    continue
                try:  # Run special config function
                    ret.auto_inst_config(ret, module)
                    LOG.debug("Ran autoconfig function for '%s'", repr(ret))
                except AttributeError:
                    pass  # OK if function doesn't exist -> no special config
                out.append(ret)
                LOG.info(
                    (
                        "Automatically instantiated module '%s' to '%s' "
                        "from interface '%s' of module '%s'"
                    ),
                    ret.name,
                    gmod.name,
                    inter.unique_name,
                    module.name,
                )
                for iinter in ret.interfaces:
                    if iinter.to_external:
                        iinter.name_prefix = (
                            module.name + "_" + iinter.name_prefix
                        )

                setattr(inter, "connect_to", ret)
        self.auto_instantiated = out
        if not self.auto_connect_run:
            foreach(self.auto_instantiated, self._extract_generics)
        return out

    ## @ingroup automatics_connection
    def connect(self, source, sink, *, top=None):
        """! @brief Connect any combination of Ports, Interfaces or ASTERICS Modules.
        User facing connect method. Stores the connect call for later.
        @param source: The data source (object to connect).
                       Should be in the direction of data, though not necessary.
        @param sink: Object to connect to. Preferrably the data sink.
        @param top: The reference toplevel. Can usually be left blank.
        """
        if top is None:
            top = self.as_main
        source_parent = as_conh.get_parent_module(source)
        sink_parent = as_conh.get_parent_module(sink)
        # For module groups below "as_main" and their modules:
        # Delegate connections to a Module Group if it has a connect method
        try:
            if (
                isinstance(source_parent, AsModuleGroup)
                and source_parent.modlevel > 1
            ):
                source_parent.connect(source, sink)
            elif (
                isinstance(sink_parent, AsModuleGroup)
                and sink_parent.modlevel > 1
            ):
                sink_parent.connect(source, sink)
            elif (
                isinstance(source_parent.parent, AsModuleGroup)
                and source_parent.modlevel > 2
            ):
                source_parent.parent.connect(source, sink)
            elif (
                isinstance(sink_parent.parent, AsModuleGroup)
                and sink_parent.modlevel > 2
            ):
                sink_parent.parent.connect(source, sink)
            else:
                self.user_cons.append((source, sink, top))
        except AttributeError:
            self.user_cons.append((source, sink, top))

    ## @}

    def _handle_connect_to(self, inter: Interface, connect_to: AsModule):
        """! @brief Connect auto-instantiated modules to their associated interface.
        This method connects the instantiating interface to the
        auto-instantiated module. A suitable interface is filtered for,
        the first matching is selected and the connect_interface method called.
        """
        # Source interfaces parent module
        mod = inter.parent
        if (
            isinstance(mod, As2DWindowPipeline)
            and connect_to.entity_name == "as_regmgr"
        ):
            connect_to.set_generic_value("AUTO_HW_REG_MODIFY_BIT", "True")
        # Make sure the connection will complete
        inter.set_connected_all(False)
        # We're looking for an interface of the same type and opposite direction
        ci_direction = "in" if inter.direction == "out" else "out"
        ci_type = inter.type
        con_inters = connect_to.get_interfaces_filtered(ci_direction, ci_type)
        if not con_inters:
            # No interfaces found! Potentially not good!
            LOG.warning(
                (
                    "The auto-instantiated module '%s' could not be "
                    "connected! No suitable interfaces found for "
                    "instantiating interface '%s' of module '%s'."
                ),
                connect_to.name,
                inter.name,
                inter.parent.name,
            )
        else:
            # We'll try the first matching interface
            con_inter = con_inters[0]

            # Make sure the connection will complete
            con_inter.set_connected_all(False)
            self.__connect_interface__(inter, con_inter, top=mod.parent)
            # Make sure the interface is not also included in the
            # ModuleGroup entity!
            inter.to_external = False

    def _extract_generics(self, module: AsModule):
        """! @brief Add generics found in Ports and Signals to their parent modules.
        For each port of module, adds all generics it finds
        in the data width definition."""
        for port in module.get_full_port_list():
            gens = extract_generics(port.data_width)
            for gen in gens:
                gen_obj = module.get_generic(gen, suppress_error=True)
                if not gen_obj:
                    LOG.error(
                        (
                            "VHDL error! Generic '%s' in port '%s', "
                            "but not in containing module '%s'!"
                        ),
                        gen,
                        port.code_name,
                        module.entity_name,
                    )
                    continue
                port.generics.append(gen_obj)

    def _resolve_generics(self, groupmod: AsModuleGroup):
        """! @brief Resolve all Generics found in data widths of ports to their values.
        Resolve the generics in data widths of signals
        and ports of modules in the current processing chain."""
        foreach(groupmod.get_full_port_list(), as_conh.resolve_generic)

    def __get_reg_addr_widths__(self, module_list: list):
        module_count = sum([len(mod.register_ifs) for mod in module_list])
        self.mod_addr_width = int(math.ceil(math.log(module_count, 2)))
        self.reg_addr_width = int(
            math.ceil(math.log(self.max_regs_per_module, 2))
        )

    def _add_pipeline(self, pipeline: As2DWindowPipeline):
        self.pipelines.append(pipeline)

    ##
    # @addtogroup automatics_connection
    # @{

    def auto_connect(self):
        """! @brief Execute the connection processes to build an ASTERICS processing chain.
        Run through a few connection methods for each module to handle
        standard ports, external interfaces and register interfaces and more.
        These do not require an explicit call of 'connect()' to be connected
        properly, this method handles these tasks automatically."""
        LOG.debug(
            "Running auto_connect() for %s modules...", str(len(self.modules))
        )

        self.auto_connect_run = True

        # Collect all modules
        all_modules = set()
        all_modules.update(self.modules)
        all_modules.update(self.pipelines)

        all_groups = set(ittls.chain(self.module_groups, self.pipelines))
        all_groups.add(self.as_main)

        foreach(self.module_groups, lambda gm: gm.__update_generics_list__())
        # Assign generics to ports
        foreach(all_modules, self._extract_generics)

        # Handle generics in ports of as_main and toplevel
        self._extract_generics(self.as_main)
        self._extract_generics(self.top)

        # Handle pipelines (if present)
        for pipe in self.pipelines:
            try:
                pipe.auto_connect()
            except AsError as err:
                if err.severity in ("Error", "Critical"):
                    return False
            all_modules.update(pipe.modules)
        foreach(self.module_groups, lambda gm: gm.__update_generics_list__())

        # Determine the maximum amount of registers per module
        self.max_regs_per_module = as_conh.get_max_regs_per_module(all_modules)
        LOG.debug(
            "Set max_regs_per_module to '%s'.", str(self.max_regs_per_module)
        )
        # Resolve address widths for all ports, if possible
        self.__get_reg_addr_widths__(all_modules)

        # Run user connection definitions
        for con in self.user_cons:
            try:
                self.__connect__(con[0], con[1], top=con[2])
            except AsError:
                pass
                # Errors at this stage are OK
                # We'll collect them, so the user has all errors that their
                # design causes at once.
        for group in self.module_groups:
            if group is self.as_main:
                continue
            self.modules.extend(group.modules)

        # If any critical errors have occurred, we stop here!
        # We don't want to pile any internal errors, caused by errors in their
        # design, onto them!
        if self.err_mgr.has_errors("Error"):
            raise AsTextError(
                "Caused by user script", "Critical errors encountered!"
            )

        # If not done already, auto-instantiate modules defined in interfaces
        if not self.auto_inst_done:
            self.auto_instantiate()
            all_modules.update(self.auto_instantiated)
            for mod in self.auto_instantiated:
                self._extract_generics(mod)

        # Add toplevel modules to all_modules list
        all_modules = tuple(ittls.chain(all_modules, (self.as_main, self.top)))

        # Propagate generics that have no value set to toplevel
        foreach(all_modules, as_conh.connect_generics)

        # For all modules in this chain
        for mod in self.modules:
            # Run connection automation for standard ports, ...
            self._connect_standard_ports(mod, mod.parent)
            # ... external interfaces (interfaces facing out towards 'as_main')
            for inter in mod.interfaces:
                # If the interface has a 'connect_to' attribute, we need to
                # automatically connect it to an AsModule, stored there
                connect_to = getattr(inter, "connect_to", None)
                if connect_to:
                    # If the connection target is on the same level as the
                    # requesting module, connect them!
                    if connect_to.parent == mod.parent:
                        self._handle_connect_to(inter, connect_to)
                        continue
                    # If the connection target is "higher up" in the ASTERICS
                    # chain, we can't handle the connection => propagate up
                    else:
                        inter.to_external = True
                self._propagate_interface(inter)
            # ... and register interfaces!
            self._connect_register_interfaces(mod)
            # Update the 'connected'-status for the module
            mod.set_connected(mod.is_connect_complete())

        # TODO: Requires more general handling
        # once full support for module groups is implemented
        # Handle module groups
        for mod in self.module_groups:
            if mod not in self.pipelines:
                mod.auto_connect()
            # Skip toplevel
            if mod is self.top:
                continue
            # Connect standard ports up
            self._connect_standard_ports(mod, mod.parent)
            # Handle interfaces...
            for inter in mod.interfaces:
                # Connect auto-inserted modules
                connect_to = getattr(inter, "connect_to", None)
                if connect_to:
                    self._handle_connect_to(inter, connect_to)
                    continue
                self._propagate_interface(inter, False)
            # ... and register interfaces!
            self._connect_register_interfaces(mod)

        # Handle unconnected ports:
        # Assign default values and report to user
        for mod in all_modules:
            if mod is self.top:
                continue
            self._handle_unconnected_ports(mod)
        self._handle_unconnected_ports(self.top)

        # Evaluate generics and replace with calculated values, where possible
        foreach(all_groups, self._resolve_generics)

        self._resolve_generics(self.top)
        self.top.__minimize_port_names__(
            self.NAME_FRAGMENTS_REMOVED_ON_TOPLEVEL
        )

        # Now, with resolved generics, try to calculate the data widths of
        # all ports of modules and signals in module groups
        for mod in all_modules:
            for port in mod.get_full_port_list():
                port.data_width = as_conh.resolve_data_width(port)
            try:
                for sig in mod.signals:
                    sig.data_width = as_conh.resolve_data_width(sig)
            except AttributeError:
                # Signals only present in module groups
                pass
        # Make sure the vector assignments of all signals are within bounds
        for gmod in self.module_groups:
            for sig in gmod.signals:
                try:
                    sig.__check_vector_assignments__()
                except AttributeError:
                    pass

    def _propagate_interface(
        self,
        inter: Interface,
        add_module_name: bool = True,
        downto_mod: AsModuleGroup = None,
    ) -> Interface:
        """! @brief Adds a copy of 'inter' to the next higher level module group.
        Returns a reference to the new interface if successful, else None."""
        if (not inter.to_external) and (downto_mod is None):
            return None
        if downto_mod is None:
            target = as_conh.get_parent_module(inter).parent
        else:
            target = downto_mod
        if not target:
            return None

        # Duplicate the interface (instead of copy.copy(), resets some vars)
        new_inter = inter.duplicate()
        new_inter.parent = inter.parent

        to_remove = []
        # Only applies if interface is moving toward toplevel, down in modlevel
        if downto_mod is None:
            # Substitute generics with those available on the next higher level
            for port in new_inter.ports:
                # port.in_entity overrides "make external"
                if not port.in_entity:
                    to_remove.append(port.code_name)
                    continue
                as_conh.resolve_generic(port)
            # Remove ports from external interface that would not appear in entity
            foreach(to_remove, new_inter.remove_port)

        # Now associate the duplicated interface with the next module group
        target.add_interface(new_inter)
        # Register new connections between inter and new_inter
        if inter.direction == "in":
            inter.incoming.append(new_inter)
            new_inter.outgoing.append(inter)
        else:
            inter.outgoing.append(new_inter)
            new_inter.incoming.append(inter)

        # Connect all the ports between the two interfaces
        for port in inter.ports:
            if port.code_name in to_remove:
                continue
            new_port = new_inter.get_port(port.name)
            if port.get_direction_normalized() == "in":
                port.incoming = new_port
                new_port.outgoing.append(port)
            else:
                port.outgoing.append(new_port)
                new_port.incoming = port
            new_port.set_connected()
            port.set_connected()

        # Add prefix to the interface port names
        new_inter.set_prefix_suffix(
            "{}_{}".format(inter.parent.name, inter.name_prefix),
            inter.name_suffix,
            add_module_name,
        )

        # Update their connection status
        as_conh.update_interface_connected(inter)
        as_conh.update_interface_connected(new_inter)

        # Exceptions:
        # If this interface has "instantiate_in_top" set
        if target is self.top and inter.instantiate_in_top:
            new_inter.to_external = False
            new_inter.instantiate_in_top = None
            if target is self.top:
                new_inter.in_entity = False

        if target is self.top:
            new_inter.set_connected()
        inter.set_connected()

        as_conh.set_unique_name(new_inter, target)
        return new_inter

    def _handle_unconnected_ports(self, module: AsModule):
        """! @brief Evaluate connections of unconnected ports of a module.
        Evalutate the port rulesets of ports that are unconnected
        of the AsModule 'module'."""
        parent = module.parent
        if not parent:
            parent = module

        # Get all unconnected ports
        unconnected = module.get_unconnected_ports()
        for port in unconnected:
            LOG.debug(
                "Handling unconnected port '%s' of '%s' ...",
                port.code_name,
                module.name,
            )
            # Look for matching ports and signals in the modules assigned group
            target = parent.get_port(port.code_name, suppress_error=True)
            if not target:
                target = parent.get_port(port.name, suppress_error=True)
            if not target and isinstance(parent, AsModuleGroup):
                target = parent.get_signal(port.code_name)
                if not target:
                    target = parent.get_signal(port.name)
                # if target:
                #    port.remove_condition("external_port")

            # Even if we couldn't identify a target, run the connect method
            # This will make sure that the ruleset for all ports is evaluated)
            ret = self.__connect_port__(
                port, target, sink_parent=parent, top=parent
            )
            if ret:
                if port.get_direction_normalized() == "in":
                    target = port.incoming
                else:
                    target = port.outgoing[0]
                if target:
                    LOG.debug(
                        "Port '%s' connected with '%s' of '%s'",
                        port.code_name,
                        getattr(target, "code_name", target),
                        parent.name,
                    )
                else:
                    LOG.debug(
                        "Port rules for '%s' of '%s' applied",
                        port.code_name,
                        parent.name,
                    )

    def _connect_register_interfaces(self, module: AsModule):
        """! @brief Analyse and 'connect' the register interfaces of an AsModule"""
        LOG.debug(
            "Running register interface analysis for module '%s'...",
            module.name,
        )
        # For all register interfaces in the module
        for regif in module.register_ifs:
            LOG.debug("Handling register interface '%s'...", str(regif))
            if not any(
                (
                    con.parent.entity_name == "as_regmgr"
                    for con in regif.incoming
                )
            ):
                LOG.debug("No connected as_regmgr! Skipping...")
                continue
            # Check if the address space is out of bounds
            if self.asterics_base_addr + self.cur_addr > self.asterics_top_addr:
                LOG.error(
                    (
                        "Too many register interfaces or too many "
                        "registers! Address space is full at module '%s'"
                    ),
                    module,
                )
                print("AsAutomatics halt! Slave register address space full!")
                raise Exception("Slave register address space full!")

            # Assign this register interface to the current address offset
            self.address_space[str(self.cur_addr)] = regif
            regif_num = self.cur_addr / (
                self.addr_per_reg * self.max_regs_per_module
            )
            # Set register interface attributes
            regif.set_module_base_addr(
                self.cur_addr + self.asterics_base_addr, int(regif_num)
            )
            regif.set_connected()
            # Update the current address offset
            self.cur_addr += self.addr_per_reg * self.max_regs_per_module
            LOG.debug(
                "Assigned address '%s' to register interface '%s'",
                "{:#8X}".format(regif.base_address),
                str(regif),
            )
            mgrs = [
                mod
                for mod in module.module_connections
                if mod.entity_name == "as_regmgr"
            ]
            for regmgr in mgrs:
                regmgr.set_generic_value("REG_COUNT", regif.reg_count)

                glue_sigs = [rport.glue_signal for rport in regif.ports]
                foreach(glue_sigs, as_conh.resolve_generic)

    def _connect_standard_ports(self, module: AsModule, top: AsModule):
        """! @brief Calls the 'connect' method for all standard ports of the module."""
        LOG.debug("Connecting standard ports of module '%s'", module.name)
        parent = module.parent
        parent_ports = tuple(
            ittls.chain(
                parent.ports,
                parent.standard_ports,
                getattr(parent, "signals", tuple()),
            )
        )
        for port in module.standard_ports:
            LOG.debug("Handling port '%s'", port.code_name)
            # Run the port rules first
            self.__connect_port__(port, None, top=top)
            # If the port is now connected, next port
            if port.connected:
                continue
            # -> Else:
            # try to connect automatically to suitable targets
            port_list = tuple(
                filter(lambda p: p.name == port.name, parent_ports)
            )
            for s_port in port_list:
                self.__connect_port__(port, s_port, top=top)

    # TODO: Refactor the __connect_xyz__ methods:
    # Refactor return values to improve debugging and user feedback
    # capabilities
    def __connect__(self, source, sink, *, top=None):
        """! @brief Internal connect() method. May be called with any combination
        of modules, interfaces and ports. Connections are executed immediately.
        """
        LOG.debug(
            "Connect called for source '%s' and sink '%s'",
            str(source),
            str(sink),
        )

        if source is None or sink is None:
            raise AsTextError(
                "Source or Sink is None",
                "Connect statement received no sink or source!",
                severity="Error",
            )
        LOG.info("Connecting '%s' to '%s'...", str(source), str(sink))
        # Swap source and sink if necessary
        source, sink = as_conh.swap_if_necessary(source, sink)
        if top is None:
            top = self.as_main
        try:
            if isinstance(source, AsModule):
                self.__connect_module__(source, sink, top=top)
            elif isinstance(source, Interface):
                self.__connect_interface__(source, sink, top=top)
            elif isinstance(source, Port):
                source.overwrite_rule("both_present", "forceconnect")
                self.__connect_port__(source, sink, top=top)
            else:
                LOG.error(
                    (
                        "'connect()' called with incompatible parameters!"
                        " '%s' and '%s'"
                    ),
                    str(source),
                    str(sink),
                )
        except AsModuleError:
            pass
        # except Exception as exc:
        #    print(
        #        (
        #            "Connect method for source '{}' and sink '{}' failed with "
        #            "Exception: '{}"
        #        ).format(source, sink, exc)
        #    )
        #    raise Exception("Connection error occurred!")

    def __connect_module__(self, source: AsModule, sink, *, top):
        """! @brief Connect an AsModule as a source to any sink.
        Tries to find matching
        Ports from the modules interfaces and lone ports to any interfaces
        and ports of the sink."""
        if getattr(source, "connected", True):
            return None

        LOG.debug(
            "Looking to connect module '%s' to '%s'.", source.name, str(sink)
        )
        ret = None
        # If the sink is an AsModule
        if isinstance(sink, AsModule):
            if sink.connected:
                return None
            # Try to match interfaces with each other:
            for from_inter in source.interfaces:
                if from_inter.direction == "in":
                    continue
                for to_inter in sink.interfaces:
                    if to_inter.type != from_inter.type:
                        continue
                    if to_inter.direction == "out":
                        continue
                    if len(to_inter.incoming) > 0:
                        continue
                    ret = self.__connect_interface__(
                        from_inter, to_inter, top=top
                    )
                    if ret is not None:
                        break
            # Try to match ports with each other:
            for from_port in source.ports:
                # For each source port, search for a matching sink port
                to_port = sink.get_port(
                    from_port.code_name, suppress_error=True
                )
                # Just call the method, see what happens
                ret = self.__connect_port__(
                    from_port, to_port, sink_parent=sink, top=top
                )
                if ret is not None:
                    break
        # If the sink is an Interface
        elif isinstance(sink, Interface):
            for from_inter in source.interfaces:
                # For all source interfaces, just call the connect method
                ret = self.__connect_interface__(from_inter, sink, top=top)
                if ret is not None:
                    break
        # If sink is a Port
        elif isinstance(sink, Port):
            for from_port in source.ports:
                # See if any ports of the module match the sink
                ret = self.__connect_port__(from_port, sink, top=top)
                if ret is not None:
                    break

        if sink is not None:
            try:
                sink.set_connected(sink.is_connect_complete())
            except AttributeError:
                # AttributeError should only occur if sink is Port.
                sink.set_connected(True if ret is not None else False)
        source.set_connected(source.is_connect_complete())
        return None

    def __connect_interface__(self, source: Interface, sink, *, top) -> bool:
        """! @brief Connect a source Interface to any sink.
        Tries to find matching Interface in AsModule sinks, tries to connect to
        Interface sinks and connect matching ports of the Interface to single
        Port sinks."""

        # If the source interface is already connected, stop here
        if not source.to_external and source.connected:
            return None

        LOG.debug(
            "Looking to connect interface '%s' to '%s'",
            source.unique_name,
            str(sink),
        )
        # If the sink is an AsModule call this method for each Interface in the AsModule
        if isinstance(sink, AsModule):
            for to_inter in sink.interfaces:
                ret = self.__connect_interface__(source, to_inter, top=top)
                if ret is not None:
                    return ret
        # Connect matching ports of the two Interfaces
        elif isinstance(sink, Interface):
            out = False

            if not source.to_external and (
                source.direction == sink.direction
                and sink.parent.modlevel == source.parent.modlevel
            ):
                LOG.info(
                    (
                        "Cannot connect interfaces with the same data direction! "
                        "Source: '%s', Sink: '%s'"
                    ),
                    repr(source),
                    repr(sink),
                )
                return None
            # Swap interfaces if necessary
            source, sink = as_conh.swap_if_necessary(source, sink)
            # If the sink interface is already connected, stop here
            if (
                len(sink.incoming) > 0
                and sink.parent.modlevel == source.parent.modlevel
            ):
                LOG.info(
                    (
                        "Connection attempted with or from an already "
                        "connected interface! Source: '%s', Sink: '%s'"
                    ),
                    repr(source),
                    repr(sink),
                )
                return None

            # Also make sure both interfaces are of the same "type"
            if source.type != sink.type:
                LOG.info(
                    (
                        "Connection attempted between incompatible interface types! "
                        "Source: '%s', Sink: '%s'"
                    ),
                    repr(source),
                    repr(sink),
                )
                return None
            # If there are templates set, make sure they match
            if source.template is not None and sink.template is not None:
                if source.template.type != sink.template.type:
                    return None
            # Check if there needs to be an intermediate interface
            # because module group boundaries are crossed
            src_mod = as_conh.get_parent_module(source)
            snk_mod = as_conh.get_parent_module(sink)
            # Connect the lower (higher modlevel) up until they are level
            while src_mod.modlevel != snk_mod.modlevel:
                if src_mod.modlevel > snk_mod.modlevel:
                    source.to_external = True
                    source = self._propagate_interface(source)
                    src_mod = as_conh.get_parent_module(source)
                    source.in_entity = False
                else:
                    sink.to_external = True
                    sink = self._propagate_interface(sink)
                    snk_mod = as_conh.get_parent_module(sink)
                    sink.in_entity = False

            # Call connect_port for each port of the source interface
            for from_port in source.ports:
                to_port = sink.get_port(from_port.name, suppress_error=True)
                ret = self.__connect_port__(
                    from_port, to_port, sink_parent=sink, top=top
                )
                if ret is not None:
                    out = True

            # After checking all ports, check if the interfaces are fully
            # connected (ie: all ports of the interface are connected)
            LOG.debug("Checking interface connection 'completeness'...")
            as_conh.update_interface_connected(source)
            as_conh.update_interface_connected(sink)
            sink.incoming.append(source)
            source.outgoing.append(sink)

            LOG.debug(
                "'%s' complete: '%s'; '%s' complete: '%s'",
                source.unique_name,
                str(source.connected),
                sink.unique_name,
                str(sink.connected),
            )
            # Return references to the accumulated connections
            return out
        # If the sink is a Port, search for a matching port in the Interface
        elif isinstance(sink, Port):
            for from_port in source.ports:
                ret = self.__connect_port__(from_port, sink, top=top)
                if ret is not None:
                    return ret

    def __connect_port__(self, source: Port, sink, *, sink_parent=None, top):
        """! @brief Connect a source Port to any sink.
        If the sink is not a Port, the
        method tries to match the source to any port of the sink.
        Else the method determines if source and sink Port will be
        connected, depending on the Ports rulesets.

        @param source: Source object of type Port
        @param sink: Sink object. Can be AsModule, Interface or Port
        @param sink_parent: .parent attribute of the sink parameter. Optional.
            Only needs to be passed if the sink could be None, or might not
            have it's .parent set correctly."""

        if sink is not None and sink_parent is None:
            sink_parent = sink.parent
        # If the sink is not a Port, call this method recursively for each Port
        # of the sink
        if not isinstance(sink, Port) and sink is not None:
            for to_port in sink.ports:
                ret = self.__connect_port__(source, to_port, top=top)
                if ret is not None:
                    return ret
            if isinstance(sink, AsModule):
                for inter in sink.interfaces:
                    to_port = inter.get_port(source.name, suppress_error=True)
                    if to_port:
                        ret = self.__connect_port__(source, to_port, top=top)
                        if ret is not None:
                            return ret

        else:
            LOG.debug(
                "Looking to connect port '%s' to '%s'",
                source.code_name,
                str(sink),
            )

            # Swap ports if necessary
            source, sink = as_conh.swap_if_necessary(source, sink)
            # If source is already connected, stop
            if source.connected and not isinstance(source, StandardPort):
                LOG.info(
                    (
                        "Connection attempted from an already "
                        "connected port! '%s' of module '%s'"
                    ),
                    source.code_name,
                    as_conh.get_parent_module(source).name,
                )
                return None
            # Evaluate the port rules. The method returns the determined target
            target = self._eval_port_rules(source, sink, sink_parent)
            if target is not None:
                # If the target is not None, create a connection
                LOG.debug(
                    "Connecting '%s' to '%s'", source.code_name, str(target)
                )
                # Generate and add glue signals to the toplevel containers
                if isinstance(target, Port) and (
                    as_conh.get_parent_module(target) is not top
                    or source.glue_signal is None
                ):
                    # Remove previously generated and now invalid glue signals
                    # Only for normal port connections (between two modules)
                    if (
                        (
                            ("signal" not in target.port_type)
                            and (
                                not isinstance(target, StandardPort)
                                and not isinstance(source, StandardPort)
                            )
                        )
                        and target.glue_signal is not None
                        and target.incoming is not None
                    ):
                        as_conh.remove_port_connection(target.incoming, target)
                    # Create the glue signal
                    glue = GlueSignal.generate_glue_signal(
                        source, source, target
                    )
                    if glue is not None:
                        if isinstance(glue, GlueSignal):
                            if not top.add_signal(glue):
                                glue = top.get_signal(glue.code_name)
                        if (glue is not source) and (
                            source.glue_signal is None
                            or as_conh.is_same_modlevel(source, target)
                        ):
                            source.set_glue_signal(glue)
                        if not (
                            glue is source and target.glue_signal is not None
                        ):
                            target.set_glue_signal(glue)

                try:
                    # Register connection and set connected attribute
                    self._propagate_connection(source, target)
                except AttributeError:
                    # Target is string, set connected attribute
                    source.set_connected()
                return True
            return None

    @staticmethod
    def _propagate_connection(source: Port, sink: Port):
        """! @brief Register a connection on all abstraction levels.
        This method registers the new port to port connection with all
        higher level objects.
        Also, for the port receiving data, the 'connected' attribute is set."""

        # For connections to the module group from a module
        if (
            source.get_direction_normalized() == "in"
            and sink.get_direction_normalized() == "in"
        ):
            if (
                as_conh.get_parent_module(source).modlevel
                == as_conh.get_parent_module(sink).modlevel + 1
            ):
                source.incoming = sink
                if source not in sink.outgoing:
                    sink.outgoing.append(source)
                source.set_connected()
                return None

        # Register connection locally (Port objects)
        source.outgoing.append(sink)
        if isinstance(sink, GenericSignal):
            sink.incoming.append(source)
        else:
            sink.incoming = source
            # Set the 'connected' attribute
            sink.set_connected()

    def _eval_port_rules(self, source: Port, sink, sink_parent):
        """! @brief Evaluate the ruleset of a Port to Port connection.
        Evaluate the ruleset of a Port object when trying to connect it to
        a sink object. Calls '_apply_port_ruleset_actions' for execution of
        the rule actions."""
        target = None
        # For each condition in the ruleset of the source port
        for cond in source.get_rule_conditions():
            LOG.debug("Checking rule '%s' of port '%s'", cond, source.code_name)
            try:
                met = Port.rule_condition_eval[cond](source, sink)
            except KeyError:
                LOG.warning(
                    "Found invalid ruleset condition '%s'. Ignored!", cond
                )
                met = False
            # Evaluate the condition
            if met:
                LOG.debug(
                    "Condition met! Now executing linked actions: '%s'",
                    str(source.get_rule_actions(cond)),
                )
                # Condition met, execute the rule actions
                ret = self._apply_port_ruleset_actions(
                    source, sink, cond, target, sink_parent
                )
                if ret is not None:
                    LOG.debug(
                        "Identified target for port '%s': '%s'",
                        source.code_name,
                        str(ret),
                    )
                    target = ret
        return target

    SKIPPED_ACTIONS = ("note", "warning", "error")

    def _apply_port_ruleset_actions(
        self, source: Port, sink, cond: str, target, sink_parent
    ):
        """! @brief Apply/Execute the rule actions of a met rule condition."""
        result = target
        # For each action of this condition
        for action in source.get_rule_actions(cond):
            try:
                result = self._apply_port_rule(
                    action, source, sink, cond, target, sink_parent, result
                )
            except AsError:
                if self.err_mgr.get_error_severity_count("Critical"):
                    raise AsConnectionError(
                        source,
                        "Critical error encountered - Connection aborted!",
                    )
                else:
                    pass
        return result

    def _apply_port_rule(
        self, action, source: Port, sink, cond: str, target, sink_parent, result
    ):
        """! @brief Apply a single action of a condition in a Port's ruleset."""

        # When handling unconnected ports of connected interfaces
        if (
            source.port_type == "interface"
            and source.parent.connected
            and (sink is None or sink.port_type == "interface")
        ):
            # Only execute certain actions (Skipped actions filtered here)
            if action in self.SKIPPED_ACTIONS:
                LOG.debug(
                    (
                        "Skipped action '%s' of source '%s' from "
                        "inteface '%s' since it is already connected."
                    ),
                    action,
                    source.code_name,
                    source.parent.name,
                )
                return result

        LOG.debug("Handling action '%s'...", action)
        # On action "connect": simple checks for compatibility:
        # port direction and port names (not code_names)
        if action in ("connect", "forceconnect"):
            # Cannot connect a port to itself...
            if source is sink:
                return result
            if action == "connect" and source.name != sink.name:
                LOG.debug(
                    "Port names didn't match! '%s' != '%s'",
                    source.name,
                    sink.name,
                )
                return result
            if (
                source.get_direction_normalized()
                == sink.get_direction_normalized()
            ):
                if not (
                    (
                        source.port_type == "interface"
                        and source.parent.to_external
                    )
                    or source.port_type == "external"
                ):
                    LOG.debug("Normalized port directions are the same!")
                    LOG.debug(
                        "Source '%s':'%s'; Sink '%s':'%s'",
                        str(source),
                        source.get_direction_normalized(),
                        str(sink),
                        sink.get_direction_normalized(),
                    )
                    return result
            if source.data_type != sink.data_type:
                return result
            if not as_conh.manage_data_widths(source, sink):
                # TODO: The function 'manage_data_widths' has been quite
                # a headache. Need a more formal implementation of
                # data width management.
                # FIXME: What should happen if we end up here?
                LOG.warning(
                    "Failed data width management! From: %s ", str(source)
                )
                LOG.warning("Of: %s", str(as_conh.get_parent_module(source)))
                if sink:
                    LOG.warning("To: %s", str(sink))
                    LOG.warning("Of: %s", str(as_conh.get_parent_module(sink)))
                raise AsConnectionError(
                    source, "Failed data width management", severity="Warning"
                )

            LOG.debug(
                "Matching ports identified: '%s' and '%s'",
                source.code_name,
                sink.code_name,
            )

            # If data sink (port with direction "in") already has a connection
            # we need to check if this target can overwrite it (does not apply to signals)
            if (
                ("signal" not in sink.port_type)
                and (
                    not isinstance(sink, StandardPort)
                    and not isinstance(source, StandardPort)
                )
            ) and (sink.incoming is not None):
                # If that connection is less fitting (possibly a fallback port)
                if sink.name not in sink.incoming.code_name:
                    # Overwrite the connection
                    return sink
                else:
                    # Otherwise output a warning
                    LOG.info(
                        (
                            "Could not connect port '%s' of '%s' to '%s' of '%s'. "
                            "Port '%s' already connected to '%s' of '%s'!"
                        ),
                        repr(source),
                        str(as_conh.get_parent_module(source)),
                        repr(sink),
                        str(as_conh.get_parent_module(sink)),
                        repr(sink),
                        repr(sink.incoming),
                        str(as_conh.get_parent_module(sink.incoming)),
                    )
                    return result
            return sink

        # For 'bundle_...' actions, the target is either "and" or "or"
        elif "bundle" in action:
            btype = action.replace("bundle", "").strip("_ ")
            source_mod = as_conh.get_parent_module(source)
            if isinstance(source_mod, AsModuleGroup):
                top_mod = source_mod
            else:
                top_mod = source_mod.parent
            try:
                # Add to a list of ports to be bundled
                top_mod.bundles[btype].append(source)
            except KeyError:
                # If the bundle action is neither 'and' nor 'or', error!
                errtxt = (
                    "Invalid bundle-action identified: '{}' for port"
                    " '{}' of module '{}'"
                ).format(action, source.code_name, str(source_mod))
                LOG.error(errtxt)
                raise AsTextError(action, errtxt)
            except AttributeError:
                raise AsModuleError(
                    top_mod.name,
                    "Bundle rule envoked for a non-group module!",
                    "From port '{}'".format(source.code_name),
                )
            # Check if toplevel already has the port
            ext_port = top_mod.get_port(source.code_name, suppress_error=True)
            # If the port is not in the next higher module,
            # make source external
            if not ext_port:
                self._make_external_port(source)
                # Now get the reference to the new external port
                ext_port = top_mod.get_port(
                    source.code_name, suppress_error=True
                )
                if not ext_port:  # If that didn't work, raise an error!
                    LOG.error("Failed to make port '%s' external!", str(source))
                    raise AsConnectionError(
                        msg="Bundle Signal, make '{}' external".format(
                            str(source)
                        ),
                        affected_obj=source,
                    )

            # Generate a new signal used to "feed" the bundling gate
            signal_name = "{}_{}_{}".format(
                source_mod.name, source.code_name, btype
            )
            signal = GlueSignal(
                name=signal_name,
                data_type=source.data_type,
                data_width=source.data_width,
            )
            # Connect the signal and associate it with the higher module
            signal.incoming.append(source)
            signal.outgoing.append(ext_port)
            signal.assign_to(top_mod)
            top_mod.signals.append(signal)

            # Add it as source's glue signal
            source.set_glue_signal(signal)
            source.set_connected()
            return ext_port

        elif action == "make_external":
            if target:
                return result
            # If source is already on toplevel
            top_mod = as_conh.get_parent_module(source)
            if top_mod == self.top:
                return result  # No need for action
            # Else, make the port external
            if not self._make_external_port(source, False):
                LOG.error("Failed to make port '%s' external!", str(source))
                raise AsConnectionError(
                    msg="Make external, make '{}' external".format(str(source)),
                    affected_obj=source,
                )
            # Set next higher up connected port as the target
            ext_mod = getattr(as_conh.get_parent_module(source), "parent", None)
            target = ext_mod.get_port(source.code_name, suppress_error=True)
            return target

        elif "fallback_port" in action:
            # This action is only valid if no other connection target is
            # found: Check parent of sink for the fallback port
            if result is not None:
                return result
            # For 'fallback_port(...)', try to find the passed port name
            # among the port of the parent of the sink port.
            fbp_name = action.replace("fallback_port", "").strip("()")
            if sink is None:
                sink = sink_parent
                to_port = sink.get_port(fbp_name, suppress_error=True)
            else:
                to_port = sink.parent.get_port(fbp_name, suppress_error=True)
            if to_port is None:
                to_port = as_conh.get_parent_module(sink).get_port(
                    fbp_name, suppress_error=True
                )
            if to_port is not None and not to_port.connected:
                return to_port

        elif "fallback_signal" in action:
            # This action is only valid if no other connection target is
            # found: Check parent of source for signals matching
            # the fallback signal name
            if result is not None:
                return result
            mod_parent = as_conh.get_parent_module(source).parent
            # If the parent of the source's module is not a module group,
            # there cannot be any signals for us to match with!
            if not isinstance(mod_parent, AsModuleGroup):
                return result
            # Extract the fallback signal name from the action string
            fbs_name = action.replace("fallback_signal", "").strip("()")
            # get_signal() returns None if no matching signal is found
            signal = mod_parent.get_signal(fbs_name)
            if signal is None:
                LOG.info(
                    "Fallback signal '%s' not found for '%s' in '%s'!",
                    fbs_name,
                    str(source),
                    str(mod_parent),
                )
            return signal

        elif "set_value" in action:
            # Only use this constant value action if no target
            if result is not None:
                return result
            # For 'set_value(...)', extract the value
            value = action.replace("set_value", "")[1:-1]
            # Generate a "fake" glue signal with the desired value as the name
            glue = GlueSignal(
                name=value,
                code_name=value,
                data_width=source.data_width,
                optional=False,
            )
            glue.is_signal = False
            glue.assign_to(as_conh.get_parent_module(source).parent)
            glue.set_connected()
            if source.get_direction_normalized() == "in":
                source.incoming = glue
            elif source.get_direction_normalized() == "out":
                source.outgoing.append(glue)
            source.set_connected()
            source.set_glue_signal(glue)
            source.in_entity = False
            return None
        # The actions 'note', 'warning' and 'error' report to the user
        elif action == "note":
            LOG.info(
                "%s triggered by '%s'",
                as_conh.__get_port_rule_message__(source),
                cond,
            )
            # Remove the action so it is only displayed once
            source.remove_rule(cond, action)
            return result
        elif action == "warning":
            LOG.warning(
                "%s triggered by '%s'",
                as_conh.__get_port_rule_message__(source),
                cond,
            )
            # Remove the action so it is only displayed once
            source.remove_rule(cond, action)
            return result
        elif action == "error":
            LOG.error(
                "%s triggered by '%s'",
                as_conh.__get_port_rule_message__(source),
                cond,
            )
            # No removal necessary, automatics should halt after diplaying
            print(
                (
                    "AsAutomatics stopped because of a triggered 'error' "
                    "rule for port {} of {}"
                ).format(source, source.parent)
            )
            raise AsConnectionError(
                msg="Port connection error raised by ruleset",
                detail="rule condition '{}'".format(cond),
                affected_obj=source,
            )
        elif action == "none":
            # No action! YEAH!
            return result
        else:
            LOG.warning(
                (
                    "Invalid port rule action detected: '%s' for "
                    "condition '%s' of port '%s' of module '%s'."
                ),
                action,
                cond,
                source.code_name,
                as_conh.get_parent_module(source).name,
            )
            raise AsTextError(
                action, "Invalid port rule action found!", severity="Warning"
            )

    def _make_external_port(self, port: Port, keep_name: bool = True) -> bool:
        """! @brief Propagate 'port' up to toplevel as an external port.
        Copies 'port' and adds it to all higher level modules,
        connecting the ports along the way."""
        # Check if port is already in toplevel
        tmod = as_conh.get_parent_module(port)
        if tmod is self.top:
            LOG.info("Port '%s' is already on toplevel!", str(port))
            return False
        # "Move" up to toplevel, module by module
        while tmod is not self.top:
            pmod = tmod.parent
            if not pmod:  # Make sure tmod is not None
                LOG.error(
                    (
                        "Make external: Error while propagating to toplevel:"
                        " Parent of Module '%s' is 'None'!"
                    ),
                    str(tmod),
                )
                return False
            # Check if port is already in the current module
            new_port = pmod.get_port(port.code_name, suppress_error=True)
            if not new_port:
                new_port = pmod.get_port(port.name, suppress_error=True)

            if new_port is None and isinstance(pmod, AsModuleGroup):
                signal = pmod.get_signal(port.code_name)
                if not signal:
                    signal = pmod.get_signal(port.name)
                if signal:
                    port.glue_signal = signal
                    self._propagate_connection(port, signal)
                    return True

            # Check if port with new name is current module
            if not keep_name and not new_port:
                new_port_name = tmod.name + "_" + port.code_name
                new_port = pmod.get_port(new_port_name, suppress_error=True)

            if not new_port:
                # If not, copy Port and add to module
                new_port = port.duplicate()
                new_port.make_external()
                # Rename the port
                if not keep_name:
                    new_port.code_name = tmod.name + "_" + port.code_name
                # Add it to the higher module
                if not pmod.add_port(new_port):
                    LOG.error(
                        (
                            "Make external: Could not add port '%s' "
                            "to module '%s'!"
                        ),
                        str(port),
                        str(pmod),
                    )
                    return False
            # Connect port-pair
            if not new_port.connected:
                self._propagate_connection(port, new_port)
            # Next module and port
            tmod = pmod
            port = new_port
        return True

    ## @}
