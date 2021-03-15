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
Class managing the construction of a 2D Window Pipeline subsystem.
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
# @ingroup automatics_2dwpl
# @ingroup automatics_intrep
# @author Philip Manke
# @brief Class managing the construction of a 2D-Window-Pipeline.
# -----------------------------------------------------------------------------

from collections import namedtuple
from copy import copy

import itertools as ittls

from as_automatics_2d_window_module import AsWindowModule
from as_automatics_2d_window_interface import AsWindowInterface
from as_automatics_2d_pipeline_row import AsPipelineRow
from as_automatics_2d_helpers import (
    get_delay,
    set_delay,
    report_buffer_statistics,
    generate_window_assignments,
    pipeline_connection_error_string,
)
from as_automatics_port import Port
from as_automatics_generic import Generic
from as_automatics_interface import Interface
from as_automatics_templates import AsStream
from as_automatics_signal import GenericSignal, GlueSignal
from as_automatics_helpers import foreach
from as_automatics_module import AsModule
from as_automatics_module_group import AsModuleGroup, Register
from as_automatics_module_wrapper import AsModuleWrapper
from as_automatics_exceptions import AsModuleError, AsConnectionError
from as_automatics_connection_helper import (
    resolve_data_width,
    swap_if_necessary,
    set_unique_name,
    get_parent_module,
    resolve_generic,
)
from as_automatics_vhdl_writer_helpers import generate_component_declaration

from as_automatics_logging import get_log

LOG = get_log()

##
# @addtogroup automatics_2dwpl
# @{

LOG = get_log()

