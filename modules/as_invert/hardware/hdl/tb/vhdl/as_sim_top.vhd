----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  Copyright (C) Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_sim_top
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Authors:        Markus Bihler, B.Eng.
--                 Michael Schaeferling, M.Sc.
--
-- Modified:       
--
-- Description:    A testbench for ASTERICS based image processing pipelines.
-- 
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
--! @file  as_sim_top.vhd
--! @brief A testbench for ASTERICS based image processing pipelines.
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;


entity as_sim_top is
  generic(
    GEN_DATA_WIDTH     : integer := 8;
    GEN_DELIMITER      : character := ';';
    GEN_FILE_IN_NAME   : string := "../images/img_in.csv";
    GEN_FILE_IN_WIDTH  : natural := 640;
    GEN_FILE_IN_HEIGHT : natural := 480;
    GEN_FILE_OUT_NAME  : string := "../images/img_out_hw.csv"
  );
end as_sim_top;


architecture simulation of as_sim_top is

  component as_sim_image_reader is
    generic(
      DOUT_WIDTH : integer := 8;
      GEN_FILENAME : string := "img_in.csv";
      GEN_DELIMITER : character := ';';
      GEN_IMAGEWIDTH : natural  := 640;
      GEN_IMAGEHEIGHT : natural := 480
    );
    port(
      Clk         : in std_logic;
      Reset       : in std_logic;
      
      ENABLE_IN   : in  std_logic;
      
      -- Pixel Stream output PORTS
      VSYNC_OUT   : out std_logic;
      HSYNC_OUT   : out std_logic;
      STROBE_OUT  : out std_logic;
      DATA_OUT    : out std_logic_vector(DOUT_WIDTH-1 downto 0);
      XRES_OUT    : out std_logic_vector(11 downto 0);
      YRES_OUT    : out std_logic_vector(11 downto 0);
      SYNC_ERROR_OUT  : out std_logic;
      PIXEL_ERROR_OUT : out std_logic;
      STALL_IN        : in  std_logic
    );
  end component;
  
  
  component as_sim_mod_inst is
    generic (
      DIN_WIDTH  : integer := 8;
      DOUT_WIDTH : integer := 8
    );
    port (
      Clk               : in  std_logic;
      Reset             : in  std_logic;
      Ready             : out std_logic;

      -- Pixel Stream input PORTS
      VSYNC_IN    : in  std_logic;
      HSYNC_IN    : in  std_logic;
      STROBE_IN   : in  std_logic;
      DATA_IN     : in  std_logic_vector(DIN_WIDTH-1 downto 0);
      XRES_IN     : in  std_logic_vector(11 downto 0);
      YRES_IN     : in  std_logic_vector(11 downto 0);
      
      SYNC_ERROR_IN  : in  std_logic;
      PIXEL_ERROR_IN : in  std_logic;
      STALL_OUT      : out std_logic;
      
      -- Pixel Stream output PORTS
      VSYNC_OUT  : out std_logic;
      HSYNC_OUT  : out std_logic;
      STROBE_OUT : out std_logic;
      DATA_OUT   : out std_logic_vector(DOUT_WIDTH-1 downto 0);
      XRES_OUT   : out std_logic_vector(11 downto 0);
      YRES_OUT   : out std_logic_vector(11 downto 0);
      
      SYNC_ERROR_OUT  : out std_logic;
      PIXEL_ERROR_OUT : out std_logic;
      STALL_IN        : in  std_logic;

      -- Module ports for parametrization (usually connected to slave registers):
      -- as_invert
      as_invert_0_control       : in  std_logic_vector(15 downto 0);
      as_invert_0_control_reset : out std_logic_vector(15 downto 0);
      as_invert_0_state         : out std_logic_vector(15 downto 0)
    );
  end component;
  
  
  component as_sim_image_writer is
    generic(
      DIN_WIDTH : integer := 8;
      GEN_FILENAME : string := "img_out.csv";
      GEN_DELIMITER : character := ';'
    );
    port(
      Clk : in std_logic;
      Reset : in std_logic;
      
      -- Pixel Stream output PORTS
      VSYNC_IN   : in  std_logic;
      HSYNC_IN   : in  std_logic;
      STROBE_IN  : in  std_logic;
      DATA_IN    : in  std_logic_vector(DIN_WIDTH-1 downto 0);
      XRES_IN    : in  std_logic_vector(11 downto 0);
      YRES_IN    : in  std_logic_vector(11 downto 0);
      SYNC_ERROR_IN  : in  std_logic;
      PIXEL_ERROR_IN : in  std_logic;
      STALL_OUT      : out std_logic;

      -- signals to testbench:
      DONE_OUT  : out std_logic;
      BACKPRESSURE_EN : in std_logic;
      PIXEL_ERROR : out std_logic;
      SYNC_ERROR  : out std_logic
    );
  end component;
  
  
  signal Clk, Reset : std_logic;
  
  -- Glue signals: IMG_READER_0 to MOD_INST_0
  signal s_img_rd0_vsync    : std_logic;
  signal s_img_rd0_hsync    : std_logic;
  signal s_img_rd0_strobe   : std_logic;
  signal s_img_rd0_data     : std_logic_vector(GEN_DATA_WIDTH-1 downto 0);
  signal s_img_rd0_xres     : std_logic_vector(11 downto 0);
  signal s_img_rd0_yres     : std_logic_vector(11 downto 0);
  signal s_img_rd0_sync_error  : std_logic;
  signal s_img_rd0_pixel_error : std_logic;
  signal s_img_rd0_stall    : std_logic;
  -- tb control:
  signal s_img_rd0_tb_enable : std_logic;
  
  -- Glue signals (RTPB): MOD_INST_0 to IMG_WRITER_0
  signal s_img_wr0_vsync    : std_logic;
  signal s_img_wr0_hsync    : std_logic;
  signal s_img_wr0_strobe   : std_logic;
  signal s_img_wr0_data     : std_logic_vector(GEN_DATA_WIDTH-1 downto 0);
  signal s_img_wr0_xres     : std_logic_vector(11 downto 0);
  signal s_img_wr0_yres     : std_logic_vector(11 downto 0);
  signal s_img_wr0_sync_error  : std_logic;
  signal s_img_wr0_pixel_error : std_logic;
  signal s_img_wr0_stall    : std_logic;
  -- tb control:
  signal s_img_wr0_tb_done            : std_logic;
  signal s_img_wr0_tb_backpressure_en : std_logic;
  signal s_img_wr0_tb_pixel_error     : std_logic;
  signal s_img_wr0_tb_sync_error      : std_logic;

  signal s_as_sim_mod_inst_ready : std_logic;

  -- slave signal connections:
  -- as_invert
  signal as_invert_0_control : std_logic_vector(15 downto 0);
  signal as_invert_0_control_reset : std_logic_vector(15 downto 0);
  signal as_invert_0_state : std_logic_vector(15 downto 0);

  shared variable SIM_FINISHED : boolean := false;

