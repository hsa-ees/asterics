# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# Copyright (C) Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_automatics_env_init.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Handles imports and initialization tasks for the user to enable them to
explore the module library and other features of Automatics.
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
# @file as_automatics_port.py
# @author Philip Manke
# @brief Initialization script for a pseudo-interactive mode of Automatics
# -----------------------------------------------------------------------------

import sys


def as_append_to_path(path: str, to_append: str):
    """Take two path fragments and merge them.
    This function makes sure that each directory is separated by a '/'
    and always returnes the path with a '/' at the end."""
    # Merge to one string
    string = path + "/" + to_append + "/"
    # Split it and filter out empty strings resulting from subsequent "/"es
    strsplit = [s for s in string.split("/") if s != ""]
    # Join the path separating each string by a single "/"
    out = "/".join(strsplit) + "/"
    if string[0] == "/":  # Add a leading "/" if the initial string had one
        return "/" + out
    return out


if __name__ == "__main__":

    print("ASTERICS Automatics: Automatic Processing Chain generator tool")
    print("Starting...")

    source_dir = sys.argv[0].rsplit("/", maxsplit=1)[0]
    asterics_dir = source_dir.rsplit("/", maxsplit=2)[0]

    print("Importing Automatics from '{}'...".format(source_dir))
    sys.path.append(source_dir)
    import as_automatics_logging as as_log
    as_log.init_log(loglevel_console="INFO", loglevel_file="INFO")

    # Even though not all imports are used here,
    # they are included for easy access from the interactive environment.
    # Plz no remove :3 - Thank!
    from as_automatics_env import AsAutomatics
    from as_automatics_proc_chain import AsProcessingChain
    from as_automatics_module import AsModule
    from as_automatics_port import Port
    from as_automatics_interface import Interface
    from as_automatics_module_lib import AsModuleLibrary
    from as_automatics_generic import Generic
    from as_automatics_templates import AsMain, AsTop
    print("Success!")
    # Init Automatics and load standard modules...
    print("Getting default modules from '{}'...".format(asterics_dir))
    auto = AsAutomatics(asterics_dir)

    # User prompt:
    print("Done.")
    print("")
    print("Automatics initialized!")
    print("Use 'as_help()' to list available functions.")

    # User functions start:
    # ----------------------
    def as_help():
        """Print list of available functions"""
        print("")
        print("ASTERICS Automatics: Automatic Processing Chain generator tool")
        print("")
        print("List of Automatics functions:")
        print("  list_modules(verbosity, repo)")
        print("  module_detail(name, repo, verbose)")
        print("  scan_folder(path, repo)")
        print("  get_module(name, repo)")
        print("  get_interface(module, interface_name)")
        print("  get_port(module, port_name)")
        print("  as_help()")
        print("")
        print("Use '<command>?' (no parentheses) for details.")
        print("")

    def list_modules(verbosity: int = 0, repo: str = ""):
        """Print a list of all modules in the library.
        Use parameter 'verbosity' [0, 1, 2, 3] to print with increasing detail.
        Use parameter 'repo' to print only modules in a specific repository.
        Modules in the default ASTERICS installation are in the repo 'default'.
        """
        auto.library.list_modules(verbosity, repo)

    def get_module(name: str, repo: str = ""):
        """Returns the module object for the module matching 'name',
        from the module library.
        Use the 'repo' parameter to only search modules from a specific location
        Modules in the standard ASTERICS installation are in the repo 'default'.
        """
        module = auto.library.get_module_template(name, repo_name=repo)
        if module:
            print("Got module '{}' from repo '{}'!"
                  .format(name, module.repository_name))
            return module
        # Else ->
        if repo == "":
            print("No module '{}' found in any repository!".format(name))
        else:
            print("No module '{}' found in repository '{}'!"
                  .format(name, repo))
        return None

    def module_detail(name: str, verbosity: int = 0, repo: str = ""):
        """List details for a single module 'name'. Use parameter 'repo' to
        specify the module repository, the standard ASTERICS modules are in repo
        'default'. Set parameter 'verbosity' to [0, 1, 2] for increasing detail.
        """
        module = get_module(name, repo)
        if module:
            module.list_module(verbosity)

    def scan_folder(path: str, repo: str = "user"):
        """Let Automatics scan a folder for additional modules.
        The paramter 'path' should point to the directory containing the
        subdirectories containing the modules.
        Use parameter 'repo' to name the repository that the modules are added
        into. Default repository is 'user'."""
        name_list = auto.add_module_repository(path, repo)
        if name_list:
            print("Found the following modules in '{}':".format(path))
            print(name_list)
        else:
            print("Found no modules in '{}'.".format(path))

    def get_port(module, port_name: str) -> Port:
        """Returns the Port object matching 'port_name' in 'module'.
        The 'module' parameter may be a module object or a module name
        (string)."""
        if isinstance(module, AsModule):
            return module.get_port(port_name)
        if isinstance(module, str):
            mod_obj = get_module(module)
            if not mod_obj:
                print("No module with name '{}' found!".format(module))
            else:
                return mod_obj.get_port(port_name)
        # Else ->
        print("Parameter 'module' must be a string or module object!")

    def get_interface(module, interface_name: str,
                      direction: str = "") -> Interface:
        """Returns the Interface object matching 'interface_name' in 'module'.
        The 'module' parameter may be a module object or a module name
        (string). Use parameter 'direction' to specify the interface direction.
        If two of the same interface type are present in a module, it is valid
        for their names to be the same, but the directions different.
        If 'direction' is omitted, the first matching interface is returned."""
        if isinstance(module, AsModule):
            return module.get_interface(interface_name, direction)
        if isinstance(module, str):
            mod_obj = get_module(module)
            if not mod_obj:
                print("No module with name '{}' found!".format(module))
                return None
            # Else ->
            return mod_obj.get_interface(interface_name, direction)
        # Else ->
        print("Parameter 'module' must be a string or module object!")
        return None
    # ----------------------
