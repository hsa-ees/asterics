# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# Copyright (C) Hochschule Augsburg, University of Applied Sciences
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
import as_automatics_logging as as_log

LOG = as_log.init_log()

# Initialization: Get ASTERICS installation directory
try:
    as_path = os.environ.get("ASTERICS_HOME")
except KeyError:
    print("ERROR: ASTERICS_HOME not set!")
    print("Source the ASTERICS settings.sh file before running Automatics!")
    exit()
if not as_path:
    print("ERROR: ASTERICS_HOME not set!")
    print("Source the ASTERICS settings.sh file before running Automatics!")
    exit()

# Initialize Automatics - scan default modules
Auto = AsAutomatics(as_path)
Chain = None


def new_chain():
    """Provide a new AsProcessingChain object.
    This allows you to specify and build a new ASTERICS processing chain.
    When building multiple systems in one script, make sure build the system,
    before calling this again to start the second system!"""
    Chain = AsProcessingChain(Auto.library, parent=Auto)
    Auto.current_chain = Chain
    return Chain

def define_hardware_target(partname : str, design_name : str, board : str = ""):
    Auto.set_hardware_target_definitions(partname, design_name, board)

def add_module_repository(path: str, repository_name: str = "user"):
    """Retrieve ASTERICS modules from another location.
    Prints the names of found modules.
    Parameters:
        path: Where to scan for ASTERICS modules.
        repository_name: (optional) Store the found modules in a reposotory of
                         this name. Default: 'user'
    """
    modules = Auto.add_module_repository(path, repository_name)
    print("Imported the following list of modules:")
    print(modules)

def vears(path: str, use_symlinks: bool = True):
    """Copy or link the VEARS video output IP-Core.
    Parameters:
        path: Where to copy/link VEARS to.
        use_symlinks: Wether to link or copy VEARS. Default: True -> Link VEARS
    """
    as_build.add_vears_core(path, as_path, use_symlinks)

def set_loglevel(console: str = "warning", logfile: str = "info"):
    """Set the logging severity level for the console and log file outputs.
    Valid loglevels are: debug, info, warning, error, critical.
    Parameters:
        console: The loglevel for the console output [default: warning].
        logfile: The loglevel for the logfile output [default: info]."""
    as_log.set_loglevel(console, logfile)
