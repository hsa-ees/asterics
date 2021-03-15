# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_automatics_2d_pipeline_row.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Module containing the class AsPipelineRow for the 2D Window Pipeline of ASTERICS
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
# @file as_automatics_2d_pipeline_row.py
# @ingroup automatics_2dwpl
# @ingroup automatics_intrep
# @author Philip Manke
# @brief Helper class AsPipelineRow for the 2D Window Pipeline of ASTERICS.
# -----------------------------------------------------------------------------


from as_automatics_port import Port
from as_automatics_signal import GenericSignal
from as_automatics_exceptions import AsConnectionError, AsModuleError
from as_automatics_2d_helpers import get_delay, set_delay
from as_automatics_connection_helper import (
    get_parent_module,
    resolve_generic,
)
from as_automatics_helpers import foreach

import as_automatics_logging as as_log

LOG = as_log.get_log()

##
# @addtogroup automatics_2dwpl
# @{

## @ingroup automatics_intrep
class AsPipelineDataInfo:
    """! @brief Class storing information about an in-/ output of an
    as_automatics_2d_pipeline_row::AsPipelineRow."""

    def __init__(
        self,
        port: Port,
        start_index: int,
    ):
        self.port = port
        self.from_module = get_parent_module(port)
        self.delay = get_delay(port)
        self.bit_width = port.data_width.get_bit_width()
        self.start_index = start_index


