----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- File:           as_stream_sync.vhd
-- Entity:         as_stream_sync
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Michael Schaeferling
--
-- Modified:       2019-04-17 by Philip Manke: New FIFO, update for use with ASTERICS
--                                             Add vsync latch functionality 
--                                             Allow different data widths per stream
--
-- Description:    Synchronize two as_stream pixel data streams
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
--! @file as_stream_sync.vhd
--! @brief Synchronize two as_stream pixel data streams
--! @addtogroup asterics_modules
--! @{
--! @defgroup as_stream_sync as_stream_sync: Synchronization of two AsStreams
--! This module synchronizes two AsStream interfaces using the number of strobe
--! signals received from either stream.
--! Useful for possible short timing discrepencies between two AsStream sources
--! that must operate synchronously.
--! Buffer depth is configurable through generics.
--! @}
----------------------------------------------------------------------------------

--! @addtogroup as_stream_sync
--! @{


library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

library asterics;
use asterics.helpers.all;
use asterics.fifo_fwft;


entity as_stream_sync is
generic (
    DATA_WIDTH_0  : integer := 8;
    DATA_WIDTH_1  : integer := 8;
    BUFF_DEPTH : integer := 512
);
port (
    clk         : in  std_logic;
    reset       : in  std_logic;
    ready       : out std_logic;

    -- as_stream in ports 0
    vsync_in_0    : in  std_logic;
    hsync_in_0    : in  std_logic;
    strobe_in_0   : in  std_logic;
    data_in_0     : in  std_logic_vector(DATA_WIDTH_0-1 downto 0);
    
    sync_error_in_0  : in  std_logic;
    data_error_in_0 : in  std_logic;
    stall_out_0      : out std_logic;
    
    -- in ports 1
    vsync_in_1    : in  std_logic;
    hsync_in_1    : in  std_logic;
    strobe_in_1   : in  std_logic;
    data_in_1     : in  std_logic_vector(DATA_WIDTH_1-1 downto 0);
    
    sync_error_in_1  : in  std_logic;
    data_error_in_1 : in  std_logic;
    stall_out_1      : out std_logic;
    
    -- out ports 0
    vsync_out_0   : out std_logic;
    hsync_out_0   : out std_logic;
    strobe_out_0  : out std_logic;
    data_out_0    : out std_logic_vector(DATA_WIDTH_0-1 downto 0);
    
    sync_error_out_0  : out std_logic;
    data_error_out_0 : out std_logic;
    stall_in_0        : in  std_logic;

    -- out ports 1
    vsync_out_1   : out std_logic;
    hsync_out_1   : out std_logic;
    strobe_out_1  : out std_logic;
    data_out_1    : out std_logic_vector(DATA_WIDTH_1-1 downto 0);
    
    sync_error_out_1  : out std_logic;
    data_error_out_1 : out std_logic;
    stall_in_1        : in  std_logic
);
end as_stream_sync;

--! @}

architecture RTL of as_stream_sync is

signal wr_en_0, rd_en_0, full_0, empty_0, fifo_0_full : std_logic;

signal wr_en_1, rd_en_1, full_1, empty_1, fifo_1_full : std_logic;

signal stall_in : std_logic;
signal data_valid_out : std_logic;

constant c_fifo_0_data_width : integer := DATA_WIDTH_0 + 4;
constant c_fifo_1_data_width : integer := DATA_WIDTH_1 + 4; 
signal din_0, dout_0 : std_logic_vector(c_fifo_0_data_width - 1 downto 0);
signal din_1, dout_1 : std_logic_vector(c_fifo_1_data_width - 1 downto 0);

constant c_prog_full_thresh : std_logic_vector(log2_ceil(BUFF_DEPTH) - 1 downto 0)
            := std_logic_vector(to_unsigned(BUFF_DEPTH - log2_ceil(BUFF_DEPTH), log2_ceil(BUFF_DEPTH)));

signal fifo_0_level, fifo_1_level : std_logic_vector(log2_ceil(BUFF_DEPTH) downto 0);

begin

ready <= not reset;


-- FIFO instantiations
fifo_sync_port0 : entity fifo_fwft
  GENERIC MAP (
    DATA_WIDTH => c_fifo_0_data_width,
    BUFF_DEPTH => BUFF_DEPTH,
    PROG_EMPTY_ENABLE => False,
    PROG_FULL_ENABLE => True
  )
  PORT MAP (
    clk => clk,
    reset => reset,
    din => din_0,
    wr_en => wr_en_0,
    rd_en => rd_en_0,
    dout => dout_0,
    full => full_0,
    level => fifo_0_level,
    empty => empty_0,
    prog_empty_thresh => (others => '0'),
    prog_empty => open,
    prog_full_thresh => c_prog_full_thresh,
    prog_full => fifo_0_full
  );

fifo_sync_port1 : entity fifo_fwft
  GENERIC MAP (
    DATA_WIDTH => c_fifo_1_data_width,
    BUFF_DEPTH => BUFF_DEPTH,
    PROG_EMPTY_ENABLE => False,
    PROG_FULL_ENABLE => True
  )
  PORT MAP (
    clk => clk,
    reset => reset,
    din => din_1,
    wr_en => wr_en_1,
    rd_en => rd_en_1,
    dout => dout_1,
    full => full_1,
    level => fifo_1_level, 
    empty => empty_1,
    prog_empty_thresh => (others => '0'),
    prog_empty => open,
    prog_full_thresh => c_prog_full_thresh,
    prog_full => fifo_1_full
  );
  
-- Synchronous FIFO Data input
fifo_in_proc: process (clk)
begin
  if rising_edge(clk) then
    -- DATASTREAM_0
    wr_en_0 <= strobe_in_0;
    din_0   <= data_in_0 & data_error_in_0 & sync_error_in_0 & hsync_in_0 & vsync_in_0;

    -- DATASTREAM_1
    wr_en_1 <= strobe_in_1;
    din_1   <= data_in_1 & data_error_in_1 & sync_error_in_1 & hsync_in_1 & vsync_in_1;
  end if;
  
end process;

--====================================================================================================================

---- FIFO output:

stall_in <= '1' when (STALL_IN_0 = '1' or STALL_IN_1 = '1') else '0';

data_valid_out <= '1' when ((empty_0 = '0') and (empty_1 = '0') and (stall_in = '0')) else '0';


-- DATASTREAM_0
rd_en_0      <= data_valid_out;
strobe_out_0 <= data_valid_out;
data_out_0   <= dout_0(c_fifo_0_data_width - 1 downto 4);
vsync_out_0  <= dout_0(0);
hsync_out_0  <= dout_0(1);
sync_error_out_0  <= dout_0(2);
data_error_out_0 <= dout_0(3);

-- DATASTREAM_1
rd_en_1      <= data_valid_out;
strobe_out_1 <= data_valid_out;
data_out_1   <= dout_1(c_fifo_1_data_width - 1 downto 4);
vsync_out_1  <= dout_1(0);
hsync_out_1  <= dout_1(1);
sync_error_out_1 <= dout_1(2);
data_error_out_1 <= dout_1(3);


-- Stall each stream, if their FIFO is full
stall_proc: process (clk)
begin
  if rising_edge(clk) then
  
    stall_out_0 <= '0';
    stall_out_1 <= '0';
  
    if (fifo_0_full = '1') then
      stall_out_0 <= '1';
    end if;
    
    if (fifo_1_full = '1') then
      stall_out_1 <= '1';
    end if;
  end if;
end process;


end RTL;
