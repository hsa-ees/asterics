# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
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

## @defgroup automatics The ASTERICS system generator Automatics

## @defgroup automatics_cds Methods for use in Automatics Scripts
# @ingroup automatics

## @defgroup automatics_internal Internal functions and methods of Automatics
# @ingroup automatics

## @defgroup automatics_2dwpl Methods for 2D Window Pipeline descriptions
# @ingroup automatics

## @defgroup automatics_gui_legacy Methods and classes of the Automatics Module Browser (legacy)
# @ingroup automatics

## @defgroup automatics_gui Methods and classes of the ASTERICS GUI
# @ingroup automatics

## @defgroup automatics_cli Methods of the Automatics Module Browser CLI
# @ingroup automatics

## @defgroup automatics_cnn Methods and classes for building CNN systems
# @ingroup automatics

## @defgroup automatics_usertemp Templates for users of Automatics
# @ingroup automatics

## @defgroup automatics_logging Logging functionalities of Automatics
# @ingroup automatics_internal

## @defgroup automatics_errors Error handling in Automatics
# @ingroup automatics_internal

## @defgroup automatics_generate Generation (HW&SW) methods of Automatics
# @ingroup automatics_internal

## @defgroup automatics_connection Connection methods of Automatics
# @ingroup automatics_internal

## @defgroup automatics_helpers Helper methods of Automatics
# @ingroup automatics_internal

## @defgroup automatics_intrep Classes for internal system representations
# @ingroup automatics_internal

## @defgroup automatics_analyze Analysis functionalities of Automatics
# @ingroup automatics_internal

## @defgroup automatics_mm Module management methods and classes
# @ingroup automatics_internal

## @file asterics.py
# @ingroup automatics_cds
# @author Philip Manke
# @brief Capsules the entire as_automatics environment.
# -----------------------------------------------------------------------------

import os

###############################
# Automatics version number
Automatics_version = "0.3.002"
###############################

# Initialization: Get ASTERICS installation directory
asterics_home = None

try:
    asterics_home = os.environ.get("ASTERICS_HOME")
except KeyError:
    print("ERROR: ASTERICS_HOME not set!")
    print("Source the ASTERICS settings.sh file before running Automatics!")
    print("Use: source <path/to/asterics/>settings.sh")
    exit()

automatics_home = None
try:
    automatics_home = os.environ.get("ASTERICS_AUTOMATICS_HOME")
except KeyError:
    print("ERROR: ASTERICS_AUTOMATICS_HOME not set!")
    print("Source the ASTERICS settings.sh file before running Automatics!")
    print("Use: source <path/to/asterics/>settings.sh")
    exit()

is_vivado_available = False
try:
    is_vivado_available = (
        True
        if (
            os.environ.get("EES_VIVADO_SETTINGS")
            or os.environ.get("XILINX_VIVADO")
        )
        else False
    )
except KeyError:
    pass


# Import Automatics
from as_automatics_env import AsAutomatics
from as_automatics_proc_chain import AsProcessingChain
from as_automatics_2d_pipeline import As2DWindowPipeline
from as_automatics_cnn_layer import AsNNLayer
from as_automatics_helpers import append_to_path
from as_automatics_module_group import Register
from as_automatics_module import AsModule
from as_automatics_interface import Interface

import as_automatics_builder as as_build
import as_automatics_logging as as_log
import as_automatics_exceptions as as_err

# Initialize logging
LOG = as_log.init_log()

# Initialize Automatics - scan default modules
Auto = AsAutomatics(asterics_home, Automatics_version)

# Automatics high-level functions:


##
# @addtogroup automatics_cds
# @{


