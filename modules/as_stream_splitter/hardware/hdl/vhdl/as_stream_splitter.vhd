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
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

---- Uncomment the following library declaration if instantiating
---- any Xilinx primitives in this code.
--library UNISIM;
--use UNISIM.VComponents.all;

entity as_stream_splitter is
  generic (
    DATA_WIDTH  : integer := 8
  );
  port (
    Clk         : in  std_logic;
    Reset       : in  std_logic;
    Ready       : out std_logic;

    -- IN ports
    VSYNC_IN    : in  std_logic;
    HSYNC_IN    : in  std_logic;
    STROBE_IN   : in  std_logic;
    DATA_IN     : in  std_logic_vector(DATA_WIDTH-1 downto 0);
    XRES_IN     : in  std_logic_vector(11 downto 0);
    YRES_IN     : in  std_logic_vector(11 downto 0);
    
    SYNC_ERROR_IN  : in  std_logic;
    PIXEL_ERROR_IN : in  std_logic;
    STALL_OUT      : out std_logic;

    -- OUT ports
    VSYNC_OUT_0   : out std_logic;
    HSYNC_OUT_0   : out std_logic;
    STROBE_OUT_0  : out std_logic;
    DATA_OUT_0    : out std_logic_vector(DATA_WIDTH-1 downto 0);
    XRES_OUT_0    : out std_logic_vector(11 downto 0);
    YRES_OUT_0    : out std_logic_vector(11 downto 0);
    
    SYNC_ERROR_OUT_0  : out std_logic;
    PIXEL_ERROR_OUT_0 : out std_logic;
    STALL_IN_0        : in  std_logic;

	VSYNC_OUT_1  : out std_logic;
    HSYNC_OUT_1  : out std_logic;
    STROBE_OUT_1 : out std_logic;
    DATA_OUT_1   : out std_logic_vector(DATA_WIDTH-1 downto 0);
    XRES_OUT_1   : out std_logic_vector(11 downto 0);
    YRES_OUT_1   : out std_logic_vector(11 downto 0);
    
    SYNC_ERROR_OUT_1 : out std_logic;
    PIXEL_ERROR_OUT_1: out std_logic;
    STALL_IN_1       : in  std_logic

  );
end as_stream_splitter;


architecture RTL of as_stream_splitter is


begin

 -- stream out 0
VSYNC_OUT_0  <= VSYNC_IN;
HSYNC_OUT_0  <= HSYNC_IN;
STROBE_OUT_0 <= STROBE_IN;

DATA_OUT_0 <= DATA_IN;

XRES_OUT_0   <= XRES_IN;
YRES_OUT_0   <= YRES_IN;

SYNC_ERROR_OUT_0 <= SYNC_ERROR_IN;
PIXEL_ERROR_OUT_0 <= PIXEL_ERROR_IN;


 -- stream out 1
VSYNC_OUT_1 <= VSYNC_IN;
HSYNC_OUT_1 <= HSYNC_IN;
STROBE_OUT_1 <= STROBE_IN;

DATA_OUT_1 <= DATA_IN;

XRES_OUT_1  <= XRES_IN;
YRES_OUT_1  <= YRES_IN;

SYNC_ERROR_OUT_1<= SYNC_ERROR_IN;
PIXEL_ERROR_OUT_1<= PIXEL_ERROR_IN;


 -- stall out for both
STALL_OUT <= STALL_IN_0 or STALL_IN_1;

end RTL;
