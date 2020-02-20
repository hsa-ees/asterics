# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_automatics_register.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Contains VHDL Code strings for use in as_automatics.
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
# @file as_automatics_register.py
# @author Philip Manke
# @brief Contains VHDL Code strings for use in as_automatics.
# -----------------------------------------------------------------------------


HEADER = (
    "----------------------------------------------------------------------------------\n"
    "--  This file is part of the ASTERICS Framework.                                  \n"
    "--  (C) 2019 Hochschule Augsburg, University of Applied Sciences             \n"
    "----------------------------------------------------------------------------------\n"
    "-- Entity:         {entity_name}                                                  \n"
    "--                                                                                \n"
    "-- Company:        Efficient Embedded Systems Group at                            \n"
    "--                 University of Applied Sciences, Augsburg, Germany              \n"
    "-- Author:         as_automatics (automated processing chain generator)           \n"
    "--                                                                                \n"
    "-- Modified:                                                                      \n"
    "--                                                                                \n"
    "-- Description: {longdesc}                                                        \n"
    "----------------------------------------------------------------------------------\n"
    "--  This program is free software; you can redistribute it and/or                 \n"
    "--  modify it under the terms of the GNU Lesser General Public                    \n"
    "--  License as published by the Free Software Foundation; either                  \n"
    "--  version 3 of the License, or (at your option) any later version.              \n"
    "--                                                                                \n"
    "--  This program is distributed in the hope that it will be useful,               \n"
    "--  but WITHOUT ANY WARRANTY; without even the implied warranty of                \n"
    "--  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU             \n"
    "--  Lesser General Public License for more details.                               \n"
    "--                                                                                \n"
    "--  You should have received a copy of the GNU Lesser General Public License      \n"
    "--  along with this program; if not, see <http://www.gnu.org/licenses/>           \n"
    "--  or write to the Free Software Foundation, Inc.,                               \n"
    "--  51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.                 \n"
    "----------------------------------------------------------------------------------\n"
    "--! @file  {filename}                                                             \n"
    "--! @brief {briefdesc}                                                            \n"
    "----------------------------------------------------------------------------------\n")

LIBS_IEEE = ("library ieee;\n"
             "use ieee.std_logic_1164.all;\n"
             "use ieee.numeric_std.all;\n\n")
LIBS_ASTERICS = ("library asterics;\n"
                 "use asterics.helpers.all;\n")

AS_MAIN_FILENAME = "as_main.vhd"
AS_MAIN_ENTITY = "as_main"
AS_MAIN_DESC = ("This file instanciates and connects all AsModules of this"
                " processing system.")

AS_TOP_FILENAME = "asterics.vhd"
AS_TOP_ENTITY = "asterics"
AS_TOP_DESC = ("Toplevel VHDL file for the ASTERICS IP-Core. Instanciates "
               "AXI interfaces and as_main.")

ASSIGNMENT_TEMPL = "  {} <= {};\n"

AS_MAIN_ARCH_BODY_STATIC = (
    #"  reset <= not reset_n;\n"
    "  -- Extract the module address from the AXI read address\n"
    "  read_module_addr <= to_integer(unsigned(\n"
    "    axi_slv_reg_read_address(c_slave_reg_addr_width + 1 downto c_reg_addr_width + 2)));\n"
    "\n"
    "  -- Connect the read data out port of the register manager of the addressed module\n"
    "  read_data_mux : process(mod_read_data_arr, read_module_addr, reset_n)\n"
    "  begin\n"
    "      if reset_n = '0' then\n"
    "          axi_slv_reg_read_data <= (others => '0');\n"
    "      else\n"
    "          if read_module_addr < c_reg_if_count and read_module_addr >= 0 then\n"
    "              axi_slv_reg_read_data <= mod_read_data_arr(read_module_addr);\n"
    "          else\n"
    "              axi_slv_reg_read_data <= (others => '0');\n"
    "          end if;\n"
    "      end if;\n"
    "  end process;\n"
    "\n"
    "  -- Select between read and write address of the AXI interface depending on the read/write enable bits\n"
    "  -- The register managers can only handle a single read/write per clock cycle\n"
    "  -- Write requests have priority\n"
    "  sw_addr_mux:\n"
    "  process(axi_slv_reg_write_address, axi_slv_reg_read_address, axi_slv_reg_write_enable, axi_slv_reg_read_enable)\n"
    "  begin\n"
    "    sw_address <= (others => '0');\n"
    "    -- Disregarding lowest two bits to account for byte addressing on 32 bit registers\n"
    "    if axi_slv_reg_write_enable = '1' then\n"
    "        sw_address <= axi_slv_reg_write_address(c_slave_reg_addr_width + 1 downto 2);\n"
    "    elsif axi_slv_reg_read_enable = '1' then\n"
    "        sw_address <= axi_slv_reg_read_address(c_slave_reg_addr_width + 1 downto 2);\n"
    "    else\n"
    "        sw_address <= (others => '0');\n"
    "    end if;\n"
    "  end process;\n")

AS_TOP_ARCH_BODY_STATIC = (
    #"  -- Get clock from AXI Slave Interface:\n"
    #"  clk <= slave_s_axi_aclk;\n"
    #"  reset_n <= slave_s_axi_aresetn;\n"
    "  \n"
)

REGMGR_BASEADDR_VAL = "c_{}_regif_num"
REGMGR_SW_DATA_OUT_TARGET = "mod_read_data_arr(c_{}_regif_num{})"

PIPE_WINDOW_TYPE = "t_generic_window"