def set_asterics_directory(path: str) -> bool:
    # Cleanup path input
    path = os.path.realpath(append_to_path(path, "/"))
    if os.path.isdir(path):
        Auto.asterics_dir = path
        LOG.info("ASTERICS home directory set to '%s'.", path)
        return True
    # -> Else
    LOG.error("Path '%s' is not a directory! ASTERICS home not set!", path)
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
            "Incompatible Automatics version! Script requires version {}".format(
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
    """! @brief Provide a new AsProcessingChain object.
    This allows you to specify and build a new ASTERICS processing chain.
    When building multiple systems in one script, make sure build the system,
    before calling this again to start the second system!
    @return  A new ASTERICS processing chain."""
    AsProcessingChain.err_mgr = as_err.AsError.err_mgr
    # Add "standard" ASTERICS modules
    Auto.add_module_repository(
        append_to_path(asterics_home, "modules"), "default"
    )
    Auto.current_chain = AsProcessingChain(Auto.library, parent=Auto)
    return Auto.current_chain


def new_2d_window_pipeline(
    image_width: int,
    image_height: int = 480,
    name: str = "",
    force_synchronous_pipeline: bool = None,
) -> As2DWindowPipeline:
    """! @brief Provide a new As2DWindowPipeline object.
    This allows you to specify and build a new ASTERICS 2D Window Pipeline for
    processing image data using convolution and other two dimensional filters.
    You need to provide the dimensions of the image data you want to process,
    as the pipeline size and resource usage is highly dependend on the size of
    the image data.
    @param image_width: The number of horizontal pixels per image row
    @param image_height: The number of vertical pixels per image column (optional)
    @param name: The name of the pipeline (optional)
    @param force_synchronous_pipeline: Wether the pipeline should be implemented in
        a synchronous design, i.e. all modules will utilize the same
        "Strobe" (data valid) signal, including the pipeline's output.
        Leave as "None" if you're not sure, to let Automatics choose.
    @return  A new As2DWindowPipeline object."""
    if not Auto.current_chain:
        LOG.error(
            (
                "Before creating a new 2D Window Pipeline, you first have to"
                " create an ASTERICS processing chain using"
                " 'asterics.new_chain()'"
            )
        )
        raise as_err.AsTextError(
            "",
            msg="2D Window Pipeline construction requires a processing chain.",
            detail=(
                "Call 'asterics.new_chain()' before "
                "'asterics.new_2d_window_pipeline()'."
            ),
            severity="Critical",
        )
    if not name:
        name = "as_window_pipe_{}".format(len(Auto.windowpipes))
    pipe = As2DWindowPipeline(
        image_width, image_height, name, chain=Auto.current_chain
    )
    if force_synchronous_pipeline is not None:
        pipe.set_pipeline_synchronous(force_synchronous_pipeline)
    Auto.windowpipes.append(pipe)
    return pipe


## @ingroup automatics_cnn
def new_nn_layer(
    image_width: int, image_height: int = 480, name: str = ""
) -> AsNNLayer:
    """! @brief Provide a new AsNNLayer object.
    This allows implementation of a neural network layer using
    a 2D Window Pipeline.
    You need to provide the width and optionally height of the input image.
    Provide a unique name, if you want to implement multiple layers.
    After creating a new layer object using this method,
    use 'layer.parametrize_and_build()' to configure the layer.
    @param image_width: The number of horizontal pixels per image row
    @param image_height: The number of vertical pixels per image column
    @param name: The name of the layer
    @return A new AsNNLayer object.
    """
    if not Auto.current_chain:
        LOG.error(
            (
                "Before creating a new AsNNLayer, you first have to"
                " create an ASTERICS processing chain using"
                " 'asterics.new_chain()'"
            )
        )
        raise as_err.AsTextError(
            "",
            msg="AsNNLayer construction requires a processing chain.",
            detail=(
                "Call 'asterics.new_chain()' before "
                "'asterics.new_nn_layer()'."
            ),
            severity="Critical",
        )
    if not name:
        name = "as_nn_layer_{}".format(len(Auto.windowpipes))
    layer = AsNNLayer(image_width, image_height, name, chain=Auto.current_chain)
    Auto.windowpipes.append(layer)
    return layer


def define_hardware_target(
    partname: str = "", design_name: str = "", board: str = ""
):
    """! @brief Define parameters for your hardware target.
    @warning This will set attributes into a TCL script imported by
    the synthesis tool! Make sure you get the internal names used by your tool!
    @param partname  The internal name of the target FPGA
    @param design_name  The name of the IP-Core design
    @param board  The internal name of the targeted board
    """
    Auto.set_hardware_target_definitions(partname, design_name, board)


def set_ipcore_name(name: str, description: str = ""):
    """! @brief Set a new name and optionally a description of the ASTERICS IP-Core.
    Defaults are: name = "ASTERICS", description = "ASTERICS Image Processing Chain".
    @param name  The short name of the generated IP-Core
    @param description  The description shown for the IP-Core
    """
    Auto.set_ipcore_name(name)
    if description:
        Auto.set_ipcore_description(description)


def add_module_repository(path: str, repository_name: str = "user") -> bool:
    """! @brief Retrieve ASTERICS modules from another location.
    @param path: Where to scan for ASTERICS modules.
    @param repository_name: (optional) Store the found modules in a reposotory of
                         this name. Default: 'user'
    @return True if the analysis is successful, False on error.
    """
    try:
        modules = Auto.add_module_repository(path, repository_name)
    except as_err.AsError:
        return False
    LOG.info("Imported the following list of modules:")
    LOG.info(str(modules))
    return True


def add_global_interface_template(template: Interface) -> bool:
    """! @brief Add a new interface template class to use
    for all modules that are imported.
    @param template: An instance of the interface template to add.
                     Must inherit from the class Interface.
    @return True if the template was successfully added,
            False if a template of this name already exists."""
    return AsModule.add_global_interface_template(template)


def vears(path: str, use_symlinks: bool = True, force: bool = False) -> bool:
    """! @brief Copy or link the VEARS video output IP-Core.
    @param path: Where to copy/link VEARS to.
    @param use_symlinks: Wether to link or copy VEARS. Default: True -> Link VEARS
    @param force: Allow Automatics to overwrite 'path' if it already exists.
               Warning - This will permanently delete data! Default: False
    """
    try:
        as_build.add_vears_core(path, asterics_home, use_symlinks, force)
    except as_err.AsError:
        return False
    return True


def set_loglevel(console: str = "warning", logfile: str = "info"):
    """! @brief Set the logging severity level for the console and log file outputs.
    Valid loglevels are: debug, info, warning, error, critical.
    @param console: The loglevel for the console output [default: warning].
    @param logfile: The loglevel for the logfile output [default: info]."""
    as_log.set_loglevel(console, logfile)


def quiet():
    """! @brief Set the loglevel for the console to CRITICAL."""
    set_loglevel(console="CRITICAL")


def verbose():
    """! @brief Set the loglevel for the console to INFO."""
    set_loglevel(console="INFO")


def list_errors():
    """! @brief List all errors encountered so far on the commandline."""
    as_err.list_errors()


## @} (addtogroup automatics_cds)
