# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
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
# @ingroup automatics_intrep
# @author Philip Manke
# @brief Template definitions for interfaces used in as_automatics.
# -----------------------------------------------------------------------------

from math import ceil, log2
import itertools as ittls
import copy

from as_automatics_interface import Interface
from as_automatics_port import Port, StandardPort
from as_automatics_signal import GlueSignal, GenericSignal
from as_automatics_generic import Generic
from as_automatics_module import AsModule
from as_automatics_module_group import AsModuleGroup

import as_automatics_vhdl_static as as_vhdl_static


def add_templates():
    """! @brief Add global interface templates.
    This function is called when AsAutomatics initializes.
    It is used to construct all interface templates and assign them to the
    AsModule class for use when discovering interfaces in modules."""

    # When new interfaces are developed and added, add the interface to
    # AsAutomatics using a copy of one of the lines below.
    AsModule.add_global_interface_template(AsStream())
    AsModule.add_global_interface_template(AXIMasterMemoryInternal())
    AsModule.add_global_interface_template(CameraInputOV7670())
    AsModule.add_global_interface_template(AXISlaveRegisterInterface())
    AsModule.add_global_interface_template(SlaveRegisterInterfaceTemplate())


# as_stream interface definition
## @ingroup automatics_intrep
class AsStream(Interface):
    """! @brief Template definition for ASTERICS' 'as_stream' interface."""

    INTERFACE_TYPE_NAME = "as_stream"

    INTERFACE_TYPE_NAME = "as_stream"

    def __init__(self):
        super().__init__(self.INTERFACE_TYPE_NAME)
        self.add_port(Port("strobe"))
        self.add_port(
            Port(
                "data",
                data_type="std_logic_vector",
                data_width=Port.DataWidth("DATA_WIDTH - 1", "downto", 0),
            )
        )
        self.add_port(Port("data_error", optional=True))
        self.add_port(Port("stall", direction="out", optional=True))
        self.add_port(Port("vsync", optional=True))
        vcomplete = Port("vcomplete", optional=True)
        vcomplete.add_rule("sink_missing", "fallback_port(vsync)", False)
        vcomplete.add_rule(
            "sink_missing", "fallback_port(data_unit_complete)", False
        )
        self.add_port(vcomplete)
        hcomplete = Port("hcomplete", optional=True)
        self.add_port(Port("hsync", optional=True))
        hcomplete.add_rule("sink_missing", "fallback_port(hsync)", False)
        self.add_port(hcomplete)
        self.add_port(Port("xres", data_type="std_logic_vector", optional=True))
        self.add_port(Port("yres", data_type="std_logic_vector", optional=True))
        self.add_port(Port("data_unit_complete", optional=True))


# Slave register interface (module <-> as_regmgr)
## @ingroup automatics_intrep
class SlaveRegisterInterfaceTemplate(Interface):
    """! @brief Template definition of the ASTERICS slave register interface.
    Template definition for the slave register interface used for
    communication between ASTERICS Modules and the register management hardware.
    """

    INTERFACE_TYPE_NAME = "slv_reg_interface"

    def __init__(self):
        super().__init__(self.INTERFACE_TYPE_NAME)
        self.add_port(Port("slv_ctrl_reg", data_type="slv_reg_data"))
        self.add_port(
            Port("slv_status_reg", direction="out", data_type="slv_reg_data")
        )
        self.add_port(
            Port(
                "slv_reg_modify", direction="out", data_type="std_logic_vector"
            )
        )
        self.add_port(
            Port(
                "slv_reg_config",
                direction="out",
                data_type="slv_reg_config_table",
            )
        )


