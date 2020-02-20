# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_regmgr_spec.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author: Philip Manke

Description:
Python module used by as_automatics used to build the generators internal model
of the ASTERICS support module as_regmgr.
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
# @file as_regmgr_spec.py
# @author Philip Manke
# @brief Specifics for as_regmgr used by as_automatics
# -----------------------------------------------------------------------------

from as_automatics_module import AsModule
from as_automatics_interface import Interface
from as_automatics_port import Port
import as_automatics_vhdl_static as vstatic

class SWRegInterface(Interface):
    def __init__(self):
        super().__init__("sw_reg_interface")
        sw_addr = Port("sw_address", data_type="std_logic_vector")
        sw_addr.overwrite_rule("sink_missing", "set_value(sw_address)")
        self.add_port(sw_addr)

        self.add_port(Port("sw_data_out", data_type="std_logic_vector",
                           direction="out"))

        sw_data_in = Port("sw_data_in", data_type="std_logic_vector")
        sw_data_in.overwrite_rule("sink_missing",
                                  "set_value(axi_slv_reg_write_data)")
        self.add_port(sw_data_in)
        sw_data_out_ena = Port("sw_data_out_ena")
        sw_data_out_ena.overwrite_rule(
                "sink_missing", "set_value(axi_slv_reg_read_enable)")
        self.add_port(sw_data_out_ena)
        sw_data_in_ena = Port("sw_data_in_ena")
        sw_data_in_ena.overwrite_rule(
                "sink_missing", "set_value(axi_slv_reg_write_enable)")
        self.add_port(sw_data_in_ena)
        sw_byte_mask = Port("sw_byte_mask", data_type="std_logic_vector")
        sw_byte_mask.overwrite_rule(
                "sink_missing", "set_value(axi_slv_reg_write_byte_strobe)")
        self.add_port(sw_byte_mask)
        


def get_module_instance(module_dir: str) -> AsModule:
    module = AsModule()
    module.add_local_interface_template(SWRegInterface())

    toplevel_file = "hardware/hdl/vhdl/register_interface/as_regmgr.vhd"
    module.files = [("hardware/hdl/vhdl/register_interface/"
                     "as_generic_regslice.vhd")]
    module.dependencies = ["helpers"]

    # as_automatics now automatically parses the toplevel file and discovers
    # ports, generics, existing interfaces and register interfaces
    module.discover_module("{mdir}/{toplevel}"
                           .format(mdir=module_dir, toplevel=toplevel_file))
    

    # Configuration method. This method is automatically executed
    # by Automatics during the connection process, only if the module was
    # automatically instantiated.
    # This way we can access information only available at runtime.
    def auto_inst_config(mod, inst_from):
        # inst_from is the module that automatically instantiated this module
        # mod is the instance of this module that was automatically instantiated
        mod.set_generic_value("REG_ADDR_WIDTH", "c_slave_reg_addr_width")
        mod.set_generic_value("REG_DATA_WIDTH", "C_S_AXI_DATA_WIDTH")
        mod.set_generic_value("MODULE_ADDR_WIDTH", "c_module_addr_width")
        base_addr_generic = \
            vstatic.REGMGR_BASEADDR_VAL.format(inst_from.name)
        mod.set_generic_value("MODULE_BASEADDR", base_addr_generic)
        regmgr_count = "_" + mod.name[-1] if mod.name[-1].isdigit() else ""
        target = vstatic.REGMGR_SW_DATA_OUT_TARGET \
                            .format(inst_from.name, regmgr_count)
        mod.set_port_fixed_value("sw_data_out", target)
        if not regmgr_count:
            regif = inst_from.register_ifs[0]
        else:
            regif = inst_from.register_ifs[int(regmgr_count.strip("_"))]
        mod.set_generic_value("REG_COUNT", str(regif.reg_count))
        mod.get_interface("out", if_type="slv_reg_interface") \
                .to_external = False

    # !Important! Assign the configuration function to this module instance
    module.auto_inst_config = auto_inst_config
    # Return the module instance to Automatics
    return module
