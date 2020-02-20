----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         ram
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Markus Bihler
--
-- Modified:       
--
-- Description:    Implements BRAM for storing data.
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
--! @file  ram.vhd
--! @brief Implements BRAM for storing data.
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity ram is
    generic ( 
        DATA_WIDTH : integer;
        ADDR_WIDTH : integer
       );
    port (
        CLK       : in  std_logic;
        WR_EN     : in  std_logic;
        WR_ADDR   : in  std_logic_vector(ADDR_WIDTH-1 downto 0);
        RD_ADDR   : in  std_logic_vector(ADDR_WIDTH-1 downto 0);
        DIN       : in  std_logic_vector(DATA_WIDTH-1 downto 0);
        DOUT      : out std_logic_vector(DATA_WIDTH-1 downto 0)
       );   
end ram;

architecture RTL of ram is

  
begin
  process (CLK)
    constant ram_size  : natural := 2**ADDR_WIDTH;
    type ramType is array (0 to (ram_size)-1) of std_logic_vector(DATA_WIDTH-1 downto 0);
    variable ram_array : ramType := (others => (others => '0'));
  begin
    if rising_edge(CLK) then
      
      -- write:
      if WR_EN = '1' then
        ram_array(to_integer(unsigned(WR_ADDR))) := DIN;
      end if;
      
      -- read:
      DOUT <= ram_array(to_integer(unsigned(RD_ADDR)));
      
    end if;
  end process;
  
  
  
end RTL;

