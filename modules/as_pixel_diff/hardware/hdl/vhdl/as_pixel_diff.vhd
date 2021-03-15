----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- File:           as_pixel_diff.vhd
-- Entity:         as_pixel_diff
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Michael Schaeferling
--
-- Modified:       2019-04-17 by Philip Manke: Update for use with ASTERICS
--
-- Description:    Compute the absolute difference between two pixel streams
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
--! @file as_pixel_diff.vhd
--! @brief Compute the absolute difference between two pixel streams
--! @addtogroup asterics_modules
--! @{
--! @defgroup as_pixel_diff as_pixel_diff: Subtract two AsStreams
--! Subtract an AsStream from another stream.
--! Returns the absolute difference in an output AsStream.
--! @}
----------------------------------------------------------------------------------

--! @addtogroup as_pixel_diff
--! @{

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;


entity as_pixel_diff is
  generic (
    DATA_WIDTH  : integer := 8
  );
  port (
    clk         : in  std_logic;
    reset       : in  std_logic;
    ready       : out std_logic;

    -- IN ports 0
    vsync_in_0    : in  std_logic;
    hsync_in_0    : in  std_logic;
    strobe_in_0   : in  std_logic;
    data_in_0     : in  std_logic_vector(DATA_WIDTH-1 downto 0);
    xres_in_0     : in  std_logic_vector(11 downto 0);
    yres_in_0     : in  std_logic_vector(11 downto 0);
    
    sync_error_in_0  : in  std_logic;
    data_error_in_0 : in  std_logic;
    stall_out_0      : out std_logic;

    -- IN ports 1
    vsync_in_1    : in  std_logic;
    hsync_in_1    : in  std_logic;
    strobe_in_1   : in  std_logic;
    data_in_1     : in  std_logic_vector(DATA_WIDTH-1 downto 0);
    xres_in_1     : in  std_logic_vector(11 downto 0);
    yres_in_1     : in  std_logic_vector(11 downto 0);
    
    sync_error_in_1  : in  std_logic;
    data_error_in_1 : in  std_logic;
    stall_out_1      : out std_logic;

    -- OUT ports
    vsync_out   : out std_logic;
    hsync_out   : out std_logic;
    strobe_out  : out std_logic;
    data_out    : out std_logic_vector(DATA_WIDTH-1 downto 0);
    xres_out    : out std_logic_vector(11 downto 0);
    yres_out    : out std_logic_vector(11 downto 0);
    
    sync_error_out  : out std_logic;
    data_error_out : out std_logic;
    stall_in        : in  std_logic
    
  );
end as_pixel_diff;

--! @}

architecture RTL of as_pixel_diff is
begin

STALL_OUT_0 <= STALL_IN;
STALL_OUT_1 <= STALL_IN;

process (Clk)
begin
  if( Clk'event and Clk = '1' ) then
    if( Reset = '1' ) then
      null;
    else

      STROBE_OUT <= '0';

      if ((STROBE_IN_0 = '1') and (STROBE_IN_1 = '1')) then
      
        VSYNC_OUT  <= VSYNC_IN_0;
        HSYNC_OUT  <= HSYNC_IN_0;
        STROBE_OUT <= STROBE_IN_0;
        DATA_OUT   <= std_logic_vector(abs(signed(DATA_IN_0) - signed(DATA_IN_1)));
        XRES_OUT   <= XRES_IN_0;
        YRES_OUT   <= YRES_IN_0;
        SYNC_ERROR_OUT <= SYNC_ERROR_IN_0 or SYNC_ERROR_IN_1;
        DATA_ERROR_OUT <= DATA_ERROR_IN_0 or DATA_ERROR_IN_1;
        
      end if;

    end if;
  end if;

end process;

end RTL;