begin

  -- module instantiation:
  
  IMG_READER_0: as_sim_image_reader
    generic map(
      DOUT_WIDTH => GEN_DATA_WIDTH,
      GEN_FILENAME => GEN_FILE_IN_NAME,
      GEN_DELIMITER => GEN_DELIMITER,
      GEN_IMAGEWIDTH  => GEN_FILE_IN_WIDTH,
      GEN_IMAGEHEIGHT => GEN_FILE_IN_HEIGHT
    )
    port map(
      Clk => Clk,
      Reset => Reset,
      
      VSYNC_OUT => s_img_rd0_vsync,
      HSYNC_OUT => s_img_rd0_hsync,
      STROBE_OUT => s_img_rd0_strobe,
      DATA_OUT => s_img_rd0_data,
      XRES_OUT => s_img_rd0_xres,
      YRES_OUT => s_img_rd0_yres,
      SYNC_ERROR_OUT => s_img_rd0_sync_error,
      PIXEL_ERROR_OUT => s_img_rd0_pixel_error,
      STALL_IN => s_img_rd0_stall,
      
      ENABLE_IN => s_img_rd0_tb_enable
    );
    
  MOD_INST_0: as_sim_mod_inst
    generic map(
      DIN_WIDTH  => GEN_DATA_WIDTH,
      DOUT_WIDTH => GEN_DATA_WIDTH
    )
    port map(
      Clk => Clk,
      Reset => Reset,
      Ready => s_as_sim_mod_inst_ready,

      -- IN ports
      VSYNC_IN => s_img_rd0_vsync,
      HSYNC_IN => s_img_rd0_hsync,
      STROBE_IN => s_img_rd0_strobe,
      DATA_IN => s_img_rd0_data,
      XRES_IN => s_img_rd0_xres,
      YRES_IN => s_img_rd0_yres,
      SYNC_ERROR_IN => s_img_rd0_sync_error,
      PIXEL_ERROR_IN => s_img_rd0_pixel_error,
      STALL_OUT => s_img_rd0_stall,
      
      -- OUT ports
      VSYNC_OUT => s_img_wr0_vsync,
      HSYNC_OUT => s_img_wr0_hsync,
      STROBE_OUT => s_img_wr0_strobe,
      DATA_OUT => s_img_wr0_data,
      XRES_OUT => s_img_wr0_xres,
      YRES_OUT => s_img_wr0_yres,
      SYNC_ERROR_OUT => s_img_wr0_sync_error,
      PIXEL_ERROR_OUT => s_img_wr0_pixel_error,
      STALL_IN => s_img_wr0_stall,

      -- Module ports for parametrization (usually connected to slave registers):
      -- as_invert
      as_invert_0_control => as_invert_0_control,
      as_invert_0_control_reset => as_invert_0_control_reset,
      as_invert_0_state => as_invert_0_state
    );
    
  IMG_WRITER_0: as_sim_image_writer
    generic map(
      GEN_FILENAME => GEN_FILE_OUT_NAME,
      GEN_DELIMITER => GEN_DELIMITER
    )
    port map(
      Clk => Clk,
      Reset => Reset,
      
      VSYNC_IN => s_img_wr0_vsync,
      HSYNC_IN => s_img_wr0_hsync,
      STROBE_IN => s_img_wr0_strobe,
      DATA_IN => s_img_wr0_data,
      XRES_IN => s_img_wr0_xres,
      YRES_IN => s_img_wr0_yres,
      SYNC_ERROR_IN => s_img_wr0_sync_error,
      PIXEL_ERROR_IN => s_img_wr0_pixel_error,
      STALL_OUT => s_img_wr0_stall,
      
      DONE_OUT => s_img_wr0_tb_done,
      BACKPRESSURE_EN => s_img_wr0_tb_backpressure_en,
      PIXEL_ERROR => s_img_wr0_tb_pixel_error,
      SYNC_ERROR  => s_img_wr0_tb_sync_error
    ); 


