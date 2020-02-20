----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  Copyright (C) Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_sim_mod_inst
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Author:         Michael Schaeferling
--
-- Modified:       
--
-- Description:    Within this module, ASTERICS modules are instanciated
--                 and interconnected to build an image processing chain.
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
--! @file  as_sim_mod_inst.vhd
--! @brief Module instantiation for simulation 
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;


entity as_sim_mod_inst is
  generic (
    DIN_WIDTH  : integer := 8;
    DOUT_WIDTH : integer := 8
  );
  port (
    Clk         : in  std_logic;
    Reset       : in  std_logic;
    Ready       : out std_logic;

    -- RTPB - IN ports
    VSYNC_IN    : in  std_logic;
    HSYNC_IN    : in  std_logic;
    STROBE_IN   : in  std_logic;
    DATA_IN     : in  std_logic_vector(DIN_WIDTH-1 downto 0);
    XRES_IN     : in  std_logic_vector(11 downto 0);
    YRES_IN     : in  std_logic_vector(11 downto 0);
    
    SYNC_ERROR_IN  : in  std_logic;
    PIXEL_ERROR_IN : in  std_logic;
    STALL_OUT      : out std_logic;
    
    -- RTPB - OUT ports
    VSYNC_OUT   : out std_logic;
    HSYNC_OUT   : out std_logic;
    STROBE_OUT  : out std_logic;
    DATA_OUT    : out std_logic_vector(DOUT_WIDTH-1 downto 0);
    XRES_OUT    : out std_logic_vector(11 downto 0);
    YRES_OUT    : out std_logic_vector(11 downto 0);
    
    SYNC_ERROR_OUT  : out std_logic;
    PIXEL_ERROR_OUT : out std_logic;
    STALL_IN        : in  std_logic;


    -- Module ports for parametrization (usually connected to slave registers):

    -- as_invert
    as_invert_0_control       : in  std_logic_vector(15 downto 0);
    as_invert_0_control_reset : out std_logic_vector(15 downto 0);
    as_invert_0_state         : out std_logic_vector(15 downto 0)

  );
end as_sim_mod_inst;



architecture mod_inst of as_sim_mod_inst is


component as_invert is
  generic (
    DIN_WIDTH  : integer := 8;
    DOUT_WIDTH : integer := 8
  );
  port (
    Clk         : in  std_logic;
    Reset       : in  std_logic;
    Ready       : out std_logic;

    -- IN ports
    VSYNC_IN    : in  std_logic;
    HSYNC_IN    : in  std_logic;
    STROBE_IN   : in  std_logic;
    DATA_IN     : in  std_logic_vector(DIN_WIDTH-1 downto 0);
    XRES_IN     : in  std_logic_vector(11 downto 0);
    YRES_IN     : in  std_logic_vector(11 downto 0);
    
    SYNC_ERROR_IN  : in  std_logic;
    PIXEL_ERROR_IN : in  std_logic;
    STALL_OUT      : out std_logic;

    -- OUT ports
    VSYNC_OUT   : out std_logic;
    HSYNC_OUT   : out std_logic;
    STROBE_OUT  : out std_logic;
    DATA_OUT    : out std_logic_vector(DOUT_WIDTH-1 downto 0);
    XRES_OUT    : out std_logic_vector(11 downto 0);
    YRES_OUT    : out std_logic_vector(11 downto 0);
    
    SYNC_ERROR_OUT  : out std_logic;
    PIXEL_ERROR_OUT : out std_logic;
    STALL_IN        : in  std_logic;

    -- Parameters
    control       : in  std_logic_vector(15 downto 0);
    control_reset : out std_logic_vector(15 downto 0);
    state         : out std_logic_vector(15 downto 0)
  );
end component;




-- Glue signals for component interconnection:
--
constant DATA_INPUT_WIDTH : integer := DIN_WIDTH;
signal as_input_vsync, as_input_hsync, as_input_strobe, as_input_stall, as_input_syncerror, as_input_pixelerror : std_logic;
signal as_input_data : std_logic_vector(DATA_INPUT_WIDTH-1 downto 0);
signal as_input_xres : std_logic_vector(11 downto 0);
signal as_input_yres : std_logic_vector(11 downto 0);
--
constant DATA_OUTPUT_WIDTH : integer := DOUT_WIDTH;
signal as_ouput_vsync, as_ouput_hsync, as_ouput_strobe, as_ouput_stall, as_ouput_syncerror, as_ouput_pixelerror : std_logic;
signal as_ouput_data : std_logic_vector(DATA_OUTPUT_WIDTH-1 downto 0);
signal as_ouput_xres : std_logic_vector(11 downto 0);
signal as_ouput_yres : std_logic_vector(11 downto 0);


signal as_invert_0_ready : std_logic;


begin


Ready <= as_invert_0_ready;


as_input_vsync <= VSYNC_IN;
as_input_hsync <= HSYNC_IN;
as_input_strobe <= STROBE_IN;
as_input_data <= DATA_IN;
as_input_xres <= XRES_IN;
as_input_yres <= YRES_IN;
as_input_syncerror <= SYNC_ERROR_IN;
as_input_pixelerror <= PIXEL_ERROR_IN;
STALL_OUT <= as_input_stall;


INVERT_0 : as_invert
  generic map (
    DIN_WIDTH  => DATA_INPUT_WIDTH,
    DOUT_WIDTH => DATA_OUTPUT_WIDTH
  )
  port map (
    Clk   => clk,
    Reset => reset,
    Ready => as_invert_0_ready,

    -- IN ports
    VSYNC_IN  => as_input_vsync,
    HSYNC_IN  => as_input_hsync,
    STROBE_IN => as_input_strobe,
    DATA_IN   => as_input_data,
    XRES_IN   => as_input_xres,
    YRES_IN   => as_input_yres,
    
    SYNC_ERROR_IN  => as_input_syncerror,
    PIXEL_ERROR_IN => as_input_pixelerror,
    STALL_OUT      => as_input_stall,

    -- OUT ports
    VSYNC_OUT  => as_ouput_vsync,
    HSYNC_OUT  => as_ouput_hsync,
    STROBE_OUT => as_ouput_strobe,
    DATA_OUT   => as_ouput_data,
    XRES_OUT   => as_ouput_xres,
    YRES_OUT   => as_ouput_yres,
    
    SYNC_ERROR_OUT  => as_ouput_syncerror,
    PIXEL_ERROR_OUT => as_ouput_pixelerror,
    STALL_IN        => as_ouput_stall,
    
    -- control / state
    control       => as_invert_0_control,
    control_reset => as_invert_0_control_reset,
    state         => as_invert_0_state
  );


VSYNC_OUT <= as_ouput_vsync;
HSYNC_OUT <= as_ouput_hsync;
STROBE_OUT <= as_ouput_strobe;
DATA_OUT <= as_ouput_data;
XRES_OUT <= as_ouput_xres;
YRES_OUT <= as_ouput_yres;
SYNC_ERROR_OUT <= as_ouput_syncerror;
PIXEL_ERROR_OUT <= as_ouput_pixelerror;
as_ouput_stall <= STALL_IN;



end mod_inst;

