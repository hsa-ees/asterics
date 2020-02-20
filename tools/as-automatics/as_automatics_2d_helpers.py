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
# @author Philip Manke
# @brief Helper functions for the 2D Window Pipeline of ASTERICS.
# -----------------------------------------------------------------------------

from as_automatics_window_module import PIPE_WINDOW_TYPE
from as_automatics_2d_infrastructure import WindowDef
from as_automatics_port import Port
from as_automatics_helpers import eval_vhdl_expr


def data_widths_to_window(columns: Port.DataWidth,
                          rows: Port.DataWidth) -> WindowDef:
    if columns.sep == "to":
        from_x = columns.a
        to_x = columns.b
    else:
        from_x = columns.b
        to_x = columns.a
    if rows.sep == "to":
        from_y = rows.a
        to_y = rows.b
    else:
        from_y = rows.b
        to_y = rows.a
    # Only return a window object, if the indices are resolved (no generics!)
    if any((not isinstance(idx, int) for idx in (from_x, to_x, from_y, to_y))):
        return None
    return WindowDef(from_x, to_x, from_y, to_y)


def parse_gwindow_type(width_str: str, generics: list) -> list:
    """Parse the generic_window custom VHDL data type."""
    gendict = {}
    for gen in generics:
        gendict[gen.code_name] = gen.get_value()

    out = []
    parens = width_str.lower().split(",")
    for par in parens:
        dt_pos = par.find(" downto ")
        to_pos = par.find(" to ")
        if dt_pos > -1:
            spliton = "downto"
        elif to_pos > -1:
            spliton = "to"
        else:
            continue

        values = par.split(spliton, 1)
        value0 = eval_vhdl_expr(values[0].strip().upper()
                                , "data width", gendict)
        value1 = eval_vhdl_expr(values[1].strip().upper()
                                , "data width", gendict)
        out.append(Port.DataWidth(a=value0, sep=spliton, b=value1))
    return out


# This is for generic_window (currently not usable with GHDL: 30.08.19):
# type pixel_line is array(natural range <>) of std_logic_vector;
# type generic_window is array(natural range <>) of pixel_line;
# generic_window(0 to 3)(0 to 3)(7 downto 0) <=>
# generic_window(0 to 3, 0 to 3, 7 downto 0)
"""
# Find enclosed data width definitions
parens = []
par_o = 0
idx = 0
while data_type[idx] != "(":
    idx += 1
pidx = idx
for char in data_type[idx:]:
    if char == "(":
        par_o += 1
    elif char == ")":
        par_o -= 1
        if par_o == 0:
            parens.append(data_type[pidx:idx + 1])
            pidx = idx + 1
    idx += 1

out = []
for par in parens:
    par = par[1:-1]  # Remove outer ()
    dt_pos = par.find(" downto ")
    to_pos = par.find(" to ")
    if dt_pos > -1:
        spliton = "downto"
    elif to_pos > -1:
        spliton = "to"
    else:
        continue

    values = par.split(spliton, 1)
    value0 = eval_vhdl_expr(values[0].strip().upper(), "data width")
    value1 = eval_vhdl_expr(values[1].strip().upper(), "data width")
    out.append(Port.DataWidth(a=value0, sep=spliton, b=value1))
return out
"""
