# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
#
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
# @file asterics.py
# @author Philip Manke
# @brief Capsules the entire as_automatics environment.
# -----------------------------------------------------------------------------

import os

from as_automatics_env import AsAutomatics
import as_automatics_builder as as_build
from as_automatics_proc_chain import AsProcessingChain
from as_automatics_2d_pipeline import As2DWindowPipeline
import as_automatics_logging as as_log
import as_automatics_exceptions as as_err
from as_automatics_helpers import append_to_path

LOG = as_log.init_log()

# Initialization: Get ASTERICS installation directory
try:
    as_path = os.environ.get("ASTERICS_HOME")
except KeyError:
    as_path = None
if not as_path:
    print("ERROR: ASTERICS_HOME not set!")
    print("Source the ASTERICS settings.sh file before running Automatics!")
    exit()


# Initialize Automatics - scan default modules
Auto = AsAutomatics(as_path)
Automatics_version = "0.2.012"


def set_asterics_directory(path: str) -> bool:
    # Cleanup path input
    path = os.path.realpath(append_to_path(path, "/"))
    if os.path.isdir(path):
        Auto.asterics_dir = path
        LOG.info("ASTERICS home directory set to '%s'.", path)
        return True
    # -> Else
    LOG.warning("Path '%s' is not a directory! ASTERICS home not set!", path)
    return False


def print_version(only_version_number: bool = False):
    if only_version_number:
        print(Automatics_version)
    else:
        print("This is Automatics version " + Automatics_version)


def requires_version(version: str) -> bool:
    if Automatics_version != version:
        LOG.error(
            "Version check failed! This is Automatics version {}!".format(
                Automatics_version
            )
        )
        raise ValueError(
            ("Incompatible Automatics version! Script requires " "version {}").format(
                version
            )
        )
    else:
        return True


def requires_at_least_version(version: str) -> bool:
    if Automatics_version <= version:
        LOG.error(
            "Version check failed! This is Automatics version {}!".format(
                Automatics_version
            )
        )
        raise ValueError(
            (
                "Incompatible Automatics version! Script requires at "
                "least version {}"
            ).format(version)
        )
    else:
        return True


def new_chain() -> AsProcessingChain:
    """Provide a new AsProcessingChain object.
    This allows you to specify and build a new ASTERICS processing chain.
    When building multiple systems in one script, make sure build the system,
    before calling this again to start the second system!"""
    AsProcessingChain.err_mgr = as_err.AsError.err_mgr
    # Add "standard" ASTERICS modules
    Auto.add_module_repository(append_to_path(as_path, "modules"), "default")
    Auto.current_chain = AsProcessingChain(Auto.library, parent=Auto)
    return Auto.current_chain


def new_2d_window_pipeline(image_width: int, image_height: int) -> As2DWindowPipeline:
    """Provide a new As2DWindowPipeline object.
    This allows you to specify and build a new ASTERICS 2D Window Pipeline for
    processing image data using convolution and other two dimensional filters.
    You need to provide the dimensions of the image data you want to process,
    as the pipeline size and resource usage is highly dependend on the size of
    the image data.
    Parameters:
        image_width: The number of horizontal pixels per image row
        image_height: The number of vertical pixels per image column
    Returns a new As2DWindowPipeline object."""
    if not Auto.current_chain:
        LOG.error(
            (
                "Before creating a new 2D Window Pipeline, you first have to"
                " create an ASTERICS Processing Chain using"
                " 'asterics.new_chain()'"
            )
        )
        raise as_err.AsTextError(
            "",
            msg=("2D Window Pipeline construction " "requires a processing chain."),
            detail=(
                "Call 'asterics.new_chain()' before "
                "'asterics.new_2d_window_pipeline()'."
            ),
            severity="Critical",
        )
    pipe = As2DWindowPipeline(image_width, image_height, chain=Auto.current_chain)
    Auto.windowpipes.append(pipe)
    return pipe


def define_hardware_target(partname: str = "", design_name: str = "", board: str = ""):
    """Define parameters for your hardware target.
    Caution: This will set attributes into a TCL script imported by 
    the synthesis tool! Make sure you get the internal names used by your tool!
    """
    Auto.set_hardware_target_definitions(partname, design_name, board)


def set_ipcore_name(name: str, description: str = ""):
    """Set a new name and optionally a description of the ASTERICS IP-Core.
    Defaults are: name = "ASTERICS"
                  description = "ASTERICS Image Processing Chain"."""
    Auto.set_ipcore_name(name)
    if description:
        Auto.set_ipcore_description(description)


def add_module_repository(path: str, repository_name: str = "user") -> bool:
    """Retrieve ASTERICS modules from another location.
    Parameters:
        path: Where to scan for ASTERICS modules.
        repository_name: (optional) Store the found modules in a reposotory of
                         this name. Default: 'user'
    Returns True or False
    """
    try:
        modules = Auto.add_module_repository(path, repository_name)
    except as_err.AsError:
        return False
    LOG.info("Imported the following list of modules:")
    LOG.info(str(modules))
    return True


def vears(path: str, use_symlinks: bool = True, force: bool = False) -> bool:
    """Copy or link the VEARS video output IP-Core.
    Parameters:
        path: Where to copy/link VEARS to.
        use_symlinks: Wether to link or copy VEARS. Default: True -> Link VEARS
        force: Allow Automatics to overwrite 'path' if it already exists.
               Warning - This will permanently delete data! Default: False
    """
    try:
        as_build.add_vears_core(path, as_path, use_symlinks, force)
    except as_err.AsError:
        return False
    return True


def set_loglevel(console: str = "warning", logfile: str = "info"):
    """Set the logging severity level for the console and log file outputs.
    Valid loglevels are: debug, info, warning, error, critical.
    Parameters:
        console: The loglevel for the console output [default: warning].
        logfile: The loglevel for the logfile output [default: info]."""
    as_log.set_loglevel(console, logfile)


def quiet():
    """Set the loglevel for the console to CRITICAL."""
    set_loglevel(console="CRITICAL")


def verbose():
    """Set the loglevel for the console to INFO."""
    set_loglevel(console="INFO")


def list_errors():
    as_err.list_errors()