## @ingroup automatics_intrep
class AsPipelineRow:
    """! @brief Class representing an image row buffer of the
    as_automatics_2d_pipeline::As2DWindowPipeline.
    The pipeline stores image data in buffers each holding one or more
    image rows storing the same number of pixels.
    Each buffer has a section stored in registers, accessible simultaneously and
    a BRAM part, where only the last pixel in the FIFO BRAM is readable.
    These buffers are described by this AsPipelineRow class.
    """

    def __init__(
        self, name: str, length: int, window_width: int, parent_pipeline
    ):
        """! @brief Constructor for AsPipelineRow.
        @param name:  Name of the AsLayer. Referenced in the Auto-Tag of AsWindowModules
        @param data_width: Width of the data transported in the layer as bits
        @param window_width: The width of the line signal and window port's window
        @param parent_pipeline: Reference to the associated As2DWindowPipeline object
        @return A new AsPipelineRow object.
        """
        self.inputs = []
        self.is_window_signal = []
        self.to_window_ports = []
        self.outputs = []
        self.bit_width_in = 0
        self.bit_width_out = 0
        self.input_delay = None
        self.output_delay = None
        self.in_signal = None
        self.out_signal = None
        self.line_signal = None

        self.name = name
        self.pipe = parent_pipeline
        self.window_width = window_width

        # Get pipeline row module:
        self.module = self.pipe.chain.library.get_module_instance(
            "as_pipeline_row", window_module=True
        )
        if self.module is None:
            LOG.error(
                "Could not find ASTERICS module 'as_pipeline_row' required to "
                "build a 2D Window Pipeline!"
                "For '{}'.".format(self.pipe.name)
            )

            raise AsModuleError("as_pipeline_row", "Module not found!")
        # Register and configure pipeline row module
        self.pipe.modules.append(self.module)
        self.module.chain = self.pipe.chain
        self.module.name = self.name
        self.module.assign_to(self.pipe)
        self.module.set_generic_value("WINDOW_WIDTH", window_width)
        self.module.set_generic_value(
            "MINIMUM_LENGTH_FOR_BRAM",
            self.pipe.get_generic("MINIMUM_BRAM_SIZE").get_value(),
        )
        self.set_buffer_length(length)

    def __repr__(self) -> str:
        return self.name

    def get_bit_width(self) -> int:
        return self.bit_width_in

    def set_buffer_length(self, length: int):
        self.length = length
        self.module.set_generic_value("LINE_WIDTH", length)
        if self.input_delay is not None:
            self.output_delay = self.input_delay + length

    def add_window_port_target(
        self, from_port: Port, to_window_port: Port, window_row_index: int
    ):
        for in_port in self.inputs:
            if in_port.port is from_port:
                index = self.inputs.index(in_port)
                self.to_window_ports[index].append(
                    (to_window_port, window_row_index)
                )
                to_window_port.parent.window.rows[window_row_index] = self

    def add_window_interface_row(
        self, window_in, row_index: int, input_port: Port = None
    ) -> GenericSignal:
        """! @brief Add a window interface row as a buffer target.
        Adds itself as the buffer row into the WindowDef of the window port,
        at row index 'row_index'. Generates an intermediate signal for data
        transport between the output of the buffer component and assigning
        the window signal, which is returned on success.
        @param window_in  The window interface to supply with data
        @param row_index  The row of the window interface to target
        @param input_port  The Port supplying the image data
        @return  intermediate signal of this buffer's delayed data output
        """
        try:
            wport = window_in.window_port
            window = window_in.window
        except AttributeError:
            raise AsConnectionError(
                window_in,
                "Invalid object passed to 'add_window_interface' for "
                "buffer '{}': {}!".format(self.name, window_in),
            )
        source = None
        if row_index == 0:
            if wport.glue_signal:
                source = wport.glue_signal
            elif wport.incoming.glue_signal:
                source = wport.incoming.glue_signal
            else:
                source = wport.incoming
        else:
            source = input_port
        # Register the source with this buffer
        if not self.add_input(
            source,
            is_window_signal=True,
            to_window_port=wport,
            window_row_idx=row_index,
        ):
            return None
        window.rows[row_index] = self
        signame = (
            window_in.parent.name
            + "_"
            + wport.code_name
            + "_row_"
            + str(row_index)
        )
        im_sig = self.pipe.define_signal(
            signame, data_type="std_logic_vector", data_width=wport.data_width
        )
        set_delay(im_sig, self.output_delay)
        self.add_output(im_sig)
        return im_sig

    def add_input(
        self,
        data_input: Port,
        is_window_signal: bool = False,
        to_window_port=None,
        window_row_idx: int = 0,
        check_delay: bool = True,
    ) -> bool:
        """! @brief Add a Port as an input for this pipeline buffer row.
        Extends this buffer by the port.
        @param data_input  The Port to add as an input of this buffer
        @param is_window_signal  Marks this part of the data buffer as a window signal
        @param to_window_port  The window port targeted by this part of the buffer
                               Must be set if is_window_signal is set to True
        @param window_row_idx  The row index this part of the buffer targets
                               Must be set if is_window_signal is set to True
        @param check_delay  Whether or not to make sure the input delay of the
                            Port added matches the other input Ports
        @return  True on success, else False
        """
        # Do we already have this data input?
        if data_input in (inp.port for inp in self.inputs):
            LOG.warning(
                "Port input '%s' already in '%s'!", str(data_input), self.name
            )
            return False
        # Does the data input have a delay value?
        if get_delay(data_input) is None:
            LOG.error(
                "Port '%s' added to '%s' without a data delay value!",
                str(data_input),
                self.name,
            )
            return False
        # If this is the first input, use it's delay as the input delay
        if self.input_delay is None:
            self.input_delay = get_delay(data_input)
            self.output_delay = self.input_delay + self.length
        elif check_delay and get_delay(data_input) != self.input_delay:
            LOG.error(
                "Port '%s' added to '%s' with differing input delays!",
                str(data_input),
                self.name,
            )
            return False
        # Create and append input management object
        new_input = AsPipelineDataInfo(data_input, self.bit_width_in)
        if new_input.bit_width is None:
            raise AsConnectionError(
                data_input,
                (
                    "Port added to buffer '{}' in '{}' "
                    "has unresolved data width [{}]!"
                ).format(self.name, self.pipe.name, data_input.data_width),
            )
        self.inputs.append(new_input)
        self.is_window_signal.append(is_window_signal)
        if isinstance(to_window_port, list):
            self.to_window_ports.append(to_window_port)
        else:
            self.to_window_ports.append([(to_window_port, window_row_idx)])

        # Update bit width and module generic
        self.bit_width_in += new_input.bit_width
        self.module.set_generic_value("DATA_WIDTH", self.bit_width_in)
        return True

    def add_output(self, data_output: Port, update_delay: bool = True) -> bool:
        """! @brief Add a data output Port to this buffer.
        The next unconnected output index is used for the connection.
        @param data_output  The Port to supply with data from this buffer
        @param update_delay  Whether or not to update the strobe delay of the Port
        @return  True on success, else False
        """
        if data_output in (out.port for out in self.outputs):
            LOG.warning(
                "Port output '%s' already in '%s'!", str(data_output), self.name
            )
            return False
        if data_output.data_width.get_bit_width() != self.inputs[-1].bit_width:
            LOG.error(
                (
                    "Bit width of data output '%s' added to '%s' does not "
                    "match corresponding data input '%s': %i <-> %i"
                ),
                str(data_output),
                self.name,
                str(self.inputs[-1].port),
                data_output.data_width.get_bit_width(),
                self.inputs[-1].bit_width,
            )
            return False
        new_output = AsPipelineDataInfo(data_output, self.bit_width_out)
        if new_output.bit_width is None:
            raise AsConnectionError(
                data_output,
                (
                    "Port added to buffer '{}' in '{}' "
                    "has unresolved data width [{}]!"
                ).format(self.name, self.pipe.name, data_output.data_width),
            )
        self.outputs.append(new_output)

        if update_delay:
            new_output.delay = self.output_delay
            set_delay(new_output.port, self.output_delay)
        self.bit_width_out += new_output.bit_width

    def remove_outputs(self):
        self.outputs.clear()
        self.bit_width_out = 0

    def get_size(self) -> int:
        return self.bit_width_in * self.length

    def build_inout_vectors(self) -> GenericSignal:
        # Get module ports
        mod_in_port = self.module.get_port("buff_in")
        mod_out_port = self.module.get_port("data_out")
        mod_line_port = self.module.get_port("line_out")

        foreach(self.module.get_full_port_list(), resolve_generic)

        # Create intermediate vector signals
        sig_name = self.name + "_data_"
        self.in_signal = self.pipe.define_signal(
            sig_name + "in",
            data_type="std_logic_vector",
            data_width=(self.bit_width_in - 1, "downto", 0),
        )
        self.out_signal = self.pipe.define_signal(
            sig_name + "out",
            data_type="std_logic_vector",
            data_width=(self.bit_width_in - 1, "downto", 0),
        )
        # Connect them to the buffers input and output
        self.pipe.chain.__connect__(self.in_signal, mod_in_port, top=self.pipe)
        self.pipe.chain.__connect__(
            mod_out_port, self.out_signal, top=self.pipe
        )
        # Define vector signal connections
        for source in self.inputs:
            self.in_signal.assign_to_this_vector(
                source.port, source.start_index
            )
        for target in self.outputs:
            self.out_signal.assign_from_this_vector(
                target.port, target.start_index
            )
        # Create line port signal
        self.line_signal = self.pipe.define_signal(
            self.name + "_line_data",
            data_type="t_generic_line",
            data_width=(self.bit_width_in - 1, "downto", 0),
        )
        setattr(
            self.line_signal,
            "line_width",
            Port.DataWidth(0, "to", self.window_width - 1),
        )
        # Connect to buffer module line port
        self.pipe.__connect__(self.line_signal, mod_line_port)
        return self.line_signal

    def merge(self, prow, merge_outputs: bool = True):
        """Merge AsPipelineRow 'prow' into this pipeline row."""
        for idx in range(len(prow.inputs)):
            window_ports = prow.to_window_ports[idx]
            for wp, row_idx in window_ports:
                if not wp:
                    continue
                winter = wp.parent
                winter.incoming.remove(prow)
                winter.incoming.insert(row_idx, self)
                winter.window.rows[row_idx] = self

            self.add_input(
                prow.inputs[idx].port,
                prow.is_window_signal[idx],
                prow.to_window_ports[idx],
                check_delay=False,
            )
        if merge_outputs:
            for out in prow.outputs:
                self.add_output(out.port, update_delay=False)


## @}
