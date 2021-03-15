----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         DUAL_BRAM_READ_FIRST
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Markus Bihler
--
-- Modified:       
--
-- Description:    Implements a dual-ported BRAM which performs read operations 
--                 before write operations.
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
--! @file  DUAL_BRAM_READ_FIRST.vhd
--! @brief Dual-port BRAM with read-first behaviour.
--! @addtogroup asterics_helpers
--! @{
--! @defgroup DUAL_BRAM_READ_FIRST DUAL_BRAM_READ_FIRST: Read-first Dual-Port BRAM
--! Implements a dual-ported BRAM which performs read operations before write operations.
--! @}
----------------------------------------------------------------------------------

--! @addtogroup DUAL_BRAM_READ_FIRST
--! @{

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

use work.helpers.all;

entity DUAL_BRAM_READ_FIRST is
    generic ( 
        gen_data_width : integer := 8;   -- width of each ram cell
        gen_data_depth : integer := 1024; -- number of ram cells
        gen_ram_style  : string  := "block" -- distributed | block
    );
    port (
        CLK_A     : in std_logic;
        CLK_B     : in std_logic;
        EN_A      : in std_logic;
        EN_B      : in std_logic;
        WE_A      : in std_logic;
        WE_B      : in std_logic;
        ADDR_A    : in std_logic_vector(log2_ceil(gen_data_depth)-1 downto 0);
        ADDR_B    : in std_logic_vector(log2_ceil(gen_data_depth)-1 downto 0);
        DI_A      : in std_logic_vector(gen_data_width-1 downto 0);
        DI_B      : in std_logic_vector(gen_data_width-1 downto 0);
        DO_A      : out std_logic_vector(gen_data_width-1 downto 0);
        DO_B      : out std_logic_vector(gen_data_width-1 downto 0)
       );   
end DUAL_BRAM_READ_FIRST;

--! @}

architecture RTL of DUAL_BRAM_READ_FIRST is
  
begin

  process (CLK_A, CLK_B)
    type mem is array (0 to gen_data_depth-1) of std_logic_vector(gen_data_width-1 downto 0);
    variable ram : mem := (others=>(others=>'0'));
  begin
    -- PORT A
    if rising_edge(CLK_A) then
      if EN_A = '1' then
        DO_A <= ram(to_integer(unsigned(ADDR_A))); -- read first (latch)
        if WE_A = '1' then
          ram(to_integer(unsigned(ADDR_A))) := DI_A;
        end if;
      end if;
    end if;

    -- PORT B
    if rising_edge(CLK_B) then
      if EN_B = '1' then
        DO_B <= ram(to_integer(unsigned(ADDR_B))); -- read first (latch)
        if WE_B = '1' then
          ram(to_integer(unsigned(ADDR_B))) := DI_B;
        end if;
      end if;
    end if;
  end process;

end RTL;
