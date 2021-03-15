# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
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
# @ingroup automatics_errors
# @author Philip Manke
# @brief Module containing all exception classes used in as_automatics.
# -----------------------------------------------------------------------------

import as_automatics_logging as as_log

LOG = as_log.get_log()


##
# @addtogroup automatics_errors
# @{

SEVERITIES = ("Error", "Warning", "Critical")
SEVERITY_MAP = {2: "Warning", 1: "Error", 0: "Critical"}
ERROR_TYPES = (
    "General",
    "Object",
    "Connection",
    "Assignment",
    "Module",
    "IO",
    "Analysis",
)


class AsErrorManager:
    """! @brief Class to collect, count and categorize all Automatics-specific errors."""

    def __init__(self):
        self.error_count = {}
        self.error_severities = {}
        self.errors = []

    def register_error(self, err):
        """! @brief Called when a new error object is generated."""
        try:
            self.error_count[err.type] += 1
        except KeyError:
            self.error_count[err.type] = 1
        try:
            self.error_severities[err.severity] += 1
        except KeyError:
            self.error_severities[err.severity] = 1
        self.errors.append(err)

    def clear_error(self, err):
        try:
            self.error_severities[err.severity] -= 1
            self.error_count[err.type] -= 1
            self.errors.remove(err)
        except KeyError:
            pass
        except ValueError:
            self.error_severities[err.severity] += 1
            self.error_count[err.type] += 1

    def has_errors(self, severity: str = "Error") -> bool:
        """! @brief Returns whether errors have been encountered.
        Use 'severity' to exclude errors below the passed severity."""
        if not self.errors:
            return False
        if severity not in SEVERITIES:
            raise ValueError("Invalid error severity '{}'".format(severity))
        sev_id = next(
            (
                idx
                for idx in sorted(SEVERITY_MAP.keys())
                if SEVERITY_MAP[idx] == severity
            )
        )
        for idx in range(sev_id, 0, -1):
            try:
                if self.error_severities[SEVERITY_MAP[idx]]:
                    return True
            except KeyError:
                pass
        return False

    def has_specific_error(
        self, err_type: str = "", severity: str = ""
    ) -> bool:
        """! @brief Returns whether specific errors have ocurred.
        Allows checking whether errors of a specific type and/or severity
        have occurred."""
        if err_type and severity:
            return bool(
                [
                    err
                    for err in self.errors
                    if err.type == err_type and err.severity == severity
                ]
            )
        elif err_type:
            return True if self.get_error_count(err_type) > 0 else False
        elif severity:
            return (
                True if self.get_error_severity_count(severity) > 0 else False
            )
        # Else ->
        return bool(len(self.errors))

    def get_error_count(self, err_type: str = "") -> int:
        if err_type:
            try:
                return self.error_count[err_type]
            except KeyError:
                if err_type in ERROR_TYPES:
                    return 0
                else:
                    LOG.error(
                        "Invalid error type querying AsErrorManager! '%s'",
                        err_type,
                    )
                    return -1
        # Else ->
        return len(self.errors)

    def get_error_severity_count(self, severity: str) -> int:
        try:
            return self.error_severities[severity]
        except KeyError:
            if severity in SEVERITIES:
                return 0
            else:
                LOG.error(
                    ("Invalid error severity querying AsErrorManager!" " '%s'"),
                    severity,
                )
                return -1

    def get_errors(self, err_type: str = "") -> list:
        if err_type:
            return [err for err in self.errors if err.type == err_type]
        # -> Else
        return self.errors

    def print_errors(self):
        count = 0
        for err in self.errors:
            try:
                getattr(err, "base_msg")
            except AttributeError:
                continue  # Skip errors that wouldn't print anything
            print("#{} [{}] - {}".format(count, err.severity, str(err)))
            count += 1


# Base exceptions:


class AsError(Exception):
    """! @brief Base exception class for all Automatics exceptions."""

    # Error manager is set in 'as_automatics_env.py' during init of Automatics
    err_mgr = None

    def __init__(self, err_type: str = "General", severity: str = "Error"):
        super().__init__()
        self.type = err_type
        self.severity = severity
        self.err_mgr.register_error(self)


class AsTextError(AsError):
    """! @brief Generic Automatics exception class with additional textual info.
    Base for multiple exceptions.
    Holds an error message, detail string and name of the affected resource."""

    def __init__(
        self,
        cause: str,
        msg: str = "",
        detail: str = "",
        err_type: str = "General",
        severity: str = "Error",
    ):
        super().__init__(err_type, severity)
        self.message = msg
        self.detail = detail
        self.cause = cause
        self.base_msg = "Error occurred!"

    def __str__(self):
        return "{}! {} {} {}".format(
            self.base_msg, self.message, self.detail, self.cause
        )


