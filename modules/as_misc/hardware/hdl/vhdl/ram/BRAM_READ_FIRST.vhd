----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         AS_AVG_FILTER
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Markus Bihler
-- Modified:       
--
-- Description:    Implements BRAM which is performs a read operation before a 
--                 write operation.
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
--! @file  BRAM_READ_FIRST.vhd
--! @brief Implements BRAM which is performs a read operation before a 
--         write operation.
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

use work.helpers.all;

entity BRAM_READ_FIRST is
    generic ( gen_data_width : integer := 8;   -- width of each ram cell
            gen_data_depth : integer := 1024; -- number of ram cells
            gen_ram_style  : string  := "block" -- distributed | block
           );
    port (CLK       : in std_logic;
        EN        : in std_logic;
        WE      : in std_logic;
        ADDR    : in std_logic_vector(log2_ceil(gen_data_depth)-1 downto 0);
        DI      : in std_logic_vector(gen_data_width-1 downto 0);
        DO      : out std_logic_vector(gen_data_width-1 downto 0)
       );   
end BRAM_READ_FIRST;

architecture RTL of BRAM_READ_FIRST is
  type ramType is array (0 to gen_data_depth-1) of std_logic_vector(gen_data_width-1 downto 0);
  signal ram : ramType := (others => (others => '0'));
  
  attribute ram_style: string;
  attribute ram_style of ram : signal is gen_ram_style;
begin
  -- PORT A
  process (CLK)
  begin
    if rising_edge(CLK) then
      if EN = '1' then
        DO <= ram(to_integer(unsigned(ADDR))); -- read first (latch)
        if WE = '1' then
          ram(to_integer(unsigned(ADDR))) <= DI;
        end if;
      end if;
    end if;
  end process;
end RTL;

