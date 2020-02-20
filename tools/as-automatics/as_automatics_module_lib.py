# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# Copyright (C) Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_automatics_module_lib.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
This file implements the as_automatics module library.
The internal representations of ASTERICS modules are collected and managed.
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
# @file as_automatics_module_lib.py
# @author Philip Manke
# @brief Implements the module library feature for as_automatics.
# -----------------------------------------------------------------------------

import os
import importlib.util as importutil
from typing import Sequence
from copy import copy, deepcopy

from as_automatics_module import AsModule
from as_automatics_exceptions import AsModuleError
from as_automatics_helpers import append_to_path
import as_automatics_logging as as_log

LOG = as_log.get_log()


class AsModuleRepo():
    """Repository for AsModule template objects, read in through
    the AsModuleLibrary. Stores modules read from the same source together."""

    def __init__(self, repo_name: str, path: str):
        self.name = repo_name
        self.path = os.path.realpath(path)
        self.module_names = []
        self.modules = {}

    def register_module(self, module: AsModule):
        """Add a module to this repository object."""
        if module.entity_name not in self.module_names:
            self.module_names.append(module.entity_name)
            self.modules[module.entity_name] = module
            module.repository_name = self.name
            return True
        return False

    def has_module(self, entity_name: str) -> bool:
        """Returns 'True' if a module with the name 'entity_name'
        is stored in this repository object."""
        return entity_name in self.module_names

    def get_module(self, entity_name: str) -> AsModule:
        """Return the module object template of the module with the name
        'entity_name' if it is present in this repository object."""
        try:
            return self.modules[entity_name]
        except KeyError:
            raise AsModuleError(entity_name, msg="Could not find module")