class AsObjectError(AsError):
    """! @brief Generic Automatics exception class concerning a specific object.
    Base for multiple exceptions.
    Holds an error message, detail string and reference to the affected object.
    """

    def __init__(
        self,
        affected_obj=None,
        msg: str = "",
        detail: str = "",
        err_type: str = "Object",
        severity: str = "Error",
    ):
        super().__init__(err_type, severity)
        self.message = msg
        self.detail = detail
        self.affected = affected_obj
        self.base_msg = "Object error occurred"

    def __str__(self):
        return "{}! {} {} {}".format(
            self.base_msg,
            self.message,
            self.detail,
            "On object: {} {}".format(str(self.affected), type(self.affected))
            if self.affected
            else "",
        )


# Specific exceptions:


class AsConnectionError(AsObjectError):
    """! @brief Automatics error class: AsConnectionError
    Signifies a problem/error with a port, interface or module connection.
    'message' contains the error message.
    'detail_string' may contain additional details.
    'affected' may refer to the affected object."""

    def __init__(
        self,
        affected_obj=None,
        msg: str = "",
        detail: str = "",
        severity: str = "Error",
    ):
        super().__init__(
            affected_obj, msg, detail, err_type="Connection", severity=severity
        )
        self.base_msg = "Connection error occurred"


class AsAnalysisError(AsTextError):
    """! @brief Automatics error class: AsAnalysisError
    Signifies a problem/error while analysing VHDL code.
    'message' and 'detail' contain details about the error.
    'filename' contains the name of the file where the error occurred."""

    def __init__(
        self,
        filename: str,
        msg: str = "",
        detail: str = "",
        severity: str = "Error",
    ):
        super().__init__(
            filename, msg, detail, err_type="Analysis", severity=severity
        )
        self.base_msg = "Error analysing VHDL file"


class AsAssignError(AsObjectError):
    """! @brief Automatics error class: AsAssignError
    Signifies a problem/error while assigning objects to each other, like ports
    to interfaces and interfaces to modules.
    'detail_string' may contain additional details.
    'affected' may refer to the affected object."""

    def __init__(
        self,
        affected_obj,
        msg: str = "",
        detail: str = "",
        assign_to: object = None,
        severity: str = "Error",
    ):
        super().__init__(
            affected_obj, msg, detail, err_type="Assignment", severity=severity
        )
        self.base_msg = "Error assigning object "


class AsFileError(AsTextError):
    """! @brief Automatics error class: AsFileError
    Signifies a problem/error with a file object.
    Usually a problem opening or writing to a file.
    'message' and 'detail' contain information about the error.
    'filename' stores the name of the file that caused the error."""

    def __init__(
        self,
        filename: str,
        msg: str = "",
        detail: str = "",
        severity: str = "Error",
    ):
        super().__init__(
            filename, msg, detail, err_type="IO", severity=severity
        )
        self.base_msg = "File error occurred"


class AsModuleError(AsTextError):
    """! @brief Automatics error class: AsModuleError
    Signifies a problem/error with an AsModule object.
    Usually a module that couldn't be found in the module library.
    'message' and 'detail' contain details about the error.
    'module_name' stores the name of the module that caused the error."""

    def __init__(
        self,
        module_name: str,
        msg: str = "",
        detail: str = "",
        severity: str = "Error",
    ):
        super().__init__(
            module_name, msg, detail, err_type="Module", severity=severity
        )
        self.base_msg = "Module error occurred"


class AsNameError(AsTextError):
    """! @brief Automatics error class: AsNameError
    Signifies a problem/error with a port/module/etc. name from the user script.
    Usually a port or interface that couldn't be found in a module.
    'message' and 'detail' contain details about the error.
    'affected_name' stores the name parameter that caused the error.
    'from_object' stores the object where the error was thrown."""

    def __init__(
        self,
        affected_name: str,
        from_object,
        msg: str = "",
        detail: str = "",
        severity: str = "Error",
    ):
        if from_object:
            label = "{} in {}".format(affected_name, str(from_object))
        else:
            label = affected_name
        super().__init__(
            label, msg, detail, err_type="InvalidName", severity=severity
        )


if AsError.err_mgr is None:
    AsError.err_mgr = AsErrorManager()


def list_errors():
    AsError.err_mgr.print_errors()


## @}
