# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_automatics_cnn_helpers.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Collection of helper functions for CNN layers in ASTERICS systems.
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
# @file as_automatics_cnn_helpers.py
# @ingroup automatics_cnn
# @author Philip Manke
# @brief Collection of helper functions for CNN layers in ASTERICS systems.
# -----------------------------------------------------------------------------

from as_automatics_logging import get_log

LOG = get_log()


##
# @addtogroup automatics_cnn
# @{


def get_csa_adder_stages(count):
    stages = 1
    while count > 2:
        count = ((count // 3) * 2) + (count % 3)
        stages += 1
    return stages


def get_csa_adder_count(count, stage):
    for _ in range(stage - 1):
        count = ((count // 3) * 2) + (count % 3)
    return count // 3


def get_total_elements_for_filter(filterkernel):
    akk = 0
    for weight in filterkernel:
        akk += ones_lut[abs(weight)]
    return akk


def elements_for_csa_with_stages(stage_count):
    elements = 2
    for _ in range(stage_count - 1):
        elements *= 3
        elements -= elements % 3
        elements /= 2
    return int(elements)


def generate_adder_layout(max_stages, filter_weights):
    elem_count = get_total_elements_for_filter(filter_weights)
    elements_per_stage = [elem_count, elem_count // 4 + elem_count % 4]
    elements_per_adder = [4]
    adders_per_stage = [elem_count // 4]
    stage_count = 1
    while True:
        cur_elems = elements_per_stage[stage_count]
        if get_csa_adder_stages(cur_elems) <= max_stages:
            elements_per_adder.append(cur_elems)
            adders_per_stage.append(1)
            elements_per_stage.append(1)
        else:
            elements_per_adder.append(elements_for_csa_with_stages(max_stages))
            adders_per_stage.append(
                cur_elems // elements_per_adder[stage_count]
            )
            elements_per_stage.append(
                adders_per_stage[stage_count]
                + cur_elems % elements_per_adder[stage_count]
            )
        stage_count += 1
        if elements_per_stage[-1] == 1:
            break
    return (elements_per_stage, elements_per_adder, adders_per_stage)


def weights_to_string(weights: list, elements_per_filter: int) -> str:
    str_out = []
    for idx in range(0, len(weights), elements_per_filter):
        str_out.append(
            "({})".format(
                ", ".join(
                    [str(w) for w in weights[idx : idx + elements_per_filter]]
                )
            )
        )
    return "({})".format(", ".join(str_out))


def weights_to_string_for_serial_filter(
    weights: list, channel_count: int, filters_per_module: int
):
    to_vhdl_list = lambda l: "({})".format(", ".join([str(i) for i in l]))
    to_list_of_lists = lambda l: "({})".format(", ".join([i for i in l]))
    filters_str = []
    weights_per_filter = len(weights) // filters_per_module
    weights_per_channel = weights_per_filter // channel_count
    for filter_idx in range(0, len(weights), weights_per_filter):
        channels_str = []
        for channel_idx in range(
            filter_idx, filter_idx + weights_per_filter, weights_per_channel
        ):
            channels_str.append(
                to_vhdl_list(
                    weights[channel_idx : channel_idx + weights_per_channel]
                )
            )
        filters_str.append(to_list_of_lists(channels_str))

    return to_list_of_lists(filters_str)


def weights_to_integer_array(
    weights: list, kernelsize: int, channel_count: int
):
    elem_count = kernelsize ** 2
    filters = int((len(weights) / elem_count) / channel_count)
    w_per_filter = int(len(weights) / filters)
    outlist = []
    for filter_idx in range(0, filters):
        cur_weights = weights[
            w_per_filter * filter_idx : w_per_filter * (filter_idx + 1)
        ]
        outlist.append(cur_weights)
    return outlist


def calc_extended_quantized_bias(filter_kernel, bias):
    akk = bias
    for w in filter_kernel:
        akk += w * 128
    return akk


def reduce_add_sub(weights: list, max_ones: int) -> list:
    """Reduce the number of PoT factors required per weight up to 'max_ones'.
    Returns the modified 'weights'."""
    out = []
    count = 0
    for w in weights:
        ones = ones_lut[abs(w)]
        if ones > max_ones:
            count += 1
            pos = w
            neg = w
            while True:
                pos += 1
                neg -= 1
                if ones_lut[abs(pos)] <= max_ones:
                    out.append(pos)
                    break
                if ones_lut[abs(neg)] <= max_ones:
                    out.append(neg)
                    break
        else:
            out.append(w)
    LOG.info("Transformed {} weights!".format(count))
    return out


##
# @ brief Look-up table for the number of factors per weight value.
# Look-up table storing the number of powers-of-two (PoT) factors required
# to represent a given number.
# Index of the list is the number, value at that index the number of PoT factors
ones_lut = [
    0,
    1,
    1,
    2,
    1,
    2,
    2,
    2,
    1,
    2,
    2,
    3,
    2,
    3,
    2,
    2,
    1,
    2,
    2,
    3,
    2,
    3,
    3,
    3,
    2,
    3,
    3,
    3,
    2,
    3,
    2,
    2,
    1,
    2,
    2,
    3,
    2,
    3,
    3,
    3,
    2,
    3,
    3,
    4,
    3,
    4,
    3,
    3,
    2,
    3,
    3,
    4,
    3,
    4,
    3,
    3,
    2,
    3,
    3,
    3,
    2,
    3,
    2,
    2,
    1,
    2,
    2,
    3,
    2,
    3,
    3,
    3,
    2,
    3,
    3,
    4,
    3,
    4,
    3,
    3,
    2,
    3,
    3,
    4,
    3,
    4,
    4,
    4,
    3,
    4,
    4,
    4,
    3,
    4,
    3,
    3,
    2,
    3,
    3,
    4,
    3,
    4,
    4,
    4,
    3,
    4,
    4,
    4,
    3,
    4,
    3,
    3,
    2,
    3,
    3,
    4,
    3,
    4,
    3,
    3,
    2,
    3,
    3,
    3,
    2,
    3,
    2,
    2,
    1,
    2,
    2,
    3,
    2,
    3,
    3,
    3,
    2,
    3,
    3,
    4,
    3,
    4,
    3,
    3,
    2,
    3,
    3,
    4,
    3,
    4,
    4,
    4,
    3,
    4,
    4,
    4,
    3,
    4,
    3,
    3,
    2,
    3,
    3,
    4,
    3,
    4,
    4,
    4,
    3,
    4,
    4,
    5,
    4,
    5,
    4,
    4,
    3,
    4,
    4,
    5,
    4,
    5,
    4,
    4,
    3,
    4,
    4,
    4,
    3,
    4,
    3,
    3,
    2,
    3,
    3,
    4,
    3,
    4,
    4,
    4,
    3,
    4,
    4,
    5,
    4,
    5,
    4,
    4,
    3,
    4,
    4,
    5,
    4,
    5,
    4,
    4,
    3,
    4,
    4,
    4,
    3,
    4,
    3,
    3,
    2,
    3,
    3,
    4,
    3,
    4,
    4,
    4,
    3,
    4,
    4,
    4,
    3,
    4,
    3,
    3,
    2,
    3,
    3,
    4,
    3,
    4,
    3,
    3,
    2,
    3,
    3,
    3,
    2,
    3,
    2,
    2,
]

## @}
