# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_automatics_helpers.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Implements some helper functions used throughout as_automatics.
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
# @file as_automatics_helpers.py
# @ingroup automatics_helpers
# @author Philip Manke
# @brief Implements some helper functions used throughout as_automatics.
# -----------------------------------------------------------------------------

import os

from typing import Sequence

from as_automatics_vhdl_static import REGMGR_REGISTER_CONFIG_NAMES

import as_automatics_logging as as_log

LOG = as_log.get_log()

__eval_env__ = {
    "locals": None,
    "globals": None,
    "__name__": None,
    "__file__": None,
    "__builtins__": None,
}


##
# @addtogroup automatics_helpers
# @{


def foreach(iterable, func):
    for item in iterable:
        func(item)


def get_foreach(iterable, func) -> list:
    return list(map(func, iterable))


## @ingroup automatics_analyze
def get_prefix_suffix(
    port_name: str, code_name: str, ignored_keywords: Sequence[str]
) -> [str, str]:
    """! @brief Extract the prefix and suffix from a code name of a VHDL port.
    removes the 'static' port name and filters out the
    'ignored_keywords'. Assumes that the name fragments of the code name
    are delimited with '_'."""
    # Remove the port name
    try:
        prefix, suffix = code_name.split(port_name, maxsplit=1)
    except ValueError:
        temp = code_name.split(port_name, maxsplit=1)
        namepos = code_name.find(port_name)
        if namepos > 0:
            prefix = temp[0]
            suffix = ""
        else:
            prefix = ""
            suffix = temp[0]

    # Remove excess '_' and split the rest of the name
    prefix_list = prefix.strip("_").split("_")
    suffix_list = suffix.strip("_").split("_")
    if suffix_list:
        suffix_list.reverse()
    prefix = suffix = ""

    # Filter out ignored keywords and rebuild the prefix and suffix
    for string in prefix_list:
        if string not in ignored_keywords and string != "":
            prefix = prefix + string + "_"
    for string in suffix_list:
        if string not in ignored_keywords and string != "":
            suffix = "_" + string + suffix

    return [prefix, suffix]


def is_data_width_compatible(dw_a, dw_b) -> bool:
    """! @brief Quick check whether the data widths represent the same width."""
    if dw_a.sep is None:
        if dw_b.sep is None:
            return True
        if dw_b.a == dw_b.b:
            return True
        return False
    if dw_a.sep != dw_b.sep:
        if dw_a.a == dw_b.b and dw_a.b == dw_b.a:
            return True
        return False
    if dw_a.a == dw_b.a and dw_a.b == dw_b.b:
        return True
    return False


def __eval_data_width__(data_width, generics, port) -> tuple:
    # String for reporting/logging
    origin = "data width of {}".format(port.code_name)
    # Evaluate low and high boundaries separately
    if isinstance(data_width.a, str):
        a = eval_vhdl_expr(data_width.a, origin, generics)
    else:
        a = data_width.a
    if isinstance(data_width.b, str):
        b = eval_vhdl_expr(str(data_width.b), origin, generics)
    else:
        b = data_width.b
    # Assemble and return new, resolved data width
    return port.DataWidth(a=a, sep=data_width.sep, b=b)


def eval_vhdl_expr(to_eval: str, string_origin: str, variable_dict: dict = {}):
    """! @brief Evaluate an expression using Python's eval function.
    eval is used in a stripped down version, removing most of Python's
    built-in functions (we only want to resolve mathematic expressions)."""
    try:
        ret = eval(to_eval, __eval_env__, variable_dict)
        return (
            int(ret)
            if (isinstance(ret, int) or isinstance(ret, float))
            else str(ret)
        )
    except TypeError as err:
        LOG.debug(
            ("Couldn't parse %s for input '%s'. Got " "TypeError: '%s'"),
            string_origin,
            to_eval,
            str(err),
        )
        return to_eval
    except SyntaxError as err:
        LOG.debug(
            ("Couldn't parse %s for input '%s'. Got " "SyntaxError: '%s'"),
            string_origin,
            to_eval,
            str(err),
        )
        return to_eval


