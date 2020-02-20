# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# Copyright (C) Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_automatics_templates.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Module containing all interface template classes for use in as_automatics.
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
# @file as_automatics_templates.py
# @author Philip Manke
# @brief Template definitions for interfaces used in as_automatics.
# -----------------------------------------------------------------------------

from as_automatics_interface import Interface
from as_automatics_port import Port, StandardPort, GlueSignal
from as_automatics_generic import Generic
from as_automatics_module import AsModule, AsModuleGroup


def add_templates():
    """This function is called when AsAutomatics initializes.
       It is used to construct all interface templates and assign them to the
       AsModule class for use when discovering interfaces in modules."""

    # When new interfaces are developed and added, add the interface to
    # AsAutomatics using a copy of one of the lines below.
    AsModule.add_global_interface_template(AsStream())
    AsModule.add_global_interface_template(AXIMasterMemoryInternal())
    AsModule.add_global_interface_template(CameraInputOV7670())
    AsModule.add_global_interface_template(AXISlaveRegisterInterface())


# as-stream interface definition
class AsStream(Interface):
    """Template definition for ASTERICS' 'as_stream' interface."""

    def __init__(self):
        super().__init__("as_stream")
        self.add_port(Port("strobe"))
        self.add_port(Port("data", data_type="std_logic_vector",
                           data_width=Port.DataWidth("DATA_WIDTH - 1",
                                                     "downto", 0)))
        self.add_port(Port("data_error", optional=True))
        self.add_port(Port("stall", direction="out", optional=True))
        self.add_port(Port("vsync", optional=True))
        vcomplete = Port("vcomplete", optional=True)
        vcomplete.add_rule("sink_missing", "fallback_port(vsync)", False)
        self.add_port(vcomplete)
        hcomplete = Port("hcomplete", optional=True)
        self.add_port(Port("hsync", optional=True))
        hcomplete.add_rule("sink_missing", "fallback_port(hsync)", False)
        self.add_port(hcomplete)
        self.add_port(
            Port(
                "xres",
                data_type="std_logic_vector",
                optional=True))
        self.add_port(
            Port(
                "yres",
                data_type="std_logic_vector",
                optional=True))


# Camera interface definition
class CameraInputOV7670(Interface):
    """Template definition for the Camera interface used by the OmniiVision
       OV7670 camera sensor."""

    def __init__(self):
        super().__init__("camera_interface_ov7670")
        self.add_port(Port("reset_n", direction="out"))
        self.add_port(Port("powerdown", direction="out"))
        self.add_port(Port("pixclk"))
        self.add_port(Port("frame_valid"))
        self.add_port(Port("line_valid"))
        self.add_port(Port("data", data_type="std_logic_vector",
                           data_width=Port.DataWidth("SENSOR_DATA_WIDTH - 1",
                                                     "downto", 0)))
        self.set_prefix_suffix("sensor_", "")
        self.to_external = True


# AXI Master Memory interface definition:
class AXIMasterMemoryInternal(Interface):
    """Template definition for the AXI Master Memory
       interface used in ASTERICS."""

    def __init__(self):
        super().__init__("axi_master_memory_int")

        # Ports for arbitration mode
        self.add_port(Port("mem_req", direction="out", optional=True))
        # This port needs to be set to '1' if not connected!
        mem_req_ack = Port("mem_req_ack", optional=True)
        mem_req_ack.overwrite_rule("sink_missing", "set_value('1')")
        self.add_port(mem_req_ack)

        # Ports towards AXI interface
        self.add_port(Port("mem_go", direction="out"))
        self.add_port(Port("mem_clr_go"))
        self.add_port(Port("mem_busy"))
        self.add_port(Port("mem_done"))
        self.add_port(Port("mem_error"))
        self.add_port(Port("mem_timeout"))
        self.add_port(Port("mem_rd_req", direction="out"))
        self.add_port(Port("mem_wr_req", direction="out"))
        self.add_port(Port("mem_bus_lock", direction="out"))
        self.add_port(Port("mem_burst", direction="out"))
        self.add_port(Port("mem_addr", direction="out",
                           data_type="std_logic_vector",
                           data_width=Port.DataWidth(
                               "MEM_ADDRESS_BIT_WIDTH - 1", "downto", 0)))
        self.add_port(Port("mem_be", direction="out",
                           data_type="std_logic_vector",
                           data_width=Port.DataWidth(15, "downto", 0)))
        self.add_port(Port("mem_xfer_length", direction="out",
                           data_type="std_logic_vector",
                           data_width=Port.DataWidth(
                               "BURST_LENGTH_BIT_WIDTH - 1", "downto", 0)))
        self.add_port(Port("mem_in_en"))
        self.add_port(Port("mem_in_data",
                           data_type="std_logic_vector",
                           data_width=Port.DataWidth("MEMORY_DATA_WIDTH - 1",
                                                     "downto", 0)))
        self.add_port(Port("mem_out_en"))
        self.add_port(Port("mem_out_data", direction="out",
                           data_type="std_logic_vector",
                           data_width=Port.DataWidth("MEMORY_DATA_WIDTH - 1",
                                                     "downto", 0)))
        # This interface usually always connects directly to an AXI Master
        # Unless an Arbiter module manages access to the AXI interface
        self.to_external = True
        self.instantiate_in_top = "AXI_Master"


