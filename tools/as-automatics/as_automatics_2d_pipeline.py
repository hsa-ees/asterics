# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
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

from collections import namedtuple
from copy import copy

from as_automatics_proc_chain import AsProcessingChain
from as_automatics_module import AsModule
from as_automatics_window_module import AsWindowModule, AsWindowInterface
from as_automatics_port import Port
from as_automatics_interface import Interface
from as_automatics_templates import AsStream
from as_automatics_exceptions import (AsAssignError, AsModuleError,
                                      AsConnectionError)
from as_automatics_2d_infrastructure import (
    AsLayer, AsWindowSection, WindowDef, WindowRef, AsConnectionRef)
from as_automatics_vhdl_static import PIPE_WINDOW_TYPE

import as_automatics_logging as as_log

LOG = as_log.get_log()


class As2DWindowPipeline:
    """Class that represents a 2DWindowPipeline of the ASTERICS Framework.
    Contains the dimensions of the pipeline as well as a list of all data
    layers with the individual sections, along with the methods to
    interact, configure the pipeline."""

    LAYER_INPUT = "LayerInput"
    LAYER_OUTPUT = "LayerOutput"

    UserConJob = namedtuple("UserConnectionJob",
                            ["type", "inter", "layer", "anchor"])

    def __init__(self, columns: int, rows: int, chain: AsProcessingChain):
        self.window_modules = []
        self.layers = []
        self.chain = chain
        self.columns = columns
        self.rows = rows
        self.min_bits_per_section = 64
        self.user_connections = []
        self.pipeline_traversal = []
        WindowRef.set_windowsize(self.columns, self.rows)

    @staticmethod
    def get_last_ref() -> WindowRef:
        return WindowRef(WindowRef.columns - 1, WindowRef.rows - 1)

    def set_bram_threshold(self, threshold_in_bits: int = -1,
                           threshold_in_bytes: int = -1):
        """Set the minimum size of sections that will get implemented as BRAM.
        Either use 'threshold_in_bits' or 'threshold_in_bytes' to set a new
        value."""
        if threshold_in_bits > 0:
            self.min_bits_per_section = threshold_in_bits
        elif threshold_in_bytes > 0:
            self.min_bits_per_section = int(threshold_in_bytes / 8)

    def add_layer(self, name: str, data_width: int,
                  baselayer: bool = False) -> AsLayer:
        """Add a new layer to the data pipeline.
        The first layer that is added is the 'base layer'.
        All layers must be added to the pipe before running the section tools!
        Parameters:
            name: Name of the layer. Must be unique.
            data_width: Data width in bits for this layer.
        Returns the layer object."""
        # Check if a layer of the provided name already exists.
        if name in [l.name for l in self.layers]:
            raise AttributeError("Layer with name {} already exists!"
                                 .format(name))
        layer = AsLayer(name, data_width, self)
        # If this is the first layer to be added, set it as the base layer
        if not self.layers or baselayer:
            layer.base_layer = True
        # Set the initial section references to span the entire layer.
        layer.set_bounds(WindowRef(0, 0),
                         WindowRef(col=self.columns - 1, row=self.rows - 1))
        self.layers.append(layer)
        return layer

    def add_section(self, section: AsWindowSection):
        """Insert a section that can span multiple layers into the pipe."""
        # For all layers that the section spans
        for layer in section.layers:
            # For all sections of that layer
            for sec in layer.sections:
                # If they dont overlap -> next section
                if not sec.overlaps(section):
                    continue
                # If they are identical, we can stop here.
                if sec == section:
                    break
                # Get the overlap between the sections
                over = sec.get_overlap(section)
                # If necessary, move the end reference of the existing section
                if over.end_ref != sec.end_ref:
                    sec.split(over.end_ref + 1)
                # If necessary, move the start reference of the existing
                # section
                if over.start_ref != sec.start_ref:
                    sec.split(over.start_ref)
                # Now, a section with matching end and start references should
                # exist. Replace that with the new section.
                if ((sec.start_ref == section.start_ref) and
                        (sec.end_ref == section.end_ref)):
                    layer.remove_section(sec)
                    layer.add_section(section)


    def __init_sections__(self):
        """Splits up the sections to align with all overlaps.
        Run only once right after initializing the sections,
        as it expects a single section per layer!"""
        for layer in self.layers:
            to_split = []
            # Instantiate a new section over the entire layer
            sec = AsWindowSection(layer, layer.data_width)
            sec.set_bounds(layer.start_ref, layer.end_ref)
            # and add it to the layer
            layer.sections.append(sec)

            # The section starts at the pixel/data input
            # (no need to build a pipeline without data to process)
            sec.start_ref.update(sec.parent.input.refnum)
            layer.start_ref = sec.start_ref

            # Sort the filter outputs by their refnums
            outputs = sec.parent.output_refs
            outputs.sort(key=lambda ref: ref.refnum)

            # Determine positions where the section must be buffered in FFs
            # This is at positions where a filter output appears after
            # a data point without an output:
            # IN -> ff -> ff -> |SPLIT| out -> out -> ff -> |SPLIT| out -> ...
            for idx in range(len(outputs)):
                outref = outputs[idx]
                # Don't split right at the input
                if idx == 0:
                    # First output requires special attention, as there's no
                    # previous output to reference
                    if outref.refnum != sec.start_ref.refnum:
                        to_split.append(
                            WindowRef.get_ref_from_refnum(outref.refnum))
                    continue
                # If an output appears right after another ouput, no split!
                if abs(outref.refnum - outputs[idx - 1].refnum) == 1:
                    continue
                else:  # otherwise:
                    to_split.append(
                        WindowRef.get_ref_from_refnum(outref.refnum))
                    continue
            # Last output is the last datapoint of the section/pipeline
            sec.end_ref.update(outputs[-1].refnum)
            layer.end_ref = sec.end_ref

            # Split the section of this layer into subsections
            # Each subsection is a candidate that may be stored in BRAM
            for ref in to_split:
                # The split method returns the section further along the
                # buffer (higher refnum), which may be split again
                sec = sec.split(ref)

    def __find_brams__(self):
        # Collect all sections of all layers
        over = []
        sections = []
        for layer in self.layers:
            sections.extend(layer.sections)
        # Remove sections that, even across all layers, would be too small
        sections = self.__filter_unsuitable__(
            sections, self.min_bits_per_section / len(self.layers))
        LOG.debug("Sections filtered")
        LOG.debug("%s", repr(sections))

        # Find overlapping sections:
        # Need to run at most [layercount - 1] times as each method call finds a
        # second overlapping section (from another layer) per checked section
        # Thus: To find a section that overlaps across all layers
        #       the method has to be run once per layer minus one
        to_check = sections
        for x in range(len(self.layers)):
            comp_res = self.__get_overlap__(to_check)
            if not comp_res:  # If no additional overlaps are found, terminate
                break
            LOG.debug("Overlap round %i:", x)
            LOG.debug("%s", repr(comp_res))
            # Sections for the next round
            to_check = comp_res
            over.extend(comp_res)

        # Remove overlapping sections that are still too small for BRAM
        over = self.__filter_unsuitable__(over)

        # Optional debug output.
        if True:
            LOG.debug("All sections:")
            for layer in self.layers:
                for sec in layer.sections:
                    LOG.debug("%s: %s", repr(sec.parent), repr(sec))
            LOG.debug("Filtered overlaps:")
            for sec in over:
                LOG.debug("%s in layers: %s", repr(sec), repr(sec.layers))

        # Sort both section lists by section size ascending
        over.sort(key=lambda sec: sec.size(), reverse=False)
        sections.sort(key=lambda sec: sec.size())
        # Filter out overlapping sections that overlap each other.
        to_remove = []
        # For all sections
        for idx in range(len(over) - 1):
            sec = over[idx]  # Select section for this run
            for csec in over[idx + 1:]:  # Compare against all larger sections
                if sec is csec:  # To be sure
                    continue
                if sec in csec:  # If the larger section contains this section
                    to_remove.append(sec)  # it can be safely removed
                    LOG.debug("Marking section '%s' of %s to be removed!",
                              repr(sec), repr(sec.layers))
                    break
            else:
                # For all non-overlapping sections
                for csec in sections:
                    # If the current section overlaps the simple section
                    # and the simple section is larger
                    # -> no resource usage advantage for the overlapping section
                    # => Can be removed!
                    if csec.overlaps(sec) and sec.size() < csec.size():
                        to_remove.append(sec)
                        LOG.debug("Marking section '%s' of %s to be removed!",
                                  repr(sec), repr(sec.layers))
                        break

        # TODO: Double Check this, comments, documentation, testing!
        # Remove the marked sections
        for sec in to_remove:
            LOG.debug("Section '%s' of %s removed!", repr(sec), sec.parent)
            over.remove(sec)

        # Insert the overlapping sections into the AsLayer objects
        for sec in over:
            LOG.debug("Adding section '%s' of %s...",
                      repr(sec), repr(sec.layers))
            self.add_section(sec)

        LOG.debug("Finished section implementation:")
        bram_count = 0
        # Mark all layers above the threshold to be implemented in BRAM
        for layer in self.layers:
            layer.sections.sort(key=lambda sec: sec.start_ref.refnum)
            for sec in layer.sections:
                if sec.size() >= self.min_bits_per_section:
                    sec.impl_type = AsWindowSection.BRAM
                    sec.bram_id = bram_count
                    bram_count += 1
                LOG.debug("'%s': %s spanning: %s as %s", layer.name, repr(sec),
                          sec.layers, sec.impl_type)

    def __filter_unsuitable__(
            self,
            sections: list,
            threshold: int = 0) -> list:
        """For a list of sections, returns only those above a threshold.
        Default threshold is 'self.min_bits_per_section'.
        Comparison value is 'section.size()'."""
        if threshold == 0:
            threshold = self.min_bits_per_section
        return [sec for sec in sections if sec.size() >= threshold]

    def __get_overlap__(self, sections: list):
        """Determine which sections of other layers overlap with the
        provided list of sections.
        Input: 'sections': List of sections to check.
        Returns the only the new overlapping sections."""
        out = []
        # For all input sections
        for sec in sections:
            # For all layers
            for layer in self.layers:
                # Check only layers that the section is not a part of
                if layer in sec.layers:
                    continue
                # For all sections of the layer
                for lsec in layer.sections:
                    # Do the sections overlap? Returns 'None' if not.
                    osec = sec.get_overlap(lsec)
                    if osec and osec not in out:
                        out.append(osec)
        return out

    def define_layer(self, name: str, data_width: int):
        """Define a datalayer in the pipeline.
        Layers are used to connect window modules to each other.
        At least two layers (input & output) are required for every pipeline."""
        self.layers.append(AsLayer(name, data_width, self))

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
        module = self.chain.library.get_module_instance(
            entity_name, repository, True)
        if module is None:
            raise AsModuleError(entity_name,
                                msg="No window module with this name found!")
        module.name = user_name
        self.window_modules.append(module)
        module.pipe = self
        # Generate unique names for the module's interfaces (with user_name)
        module.__gen_uname_for_window_ifs__()

        # Rework in progress...
        #module.offset.__update__()
        return module

    def get_layer(self, layer_name: str):
        """Return a Layer object using the layer name.
        Returns None if layer name not found."""
        return next((layer for layer in self.layers
                     if layer.name == layer_name), None)

    def auto_connect(self):
        raise NotImplementedError("This feature is still Work-in-Progress!")
        # TODO


        # Apply user connections
        self.__run_user_connect_calls__()
        # Initialize Window sections
        #self.__init_sections__()
        # self.connect_signals()
        # self.connect_modules()
        
        # Apply multi-input offset normalization
        #for module in self.window_modules:
        #    module.update_input_refs_for_offset()

        
        # Run simple algorithm for BRAM assignment
        #self.__find_brams__()
        # TODO: self.__optimize_bram__()
        

    def generate_pipeline(self):
        raise NotImplementedError("This feature is still Work-in-Progress!")
        # TODO:
        # Generate VHDL code for data pipeline
        # Probably move to own module/file
        # Reuse some code from old generator?
        pass

    def connect(self, interface: Interface, layer: AsLayer,
                offset: tuple = None):
        """Connect an interface from an AsModule to a pipeline data layer."""
        if offset:
            anchor = WindowRef(*offset)
        else:
            anchor = None
        if interface.direction == "out":
            con_type = self.LAYER_INPUT
        else:
            con_type = self.LAYER_OUTPUT
        conjob = self.UserConJob(con_type, interface, layer, anchor)
        self.user_connections.append(conjob)
        LOG.debug("Pipe: Got connection job for '%s' and layer '%s' @ %s.",
                  repr(interface), str(layer),
                  "auto" if not anchor else str(anchor))

    def __run_user_connect_calls__(self):
        """Run the connect method calls that the user specified for the pipeline
        Starts the recursive job runner."""
        for job in self.user_connections:
            # DEBUG
            print("{} ({}) [{}] <-> {} [{}]".format(job.inter.name, job.inter.unique_name, job.inter.parent.name, job.layer.name, job.type))
        # Run the base layers first:
        # (layers where the input comes from outside of the pipeline)
        LOG.debug("Pipeline: Start handling user connections for pipeline...")
        base = self.__get_base_layers__()
        if not base:  # Need at least one base layer...
            LOG.debug("Missing base layer among: '%s'", self.layers)
            raise AsConnectionError(("Could not start connection process, "
                                     "no base layer specified!"))
        LOG.debug("Pipeline: Base layers %s:", str(base))

        # Sort user connection jobs
        input_cons = [con for con in self.user_connections
                      if con.type is self.LAYER_INPUT]
        output_cons = [con for con in self.user_connections
                       if con.type is self.LAYER_OUTPUT]
        LOG.debug("Pipeline: Sorted %i input jobs and %i output jobs.",
                  len(input_cons), len(output_cons))

        done_jobs = []  # Has to stay consistent between job handler calls!
        for layer in base:
            LOG.debug("Pipeline: Starting job handler for layer '%s'...",
                      layer.name)
            self.__rec_conjob_handler__(layer, input_cons, output_cons,
                                        done_jobs)
        
        # Use the resulting list of connection jobs (order is important!)
        # to calculate the physical pixel references in order
        self.pipeline_traversal = done_jobs
        self.__calc_phys_addr__()

    def __rec_conjob_handler__(self, layer: AsLayer, input_conjobs: list,
                               output_conjobs: list, complete: list):
        """Recursive user connection job handler.
        Algorithm:
            1. Handle the input for the current data layer (parameter 'layer')
            2. Handle all outputs to modules from that layer
            3. For each module that gets data from the current layer:
                3.1. Get the associated input connection job for that module
                3.2. Call this method with the layer referenced by the job
        Each handled connection job gets added to the list 'complete'.
        With correctly architected pipelines this should be unnecessary, though
        undefined behaviour (infinite recursion!) might happen without checking.
        Parameters:
            layer: The currently handled data layer
            input_conjobs: list of all user connection jobs: x -> layer
            output_conjobs: list of all user connection jobs: layer -> x
            complete: empty list. Is appended completed connection jobs.
        """
        LOG.debug("UserCon: Current layer: '%s'", layer.name)
        # For all inputs of the current layer (should only be one per layer!)
        for conjob in [con for con in input_conjobs if con.layer is layer]:
            if conjob not in complete:  # Run if not handled
                LOG.debug("UserCon: Setting input of layer '%s' from '%s'...",
                          layer.name, repr(conjob.inter))
                self.__connect_layer_input__(conjob.inter, conjob.layer,
                                             conjob.anchor)
            complete.append(conjob)

        # For all outputs of the current layer
        for conjob in [con for con in output_conjobs if con.layer is layer]:
            if conjob not in complete:  # Run if not handled
                LOG.debug("UserCon: Connecting '%s' to '%s'...",
                          repr(conjob.layer), repr(conjob.inter))

                self.__connect_layer_output__(conjob.inter, conjob.layer,
                                              conjob.anchor)
                complete.append(conjob)
                interface = conjob.inter
                # Handle all jobs with the module, that takes data from
                # the current layer -> Recursion! We're going down!
                for conjob in [con for con in input_conjobs if con.inter.parent is interface.parent]:
                    LOG.debug("UserCon: Running handler for layer '%s'",
                              repr(conjob.layer))
                    self.__rec_conjob_handler__(conjob.layer, input_conjobs,
                                                output_conjobs, complete)

    def __get_base_layers__(self) -> list:
        return [layer for layer in self.layers if layer.base_layer]



    def __connect_layer_input__(self, inter: Interface, layer: AsLayer,
                                anchor: WindowRef):
        window = isinstance(inter, AsWindowInterface)
        
        if window:
            if len(inter.references) > 1:
                LOG.error(("Tried connection interface '%s' input to layer '%s'"
                        " with more than one port!"), inter.name, layer.name)
                raise AsConnectionError(("Layer input interfaces must have only"
                                        " one port!"))
            else:
                # There should only be one port / reference for layer input interfaces
                port = inter.references[0].port
        elif isinstance(inter, Interface):
            try:  # Assuming AsStream interface!
                port = inter.get_port("data")
            except NameError as err:
                LOG.error("Could not find port 'data' in '%s'! - '%s'",
                          inter.name, str(err))
                raise AsConnectionError(("When connecting '{}' in 2D Window "
                        "Pipeline to '{}'. Missing port 'data'! Might not be "
                        "AsStream!").format(inter.name, layer.name))
        if anchor is None:
            anchor = WindowRef(0, 0)
        module = inter.parent
        # The input of each layer should be @ (0,0)
        # The pixel offset between the base layer and all other layers
        # is determined by each layers 'offset' attribute
        layer.set_input(AsConnectionRef(WindowRef(0, 0), port))
        layer.set_offset(WindowRef(0, 0))
        
        # Register the layer input connection with the layer, interface
        # and module objects involved
        layer.interfaces.append(inter)
        layer.modules.append(module)
        # Assuming window interface is only present in AsWindowModule
        if window:  
            module.output_layers.append(layer)
            inter.layer = layer
        elif isinstance(module, AsModule):
            inter.outgoing.append(layer)
        else:
            LOG.error("Connected to unkown object type!")
            raise TypeError("Unkown module type for connection: {}"
                            .format(type(module)))

    def __connect_layer_output__(self, inter: Interface, layer: AsLayer,
                                 anchor: WindowRef):
        # TODO: Handle anchor case
        window = isinstance(inter, AsWindowInterface)

        # Check if the interface is ready to be connected
        if window:
            if not inter.update_footprint():
                LOG.error(
                    ("Could not connect interface '%s'! The generics used in "
                    "'%s' need to be defined before making the connection!"),
                    inter.name,
                    inter.data_type)
                raise ValueError("Undefined generics in interface '{}': '{}'"
                                .format(inter.name, inter.data_type))
        if not anchor:
            anchor = WindowRef(0, 0)
        if layer.input is None:  # Just making sure!
            LOG.error(
                ("Attempted to connect output interface '%s' to layer"
                    " '%s' without an input!"), inter.name, layer.name)
            raise AsConnectionError(("Cannot connect outputs to layer "
                                     "without an input!"))
        
        module = inter.parent

        if window:
            if module.user_phys_offset:
                module.offset = module.user_phys_offset
            else:
                module.offset = anchor
            # For each input port of the interface
            for pref in inter.references:
                layer_ref = layer.add_output(pref)
                # Add the resulting reference to the module
                module.input_refs.append(layer_ref)
                # TODO: Testing!
        else:
            try:
                port = inter.get_port("data", suppress_error=True)
            except NameError as err:
                LOG.error("Could not find port 'data' in '%s'! - '%s'",
                          inter.name, str(err))
                raise AsConnectionError(("When connecting '{}' in 2D Window "
                        "Pipeline to '{}'. Missing port 'data'! Might not be "
                        "AsStream!").format(inter.name, layer.name))
            pref = AsConnectionRef(WindowRef(0, 0), port)
            layer.add_output(pref, True)
            
        # Register this connection with the module, layer and interface involved
        layer.interfaces.append(inter)
        layer.modules.append(module)
        if window:
            module.input_layers.append(layer)
            inter.layer = layer
        elif isinstance(module, AsModule):
            inter.incoming.append(layer)

    def __calc_phys_addr__(self):
        for con in self.pipeline_traversal:
            inter = con.inter
            layer = con.layer
            offset = con.anchor
            module = inter.parent
            #is_input = True if con.con_type is self.LAYER_INPUT else False
            

            #if is_input:
            #    if module.user_phys_offset:
            #        offset = 1
            #    layer.delay = 1
            #    pass
            #    # TODO !!

            # TODO: - Calculate the physical addresses of each layer in-/output
            #         and module offset.
            #       - Verify each reference (eg. output only after input)



