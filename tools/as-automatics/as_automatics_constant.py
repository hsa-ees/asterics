# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_constant.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Implements the Constant class for as_automatics.
Used to store information about VHDL constants for use in as_automatics.
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
# @file as_constant.py
# @ingroup automatics_intrep
# @author Philip Manke
# @brief Used to store details about VHDL constants for use in as_automatics.
# -----------------------------------------------------------------------------

from as_automatics_helpers import get_printable_datatype


## @ingroup automatics_intrep
class Constant:
    """! @brief Class Representing a VHDL-constant.
    Acts mostly as data storage."""

    def __init__(
        self,
        name: str = "",
        code_name: str = "",
        data_type: str = "",
        value="",
        data_width="",
    ):
        self.name = name
        self.code_name = code_name
        self.data_type = data_type
        self.data_width = data_width
        self.value = value
        self.parent = None

        if not self.code_name:
            self.code_name = self.name
        if not self.name:
            self.name = self.code_name

    def __str__(self) -> str:
        return "'{}' with value: '{}'".format(self.code_name, self.value)

    def __repr__(self) -> str:
        return self.code_name

    def list_constant(self):
        """Prints a complete list of information available for this constant"""
        print(
            "{name}: {data_type}-constant with value: {value}".format(
                name=self.code_name,
                data_type=get_printable_datatype(self),
                value=self.value,
            )
        )

    ## @ingroup automatics_connection
    def assign_to(self, parent):
        """Assigns this instance as part of/linked to 'parent'"""
        self.parent = parent
