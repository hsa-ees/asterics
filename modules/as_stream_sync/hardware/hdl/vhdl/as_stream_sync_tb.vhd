----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- File:           as_stream_sync_tb.vhd
-- Entity:         as_stream_sync_tb
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Philip Manke
--
-- Modified:       
--
-- Description:    Brief (manual) testbench for as_stream_sync.vhd 
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
--! @file as_stream_sync_tb.vhd
--! @brief Brief (manual) testbench for as_stream_sync.vhd 
----------------------------------------------------------------------------------


library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity as_stream_sync_tb is
end entity;

architecture TB of as_stream_sync_tb is

  component as_stream_sync is
  generic (
      DATA_WIDTH_0  : integer := 8;
      DATA_WIDTH_1  : integer := 8;
      BUFF_DEPTH : integer := 512
  );
  port (
      clk         : in  std_logic;
      reset       : in  std_logic;
      ready       : out std_logic;

      -- as_stream IN ports 0
      VSYNC_IN_0    : in  std_logic;
      HSYNC_IN_0    : in  std_logic;
      STROBE_IN_0   : in  std_logic;
      DATA_IN_0     : in  std_logic_vector(DATA_WIDTH_0-1 downto 0);
      XRES_IN_0     : in  std_logic_vector(11 downto 0);
      YRES_IN_0     : in  std_logic_vector(11 downto 0);
      
      SYNC_ERROR_IN_0  : in  std_logic;
      DATA_ERROR_IN_0 : in  std_logic;
      STALL_OUT_0      : out std_logic;
      
      -- IN ports 1
      VSYNC_IN_1    : in  std_logic;
      HSYNC_IN_1    : in  std_logic;
      STROBE_IN_1   : in  std_logic;
      DATA_IN_1     : in  std_logic_vector(DATA_WIDTH_1-1 downto 0);
      XRES_IN_1     : in  std_logic_vector(11 downto 0);
      YRES_IN_1     : in  std_logic_vector(11 downto 0);
      
      SYNC_ERROR_IN_1  : in  std_logic;
      DATA_ERROR_IN_1 : in  std_logic;
      STALL_OUT_1      : out std_logic;
      
      -- OUT ports 0
      VSYNC_OUT_0   : out std_logic;
      HSYNC_OUT_0   : out std_logic;
      STROBE_OUT_0  : out std_logic;
      DATA_OUT_0    : out std_logic_vector(DATA_WIDTH_0-1 downto 0);
      XRES_OUT_0    : out std_logic_vector(11 downto 0);
      YRES_OUT_0    : out std_logic_vector(11 downto 0);
      
      SYNC_ERROR_OUT_0  : out std_logic;
      DATA_ERROR_OUT_0 : out std_logic;
      STALL_IN_0        : in  std_logic;

      -- OUT ports 1
      VSYNC_OUT_1   : out std_logic;
      HSYNC_OUT_1   : out std_logic;
      STROBE_OUT_1  : out std_logic;
      DATA_OUT_1    : out std_logic_vector(DATA_WIDTH_1-1 downto 0);
      XRES_OUT_1    : out std_logic_vector(11 downto 0);
      YRES_OUT_1    : out std_logic_vector(11 downto 0);
      
      SYNC_ERROR_OUT_1  : out std_logic;
      DATA_ERROR_OUT_1 : out std_logic;
      STALL_IN_1        : in  std_logic;
      
      DEBUG    : out std_logic_vector(1 downto 0);
      FILL_LEVEL_FIFO_0 : out std_logic_vector(31 downto 0);
      FILL_LEVEL_FIFO_1 : out std_logic_vector(31 downto 0)
  );
  end component;


  signal clk, reset, running, ready : std_logic; 

  constant c_data_width_in_0 : integer := 8;
  constant c_data_width_in_1 : integer := 8;

  signal strobe_in_0, hsync_in_0, vsync_in_0, sync_error_in_0, data_error_in_0 : std_logic;
  signal data_in_0 : std_logic_vector(c_data_width_in_0 - 1 downto 0);
  
  signal strobe_in_1, hsync_in_1, vsync_in_1, sync_error_in_1, data_error_in_1 : std_logic;
  signal data_in_1 : std_logic_vector(c_data_width_in_1 - 1 downto 0);
  
  signal strobe_out_0, hsync_out_0, vsync_out_0, sync_error_out_0, data_error_out_0 : std_logic;
  signal data_out_0 : std_logic_vector(c_data_width_in_0 - 1 downto 0);
  
  signal strobe_out_1, hsync_out_1, vsync_out_1, sync_error_out_1, data_error_out_1 : std_logic;
  signal data_out_1 : std_logic_vector(c_data_width_in_1 - 1 downto 0);
  
  signal stall_in_0, stall_in_1, stall_out_0, stall_out_1 : std_logic;
  signal debug : std_logic_vector(1 downto 0);
  signal level_0, level_1 : std_logic_vector(31 downto 0);

