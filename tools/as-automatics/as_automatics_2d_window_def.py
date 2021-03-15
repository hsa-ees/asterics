# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_automatics_2d_infrastructure.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Class defining the 2D window of window interfaces for 2D Window Pipeline subsystems.
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
# @file as_automatics_2d_infrastructure.py
# @ingroup automatics_intrep
# @ingroup automatics_2dwpl
# @author Philip Manke
# @brief Class defining the 2D window of window interfaces for 2D Window Pipeline subsystems.
# -----------------------------------------------------------------------------

from math import ceil, floor


##
# @addtogroup automatics_2dwpl
# @{

## @ingroup automatics_intrep
class WindowDef:
    """! @brief Stores information about the window port of an
    as_automatics_2d_window_interface::AsWindowInterface."""

    def __init__(self, x: int = 0, y: int = 0):
        self.x = x
        self.y = y
        self.elements = self.x * self.y
        self.rows = dict()

    def get_delay(self, line_width: int):
        return line_width * floor(self.y / 2) + ceil(self.x / 2)

    def __str__(self) -> str:
        return "Window {} by {}".format(self.x, self.y)

    def __repr__(self) -> str:
        return "[x{},y{}]".format(self.x, self.y)


## @}