# ↓↓↓ OLD CODE ↓↓↓ !for reference only!

"""
    def __connect_layer_input__(self, inter: Interface, layer: AsLayer,
                                anchor: WindowRef):
        window = isinstance(inter, AsWindowInterface)
        if window and any(ref.refnum is None for ref in inter.references):
                for ref in inter.references:
                    ref.__update__()
        if window:
            if len(inter.references) > 1:
                LOG.error(("Tried connection interface '%s' input to layer '%s'"
                        " with more than one port!"), inter.name, layer.name)
                raise AsConnectionError(("Layer input interfaces must have only"
                                        " one port!"))
            else:
                # There should only be one port / reference for layer input interfaces
                port = inter.references[0].port
        elif isinstance(inter, Interface):
            try:
                port = inter.get_port("data")
            except NameError as err:
                LOG.error("Could not find port 'data' in '%s'! - '%s'",
                          inter.name, str(err))
                raise AsConnectionError(("When connecting '{}' in 2D Window "
                        "Pipeline to '{}'. Missing port 'data'! Might not be "
                        "AsStream!").format(inter.name, layer.name))
        if anchor is None:
            anchor = WindowRef(0, 0)
        module = inter.parent
        # The input of each layer should be @ (0,0)
        # The pixel offset between the base layer and all other layers
        # is determined by each layers 'offset' attribute
        layer.set_input(AsConnectionRef(WindowRef(0, 0), port))
        # Base layers always have an offset of (0,0)
        if layer.base_layer:
            layer.set_offset(WindowRef(0, 0))
        else:
            # For all other layers: The offset is the number of clock cycles
            # with active strobe signal (movement of pixel data through the
            # pipeline) until pixel (0,0) arrives at the layer input reference
            offset = module.offset + inter.references[0] + anchor
            layer.set_offset(offset.get_ref())

        # Register the layer input connection with the layer, interface
        # and module objects involved
        layer.interfaces.append(inter)
        layer.modules.append(module)
        # Assuming window interface is only present in AsWindowModule
        if window:  
            module.output_layers.append(layer)
            inter.layer = layer
        elif isinstance(module, AsModule):
            inter.outgoing.append(layer)
        else:
            LOG.error("Connected to unkown object type!")
            raise TypeError("Unkown module type for connection: {}"
                            .format(type(module)))

    def __connect_layer_output__(self, inter: Interface, layer: AsLayer,
                                 anchor: WindowRef):
        # TODO: Handle anchor case
        window = isinstance(inter, AsWindowInterface)
        if window and any(ref.refnum is None for ref in inter.references):
            for ref in inter.references:
                ref.__update__()
        # Check if the interface is ready to be connected
        if window:
            if not inter.update_footprint():
                LOG.error(
                    ("Could not connect interface '%s'! The generics used in "
                    "'%s' need to be defined before making the connection!"),
                    inter.name,
                    inter.data_type)
                raise ValueError("Undefined generics in interface '{}': '{}'"
                                .format(inter.name, inter.data_type))

        # Check if the anchor is viable:
        if anchor is not None:
            if not layer.is_valid_ref(anchor, inter.direction):
                LOG.warning(("Connect: Invalid window anchor '%s' for "
                             "connecting '%s' to layer '%s'! Using automatic"
                             " choice!"), str(anchor), inter.name, layer.name)
                anchor = WindowRef(0, 0)
        else:
            anchor = WindowRef(0, 0)
        if layer.input is None:  # Just making sure!
            LOG.error(
                ("Attempted to connect output interface '%s' to layer"
                    " '%s' without an input!"), inter.name, layer.name)
            raise AsConnectionError(("Cannot connect outputs to layer "
                                     "without an input!"))
        
        module = inter.parent

        if window:
            if module.user_phys_offset:
                module.offset = module.user_phys_offset
                if module.user_phys_offset < layer.offset:  # This would make a broken pipe
                    LOG.error(("ERROR connecting interface '%s' of module "
                                "'%s' to layer '%s': Layer offset @ %s > "
                                "physical offset set to %s!"), inter.name,
                                module.name, layer.name, str(layer.offset),
                                module.user_phys_offset)
                    raise AsConnectionError(
                        ("Cannot use physical offset {}, data from layer "
                         "'{}' not ready!").format(module.user_phys_offset,
                                            layer))
            # For each input port of the interface
            for pref in inter.references:
                # User set module.set_physical_position
                if module.user_phys_offset:
                    layer_ref = layer.add_output(
                            pref + module.user_phys_offset, True)
                else:
                    # Use the anchor as an offset for the reference
                    layer_ref = layer.add_output(pref + anchor)
                # Add the resulting reference to the module
                module.input_refs.append(layer_ref)
                # TODO: Testing!
            off1 = anchor + layer.offset
            module.offset = module.offset if module.offset > off1 else off1
        else:
            try:
                port = inter.get_port("data", suppress_error=True)
            except NameError as err:
                LOG.error("Could not find port 'data' in '%s'! - '%s'",
                          inter.name, str(err))
                raise AsConnectionError(("When connecting '{}' in 2D Window "
                        "Pipeline to '{}'. Missing port 'data'! Might not be "
                        "AsStream!").format(inter.name, layer.name))
            pref = AsConnectionRef(WindowRef(0, 0), port)
            layer.add_output(pref + anchor, True)
            
        # Register this connection with the module, layer and interface involved
        layer.interfaces.append(inter)
        layer.modules.append(module)
        if window:
            module.input_layers.append(layer)
            inter.layer = layer
        elif isinstance(module, AsModule):
            inter.incoming.append(layer)


"""
"""
    def __connect_layer_input__(self, inter: Interface, layer: AsLayer,
                                anchor: WindowRef):
        if layer.input:
            # If an input already exists: Error! Max one input per layer!
            LOG.error("Failed connecting to layer '%s'", layer.name)
            raise AsConnectionError(("Each layer may only have one input!"
                                     "Failed connecting {} to {}.")
                                    .format(str(inter), layer.name))
        # TODO
        LOG.debug("UCLI: Got '%s' -> '%s' @ '%s'", repr(inter), layer.name,
                  str(anchor))
        module = inter.parent

        # If no anchor reference is provided: Use the first possible reference
        if not anchor:
            if layer.base_layer:
                anchor = layer.start_ref
            else:

                # TODO: determine next possible input ref
                # TODO: Update module.reference (add offset = first possible start ref)
                # TODO: Add checks: references are in bounds of the layers
                pass

    def __connect_layer_output__(self, inter: Interface, layer: AsLayer,
                                 anchor: WindowRef):
        LOG.debug("UCLO: Got '%s' -> '%s' @ '%s'", layer.name, repr(inter),
                  str(anchor))

        if anchor is not None and anchor < layer.input:
            LOG.error(("Pipeline: Anchor %s for connection '%s -> %s' invalid!"
                       " Layer input at '%s'."), str(anchor),
                      layer.name, repr(inter), str(layer.input))
            raise AsConnectionError("Invalid data output placement!")
        else:
            # Determine anchor reference (lowest valid reference)
            # Valid references are <= layer.input
            anchor = layer.input

        module = inter.parent

        if isinstance(inter, AsWindowInterface):
            # TODO: Manage window module specific things (set input refs, etc.)
            layer.modules.append(module)
            layer.interfaces.append(inter)

            # TODO: Calculate new module reference (paper sketch, module.size)
            #       Update module.reference
            # TODO: Add checks: references are in bounds of the layers

            ref = module.reference
            wsize = module.size
            ref.col = ref.col + int((wsize.to_x + wsize.from_x) / 2)
            ref.row = ref.row + int((wsize.to_y + wsize.from_y) / 2)
            # TODO: Check: Is this ↑ correct?

            for port in inter:
                if port in AsWindowModule.standard_port_templates:
                    continue
                pconf = port.window_config
                if PIPE_WINDOW_TYPE in port.data_type:
                    pass
                    # TODO window interface type management
                elif port.data_type == "std_logic_vector":
                    pconf.x += anchor.col
                    pconf.y += anchor.row
                    layer.add_output(AsConnectionRef(
                        WindowRef(pconf.x, pconf.y), port))

        elif isinstance(inter, Interface):
            if isinstance(inter, AsStream):
                layer.modules.append(module)
                layer.interfaces.append(inter)
                port = inter.get_port("data")
                layer.add_output(AsConnectionRef(anchor, port))
                port.window_config = Port.WindowReference(
                    anchor.col, anchor.row, inter.name)
            else:
                LOG.error("")
                raise AsConnectionError(
                    ("Non-window modules can only connect "
                     "AsStreams to the 2D Window Pipeline!"))
        else:
            LOG.error("Wrong data type passed to pipeline.connect()!")
            raise TypeError("Cannot connect data layer with object of type {}!"
                            .format(type(inter)))

        # TODO: Establish connection
"""

# ↑↑↑ OLD CODE ↑↑↑ !for reference only!


# DEBUG for WindowSection management:
if __name__ == "__main__":
    LOG = as_log.init_log(loglevel_console="DEBUG")
    pipe = As2DWindowPipeline(640, 480, None)

    l0 = pipe.add_layer("grey", 8)
    l0.set_input(WindowRef(col=0, row=0))
    # l0.add_outputs(window=WindowDef(0,2,0,2))

    l1 = pipe.add_layer("gauss", 8)
    l1.set_input(WindowRef(1, 0))
    l1.add_output(WindowRef(6, 1))

    l2 = pipe.add_layer("cordic", 12)
    l2.set_input(WindowRef(7, 1))
    l2.add_output(WindowRef(5, 5))
    l2.add_output(WindowRef(6, 5))

    l3 = pipe.add_layer("result", 8)
    l3.set_input(WindowRef(15, 3))
    l3.add_output(WindowRef(6, 4))
    #l3.add_outputs(window=WindowDef(7, 9, 4, 6))

    #pipe.autotune()
