# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_automatics_env.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Capsules the entire as_automatics environment.
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
# @file as_automatics_env.py
# @ingroup automatics_mngmt
# @author Philip Manke
# @brief Capsules the entire as_automatics environment.
# -----------------------------------------------------------------------------

import os

from as_automatics_helpers import append_to_path
from as_automatics_module_lib import AsModuleLibrary
from as_automatics_vhdl_writer import VHDLWriter
from as_automatics_exceptions import AsError, AsFileError, AsErrorManager
from as_automatics_proc_chain import AsProcessingChain
from as_automatics_2d_pipeline import As2DWindowPipeline

import as_automatics_builder as as_build
import as_automatics_logging as as_log
import as_automatics_templates as as_templates
import as_automatics_visual as as_vis

LOG = as_log.get_log()


## @ingroup automatics_mngmt
class AsAutomatics:
    """! @brief Class bundling the main user-facing functionality of Automatics.
    Should be the only thing you need to import to use Automatics."""

    def __init__(self, asterics_home: str, version_no: str):
        self.asterics_home = append_to_path(
            os.path.realpath(asterics_home), "//"
        )
        self.version = version_no
        self.library = AsModuleLibrary(asterics_home)
        self.current_chain = None
        self.windowpipes = []

        self.design_name = "asterics"
        self.board_target = ""
        self.partname_hw = "xc7z010clg400-1"

        self.ipcore_name = "ASTERICS"
        self.ipcore_descr = "ASTERICS Image Processing Chain"

        # Construct and assign interface templates
        as_templates.add_templates()

    ##
    # @addtogroup automatics_mngmt
    # @}

    def set_hardware_target_definitions(
        self, partname: str = "", design: str = "", board: str = ""
    ):
        if design:
            self.design_name = design
        if board:
            self.board_target = board
        if partname:
            self.partname_hw = partname

    def set_ipcore_name(self, display_name: str):
        self.ipcore_name = display_name

    def set_ipcore_description(self, description_text: str):
        self.ipcore_descr = description_text

    def add_module_repository(self, module_dir: str, repo_name: str) -> list:
        """! @brief Add a repository of ASTERICS modules.
        The module repository must be structured in the same way
        as the default module repository.
        For more detail, check the Automatics chapter in the ASTERICS manual.

        Parameters:
        module_dir: Path to the repository folder
            (where the individual module directories are stored)
        repo_name: Name that is internally used to refer to the repository.
        Returns a list of the names of the found modules."""
        return self.library.add_module_repository(module_dir, repo_name)

    ## @}

    ## @ingroup automatics_helpers
    @staticmethod
    def _check_and_get_output_path(path: str) -> bool:
        path = os.path.realpath(path)
        # If path doesn't exist, create the necessary folders
        if not os.path.exists(path):
            try:
                os.makedirs(path, mode=0o755)
            except IOError as err:
                LOG.error(
                    (
                        "Automatics: Could not create output directory! - "
                        "'%s' - '%s'"
                    ),
                    path,
                    str(err),
                )
                return None
        return path

    ##
    # @addtogroup automatics_generate
    # @{

    # Relative path constants
    ## @brief Software driver source file path
    DRIVERS_REL_PATH = "drivers/asterics_v1_0/src/"
    ## @brief Hardware source file path
    HW_SRC_REL_PATH = "hw/hdl/vhdl/"
    ## @brief Default path for generating the ASTERICS IP Core
    IP_CORE_REL_PATH = "vivado_cores/ASTERICS/"
    ## @brief Path to the IP-Core template in the ASTERICS installation
    IP_CORE_TEMPLATE_PATH = "support/sys_template/vivado_cores/ASTERICS/"
    ## @brief Path to the system template in the ASTERICS installation
    SYSTEM_TEMPLATE_PATH = "support/sys_template/"

    def _write_hw(
        self, path: str, use_symlinks: bool = True, allow_deletion: bool = False
    ):
        # Make sure path is good
        opath = self._check_and_get_output_path(path)
        if not opath:
            raise AsFileError(path, "Could not create output folder!")
        opath = append_to_path(opath, "/")
        # Clean up if not empty
        try:
            as_build.prepare_output_path(None, opath, allow_deletion)
        except IOError as err:
            LOG.error(
                ("Could not prepare the output directory '%s'" "! - '%s'"),
                opath,
                str(err),
            )
            raise AsFileError(opath, "Could not write to output folder!")
        # Generate and collect hardware files
        try:
            self._gen_hw(opath, use_symlinks)
        except IOError:
            LOG.error(
                (
                    "Cannot write to '%s'! - "
                    "Could not create VHDL source files!"
                ),
                opath,
            )
            return False
        except AsError as err:
            LOG.error(str(err))
            return False
        return True

    def _gen_hw(self, path: str, use_symlinks: bool = True):
        err_mgr = self.current_chain.err_mgr
        if err_mgr.has_errors():
            LOG.critical(
                "%s errors encountered!\nGeneration aborted!",
                str(err_mgr.get_error_count()),
            )
            raise AsError(
                severity="Critical",
            )
        # Instantiate VHDL writer class
        writer = VHDLWriter(self.current_chain)
        # Generate asterics.vhd
        writer.write_module_group_vhd(path, self.current_chain.top)
        # Generate additional files for generic module groups
        for group in self.current_chain.module_groups:
            writer.write_module_group_vhd(path, group)

        # Collect the hardware and software source files
        as_build.gather_hw_files(self.current_chain, path, use_symlinks)

    def _write_sw(
        self,
        path: str,
        use_symlinks: bool = True,
        allow_deletion: bool = False,
        module_driver_dirs: bool = False,
    ):
        # Make sure path is good
        path = self._check_and_get_output_path(path)
        if not path:
            return False
        path = append_to_path(path, "/")
        # Clean up if not empty
        try:
            as_build.prepare_output_path(None, path, allow_deletion)
        except IOError as err:
            LOG.error(
                ("Could not prepare the output directory '%s'" "! - '%s'"),
                path,
                str(err),
            )
            return False
        # Generate and collect software files
        try:
            self._gen_sw(path, use_symlinks, module_driver_dirs)
        except (IOError, AsError) as err:
            LOG.error(str(err))
            return False
        return True

    def _gen_sw(
        self,
        path: str,
        use_symlinks: bool = True,
        module_driver_dirs: bool = True,
    ):
        err_mgr = self.current_chain.err_mgr
        if err_mgr.has_errors():
            LOG.critical(
                "%s errors encountered!\nGeneration aborted!",
                str(err_mgr.get_error_count()),
            )
            raise AsError(severity="Critical")
        as_build.write_asterics_h(self.current_chain, path)
        as_build.write_config_hc(self.current_chain, path)
        as_build.gather_sw_files(
            self.current_chain, path, use_symlinks, module_driver_dirs
        )

    def _write_asterics_core(
        self,
        path: str,
        use_symlinks: bool = True,
        allow_deletion: bool = False,
        module_driver_dirs: bool = False,
    ) -> bool:
        err_mgr = self.current_chain.err_mgr
        path = self._check_and_get_output_path(path)
        if not path:
            return False
        try:
            as_build.prepare_output_path(None, path, allow_deletion)
        except IOError as err:
            LOG.error(
                ("Could not prepare the output directory '%s'" "! - '%s'"),
                path,
                str(err),
            )
            return False
        try:
            self._write_hw(
                append_to_path(path, "hardware"), use_symlinks, allow_deletion
            )

            if err_mgr.has_errors():
                LOG.critical("Abort! Errors occurred during system build:")
                err_mgr.print_errors()
                return False
            self._write_sw(
                append_to_path(path, "software"),
                use_symlinks,
                allow_deletion,
                module_driver_dirs,
            )
            if err_mgr.has_errors():
                LOG.critical("Abort! Errors occurred during system build:")
                err_mgr.print_errors()
                return False
        except (IOError, AsError) as err:
            LOG.error(str(err))
            err_mgr.print_errors()
            return False
        return True

    TCL_ADDITIONS = (
        'set design "{design}"\n'
        'set partname "{part}"\n'
        'set boardpart "{board}"\n'
        'set display_name "{display_name}"\n'
        'set description "{description}"\n'
    )

    def _write_ip_core_xilinx(
        self,
        path: str,
        use_symlinks: bool = True,
        allow_deletion: bool = False,
        module_driver_dirs: bool = False,
    ):
        err_mgr = self.current_chain.err_mgr
        # Make sure path is good
        path = self._check_and_get_output_path(path)
        if not path:
            return False
        # Clean up if not empty
        try:
            src_path = append_to_path(
                self.asterics_home, self.IP_CORE_TEMPLATE_PATH
            )
            as_build.prepare_output_path(src_path, path, allow_deletion)
        except IOError as err:
            LOG.error(
                ("Could not prepare the output directory '%s'" "! - '%s'"),
                path,
                str(err),
            )
            return False
        # Get paths for HW and SW gen
        sw_path = append_to_path(path, self.DRIVERS_REL_PATH)
        hw_path = append_to_path(path, self.HW_SRC_REL_PATH)
        # Generate and collect source files
        try:
            self._gen_sw(sw_path, use_symlinks, module_driver_dirs)
            if err_mgr.has_errors():
                LOG.critical("Abort! Errors occurred during system build:")
                err_mgr.print_errors()
                return False
            self._gen_hw(hw_path, use_symlinks)
            if err_mgr.has_errors():
                LOG.critical("Abort! Errors occurred during system build:")
                err_mgr.print_errors()
                return False
        except (IOError, AsError) as err:
            LOG.error(str(err))
            return False
        add_c1 = self.TCL_ADDITIONS.format(
            design=self.design_name,
            part=self.partname_hw,
            board=self.board_target,
            display_name=self.ipcore_name,
            description=self.ipcore_descr,
        )
        # Run packaging
        LOG.info("Running packaging in '%s'.", path)
        try:
            as_build.run_vivado_packaging(self.current_chain, path, add_c1)
        except (IOError, AsError) as err:
            LOG.error(str(err))
            return False
        return True

    def _write_system(
        self,
        path: str,
        use_symlinks: bool = True,
        allow_deletion: bool = False,
        module_driver_dirs: bool = False,
        add_vears: bool = False,
    ):
        err_mgr = self.current_chain.err_mgr
        # Make sure path is good
        path = self._check_and_get_output_path(path)
        ip_path = append_to_path(path, self.IP_CORE_REL_PATH)
        if not path:
            return False
        # Clean up if not empty
        try:
            src_path = append_to_path(
                self.asterics_home, self.SYSTEM_TEMPLATE_PATH
            )
            as_build.prepare_output_path(src_path, path, allow_deletion)
        except IOError as err:
            LOG.error(
                ("Could not prepare the output directory '%s'" "! - '%s'"),
                path,
                str(err),
            )
            return False
        # Get paths for HW and SW gen
        sw_path = append_to_path(ip_path, self.DRIVERS_REL_PATH)
        hw_path = append_to_path(ip_path, self.HW_SRC_REL_PATH)
        # Generate and collect source files
        try:
            self._gen_sw(sw_path, use_symlinks, module_driver_dirs)
            if err_mgr.has_errors():
                LOG.critical("Abort! Errors occurred during system build:")
                err_mgr.print_errors()
                return False
            self._gen_hw(hw_path, use_symlinks)
            if err_mgr.has_errors():
                LOG.critical("Abort! Errors occurred during system build:")
                err_mgr.print_errors()
                return False
        except (IOError, AsError) as err:
            LOG.error(str(err))
            return False
        # Run packaging
        LOG.info("Running packaging in '%s'.", ip_path)

        add_c1 = self.TCL_ADDITIONS.format(
            design=self.design_name,
            part=self.partname_hw,
            board=self.board_target,
            display_name=self.ipcore_name,
            description=self.ipcore_descr,
        )
        as_build.run_vivado_packaging(self.current_chain, ip_path, add_c1)

        # Add VEARS core
        if add_vears:
            try:
                as_build.add_vears_core(
                    append_to_path(path, "vivado_cores"),
                    self.asterics_home,
                    use_symlinks,
                )
            except (IOError, AsError) as err:
                LOG.error(str(err))
                return False
        return True

    def _write_system_graph(
        self,
        system=None,
        out_file: str = "asterics_graph",
        show_toplevels: bool = False,
        show_auto_inst: bool = False,
        show_ports: bool = False,
        show_unconnected: bool = False,
        show_line_buffers: bool = False,
    ):
        """! @brief Generate an SVG graph of the generated system.
        Generates and writes a graph representation of the ASTERICS chain
        and, if present, the 2D Window Pipelines using GraphViz Dot.
        This is a wrapper for as_automatics_visual::system_graph() and should be
        called via
        as_automatics_proc_chain::AsProcessingChain::write_system_graph().
        @param system: Chain or pipe object to visualize
                       (AsProcessingChain or As2DWindowPipeline).
        @param out_file: Path and filename of the graph to generate.
                         Default=[asterics_graph]
        @param show_toplevels: Include the toplevel module groups. [False]
        @param show_auto_inst: Include the automatically included modules. [False]
        @param show_ports: Add all ports to the interface edges. [False]
        @param show_unconnected: Write a list of unconnected ports into the module
                                 nodes. WARNING: Many false positives! [False]
        """
        if not as_vis.graphviz_available:
            LOG.critical(
                (
                    "Could not find python package 'graphviz' on your system!"
                    " Cannot generate system graph!\nTry installing it "
                    "using: 'pip install graphviz'"
                )
            )
        elif system is None:
            as_vis.system_graph(
                self.current_chain,
                out_file,
                show_ports,
                show_auto_inst,
                show_unconnected,
                show_toplevels,
                show_line_buffers,
            )
        elif isinstance(system, AsProcessingChain):
            as_vis.system_graph(
                system,
                out_file,
                show_ports,
                show_auto_inst,
                show_unconnected,
                show_toplevels,
                show_line_buffers,
            )

    ## @}
