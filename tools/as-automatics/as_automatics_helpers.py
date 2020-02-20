# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# Copyright (C) Hochschule Augsburg, University of Applied Sciences
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
# @author Philip Manke
# @brief Implements some helper functions used throughout as_automatics.
# -----------------------------------------------------------------------------

from typing import Sequence

import as_automatics_logging as as_log

LOG = as_log.get_log()

##
# Doxygen: Start doxy module 'Helpers'
# @defgroup Helpers Various helper functions / resources used in as_automatics.
# @{

__eval_env__ = {"locals": None, "globals": None, "__name__": None,
                "__file__": None, "__builtins__": None}


def get_matching_prefix_suffix(port_names: Sequence[str],
                               ignored_substrings: Sequence[str])-> [str, str]:
    """Find matching prefixes and suffixes for all strings in list 'port_names'.
       Assumes that all substrings including the pre-/suffixes are delimited
       with '_'. The keywords 'in', 'out' and 'inout' are ignored."""
    prefix = ""
    suffix = ""
    str_list = []
    idx = 0

    if len(port_names) < 2:
        return ["", ""]

    # Split the names on the delimiter '_' and filter out
    # the port directions, which may be included in the port names
    for str_ in port_names:
        tokens = str_.split('_')
        str_list.append([token for token in tokens
                         if token not in ignored_substrings])

    # Look for matching prefixes
    for crt_token in str_list[0]:
        if all([token == crt_token for token in
                [subtokens[idx] for subtokens in str_list]]):
            prefix = prefix + crt_token + "_"
        idx += 1

    # Look for matching suffixes
    idx = -1
    for crt_token in reversed(str_list[0]):
        if all([token == crt_token for token in
                [subtokens[idx] for subtokens in str_list]]):
            suffix = "_" + crt_token + suffix
        idx -= 1

    return [prefix, suffix]


def get_prefix_suffix(port_name: str, code_name: str,
                      ignored_keywords: Sequence[str]) -> [str, str]:
    """Extract the prefix and suffix from a code name of a VHDL port.
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
    prefix_list = prefix.strip('_').split('_')
    suffix_list = suffix.strip('_').split('_')
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


def strip_name(code_name: str, to_strip: Sequence[str],
               ignored_keywords: Sequence[str]) -> [str, str]:
    """Remove 'ignored_keywords' from the name along with all matching strings
       in the list 'to_strip'. Assumes that the name fragments are delimited
       with '_'."""
    out = ""
    if any([keyword in code_name for keyword in ignored_keywords]):
        # Remove the ignored keywords from the code name
        temp = code_name.split('_')
        while temp[0] in ignored_keywords:
            del temp[0]
        temp.reverse()
        while temp[0] in ignored_keywords:
            del temp[0]
        temp.reverse()
        # Rebuild the string:
        for string in temp:
            if out == "":
                out = string
            else:
                out = out + "_" + string
    else:
        # If there's no ignored keywords to remove
        out = code_name

    # Replace the strings to (potentially) remove with emtpy strings
    for string in to_strip:
        out = out.replace(string, "", 1)

    return out


def is_data_width_compatible(dw_a, dw_b) -> bool:
    """Quick check whether the data widths represent the same width."""
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


def generate_generic_dict(module) -> dict:
    """Returns a dictionary containing all generics of 'module'
    indexed by their code_name."""
    out = dict()
    for gen in module.generics:
        out[gen.code_name] = gen.get_value()
    return out


def eval_data_width(port, extra_dict: dict = None):
    """Evalutate the data width attribute of 'port'
    so that no generic names are contained (it is static).
    Pass additional generics not contained in 'port' using 'extra_dict'."""
    # Is port's data width already resolved?
    if is_data_width_resolved(port.data_width):
        return port.data_width

    # Add extra dicts contents to the generic pool
    if extra_dict is not None:
        gen_dict = merge_dicts(generate_generic_dict(port.parent), extra_dict)

    # String for reporting/logging
    origin = "data width of {}".format(port.code_name)
    # Evaluate low and high boundaries separately
    if isinstance(port.data_width.a, str):
        a = eval_vhdl_expr(port.data_width.a, origin, gen_dict)
    else:
        a = port.data_width.a
    if isinstance(port.data_width.b, str):
        b = eval_vhdl_expr(str(port.data_width.b), origin, gen_dict)
    else:
        b = port.data_width.b
    # Assemble and return new, resolved data width
    return port.DataWidth(a=a, sep=port.data_width.sep, b=b)


def eval_vhdl_expr(to_eval: str, string_origin: str,
                   variable_dict: dict = {}):
    """Evaluate an expression using Python's eval function.
    eval is used in a stripped down version, removing most of Python's
    built-in functions (we only want to resolve mathematic expressions)."""
    try:
        ret = eval(to_eval, __eval_env__, variable_dict)
        return int(ret) if (isinstance(ret, int) or isinstance(ret, float)) \
            else str(ret)
    except TypeError as err:
        LOG.debug(("Couldn't parse %s for input '%s'. Got "
                   "TypeError: '%s'"), string_origin, to_eval, str(err))
        return to_eval
    except SyntaxError as err:
        LOG.debug(("Couldn't parse %s for input '%s'. Got "
                   "SyntaxError: '%s'"), string_origin, to_eval, str(err))
        return to_eval


def is_data_width_resolved(data_width) -> bool:
    """Quick check to see if the data width is resolved
    (minimum complexity, no generic names in expressions)."""
    if data_width.sep is None:
        return True
    if isinstance(data_width.a, int) and isinstance(data_width.b, int):
        return True
    return False


def extract_generics(data_width) -> Sequence[str]:
    """Extract generic names from the data width tuple."""
    if not data_width.sep:
        return ""
    dwstr = "{}{}".format(data_width.a, data_width.b)
    to_replace = " -+*/^()<>"
    for repl in to_replace:
        dwstr = dwstr.replace(repl, ".")
    return list(filter(lambda x: bool(x) and not x.isnumeric(),
                       dwstr.split(".")))


def get_printable_datatype(port) -> str:
    """Formats the data width and type of the passed 'port' object
    into a printable string."""
    if port.data_width.sep is None:
        return port.data_type
    return "{}({})".format(port.data_type,
                           port.data_width_to_string(port.data_width))


def append_to_path(path: str, to_append: str, add_trailing_slash: bool = True):
    """Take two path fragments and merge them.
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


# From
# https://stackoverflow.com/questions/38987/how-to-merge-two-dictionaries-in-a-single-expression

def merge_dicts(*dict_args):
    """Given any number of dicts, shallow copy and merge into a new dict,
       precedence goes to key value pairs in latter dicts."""
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


def get_source_module(inter) -> object:
    """Returns the module that is the source of the interface 'inter'."""
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

##
# Doxygen: Stop doxy module 'Helpers'
# @}