class AsModuleLibrary():
    """Handle all AsModule object templates.
    Contains the methods to read and create AsModule objects from VHDL sources.
    Contains the repositories of AsModule object templates
    to access and provide the objects to the rest of Automatics."""

    SCRIPT_FOLDER = "hardware/automatics"

    def __init__(self, asterics_dir: str):
        self.asterics_dir = asterics_dir  # ASTERICS install path (unused?)
        self.modules = {}  # Dictionary for easier access to modules (unused?)
        self.repos = []  # List storing the module repositories

    def add_module_repository(
            self,
            path: str,
            repo_name: str) -> Sequence[str]:
        """Add a repository to the module library.
        Parameters:
        path: Path to the repository directory.
              Automatics will search for modules here.
        repo_name: Name with which to refer to the repository to.
        No return value."""
        LOG.debug("Adding module repository '%s' for path '%s'...",
                  repo_name, path)
        repo = AsModuleRepo(repo_name, path)
        module_names = self.__get_and_add_modules_from_dir__(path, repo)
        self.repos.append(repo)
        LOG.info(("Found and registered %i modules in repository '%s'"
                  " from '%s'."), len(module_names), repo_name, path)
        return module_names

    def get_repo(self, repo_name: str) -> AsModuleRepo:
        """Return the module repository with the name 'repo_name'.
        Returns 'None' if no match is found."""
        for repo in self.repos:
            if repo.name == repo_name:
                return repo
        return None

    def has_module(self, module_name: str, repo: str = "") -> bool:
        """Searches the ModuleLibrary for a module
        with the entity name 'module_name'.
        Optionally only searches in the repository 'repo'.
        Parameters:
        module_name: The module name to search for.
                Modules are named after their toplevel VHDL entity.
        repo: Optional parameter. Search only in repository 'repo'.
        Returns True if a matching module was found, False otherwise."""

        module_name = module_name.lower()
        if not repo:
            search = self.repos
        else:
            search = [self.get_repo(repo)]
            if not search:
                LOG.error("Repository '%s' does not exist!", repo)
                return False

        for search_repo in search:
            if search_repo.has_module(module_name):
                return True
        return False

    def get_module_template(self, module_name: str,
                            repo_name: str = "") -> AsModule:
        """Search for and return a reference to the AsModule with the entity
        name 'module_name' in the AsModuleLibrary.
        Alternatively search only in module repository 'repo_name'.
        Note: Do NOT add the return value to an AsProcessingChain!
        To get an AsModule to use in a chain use 'get_module_instance' instead!
        Parameters:
        module_name: The module name to search for.
                Modules are named after their toplevel VHDL entity.
        repo_name: Optional. Search only in module repository 'repo_name'.
        Returns a reference to the matching module, 'None' if no match found.
        """
        repo = None
        module_name = module_name.lower()
        # If no reponame was defined, check all repos
        if repo_name == "":
            for irepo in self.repos:
                if irepo.has_module(module_name):
                    repo = irepo
                    break
        else:
            repo = self.get_repo(repo_name)
        if repo is None:
            return None
        return repo.get_module(module_name)

    def get_module_instance(self, module_name: str,
                            repo_name: str = "") -> AsModule:
        """Search for and return a copy to the AsModule with the entity
        name 'module_name' in the AsModuleLibrary.
        Alternatively search only in module repository 'repo_name'.
        Note: Only use this function if you want to modify the module object.
        Else you might want to use 'get_module_template', for better performance
        Parameters:
        module_name: The module name to search for.
                Modules are named after their toplevel VHDL entity.
        repo_name: Optional. Search only in module repository 'repo_name'.
        Returns a copy to the matching module object, 'None' if no match found.
        """
        template = self.get_module_template(module_name, repo_name)
        if template:
            return deepcopy(template)
        # Else ->
        return None

    def get_module_names(self) -> Sequence[str]:
        """Return a list of the entity name of all modules in the library."""
        out = []
        for repo in self.repos:
            out.extend(repo.module_names)
        return out

    def get_module_dict(self) -> dict:
        """Return a dictionary containing references to all modules.
        The dictionary is keyed with the repository names."""
        out = {}
        for repo in self.repos:
            out[repo.name] = repo.modules
        return out

    def list_modules(self, verbosity: bool = 0, repo_name: str = ""):
        """List the modules present in this module library using three degrees
           of verbosity: 0 (minimal), 1 (verbose), 2 (very verbose).
           Use repo_name to list modules of only the repo 'repo_name'."""

        mods = self.get_module_dict()
        for reponame in mods:
            if repo_name:
                if repo_name != reponame:
                    continue
            print("Repository '{}':".format(reponame))
            modnames = list(mods[reponame].keys())
            modnames.sort()
            if verbosity == 0:
                print(modnames)
                continue
            # For verbosity > 0: print module details
            for module in modnames:
                mods[reponame][module].list_module(verbosity - 1)
                print("~~~~~~")
            print("\n")


    @staticmethod
    def add_module(module: AsModule, repo: AsModuleRepo) -> bool:
        """Add an AsModule object to the ModuleLibrary.
        Duplicate modules are ignored.
        Parameters:
        module: The AsModule object to add.
        repo: The Repository object to add the module to.
        Returns True on success, else False."""
        if not isinstance(module, AsModule):
            LOG.error(("Couldn't add module '%s' to module lib. "
                       "Not an AsModule object!"), str(module))
            return False

        if repo.has_module(module.entity_name):
            LOG.debug("Module '%s' already in module lib, skipping",
                      module.name)
            return False
        LOG.debug("Adding module '%s' to module library.", module.entity_name)
        # Add the module to the library
        return repo.register_module(module)

    def get_module_repo(self, module_name: str) -> str:
        """Return the repository name of the module matching 'module_name'."""
        for repo in self.repos:
            if repo.has_module(module_name):
                return repo.name
        raise AsModuleError(
            module_name, msg="Could not find module in library")

    @staticmethod
    def __script_name_valid__(name: str) -> bool:
        return name[:3] == "as_" and name[-8:] == "_spec.py"

    @classmethod
    def __get_module_scripts_in_dir__(cls, module_dir: str) -> Sequence[str]:
        scripts = []
        module_dir = os.path.realpath(module_dir)
        mod_folders = os.listdir(append_to_path(module_dir, ""))
        for folder in mod_folders:
            folder_path = append_to_path(module_dir, folder)
            if not os.path.isdir(folder_path):
                continue
            script_path = append_to_path(folder_path, cls.SCRIPT_FOLDER)
            if not os.path.isdir(script_path):
                continue
            for file in os.listdir(script_path):
                if cls.__script_name_valid__(file):
                    scripts.append((folder_path, script_path + file))
        return scripts

    @classmethod
    def __get_modules_from_dir__(cls, module_dir: str) -> Sequence[AsModule]:
        # Make sure the module path is valid syntactically and ends in a "/"
        module_dir = append_to_path(module_dir, "/")
        module_list = []
        # Get all module initialization scripts
        script_list = cls.__get_module_scripts_in_dir__(module_dir)
        for script in script_list:
            module_folder = script[0]
            script_path = script[1]
            script_name = script_path.rsplit("/", maxsplit=1)[-1]

            # For each valid script: run the contained function
            # 'get_module_instance'
            LOG.debug("Modlib importing script '%s' ...", script_name)
            # Get Python module spec
            spec = importutil.spec_from_file_location(script_name, script_path)
            # Get Python module and run / load it
            imported_script = importutil.module_from_spec(spec)
            spec.loader.exec_module(imported_script)
            LOG.debug("Modlib calls 'get_module_inst' of script '%s'",
                      script_name)
            # Execute the function "get_module_instance"
            module_inst = imported_script.get_module_instance(module_folder)
            LOG.debug("Modlib received '%s' from script '%s'",
                      str(module_inst), script_name)
            # If the output is an AsModule, add it to the library
            if isinstance(module_inst, AsModule):
                # Add the module source dir, making sure it
                module_inst.module_dir = module_folder
                module_list.append(module_inst)
        return module_list

    def __get_and_add_modules_from_dir__(self, module_dir: str,
                                         repo: AsModuleRepo) -> Sequence[str]:
        modules = self.__get_modules_from_dir__(module_dir)
        name_list = []
        # Count the number of modules that are actually added to the library
        for mod in modules:
            if self.add_module(mod, repo):
                name_list.append(mod.entity_name)
        return name_list
