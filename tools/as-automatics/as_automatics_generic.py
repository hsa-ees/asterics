# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_automatics_generic.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Implements the class 'Generic' for as_automatics.
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
# @file as_automatics_generic.py
# @ingroup automatics_intrep
# @author Philip Manke
# @brief Implements the class 'Generic' for as_automatics.
# -----------------------------------------------------------------------------

from inspect import isfunction
import as_automatics_logging as as_log

LOG = as_log.get_log()


## @ingroup automatics_intrep
class Generic:
    """! @brief Class representing a VHDL generic.
    Description of a single generic as defined in the entity of the
    associated module's top_level VHDL-file.
    Additionally, some meta information for as_automatics and data
    relevant only while building the processing chain is stored."""

    generic_types = "interface", "module"

    def __init__(
        self,
        name: str,
        default_value: str = None,
        code_name: str = "",
        data_type: str = "integer",
        link_to: str = "",
        to_external: bool = False,
        comment: str = "",
    ):

        self.value_check_function = lambda value: True
        self.comment = comment

        self.name = name
        self.default_value = default_value
        self.code_name = code_name
        self.data_type = data_type
        self.value = default_value
        self.to_external = to_external

        self.link_to = ""

        self.parent = None

        if not self.code_name:
            self.code_name = self.name
        if not self.name:
            self.name = self.code_name

    def __str__(self) -> str:
        """! @brief Print the configuration of this generic instance."""
        return "{}('{}'): {} with default value: {}".format(
            self.name, self.code_name, self.data_type, str(self.default_value)
        )

    def __repr__(self) -> str:
        return self.code_name

    def check_value(self):
        """! @brief Check if the currently set value is valid.
        Can only be invalid if set directly, not using the 'set_value()' method."""
        self.run_value_check(self.value)

    ## @ingroup automatics_cds
    def keep_default_value(self):
        """! @brief Set the Generic back to its default value.
        This Generic will set it's value to the default value read in
        from the VHDL source code of the module."""
        self.value = self.default_value

    def run_value_check(self, value) -> bool:
        """! @brief Checks if 'value' is valid for this generic."""
        return self.value_check_function(value)

    ## @ingroup automatics_cds
    def set_value_check(self, function):
        """! @brief Set a value check function for this Generic.
        Set the function that is used to perform the value check
        for this generic instance."""
        if isfunction(function):
            self.value_check_function = function
        else:
            LOG.error(
                (
                    "Setting value check function failed. "
                    "Parameter is not a function!"
                )
            )

    def get_value(self, top_default: bool = True):
        """! @brief Return the value of this generic object.
        If this generic does not have an assigned value, the 'default_value'
        is returned.
        Will recursively resolve 'value' if it is set to another generic object.
        """
        if getattr(self.parent, "window_interfaces", False):
            if self.value is not None:
                return self.value
            return self.default_value
        # If this generic is on toplevel
        if not self.parent.parent:
            if not self.value and top_default:
                return self.default_value
            return None
        if self.value is None:
            return self.default_value
        # This will work if 'value' is a generic object
        # Can't use 'isinstance(self.value, Generic)
        # Generic class not defined in itself
        try:
            return self.value.get_value()
        except AttributeError:
            pass
        return self.value

    def is_value_set(self):
        """! @brief Determine if the 'value' attribute is set."""
        return self.value is not None

    def set_value(self, value) -> bool:
        """! @brief Set the 'value' attribute of this generic object safely."""
        if self.run_value_check(value):
            # Generics can be linked through value attribute
            # -> propagate value change recursively
            try:
                return self.value.set_value(value)
            except AttributeError:
                pass  # If value is not a linked Generic, set it here
            self.value = value
            return True
        return False

    def link_to_generic(self, link_to_generic: str):
        """! @brief Setup this generic to link to another generic object."""
        self.value = None
        self.link_to = link_to_generic

    ## @ingroup automatics_connection
    def assign_to(self, parent):
        """! @brief Assigns this instance as part of/linked to 'parent'"""
        self.parent = parent
