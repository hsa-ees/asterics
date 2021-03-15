# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_automatics_2d_window_interface.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Class representing an ASTERICS window interface used by AsWindowModules
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
# @file as_automatics_2d_window_interface.py
# @ingroup automatics_intrep
# @ingroup automatics_2dwpl
# @author Philip Manke
# @brief Class representing an ASTERICS window interface used by AsWindowModules
# -----------------------------------------------------------------------------

import itertools as ittls

from as_automatics_helpers import extract_generics
from as_automatics_port import Port
from as_automatics_interface import Interface
from as_automatics_2d_window_def import WindowDef
from as_automatics_2d_helpers import resolve_data_width

import as_automatics_logging as as_log

LOG = as_log.get_log()

##
# @addtogroup automatics_2dwpl
# @{

## @ingroup automatics_intrep
class AsWindowInterface(Interface):
    """! @brief Interface definition for interface 'as_window'.
    Used in as_automatics_2d_pipeline::As2DWindowPipeline."""

    INTERFACE_TYPE_STR = "as_window"

    def __init__(self):
        super().__init__(self.INTERFACE_TYPE_STR)
        self.delay = None
        self.incoming = []
        self.window = WindowDef(0, 0)
        self.window_port = None

    def print_interface(self, verbosity: int = 0):
        super().print_interface()
        print("\nWindow port:")
        print(self.window_port)
        print("Window size: {}".format(self.window))

    def update_window(self) -> bool:
        """! @brief Update and set the window size for this interface.
        Also attempts to parse the variable size of the 't_generic_window'
        datatype.
        @return Whether the t_generic_window data type could be parsed."""
        parse_successful = True
        port = self.window_port

        # Find and assign generics to the port
        # Put the data widths into a single list
        widths = ittls.chain([port.data_width], port.window_config)
        # Extract the generics and package the result into a list
        gen_names = ittls.chain(*(extract_generics(w) for w in widths))
        # Add found generics of the parent module to the port this interface
        for name in gen_names:
            gen = self.parent.get_generic(name, suppress_error=True)
            if gen:
                port.add_generic(gen)
                self.add_generic(gen)

        port.window_config = [
            resolve_data_width(width, port.generics)
            for width in port.window_config
        ]

        if not all((width.is_resolved() for width in port.window_config)):
            LOG.warning(
                (
                    "Could not determine window size for "
                    "interface '%s' of module '%s'! Unresolved "
                    "generics present in '%s'!"
                ),
                self.name,
                self.parent.name,
                str(port.window_config),
            )
            parse_successful = False
        else:
            self.window = self.data_widths_to_window(*port.window_config)

        return parse_successful

    ## @ingroup automatics_helpers
    @staticmethod
    def data_widths_to_window(
        columns: Port.DataWidth, rows: Port.DataWidth
    ) -> WindowDef:
        if columns.sep == "to":
            to_x = columns.b
        else:
            to_x = columns.a
        if rows.sep == "to":
            to_y = rows.b
        else:
            to_y = rows.a
        # Only return a window object, if the indices are resolved (no generics!)
        if any((not isinstance(idx, int) for idx in (to_x, to_y))):
            return None
        return WindowDef(to_x + 1, to_y + 1)


## @}
