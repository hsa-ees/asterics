# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_automatics_module_wrapper.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Class managing a single module to wrap in a VHDL file.
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
# @file as_automatics_module_wrapper.py
# @ingroup automatics_intrep
# @author Philip Manke
# @brief Class managing a single module to wrap in a VHDL file.
# -----------------------------------------------------------------------------

from as_automatics_module import AsModule
from as_automatics_module_group import AsModuleGroup
from as_automatics_signal import GlueSignal
from as_automatics_2d_window_module import AsWindowModule
from as_automatics_2d_window_interface import AsWindowInterface
from as_automatics_2d_helpers import get_delay, set_delay
from as_automatics_port import Port


from as_automatics_logging import get_log


LOG = get_log()

## @ingroup automatics_mngtm
class AsModuleWrapper(AsModuleGroup):
    """! @brief Class encapsulating an AsModule to manage generating an
    out-of-context Vivado run for it.
    This feature will generate a managed wrapper VHDL component containing only
    the interface for the wrapped ASTERICS module and instantiates it within the
    wrapper entity.
    This is necessary, as only standard std_logic data types are supported within
    interfaces and only component instantation is supported for out-of-context runs.
    @warning This is feature only compatible with Xilinx Vivado.
    This feature is not fully tested and considered an alpha feature.
    Using this will not allow Automatics to generate an IP-Core that
    can be used directly within block designs! The resulting IP-Core must first
    be opened manually as a Vivado project and synthesized before it can be used
    in other projects!"""

    def __init__(self, chain, parent):
        super().__init__("wrapper", parent, [])
        self.standard_ports = []
        self.parent = parent
        self.chain = chain

    def define_module_to_wrap(self, module: AsModule):
        self.modules = [module]
        module.modlevel += 1
        self.name = module.name
        self.entity_name = module.name + "_wrapper"
        self.generics = []
        self.standard_port_templates = module.standard_port_templates
        set_delay(self, get_delay(module))
        for inter in module.interfaces:
            self.add_interface(inter)
        for port in module.ports:
            self.add_port(port)
        for port in module.standard_ports:
            self.add_standard_port(port)
        if isinstance(module, AsWindowModule):
            self.vhdl_libraries.append("as_generic_filter")
            setattr(self, "window_interfaces", module.window_interfaces)
            module.window_interfaces = []

        module.interfaces = []
        module.ports = []
        module.standard_ports = []

        full_port_list = self.get_full_port_list(include_signals=False)

        for port in full_port_list:
            nport = port.duplicate()
            if nport.port_type == "interface":
                nport.set_port_type("single")
            module.add_port(nport)
            if port.direction == "in":
                nport.incoming = port
                port.outgoing.append(nport)
            else:
                nport.outgoing.append(port)
                port.incoming = nport

    def get_full_port_list(self, include_signals=True):
        portlist = super().get_full_port_list(include_signals)
        if self.modules and isinstance(self.modules[0], AsWindowModule):
            portlist.extend(
                [
                    winter.window_port
                    for winter in getattr(self, "window_interfaces", [])
                ]
            )
        return portlist

    def convert_window_port_to_vector(self) -> list:
        """! @brief Convert as_window to only use standard data types.
        If this module wrapper contains a window module, the window port's
        data type must be converted from t_generic_window to std_logic_vector.
        Generates the conversion code and adds the necessary signals within
        the wrapper VHDL file (conversion from vector to window type) and
        converts the port data type."""
        # If we wrap a window module, we need to convert t
        if not isinstance(self.modules[0], AsWindowModule):
            return None
        mod = self.modules[0]
        window_ports = []
        conversion_template = (
            "f_convert_vector_to_generic_window({vector_name}, {x}, {y})"
        )
        # Xilinx Vivado OOC Synthesis can't deal with custom data types
        # For all window interfaces, take the window port using the
        # t_generic_window data type and convert it to a std_logic_vector
        # Within this wrapper, take the vectorized port and convert it back
        # to a t_generic_window port to pass to the filter module.
        # The conversion from window to vector is done in the 2D Pipeline class
        for winter in getattr(self, "window_interfaces"):
            wport = winter.window_port
            window_dims = winter.window
            window_elements = window_dims.x * window_dims.y
            new_vector_width = (
                window_elements * wport.data_width.get_bit_width()
            )
            wport.data_type = "std_logic_vector"
            wport.data_width = Port.DataWidth(new_vector_width - 1, "downto", 0)
            mport = mod.get_port(wport.code_name, suppress_error=True)
            sig = self.define_signal(
                mport.code_name + "_reconv",
                data_type=mport.data_type,
                data_width=mport.data_width,
                fixed_value=conversion_template.format(
                    vector_name=wport.code_name,
                    x=window_dims.x,
                    y=window_dims.y,
                ),
            )
            sig.window_config = wport.window_config
            wport.window_config = None
            mport.incoming = sig
            window_ports.append(wport)
        return window_ports
