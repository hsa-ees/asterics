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
# @author Philip Manke
# @brief Class representing an ASTERICS processing chain.
# -----------------------------------------------------------------------------

import time
import copy
import math
from typing import Sequence
from collections import namedtuple

from as_automatics_module import AsModule, AsModuleGroup
from as_automatics_port import Port, GlueSignal, StandardPort
from as_automatics_interface import Interface
from as_automatics_module_lib import AsModuleLibrary
from as_automatics_generic import Generic
from as_automatics_templates import AsMain, AsTop
from as_automatics_exceptions import (
    AsConnectionError,
    AsModuleError,
    AsErrorManager,
    AsTextError,
    AsError,
)
import as_automatics_helpers as as_help
import as_automatics_logging as as_log
import as_automatics_connection_helper as as_conh

# Get logging object reference
LOG = as_log.get_log()


class AsProcessingChain:
    """This class is used to contain and handle all information
       necessary to fully define and build an ASTERICS processing chain
       in the form of an IP-Core."""

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
        self.as_main.assign_to(self.top)
        self.top.modules.append(self.as_main)
        self.module_groups = [self.as_main]
        self.modules = []
        self.user_cons = []
        self.bundles = {"and": [], "or": [], "xor": [], "xnor": []}
        self.address_space = {}
        self.max_regs_per_module = 0
        self.cur_addr = 0
        self.mod_addr_width = 0
        self.reg_addr_width = 0
        self.asterics_top_addr = self.asterics_base_addr + 0x0000FFFF
        self.auto_inst_done = False
        self.auto_connect_run = False
        self.auto_instantiated = None
        for module in [self.as_main, self.top]:
            for inter in module.interfaces:
                # Assign a unique name to all interfaces, so that two as_streams
                # for example, don't have the same name, append the module name
                as_conh.set_unique_name(inter, module)

    def set_asterics_base_address(
        self, base_address: int, address_space_size: int = 0xFFFF
    ):
        """Allows setting of the base address and the address space size of 
        ASTERICS in the user script."""
        self.asterics_base_addr = base_address
        self.asterics_top_addr = base_address + address_space_size

    def write_hw(self, path: str, use_symlinks: bool = True, force: bool = False):
        """Wrapper function for AsAutomatics.__write_hw__.
        If necessary, auto_connect() is called before exporting the output.
        Generate the VHDL files and collect all VHDL source files
        of the ASTERICS hardware modules in this processing chain.
        Parameters:
            path: String - Where to put the output. Relative or static path.
            use_symlinks: Whether to copy or link to source files.
            force: If 'True', deletes anything in the output directory.
        """
        if not self.auto_connect_run:
            try:
                self.auto_connect()
            except AsError:
                return False
        return self.parent.__write_hw__(path, use_symlinks, allow_deletion=force)

    def write_sw(
        self,
        path: str,
        use_symlinks: bool = True,
        force: bool = False,
        module_driver_dirs: bool = False,
    ):
        """Wrapper function for AsAutomatics.__write_sw__.
        If necessary, auto_connect() is called before exporting the output.
        Generate the C and header files and collect all driver source files
        of the ASTERICS hardware modules in this processing chain.
        Parameters:
            path: String - Where to put the output. Relative or static path.
            use_symlinks: Whether to copy or link to source files.
            force: If 'True', deletes anything in the output directory.
            module_driver_dirs: Sort drivers into subfolders per module.
        """
        if not self.auto_connect_run:
            try:
                self.auto_connect()
            except AsError:
                return False
        return self.parent.__write_sw__(
            path,
            use_symlinks,
            allow_deletion=force,
            module_driver_dirs=module_driver_dirs,
        )

    def write_asterics_core(
        self,
        path: str,
        use_symlinks: bool = True,
        force: bool = False,
        module_driver_dirs: bool = False,
    ):
        """Wrapper function for AsAutomatics.__write_asterics_core__.
        If necessary, auto_connect() is called before exporting the output.
        Generate and collect all source files that are necessary to build
        this ASTERICS IP core.
        Parameters:
            path: String - Where to put the output. Relative or static path.
            use_symlinks: Whether to copy or link to source files.
            force: If 'True', deletes anything in the output directory.
            module_driver_dirs: Sort drivers into subfolders per module.
        """
        if not self.auto_connect_run:
            try:
                self.auto_connect()
            except AsError:
                return False
        return self.parent.__write_asterics_core__(
            path,
            use_symlinks,
            allow_deletion=force,
            module_driver_dirs=module_driver_dirs,
        )

    def write_ip_core_xilinx(
        self,
        path: str,
        use_symlinks: bool = True,
        force: bool = False,
        module_driver_dirs: bool = False,
    ):
        """Wrapper function for AsAutomatics.__write_ip_core_xilinx__.
        If necessary, auto_connect() is called before exporting the output.
        Generate and collect all source files that are necessary to build
        this ASTERICS IP core.
        Uses a directory structure compatible with Vivado IP-Cores and
        runs Vivado to generate the meta-files, making it an IP-Core.
        Parameters:
            path: String - Where to put the output. Relative or static path.
            use_symlinks: Whether to copy or link to source files.
            force: If 'True', deletes anything in the output directory.
            module_driver_dirs: Sort drivers into subfolders per module.
        """
        if not self.auto_connect_run:
            try:
                self.auto_connect()
            except AsError:
                return False
        return self.parent.__write_ip_core_xilinx__(
            path,
            use_symlinks,
            allow_deletion=force,
            module_driver_dirs=module_driver_dirs,
        )

    def write_system(
        self,
        path: str,
        use_symlinks: bool = True,
        force: bool = False,
        module_driver_dirs: bool = False,
        add_vears: bool = False,
    ):
        """Wrapper function for AsAutomatics.__write_system__.
        If necessary, auto_connect() is called before exporting the output.
        Generate and package the ASTERICS IP-Core into an FPGA system
        directory template. Optionally add the VEARS IP-Core.
        Parameters:
            path: String - Where to put the output. Relative or static path.
            use_symlinks: Whether to copy or link to source files.
            force: If 'True', deletes anything in the output directory.
            module_driver_dirs: Sort drivers into subfolders per module.
            add_vears: Link or copy VEARS (video output) into the system.
        """
        if not self.auto_connect_run:
            try:
                self.auto_connect()
            except AsError:
                return False
        return self.parent.__write_system__(
            path,
            use_symlinks,
            allow_deletion=force,
            module_driver_dirs=module_driver_dirs,
            add_vears=add_vears,
        )

    def write_system_graph(
        self,
        out_file: str = "asterics_graph",
        show_toplevels: bool = False,
        show_auto_inst: bool = False,
        show_ports: bool = False,
        show_unconnected: bool = False,
    ):
        """Wrapper function for AsAutomatics.__write_system_graph__.
        Generates and writes a graph representation of the ASTERICS chain
        and, if present, the 2D Window Pipelines using GraphViz Dot.
        Parameters:
            system: Chain or pipe object to visualize
                    (AsProcessingChain or As2DWindowPipeline).
            out_file: Path and filename of the graph to generate.
                    Default=[asterics_graph]
            show_toplevels: Include the toplevel module groups. [False]
            show_auto_inst: Include the automatically included modules. [False]
            show_ports: Add all ports to the interface edges. [False]
            show_unconnected: Write a list of unconnected ports into the module
                            nodes. WARNING: Many false positives! [False]
        """
        self.parent.__write_system_graph__(
            self, out_file, show_toplevels, show_auto_inst, show_ports, show_unconnected
        )

    def add_module(
        self,
        entity_name: str,
        module_name: str = "",
        repo_name: str = "",
        *,
        group=None
    ) -> AsModule:
        """Add a copy of an AsModule from the AsModuleLibrary to this instance
           of the AsProcessingChain. A custom name can be given to the module.
           If none is provided, a consecutive number is appended to the
           standard module name (the name of the VHDL entity)."""
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
                    "Could not find a module with " "this name in the module library!"
                ),
            )
        # Give the module a name, if none was provided
        if module_name == "":
            module_list = self.modules
            # Naming scheme: module's entity_name + "_" + module type count
            module_name = "{}_{}".format(
                entity_name,
                sum([1 for mod in module_list if entity_name == mod.entity_name]),
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
        LOG.info("Module '%s' added to chain as '%s'.", entity_name, module_name)
        return module

    # WIP!!!
    # TODO: Complete implementation and test!
    def __group__(
        self, group_name: str, parent_module: AsModule, *sub_modules: AsModule
    ):
        """Feature still under development! Do not use!
        Create a new module group. Provide a group_name, parent_module and
        a variable amount of sub_modules part of the new group."""
        raise NotImplementedError(
            (
                "Grouping feature still under development!"
                "This will most likely break your processing chain!"
            )
        )
        new_group = AsModuleGroup(group_name, parent_module, sub_modules)
        self.module_groups.append(new_group)
        new_group.assign_to(parent_module)
        for mod in sub_modules:
            mod.assign_to(new_group)
            for inter in mod.interfaces:
                if inter.to_external:
                    self.propagate_interface_up_once(inter)
            for port in mod.get_full_port_list():
                if port.to_external:
                    ext_port = copy.copy(port)
                    new_group.add_port(ext_port)
                    if port.get_direction_normalized() == "in":
                        port.incoming = ext_port
                        ext_port.outgoing.append(port)
                    else:
                        port.outgoing.append(ext_port)
                        ext_port.incoming = port
            for gen in mod.generics:
                if not gen.value:
                    ext_gen = copy.copy(gen)
                    new_group.add_generic(ext_gen)
                    gen.value = ext_gen

    def get_module(self, module_name: str) -> AsModule:
        """Return the first module of the current processing chain
        that matches the name 'module_name'. If none is found, returns None."""
        return next((mod for mod in self.modules if mod.name == module_name), None)

    def get_module_group(self, module_name: str) -> AsModuleGroup:
        """Return the first module group of the current processing chain
        that matches the name 'module_name'. If none is found, returns None."""
        return next(
            (mod for mod in self.module_groups if mod.name == module_name), None
        )

    def list_address_space(self):
        """Prints the current address space of the slave registers."""
        print("{} registers per ASTERICS module.".format(self.max_regs_per_module))
        as_conh.list_address_space(
            self.address_space, self.addr_per_reg, self.max_regs_per_module
        )

    def auto_connect(self):
        """Run through a few connection methods for each module to handle
           standard ports, external interfaces and register interfaces.
           These do not require an explicit call of 'connect()' to be connected
           properly, this method handles these tasks automatically."""
        LOG.debug("Running auto_connect() for %s modules...", str(len(self.modules)))

        self.auto_connect_run = True

        # Collect all modules
        all_modules = []
        all_modules.extend(self.modules)

        # Determine the maximum amount of registers per module
        self.max_regs_per_module = as_conh.get_max_regs_per_module(self.modules)
        LOG.debug("Set max_regs_per_module to '%s'.", str(self.max_regs_per_module))
        # Resolve address widths for all ports, if possible
        self.__get_reg_addr_widths__()

        # Assign generics to ports
        for mod in all_modules:
            self._extract_generics(mod)
        # Handle generics in ports of as_main and toplevel
        self._extract_generics(self.as_main)
        self._extract_generics(self.top)

        # Run user connection definitions
        for con in self.user_cons:
            try:
                self.__connect__(con[0], con[1], top=con[2])
            except AsError:
                pass
                # Errors at this stage are OK
                # We'll collect them, so the user has all errors that their
                # design causes at once.

        # If any critical errors have occurred, we stop here!
        # We don't want to pile any internal errors, caused by errors in their
        # design, onto them!
        if self.err_mgr.get_error_severity_count("Critical"):
            raise AsTextError("Caused by user script", "Critical errors encountered!")

        # If not done already, auto-instantiate modules defined in interfaces
        if not self.auto_inst_done:
            self.auto_instantiate()
            all_modules.extend(self.auto_instantiated)
            for mod in self.auto_instantiated:
                self._extract_generics(mod)

        # Now add all module groups to module list
        all_modules.append(self.as_main)
        all_modules.append(self.top)

        # Propagate generics that have no value set to toplevel
        for mod in all_modules:
            self.connect_generics(mod)

        # For all modules in this chain
        for mod in self.modules:
            # Run connection automation for standard ports, ...
            self.connect_standard_ports(mod, self.as_main)
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
                # FIXME: Can we make this more generic using
                # 'make_interface_external'? Method might have to be modified...
                self.propagate_interface_up_once(inter)
            # ... and register interfaces!
            self.connect_register_interfaces(mod)
            # Update the 'connected'-status for the module
            mod.set_connected(mod.is_connect_complete())

        # Sort module groups by modlevel?
        # TODO: Implement along with module group support
        # modlevel_high = 0
        # modgroups = {}
        # module_groups = []
        # for mod in self.module_groups:
        #    modgroups[mod.modlevel] = mod
        #    if mod.modlevel > modlevel_high:
        #        modlevel_high = mod.modlevel
        # for idx in range(modlevel_high, 0, -1):
        #    try:
        #        module_groups.extend(modgroups[idx])
        #    except KeyError:
        #        pass

        # TODO: Requires more general handling
        # once full support for module groups is implemented
        # Handle module groups
        for mod in self.module_groups:
            # Skip toplevel
            if mod is self.top:
                continue
            # Connect standard ports up
            self.connect_standard_ports(mod, mod.parent)
            # Handle interfaces...
            for inter in mod.interfaces:
                # Connect auto-inserted modules
                connect_to = getattr(inter, "connect_to", None)
                if connect_to:
                    self._handle_connect_to(inter, connect_to)
                    continue
                # FIXME: This call should be replaced by
                # 'make_interface_external'. Requires more testing!
                self.propagate_interface_up_once(inter, False)

        # Handle unconnected ports:
        # Assign default values and report to user
        for mod in all_modules:
            if mod is self.top:
                continue
            self.handle_unconnected_ports(mod)
        self.handle_unconnected_ports(self.top)

        # Evaluate generics and replace with calculated values, where possible
        for mod in self.module_groups:
            self.resolve_generics(mod)
            mod.__minimize_port_names__()

        self.top.__minimize_port_names__(self.NAME_FRAGMENTS_REMOVED_ON_TOPLEVEL)

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

    def _handle_connect_to(self, inter: Interface, connect_to: AsModule):
        """This method connects the instantiating interface to the 
        auto-instantiated module. A suitable interface is filtered for,
        the first matching is selected and the connect_interface method called.
        """
        # Source interfaces parent module
        mod = inter.parent
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
            # Interface direction is important!
            if inter.direction == "in":
                self.__connect_interface__(con_inter, inter, top=mod.parent)
            else:
                self.__connect_interface__(inter, con_inter, top=mod.parent)
            # Make sure the interface is not also included in the
            # ModuleGroup entity!
            inter.to_external = False

    def _extract_generics(self, module: AsModule):
        """For each port of module, adds all generics it finds
        in the data width definition."""
        for port in module.get_full_port_list():
            gens = as_help.extract_generics(port.data_width)
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

    def resolve_generics(self, groupmod: AsModuleGroup):
        """Resolve the generics in data widths of signals
        and ports of modules in the current processing chain."""
        for sig in groupmod.signals:
            self.resolve_generic(sig)
        for port in groupmod.get_full_port_list():
            self.resolve_generic(port)

    @staticmethod
    def resolve_generic(port: Port) -> bool:
        """This method makes sure that the Generics in port's data width
        exist in the VDHL entity of port's entity. Port may also be a GlueSignal
        Process: 1. Extract Generic strings from port's data width
        2. Match those strings to Generic objects in Port and the parent module
        3. Check if the Generic value is set; Check for and match linked Generic
        4. If necessary, substitute the Generic(s) with a match in group module
        5. If possible, use the defined value of the Generic
        6. Update port's data width and try to evaluate it.
        Parameters:
          port: The data width attribute of this port will be resolved.
        Returns True if the resolve function ran, False if nothing was done."""

        # If data_width.sep is not set, there can't be any generics
        if not port.data_width.sep:
            return False  # No vector? Nothing to do...
        # Grab some resources (port's parent module and generics)
        module = AsModule.get_parent_module(port)
        gen_strs = as_help.extract_generics(port.data_width)
        if not gen_strs:
            return False  # No generics? Nothing to do...

        # Grab the module group (module's parent)
        if not isinstance(module, AsModuleGroup):
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

        # Unpack port's data_width
        ndw_a = port.data_width.a
        ndw_sep = port.data_width.sep
        ndw_b = port.data_width.b

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
                    if not str(port.data_width.a).isnumeric():
                        ndw_a = ndw_a.replace(gen.code_name, str(val))
                    if not str(port.data_width.b).isnumeric():
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
            if not str(port.data_width.a).isnumeric():
                ndw_a = ndw_a.replace(gpair[0].code_name, gpair[1].code_name)
            if not str(port.data_width.b).isnumeric():
                ndw_b = ndw_b.replace(gpair[0].code_name, gpair[1].code_name)
        # Re-assemble the data_width tuple and update it for port
        port.data_width = port.DataWidth(a=ndw_a, sep=ndw_sep, b=ndw_b)
        # Re-evaluate data_width (resolve math)
        port.data_width = as_conh.resolve_data_width(port)
        return True

    def auto_instantiate(self) -> Sequence[AsModule]:
        """Check all interfaces of all modules for the 'instantiate_in_top'
        attribute. Adds the modules referenced by this attribute to the
        system toplevel module group."""

        out = []
        if self.auto_inst_done:
            return out
        self.auto_inst_done = True
        all_modules = copy.copy(self.modules)
        all_modules.append(self.as_main)
        # For all modules
        for module in all_modules:
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
                        err = "Could not find module group '{}'!".format(gmod_name)
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
                        iinter.name_prefix = module.name + "_" + iinter.name_prefix

                setattr(inter, "connect_to", ret)
        self.auto_instantiated = out
        return out

    def make_interface_external(self, inter: Interface):
        """Propagates 'inter' up until it reaches toplevel.
        Returns the interface added to toplevel if successful, else None."""
        last_inter = inter  # Set return value, in case bool(inter) == False
        while inter:
            last_inter = inter
            inter = self.propagate_interface_up_once(inter)
        return last_inter

    def propagate_interface_up_once(
        self, inter: Interface, add_module_name: bool = True
    ) -> Interface:
        """Adds a copy of 'inter' to the next higher level module group.
        Returns a reference to the new interface if successful, else None."""
        if not inter.to_external:
            return None
        top = AsModule.get_parent_module(inter).parent
        if not top:
            return None

        # Duplicate the interface (instead of copy.copy(), resets some vars)
        ext_inter = inter.duplicate()
        ext_inter.parent = inter.parent

        to_remove = []
        # Substitute generics with those available on the next higher level
        for port in ext_inter.ports:
            # port.in_entity overrides "make external"
            if not port.in_entity:
                to_remove.append(port.code_name)
                continue
            self.resolve_generic(port)
        # Remove ports from external interface that would not appear in entity
        for portname in to_remove:
            ext_inter.remove_port(portname)

        # Now associate the duplicated interface with the next module group
        top.add_interface(ext_inter)
        # Register new connections between inter and ext_inter
        if inter.direction == "in":
            inter.incoming.append(ext_inter)
            ext_inter.outgoing.append(inter)
        else:
            inter.outgoing.append(ext_inter)
            ext_inter.incoming.append(inter)

        # Connect all the ports between the two interfaces
        for port in inter.ports:
            if port.code_name in to_remove:
                continue
            ext_port = ext_inter.get_port(port.name)
            if port.get_direction_normalized() == "in":
                port.incoming = ext_port
                ext_port.outgoing.append(port)
                port.set_connected()
            else:
                port.outgoing.append(ext_port)
                ext_port.incoming = port
                ext_port.set_connected()

        # Add prefix to the interface port names
        ext_inter.set_prefix_suffix(
            "{}_{}".format(inter.parent.name, inter.name_prefix),
            inter.name_suffix,
            add_module_name,
        )

        # Update their connection status
        as_conh.update_interface_connected(inter)
        as_conh.update_interface_connected(ext_inter)

        # Exceptions:
        # If this interface has "instantiate_in_top" set
        if top is self.top and inter.instantiate_in_top:
            ext_inter.to_external = False
            ext_inter.instantiate_in_top = None
            if top is self.top:
                ext_inter.in_entity = False

        if top is self.top:
            ext_inter.set_connected()

        as_conh.set_unique_name(ext_inter, top)
        return ext_inter

    def handle_unconnected_ports(self, module: AsModule):
        """Evalutate the port rulesets of ports that are unconnected
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
            # This will make sure that the ruleset for all ports is evaluated
            ret = self.__connect_port__(port, target, sink_parent=parent, top=self.top)
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

    def __get_reg_addr_widths__(self):
        module_count = sum([len(mod.register_ifs) for mod in self.modules])
        self.mod_addr_width = int(math.ceil(math.log(module_count, 2)))
        self.reg_addr_width = int(math.ceil(math.log(self.max_regs_per_module, 2)))

    def connect_register_interfaces(self, module: AsModule):
        """Analyse and 'connect' the register interfaces of an AsModule"""
        LOG.debug("Running register interface analysis for module '%s'...", module.name)
        # For all register interfaces in the module
        for regif in module.register_ifs:
            LOG.debug("Handling register interface '%s'...", str(regif))
            if not any(
                (con.parent.entity_name == "as_regmgr" for con in regif.outgoing)
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
            regif_num = self.cur_addr / (self.addr_per_reg * self.max_regs_per_module)
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
                for glue in glue_sigs:
                    self.resolve_generic(glue)

    def connect_standard_ports(self, module: AsModule, top: AsModule):
        """Calls the 'connect' method for all standard ports of the module."""
        LOG.debug("Connecting standard ports of module '%s'", module.name)
        for port in module.standard_ports:
            LOG.debug("Handling port '%s'", port.code_name)
            # Call connect_port for the standard port and None, so that
            # the necessary rule actions are executed (mark as external, etc.)
            parent = AsModule.get_parent_module(port).parent
            for s_port in parent.standard_ports:
                if self.__connect_port__(port, s_port, top=top):
                    break
            # self.__connect_port__(
            #    port, AsModule.get_parent_module(port).parent, top=top)

    @staticmethod
    def connect_generics(module: AsModule):
        """Connect the generics of 'module' to linked generics or to external"""
        # We process every Generic of the module
        for gen in module.generics:
            LOG.debug("Handling Generic '%s' of '%s'...", gen.code_name, module.name)
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
                        LOG.debug("Adding '%s' to module '%s'", gen.code_name, mod.name)
                        # Add a copy of the generic to every module
                        tgen = copy.copy(gen)
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
                ext_gen = copy.copy(gen)
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
                        mgp = ModGenPair(mgp.mod, copy.copy(ext_gen))
                        mgp.mod.add_generic(mgp.gen)
                    # Link this generic to the generic of the higher module
                    mgp.gen.value = tgen
                    tgen = mgp.gen
                # Finally, link to the source generic
                gen.value = tgen

    def connect(self, source, sink, *, top=None):
        """Connect any combination of Ports, Interfaces or ASTERICS Modules.
        User facing connect method. Stores the connect call for later.
        Parameters:
          source: The data source (object to connect).
                  Should be in the direction of data, though not necessary.
          sink: Object to connect to. Preferrably the data sink.
          top: The reference toplevel. Can usually be left blank."""
        if top is None:
            top = self.as_main
        self.user_cons.append((source, sink, top))

    # TODO: Refactor the __connect_xyz__ methods:
    # Need a better connection handling (storing connections)
    # Currently a bit vague and wonky.
    # Refactor return values to improve debugging and user feedback
    # capabilities
    def __connect__(self, source, sink, *, top=None):
        """Abstract connect() method. May be called with any combination
           of modules, interfaces and ports."""
        LOG.debug(
            "Connect called for source '%s' and sink '%s'", str(source), str(sink)
        )

        if source is None or sink is None:
            raise AsTextError(
                "Source or Sink is None",
                "Connect statement received no sink or source!",
                severity="Critical",
            )
        LOG.info("Connecting '%s' to '%s'...", str(source), str(sink))
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
        #    print(("Connect method for source '{}' and sink '{}' failed with "
        #           "Exception: '{}").format(source, sink, exc))
        #    raise Exception("Connection error thrown!")

    def __connect_module__(self, source: AsModule, sink, *, top):
        """Connect an AsModule as a source to any sink. Tries to find matching
           Ports from the modules interfaces and lone ports to any interfaces
           and ports of the sink."""
        if getattr(source, "connected", True):
            return None

        LOG.debug("Looking to connect module '%s' to '%s'.", source.name, str(sink))
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
                    if to_inter.direction == from_inter.direction:
                        continue
                    ret = self.__connect_interface__(from_inter, to_inter, top=top)
                    if ret is not None:
                        break
            # Try to match ports with each other:
            for from_port in source.ports:
                # For each source port, search for a matching sink port
                to_port = sink.get_port(from_port.code_name, suppress_error=True)
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
        """Connect a source Interface to any sink. Tries to find matching
           Interface in AsModule sinks, tries to connect to Interface sinks
           and connect matching ports of the Interface to single Port sinks."""

        # If the source interface is already connected, stop here
        if not source.to_external and source.connected:
            return None

        LOG.debug(
            "Looking to connect interface '%s' to '%s'", source.unique_name, str(sink)
        )
        # If the sink is an AsModule call this method recurslively for each
        # Interface in the AsModule
        if isinstance(sink, AsModule):
            for to_inter in sink.interfaces:
                ret = self.__connect_interface__(source, to_inter, top=top)
                if ret is not None:
                    return ret
        # Connect matching ports of the two Interfaces
        elif isinstance(sink, Interface):
            out = False
            # If the sink interface is already connected, stop here
            if source.connected or sink.connected:
                LOG.warning(
                    (
                        "Connection attempted with or from an already "
                        "connected interface! Source: '%s', Sink: '%s'"
                    ),
                    repr(source),
                    repr(sink),
                )
                return None

            # Also make sure both interfaces are of the same "type"
            # (name == name) and the Interfaces have differing
            # directions (out <-> in)
            if source.type != sink.type or (
                not source.to_external and source.direction == sink.direction
            ):
                return None
            # If there are templates set, make sure they match
            if source.template is not None and sink.template is not None:
                if source.template.type != sink.template.type:
                    return None
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
        """__connect_port__(self, source, sink, sink_parent) --> (from, to)
        Connect a source Port to any sink. If the sink is not a Port, the
        method tries to match the source to any port of the sink.
        Else the method determines if source and sink Port will be
        connected, depending on the Ports rulesets.
        Parameters:
        source: Source object of type Port
        sink: Sink object. Can be AsModule, Interface or Port
        sink_parent: .parent attribute of the sink parameter. Optional.
            Only needs to be passed if the sink could be None, or might not
            have it's .parent set correctly.
        Return: Returns a tuple with the connection (original, reversed)
            Each item of the tuple is a namedTuple: Connection(from, to)
        """
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
                "Looking to connect port '%s' to '%s'", source.code_name, str(sink)
            )
            # If source is already connected, stop
            if source.connected and not isinstance(source, StandardPort):
                LOG.warning(
                    (
                        "Connection attempted from an already "
                        "connected port! '%s' of module '%s'"
                    ),
                    source.code_name,
                    AsModule.get_parent_module(source).name,
                )
                return None
            # Evaluate the port rules. The method returns the determined target
            target = self.eval_port_rules(source, sink, sink_parent)
            if target is not None:
                # If the target is not None, create a connection
                LOG.debug("Connecting '%s' to '%s'", source.code_name, str(target))
                # Generate and add glue signals to the toplevel containers
                if (
                    isinstance(target, Port)
                    and AsModule.get_parent_module(target) is not top
                ):
                    glue = self.__generate_glue_signal__(source, source, target)
                    if glue is not None:
                        if not top.add_signal(glue):
                            glue = top.get_signal(glue.code_name)
                        # top.signals.append(glue)
                        source.set_glue_signal(glue)
                        target.set_glue_signal(glue)

                try:
                    # Register connection and set connected attribute
                    self.propagate_connection(source, target)
                except AttributeError:
                    # Target is string, set connected attribute
                    source.set_connected()
                return True
            return None

    @staticmethod
    def propagate_connection(source: Port, sink: Port):
        """This method registers the new port to port connection with all
        higher level objects.
        Also, for the port receiving data, the 'connected' attribute is set."""
        dsrc_inter = None
        dsink_inter = None

        # Resolve data direction
        if source.get_direction_normalized() == "in":
            dsrc = sink
            dsink = source
        else:
            dsrc = source
            dsink = sink

        # Register connection locally (Port objects)
        dsrc.outgoing.append(dsink)
        dsink.incoming = dsrc
        # Set the 'connected' attribute
        dsink.set_connected()

        # Register connection with the 'Interface' objects
        # Get interface oobjects
        if dsrc.port_type == "interface":
            dsrc_inter = dsrc.parent
        if dsink.port_type == "interface":
            dsink_inter = dsink.parent
        # If both ports are part of interfaces
        if dsrc_inter and dsink_inter:
            # Register Interface relations
            if dsrc_inter not in dsink_inter.incoming:
                dsink_inter.incoming.append(dsrc_inter)
            if dsink_inter not in dsrc_inter.outgoing:
                dsrc_inter.outgoing.append(dsink_inter)
        # Else: Add the "foreign" port to the interface connection lists
        elif dsrc_inter and not dsink_inter:
            dsrc_inter.outgoing.append(dsink)
        elif dsink_inter and not dsrc_inter:
            dsink_inter.incoming.append(dsrc)

        # Register connection with the 'AsModule' objects
        dsrc_mod = AsModule.get_parent_module(dsrc)
        dsink_mod = AsModule.get_parent_module(dsink)
        dsrc_mod.register_connection(dsink_mod)
        dsink_mod.register_connection(dsrc_mod)

        LOG.debug(
            "Registered connection from '%s' of '%s' to '%s' of '%s'.",
            dsrc.code_name,
            dsrc_mod.name,
            dsink.code_name,
            dsink_mod.name,
        )

    def eval_port_rules(self, source: Port, sink, sink_parent):
        """Evaluate the ruleset of a Port object when trying to connect it to
           a sink object. Calls 'apply_port_ruleset_actions' for execution of
           the rule actions."""
        target = None
        # For each condition in the ruleset of the source port
        for cond in source.get_rule_conditions():
            LOG.debug("Checking rule '%s' of port '%s'", cond, source.code_name)
            try:
                met = Port.rule_condition_eval[cond](source, sink)
            except KeyError:
                LOG.warning("Found invalid ruleset condition '%s'. Ignored!", cond)
                met = False
            # Evaluate the condition
            if met:
                LOG.debug(
                    "Condition met! Now executing linked actions: '%s'",
                    str(source.get_rule_actions(cond)),
                )
                # Condition met, execute the rule actions
                ret = self.apply_port_ruleset_actions(
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

    def apply_port_ruleset_actions(
        self, source: Port, sink, cond: str, target, sink_parent
    ):
        """Apply/Execute the rule actions of a met rule condition."""
        result = target
        # For each action of this condition
        for action in source.get_rule_actions(cond):
            try:
                result = self.apply_port_rule(
                    action, source, sink, cond, target, sink_parent, result
                )
            except AsError:
                if self.err_mgr.get_error_severity_count("Critical"):
                    raise AsConnectionError(
                        source, "Critical error encountered - Connection aborted!"
                    )
                else:
                    pass
        return result

    def apply_port_rule(
        self, action, source: Port, sink, cond: str, target, sink_parent, result
    ):
        """Apply a single action of a condition in a Port's ruleset."""

        # When handling unconnected ports of connected interfaces
        if (
            source.port_type == "interface"
            and source.parent.connected
            and (sink is None or sink.port_type == "interface")
        ):
            # Only execute certain actions (Skipped actions filtered here)
            if action in self.SKIPPED_ACTIONS:
                # Notify user
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
            if action == "connect" and source.name != sink.name:
                LOG.debug(
                    "Port names didn't match! '%s' != '%s'", source.name, sink.name
                )
                return result
            if source.get_direction_normalized() == sink.get_direction_normalized():
                if not (
                    (source.port_type == "interface" and source.parent.to_external)
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
                # pass
                # TODO: The function 'manage_data_widths' has been quite
                # a headache. Need a more formal implementation of
                # data width management.
                # FIXME: What should happen if we end up here?
                LOG.warning("Failed data width management! From: %s ", str(source))
                LOG.warning("Of: %s", str(AsModule.get_parent_module(source)))
                if sink:
                    LOG.warning("To: %s", str(sink))
                    LOG.warning("Of: %s", str(AsModule.get_parent_module(sink)))
                raise AsConnectionError(
                    source, "Failed data width management", severity="Warning"
                )

            LOG.debug(
                "Matching ports identified: '%s' and '%s'",
                source.code_name,
                sink.code_name,
            )
            return sink

        # For 'bundle_...' actions, the target is either "and" or "or"
        elif "bundle" in action:
            btype = action.replace("bundle", "").strip("_ ")
            source_mod = AsModule.get_parent_module(source)
            try:
                # Add to a list of ports to be bundled
                self.bundles[btype].append(source)
            except KeyError:
                # If the bundle action is neither 'and' nor 'or', error!
                errtxt = (
                    "Invalid bundle-action identified: '{}' for port"
                    " '{}' of module '{}'"
                ).format(action, source.code_name, str(source_mod))
                LOG.error(errtxt)
                raise AsTextError(action, errtxt)
            top_mod = source_mod.parent
            # Check if toplevel already has the port
            ext_port = top_mod.get_port(source.code_name, suppress_error=True)
            # If the port is not in the next higher module,
            # make source external
            if not ext_port:
                self.make_external_port(source)
                # Now get the reference to the new external port
                ext_port = top_mod.get_port(source.code_name, suppress_error=True)
                if not ext_port:  # If that didn't work, raise an error!
                    LOG.error("Failed to make port '%s' external!", str(source))
                    raise AsConnectionError(
                        msg="Bundle Signal, make '{}' external".format(str(source)),
                        affected_obj=source,
                    )

            # Generate a new signal used to "feed" the bundling gate
            signal_name = "{}_{}_{}".format(source_mod.name, source.code_name, btype)
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
            top_mod = AsModule.get_parent_module(source)
            if top_mod == self.top:
                return result  # No need for action
            # Else, make the port external
            if not self.make_external_port(source, False):
                LOG.error("Failed to make port '%s' external!", str(source))
                raise AsConnectionError(
                    msg="Make external, make '{}' external".format(str(source)),
                    affected_obj=source,
                )
            # Set next higher up connected port as the target
            ext_mod = getattr(AsModule.get_parent_module(source), "parent", None)
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
                to_port = AsModule.get_parent_module(sink).get_port(
                    fbp_name, suppress_error=True
                )
            if to_port is not None and not to_port.connected:
                return to_port

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
                port_type=source.port_type,
                data_width=source.data_width,
                optional=False,
            )
            glue.is_signal = False
            glue.set_connected()
            source.set_connected()
            source.set_glue_signal(glue)
            source.in_entity = False
            return None
        # The actions 'note', 'warning' and 'error' report to the user
        elif action == "note":
            LOG.info(
                "%s triggered by '%s'", as_conh.__get_port_rule_message__(source), cond
            )
            # Remove the action so it is only displayed once
            source.remove_rule(cond, action)
            return result
        elif action == "warning":
            LOG.warning(
                "%s triggered by '%s'", as_conh.__get_port_rule_message__(source), cond
            )
            # Remove the action so it is only displayed once
            source.remove_rule(cond, action)
            return result
        elif action == "error":
            LOG.error(
                "%s triggered by '%s'", as_conh.__get_port_rule_message__(source), cond
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
                AsModule.get_parent_module(source).name,
            )
            raise AsTextError(
                action, "Invalid port rule action found!", severity="Warning"
            )

    @staticmethod
    def __generate_glue_signal__(port: Port, con_from: Port, con_to: Port) -> Port:
        """Generates and returns a GlueSignal port for the given port.
        First checks a few things using the provided ports (con_to, con_from),
        to determine if a glue signal is required."""
        from_parent = AsModule.get_parent_module(con_from)
        to_parent = AsModule.get_parent_module(con_to)
        if getattr(from_parent, "modlevel", 0) != getattr(to_parent, "modlevel", 0):
            return None
        if con_from.port_type == "interface":
            signame = "{}_{}{}".format(
                AsModule.get_parent_module(port).name,
                port.parent.name_prefix,
                port.code_name,
            )
        else:
            signame = "{}_{}".format(
                AsModule.get_parent_module(port).name, port.code_name
            )
        signal = GlueSignal(
            name=signame, data_width=port.data_width, data_type=port.data_type
        )
        signal.assign_to(AsModule.get_parent_module(port))
        signal.incoming = con_from
        signal.outgoing.append(con_to)
        return signal

    def make_external_port(self, port: Port, keep_name: bool = True) -> bool:
        """Propagate 'port' up to toplevel as an external port.
        Copies 'port' and adds it to all higher level modules,
        connecting the ports along the way."""
        # Check if port is already in toplevel
        tmod = AsModule.get_parent_module(port)
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
                    self.propagate_connection(port, signal)
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
                        ("Make external: Could not add port '%s' " "to module '%s'!"),
                        str(port),
                        str(pmod),
                    )
                    return False
            # Connect port-pair
            if not new_port.connected:
                self.propagate_connection(port, new_port)
            # Next module and port
            tmod = pmod
            port = new_port
        return True
