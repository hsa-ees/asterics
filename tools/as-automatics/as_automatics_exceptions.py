# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# Copyright (C) Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_automatics_exceptions.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Module containing all error and exception classes used in as_automatics.
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
# @file as_automatics_exceptions.py
# @author Philip Manke
# @brief Module containing all exception classes used in as_automatics.
# -----------------------------------------------------------------------------

# Base exceptions:

class AsError(Exception):
    """Exception class. Base for all Automatics exceptions."""
    def __init__(self):
        super().__init__()

class AsTextError(AsError):
    """Generic Automatics exception class. Base for multiple exceptions.
    Holds an error message, detail string and name of the affected resource."""
    def __init__(self, cause: str, msg: str = "", detail: str = ""):
        super().__init__()
        self.message = msg
        self.detail = detail
        self.cause = cause
        self.base_msg = "Error occurred!"
        

    def __str__(self):
        return "{}! {} {} {}" \
            .format(self.base_msg, self.message, self.detail, self.cause)
    
class AsObjectError(AsError):
    """Generic Automatics exception class. Base for multiple exceptions.
    Holds an error message, detail string and reference to the affected object.
    """

    def __init__(self, affected_obj=None, msg: str = "", detail: str = ""):
        super().__init__()
        self.message = msg
        self.detail = detail
        self.affected = affected_obj
        self.base_msg = "Object error occurred"

    def __str__(self):
        return "{}! {} {} {}" \
            .format(self.base_msg, self.message, self.detail,
                    "On object: {} {}".format(
                        str(self.affected), type(self.affected))
                    if self.affected else "")


# Specific exceptions:

class AsConnectionError(AsObjectError):
    """Automatics error class: AsConnectionError
    Signifies a problem/error with a port, interface or module connection.
    'message' contains the error message.
    'detail_string' may contain additional details.
    'affected' may refer to the affected object."""

    def __init__(self, affected_obj=None, msg: str = "", detail: str = ""):
        super().__init__(affected_obj, msg, detail)
        self.base_msg = "Connection error occurred"

class AsAnalysisError(AsTextError):
    """Automatics error class: AsAnalysisError
    Signifies a problem/error while analysing VHDL code.
    'message' and 'detail' contain details about the error.
    'filename' contains the name of the file where the error occurred."""

    def __init__(self, filename: str, msg: str = "", detail: str = ""):
        super().__init__(filename, msg, detail)
        self.base_msg = "Error analysing VHDL file"

class AsAssignError(AsObjectError):
    """Automatics error class: AsAssignError
    Signifies a problem/error while assigning objects to each other, like ports
    to interfaces and interfaces to modules.
    'detail_string' may contain additional details.
    'affected' may refer to the affected object."""

    def __init__(self, affected_obj, msg: str = "", detail: str = "",
                 assign_to: object = None):
        super().__init__(affected_obj, msg, detail)
        self.base_msg = "Error assigning object "

class AsFileError(AsTextError):
    """Automatics error class: AsFileError
    Signifies a problem/error with a file object.
    Usually a problem opening or writing to a file.
    'message' and 'detail' contain information about the error.
    'filename' stores the name of the file that caused the error."""

    def __init__(self, filename: str, msg: str = "", detail: str = ""):
        super().__init__(filename, msg, detail)
        self.base_msg = "File error occurred"


class AsModuleError(AsTextError):
    """Automatics error class: AsModuleError
    Signifies a problem/error with an AsModule object.
    Usually a module that couldn't be found in the module library.
    'message' and 'detail' contain details about the error.
    'module_name' stores the name of the module that caused the error."""

    def __init__(self, module_name: str, msg: str = "", detail: str = ""):
        super().__init__(module_name, msg, detail)
        self.base_msg = "Module error occurred"
