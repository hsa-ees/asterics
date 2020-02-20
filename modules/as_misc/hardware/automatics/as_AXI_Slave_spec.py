# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# Copyright (C) Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_AXI_Master_spec.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author: Philip Manke

Description:
Python module used by as_automatics used to build the generators internal model
of the ASTERICS support module AXI_Slave.
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
# @file as_AXI_Slave_spec.py
# @author Philip Manke
# @brief Specifics for AXI_Slave used by as_automatics
# -----------------------------------------------------------------------------

from as_automatics_module import AsModule
from as_automatics_interface import Interface
from as_automatics_port import Port, GlueSignal
from as_automatics_generic import Generic

class AXISlaveExternal(Interface):
    def __init__(self):
        super().__init__("AXI_Slave_external")

        self.add_port(Port("aclk"))
        self.add_port(Port("aresetn"))
        self.add_port(Port("awaddr", data_type="std_logic_vector",
                           data_width=Port.DataWidth(a="C_S_AXI_ADDR_WIDTH - 1",
                                                     sep="downto", b=0)))
        self.add_port(Port("awprot", data_type="std_logic_vector",
                           data_width=Port.DataWidth(a=2, sep="downto", b=0)))
        self.add_port(Port("awvalid"))
        self.add_port(Port("awready", direction="out"))
        self.add_port(Port("wdata", data_type="std_logic_vector",
                           data_width=Port.DataWidth(a="C_S_AXI_DATA_WIDTH - 1",
                                                     sep="downto", b=0)))
        self.add_port(Port("wstrb", data_type="std_logic_vector",
                           data_width=Port.DataWidth(
                               a="C_S_AXI_DATA_WIDTH / 8 - 1", sep="downto",
                               b=0)))
        self.add_port(Port("wvalid"))
        self.add_port(Port("wready", direction="out"))
        self.add_port(Port("bresp", direction="out",
                           data_type="std_logic_vector",
                           data_width=Port.DataWidth(a=1, sep="downto", b=0)))
        self.add_port(Port("bvalid", direction="out"))
        self.add_port(Port("bready"))

        self.add_port(Port("araddr", data_type="std_logic_vector",
                           data_width=Port.DataWidth(a="C_S_AXI_ADDR_WIDTH - 1",
                                                     sep="downto", b=0)))
        self.add_port(Port("arprot", data_type="std_logic_vector",
                           data_width=Port.DataWidth(a=2, sep="downto", b=0)))
        self.add_port(Port("arvalid"))
        self.add_port(Port("arready", direction="out"))
        self.add_port(Port("rdata", direction="out",
                           data_type="std_logic_vector",
                           data_width=Port.DataWidth(a="C_S_AXI_DATA_WIDTH - 1",
                                                     sep="downto", b=0)))
        self.add_port(Port("rresp", direction="out",
                           data_type="std_logic_vector",
                           data_width=Port.DataWidth(a=1, sep="downto", b=0)))
        self.add_port(Port("rvalid", direction="out"))
        self.add_port(Port("rready"))


        self.set_prefix_suffix(new_prefix="s_axi_", new_suffix="")
        self.to_external = True


def get_module_instance(module_dir: str) -> AsModule:
    module = AsModule("AXI_Slave")

    module.add_local_interface_template(AXISlaveExternal())
    
    toplevel_file = "hardware/hdl/vhdl/AXI/AXI_Slave.vhd"
    module.files = []
    module.dependencies = ["fifo_fwft", "helpers"]

    # as_automatics now automatically parses the toplevel file and discovers
    # ports, generics, existing interfaces and register interfaces
    module.discover_module("{mdir}/{toplevel}"
                           .format(mdir=module_dir, toplevel=toplevel_file))
    
    module.get_generic("C_S_AXI_DATA_WIDTH").set_value(None)
    module.get_generic("C_S_AXI_ADDR_WIDTH").set_value(None)

    return module
