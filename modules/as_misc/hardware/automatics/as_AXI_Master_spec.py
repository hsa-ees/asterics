# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
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
of the ASTERICS support module AXI_Master.
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
# @file as_AXI_Master_spec.py
# @author Philip Manke
# @brief Specifics for AXI_Master used by as_automatics
# -----------------------------------------------------------------------------

from as_automatics_module import AsModule
from as_automatics_interface import Interface
from as_automatics_port import Port
from as_automatics_generic import Generic

class AXIMasterExternal(Interface):
    def __init__(self):
        super().__init__("AXI_Master_external")

        self.add_port(Port("m_axi_aclk"))
        self.add_port(Port("m_axi_aresetn"))
        self.add_port(Port("m_axi_arready"))
        self.add_port(Port("m_axi_arvalid", direction="out"))
        self.add_port(Port("m_axi_araddr", direction="out", 
                           data_type="std_logic_vector",
                           data_width=Port.DataWidth(a="C_M_AXI_ADDR_WIDTH - 1",
                                                     sep="downto", b=0)))
        self.add_port(Port("m_axi_arlen", direction="out",
                           data_type="std_logic_vector",
                           data_width=Port.DataWidth(a=7, sep="downto", b=0)))
        self.add_port(Port("m_axi_arsize", direction="out",
                           data_type="std_logic_vector",
                           data_width=Port.DataWidth(a=2, sep="downto", b=0)))
        self.add_port(Port("m_axi_arburst", direction="out",
                           data_type="std_logic_vector",
                           data_width=Port.DataWidth(a=1, sep="downto", b=0)))
        self.add_port(Port("m_axi_arprot", direction="out",
                           data_type="std_logic_vector",
                           data_width=Port.DataWidth(a=2, sep="downto", b=0)))
        self.add_port(Port("m_axi_arcache", direction="out",
                           data_type="std_logic_vector",
                           data_width=Port.DataWidth(a=3, sep="downto", b=0)))
        self.add_port(Port("m_axi_rready", direction="out"))
        self.add_port(Port("m_axi_rvalid"))
        self.add_port(Port("m_axi_rdata", data_type="std_logic_vector",
                           data_width=Port.DataWidth(a="C_M_AXI_DATA_WIDTH - 1",
                                                     sep="downto", b=0)))
        self.add_port(Port("m_axi_rresp", data_type="std_logic_vector",
                           data_width=Port.DataWidth(a=1, sep="downto", b=0)))
        self.add_port(Port("m_axi_rlast"))
        self.add_port(Port("m_axi_awready"))
        self.add_port(Port("m_axi_awvalid", direction="out"))
        self.add_port(Port("m_axi_awaddr", direction="out",
                           data_type="std_logic_vector",
                           data_width=Port.DataWidth(a="C_M_AXI_ADDR_WIDTH - 1",
                                                     sep="downto", b=0)))
        self.add_port(Port("m_axi_awlen", direction="out",
                           data_type="std_logic_vector",
                           data_width=Port.DataWidth(a=7, sep="downto", b=0)))
        self.add_port(Port("m_axi_awsize", direction="out",
                           data_type="std_logic_vector",
                           data_width=Port.DataWidth(a=2, sep="downto", b=0)))
        self.add_port(Port("m_axi_awburst", direction="out",
                           data_type="std_logic_vector",
                           data_width=Port.DataWidth(a=1, sep="downto", b=0)))
        self.add_port(Port("m_axi_awprot", direction="out",
                           data_type="std_logic_vector",
                           data_width=Port.DataWidth(a=2, sep="downto", b=0)))
        self.add_port(Port("m_axi_awcache", direction="out",
                           data_type="std_logic_vector",
                           data_width=Port.DataWidth(a=3, sep="downto", b=0)))
        self.add_port(Port("m_axi_wready"))
        self.add_port(Port("m_axi_wvalid", direction="out"))
        self.add_port(Port("m_axi_wdata", direction="out",
                           data_type="std_logic_vector",
                           data_width=Port.DataWidth(a="C_M_AXI_DATA_WIDTH - 1",
                                                     sep="downto", b=0)))
        self.add_port(Port("m_axi_wstrb", direction="out",
                           data_type="std_logic_vector",
                           data_width=Port.DataWidth(
                               a="C_M_AXI_DATA_WIDTH / 8 - 1", sep="downto",
                               b=0)))
        self.add_port(Port("m_axi_wlast", direction="out"))
        self.add_port(Port("m_axi_bready", direction="out"))
        self.add_port(Port("m_axi_bvalid"))
        self.add_port(Port("m_axi_bresp", data_type="std_logic_vector",
                           data_width=Port.DataWidth(a=1, sep="downto", b=0)))
        md_err = Port("md_error", direction="out", optional=True)
        md_err.overwrite_rule("sink_missing", "set_value(open)")
        self.add_port(md_err)

        self.to_external = True


def get_module_instance(module_dir: str) -> AsModule:
    
    module = AsModule()

    module.add_local_interface_template(AXIMasterExternal())
    
    
    toplevel_file = "hardware/hdl/vhdl/AXI/AXI_Master.vhd"
    module.files = []
    module.dependencies = ["fifo_fwft", "helpers"]

    # as_automatics now automatically parses the toplevel file and discovers
    # ports, generics, existing interfaces and register interfaces
    module.discover_module("{mdir}/{toplevel}"
                           .format(mdir=module_dir, toplevel=toplevel_file))

    internal_memory = module.get_interface("out")
    internal_memory.to_external = False
    internal_memory.instantiate_in_top = None
    
    module.get_generic("C_M_AXI_DATA_WIDTH").set_value(None)
    module.get_generic("C_M_AXI_ADDR_WIDTH").set_value(None)

    return module
