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
# @author Philip Manke
# @brief Capsules the entire as_automatics environment.
# -----------------------------------------------------------------------------

import os

from as_automatics_helpers import append_to_path
from as_automatics_module_lib import AsModuleLibrary
from as_automatics_vhdl_writer import VHDLWriter
from as_automatics_exceptions import AsError, AsFileError, AsErrorManager

import as_automatics_builder as as_build
import as_automatics_logging as as_log
import as_automatics_templates as as_templates

LOG = as_log.get_log()


class AsAutomatics():
    """Class bundling the main user-facing functionality of Automatics.
    Should be the only thing you need to import to use Automatics."""

    default_asterics_dir = "/opt/ees/share/asterics/"

    def __init__(self, asterics_dir: str):
        if not asterics_dir:
            self.asterics_dir = self.default_asterics_dir
        else:
            self.asterics_dir = append_to_path(
                os.path.realpath(asterics_dir), "//")

        self.library = AsModuleLibrary(self.asterics_dir)
        self.current_chain = None
        self.windowpipes = []

        self.design_name = "asterics"
        self.board_target = ""
        self.partname_hw = "xc7z010clg400-1"

        self.ipcore_name = "ASTERICS"
        self.ipcore_descr = "ASTERICS Image Processing Chain"

        # Construct and assign interface templates
        as_templates.add_templates()

    def set_hardware_target_definitions(self, partname: str = "",
                                        design: str = "", board: str = ""):
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
        """Add a repository of ASTERICS modules.
        The module repository must be structured in the same way
        as the default module repository.
        For more detail, check the Automatics chapter in the ASTERICS manual.

        Parameters:
        module_dir: Path to the repository folder
            (where the individual module directories are stored)
        repo_name: Name that is internally used to refer to the repository.
        Returns a list of the names of the found modules."""
        return self.library.add_module_repository(module_dir, repo_name)

    @staticmethod
    def __check_and_get_output_path__(path: str) -> bool:
        path = os.path.realpath(path)
        # If path doesn't exist, create the necessary folders
        if not os.path.exists(path):
            try:
                os.makedirs(path, mode=0o755)
            except IOError as err:
                LOG.error(("Automatics: Could not create output directory! - "
                           "'%s' - '%s'"), path, str(err))
                return None
        return path

    # Relative path constants
    # Software driver source file path
    DRIVERS_REL_PATH = "drivers/asterics_v1_0/src/"
    # Hardware source file path
    HW_SRC_REL_PATH = "hw/hdl/vhdl/"
    # Default path for generating the ASTERICS IP Core
    IP_CORE_REL_PATH = "vivado_cores/ASTERICS/"
    # Path to the IP-Core template in the ASTERICS installation
    IP_CORE_TEMPLATE_PATH = "support/sys_template/vivado_cores/ASTERICS/"
    # Path to the system template in the ASTERICS installation
    SYSTEM_TEMPLATE_PATH = "support/sys_template/"

    def __write_hw__(self, path: str, use_symlinks: bool = True,
                     allow_deletion: bool = False):
        # Make sure path is good
        opath = self.__check_and_get_output_path__(path)
        if not opath:
            raise AsFileError(path, "Could not create output folder!")
        opath = append_to_path(opath, "/")
        # Clean up if not empty
        try:
            as_build.prepare_output_path(None, opath, allow_deletion)
        except IOError as err:
            LOG.error(("Could not prepare the output directory '%s'"
                       "! - '%s'"), opath, str(err))
            raise AsFileError(opath, "Could not write to output folder!")
        # Generate and collect hardware files
        try:
            self.__gen_hw__(opath, use_symlinks)
        except IOError:
            LOG.error(("Cannot write to '%s'! - "
                       "Could not create VHDL source files!"), opath)
            return False
        except AsError as err:
            LOG.error(str(err))
            return False

    def __gen_hw__(self, path: str, use_symlinks: bool = True):
        err_mgr = self.current_chain.err_mgr
        if err_mgr.has_errors():
            LOG.critical("%s errors encountered!\nGeneration aborted!",
                         str(err_mgr.get_error_count()))
            raise AsError(severity="Critical")
        # Instantiate VHDL writer class
        writer = VHDLWriter(self.current_chain)
        # Generate as_main.vhd and asterics.vhd
        writer.write_as_main_vhd(path)
        writer.write_asterics_vhd(path)
        # Collect the hardware and software source files
        as_build.gather_hw_files(self.current_chain, path, use_symlinks)

    def __write_sw__(
            self,
            path: str,
            use_symlinks: bool = True,
            allow_deletion: bool = False,
            module_driver_dirs: bool = False):
        # Make sure path is good
        path = self.__check_and_get_output_path__(path)
        if not path:
            return False
        path = append_to_path(path, "/")
        # Clean up if not empty
        try:
            as_build.prepare_output_path(None, path, allow_deletion)
        except IOError as err:
            LOG.error(("Could not prepare the output directory '%s'"
                       "! - '%s'"), path, str(err))
            return False
        # Generate and collect software files
        try:
            self.__gen_sw__(path, use_symlinks, module_driver_dirs)
        except (IOError, AsError) as err:
            LOG.error(str(err))
            return False
        return True

    def __gen_sw__(self, path: str, use_symlinks: bool = True,
                   module_driver_dirs: bool = False):
        err_mgr = self.current_chain.err_mgr
        if err_mgr.has_errors():
            LOG.critical("%s errors encountered!\nGeneration aborted!",
                         str(err_mgr.get_error_count()))
            raise AsError(severity="Critical")
        as_build.write_asterics_h(self.current_chain, path)
        as_build.write_config_c(path)
        as_build.gather_sw_files(self.current_chain, path,
                                 use_symlinks, module_driver_dirs)

    def __write_asterics_core__(
            self,
            path: str,
            use_symlinks: bool = True,
            allow_deletion: bool = False,
            module_driver_dirs: bool = False) -> bool:
        path = self.__check_and_get_output_path__(path)
        if not path:
            return False
        try:
            as_build.prepare_output_path(None, path, allow_deletion)
        except IOError as err:
            LOG.error(("Could not prepare the output directory '%s'"
                       "! - '%s'"), path, str(err))
            return False
        try:
            self.__write_hw__(append_to_path(path, "hardware"), use_symlinks,
                            allow_deletion)
            self.__write_sw__(append_to_path(path, "software"), use_symlinks,
                            allow_deletion, module_driver_dirs)
        except (IOError, AsError) as err:
            LOG.error(str(err))
            return False
        return True

    TCL_ADDITIONS = ('set design "{design}"\n'
                     'set partname "{part}"\n'
                     'set boardpart "{board}"\n'
                     'set display_name "{display_name}"\n'
                     'set description "{description}"\n')

    def __write_ip_core_xilinx__(
            self,
            path: str,
            use_symlinks: bool = True,
            allow_deletion: bool = False,
            module_driver_dirs: bool = False):
        # Make sure path is good
        path = self.__check_and_get_output_path__(path)
        if not path:
            return False
        # Clean up if not empty
        try:
            src_path = append_to_path(
                self.asterics_dir, self.IP_CORE_TEMPLATE_PATH)
            as_build.prepare_output_path(src_path, path, allow_deletion)
        except IOError as err:
            LOG.error(("Could not prepare the output directory '%s'"
                       "! - '%s'"), path, str(err))
            return False
        # Get paths for HW and SW gen
        sw_path = append_to_path(path, self.DRIVERS_REL_PATH)
        hw_path = append_to_path(path, self.HW_SRC_REL_PATH)
        # Generate and collect source files
        try:
            self.__gen_sw__(sw_path, use_symlinks, module_driver_dirs)
            self.__gen_hw__(hw_path, use_symlinks)
        except (IOError, AsError) as err:
            LOG.error(str(err))
            return False
        add_c1 = self.TCL_ADDITIONS.format(design=self.design_name,
                                           part=self.partname_hw,
                                           board=self.board_target,
                                           display_name=self.ipcore_name,
                                           description=self.ipcore_descr)
        # Run packaging
        LOG.info("Running packaging in '%s'.", path)
        try:
            as_build.run_vivado_packaging(self.current_chain, path, add_c1)
        except (IOError, AsError) as err:
            LOG.error(str(err))
            return False
        return True

    def __write_system__(
            self,
            path: str,
            use_symlinks: bool = True,
            allow_deletion: bool = False,
            module_driver_dirs: bool = False,
            add_vears: bool = False):
        # Make sure path is good
        path = self.__check_and_get_output_path__(path)
        ip_path = append_to_path(path, self.IP_CORE_REL_PATH)
        if not path:
            return False
        # Clean up if not empty
        try:
            src_path = append_to_path(
                self.asterics_dir, self.SYSTEM_TEMPLATE_PATH)
            as_build.prepare_output_path(src_path, path, allow_deletion)
        except IOError as err:
            LOG.error(("Could not prepare the output directory '%s'"
                       "! - '%s'"), path, str(err))
            return False
        # Get paths for HW and SW gen
        sw_path = append_to_path(ip_path, self.DRIVERS_REL_PATH)
        hw_path = append_to_path(ip_path, self.HW_SRC_REL_PATH)
        # Generate and collect source files
        try:
            self.__gen_sw__(sw_path, use_symlinks, module_driver_dirs)
            self.__gen_hw__(hw_path, use_symlinks)
        except (IOError, AsError) as err:
            LOG.error(str(err))
            return False
        # Run packaging
        LOG.info("Running packaging in '%s'.", ip_path)

        add_c1 = self.TCL_ADDITIONS.format(design=self.design_name,
                                           part=self.partname_hw,
                                           board=self.board_target,
                                           display_name=self.ipcore_name,
                                           description=self.ipcore_descr)
        as_build.run_vivado_packaging(self.current_chain, ip_path, add_c1)

        # Add VEARS core
        if add_vears:
            try:
                as_build.add_vears_core(append_to_path(path, "vivado_cores"),
                                        self.asterics_dir, use_symlinks)
            except (IOError, AsError) as err:
                LOG.error(str(err))
                return False
        return True
