----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         DUAL_BRAM_READ_WRITE
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Markus Bihler
--
-- Modified:       
--
-- Description:    Implements BRAM which can perform read and write operations 
--                 simultaneously.
----------------------------------------------------------------------------------
--  This program is free software; you can redistribute it and/or
--  modify it under the terms of the GNU Lesser General Public
--  License as published by the Free Software Foundation; either
--  version 3 of the License, or (at your option) any later version.
--  
--  This program is distributed in the hope that it will be useful,
--  but WITHOUT ANY WARRANTY; without even the implied warranty of
--  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
--  Lesser General Public License for more details.
--  
--  You should have received a copy of the GNU Lesser General Public License
--  along with this program; if not, see <http://www.gnu.org/licenses/>
--  or write to the Free Software Foundation, Inc.,
--  51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
----------------------------------------------------------------------------------
--! @file  DUAL_BRAM_READ_WRITE.vhd
--! @brief Implements BRAM which can perform read and write operations 
--         simultaneously.
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

use work.helpers.all;

entity DUAL_BRAM_READ_WRITE is
    generic ( gen_data_width : integer := 8;   -- width of each ram cell
            gen_data_depth : integer := 1024; -- number of ram cells
            gen_ram_style  : string  := "block" -- distributed | block
           );
    port (CLK_A         : in std_logic;
        CLK_B       : in std_logic;
        WE_A      : in std_logic;
        RE_B      : in std_logic;
        ADDR_A    : in std_logic_vector(log2_ceil(gen_data_depth)-1 downto 0);
        ADDR_B    : in std_logic_vector(log2_ceil(gen_data_depth)-1 downto 0);
        DI_A      : in std_logic_vector(gen_data_width-1 downto 0);
        DO_B      : out std_logic_vector(gen_data_width-1 downto 0)
       );   
end DUAL_BRAM_READ_WRITE;

architecture RTL of DUAL_BRAM_READ_WRITE is
  type ramType is array (0 to gen_data_depth-1) of std_logic_vector(gen_data_width-1 downto 0);
  shared variable ram : ramType := (others => (others => '0'));
  
begin

  assert gen_ram_style = "auto" or gen_ram_style = "block" or gen_ram_style = "distributed"
    report "Generic gen_ram_style must be auto | block | distributed"
    severity failure;
    
  -- PORT A WRITE
  process (CLK_A)
  begin
    if rising_edge(CLK_A) then
      if WE_A = '1' then
        ram(to_integer(unsigned(ADDR_A))) := DI_A;
      end if;
    end if;
  end process;
  
  -- PORT B READ
  process (CLK_B)
  begin
    if rising_edge(CLK_B) then
      if RE_B = '1' then
        DO_B <= ram(to_integer(unsigned(ADDR_B)));
      end if;
    end if;
  end process;

end RTL;

