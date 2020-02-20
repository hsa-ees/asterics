# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# Copyright (C) Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_automatics_window_module.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Class representing an ASTERICS window module used to construct
2D-Window-Pipelines.
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
# @file as_automatics_window_module.py
# @author Philip Manke
# @brief Class representing a window module for 2D-Window-Pipelines.
# -----------------------------------------------------------------------------


from collections import namedtuple

from as_automatics_module import AsModule
from as_automatics_interface import Interface
from as_automatics_port import Port, StandardPort
from as_automatics_exceptions import AsAssignError, AsAnalysisError


import as_automatics_logging as as_log


LOG = as_log.get_log()

# Coordinate namedtuple definition
Coordinate = namedtuple("coordinate", "x y")

class AsWindowInterface(Interface):
    """Simple Interface definition for window interfaces used in the 
    2D-Window-Pipeline. Adds the 'layer_name' attribute."""
    def __init__(self, layer_name):
        super().__init__("as_window")
        self.add_port(Port("strobe", optional=True))
        self.layer_name = layer_name

class AsWindowInterfaceMerged(Interface):

    def __init__(self, layer_name):
        super().__init__("as_merged_window")
        self.layer_name = layer_name
        self.add_port(Port("data", data_type="generic_window"))
        self.add_port(Port("data", direction="out",
                           data_type="std_logic_vector", optional=True))
        self.add_port(Port("data", direction="out",
                           data_type="generic_window", optional=True))
        self.add_port(Port("strobe", optional=True))
                           


class AsWindowModule(AsModule):
    """Automatics class representing a module for the 2D-Window-Pipeline.
    Based on the AsModule class.
    Adds multiple attributes for managing aspects of the pipeline."""

    standard_port_templates = [StandardPort("strobe", port_type="single",
                            extra_rules=[Port.Rule("both_present", "connect")])]
    standard_port_templates.extend(AsModule.standard_port_templates)

    def __init__(self):
        super().__init__()
        self.reference = Coordinate(x=0, y=0)
        self.size = Coordinate(x=0, y=0)
        self.input_refs = []
        self.output_refs = []
        self.delay = None
        self.window_interfaces = []


    def __str__(self) -> str:
        return "ASTERICS Window-Module '{}' ({})" \
            .format(self.name, self.entity_name)


    def set_reference(self, x : int, y : int):
        self.reference = Coordinate(x, y)


    def set_size(self, width : int, height : int):
        self.size = Coordinate(width, height)


    def add_input(self, x : int, y : int):
        self.input_refs.append(Coordinate(x, y))


    def add_output(self, x : int, y : int):
        self.output_refs.append(Coordinate(x, y))


    def add_inputs(self, input_matrix : list):
        for x in range(len(input_matrix)):
            for y in range(len(input_matrix[x])):
                for _ in range(input_matrix[x][y]):
                    self.add_input(x, y)


    def add_outputs(self, output_matrix : list):
        for x in range(len(output_matrix)):
            for y in range(len(output_matrix[x])):
                for _ in range(output_matrix[x][y]):
                    self.add_output(x, y)


    def get_last_reference(self, reflist : list):
        if not reflist:
            return None
        
        refs = list((r.x * self.size.x + r.y for r in reflist))
        refs.sort(reverse=True)
        return refs[0]


    def get_delay(self):
        last_input = self.get_last_reference(self.input_refs)
        if last_input is None:
            raise AttributeError("No inputs set for {}".format(str(self)))

        last_output = self.get_last_reference(self.output_refs)
        if last_output is None:
            raise AttributeError("No outputs set for {}".format(str(self)))

        self.delay = last_output - last_input


    def assign_output(self):
        if self.delay is None:
            LOG.error(("%s: Cannot assign output reference! Module delay not"
                       " set!"), str(self))
            raise AttributeError("Module delay not set!")
        last_input = self.get_last_reference(self.input_refs)
        last_output = last_input + self.delay
        self.add_output(int(last_output / self.size.x),
                        last_output % self.size.x)


    def discover_module(self, file: str):
        super().discover_module(file, window_module=True,
                extra_function=self.__assign_window_interfaces__)


    def __assign_window_interfaces__(self):
        to_remove = []  # Collecting ports assigned before
        for port in self.entity_ports:
            # If port is not part of a window interface, skip it
            if not getattr(port, "window_config"):
                continue
            # Try to match port with an existing window interface
            match = self.__assign_port_to_existing_window__(port)
            if match:
                to_remove.append(port)
                continue
            match = self.__assign_port_to_new_window__(port)
            if not match:
                LOG.debug("Port '%s' not assigned to a window interface.",
                          port.code_name)
            else:
                to_remove.append(port)
        
        for port in to_remove:
            self.entity_ports.remove(port)


    def __assign_port_to_existing_window__(self, port: Port) -> bool:
        try:  # Just making sure
            # Check each window interface
            for inter in self.window_interfaces:
                # If the layer names match, we can assign the port
                if port.window_config.layer == inter.layer_name:
                    inter.add_port(port)
                    break  # Done!
            else:
                return False
        except AttributeError as err:
            LOG.debug("'%s': Got Attribute Error: '%s'", str(self), str(err))
            return False
        
        LOG.debug("Port '%s' assigned to interface '%s'",
            port.code_name, str(inter))
        return True


    def __assign_port_to_new_window__(self, port: Port) -> bool:
        try:
            # If we have a layer name...
            if port.window_config.layer:
                # Create a new window interface and add the port
                winter = AsWindowInterface(port.window_config.layer)
                winter.add_port(port)
                # Register the window interface with the module
                self.window_interfaces.append(winter)
            else:
                LOG.error("Missing layer name for port '%s' of module '%s'!",
                    port.code_name, str(self))
                return False
        except AttributeError as err:
            LOG.debug("'%s': Got Attribute Error: '%s'", str(self), str(err))
            return False

        LOG.debug("Port '%s' assigned to new interface '%s'.",
            port.code_name, str(winter))
        return True