# Camera interface definition
## @ingroup automatics_intrep
class CameraInputOV7670(Interface):
    """! @brief Template definition for the Camera interface used by the OmniiVision
    OV7670 camera sensor."""

    INTERFACE_TYPE_NAME = "camera_interface_ov7670"

    INTERFACE_TYPE_NAME = "camera_interface_ov7670"

    def __init__(self):
        super().__init__(self.INTERFACE_TYPE_NAME)
        self.add_port(Port("reset_n", direction="out"))
        self.add_port(Port("powerdown", direction="out"))
        self.add_port(Port("pixclk"))
        self.add_port(Port("frame_valid"))
        self.add_port(Port("line_valid"))
        self.add_port(
            Port(
                "data",
                data_type="std_logic_vector",
                data_width=Port.DataWidth("SENSOR_DATA_WIDTH - 1", "downto", 0),
            )
        )
        self.set_prefix_suffix("sensor_", "")
        self.to_external = True


# AXI Master Memory interface definition:
## @ingroup automatics_intrep
class AXIMasterMemoryInternal(Interface):
    """! @brief Template definition for the AXI Master Memory
    interface used in ASTERICS."""

    INTERFACE_TYPE_NAME = "axi_master_memory_int"

    INTERFACE_TYPE_NAME = "axi_master_memory_int"

    def __init__(self):
        super().__init__(self.INTERFACE_TYPE_NAME)

        # Ports for arbitration mode
        mem_req = Port("mem_req", direction="out", optional=True)
        mem_req.in_entity = False
        self.add_port(mem_req)
        # This port needs to be set to '1' if not connected!
        mem_req_ack = Port("mem_req_ack", optional=True)
        mem_req_ack.overwrite_rule("sink_missing", "set_value('1')")
        mem_req_ack.in_entity = False
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
        self.add_port(
            Port(
                "mem_addr",
                direction="out",
                data_type="std_logic_vector",
                data_width=Port.DataWidth(
                    "MEM_ADDRESS_BIT_WIDTH - 1", "downto", 0
                ),
            )
        )
        self.add_port(
            Port(
                "mem_be",
                direction="out",
                data_type="std_logic_vector",
                data_width=Port.DataWidth(15, "downto", 0),
            )
        )
        self.add_port(
            Port(
                "mem_xfer_length",
                direction="out",
                data_type="std_logic_vector",
                data_width=Port.DataWidth(
                    "BURST_LENGTH_BIT_WIDTH - 1", "downto", 0
                ),
            )
        )
        self.add_port(Port("mem_in_en"))
        self.add_port(
            Port(
                "mem_in_data",
                data_type="std_logic_vector",
                data_width=Port.DataWidth("MEMORY_DATA_WIDTH - 1", "downto", 0),
            )
        )
        self.add_port(Port("mem_out_en"))
        self.add_port(
            Port(
                "mem_out_data",
                direction="out",
                data_type="std_logic_vector",
                data_width=Port.DataWidth("MEMORY_DATA_WIDTH - 1", "downto", 0),
            )
        )
        # This interface usually always connects directly to an AXI Master
        # Unless an Arbiter module manages access to the AXI interface
        self.instantiate_module("AXI_Master")


## @ingroup automatics_intrep
class AXISlaveRegisterInterface(Interface):
    """! @brief Template definition for the AXI Slave Register
    interface used in ASTERICS."""

    INTERFACE_TYPE_NAME = "axi_slave_register_interface"

    INTERFACE_TYPE_NAME = "axi_slave_register_interface"

    def __init__(self):
        super().__init__(self.INTERFACE_TYPE_NAME)
        self.add_port(
            Port(
                "write_data",
                data_type="std_logic_vector",
                data_width=Port.DataWidth(
                    "C_S_AXI_DATA_WIDTH - 1", "downto", 0
                ),
            )
        )
        self.add_port(
            Port(
                "read_data",
                data_type="std_logic_vector",
                direction="out",
                data_width=Port.DataWidth(
                    "C_S_AXI_DATA_WIDTH - 1", "downto", 0
                ),
            )
        )
        self.add_port(Port("write_enable"))
        self.add_port(Port("read_enable"))
        self.add_port(
            Port(
                "write_address",
                data_type="std_logic_vector",
                data_width=Port.DataWidth(
                    "C_S_AXI_ADDR_WIDTH - 1", "downto", 0
                ),
            )
        )
        self.add_port(
            Port(
                "read_address",
                data_type="std_logic_vector",
                data_width=Port.DataWidth(
                    "C_S_AXI_ADDR_WIDTH - 1", "downto", 0
                ),
            )
        )
        self.add_port(
            Port(
                "write_byte_strobe",
                data_type="std_logic_vector",
                data_width=Port.DataWidth(
                    "C_S_AXI_DATA_WIDTH / 8 - 1", "downto", 0
                ),
            )
        )
        self.set_prefix_suffix("axi_slv_reg_", "")