clock: process
  begin
    if SIM_FINISHED=false then
      Clk <= '1';
      wait for 1 ns;
      Clk <= '0';
      wait for 1 ns;
    else 
      wait;
    end if;
      
end process;


tb: process 
begin

  -- =======================================================
  -- Module configuration:
  
  -- == as_invert ==
  -- enable inversion:
  as_invert_0_control <= (others=>'0');
  as_invert_0_control(1) <= '1';
  
  -- =======================================================

  s_img_rd0_tb_enable <= '0';
  s_img_wr0_tb_backpressure_en <= '0';

  Reset <= '1';
  wait for 5 ns;
  Reset <= '0';
  
  wait until s_as_sim_mod_inst_ready = '1';
  
  s_img_rd0_tb_enable <= '1';
  
  -- continuous reading (all active)
  for i in 0 to 100 loop
    wait until rising_edge(Clk);
  end loop;
  
  -- vary strobes while reading: 1 active - 1 inactive
  for i in 0 to 100 loop
    wait until rising_edge(Clk);
    s_img_rd0_tb_enable <= '0';
    wait until rising_edge(Clk);
    s_img_rd0_tb_enable <= '1';
  end loop;
  
  -- vary strobes while reading: 1 active - 2 inactive
  for i in 0 to 100 loop
    wait until rising_edge(Clk);
    s_img_rd0_tb_enable <= '0';
    wait until rising_edge(Clk);
    wait until rising_edge(Clk);
    s_img_rd0_tb_enable <= '1';
  end loop;
  
  wait until s_img_wr0_tb_done ='1';
  
  assert false
    report "SIMULATION FINISHED"
    severity note;
    
    SIM_FINISHED:=true;
    
  wait;
    
end process;


end simulation;