class AXISlaveRegisterInterface(Interface):
    """Template definition for the AXI Slave Register
       interface used in ASTERICS."""

    def __init__(self):
        super().__init__("axi_slave_register_interface")
        self.add_port(Port("write_data", data_type="std_logic_vector",
                           data_width=Port.DataWidth("C_S_AXI_DATA_WIDTH - 1",
                                                     "downto", 0)))
        self.add_port(Port("read_data", data_type="std_logic_vector",
                           direction="out",
                           data_width=Port.DataWidth("C_S_AXI_DATA_WIDTH - 1",
                                                     "downto", 0)))
        self.add_port(Port("write_enable"))
        self.add_port(Port("read_enable"))
        self.add_port(Port("write_address", data_type="std_logic_vector",
                           data_width=Port.DataWidth("C_S_AXI_ADDR_WIDTH - 1",
                                                     "downto", 0)))
        self.add_port(Port("read_address", data_type="std_logic_vector",
                           data_width=Port.DataWidth("C_S_AXI_ADDR_WIDTH - 1",
                                                     "downto", 0)))
        self.add_port(Port("write_byte_strobe", data_type="std_logic_vector",
                           data_width=Port.DataWidth(
                               "C_S_AXI_DATA_WIDTH / 8 - 1",
                               "downto", 0)))
        self.set_prefix_suffix("axi_slv_reg_", "")


class AXISlaveInterface(Interface):
    """Template definition for the AXI Slave interface used in ASTERICS."""

    def __init__(self):
        super().__init__("axi_slave_interface")
        self.add_port(Port("aclk"))
        self.add_port(Port("areset_n"))
        self.add_port(Port("awaddr", data_type="std_logic_vector",
                           data_width=Port.DataWidth("C_S_AXI_ADDR_WIDTH - 1",
                                                     "downto", 0)))
        self.add_port(Port("awprot", data_type="std_logic_vector",
                           data_width=Port.DataWidth(2, "downto", 0)))
        self.add_port(Port("awvalid"))
        self.add_port(Port("awready", direction="out"))
        self.add_port(Port("wdata", data_type="std_logic_vector",
                           data_width=Port.DataWidth("C_S_AXI_DATA_WIDTH - 1",
                                                     "downto", 0)))
        self.add_port(Port("wstrb", data_type="std_logic_vector",
                           data_width=Port.DataWidth(
                               "C_S_AXI_DATA_WIDTH / 8 - 1", "downto", 0)))
        self.add_port(Port("wvalid"))
        self.add_port(Port("wready", direction="out"))
        self.add_port(Port("bresp", direction="out",
                           data_type="std_logic_vector",
                           data_width=Port.DataWidth(1, "downto", 0)))
        self.add_port(Port("bvalid", direction="out"))
        self.add_port(Port("araddr", data_type="std_logic_vector",
                           data_width=Port.DataWidth("C_S_AXI_ADDR_WIDTH - 1",
                                                     "downto", 0)))
        self.add_port(Port("arprot", data_type="std_logic_vector",
                           data_width=Port.DataWidth(2, "downto", 0)))
        self.add_port(Port("arvalid"))
        self.add_port(Port("arready", direction="out"))
        self.add_port(Port("rdata", direction="out",
                           data_type="std_logic_vector",
                           data_width=Port.DataWidth("C_S_AXI_DATA_WIDTH - 1",
                                                     "downto", 0)))
        self.add_port(Port("rresp", data_type="std_logic_vector",
                           data_width=Port.DataWidth(1, "downto", 0),
                           direction="out"))
        self.add_port(Port("rvalid", direction="out"))
        self.add_port(Port("rready"))
        self.set_prefix_suffix("s_axi_", "")
        self.to_external = True


class AsMain(AsModuleGroup):

    def __init__(self, top):
        super().__init__("as_main", top, [])
        self.entity_name = "as_main"

        # Setup default reset signal and port and default AXI Slave Interface
        self.add_standard_port(StandardPort("reset_n", port_type="external"))

        clk = StandardPort("clk", port_type="single")
        self.add_standard_port(clk)
        axi_slave_reg_inter = AXISlaveRegisterInterface()
        axi_slave_reg_inter.instantiate_in_top = "AXI_Slave"
        self.add_interface(axi_slave_reg_inter)
        reset = GlueSignal("reset")
        reset.assign_to(self)
        self.signals = [reset]
        self.add_generic(Generic(name="C_S_AXI_ADDR_WIDTH",
                                 default_value=32))
        self.add_generic(Generic(name="C_S_AXI_DATA_WIDTH",
                                 default_value=32))
        self.dependencies = ["as_regmgr"]


class AsTop(AsModuleGroup):

    def __init__(self):
        super().__init__("asterics", None, [])
        self.entity_name = "asterics"
        clk_p = StandardPort("clk")
        clk_p.in_entity = False
        rst_p = StandardPort("reset_n")
        rst_p.in_entity = False
        self.add_standard_port(clk_p)
        self.add_standard_port(rst_p)
        clk = GlueSignal("clk")
        rst = GlueSignal("reset_n")
        clk.assign_to(self)
        rst.assign_to(self)
        self.signals = [clk, rst]
        self.dependencies = ["as_main"]
