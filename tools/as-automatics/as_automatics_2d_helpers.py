# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_automatics_2d_helpers.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Module containing helper functions without a class association for the
2D Window Pipeline in Automatics.
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
# @file as_automatics_2d_helpers.py
# @ingroup automatics_2dwpl
# @ingroup automatics_helpers
# @author Philip Manke
# @brief Helper functions for the 2D Window Pipeline of ASTERICS.
# -----------------------------------------------------------------------------

from as_automatics_port import Port
from as_automatics_helpers import eval_vhdl_expr
from as_automatics_connection_helper import get_parent_module
from as_automatics_vhdl_static import (
    PROCESS_WITH_VARIABLES,
    LINE_ARRAY_VARIABLE_DECLARATION,
    LINE_ARRAY_TO_WINDOW_FUNCTION,
    LINE_ARRAY_TYPE_DECLARATION,
    LINE_SIGNAL_TO_LINE_ARRAY,
    RESET_WINDOW_SIGNAL,
    WINDOW_FROM_LINE_ARRAY,
)


##
# @addtogroup automatics_2dwpl
# @{


def get_delay(obj: object) -> int:
    """! @brief Returns objects strobe delay.
    @return None if the attribute doesn't exist."""
    return getattr(obj, "delay", None)


def set_delay(obj: object, delay: int):
    """! @brief Sets objects strobe delay.
    Creates the attribute if it doesn't exist."""
    if get_delay(obj) is None:
        setattr(obj, "delay", delay)
        try:
            setattr(obj.glue_signal, "delay", delay)
        except AttributeError:
            pass
    else:
        obj.delay = delay


def resolve_data_width(data_width: Port.DataWidth, generics: list) -> list:
    """! @brief Resolve data_width using a list of generics."""
    if data_width.is_resolved():
        return data_width

    gendict = {}
    for gen in generics:
        gendict[gen.code_name] = gen.get_value()

    spliton = data_width.sep
    value0 = eval_vhdl_expr(
        str(data_width.a).strip().upper(), "data width", gendict
    )
    value1 = eval_vhdl_expr(
        str(data_width.b).strip().upper(), "data width", gendict
    )
    return Port.DataWidth(a=value0, sep=spliton, b=value1)


def report_buffer_statistics(
    buffer_rows: list, minimum_bram_size: int, verbosity: int = 0
):
    """! @brief Prints buffer statistics to console.
    Calculates statistics for used flip-flops and BRAM resources by image
    buffers and prints to console.
    A summary (default) or a per-buffer report can be created using 'verbosity'.
    """
    count = len(buffer_rows)
    total_size = 0
    count_bram = 0
    count_reg = 0
    size_bram = 0
    size_reg = 0

    for buff in buffer_rows:
        buffsize = buff.get_size()
        total_size += buffsize
        if buffsize > minimum_bram_size:
            count_bram += 1
            window_size = buff.window_width * buff.get_bit_width()
            size_bram += buffsize - window_size
            size_reg += window_size
        else:
            count_reg += 1
            size_reg += buffsize
    print(
        (
            "\n"
            "###############################################\n"
            "Automatics 2D Window Pipeline Buffer Row Report\n"
            "###############################################\n"
            "\n"
            "Total number of buffers: {count}\n"
            "Total buffer size in bits: {size}\n"
            "Number of buffers implemented as BRAM: {count_bram}\n"
            "Number of buffers implemented as registers only: {count_reg}\n"
            "Total size of BRAM required in bits: {size_bram}\n"
            "Total size of registers required: {size_reg}\n"
            "\n"
        ).format(
            count=count,
            size=total_size,
            count_bram=count_bram,
            count_reg=count_reg,
            size_bram=size_bram,
            size_reg=size_reg,
        )
    )
    if verbosity > 0:
        count = 0
        for buff in buffer_rows:
            buffsize = buff.get_size()
            if buffsize <= minimum_bram_size:
                size_reg = buffsize
                size_bram = 0
            else:
                window_size = buff.window_width * buff.get_bit_width()
                size_bram = buffsize - window_size
                size_reg = window_size
            print(
                (
                    "-- {num} --\n"
                    "Buffer '{name}':\n"
                    "Input delay: {in_delay}\n"
                    "Output delay: {out_delay}\n"
                    "Buffer length: {length}\n"
                    "Bit width: {bit_width}\n"
                    "Window width: {window_width}\n"
                    "BRAM size in bits: {size_bram}\n"
                    "Register size in bits: {size_reg}\n"
                    "\n"
                ).format(
                    num=count,
                    name=buff.name,
                    in_delay=buff.input_delay,
                    out_delay=buff.output_delay,
                    length=buff.length,
                    bit_width=buff.get_bit_width(),
                    window_width=buff.window_width,
                    size_bram=size_bram,
                    size_reg=size_reg,
                )
            )
            count += 1