begin

clk_gen : process
begin
  clk <= '0';
  wait for 500 ns;
  clk <= '1';
  wait for 500 ns;
  report "here";
  if running = '0' then
    wait;
  end if;
end process;

testbench : process
begin
  report "Starting";
  running <= '1';
  reset <= '1';
  strobe_in_0 <= '0';
  hsync_in_0 <= '0';
  vsync_in_0 <= '0';
  sync_error_in_0 <= '0';
  data_error_in_0 <= '0';

  report "here";
  strobe_in_1 <= '0';
  hsync_in_1 <= '0';
  vsync_in_1 <= '0';
  sync_error_in_1 <= '0';
  data_error_in_1 <= '0';
  
  stall_in_0 <= '0';
  stall_in_1 <= '0';

  report "here";
  data_in_0 <= (others => '0');
  data_in_1 <= (others => '0');
  report "here";
  wait for 2 us;

  reset <= '0';

  wait for 2 us;

  strobe_in_0 <= '1';
  data_in_0 <= x"42";

  wait for 4 us;

  vsync_in_0 <= '1';

  wait for 2 us;

  vsync_in_0 <= '0';

  data_in_0 <= x"24";

  wait for 4 us;

  strobe_in_1 <= '1';
  vsync_in_1 <= '1';
  data_in_1 <= x"75";
  
  wait for 2 us;

  vsync_in_1 <= '0';

  data_in_0 <= x"62";
  data_in_1 <= x"55";
  wait for 10 us;

  strobe_in_0 <= '0';
  data_in_1 <= x"37";

  wait for 10 us;
  strobe_in_1 <= '0';

  wait for 20 us;

  running <= '0';
  wait;
end process;


unit_under_test : as_stream_sync
generic map(
  DATA_WIDTH_0 => c_data_width_in_0,
  DATA_WIDTH_1 => c_data_width_in_1,
  BUFF_DEPTH => 512
)
port map(
clk        => clk,
reset      => reset,
ready      => ready,

VSYNC_IN_0       => vsync_in_0,
HSYNC_IN_0       => hsync_in_0,
STROBE_IN_0      => strobe_in_0,
DATA_IN_0        => data_in_0,
XRES_IN_0        => (others => '0'),
YRES_IN_0        => (others => '0'),
SYNC_ERROR_IN_0  => sync_error_in_0,
DATA_ERROR_IN_0  => data_error_in_0,
STALL_OUT_0      => stall_out_0,
-- IN ports 1
VSYNC_IN_1      => vsync_in_1,
HSYNC_IN_1      => hsync_in_1,
STROBE_IN_1     => strobe_in_1,
DATA_IN_1       => data_in_1,
XRES_IN_1       => (others => '0'),
YRES_IN_1       => (others => '0'),
SYNC_ERROR_IN_1 => sync_error_in_1,
DATA_ERROR_IN_1 => data_error_in_1,
STALL_OUT_1     => stall_out_1,
-- OUT ports 0
VSYNC_OUT_0     => vsync_out_0,
HSYNC_OUT_0     => hsync_out_0,
STROBE_OUT_0    => strobe_out_0,
DATA_OUT_0      => data_out_0,
XRES_OUT_0      => open,
YRES_OUT_0      => open,
SYNC_ERROR_OUT_0=> sync_error_out_0,  
DATA_ERROR_OUT_0=> data_error_out_0,
STALL_IN_0      => stall_in_0,  
-- OUT ports 1
VSYNC_OUT_1     => vsync_out_1,
HSYNC_OUT_1     => hsync_out_1,
STROBE_OUT_1    => strobe_out_1,
DATA_OUT_1      => data_out_1,
XRES_OUT_1      => open,
YRES_OUT_1      => open,
SYNC_ERROR_OUT_1=> sync_error_out_1,  
DATA_ERROR_OUT_1=> data_error_out_1,
STALL_IN_1      => stall_in_1,  
DEBUG    => debug,
FILL_LEVEL_FIFO_0 => level_0,
FILL_LEVEL_FIFO_1 => level_1
);



end TB;
