----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_reorder
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Matthias Struwe
--
-- Modified:       Philip Manke
--
-- Description:    Invert the order of pixels (configurable bitwidth) in the data stream.
--                 DATA_WIDTH must be evenly divisible by PIXEL_BITWIDTH.
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
--! @brief Invert the order of pixels (configurable bitwidth) in the data stream.
--! @addtogroup asterics_modules
--! @{
--! @defgroup as_reorder as_reorder: Reorder AsStream Data
--! Invert the order of pixels (configurable bitwidth) in the data stream.
--! DATA_WIDTH must be evenly divisible by PIXEL_BITWIDTH.
--! @}
----------------------------------------------------------------------------------

--! @addtogroup as_reorder
--! @{


library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

library asterics;
use asterics.helpers.all;


entity as_reorder is
  generic (
    -- Width of the data ports
    DATA_WIDTH  : integer := 32;
    -- Bit width of an indiviual pixel
    PIXEL_BITWIDTH : integer := 8
  );
  port (
    -- IN as_stream interface
    vsync_in      : in  std_logic;
    hsync_in      : in  std_logic;
    strobe_in     : in  std_logic;
    data_in       : in  std_logic_vector(DATA_WIDTH - 1 downto 0);
    stall_out     : out std_logic;
    sync_error_in : in  std_logic;
    data_error_in : in  std_logic;

    -- OUT as_stream interface
    vsync_out      : out std_logic;
    hsync_out      : out std_logic;
    strobe_out     : out std_logic;
    data_out       : out std_logic_vector(DATA_WIDTH - 1 downto 0);
    stall_in       : in  std_logic;
    sync_error_out : out std_logic;
    data_error_out : out std_logic
  );
end as_reorder;

--! @}

architecture RTL of as_reorder is
  -- Number of pixels in the data stream
  constant c_pixel_count : integer := DATA_WIDTH / PIXEL_BITWIDTH;

begin
  assert DATA_WIDTH mod PIXEL_BITWIDTH = 0 
    report "as_reorder: DATA_WIDTH not divisible by PIXEL_BITWIDTH! Cannot generate module logic!"
    severity failure;

  -- Invert the order of the pixels in the data stream
  gen_reorder_pixels : for N in 0 to c_pixel_count - 1 generate
    constant m : integer := (c_pixel_count - 1) - N;
  begin
    data_out((N + 1) * PIXEL_BITWIDTH - 1 downto N * PIXEL_BITWIDTH) 
      <= data_in((m + 1) * PIXEL_BITWIDTH - 1 downto m * PIXEL_BITWIDTH);
  end generate;
  
  -- All control signals are unmodified
  vsync_out      <= vsync_in;
  hsync_out      <= hsync_in;
  strobe_out     <= strobe_in;
  sync_error_out <= sync_error_in;
  data_error_out <= data_error_in;
  stall_out      <= stall_in;
end RTL;