## @ingroup automatics_generate
def generate_window_assignments(window_signals: list, code_dict: dict):
    """! @brief Generate VHDL code to assign image rows to t_generic_window signals.
    Creates a process for use in a 2D Window Pipeline subsystem.
    Assigning t_generic_line signals to one or more t_generic_window signals."""
    process_body = []
    line_arrays = []
    input_line_signals = set()
    window_configs = set()

    # For all window ports
    for ws in window_signals:
        wp = ws.outgoing[0]
        winter = wp.parent
        line_arrays.append(
            LINE_ARRAY_VARIABLE_DECLARATION.format(
                window=ws.code_name,
                width=winter.window.x,
                height=winter.window.y,
                bits=ws.data_width.get_bit_width(),
            )
        )
        window_configs.add((winter.window.x, ws.data_width.get_bit_width()))
        # Add comment with the window signal name
        process_body.append("      -- Build window '{}'".format(ws.code_name))

        # 'incoming' stores the buffers that provide data for this window
        for row_idx in range(len(winter.incoming)):
            buff = winter.incoming[row_idx]

            # We need to scan all inputs
            for in_port, window_connection, to_ports in zip(
                buff.inputs,
                buff.is_window_signal,
                buff.to_window_ports,
            ):
                # Skip unrelated inputs (^= buffer slices)
                if (not window_connection) or ((wp, row_idx) not in to_ports):
                    continue
                line_signal = buff.line_signal.code_name
                input_line_signals.add(line_signal)

                # Fill assignment template
                process_body.append(
                    LINE_SIGNAL_TO_LINE_ARRAY.format(
                        row_idx=row_idx,
                        line_signal=line_signal,
                        start_bit_idx=in_port.start_index,
                        bit_width=in_port.bit_width,
                        width=winter.window.x,
                        window=ws.code_name,
                    )
                )
        process_body.append(
            WINDOW_FROM_LINE_ARRAY.format(
                window=ws.code_name,
                width=winter.window.x,
                bits=ws.data_width.get_bit_width(),
            )
        )
    sens = list(sorted(input_line_signals))
    code_dict["body"].append(
        PROCESS_WITH_VARIABLES.format(
            sens=", ".join(sens),
            variables="\n".join(line_arrays),
            in_process="\n".join(process_body),
        )
    )
    for width, bits in window_configs:
        code_dict["signals"].append(
            LINE_ARRAY_TYPE_DECLARATION.format(width=width, bits=bits)
        )
        code_dict["signals"].append(
            LINE_ARRAY_TO_WINDOW_FUNCTION.format(width=width, bits=bits)
        )
    code_dict["signals"].append("  ")


## @ingroup automatics_logging
def pipeline_connection_error_string(
    pipe, source, sink, detail_generator
) -> str:
    """! @brief Template for pipeline connection errors."""
    return (
        "'{}' of module '{}' and '{}' of module '{}' "
        "- in window pipeline module '{}'."
    ).format(
        detail_generator(source),
        get_parent_module(source),
        detail_generator(sink),
        get_parent_module(sink),
        pipe.name,
    )


## @}
