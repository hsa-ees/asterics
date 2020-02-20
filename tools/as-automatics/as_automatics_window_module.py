# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
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

from as_automatics_helpers import extract_generics
from as_automatics_module import AsModule
from as_automatics_interface import Interface
from as_automatics_port import Port, StandardPort
from as_automatics_exceptions import AsAssignError, AsAnalysisError
from as_automatics_2d_infrastructure import (WindowDef, WindowRef, AsLayer,
                                             AsLayerRef, AsConnectionRef)
from as_automatics_vhdl_static import PIPE_WINDOW_TYPE
from as_automatics_2d_helpers import parse_gwindow_type, data_widths_to_window

import as_automatics_logging as as_log


LOG = as_log.get_log()


class AsWindowInterface(Interface):
    """Simple Interface definition for window interfaces used in the
    2D-Window-Pipeline. Adds the 'layer_name' attribute."""

    INTERFACE_TYPE_STR = "as_window"

    def __init__(self):
        super().__init__(self.INTERFACE_TYPE_STR)
        self.layer = None
        self.footprint = None
        self.references = []  # Not updated! List generated from AUTO-Tags!

    def add_window_ref(self, ref: AsConnectionRef):
        """Add a port window reference to this interface.
        The reference must be associated with one of the interface ports."""
        if ref not in self.references:
            if ref.port in self.ports:
                self.references.append(ref)
            else:
                LOG.debug("Received reference of unkown port '%s' by '%s'!",
                          ref.port.code_name, self.name)
        else:
            LOG.debug("Duplicate reference for port '%s' received by '%s'!",
                      ref.port.code_name, self.name)

    def sort_references(self):
        """Sort interface port references in ascending order for easier
        calculations."""
        if WindowRef.init:
            if any(ref.refnum is None for ref in self.references):
                for ref in self.references:
                    ref.__update__()
            self.references.sort(key=lambda ref: ref.refnum)

    def __str__(self):
        if self.layer:
            return "{}{}{} - Layer: '{}'".format(
                self.name_prefix, self.name, self.name_suffix, self.layer.name)
        else:
            return "{}{}{} - Layer: None".format(self.name_prefix, self.name,
                                                 self.name_suffix)

    def update_footprint(self) -> bool:
        """Update and set the footprint size for this interface based on the
        auto-tags of it's ports.
        Also attempts to parse the variable size of the 'generic_window'
        datatype.
        Returns whether the generic_window data type could be parsed."""
        parse_successful = True
        left_col = 0
        right_col = 0
        upper_row = 0
        lower_row = 0
        for port in self.ports:
            if getattr(port, "window_config", None) is None:
                continue  # Skip non-window ports

            if not port.generics:
                # Find and assign generics to the port
                gen_names = extract_generics(port.data_width)
                for name in gen_names:
                    gen = self.parent.get_generic(name, suppress_error=True)
                    if gen:
                        port.add_generic(gen)

            if PIPE_WINDOW_TYPE in port.data_type:
                if not isinstance(port.data_width, str):
                    continue
                widths = parse_gwindow_type(port.data_width,
                                            port.generics)
                if len(widths) < 3:
                    LOG.error("Syntax error detected! In '%s' for port '%s'",
                              self.name, port.code_name)
                
                # Add the auto-tag information to the window size
                window = data_widths_to_window(widths[0], widths[1])

                # Determine footprint of this window-port
                if window is not None:
                    # Add actual data width
                    port.data_width = widths[2]

                    col_offset = int(port.window_config.x)
                    row_offset = int(port.window_config.y)
                    window.from_x += col_offset
                    window.to_x += col_offset
                    window.from_y += row_offset
                    window.to_y += row_offset

                    # Add window-refs for each "pixel"
                    for x in range(window.from_x, window.to_x + 1):
                        for y in range(window.from_y, window.to_y + 1):
                            self.add_window_ref(AsConnectionRef(
                                WindowRef(col=x, row=y), port))
                else:
                    LOG.info(("Could not determine window size for "
                              "interface '%s' of module '%s'! Unresolved "
                              "generics present in '%s'!"), self.name,
                             self.parent.name, str(port.data_width))
                    parse_successful = False
            else:  # Not a window type:
                pref = WindowRef(int(port.window_config.x), int(port.window_config.y))
                self.add_window_ref(AsConnectionRef(pref, port))

        for ref in self.references:
            if ref.col < left_col:
                left_col = ref.col
            elif ref.col > right_col:
                right_col = ref.col
            if ref.row < upper_row:
                upper_row = ref.row
            elif ref.row > lower_row:
                lower_row = ref.row
        
        self.footprint = WindowDef(left_col, right_col,
                                   upper_row, lower_row)
        self.sort_references()
        return parse_successful


