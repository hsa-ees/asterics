----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_reorder
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Matthias Struwe
--
-- Modified:       
--
-- Description:    
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
--! @file  as_reorder.vhd
--! @brief reorders the pixel.
----------------------------------------------------------------------------------


library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use work.helpers.all;


entity as_reorder is
  generic (
    DIN_WIDTH  : integer := 32;
    DOUT_WIDTH : integer := 32
  );
  port (
    Clk         : in  std_logic;
    Reset       : in  std_logic;

    -- IN ports from previous module:
    VSYNC_IN    : in  std_logic;
    HSYNC_IN    : in  std_logic;
    STROBE_IN   : in  std_logic;
    DATA_IN     : in  std_logic_vector(DIN_WIDTH-1 downto 0);

    SYNC_ERROR_IN   : in  std_logic;
    DATA_ERROR_IN  : in  std_logic;
    STALL_OUT       : out std_logic;

    -- OUT ports to next module:
    VSYNC_OUT   : out std_logic;
    HSYNC_OUT   : out std_logic;
    STROBE_OUT  : out std_logic;
    DATA_OUT    : out std_logic_vector(DOUT_WIDTH-1 downto 0);
    
    SYNC_ERROR_OUT  : out std_logic;
    DATA_ERROR_OUT : out std_logic;
    STALL_IN        : in  std_logic
  );
end as_reorder;

architecture RTL of as_reorder is

begin

VSYNC_OUT <= VSYNC_IN;

 HSYNC_OUT  <= HSYNC_IN;
    STROBE_OUT  <= STROBE_IN;
    DATA_OUT(7 downto 0)    <= DATA_IN(31 downto 24);
    DATA_OUT(15 downto 8)    <= DATA_IN(23 downto 16);
    DATA_OUT(23 downto 16)    <= DATA_IN(15 downto 8);
    DATA_OUT(31 downto 24)    <= DATA_IN(7 downto 0);
    
    SYNC_ERROR_OUT  <= SYNC_ERROR_IN;
    DATA_ERROR_OUT <= DATA_ERROR_IN;
    STALL_OUT         <= STALL_IN;


end RTL;
