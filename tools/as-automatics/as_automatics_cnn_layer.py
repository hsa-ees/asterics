# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_automatics_cnn_layer.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Class modelling a CNN layer in automatics for ASTERICS systems.
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
# @file as_automatics_cnn_layer.py
# @ingroup automatics_cnn
# @author Philip Manke
# @brief Class modelling a CNN layer in automatics for ASTERICS systems..
# -----------------------------------------------------------------------------

import os

import numpy as np

import as_automatics_cnn_helpers as cnn_help

from as_automatics_2d_pipeline import As2DWindowPipeline
from as_automatics_module import AsModule
from as_automatics_interface import Interface
from as_automatics_signal import GenericSignal
from as_automatics_port import Port
from as_automatics_templates import AsStream
from as_automatics_logging import get_log

LOG = get_log()

##
# @addtogroup automatics_cnn
# @{

## @ingroup automatics_intrep
class AsNNLayer(As2DWindowPipeline):
    """! @brief Class representing a CNN layer accelerator subsystem.
    This class is based on As2DWindowPipeline and internally implements a
    2D Window Pipeline subsystem.
    This class automatically adds and manages the data processing modules for
    the calculation of the convolution or pooling operations in the configured
    layer.
    @note The method parametrize_and_build MUST be called before connecting the layer.
    """

    OPERATION_TO_MODULE_DICT = {
        "CONV2D": "as_cnn_serial_convolution",
        "CONV2D_LARGE": "as_cnn_serial_convolution_one_summand",
        "POOL": "as_cnn_pooling_filter",
    }

    OPERATION_TO_FUNCTION_DICT = {
        "CONV2D": ("none", "relu"),
        "CONV2D_LARGE": ("none", "relu"),
        "POOL": ("none", "max"),
    }

    OPERATIONS_REQUIREING_VALUES = ("CONV2D", "CONV2D_LARGE")

    ADDITIONAL_VHDL_LIBRARIES = ("as_cnn_helpers",)

    USE_CONV2D_LARGE_THRESHOLD = 3 * 3 * 16

    def __init__(self, columns, rows, name, chain):
        super().__init__(columns, rows, name, chain)

        self.operation = "CONV2D"
        self.input_bit_width = 8
        self.output_bit_width = 8
        self.kernel_size = 3
        self.input_channel_count = 1
        self.filter_count = 1
        self.strides = 1
        self.activation_function = "none"
        self.weights_file = ""
        self.biases_file = ""
        self.quant_mults_file = ""
        self.filters_per_module = 1
        self.quant_offset = -128
        self.weight_accuracy = 8
        self.filter_count = 1
        self.filter_module_entity = "as_cnn_serial_convolution"
        self.weight_values = None
        self.bias_values = None
        self.quant_mult_values = None
        self.weights_per_filter = 9
        self.filter_module_count = 1
        self.filter_modules = []
        self.result_interface = None

    ## @ingroup automatics_cds
    def parametrize_and_build(
        self,
        operation: str = "CONV2D",
        input_bit_width: int = 8,
        output_bit_width: int = 8,
        kernel_size: int = 3,
        input_channel_count: int = 3,
        filter_count: int = 1,
        strides: int = 1,
        activation_function: str = "none",
        weight_values=None,
        bias_values=None,
        quantization_factors=None,
        weights_npy_file: str = "",
        biases_npy_file: str = "",
        quantization_factors_npy_file: str = "",
        filters_per_module: int = 1,
        quantization_offset_value: int = -128,
        weight_accuracy: int = 4,
        *,
        build_immediatly: bool = True,
        force_set_operation: bool = False
    ):
        """! @brief Configure this CNN layer accelerator module.
        Define the trainable parameters, quantization values
        and configuration parameters for this layer.
        @note This method must be used BEFORE the layer is connected!
        @param operation:
            Operation this layer should implement.
            Supported: ["CONV2D", "CONV2D_LARGE", "POOL"]
            Default: "CONV2D"
        @param input_bit_width:
            Bit width of the data to process.
            Valid values: [1 .. n]; Default is [8]
        @param output_bit_width:
            Bit width of the output of a single filter module.
            Total output width is determined by output_bit_width * filter_count
            Valid values: [1 .. n]; Default is [8]
        @param kernel_size:
            Size of the quadratic convolution kernel.
            Informs the number of required weight values per kernel.
            Valid values: >= 3 ; Must be odd numbers; Default is [3]
        @param input_channel_count:
            Number of input channels.
            A seperate set of kernel values is expected per input channel.
            Each filter performs a multi-channel convolution over all input
            channels and outputs the accumulated and quantized result.
            Valid values: [1 .. n]; integers; Default is [1]
        @param filter_count:
            The number of filters that are to be implemented.
            Default is [1]
        @param strides:
            Reduces the size of the output image.
            1 = no reduction, 2 = keep every second column and row,
            3 = keep every third column and row, ...
            Default is [1]
        @param activation_function:
            Define the activation function of the filter modules.
            Valid values depend on the configured operation:
            For "CONV2D": ["relu", "none"]; Default is "none"
            For "POOL": ["max", "none"]; Default is "none"
        @param weight_values:
            Python list or Numpy array containing the weight values to use.
            The weights must be 8 bit signed integers.
            The values are exptected to be in the following order: 'NHWC'
            [output channels/filters, value rows, value columns, input channels]
            Can also be provided via a numpy file using 'weights_npy_file'.
        @param bias_values:
            Python list or Numpy array containing the bias values to use.
            The biases must be 32 bit signed integers.
            The values are expected in the order of the output channels.
            Can also be provided via a numpy file using 'biases_npy_file'.
        @param quantization_factors:
            Python list or Numpy array containing the factors to use.
            The values must be 32 bit floating point numbers.
            The values are expected in the same order as the biases.
            These values are used to scale the filter responses back to int8.
            Can also be provided via a numpy file using
            'quantization_factors_npy_file'.
        @param weights_npy_file:
            Path and file name of the numpy file containing the weight values.
            See 'weight_values' for more information.
        @param biases_npy_file:
            Path and file name of the numpy file containing the bias values.
            See 'bias_values' for more information.
        @param quantization_factors_npy_file:
            Path and file name of the numpy file containing the quantiation factors.
            See 'quantization_factors' for more information.
        @param filters_per_module:
            Number of filters to implement within a serial convolution module.
            If = 1: Implement all filters in parallel: Uses most amount of resources
                    with greatest processing speed. Note that this is only possible
                    for !very! small networks
            If > 1: Implement multiple filters per module in serial processing:
                    Lowers resource usage and linearly reduces processing speed.
            Default is [1]: fully parallel operation
        @param quantization_offset_value:
            8 bit integer value applied to the outputs of this layer.
            Used by tensorflow lite to achieve an offset number representation.
            Default is [-128]
        @param weight_accuracy:
            Allows reduction of weight value accuracy to reduce FPGA resource
            usage. Weight values are transformed into factors of 2^n and
            implemented in hardware as fixed mathematical bit shifts.
            By reducing the number of factors allowed per weight, hardware
            resources can be saved.
            Valid values are [1 .. 4].
            Default is [4] = full accuracy.
        """

        self.operation = operation
        self.input_bit_width = input_bit_width
        self.output_bit_width = output_bit_width
        self.kernel_size = kernel_size
        self.input_channel_count = input_channel_count
        self.filter_count = filter_count
        self.strides = strides
        self.activation_function = activation_function
        self.weights_file = weights_npy_file
        self.biases_file = biases_npy_file
        self.quant_mults_file = quantization_factors_npy_file
        self.filters_per_module = filters_per_module
        self.quant_offset = quantization_offset_value
        self.weight_accuracy = weight_accuracy
        self.weights_per_filter = self.input_channel_count * (
            self.kernel_size ** 2
        )
        self.weight_values = weight_values
        self.bias_values = bias_values
        self.quant_mult_values = quantization_factors

        if not force_set_operation:
            if (
                self.weights_per_filter > self.USE_CONV2D_LARGE_THRESHOLD
                and self.operation == "CONV2D"
            ):
                self.operation = "CONV2D_LARGE"
                LOG.info(
                    (
                        "Weight values per kernel over threshold %i > %i !\n"
                        "Switching to CONV2D implementation optimized for "
                        "larger filter kernels."
                    ),
                    self.weights_per_filter,
                    self.USE_CONV2D_LARGE_THRESHOLD,
                )

        self.module_config_dicts = {
            "as_cnn_serial_convolution": {
                "DIN_WIDTH": self.input_bit_width,
                "DOUT_WIDTH": self.output_bit_width,
                "CHANNEL_COUNT": self.input_channel_count,
                "KERNEL_SIZE": self.kernel_size,
                "ACTIVATION_FUNCTION": '"' + self.activation_function + '"',
                "FILTER_COUNT": self.filters_per_module,
                "QUANTIZATION_OFFSET": self.quant_offset,
            },
            "as_cnn_serial_convolution_one_summand": {
                "DIN_WIDTH": self.input_bit_width,
                "DOUT_WIDTH": self.output_bit_width,
                "CHANNEL_COUNT": self.input_channel_count,
                "KERNEL_SIZE": self.kernel_size,
                "ACTIVATION_FUNCTION": '"' + self.activation_function + '"',
                "FILTER_COUNT": self.filters_per_module,
                "QUANTIZATION_OFFSET": self.quant_offset,
            },
            "as_cnn_pooling_filter": {
                "DATA_WIDTH": self.input_bit_width,
                "CHANNEL_COUNT": self.input_channel_count,
                "POOLING_METHOD": '"' + self.activation_function + '"',
            },
        }
        if self.operation == "POOL":
            self.output_bit_width = (
                self.input_bit_width * self.input_channel_count
            )

        try:
            self.filter_module_entity = self.OPERATION_TO_MODULE_DICT[
                self.operation
            ]
        except KeyError:
            raise ValueError(
                (
                    "AsNNLayer '{}': Operation '{}' not implemented! Aborted."
                ).format(self.name, self.operation)
            )

        if (
            self.activation_function
            not in self.OPERATION_TO_FUNCTION_DICT[self.operation]
        ):
            raise ValueError(
                (
                    "AsNNLayer '{}': Activation function '{}' not implemented "
                    "for operation '{}'! Aborted."
                ).format(self.name, self.activation_function, self.operation)
            )

        self.vhdl_libraries.extend(self.ADDITIONAL_VHDL_LIBRARIES)
        self.set_generic_value("MINIMUM_BRAM_SIZE", 16)
        self.pipe_manager.set_generic_value("STRIDE_X", self.strides)
        self.pipe_manager.set_generic_value("STRIDE_Y", self.strides)

        if operation in self.OPERATIONS_REQUIREING_VALUES:
            self._aquire_values()
        if build_immediatly:
            self._build_layer()

    ## @ingroup automatics_cds
    def connect(
        self,
        source=None,
        sink=None,
        *,
        no_delay: bool = False,
        no_stall: bool = False
    ):
        """! @brief Add a connection from this layer module as a data source."""
        if sink is None:
            sink = source
            source = self
        if source is None and sink is not None:
            source = self

        if source is self:
            if isinstance(sink, AsNNLayer):
                sink.connect(source=self.result_interface, sink=sink)
            else:
                super().connect(
                    self.result_interface,
                    sink,
                    no_delay=no_delay,
                    no_stall=no_stall,
                )
        elif sink is self:
            if isinstance(source, AsNNLayer):
                source.connect(self)
            elif isinstance(source, AsModule) or isinstance(source, Interface):
                for fm in self.filter_modules:
                    super().connect(
                        source, fm, no_delay=no_delay, no_stall=no_stall
                    )
            else:
                super().connect(source, self)
        else:
            super().connect(source, sink, no_delay=no_delay, no_stall=no_stall)

    def _aquire_values(self):
        values = []
        # Read and verify contents of numpy files
        for filename, direct_values in zip(
            (
                self.weights_file,
                self.biases_file,
                self.quant_mults_file,
            ),
            (self.weight_values, self.bias_values, self.quant_mult_values),
        ):
            # If the values are directly provided, skip reading the file
            if direct_values is not None:
                values.append(None)
                continue
            filename = os.path.realpath(filename)
            if not os.path.isfile(filename):
                raise NameError("File '{}' not found!".format(filename))
            values.append(np.array(np.load(filename)))

        if values[0] is not None:
            self.weight_values = values[0]
        if values[1] is not None:
            self.bias_values = values[1]
        if values[2] is not None:
            self.quant_mult_values = values[2]

        # Make sure all values are stored in numpy arrays
        self.weight_values = np.array(self.weight_values)
        self.bias_values = np.array(self.bias_values)
        self.quant_mult_values = np.array(self.quant_mult_values)

        # Verify and prepare weight values
        expected_weight_count = (
            self.filter_count
            * self.input_channel_count
            * (self.kernel_size ** 2)
        )
        if self.weight_values.size != expected_weight_count:
            raise ValueError(
                (
                    "Number of weight values does not match required "
                    "number of weights for '{}'! Need {}, got {}"
                ).format(
                    self.name, expected_weight_count, len(self.weight_values)
                )
            )

        filter_modules_required = expected_weight_count / (
            self.filters_per_module * self.weights_per_filter
        )
        if not filter_modules_required.is_integer():
            raise ValueError(
                (
                    "Cannot evenly distribute {} filters using {} filters per "
                    "filter module! Aborted."
                ).format(self.filter_count, self.filters_per_module)
            )
        self.filter_module_count = int(filter_modules_required)

        if self.weight_values.dtype != np.int8:
            LOG.warning(
                (
                    "AsNNLayer: Numpy weight values in file '%s' are "
                    "stored as data type '%s' instead of int8. "
                    "This might cause problems!"
                ),
                self.weights_file,
                str(self.weight_values.dtype),
            )
            self.weight_values = np.array(self.weight_values, dtype=np.int8)

        # Transform the weight values into the order expected by the HW:

        # Shape as expected on input
        weights_shape = (
            self.filter_count,
            self.kernel_size,
            self.kernel_size,
            self.input_channel_count,
        )
        self.weight_values = self.weight_values.reshape(weights_shape)
        # Move input channel axis from position 3 to position 1
        self.weight_values = np.moveaxis(
            self.weight_values, (3, 2, 1, 0), (1, 2, 3, 0)
        )
        # Swap kernel rows and kernel column axes
        self.weight_values = np.moveaxis(
            self.weight_values, (3, 2, 1, 0), (2, 3, 1, 0)
        )
        # Mirror the order of the kernels on the horizontal and vertical axes
        # In HW the image provided mirrored in this way to the filter modules
        self.weight_values = np.flip(self.weight_values, axis=(2, 3))

        # Reshape the weight values and store them as a Python list
        self.weight_values = self.weight_values.reshape((expected_weight_count))
        self.weight_values = list(self.weight_values)

        # If configured, reduce weight accuracy to save hardware resources
        if self.weight_accuracy < 8:
            LOG.info(
                "Reducing weight accuracy to at most %i factors per weight.",
                self.weight_accuracy,
            )
            self.weight_values = cnn_help.reduce_add_sub(
                self.weight_values, self.weight_accuracy
            )

        # Verify and prepare bias values
        if self.bias_values.size != self.filter_count:
            raise ValueError(
                (
                    "Number of bias values does not match the filter number in "
                    "'{}'! Need {}, got {}"
                ).format(self.name, self.filter_count, len(self.bias_values))
            )
        if self.bias_values.dtype != np.int32:
            LOG.warning(
                (
                    "AsNNLayer: Numpy bias values in file '%s' are "
                    "stored as data type '%s' instead of int32. "
                    "This might cause problems!"
                ),
                self.biases_file,
                str(self.bias_values.dtype),
            )
            self.bias_values = np.array(self.bias_values, dtype=np.int32)
        self.bias_values = self.bias_values.reshape((self.filter_count,))

        # Verify and prepare quantization values
        if len(self.quant_mult_values) != self.filter_count:
            raise ValueError(
                (
                    "Number of quantization values does not match the filter "
                    "number in '{}'! Need {}, got {}"
                ).format(
                    self.name, self.filter_count, len(self.quant_mult_values)
                )
            )
        if self.quant_mult_values.dtype not in (np.float32, np.float64):
            LOG.warning(
                (
                    "AsNNLayer: Numpy bias values in file '%s' are "
                    "stored as data type '%s' instead of float32. "
                    "This might cause problems!"
                ),
                self.quant_mults_file,
                str(self.quant_mult_values.dtype),
            )
            self.quant_mult_values = np.array(
                self.quant_mult_values, dtype=np.float32
            )
        self.quant_mult_values = self.quant_mult_values.reshape(
            (self.filter_count,)
        )

    def _build_layer(self):

        config_dict = self.module_config_dicts[self.filter_module_entity]

        # Add and configure filter modules:
        for idx in range(self.filter_module_count):

            modulename = self.name + "_module_" + str(idx)
            filter_module = self.add_module(
                self.filter_module_entity, modulename
            )
            # Configure the filter module
            for param, value in config_dict.items():
                filter_module.set_generic_value(param, value)

            # Select values for this filter module
            if self.operation in self.OPERATIONS_REQUIREING_VALUES:
                lower_bound = idx * self.filters_per_module
                upper_bound = (idx + 1) * self.filters_per_module
                weights = self.weight_values[
                    lower_bound
                    * self.weights_per_filter : upper_bound
                    * self.weights_per_filter
                ]
                biases = self.bias_values[lower_bound:upper_bound]
                quant_mults = self.quant_mult_values[lower_bound:upper_bound]
                filter_module.assign_trained_values(
                    weights, biases, quant_mults
                )

            self.filter_modules.append(filter_module)

        total_output_width = self.output_bit_width * self.filter_count
        data_out_inter = Interface(
            AsStream.INTERFACE_TYPE_NAME, AsStream(), default_name="out"
        )
        data_out_inter.direction = "out"

        data_out_port = Port(
            "data",
            "results_data_out",
            direction="out",
            data_type="std_logic_vector",
            data_width=Port.DataWidth(total_output_width - 1, "downto", 0),
        )
        strobe_out_port = Port("strobe", "results_strobe_out", direction="out")
        stall_out_port = Port("stall", "results_stall_out")

        data_out_inter.add_port(data_out_port)
        data_out_inter.add_port(strobe_out_port)
        data_out_inter.add_port(stall_out_port)

        strobe_signal_value = "pipeline_strobe_out_combined and {}".format(
            self.outgoing_strobes_valid_signal.code_name
        )
        strobe_out_inter_sig = self.define_signal(
            "results_strobe_out_int", fixed_value=strobe_signal_value
        )

        strobe_out_port.set_glue_signal(strobe_out_inter_sig)
        strobe_out_port.incoming = strobe_out_inter_sig
        strobe_out_inter_sig.outgoing.append(strobe_out_port)

        stall_out_sig = self.define_signal("results_stall_out_int")
        stall_out_port.outgoing.append(stall_out_sig)
        stall_out_sig.incoming.append(stall_out_port)

        self.pipe_manager.get_port("output_stall_in").connect(stall_out_sig)

        self.flush_in_stall = stall_out_sig

        self.result_interface = data_out_inter
        self.result_interface.assign_to(self)
        self.add_interface(self.result_interface)

    ## @ingroup automatics_connection
    def auto_connect(self):
        super().auto_connect()

        self.pipe_manager.get_port("result_data_in").clear_connections()
        self.pipe_manager.get_port("result_data_in").set_value(
            "(others => '0')"
        )

        self.pipe_manager.get_port("output_data_out").clear_connections()
        self.pipe_manager.get_port("output_data_out").set_value("open")

        data_out_port = self.result_interface.get_port("data")
        data_out_sig = self.define_signal(
            "result_data_out_signal",
            data_out_port.data_type,
            data_out_port.data_width,
        )
        for idx, mod in enumerate(self.filter_modules):
            upper = (
                ((self.filter_module_count - 1) - idx)
                * self.output_bit_width
                * self.filters_per_module
            )
            data_out_sig.assign_to_this_vector(mod.get_port("data_out"), upper)
        data_out_sig.connect(data_out_port)
        self.__connect__(
            self.pipe_manager.get_port("input_stall_out"),
            self.result_interface.get_port("stall"),
        )


## @}