## @ingroup automatics_intrep
class AXISlaveInterface(Interface):
    """! @brief Template definition for the AXI Slave interface used in ASTERICS."""

    INTERFACE_TYPE_NAME = "axi_slave_interface"

    INTERFACE_TYPE_NAME = "axi_slave_interface"

    def __init__(self):
        super().__init__(self.INTERFACE_TYPE_NAME)
        self.add_port(Port("aclk"))
        self.add_port(Port("areset_n"))
        self.add_port(
            Port(
                "awaddr",
                data_type="std_logic_vector",
                data_width=Port.DataWidth(
                    "C_S_AXI_ADDR_WIDTH - 1", "downto", 0
                ),
            )
        )
        self.add_port(
            Port(
                "awprot",
                data_type="std_logic_vector",
                data_width=Port.DataWidth(2, "downto", 0),
            )
        )
        self.add_port(Port("awvalid"))
        self.add_port(Port("awready", direction="out"))
        self.add_port(
            Port(
                "wdata",
                data_type="std_logic_vector",
                data_width=Port.DataWidth(
                    "C_S_AXI_DATA_WIDTH - 1", "downto", 0
                ),
            )
        )
        self.add_port(
            Port(
                "wstrb",
                data_type="std_logic_vector",
                data_width=Port.DataWidth(
                    "C_S_AXI_DATA_WIDTH / 8 - 1", "downto", 0
                ),
            )
        )
        self.add_port(Port("wvalid"))
        self.add_port(Port("wready", direction="out"))
        self.add_port(
            Port(
                "bresp",
                direction="out",
                data_type="std_logic_vector",
                data_width=Port.DataWidth(1, "downto", 0),
            )
        )
        self.add_port(Port("bvalid", direction="out"))
        self.add_port(
            Port(
                "araddr",
                data_type="std_logic_vector",
                data_width=Port.DataWidth(
                    "C_S_AXI_ADDR_WIDTH - 1", "downto", 0
                ),
            )
        )
        self.add_port(
            Port(
                "arprot",
                data_type="std_logic_vector",
                data_width=Port.DataWidth(2, "downto", 0),
            )
        )
        self.add_port(Port("arvalid"))
        self.add_port(Port("arready", direction="out"))
        self.add_port(
            Port(
                "rdata",
                direction="out",
                data_type="std_logic_vector",
                data_width=Port.DataWidth(
                    "C_S_AXI_DATA_WIDTH - 1", "downto", 0
                ),
            )
        )
        self.add_port(
            Port(
                "rresp",
                data_type="std_logic_vector",
                data_width=Port.DataWidth(1, "downto", 0),
                direction="out",
            )
        )
        self.add_port(Port("rvalid", direction="out"))
        self.add_port(Port("rready"))
        self.set_prefix_suffix("s_axi_", "")
        self.to_external = True


