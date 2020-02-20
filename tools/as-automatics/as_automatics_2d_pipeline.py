# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# Copyright (C) Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_automatics_2d_pipeline.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Class managing the construction of a 2D-Window-Pipeline.
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
# @file as_automatics_2d_pipeline.py
# @author Philip Manke
# @brief Class managing the construction of a 2D-Window-Pipeline.
# -----------------------------------------------------------------------------

from as_automatics_proc_chain import AsProcessingChain
from as_automatics_module import AsModule
from as_automatics_window_module import AsWindowModule
from as_automatics_port import Port
from as_automatics_interface import Interface
from as_automatics_exceptions import AsAssignError, AsModuleError

import as_automatics_logging as as_log

LOG = as_log.get_log()


# TODO:
# Find good way to pass window to filter module in fewest possible ports
# New Repo/Category for Window modules in the library



class As2DWindowPipeline():

    class AsLayer():
        def __init__(self, name: str, data_width: int):
            self.modules = []
            self.interfaces = []
            self.data_width = data_width
            self.start_ref = None
            self.end_ref = None


    def __init__(self, chain: AsProcessingChain):
        self.window_modules = []
        self.layers = []
        self.chain = chain

    def define_layer(self, name: str, data_width: int):
        """Define a datalayer in the pipeline.
        Layers are used to connect window modules to each other.
        At least two layers (input & output) are required for every pipeline."""
        self.layers.append(self.AsLayer(name, data_width))


    def add_module(self, entity_name: str, user_name: str = "",
                   repository: str = "") -> AsWindowModule:
        """Add a window module to the pipeline.
        Parameters:
            'entity_name': Name of the window module to add (as in VHDL)
            'user_name': Optional. Name used in generated code for this module
            'repository': Optional. Where to look for the module.
        """
        if not user_name:
            count = len([1 for mod in self.window_modules
                         if mod.entity_name == entity_name])
            user_name = "{}_{}".format(entity_name, count)
        module = self.chain.library.get_module_instance(entity_name, repository, True)
        if module is None:
            raise AsModuleError(entity_name,
                                msg="No window module with this name found!")
        module.name = user_name
        self.window_modules.append(module)
        return module


    def get_layer(self, layer_name: str):
        """Return a Layer object using the layer name.
        Returns None if layer name not found."""
        return next((layer for layer in self.layers
                     if layer.name == layer_name), None)

    def auto_connect(self):
        # TODO

        # self.connect_signals()
        # self.connect_modules()
        # self.determine_reference_coords()
        # self.assign_BRAM()
        # ...
        pass

    def generate_pipeline(self):
        # TODO:
        # Generate VHDL code for data pipeline
        # Probably move to own module/file
        # Reuse some code from old generator?
        pass

    def connect(self, source, sink):
        if(isinstance(source, str) and
            (isinstance(sink, Interface) or isinstance(sink, AsModule))):
            layer = self.get_layer(source)
            if layer is None:
                LOG.error("Layer with name '%s' not found!", source)
                raise AttributeError("Layer with name {} not found!"
                                     .format(source))
            self.__connect_layer_output__(layer, sink)
        elif((isinstance(source, AsModule) or isinstance(source, Interface)) and
                isinstance(sink, str)):
            layer = self.get_layer(sink)
            if layer is None:
                LOG.error("Layer with name '%s' not found!", source)
                raise AttributeError("Layer with name {} not found!"
                                     .format(source))
            self.__connect_layer_input__(source, layer)
        else:
            LOG.error(("Wrong parameters passed to 'As2DWindowPipeline.connect'"
                       "!\n Need (layer name, module/interface) or reverse!"))
            raise ValueError("Wrong parameters passed to connect!")
        
        # TODO:
        # Done?

    def __connect_layer_input__(self, source, layer: AsLayer):
        # TODO
        pass

    def __connect_layer_output__(self, layer: AsLayer, sink):
        # TODO
        pass