class AsWindowModule(AsModule):
    """Automatics class representing a module for the 2D-Window-Pipeline.
    Based on the AsModule class.
    Adds multiple attributes for managing aspects of the pipeline."""

    standard_port_templates = [
        StandardPort(
            "strobe",
            port_type="single",
            extra_rules=[
                Port.Rule(
                    "both_present",
                    "connect")])]
    standard_port_templates.extend(AsModule.standard_port_templates)

    def __init__(self):
        super().__init__()
        self.input_refs = []  # Updated. AsLayerRef objects
        self.output_refs = []  # Updated. AsLayerRef objects
        self.delay = None  # Module output delay in clock cycles
        self.window_interfaces = []  # List of AsWindowInterface objects
        self.input_layers = []  # List of AsLayers this module gets data from
        self.output_layers = []  # List of AsLayers with this module as input
        # ↓ Offset that applies to all outgoing references
        self.offset = WindowRef(0, 0)
        self.user_phys_offset = None  # Physical position set by user
        self.pipe = None  # Reference to the As2DWindowPipeline object (parent)

    def __str__(self) -> str:
        return "ASTERICS Window-Module '{}' ({})" \
            .format(self.name, self.entity_name)


    def update_input_refs_for_offset(self, reference_layer: AsLayer):
        """'Normalize' the input references depending on the layer offsets.
        To build a common reference space, data inputs from different data
        layers must be shifted to synchronize for the different latencies
        in the pipeline.
        Example:
        Layer 0: Input directly from a camera. Has 0 pixel latency: offset = 0
        Layer 1: Gets data from a Gauss module delivering the first processed
                 pixel after two pixels + an entire row of pixels = offset
        This module uses data from both layers.
        To get the data of the "same" pixel, both raw and from the gauss filter,
        the raw pixel references must be shifted by the difference the offset of
        the layer with the largest offset and each other input layer.
        So: shift_input_refs(for=layer0, by=abs(layer1.offset - layer0.offset))

        This method should run after all connections to this module are
        registered. It MUST be run exactly and only ONCE for every module!"""
        
        # Get the reference layer (with the largest offset)
        self.input_layers.sort(key=lambda layer: layer.offset, reverse=True)
        reflayer = self.input_layers[0]
        
        self.input_refs.sort(key=lambda r: r.layer)

        crt_layer = None
        # For every input reference
        for ref in self.input_refs:
            # Inputs of the reference layer must be left unmodified
            if ref.layer is reflayer:
                continue
            # If the layer of the current ref is not the same as last loop
            if ref.layer is not crt_layer:
                crt_layer = ref.layer
                # Calculate the difference in layer offsets
                delta = abs(reflayer.offset - crt_layer.offset)
            ref += delta  # Apply the offset delta (shift the reference)

    def set_physical_position(self, ref_x: int, ref_y: int):
        self.user_phys_offset = WindowRef(ref_x, ref_y)


    def connect(self, interface, layer: AsLayer,
                offset: tuple = None) -> bool:
        """Add a connection operation to the queue.
        Connect the interface <interface_name> of this module to the data layer
        <layer>. The data flow direction is determined via the data direction
        of the specified interface."""
        if isinstance(interface, str):
            inter = self.get_window_interface(interface)
        elif isinstance(interface, Interface):
            inter = interface
        else:
            inter = None
        if not inter:
            LOG.error("Could not find interface with name '%s'!",
                      interface)
            raise ValueError("Interface '{}' does not exist!"
                             .format(interface))
        self.pipe.connect(inter, layer, offset)

    def get_output_layer_offset(self) -> AsLayerRef:
        """Returns the largest offset of any layer that inputs to this module.
        """
        out = AsLayerRef(0, 0, None)
        for ref in self.input_refs:
            if ref.layer.offset > out:
                out.update(ref.layer.offset)
                out.layer = ref.layer
        return out

    def get(self, name: str, direction: str = ""):
        inter = self.get_window_interface(name, direction)
        if inter:
            LOG.debug("Selected interface '%s' from '%s'.",
                      inter.name, self.name)
            return inter
        return super().get(name, direction)

    def get_window_interface(self, interface_name: str,
                             direction: str = "") -> AsWindowInterface:
        """Search for and return a specific WindowInterface of this module."""
        return next(
            (inter for inter in self.window_interfaces if inter.name == interface_name and (
                True if (
                    not direction) else (
                    inter.direction == direction))),
            None)

    def __gen_uname_for_window_ifs__(self):
        # Generate unique name for this module's interfaces
        for inter in self.window_interfaces:
            inter.unique_name = "{}_{}_{}_{}".format(inter.type,
                    inter.name, inter.direction, self.name)

    def list_module(self, verbosity: int = 0):
        """List the configuration of this window module."""
        super().list_module(verbosity)

        if self.window_interfaces:
            print("\n~~~\nWindow Interfaces:")
            for inter in self.window_interfaces:
                if verbosity > 0:
                    inter.print_interface(verbosity > 0)
                else:
                    print(str(inter) +
                          (" ->" if inter.direction == "in" else " <-"))
                print("")

    def add_input(self, col: int, row: int, layer: AsLayer):
        self.input_refs.append(AsLayerRef(col, row, layer))

    def add_output(self, col: int, row: int, layer: AsLayer):
        self.output_refs.append(AsLayerRef(col, row, layer))

    def add_inputs(self, input_matrix: list, layer: AsLayer):
        for col in range(len(input_matrix)):
            for row in range(len(input_matrix[col])):
                for _ in range(input_matrix[col][row]):
                    self.add_input(col, row, layer)

    def add_outputs(self, output_matrix: list, layer: AsLayer):
        for col in range(len(output_matrix)):
            for row in range(len(output_matrix[col])):
                for _ in range(output_matrix[col][row]):
                    self.add_output(col, row, layer)

    def discover_module(self, file: str):
        """Read and parse VHDL-file 'file'.
           Extracts the generic, port and register interface definitions
           to configure this AsWindowModule object.
           Passes the call onto AsModule.discover_module() and handles
           additional tasks requried for AsWindowModules."""
        super().discover_module(file, window_module=True,
                    extra_function=self.__assign_window_interfaces__)
        for inter in self.window_interfaces:
            inter.update_footprint()

    def __assign_window_interfaces__(self):
        """Must be run before regular interfaces are assigned.
        Picks out all ports with auto-tags and bundles them to WindowInterfaces.
        """

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
        """Helper function for '__assign_window_interfaces__().
        Matches and adds 'port' to existing window interfaces.
        Returns False if no match is found!"""
        try:  # Just making sure
            # Check each window interface
            for inter in self.window_interfaces:
                # If the layer names match, we can assign the port
                if ((port.window_config.layer == inter.layer_name) and
                        (port.direction == inter.direction)):
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
        """Helper function for __assign_window_interfaces__().
        Creates a new AsWindowInterface instance based on 'port'."""
        try:
            # If we have an interface name...
            if port.window_config.intername:
                # Create a new window interface and add the port
                inter = AsWindowInterface()
                inter.name = port.window_config.intername
                inter.add_port(port)
                inter.assign_to(self)
                inter.direction = port.direction

                # Register the window interface with the module
                self.window_interfaces.append(inter) 
            else:
                LOG.error(
                    "Missing interface name for port '%s' of module '%s'!",
                    port.code_name,
                    str(self))
                return False
        except AttributeError as err:
            LOG.debug("'%s': Got Attribute Error: '%s'", str(self), str(err))
            return False

        LOG.debug("Port '%s' assigned to new interface '%s'.",
                  port.code_name, str(inter))
        return True