## @ingroup automatics_analyze
def extract_generics(data_width) -> Sequence[str]:
    """! @brief Extract generic names from the data width tuple or a string."""
    if isinstance(data_width, str):
        temp = data_width.split("downto")
        dwstr = []
        for tstr in temp:
            dwstr.extend(tstr.split("to"))
        dwstr = "".join(dwstr)
    else:
        if not data_width.sep:
            return ""
        dwstr = "{}.{}".format(data_width.a, data_width.b)

    to_replace = " -+*/^()<>,"
    for repl in to_replace:
        dwstr = dwstr.replace(repl, ".")
    return list(
        filter(lambda x: bool(x) and not x.isnumeric(), dwstr.split("."))
    )


## @ingroup automatics_generate
def get_printable_datatype(port) -> str:
    """! @brief Formats the data width and type of the passed 'port' object
    into a printable string."""
    if isinstance(port.data_width, str):
        return "" + port.data_type + port.data_width
    if port.data_width.sep is None:
        return port.data_type
    try:
        ldw = port.line_width
        return "{}({}, {})".format(
            port.data_type,
            str(ldw).strip("()"),
            str(port.data_width).strip("()"),
        )
    except AttributeError:
        pass
    try:
        window = port.window_config
        if window is not None:
            return "{}({}, {}, {})".format(
                port.data_type,
                str(window[0]).strip("()"),
                str(window[1]).strip("()"),
                str(port.data_width).strip("()"),
            )
    except AttributeError:
        pass
    return "{}{}".format(port.data_type, port.data_width)


def append_to_path(path: str, to_append: str, add_trailing_slash: bool = True):
    """! @brief Take two path fragments and merge them.
    This function makes sure that each directory is separated by a '/'
    and returns the path with a '/' at the end
    unless 'add_slash' is set to False."""
    # Merge to one string
    string = path + "/" + to_append + "/"
    # Split it and filter out empty strings resulting from subsequent "/"es
    strsplit = [s for s in string.split("/") if s != ""]
    # Join the path separating each string by a single "/"
    out = "/".join(strsplit) + ("/" if add_trailing_slash else "")
    if string[0] == "/":  # Add a leading "/" if the initial string had one
        return "/" + out
    return out


def get_software_drivers_from_dir(path: str) -> list:
    """! @brief Return a list of all software files (ending with '.c' or '.h') in 'path'.
    Returns the full path for every file."""
    out = []
    if not os.path.exists(path):
        return out
    for item in os.listdir(path):
        if item.endswith(".h") or item.endswith(".c"):
            out.append(
                os.path.realpath(
                    append_to_path(path, item, add_trailing_slash=False)
                )
            )
    return out


def minimize_name(name: str, exclude: list = None):
    if not exclude:
        exclude = []
    split = name.lower().split("_")
    split.reverse()
    result = []
    for fragment in split:
        if fragment not in result and not fragment in exclude:
            result.append(fragment)
    result.reverse()
    return "_".join(result)


def get_source_module(inter) -> object:
    """! @brief Returns the module that is the source of the interface 'inter'."""
    con = inter
    while True:
        try:
            if con.direction == "in":
                con_new = con.outgoing[0]
            else:
                con_new = con.incoming[0]
        except (AttributeError, IndexError):
            break
        con = con_new
    return getattr(con, "parent", None)


## @ingroup automatics_generate
def generate_register_config_value_string(register_config_list: list) -> str:
    if len(register_config_list) == 0:
        return "()"
    elif len(register_config_list) == 1:
        return "(0 => " + register_config_list[0] + ")"
    else:
        out = "(" + register_config_list[0]
        for idx in range(1, len(register_config_list)):
            out += ", " + register_config_list[idx]
        out += ")"
        return out


## @}
