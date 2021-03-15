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
Contains VHDL Code strings for use in Automatics.
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
# @ingroup automatics_generate
# @author Philip Manke
# @brief Contains VHDL Code strings for use in Automatics.
# -----------------------------------------------------------------------------

##
# @addtogroup automatics_generate
# @{

HEADER = (
    "----------------------------------------------------------------------------------\n"
    "--  This file is part of the ASTERICS Framework.                                  \n"
    "--  (C) 2020 Hochschule Augsburg, University of Applied Sciences                  \n"
    "----------------------------------------------------------------------------------\n"
    "-- Entity:         {entity_name}                                                  \n"
    "--                                                                                \n"
    "-- Company:        Efficient Embedded Systems Group at                            \n"
    "--                 University of Applied Sciences, Augsburg, Germany              \n"
    "-- Author:         Automatics (ASTERICS processing chain generator)               \n"
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
    "----------------------------------------------------------------------------------\n"
)

LIBS_IEEE = (
    "library ieee;\n"
    "use ieee.std_logic_1164.all;\n"
    "use ieee.numeric_std.all;\n\n"
)

LIBS_ASTERICS = "library asterics;\n"

AS_MAIN_DESC = (
    "This file instanciates and connects all AsModules of this"
    " processing system."
)

AS_TOP_DESC = (
    "Toplevel VHDL file for the ASTERICS IP-Core. Instanciates "
    "AXI interfaces and as_main."
)

ASSIGNMENT_TEMPL = "  {} <= {};"

AS_MAIN_ARCH_BODY_STATIC = (
    # "  reset <= not reset_n;\n"
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
    "  end process;\n"
)

AS_TOP_ARCH_BODY_STATIC = (
    # "  -- Get clock from AXI Slave Interface:\n"
    # "  clk <= slave_s_axi_aclk;\n"
    # "  reset_n <= slave_s_axi_aresetn;\n"
    "  \n"
)

MODULE_INSTANTIATION_TEMPLATE = (
    "  \n"
    "  -- Instantiate module {module_name}\n"
    "  {module_name} :{entity_keyword} {entity_name}\n"
    "{generic_map}"
    "{port_map}"
)

COMPONENT_DECLARATION_TEMPLATE = (
    "  -- Declare {module_name}\n"
    "  component {entity_name} is\n"
    "  {generic_list}"
    "  {port_list}"
    "  end component;\n"
)


REGMGR_BASEADDR_VAL = "c_{}_regif_num"

REGMGR_SW_DATA_OUT_TARGET = "mod_read_data_arr(c_{}_regif_num{})"

REGMGR_REGISTER_CONFIG_NAMES = {
    "none": "AS_REG_NONE",
    "control": "AS_REG_CONTROL",
    "status": "AS_REG_STATUS",
    "both": "AS_REG_BOTH",
}

PIPE_WINDOW_TYPE = "t_generic_window"
PIPE_LINE_TYPE = "t_generic_line"


CLOCKED_PROCESS = (
    "\n  -- Assigning window signals:\n"
    "  assign_windows_p : process(clk) is\n"
    "  begin\n"
    "    if rising_edge(clk) then\n"
    "      if reset = '1' then\n"
    "{resets}\n"
    "      else\n"
    "{in_process}\n"
    "      end if;\n"
    "    end if;\n"
    "  end process;\n"
)

CLOCKED_PROCESS_WITH_VARIABLES = (
    "\n  -- Assigning window signals:\n"
    "  assign_windows_p : process(clk) is\n"
    "{variables}\n"
    "  begin\n"
    "    if rising_edge(clk) then\n"
    "      if reset = '1' then\n"
    "{resets}\n"
    "      else\n"
    "{in_process}\n"
    "      end if;\n"
    "    end if;\n"
    "  end process;\n"
)

PROCESS_WITH_VARIABLES = (
    "\n  -- Assigning window signals:\n"
    "  assign_windows_p : process({sens}) is\n"
    "{variables}\n"
    "  begin\n"
    "{in_process}\n"
    "  end process;\n"
)

LINE_ARRAY_TO_WINDOW_FUNCTION = (
    "  function f_line_array_{width}_{bits}_to_generic_window("
    "constant line_array : in t_generic_line_array_{width}_{bits}) "
    "return t_generic_window is\n"
    "  variable gwindow_out : t_generic_window("
    "0 to {width} - 1, line_array'range, {bits} - 1 downto 0);\n"
    "  begin\n"
    "    for x in gwindow_out'range(1) loop\n"
    "      for y in gwindow_out'range(2) loop\n"
    "        for b in gwindow_out'range(3) loop\n"
    "          gwindow_out(x, y, b) := line_array(y)(x, b);\n"
    "        end loop;\n"
    "      end loop;\n"
    "    end loop;\n"
    "    return gwindow_out;\n"
    "  end f_line_array_{width}_{bits}_to_generic_window;"
)

RESET_WINDOW_SIGNAL = (
    "        {window_sig} <= (others => (others => (others => '0')));"
)

LINE_SIGNAL_TO_LINE_ARRAY = (
    "        line_array_{window}_{width}_{bit_width}({row_idx}) := "
    "f_cut_vectors_of_generic_line("
    "f_get_part_of_generic_line({line_signal}, 0, {width})"
    ", {start_bit_idx}, {bit_width});"
)

LINE_ARRAY_VARIABLE_DECLARATION = (
    "  variable line_array_{window}_{width}_{bits} : "
    "t_generic_line_array_{width}_{bits}(0 to {height} - 1);"
)

LINE_ARRAY_TYPE_DECLARATION = (
    "  type t_generic_line_array_{width}_{bits} is array(natural range<>)"
    " of t_generic_line(0 to {width} - 1, {bits} - 1 downto 0);"
)

WINDOW_FROM_LINE_ARRAY = (
    "        {window} <= f_line_array_{width}_{bits}_to_generic_window("
    "line_array_{window}_{width}_{bits});"
)

## @}
