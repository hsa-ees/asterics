# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_automatics_2d_window_module.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Class representing an ASTERICS window module used to construct
2D-Window-Pipelines.
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
# @file as_automatics_2d_window_module.py
# @ingroup automatics_intrep
# @ingroup automatics_2dwpl
# @author Philip Manke
# @brief Class representing a window module for 2D-Window-Pipelines.
# -----------------------------------------------------------------------------


from as_automatics_module import AsModule
from as_automatics_port import Port, StandardPort
from as_automatics_2d_window_interface import AsWindowInterface

import as_automatics_logging as as_log

LOG = as_log.get_log()

##
# @addtogroup automatics_2dwpl
# @{

## @ingroup automatics_intrep
class AsWindowModule(AsModule):
    """! @brief Class representing a module for use in 2D Window Pipelines.
    Based on the AsModule class.
    Adds multiple attributes for managing aspects of the pipeline."""

    standard_port_templates = [
        StandardPort(name="clk", port_type="external"),
        StandardPort(
            "strobe",
            port_type="single",
            extra_rules=[
                Port.Rule("source_present", "fallback_signal(strobe_int)")
            ],
            overwrite_ruleset=True,
        ),
        StandardPort(
            "strobe_in",
            port_type="single",
            extra_rules=[
                Port.Rule("source_present", "fallback_signal(strobe_int)")
            ],
            overwrite_ruleset=True,
        ),
        StandardPort(
            "reset",
            port_type="single",
            extra_rules=[
                Port.Rule("source_present", "fallback_signal(reset_int)")
            ],
            overwrite_ruleset=True,
        ),
        StandardPort(
            name="flush_in",
            port_type="single",
            extra_rules=[Port.Rule("source_present", "fallback_signal(flush)")],
            overwrite_ruleset=True,
        ),
    ]

    def __init__(self):
        super().__init__()
        self.window_interfaces = []  # List of AsWindowInterface objects

        # Strobe delays:
        # Delay from previous module
        self.input_delay = -1
        # Delay from the processing of this module
        self.processing_delay = 0
        # Sum of all delays of this module on its output
        self.delay = 0
        # Additional delay set by user
        self.user_delay = 0

        self.pipe = None  # Reference to the As2DWindowPipeline object (parent)

    def __str__(self) -> str:
        return "ASTERICS Window-Module '{}' ({})".format(
            self.name, self.entity_name
        )

    def __update_delay__(self):
        self.delay = self.input_delay + self.processing_delay + self.user_delay

    ##
    # @addtogroup automatics_cds
    # @{

    def connect(self, connect_to) -> bool:
        """! @brief Add a connection from this module as a data source."""
        self.pipe.connect(self, connect_to)

    def get(self, name: str, direction: str = ""):
        """! @brief Generic interface and port search method.
        This method first searches for matching window interfaces.
        If none were found, passes the search request onto AsModule.get()."""
        inter = self.get_window_interface(name, direction)
        if inter:
            LOG.debug(
                "Selected interface '%s' from '%s'.", inter.name, self.name
            )
            return inter
        return super().get(name, direction)

    def get_window_interface(
        self, interface_name: str, direction: str = ""
    ) -> AsWindowInterface:
        """! @brief Search for and return a 'as_window' interface of this module.
        @param interface_name  Name of the interface to search for
        @param direction  Data direction of the interface to search for
        @return  A window interface or None if no match is found"""
        return next(
            (
                inter
                for inter in self.window_interfaces
                if inter.name == interface_name
                and (
                    True if (not direction) else (inter.direction == direction)
                )
            ),
            None,
        )

    ## @}

    def __gen_uname_for_window_ifs__(self):
        # Generate unique name for this module's interfaces
        for inter in self.window_interfaces:
            inter.unique_name = "{}_{}_{}_{}".format(
                inter.type, inter.name, inter.direction, self.name
            )

    def list_module(self, verbosity: int = 0):
        """! @brief List the configuration of this window module."""
        super().list_module(verbosity)

        if self.window_interfaces:
            print("\n~~~\nWindow Interfaces:")
            for inter in self.window_interfaces:
                if verbosity > 0:
                    inter.print_interface(verbosity > 0)
                else:
                    print(
                        str(inter)
                        + (" ->" if inter.direction == "in" else " <-")
                    )
                print("")

    def get_full_port_list(self, include_signals: bool = True) -> list:
        """Return a list containing a reference to every port in this module"""
        plist = super().get_full_port_list(include_signals)
        plist.extend((w.window_port for w in self.window_interfaces))
        return plist

    ## @ingroup automatics_analyze
    def discover_module(self, file: str):
        """! @brief Analyze and parse a VHDL toplevel file creating an AsWindowModule.
        Passes the call onto AsModule.discover_module() and handles
        additional tasks requried for AsWindowModules."""
        super().discover_module(
            file,
            window_module=True,
            extra_function=self.__assign_window_interfaces__,
        )

    ## @ingroup automatics_analyze
    def __assign_window_interfaces__(self):
        """! @brief Picks out all window ports and bundles them to WindowInterfaces.
        Must be run before regular interfaces are assigned."""

        to_remove = []  # Collecting ports assigned before
        for port in self.entity_ports:
            # If port is not part of a window interface, skip it
            if not getattr(port, "window_config"):
                continue
            # Create a new window interface and add the port
            inter = AsWindowInterface()
            inter.name = port.code_name
            inter.add_port(port)
            inter.window_port = port
            inter.assign_to(self)
            inter.direction = port.direction

            # Register the window interface with the module
            self.window_interfaces.append(inter)
            to_remove.append(port)

        for port in to_remove:
            self.entity_ports.remove(port)


## @}
