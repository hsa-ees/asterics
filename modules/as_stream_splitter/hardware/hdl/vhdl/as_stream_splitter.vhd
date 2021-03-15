----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- File:           as_stream_splitter.vhd
-- Entity:         as_stream_splitter
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Author:         Matthias Struwe
--
-- Modified:       Philip Manke: Make data width generic more generic
--
-- Description:    This module outputs the same input as_stream on its two ouput streams.
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
--! @file as_stream_splitter.vhd
--! @brief This module outputs the same input as_stream on its two ouput streams.
--! @addtogroup asterics_modules
--! @{
--! @defgroup as_stream_splitter as_stream_splitter: AsStream Duplicator
--! This module duplicates an AsStream interface, outputting the same data on
--! 2 output streams.
--! @}
----------------------------------------------------------------------------------

--! @addtogroup as_stream_splitter
--! @{

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;


entity as_stream_splitter is
  generic (
    DATA_WIDTH  : integer := 8
  );
  port (
    clk         : in  std_logic;
    reset       : in  std_logic;
    ready       : out std_logic;

    -- in ports
    vsync_in    : in  std_logic;
    hsync_in    : in  std_logic;
    strobe_in   : in  std_logic;
    data_in     : in  std_logic_vector(DATA_WIDTH-1 downto 0);
    xres_in     : in  std_logic_vector(11 downto 0);
    yres_in     : in  std_logic_vector(11 downto 0);
    
    sync_error_in  : in  std_logic;
    pixel_error_in : in  std_logic;
    stall_out      : out std_logic;

    -- out ports
    vsync_out_0   : out std_logic;
    hsync_out_0   : out std_logic;
    strobe_out_0  : out std_logic;
    data_out_0    : out std_logic_vector(DATA_WIDTH-1 downto 0);
    xres_out_0    : out std_logic_vector(11 downto 0);
    yres_out_0    : out std_logic_vector(11 downto 0);
    
    sync_error_out_0  : out std_logic;
    pixel_error_out_0 : out std_logic;
    stall_in_0        : in  std_logic;

    vsync_out_1  : out std_logic;
    hsync_out_1  : out std_logic;
    strobe_out_1 : out std_logic;
    data_out_1   : out std_logic_vector(DATA_WIDTH-1 downto 0);
    xres_out_1   : out std_logic_vector(11 downto 0);
    yres_out_1   : out std_logic_vector(11 downto 0);
    
    sync_error_out_1 : out std_logic;
    pixel_error_out_1: out std_logic;
    stall_in_1       : in  std_logic

  );
end as_stream_splitter;

--! @}

architecture RTL of as_stream_splitter is

begin

 -- Stream out 0
vsync_out_0  <= vsync_in;
hsync_out_0  <= hsync_in;
strobe_out_0 <= strobe_in;

data_out_0 <= data_in;

xres_out_0   <= xres_in;
yres_out_0   <= yres_in;

sync_error_out_0 <= sync_error_in;
pixel_error_out_0 <= pixel_error_in;


 -- Stream out 1
vsync_out_1 <= vsync_in;
hsync_out_1 <= hsync_in;
strobe_out_1 <= strobe_in;

data_out_1 <= data_in;

xres_out_1  <= xres_in;
yres_out_1  <= yres_in;

sync_error_out_1<= sync_error_in;
pixel_error_out_1<= pixel_error_in;


 -- stall out for both
stall_out <= stall_in_0 or stall_in_1;

end RTL;