## @ingroup automatics_intrep
class As2DWindowPipeline(AsModuleGroup):
    """! @brief Class that represents a 2D Window Pipeline of the ASTERICS Framework.
    Inheriting the AsModuleGroup class, this class describes a 2D Window Pipeline
    subsystem. Containes additional attributes managing the window interfaces
    (as_automatics_2d_window_interface::AsWindowInterface) and image row buffers
    (as_automatics_2d_pipeline_row::AsPipelineRow) of the subsystem.
    Contains custom connect methods for the modules within the subsystem and
    methods for creating, managing and optimizing the size of all image row
    buffers.
    """

    InputStream = namedtuple(
        "InputStream", ("stream", "pipe_if", "target", "signal")
    )
    OutputStream = namedtuple(
        "OutputStream", ("stream", "source", "signal", "target_stream")
    )

    def __init__(self, columns: int, rows: int, name: str, chain):
        if chain is None:
            super().__init__(name, None, [])
        else:
            super().__init__(name, chain.as_main, [])

        self.vhdl_libraries.append("as_generic_filter")
        self.entity_name = name + "_ent"
        self.buffer_rows = []
        # Map of source port to buffer rows
        self.buffer_map = dict()
        self.window_ports = []
        self.window_signals = []
        self.input_streams = []
        self.output_streams = []
        self.pipeline_delay = 0
        self.minimum_bram_size = 256
        self.is_pipe_synchronous = None

        self.optimize_none = None
        self.optimize_all_same_length = self._merge_all_same_length_buffers
        self.optimize_row_number_sensitive = (
            self._merge_same_length_buffers_row_sensitive
        )
        self.optimize_window_width_sensitive = (
            self._merge_same_length_buffers_window_width_sensitive
        )

        self.main_buffer_optimization_strategy = (
            self.optimize_window_width_sensitive
        )
        self.additional_optimizations = {
            "optimize_similar_length_buffers": {
                "active": True,
                "parameters": {"max_length_difference": 100},
            },
            "optimize_thin_and_long_buffers": {
                "active": True,
                "parameters": {"min_length": -1, "maximum_width": 7},
            },
        }

        self.chain = chain
        self.columns = columns
        self.rows = rows
        self.user_connections = []
        self.dependencies = [
            "as_generic_filter",
            "as_pipeline_flush",
            "as_pipeline_manager",
        ]
        self.dynamic_code_generators.append(self._generate_pipeline)

        if chain is not None:
            chain._add_pipeline(self)
            # Insert pipeline in module group list as first object
            self.chain.module_groups.insert(0, self)
            # Standard additions to 2D Window Pipelines:
            #  - Common software drivers:
            pipe_commons = self.chain.library.get_module_template(
                "as_window_pipeline_helper_ent"
            )
            self.driver_files.extend(pipe_commons.driver_files)

        #  - Signals:
        self.internal_reset_signal = self.define_signal(
            "reset_int", fixed_value="reset or sw_reset"
        )
        self.flush_done = self.define_signal("flush_done_int")
        self.internal_reset_signal.name_suffix = "_int"
        self.outgoing_strobe_signal = self.define_signal("strobe_int_out")
        self.outgoing_strobes_valid_signal = self.define_signal(
            "pipemgr_output_data_valid"
        )
        self.flush_in_stall = None
        self.internal_strobe_signal = self.define_signal("strobe_int")
        self.stall_signal_outgoing = self.define_signal("stall_out_int")

        self.input_stream_in = self.define_signal(
            "data_stream_in", "std_logic_vector", Port.DataWidth(7, "downto", 0)
        )
        self.input_stream_out = self.define_signal(
            "pipeline_stream_in",
            "std_logic_vector",
            Port.DataWidth(7, "downto", 0),
        )
        self.output_stream_in = self.define_signal(
            "result_stream_out",
            "std_logic_vector",
            Port.DataWidth(7, "downto", 0),
        )
        self.output_stream_out = self.define_signal(
            "data_stream_out",
            "std_logic_vector",
            Port.DataWidth(7, "downto", 0),
        )

        #  - Generics:
        self.add_generic(Generic("DIN_WIDTH", 8))
        self.add_generic(Generic("LINE_WIDTH", 640))
        self.add_generic(Generic("IMAGE_HEIGHT", 480))
        self.add_generic(Generic("MINIMUM_BRAM_SIZE", self.minimum_bram_size))
        self.set_generic_value("LINE_WIDTH", columns)
        self.set_generic_value("IMAGE_HEIGHT", rows)

    # ----------------------- AUTOMATICS SCRIPT METHODS ------------------------

    ## @ingroup automatics_cds
    def set_main_buffer_optimization_strategy(self, new_strategy):
        """! @brief Set the main buffer optimization strategy.
        Valid options are the attributes of the As2DWindowPipeline object
        starting width 'optimize_'.
        @verbatim
        Namely:
         - pipe.optimize_none : Disable main optimization
         - pipe.optimize_all_same_length : Merge all window buffers
                -> minimal BRAM and LUT usage at the expense
                   of slightly higher register usage
                -> not recommended for systems with
                   very disparately sized window filters
         - pipe.optimize_row_number_sensitive : Merge by row number
                -> useful if further manual optimizations are planned
                -> results in more readable code, with higher resource usage
         - pipe.optimize_window_width_sensitive :
                -> minimal register usage, with higher LUT
                   and possibly very slightly elevated BRAM usage
        @endverbatim
        """
        self.main_buffer_optimization_strategy = new_strategy

    ## @ingroup automatics_cds
    def set_similar_length_optimization(
        self,
        active: bool = True,
        max_length_difference: int = 100,
    ):
        """! @brief Set configuration for optimization step for buffers of similar length.
        @param active: Whether this optmization is run. Default: True
        @param max_length_difference: Higher values result in more register usage
                lower values result in higher BRAM usage. Default: 100"""
        self.additional_optimizations["optimize_similar_length_buffers"] = {
            "active": active,
            "parameters": {"max_length_difference": max_length_difference},
        }

    ## @ingroup automatics_cds
    def set_reshape_long_buffers_optimization(
        self,
        active: bool = True,
        minimum_length_to_reshape: int = -1,
        maximum_width_to_reshape: int = 7,
    ):
        """! @brief Set configuration for optimization step for long and thin buffers.

        @param active: Whether this optimization is run. Default: True
        @param minimum_length_to_reshape: Define a threshold of buffer length
               from when the optimization is applied. If set to '-1', a number
               is calculated from the generic value 'MINIMUM_BRAM_SIZE'.
               Small values result in possibly higher LUT and register usage,
               larger values have smaller impacts and result
               in lower BRAM usage. Default: -1
        @param maximum_width_to_reshape: Define a threshold of maximal buffer
               width up to which the optimization applies. Value should be
               adapted to each system individually.
               Use pipe.print_pipeline_buffer_report(1) to inspect buffers and
               set the value considering the hardware platform
               and the buffers listed. Default: 7"""
        self.additional_optimizations["optimize_thin_and_long_buffers"] = {
            "active": active,
            "parameters": {
                "min_length": minimum_length_to_reshape,
                "maximum_width": maximum_width_to_reshape,
            },
        }

    ## @ingroup automatics_cds
    def set_flushing_behaviour(
        self, debug_flushdata: bool = False, constant_flushdata_value: int = 128
    ):
        """! @brief Configure the flush control module of the pipeline.
        @param debug_flushdata: Whether to use a constant value (False) or
               a generated value (True) (pixel count) to flush the pipeline.
               Default: False
        @param constant_flushdata_value: The constant value to use as flushdata.
               Default: 128"""
        self.pipe_manager.set_generic_value(
            "IS_FLUSHDATA_CONSTANT", "False" if debug_flushdata else "True"
        )
        self.pipe_manager.set_generic_value(
            "CONSTANT_DATA_VALUE", constant_flushdata_value
        )

    ## @ingroup automatics_cds
    def add_module(
        self,
        entity_name: str,
        user_name: str = "",
        repo_name: str = "",
        create_wrapper: bool = False,
    ) -> AsWindowModule:
        """! @brief Add a window module to the pipeline and return it.
        @note Only AsWindowModule modules are available in 2D Window Pipeline systems!
        @param entity_name: Name of the window module to add (as in VHDL)
        @param user_name: Optional. Name used in generated code for this module
        @param repo_name: Optional. Where to look for the module.
        @return A reference to the newly created module.
        """

        if not user_name:
            count = sum(
                (1 for mod in self.modules if mod.entity_name == entity_name)
            )
            user_name = "{}_{}".format(entity_name, count)
        module = self.chain.library.get_module_instance(
            entity_name, repo_name, True
        )
        if module is None:
            raise AsModuleError(
                entity_name, msg="No window module with this name found!"
            )
        module.name = user_name
        if create_wrapper:
            setattr(module, "wrap", True)
        self.modules.append(module)
        module.pipe = self
        # Generate unique names for the module's interfaces (with user_name)
        module.__gen_uname_for_window_ifs__()
        module.assign_to(self)
        module.chain = self.chain
        if isinstance(module, AsWindowModule):
            for wif in module.window_interfaces:
                self.window_ports.append(wif.window_port)

        return module

    ## @ingroup automatics_cds
    def set_pipeline_synchronous(self, is_synchronous: bool = True):
        """! @brief Define the pipeline's strobe behaviour.
        A pipeline is considered synchronous if all inputs and outputs of the
        pipeline update their data at the same time (all strobe signals are synchronized).
        If any module within the pipeline has its own 'strobe_out' port the pipeline
        is no longer considered synchronous. This may be the case if a module
        does not provide new data at every strobe input (for example for scaling
        the image).
        In some cases, this auto-detection may be wrong, though the generated
        system should still work. However, slightly more resources may be used
        and the flushing behaviour may be incorrect.
        @note This characteristic is normally set automatically by Automatics.
        @param is_synchronous  Whether the pipeline should be seen as synchronous
        """
        self.is_pipe_synchronous = is_synchronous

    ## @ingroup automatics_cds
    def print_pipeline_buffer_report(self, verbosity: int = 0):
        """! @brief Prints a report of memory resource requirements for this 2D Window Pipeline.
        Reports on the number of buffers implemented,
        the amount of storage required in bits and the split between storage
        using Block RAM and distributed RAM using registers.
        @param verbosity Set to 1 to print additional reports per buffer."""
        report_buffer_statistics(
            self.buffer_rows, self.minimum_bram_size, verbosity
        )

    ## @ingroup automatics_cds
    def connect(
        self, source, sink, *, no_delay: bool = False, no_stall: bool = False
    ):
        """! @brief Connect a source and sink within the pipeline.
        Any AsModule, Interface, Port or signal may be connected.
        This method stores the desired connection to be connected during the
        system generation process."""
        # Add connection to list to be connected
        self.user_connections.append((source, sink, no_delay, no_stall))

    def _wrap_modules(self):
        wrappers = []
        for mod in self.modules:
            if getattr(mod, "wrap", False):
                wrapper = AsModuleWrapper(self.chain, self)
                wrapper.define_module_to_wrap(mod)
                wrappers.append(wrapper)
        # self.modules.extend(wrappers)
        for wrapper in wrappers:
            try:
                self.modules.remove(wrapper.modules[0])
                self.chain.modules.remove(wrapper.modules[0])
            except ValueError:
                pass
        self.chain.module_groups.extend(wrappers)

    # ------------------------ DELAY MANAGEMENT METHODS ------------------------

    def _propagate_delays(self):
        if len(self.input_streams) == 0:
            LOG.error(
                (
                    "Pipeline '%s' has no input streams!\n"
                    "Cannot perform delay analysis, pipeline generation "
                    "cannot continue! - Abort."
                ),
                self.name,
            )
            raise AsConnectionError(
                self,
                "No input streams for pipeline.",
                "Delay analysis cannot be performed.",
            )
        # Start the delay propagation for all input streams
        for _, _, _, signal in self.input_streams:
            for target in signal.outgoing:
                if isinstance(target.parent, AsWindowInterface):
                    window = target.parent.window
                    set_delay(target, window.get_delay(self.columns) + 1)
                else:
                    set_delay(target, 0)
                set_delay(target.incoming, 0)
                set_delay(signal, 0)
                self._propagate_delay(target)
        self.pipe_manager.set_generic_value(
            "PIPELINE_DEPTH", self.pipeline_delay
        )

    def _propagate_delay(self, source):
        """! @brief Recursive method to propagate a strobe/pixel delay across the pipeline.
        Uses the delay of Port 'source' as the input delay.
        Passes the delay to all output ports of the module.
        Calls itself for all output port connections.
        Stops if moving outside of this module group (the pipeline)
        or when reaching a module with equal or greater input delay."""
        module = get_parent_module(source)
        # Special case for modules looping back a window port
        if module is get_parent_module(source.incoming):
            set_delay(source, module.input_delay)
            return None
        LOG.debug("DP @ '%s' for '%s'", module.name, source.code_name)
        self.pipeline_delay = max(get_delay(source), self.pipeline_delay)
        # If we made it to outside of the pipeline, stop!
        if module.parent is not self:
            LOG.debug("STOP! Outside of pipeline.")
            return None
        try:
            # For window modules: Update the input delay attribute if necessary
            if module.input_delay < get_delay(source):
                module.input_delay = get_delay(source)
                module.__update_delay__()
                LOG.debug("Updated module delay to " + str(module.delay))
            else:
                # We only need to update the delays of the module,
                # if the input delay of the module is greater than
                # the source delay or if it isn't (-1) (initial value)
                LOG.debug("STOP! Module delay is greater than source delay.")
                return None
        except AttributeError:
            # For regular modules: Use the single delay attribute
            if get_delay(module) is not None:
                if get_delay(module) < get_delay(source):
                    # Found an input port with a higher delay than previously
                    # Update the delay and all module connections
                    set_delay(module, get_delay(source))
                    LOG.debug("Updated module delay to " + str(module.delay))
                else:
                    # We only need to update the delays of the module,
                    # if the input delay of the module is greater than
                    # the source delay or if it isn't (-1) (initial value)
                    LOG.debug(
                        "STOP! Module delay is greater/equal than source delay."
                    )
                    return None
            else:  # No delay set, this is the initial pass for this module
                set_delay(module, get_delay(source))
                LOG.debug("Updated module delay to " + module.delay)
        # Need to handle this module! For all ports
        for port in module.get_full_port_list(include_signals=False):
            # We move from a module input to all of it's outputs
            # Only handle non-interface ports that are outputs
            if (
                port.port_type in ("single", "interface")
                and port.get_direction_normalized() == "out"
            ):
                LOG.debug("For port '%s'", port.code_name)
                # Set the delay for this port
                set_delay(port, get_delay(module))
                # Handle all port connections
                for target in port.outgoing:
                    LOG.debug("Found connection to '%s'", target.code_name)
                    # Update the delay for the connected port
                    if isinstance(target.parent, AsWindowInterface):
                        window = target.parent.window
                        set_delay(
                            target,
                            get_delay(module)
                            + window.get_delay(self.columns)
                            + 1,
                        )
                    else:
                        set_delay(target, get_delay(module))
                    # and run this method again for the port
                    self._propagate_delay(target)

    def _add_delay_lines(self):
        """! @brief Add delay lines where needed (automatically).
        For all modules: For every relevant input that has a lower pixel delay
        than the input with the highest pixel delay, add a delay line with a
        length of the difference between the highest delay and the delay
        of the port."""
        for mod in self.modules:
            # All inputs of the module
            input_list = [p for p in mod.ports if p.direction == "in"]
            if isinstance(mod, AsWindowModule):  # Add window inputs
                input_list.extend(
                    (wif.window_port for wif in mod.window_interfaces)
                )
            # Tuple: (Delay value, input port)
            delays = []
            # Compile the delay list; Leave out ports without a delay value
            for inp in input_list:
                try:
                    delays.append((inp.delay, inp))
                except AttributeError:
                    pass
            # If only one input port is present, we don't need any delay lines
            if len(delays) <= 1:
                continue
            # Sort the delay list in descending order
            delays = sorted(delays, key=lambda delay: delay[0], reverse=True)
            high_delay = delays[0][0]

            # Are there any delays that differ from the greatest delay (idx 0)?
            if any((delay[0] != high_delay for delay in delays)):
                # We can skip the first delay, as it is the reference value
                for delay in delays[1:]:
                    # If the delay values differ, add a delay line
                    if delay[0] < high_delay:
                        LOG.info(
                            (
                                "Delay line inserted for\nModule '%s'   \n"
                                "Port   '%s'   \nWith delay  %i\nInput delay %i"
                                "\nPort delay  %i\n"
                            ),
                            mod.name,
                            delay[1].code_name,
                            high_delay - delay[0],
                            high_delay,
                            delay[0],
                        )
                        self._add_delay_line(
                            mod, delay[1], high_delay - delay[0]
                        )

            # -> Else
            # All delays at the inputs of this module are the same!
            # No delay lines needed

    def _add_delay_line(self, module: AsModule, port: Port, delay: int):
        """! @brief Insert a delay line infront of 'port' of 'module'.
        Connect the input of the delay line to the incoming port of 'port'
        and the output to the input of 'port'
        The bit width of the delay line is port's bitwidth
        and the length is the provided 'delay'."""
        source = port.incoming

        dl_name = (
            get_parent_module(source).name
            + "_"
            + source.code_name
            + "_buffer_line_0"
        )
        dl_num = 0
        for buff in self.buffer_rows:
            if (
                buff.name == dl_name
                and buff.inputs[0].port.incoming[0] is source
            ):
                if buff.length == delay:
                    self.__connect__(buff.outputs[0].port, port)
                    return None
                else:
                    dl_name, dl_num = tuple(dl_name.rsplit("_", maxsplit=1))
                    dl_num = int(dl_num) + 1
                    dl_name += "_" + str(dl_num)
                    continue

        delay_line = AsPipelineRow(dl_name, delay - 1, 1, self)

        if get_parent_module(source) is self:
            signame = source.code_name + "_delay_input_" + str(dl_num)
        else:
            signame = (
                get_parent_module(source).name
                + "_"
                + source.code_name
                + "_delay_input_"
                + str(dl_num)
            )

        in_signal = self.define_signal(
            signame, source.data_type, source.data_width
        )
        set_delay(in_signal, get_delay(source))
        source.glue_signal = in_signal
        source.outgoing.append(in_signal)
        in_signal.incoming.append(source)

        if not delay_line.add_input(in_signal):
            raise AsConnectionError(
                port, "Unable to add delay line because of previous errors!"
            )
        # Create an intermediate signal between the buffer and the target port
        if get_parent_module(source) is self:
            signame = source.code_name + "_delayed_" + str(dl_num)
        else:
            signame = (
                get_parent_module(source).name
                + "_"
                + source.code_name
                + "_delayed_"
                + str(dl_num)
            )
        out_signal = self.define_signal(
            signame, source.data_type, source.data_width
        )
        # Remove incoming port connection
        if isinstance(port.parent, AsWindowInterface):
            port.glue_signal = out_signal
        else:
            port.glue_signal = None
            port.incoming = None
            # and reconnect the port with the delayed signal
            self.__connect__(out_signal, port)
        # Add the signal as an output of the buffer line
        delay_line.add_output(out_signal)
        # Add the buffer to the pipeline
        self.buffer_rows.append(delay_line)

    # ---------------------- BUFFER OPTIMIZATION METHODS -----------------------

    def _merge_same_signal_buffers(self):
        """! @brief Optimize buffers that delay the same signal by merging them.
        This method looks for buffers that have the same input signal.
        These buffers of differing delay length are then merged:
        @verbatim
        E.g. sig1 -> [BUFFER 1200] -> out1
             sig1 -> [BUFFER 400 ] -> out2
        Is merged to:
          sig1 -> [BUFFER 400] -+-> [BUFFER 800] -> out1
                                +-> out2
        @endverbatim"""
        treated_signals = []
        removed_buffers = []
        # For every buffer
        for crt_buff in self.buffer_rows:
            if crt_buff in removed_buffers:
                continue
            try:
                crt_signal = crt_buff.inputs[0].port.incoming[0]
            except (IndexError, TypeError):
                continue
            if crt_signal in treated_signals:
                continue
            # Remember which signals we have searched for
            treated_signals.append(crt_signal)
            LOG.debug(
                "Finding buffers to merge for signal '%s'", crt_signal.code_name
            )
            # --------- FIND buffers to merge -----------
            bufflist = [crt_buff]  # List for buffers to merge
            # For all buffers
            for comp_buff in self.buffer_rows:
                if (comp_buff is crt_buff) or (comp_buff in removed_buffers):
                    continue
                try:
                    # Only handle buffers which use the same input signal
                    if crt_signal is not comp_buff.inputs[0].port.incoming[0]:
                        continue
                except (IndexError, TypeError):
                    continue
                # Add this buffer to the list of buffers to merge
                bufflist.append(comp_buff)
            # --------- MERGE buffers -------------------
            # If we found no additional buffers
            if len(bufflist) == 1:
                continue
            # Sort the buffer list ascending by buffer length
            bufflist.sort(key=lambda buff: buff.length)
            LOG.debug("Merging buffers: %s", str(bufflist))
            # Merge the buffers
            prev_buff = bufflist[0]
            for buff in bufflist[1:]:

                # delay_diff is the length that buff needs to be
                start_delay = prev_buff.input_delay
                if start_delay != buff.input_delay:
                    raise AsConnectionError(buff, "Buffer without a delay!")
                delay_diff = buff.output_delay - prev_buff.output_delay
                LOG.debug(
                    "New delay for buffer '%s': %i", buff.name, delay_diff
                )
                buff_input_signal = prev_buff.outputs[0].port
                sig_to_remove = buff.inputs[0].port

                buff.inputs[0].port = buff_input_signal
                for sig_out in sig_to_remove.outgoing:
                    if isinstance(sig_out, GenericSignal):
                        sig_out.incoming.remove(sig_to_remove)
                        sig_out.incoming.append(buff_input_signal)
                    else:
                        sig_out.incoming = buff_input_signal
                # If the delay difference is zero, we can replace buff
                # with prev_buff: Remove buff and all signals and connect the
                # output glue signal of prev_buff to the target of buff
                if delay_diff == 0:
                    # Mark buffer to be removed
                    removed_buffers.append(buff)
                    # Remove the connection for buff's input signal
                    # from the source signal
                    sig_to_remove.incoming[0].outgoing.remove(sig_to_remove)
                    # Remove the input glue signal for buff
                    self.remove_signal(sig_to_remove)
                    # Buff's output glue signal
                    old_source = buff.outputs[0].port
                    # Buff's target port
                    target = old_source.outgoing[0]
                    # Remove the target port's connections to the glue signal
                    target.incoming = None
                    target.glue_signal = None
                    # Remove the glue signal
                    self.remove_signal(old_source)
                    # Connect the output glue signal of prev_buff to the target
                    self.__connect__(
                        prev_buff.outputs[0].port,
                        target,
                    )
                else:
                    # Update buff input delay
                    buff.input_delay = prev_buff.output_delay
                    # Change BUFFs length to the delay difference
                    buff.set_buffer_length(delay_diff)
                    # Move to next buffer
                    prev_buff = buff
        for buff in removed_buffers:
            # Remove buffers that were merged into other buffers
            self.modules.remove(buff.module)
            self.buffer_rows.remove(buff)

    def _merge_same_length_buffers_window_width_sensitive(self):
        """! @brief Merge buffers of the same length and window width."""
        buffdict = {}  # Dictionary of buffer rows keyed by (length, window)
        # Collect, sort and filter buffer rows
        for buff in self.buffer_rows:
            key = (buff.length, buff.window_width)
            try:
                buffdict[key].append(buff)
            except KeyError:
                buffdict[key] = [buff]
        # For all buffers
        for key in buffdict:
            # Order does not matter, only sorted for deterministic results
            bufflist = sorted(buffdict[key], key=lambda b: b.name)
            if len(bufflist) < 2:
                continue  # No buffers to merge (need at least 2)
            main_buff = bufflist[0]
            for mbuff in bufflist[1:]:
                LOG.debug(
                    "Merging buffer '%s' into '%s'", mbuff.name, main_buff.name
                )
                main_buff.merge(mbuff)
                # Remove buffer that was merged into main_buff
                self.modules.remove(mbuff.module)
                self.buffer_rows.remove(mbuff)

    def _merge_all_same_length_buffers(self):
        """! @brief Merge buffers of the same length indifferent to window width.
        Results in larger-than-necessary register windows for some buffers."""
        buffdict = {}  # Dictionary of buffer rows keyed by length
        # Collect and sort buffer rows
        for buff in self.buffer_rows:
            key = buff.length
            try:
                buffdict[key].append(buff)
            except KeyError:
                buffdict[key] = [buff]
        # For all buffers
        for key in buffdict:
            # Sort by winodw width descending: The buffer with the largest
            # window needs to be at index 0!
            bufflist = sorted(
                buffdict[key], key=lambda b: b.window_width, reverse=True
            )

            if len(bufflist) < 2:
                continue  # No buffers to merge (need at least 2)
            main_buff = bufflist[0]
            for mbuff in bufflist[1:]:
                LOG.debug(
                    "Merging buffer '%s' into '%s'", mbuff.name, main_buff.name
                )
                main_buff.merge(mbuff)
                # Remove buffer that was merged into main_buff
                self.modules.remove(mbuff.module)
                self.buffer_rows.remove(mbuff)

    def _merge_same_length_buffers_row_sensitive(self):
        """! @brief Merge buffers of the same length and row index and window width.
        Results in more legible code. Not a very effective optimization strategy.
        May consider removing this method."""
        buffdict = {}
        BuffEntry = namedtuple("BuffEntry", ["buff", "row_idx", "windowsize"])
        for buff in self.buffer_rows:
            if buff.get_size() < self.minimum_bram_size:
                continue
            if buff.is_window_signal[0]:
                row_idx = buff.to_window_ports[0][0][1]
            else:
                row_idx = 0
            be = BuffEntry(
                buff=buff, row_idx=row_idx, windowsize=buff.window_width
            )
            try:
                buffdict[buff.length].append(be)
            except KeyError:
                buffdict[buff.length] = [be]
        for bufflist in list(buffdict.values()):
            bufflist.sort(key=lambda be: be.windowsize, reverse=True)
            bufflist.sort(key=lambda be: be.row_idx)

            crt_be = bufflist[0]
            for be in bufflist[1:]:
                if crt_be.row_idx < be.row_idx:
                    crt_be = be
                    continue
                crt_be.buff.merge(be.buff)
                self.modules.remove(be.buff.module)
                self.buffer_rows.remove(be.buff)

    def _merge_similiar_length_buffers_(
        self,
        max_length_difference: int = 100,
    ):
        """! @brief Buffer optimization to merge buffers of similar length.
        Adds additional small buffer to the longer of both buffers.
        @param max_length_difference: The largest allowed buffer length difference
                    Buffers with larger length disaparaties are not optimized"""
        bufflist = sorted(self.buffer_rows, key=lambda b: b.length)
        bufflist = [b for b in bufflist if not any(b.is_window_signal)]
        if len(bufflist) < 1:
            return None

        if max_length_difference < 1:
            return None

        prev_buff = bufflist[0]
        for buff in bufflist[1:]:
            diff = buff.length - prev_buff.length
            if diff == 0 or diff > max_length_difference:
                prev_buff = buff
                continue
            else:
                prev_buff.merge(buff, merge_outputs=False)
                buff.set_buffer_length(diff)
                sig = buff.inputs[0].port
                inter_signal = self.define_signal(
                    sig.code_name + "_intermediate",
                    sig.data_type,
                    sig.data_width,
                )
                set_delay(inter_signal, prev_buff.output_delay)
                prev_buff.add_output(inter_signal)
                buff.inputs[0].port = inter_signal

    def _reshape_long_buffers(
        self, min_length: int = -1, maximum_width: int = 7
    ):
        """! @brief Buffer optimization reshaping long and thin buffers.
        This optimization turns long and thin buffers into wider but shorter
        buffers, potentially using fewer BRAM resources.
        @param min_length  Any buffers shorter than this value are not optimized
                This value is also used as a target length for the optimization
        @param maximum_width  Buffers wider than this value are not optimzed"""

        if min_length == -1:
            min_length = int(self.minimum_bram_size * 2.5)
        elif min_length < self.minimum_bram_size:
            return None

        bufflist = [
            b
            for b in self.buffer_rows
            if b.length > min_length
            and b.get_bit_width() <= maximum_width
            and not any(b.is_window_signal)
            and len(b.inputs) == 1
        ]

        for buff in bufflist:
            iterations = int(buff.length / min_length)
            new_length = int(buff.length / iterations)
            left_over = buff.length - new_length * iterations

            buff.set_buffer_length(new_length)
            bsig = buff.outputs[0].port
            buff.remove_outputs()
            for n in range(iterations - 1):
                intersig = self.define_signal(
                    bsig.code_name + "_loopdelay_" + str(n),
                    bsig.data_type,
                    bsig.data_width,
                )
                set_delay(intersig, buff.input_delay + new_length * (n + 1))
                buff.add_output(intersig)
                buff.add_input(intersig, check_delay=False)
            if left_over == 0:
                buff.add_output(bsig)
            else:
                buff.output_delay = new_length * iterations
                new_buff = AsPipelineRow(
                    buff.name + "_last_delay", left_over, 1, self
                )
                intersig = self.define_signal(
                    bsig.code_name + "_last_delay",
                    bsig.data_type,
                    bsig.data_width,
                )
                set_delay(intersig, buff.output_delay - left_over)
                buff.add_output(intersig)
                new_buff.add_input(intersig)
                new_buff.add_output(bsig)
                self.buffer_rows.append(new_buff)

    # ------------------------ CODE GENERATION METHODS -------------------------

    ## @ingroup automatics_generate
    def _generate_window_signals(self):
        to_generate = {}
        port_list = copy(self.window_ports)
        port_list = list(filter(lambda p: p.incoming is not None, port_list))
        port_list.sort(key=lambda p: p.parent.window.y)
        port_list.sort(key=lambda p: p.parent.window.x)
        port_list.sort(key=lambda p: p.data_width.get_bit_width())
        port_list.sort(key=lambda p: p.incoming.code_name)

        PortData = namedtuple("PortData", ["incoming", "wx", "wy", "wb"])

        def get_port_data(window_port: Port) -> PortData:
            return PortData(
                incoming=window_port.incoming,
                wx=window_port.parent.window.x,
                wy=window_port.parent.window.y,
                wb=window_port.data_width.get_bit_width(),
            )

        if len(port_list) > 0:
            crt_port = port_list[0]
            to_generate[crt_port.incoming] = [crt_port]
            if len(port_list) > 1:
                crt_port_data = get_port_data(crt_port)

                for wp in port_list[1:]:
                    if wp.incoming is None:
                        continue
                    wp_data = get_port_data(wp)
                    if crt_port_data == wp_data:
                        to_generate[crt_port.incoming].append(wp)
                    else:
                        crt_port = wp
                        crt_port_data = get_port_data(wp)
                        to_generate[wp.incoming] = [wp]

        for _, connect_to in to_generate.items():
            signame = (
                get_parent_module(connect_to[0]).name
                + "_"
                + connect_to[0].code_name
            )
            wsig = self.define_signal(
                signame, connect_to[0].data_type, connect_to[0].data_width
            )
            self.window_signals.append(wsig)
            setattr(wsig, "window_config", connect_to[0].window_config)
            for wp in connect_to:
                self.__connect__(wsig, wp)

    ## @ingroup automatics_generate
    def _generate_pipeline(self, chain, code_dict: dict):
        generate_window_assignments(self.window_signals, code_dict)
        self._handle_ooc_modules(self.modules, code_dict)

    ## @ingroup automatics_generate
    def _handle_ooc_modules(self, modules: list, code_dict: dict):
        ooc_modules = [
            mod for mod in modules if isinstance(mod, AsModuleWrapper)
        ]
        conversion_template = (
            "f_convert_generic_window_to_vector({source_signal})"
        )
        # Xilinx Vivado Out-of-Context Synthesis can't deal with custom
        # data types. -> Serialize t_generic_window of the window port
        # to a std_logic_vector using a GenericSignal
        for mod in ooc_modules:
            wports = mod.convert_window_port_to_vector()
            for wport in wports:
                if not wport.incoming:
                    continue
                signame = wport.incoming.code_name + "_to_vector"
                sig = self.get_signal(signame)
                if not sig:
                    sigvalue = conversion_template.format(
                        source_signal=wport.incoming.code_name
                    )
                    sig = self.define_signal(
                        signame, wport.data_type, wport.data_width, sigvalue
                    )
                wport.incoming = sig
                wport.glue_signal = sig
            # Xilinx Vivado OOC Runs can't deal with entity declarations
            # Modules have to be declared as components
            declr_str = generate_component_declaration(mod)
            code_dict["signals"].append(declr_str)

    # --------------------- CONNECTION MANAGEMENT METHODS ----------------------

    ## @ingroup automatics_connection
    def auto_connect(self):
        """Handle all management and connection tasks required to build this
        pipeline module group."""
        self.minimum_bram_size = self.get_generic(
            "MINIMUM_BRAM_SIZE"
        ).get_value()

        # Determine synchronisity if not manually set
        if self.is_pipe_synchronous is None:
            self.is_pipe_synchronous = self._check_pipeline_synchronisity()

        # Insert the appropriate manager module
        self._insert_pipeline_management_module()

        self.__update_generics_list__()
        for mod in self.modules:
            for inter in mod.window_interfaces:
                inter.update_window()
            self.chain._extract_generics(mod)

        # Apply user connections
        self._run_user_connect_calls()
        for mod in self.modules:
            for port in mod.get_full_port_list():
                resolve_generic(port)
        self.__update_generics_list__()
        # foreach(self.get_full_port_list(), resolve_generic)

        super().auto_connect()

        # Generate and apply delay numbers
        self._propagate_delays()
        # Add delay lines where needed
        self._add_delay_lines()
        # Add window buffer lines
        self._add_window_buffers()
        # Manage and connect inputs and output streams of this pipeline
        self._resolve_inout_streams()
        # Manage stall ports
        self._connect_stall_signals()
        self._connect_strobe_signals()
        # Optimize buffers that delay the same signal
        self._merge_same_signal_buffers()
        # Optimize buffers that have a similiar length,
        # merging them to a larger and a small buffer
        if self.additional_optimizations["optimize_similar_length_buffers"][
            "active"
        ]:
            self._merge_similiar_length_buffers_(
                **(
                    self.additional_optimizations[
                        "optimize_similar_length_buffers"
                    ]["parameters"]
                )
            )
        # Optimize buffers by shrinking the length of long and thin buffers and
        # looping the signal through the buffer
        # Adds a small buffer for uneven buffer lengths
        if self.additional_optimizations["optimize_thin_and_long_buffers"][
            "active"
        ]:
            self._reshape_long_buffers(
                **(
                    self.additional_optimizations[
                        "optimize_thin_and_long_buffers"
                    ]["parameters"]
                )
            )
        # Optimize buffers that have the same buffer length by merging them
        if self.main_buffer_optimization_strategy:
            self.main_buffer_optimization_strategy()

        # Create connective signals for buffer rows
        foreach(self.buffer_rows, lambda buf: buf.build_inout_vectors())
        # Create window signal assignment statements
        self._generate_window_signals()

        # Create wrapper files for modules to be wrapped
        # Required for out-of-context synthesis of modules
        self._wrap_modules()

    def _check_pipeline_synchronisity(self):
        for mod in self.modules:
            port = mod.get_port("strobe_out", suppress_error=True)
            if port is not None:
                return False
        return True

    def _insert_pipeline_management_module(self):

        internal_flush_signal = self.define_signal("flush")

        internal_ready_signal = self.define_signal("pipeline_ready")
        sw_reset_signal = self.define_signal("sw_reset")

        # Add module
        # if self.is_pipe_synchronous:
        #    self.pipe_manager = self.add_module("as_pipeline_flush")
        # else:
        self.pipe_manager = self.add_module("as_pipeline_manager")

        if self.is_pipe_synchronous:
            self.pipe_manager.set_generic_value("PIPELINE_SYNCHRONOUS", "true")
        else:
            self.pipe_manager.set_generic_value("PIPELINE_SYNCHRONOUS", "false")

        self.pipe_manager.set_generic_value("IMAGE_WIDTH", self.columns)
        self.pipeline_stall_in_flush = self.pipe_manager.get_port(
            "pipeline_stall_in"
        )
        self.pipeline_strobe_in_flush = self.pipe_manager.get_port(
            "result_strobe_in"
        )

        # Set default flush behaviour
        self.set_flushing_behaviour()
        # Get ports for internal connections
        ready_port_flush = self.pipe_manager.get_port("ready")
        strobe_port_flush = self.pipe_manager.get_port("pipeline_strobe_out")
        stall_out_port_flush = self.pipe_manager.get_port("input_stall_out")
        self.stall_in_port_flush = self.pipe_manager.get_port("output_stall_in")
        in_data_in_port_flush = self.pipe_manager.get_port("input_data_in")
        out_data_out_port_flush = self.pipe_manager.get_port("output_data_out")
        out_data_in_port_flush = self.pipe_manager.get_port("result_data_in")
        in_data_out_port_flush = self.pipe_manager.get_port("pipeline_data_out")
        outgoing_strobe_flush = self.pipe_manager.get_port("output_strobe_out")
        outgoing_strobes_valid_flush = self.pipe_manager.get_port(
            "output_data_valid"
        )

        flush_done_flush = self.pipe_manager.get_port("flush_done_out")

        internal_ready_signal.make_external("ready_out")

        #  - Connect flushing module signals
        self.connect(ready_port_flush, internal_ready_signal)
        self.connect(strobe_port_flush, self.internal_strobe_signal)
        self.connect(self.input_stream_in, in_data_in_port_flush)
        self.connect(out_data_in_port_flush, self.output_stream_in)
        self.connect(self.input_stream_out, in_data_out_port_flush)
        self.connect(out_data_out_port_flush, self.output_stream_out)
        self.connect(outgoing_strobe_flush, self.outgoing_strobe_signal)
        self.connect(
            self.outgoing_strobes_valid_signal, outgoing_strobes_valid_flush
        )
        self.connect(self.stall_signal_outgoing, stall_out_port_flush)
        self.connect(flush_done_flush, self.flush_done)

        #  - Registers & standard status & control signals
        self.assign_register_to_port(0, sw_reset_signal, 0)
        self.assign_register_to_port(0, internal_flush_signal, 1)
        self.assign_port_to_register(1, internal_ready_signal, 0)
        self.modify_register_type(0, Register.both)
        self.assign_port_to_register(
            0,
            self.define_signal(
                "register_0_neutral_value",
                "std_logic_vector",
                Port.DataWidth(31, "downto", 0),
                'X"00000000"',
            ),
            0,
        )

    ## @ingroup automatics_connection
    def _add_input_stream(self, stream_in, target: Port):
        in_port = None
        if isinstance(stream_in, Port):
            in_port = stream_in
            stream_in = None

        elif (not isinstance(stream_in, Interface)) or (
            stream_in.type != AsStream.INTERFACE_TYPE_NAME
        ):
            raise AsConnectionError(
                self,
                (
                    "Cannot add interface '{}' of type '{}' as an input stream "
                    "for pipeline '{}'. Only type '{}' allowed!"
                ).format(
                    stream_in.unique_name,
                    stream_in.type,
                    self.name,
                    AsStream.INTERFACE_TYPE_NAME,
                ),
            )
        # If we have already connected to this target
        if any(
            (in_stream.target is target for in_stream in self.input_streams)
        ):
            LOG.warning(
                "Cannot connect two streams to one target in a pipeline!"
            )
            return None
        # For input ports
        if stream_in is None and in_port is not None:
            if any((in_port is i.stream for i in self.input_streams)):
                input_tuple = next(
                    (i for i in self.input_streams if in_port is i.stream)
                )
                _, pipe_port, _, intermediate_signal = input_tuple
                pipe_port = in_port
            # Check if the input port is part of any already added input streams
            elif any((in_port.parent is i.stream for i in self.input_streams)):
                pipe_if = next(
                    (
                        i.pipe_if
                        for i in self.input_streams
                        if in_port.parent is i.stream
                    )
                )
                pipe_port = pipe_if.get_port(in_port.name)
                intermediate_signal = self.define_signal(
                    pipe_if.name_prefix + in_port.name + "_stream_in",
                    in_port.data_type,
                    in_port.data_width,
                )
                intermediate_signal.generics = copy(pipe_port.generics)
                intermediate_signal.data_width = resolve_data_width(
                    intermediate_signal
                )
                self.input_streams.append(
                    self.InputStream(
                        in_port, pipe_port, target, intermediate_signal
                    )
                )

            else:
                # If this is not a port of an existing input stream:
                # + Duplicate the source port and add it to this pipeline module
                # + Create the intermediate signal
                # + Add the input stream tuple
                pipe_port = in_port.duplicate()
                pipe_port.port_type = "single"
                self.add_port(pipe_port)
                pipe_port.code_name = (
                    get_parent_module(in_port).name + "_" + in_port.code_name
                )
                pipe_port.direction = (
                    "in"
                    if in_port.get_direction_normalized() == "out"
                    else "out"
                )
                pipe_port.in_entity = True
                # Early return for when the port shouldn't be managed or delayed
                # Eg: port for control / not data
                if getattr(in_port, "nodelay", False):
                    return pipe_port

                intermediate_signal = self.define_signal(
                    pipe_port.code_name + "_stream_in",
                    pipe_port.data_type,
                    pipe_port.data_width,
                )
                intermediate_signal.generics = copy(pipe_port.generics)
                intermediate_signal.data_width = resolve_data_width(
                    intermediate_signal
                )
                self.input_streams.append(
                    self.InputStream(
                        in_port, pipe_port, target, intermediate_signal
                    )
                )

        # If this stream hasn't been addded as an input for this pipeline yet
        elif not any((item.stream is stream_in for item in self.input_streams)):
            # Duplicate the source interface and add it to this pipeline
            pipe_if = stream_in.duplicate()
            pipe_if.direction = "out" if stream_in.direction == "in" else "in"
            pipe_if.set_prefix_suffix(
                (stream_in.parent.name + "_" + pipe_if.name_prefix).replace(
                    "__", "_"
                ),
                pipe_if.name_suffix,
            )
            self.add_interface(pipe_if)
            set_unique_name(pipe_if, self)
            pipe_if.in_entity = True

            # Create an intermediate signal for the data stream
            data = pipe_if.get_port("data")
            intermediate_signal = self.define_signal(
                pipe_if.name_prefix + "data_stream_in",
                data.data_type,
                data.data_width,
            )
            intermediate_signal.generics = copy(data.generics)
            intermediate_signal.data_width = resolve_data_width(
                intermediate_signal
            )
            if not self.is_pipe_synchronous:
                if pipe_if.has_port("vsync"):
                    self.pipe_manager.get_port("input_vsync_in").set_value(
                        pipe_if.get_port("vsync").code_name
                    )
                if pipe_if.has_port("hsync"):
                    self.pipe_manager.get_port("input_hsync_in").set_value(
                        pipe_if.get_port("hsync").code_name
                    )
            self.input_streams.append(
                self.InputStream(
                    stream_in, pipe_if, target, intermediate_signal
                ),
            )
        else:  # Stream already an input stream list
            # Get data to complete the connection process
            input_tuple = next(
                (
                    item
                    for item in self.input_streams
                    if item.stream is stream_in
                )
            )
            # Unpack input_stream tuple:
            # Don't overwrite vars that are different for this input connection
            _, pipe_if, _, intermediate_signal = input_tuple

        target.incoming = intermediate_signal
        intermediate_signal.outgoing.append(target)
        target.set_connected()
        if in_port:
            return pipe_port
        return pipe_if

    ## @ingroup automatics_connection
    def _resolve_inout_streams(self):
        bit_width = 0
        strobe_list = []
        stall_list = []

        # ---------------------------- IN -------------------------

        # @action Handle the input streams:
        # Resulting architecture:
        # @vision  [              _ pipeline_module_group _                    ]
        # @v in0 ->[-> in_stream_in->[FLUSH]->in_stream_out-\->in_0_managed->..]
        # @v in1 ->[->/                                      ->in_1_managed->..]
        # @v       [->strobe0 and strobe1-↑                                    ]
        # For all registered input streams
        for _, stream, target, data_signal in self.input_streams:
            if isinstance(stream, Interface):
                # Get the data ports and make sure the data widths are resolved
                data = stream.get_port("data")

                strobe_list.append(stream.get_port("strobe"))
                try:
                    self.__connect__(
                        stream.get_port("stall"), self.stall_signal_outgoing
                    )
                except NameError:
                    pass
            elif isinstance(stream, Port):
                data = stream

            for data_port in (data, target, data_signal):
                data_port.data_width = resolve_data_width(data_port)
                if not data_port.data_width.is_resolved():
                    raise AsConnectionError(
                        data_port,
                        "Cannot resolve data width of port. "
                        "Cannot build assignment of input "
                        "streams for pipeline '{}'".format(self.name),
                    )
            if data.data_width > target.data_width:
                raise AsConnectionError(
                    stream,
                    (
                        "Cannot connect '{}' and '{}' "
                        "within pipeline '{}'. Data widths do not match!"
                    ).format(stream, target, self.name),
                )
            self.input_stream_out.assign_from_this_vector(
                data_signal, bit_width
            )
            # Assign all input streams to one large signal
            self.input_stream_in.assign_to_this_vector(data, bit_width)

            # Accumulate the resulting bit width
            bit_width += data.data_width.get_bit_width()

        # Assign the input strobe port of the flush module to
        # an AND combination of all input streams
        assign_str = " and ".join((port.code_name for port in strobe_list))
        stream_in_strobe = self.define_signal(
            "strobe_in_combined", fixed_value=assign_str
        )
        self.__connect__(
            self.pipe_manager.get_port("input_strobe_in"), stream_in_strobe
        )
        # Update the data width of all internal input stream data signals
        self.input_stream_in.data_width = Port.DataWidth(
            bit_width - 1, "downto", 0
        )
        self.input_stream_out.data_width = Port.DataWidth(
            bit_width - 1, "downto", 0
        )
        # and its input data width generic
        self.pipe_manager.set_generic_value("DIN_WIDTH", bit_width)

        # ------------------------ OUT --------------------------------
        # Reset variables
        bit_width = 0
        stall_list.clear()
        strobe_list.clear()

        # @action Handle the output streams:
        # Resulting architecture:
        # @vision  [           _ pipeline_module_group _               ]
        # @v [ filter0->out_stream->[FLUSH]->out_stream_managed-\->out0]->mod0
        # @v [ filter1->/                                        ->out1]->mod1

        for stream, source, out_signal, _ in self.output_streams:
            # Get ports of interface (pipeline)
            data = stream.get_port("data")
            strobe = stream.get_port("strobe")
            stall = stream.get_port("stall", suppress_error=True)
            stream_in = None
            # For output streams
            if isinstance(source, Interface):
                stream_in = source
                source = stream_in.get_port("data")

            for data_port in (data, source, out_signal):
                data_port.data_width = resolve_data_width(data_port)
                if not data_port.data_width.is_resolved():
                    raise AsConnectionError(
                        data_port,
                        "Cannot resolve data width of port. "
                        "Cannot build assignment of output "
                        "streams for pipeline '{}'".format(self.name),
                    )
            # Make sure the interface's data width matches the source data width
            if data.data_width != source.data_width:
                raise AsConnectionError(
                    stream,
                    (
                        "Cannot connect interfaces '{}' and '{}' "
                        "within pipeline '{}'. Data widths do not match!"
                    ).format(stream, out_signal, self.name),
                )

            vcomplete = stream.get_port("vcomplete", suppress_error=True)
            if not vcomplete:
                vcomplete = stream.get_port(
                    "data_unit_complete", suppress_error=True
                )
            if vcomplete:
                vcomplete.incoming = self.flush_done
                self.flush_done.outgoing.append(vcomplete)
            # Assign all output data streams to one large signal
            self.output_stream_in.assign_to_this_vector(source, bit_width)
            # Assign to the signal
            self.output_stream_out.assign_from_this_vector(
                out_signal, bit_width
            )
            # Connect the signal with the output stream
            self.__connect__(data, out_signal)
            if stream_in:
                out_strobe = stream_in.get_port("strobe")
                if out_strobe.glue_signal:
                    strobe_glue = out_strobe.glue_signal
                else:
                    strobe_glue = GlueSignal(
                        get_parent_module(out_strobe).name
                        + "_"
                        + out_strobe.code_name
                        + "_signal"
                    )
                    out_strobe.glue_signal = strobe_glue
                    out_strobe.outgoing.append(strobe_glue)
                fixed = self.define_signal(
                    out_strobe.code_name
                    + "_"
                    + stream_in.parent.name
                    + "_fixed_value",
                    fixed_value="{} and {}".format(
                        self.outgoing_strobes_valid_signal.code_name,
                        strobe_glue.code_name,
                    ),
                )
                # strobe.glue_signal = fixed
                strobe.incoming = fixed
                fixed.outgoing.append(strobe)
            else:
                # Connect the strobe signal with the global strobe output signal
                self.__connect__(strobe, self.outgoing_strobe_signal)
            if stall:
                stall_list.append(stall)
            # Accumulate the bit width
            bit_width += data.data_width.get_bit_width()

        if stall_list:
            # Assign the input stall port of the flush module to
            # an OR combination of all input streams
            assign_str = " or ".join(
                sorted((port.code_name for port in set(stall_list)))
            )
            self.flush_in_stall = self.define_signal(
                "stall_in_combined", fixed_value=assign_str
            )
            self.__connect__(self.flush_in_stall, self.stall_in_port_flush)

        self.pipe_manager.set_generic_value("DOUT_WIDTH", bit_width)
        if bit_width == 0:
            self.remove_signal(self.output_stream_in)
            self.remove_signal(self.output_stream_out)
        else:
            # Update the data width of all internal output stream data signals
            self.output_stream_in.data_width = Port.DataWidth(
                bit_width - 1, "downto", 0
            )
            self.output_stream_out.data_width = Port.DataWidth(
                bit_width - 1, "downto", 0
            )

    ## @ingroup automatics_connection
    def _add_output_stream(self, source, stream_out: Interface) -> Interface:
        """Create a new as_stream interface for the pipeline to connect to
        a module from within the pipeline."""
        stream_in = None
        if not isinstance(stream_out, AsStream):
            raise AsConnectionError(
                self,
                (
                    "Cannot add interface '{}' of type '{}' as an output stream "
                    "for pipeline '{}'. Only type '{}' allowed!"
                ).format(
                    stream_out.unique_name,
                    stream_out.type,
                    self.name,
                    AsStream.INTERFACE_TYPE_NAME,
                ),
            )
        if isinstance(source, Interface):
            stream_in = source
            source = stream_in.get_port("data")
        if not any(
            (
                stream_out.unique_name in row_name
                for row_name in [
                    item.stream.unique_name for item in self.output_streams
                ]
            )
        ):
            foreach(stream_out.ports, resolve_generic)
            pipe_if = stream_out.duplicate()

            try:
                if stream_in.no_stall:
                    pipe_if.remove_port("stall")
            except AttributeError:
                pass

            pipe_if.direction = "out" if stream_out.direction == "in" else "in"
            if isinstance(get_parent_module(source), AsWindowModule):
                pipe_if.set_prefix_suffix(
                    (
                        get_parent_module(source).name
                        + "_"
                        + pipe_if.name_prefix
                    ).replace("__", "_"),
                    pipe_if.name_suffix,
                )
            else:
                pipe_if.set_prefix_suffix(
                    (source.code_name + "_" + pipe_if.name_prefix).replace(
                        "__", "_"
                    ),
                    pipe_if.name_suffix,
                )

            self.add_interface(pipe_if)
            set_unique_name(pipe_if, self)
            pipe_if.in_entity = True
            self.chain.__connect__(pipe_if, stream_out, top=self.parent)

            if get_parent_module(source) is self:
                signame = source.code_name + "_data_out_synced"
            else:
                signame = get_parent_module(source).name + "_data_out_synced"

            # Create an intermediate signal
            out_signal = self.define_signal(
                signame,
                data_type=source.data_type,
                data_width=source.data_width,
            )

            out_signal.generics = copy(source.generics)
            if stream_in:
                self.output_streams.append(
                    self.OutputStream(
                        pipe_if, stream_in, out_signal, stream_out
                    )
                )
            else:
                self.output_streams.append(
                    self.OutputStream(pipe_if, source, out_signal, stream_out)
                )
            return pipe_if
        else:
            LOG.warning(
                (
                    "Attempted to add interface '%s' as output stream "
                    "for pipeline '%s' more than once!"
                ),
                str(stream_out),
                self.name,
            )

    ## @ingroup automatics_connection
    def _connect_stall_signals(self):
        """Connects incoming and outgoing stall ports
        of modules in this pipeline."""
        if not self.is_pipe_synchronous:
            stall_list = []
            # Collect stall ports of modules
            for mod in self.modules:
                stall_port = mod.get_port("stall_in", suppress_error=True)
                if stall_port is not None:
                    stall_list.append(stall_port)
            # If there are module with stall outputs
            if stall_list:
                stall_signals = []
                # Connect outgoing stall signals:
                # Create a signal per port
                for stall_port in stall_list:
                    signame = (
                        get_parent_module(stall_port).name
                        + "_"
                        + stall_port.code_name
                    )
                    signal = self.define_signal(signame)
                    self.__connect__(stall_port, signal)
                    stall_signals.append(signal)

                # Combine stalls using "or" gates
                stall_str = " or ".join(
                    (sig.code_name for sig in stall_signals)
                )
                combined_stall_signal = self.define_signal(
                    "pipeline_module_stall_combined", fixed_value=stall_str
                )
                # Connect the combined signals to the pipeline manager
                self.__connect__(
                    combined_stall_signal, self.pipeline_stall_in_flush
                )

        # Assign the combined stall signal to all modules with a stall input
        if self.flush_in_stall:
            for mod in self.modules:
                # For all modules that have stall inputs
                stall_port = mod.get_port("stall_out", suppress_error=True)
                if stall_port is not None:
                    self.__connect__(self.flush_in_stall, stall_port)

    ## @ingroup automatics_connection
    def _connect_strobe_signals(self):
        # We only do this if the pipeline is not synchronous
        if self.is_pipe_synchronous:
            return

        strobe_list = []
        exclude_mods = ("as_pipeline_row", self.pipe_manager.entity_name)
        for mod in self.modules:
            if mod.entity_name not in exclude_mods:
                port = mod.get_port("strobe_out", suppress_error=True)
                if port is not None:
                    if port.glue_signal is None:
                        glue = self.define_signal(
                            mod.name + "_" + port.code_name
                        )
                        self.__connect__(port, glue)
                        port.glue_signal = glue
                    strobe_list.append(port.glue_signal)

        if strobe_list:
            assign_str = " or ".join(
                sorted((repr(port).strip("'") for port in set(strobe_list)))
            )
            strobe_out_combined = self.define_signal(
                "pipeline_strobe_out_combined", fixed_value=assign_str
            )
            self.__connect__(strobe_out_combined, self.pipeline_strobe_in_flush)

    ## @ingroup automatics_connection
    def _add_window_buffers(self):
        """! @brief Create all single line buffers required by the window ports."""
        # For all window ports
        for wp in self.window_ports:
            # If the window port is not connected, skip it
            if wp.incoming is None:
                continue
            im_signal = None
            # Grab the window definition
            window = wp.parent.window
            winter = wp.parent
            # For all lines of the window
            for row_idx in range(window.y):
                # Compute the length of buffer required
                if row_idx == window.y - 1:
                    buf_len = window.x
                else:
                    buf_len = self.columns
                try:
                    buf = self.buffer_map[wp.incoming][row_idx]
                    if buf.length == buf_len and buf.window_width >= window.x:
                        if row_idx == 0:
                            if wp.glue_signal:
                                source = wp.glue_signal
                            elif wp.incoming.glue_signal:
                                source = wp.incoming.glue_signal
                            else:
                                source = wp.incoming
                        else:
                            source = im_signal
                        buf.add_window_port_target(source, wp, row_idx)
                        im_signal = buf.outputs[0].port
                        winter.incoming.append(buf)

                        continue
                except (KeyError, IndexError):
                    pass
                # Create a name for the buffer instance
                if get_parent_module(wp.incoming) is self:
                    bufname = wp.incoming.name + "_buffer_row_" + str(row_idx)
                else:
                    bufname = (
                        get_parent_module(wp.incoming).name
                        + "_buffer_row_"
                        + str(row_idx)
                    )
                if row_idx == window.y - 1:
                    bufname += "_end"
                # Create the buffer management object
                buf = AsPipelineRow(bufname, buf_len, window.x, self)
                # Register the new buffer
                self.buffer_rows.append(buf)
                try:
                    self.buffer_map[wp.incoming].append(buf)
                except KeyError:
                    self.buffer_map[wp.incoming] = [buf]
                winter.incoming.append(buf)
                # Create intermediate connection signals and connect them
                # Managed by the buffer object
                if row_idx == 0:
                    im_signal = buf.add_window_interface_row(wp.parent, row_idx)
                else:
                    im_signal = buf.add_window_interface_row(
                        wp.parent, row_idx, im_signal
                    )

    ## @ingroup automatics_connection
    def _run_user_connect_calls(self):
        # Run all user connection jobs
        for conjob in self.user_connections:
            LOG.debug(
                "[%s] Connect [%s] -> [%s]",
                self.name,
                conjob[0].name,
                conjob[1].name,
            )
            if conjob[2]:
                source, _ = swap_if_necessary(conjob[0], conjob[1])
                setattr(source, "nodelay", True)
            if conjob[3]:
                source, _ = swap_if_necessary(conjob[0], conjob[1])
                setattr(source, "no_stall", True)
            self.__connect__(*conjob[:2])

    ## @ingroup automatics_connection
    def __connect__(self, source, sink):
        """! @brief Internal connect method.
        The connection is executed immediately."""
        # Make sure data direction is OK
        source, sink = swap_if_necessary(source, sink)

        if isinstance(source, AsWindowModule):
            self.__connect_window_module__(source, sink)
        elif isinstance(source, AsModule):
            self.__connect_module__(source, sink)
        elif isinstance(source, Interface):
            self.__connect_interface__(source, sink)
        elif isinstance(source, Port):
            if isinstance(
                get_parent_module(source), (AsWindowModule, As2DWindowPipeline)
            ) or isinstance(
                get_parent_module(sink), (AsWindowModule, As2DWindowPipeline)
            ):
                self.__connect_port__(source, sink)
            else:
                # Delegate to chain
                self.chain.__connect__(source, sink, top=self)
        else:
            raise AsConnectionError(
                source,
                "Invalid object as source for connection call!",
                "Object '{}' used in connect method.".format(str(source)),
            )

    ## @ingroup automatics_connection
    def __connect_window_module__(self, source: AsWindowModule, sink):
        if isinstance(sink, (AsWindowModule, AsWindowInterface)):
            for winter in source.window_interfaces:
                self.__connect__(winter, sink)
            if isinstance(sink, AsWindowModule):
                for inter in sink.interfaces:
                    self.__connect__(source, inter)
        elif isinstance(sink, AsStream) and sink.parent.parent is not self:
            for inter in source.interfaces:
                if inter.direction == "out":
                    self.__connect_interface__(inter, sink)
        elif isinstance(sink, (AsModule, Interface, Port)):
            self.chain.__connect__(source, sink, top=self)

    ## @ingroup automatics_connection
    def __connect_module__(self, source: AsModule, sink):
        if isinstance(sink, AsWindowModule):
            for winter in sink.window_interfaces:
                self.__connect__(source, winter)
            self.chain.__connect__(source, sink, top=self)
        elif isinstance(sink, AsWindowInterface):
            for inter in source.interfaces:
                self.__connect__(inter, sink)
        elif isinstance(sink, (Interface, AsModule, Port)):
            self.chain.__connect__(source, sink, top=self)

    ## @ingroup automatics_connection
    def __connect_interface__(self, source: Interface, sink):
        if isinstance(sink, AsWindowInterface):
            # This connection (AsStream -> AsWindow)
            # will create a window buffer!
            # First, check if the interface is an as_stream!
            if source.type != "as_stream":
                LOG.info(
                    (
                        "Connection attempt with window interface ignored "
                        "- invalid interface type! Between '%s'"
                    ),
                    pipeline_connection_error_string(
                        self, source, sink, lambda inter: inter.type
                    ),
                )
                return None
            if source.direction == "in":
                LOG.info(
                    (
                        "Cannot connect as_stream of direction "
                        "'in' to window interface!"
                    )
                )
                return None
            # Next, check if the interfaces data type is ok
            if source.get_port("data").data_type != "std_logic_vector":
                raise AsConnectionError(
                    source,
                    (
                        "Invalid data type of as_stream interface for "
                        "connection to a window interface! Between {}"
                    ).format(
                        pipeline_connection_error_string(
                            self, source, sink, lambda inter: str(inter)
                        )
                    ),
                )
            # Now let's look at the data width.
            # First make sure that the data width does not contain any generics:
            # Attempt to resolve
            for port in ittls.chain(source.ports, sink.ports):
                resolve_generic(port)
            # Check
            if not all(
                (port.data_width.is_resolved() for port in source.ports)
            ):
                raise AsConnectionError(
                    source,
                    (
                        "Data width of stream interface '{}' of module '{}' "
                        "contains unresolved generics! Cannot connect to "
                        "window interface! In pipeline '{}'."
                    ).format(source, source.parent, self.name),
                )
            if not all((port.data_width.is_resolved() for port in sink.ports)):
                raise AsConnectionError(
                    source,
                    (
                        "Data width of window interface '{}' of module '{}' "
                        "contains unresolved generics! Cannot connect with "
                        "streaming interface! In pipeline '{}'."
                    ).format(sink, sink.parent, self.name),
                )
            # Check if the window interface already has a connection:
            if len(sink.incoming) > 0:
                LOG.warning(
                    (
                        "Window interface already has a connection to '%s'. "
                        "Ignoring connection attempt between %s"
                    ),
                    str(sink.incoming[0]),
                    pipeline_connection_error_string(
                        self, source, sink, lambda inter: str(inter)
                    ),
                )
                return None

            # If the connection is not "direct", crosses module group boundaries
            if source.parent.modlevel < sink.parent.modlevel:
                pipe_if = self._add_input_stream(source, sink.window_port)
                self.chain.__connect__(source, pipe_if, top=self.parent)
            else:
                # All seems well, connect!
                sink.incoming.append(source)
                source.outgoing.append(sink)
                sink.connected = True

        elif isinstance(sink, Interface):
            src_mod = get_parent_module(source)
            snk_mod = get_parent_module(sink)
            if src_mod.modlevel == snk_mod.modlevel + 1:
                self._add_output_stream(source, sink)

        elif isinstance(sink, AsWindowModule):
            src_mod = get_parent_module(source)
            if src_mod.modlevel + 1 == sink.modlevel:
                if sink.window_interfaces:
                    pipe_if = self._add_input_stream(
                        source, sink.window_interfaces[0].window_port
                    )
                    self.chain.__connect__(source, pipe_if, top=self.parent)

        elif isinstance(sink, (AsModule, Interface, Port)):
            self.chain.__connect__(source, sink, top=self)

    ## @ingroup automatics_connection
    def __connect_port__(self, source: Port, sink):
        if isinstance(sink, AsWindowInterface):
            if sink not in source.outgoing:
                source.outgoing.append(sink.window_port)
            sink.set_connected()
            sink.window_port.incoming = source
            sink.window_port.set_connected()
        elif isinstance(sink, Interface):
            if sink.type != "as_stream":
                # Delegate:
                self.chain.__connect__(source, sink, top=self)
                return None
            # TODO: connect output stream
            if isinstance(
                get_parent_module(source), (AsWindowModule, As2DWindowPipeline)
            ):
                if sink.parent.modlevel < get_parent_module(
                    source
                ).modlevel or (
                    sink.parent.modlevel == get_parent_module(source).modlevel
                    and isinstance(
                        get_parent_module(source), As2DWindowPipeline
                    )
                ):
                    self._add_output_stream(source, sink)
                    return None
                    # -> Else
            self.chain.__connect__(source, sink)
        elif isinstance(sink, AsWindowModule):
            for wif in sink.window_interfaces:
                self.__connect__(source, wif)
            self.chain.__connect__(source, sink)
        elif isinstance(sink, Port) and isinstance(
            get_parent_module(sink), AsWindowModule
        ):
            if (
                get_parent_module(source) is not self
                and get_parent_module(source).modlevel <= self.modlevel
            ):
                pipe_port = self._add_input_stream(source, sink)
                sink = pipe_port
            # For ports that are already in an input !stream!,
            # check if the connection already exists
            if sink.incoming is not source:
                self.chain.__connect__(source, sink, top=self)
        else:
            # Delegate
            self.chain.__connect__(source, sink, top=self)


## @}
