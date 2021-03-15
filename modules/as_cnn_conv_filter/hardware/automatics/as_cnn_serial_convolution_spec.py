# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_cnn_serial_convolution_filter_spec.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Python module used by as_automatics used to build the generators internal model
of the ASTERICS hardware module as_cnn_serial_convolution_filter.
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
# @file as_cnn_serial_convolution_filter_spec.py
# @author Philip Manke
# @brief Specifics for as_cnn_serial_convolution_filter used by as_automatics
# -----------------------------------------------------------------------------
from ast import literal_eval

from as_automatics_2d_window_module import AsWindowModule
from as_automatics_port import Port
from as_automatics_constant import Constant
from as_automatics_cnn_helpers import (
    weights_to_string_for_serial_filter,
    calc_extended_quantized_bias,
)


def get_module_instance(module_dir: str) -> AsWindowModule:

    module = AsWindowModule()
    toplevel_file = "hardware/hdl/vhdl/as_cnn_serial_convolution.vhd"
    module.files = [
        "hardware/hdl/vhdl/as_wallace_adder_tree_generic.vhd",
        "hardware/hdl/vhdl/as_weighted_summand_generator.vhd",
        "hardware/hdl/vhdl/as_cnn_quantizer.vhd",
        "hardware/hdl/vhdl/as_carry_safe_adder.vhd",
        "hardware/hdl/vhdl/as_carry_safe_operator.vhd",
    ]
    module.dependencies = ["as_cnn_helpers", "as_generic_filter", "helpers"]
    module.processing_delay = 11

    module.show_in_browser = True
    module.dev_status = AsWindowModule.DevStatus.BETA
    module.module_type = AsWindowModule.ModuleTypes.HARDWARE
    module.module_category = "AI Accelerator Window Filter"

    # as_automatics now automatically parses the toplevel file and discovers
    # ports, generics, existing interfaces and register interfaces
    module.discover_module(module_dir + "/" + toplevel_file)

    def assign_trained_values(
        self, weights: list, biases: list, quant_mults: list
    ):
        filter_count = self.get_generic("FILTER_COUNT").get_value()
        kernel_size = self.get_generic("KERNEL_SIZE").get_value()
        # Depth of pipeline in module: 4 + (filter_count - 1)
        self.processing_delay += filter_count - 1

        # Generate kernel weight value string
        channel_count = self.get_generic("CHANNEL_COUNT").get_value()
        kernel_str = weights_to_string_for_serial_filter(
            weights, channel_count, filter_count
        )

        # Calculate quantization BIAS extension from weights
        weights_per_filter = len(weights) // filter_count
        biases = tuple(biases)
        biases_new = []
        for f_idx in range(filter_count):
            biases_new.append(
                calc_extended_quantized_bias(
                    weights[
                        weights_per_filter
                        * f_idx : weights_per_filter
                        * (f_idx + 1)
                    ],
                    biases[f_idx],
                )
            )

        # Convert values to strings
        if filter_count == 1:
            kernel_str = "(0 => " + kernel_str[1:]
            qmult_str = "(0 => {})".format(quant_mults[0])
            biases_str = "(0 => {})".format(biases_new[0])
        else:
            qmult_str = str(tuple(quant_mults))
            biases_str = str(tuple(biases_new))

        kernel_const_name = self.name + "_kernel_values"
        biases_const_name = self.name + "_bias_values"
        quant_mults_const_name = self.name + "_quantization_factors"

        # Create constants for each value type
        kernel_value_const = Constant(
            kernel_const_name,
            kernel_const_name,
            "t_generic_filter_array",
            kernel_str,
            "(0 to {filter_count}, 0 to {channel_count}, 0 to {kernel_values})".format(
                filter_count=filter_count - 1,
                channel_count=channel_count - 1,
                kernel_values=(kernel_size ** 2) - 1,
            ),
        )
        biases_value_const = Constant(
            biases_const_name,
            biases_const_name,
            "t_integer_array",
            biases_str,
            Port.DataWidth(0, "to", filter_count - 1),
        )
        quant_mult_const = Constant(
            quant_mults_const_name,
            quant_mults_const_name,
            "t_real_array",
            qmult_str,
            Port.DataWidth(0, "to", filter_count - 1),
        )
        self.parent.add_constant(kernel_value_const)
        self.parent.add_constant(biases_value_const)
        self.parent.add_constant(quant_mult_const)

        # Assign constants to the generics
        self.set_generic_value("KERNEL_VALUES", kernel_const_name)
        self.set_generic_value("BIAS_VALUES", biases_const_name)
        self.set_generic_value(
            "QUANTIZATION_MULTIPLIERS", quant_mults_const_name
        )

    module.assign_trained_values = assign_trained_values.__get__(module)

    return module