## @ingroup automatics_intrep
class AsMain(AsModuleGroup):
    """! @brief Template for the module group AsMain in which all AsModules are instantiated."""

    def __init__(self, top, chain):
        super().__init__("as_main", top, [])
        self.entity_name = "as_main_impl"
        self.name = "as_main"
        self.chain = chain
        self.description = as_vhdl_static.AS_MAIN_DESC
        # Setup default reset signal and port and default AXI Slave Interface

        # Need to remove reset port: these are non-standard for as_main
        self.standard_ports.clear()

        self.define_port("reset_n")
        self.reset_signal = self.define_signal(
            "reset", fixed_value="not reset_n"
        )
        self.define_port("clk")

        axi_slave_reg_inter = AXISlaveRegisterInterface()
        axi_slave_reg_inter.instantiate_module("AXI_Slave")
        self.add_interface(axi_slave_reg_inter)

        # reset = GlueSignal("reset")
        # reset.assign_to(self)
        # self.signals = [reset]
        self.add_generic(Generic(name="C_S_AXI_ADDR_WIDTH", default_value=32))
        self.add_generic(Generic(name="C_S_AXI_DATA_WIDTH", default_value=32))
        self.dependencies = ["as_regmgr"]
        self.static_code["body"].append(as_vhdl_static.AS_MAIN_ARCH_BODY_STATIC)

        def as_main_dynamic_code(chain, code_dict: dict):
            # code_dict format: lists "signals" and "body"

            # Generate a hexadecimal string storing the ASTERICS base address:
            # Calculate the width in hexadecimal characters of the base address
            length = int(
                2 ** ceil(log2(chain.asterics_base_addr.bit_length())) / 4
            )
            base_addr_str = 'X"{addr:0{length}X}"'.format(
                length=length, addr=chain.asterics_base_addr
            )
            # Generate some required signals and constants for register management:
            code_dict["signals"].extend(
                [
                    "\n  -- Register interface constants and signals:",
                    "  constant c_asterics_base_addr : unsigned({} downto 0) := {};".format(
                        length * 4 - 1, base_addr_str
                    ),
                    "  constant c_slave_reg_addr_width : integer := {};".format(
                        chain.mod_addr_width + chain.reg_addr_width
                    ),
                    "  constant c_module_addr_width : integer := {};".format(
                        chain.mod_addr_width
                    ),
                    "  constant c_reg_addr_width : integer := {};".format(
                        chain.reg_addr_width
                    ),
                    "  constant c_reg_if_count : integer := {};".format(
                        sum(
                            [
                                len(mod.register_ifs)
                                for mod in ittls.chain(
                                    chain.modules, chain.pipelines
                                )
                            ]
                        )
                    ),
                    ("  signal read_module_addr : integer;"),
                    (
                        "  signal sw_address : std_logic_vector"
                        "(c_slave_reg_addr_width - 1 downto 0);"
                    ),
                    (
                        "  signal mod_read_data_arr : slv_reg_data"
                        "(0 to c_reg_if_count - 1);"
                    ),
                ]
            )

            # Generate the register manager instantiations:
            for addr in chain.address_space:  # For each address space
                # Grab the register manager reference
                regif = chain.address_space[addr]
                code_dict["signals"].append(
                    "  -- Module register base address: 16#{:8X}#".format(
                        regif.base_address
                    )
                )
                code_dict["signals"].append(
                    "  constant c_{}_regif_num{} : integer := {};".format(
                        regif.parent.name, regif.name_suffix, regif.regif_num
                    )
                )

        self.dynamic_code_generators.append(as_main_dynamic_code)


## @ingroup automatics_intrep
class AsTop(AsModuleGroup):
    """! @brief Template for the ASTERICS processing chain toplevel module group.
    The AsMain module group and AXI interfaces are instantiated here."""

    def __init__(self, chain):
        super().__init__("asterics", None, [])
        self.entity_name = "asterics"
        self.chain = chain
        self.description = as_vhdl_static.AS_TOP_DESC

        # Remove reset port: non-standard for asterics.vhd
        self.standard_ports.clear()

        self.define_signal("clk", fixed_value="slave_s_axi_aclk")
        self.define_signal("reset_n", fixed_value="slave_s_axi_aresetn")
        self.dependencies = ["as_main"]
        self.static_code["body"].append(as_vhdl_static.AS_TOP_ARCH_BODY_STATIC)
