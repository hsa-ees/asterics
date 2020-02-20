# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_ram_spec.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Python module used by as_automatics used to build the generators internal model
of the ASTERICS hardware module ram, simple ram hardware description.
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
# @file as_ram_spec.py
# @author Philip Manke
# @brief Specifics for the simple ram module used by as_automatics
# -----------------------------------------------------------------------------

from as_automatics_module import AsModule
from as_automatics_port import Port
from as_automatics_interface import Interface

class SimpleRAMInterface(Interface):

    def __init__(self):
        super().__init__("simple_ram_interface")

        self.add_port(Port("wr_en"))
        self.add_port(Port("wr_addr",
                           data_type="std_logic_vector",
                           data_width=Port.DataWidth(a="ADDR_WIDTH - 1",
                                                     sep="downto",
                                                     b=0)))
        self.add_port(Port("rd_addr",
                           data_type="std_logic_vector",
                           data_width=Port.DataWidth(a="ADDR_WIDTH - 1",
                                                     sep="downto",
                                                     b=0)))
        self.add_port(Port("din",
                           data_type="std_logic_vector",
                           data_width=Port.DataWidth(a="DATA_WIDTH - 1",
                                                     sep="downto",
                                                     b=0)))
        self.add_port(Port("dout",
                           direction="out",
                           data_type="std_logic_vector",
                           data_width=Port.DataWidth(a="DATA_WIDTH - 1",
                                                     sep="downto",
                                                     b=0)))


def get_module_instance(module_dir: str) -> AsModule:
    module = AsModule()
    
    toplevel_file = "hardware/hdl/vhdl/ram/ram.vhd"
    
    module.files = []
    
    module.dependencies = []

    module.add_local_interface_template(SimpleRAMInterface())

    # as_automatics now automatically parses the toplevel file and discovers
    # ports, generics, existing interfaces and register interfaces
    module.discover_module("{mdir}/{toplevel}"
                           .format(mdir=module_dir, toplevel=toplevel_file))

    return module
