----------------------------------------------------------------------------------
-- This file is part of V.E.A.R.S.
--
-- V.E.A.R.S. is free software: you can redistribute it and/or modify
-- it under the terms of the GNU Lesser General Public License as published by
-- the Free Software Foundation, either version 3 of the License, or
-- (at your option) any later version.
--
-- V.E.A.R.S. is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
-- GNU Lesser General Public License for more details.
--
-- You should have received a copy of the GNU Lesser General Public License
-- along with V.E.A.R.S. If not, see <http://www.gnu.org/licenses/lgpl.txt>.
--
-- Copyright (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- File:           clocking.vhd
-- Entity:         clocking
--
-- Project Name:   VEARS
--  \\        // ////////     //\\     //////\\    ///////         ////\\\\
--   \\      //  //          //  \\    //    //   /              //  ///   \\
--    \\    //   /////      //    \\   ///////    \\\\\\        ||  |      ||
--     \\  //    //        /////\\\\\  //   \\         /         \\  \\\   //
--      \\//     //////// //        \\ //    \\ ///////            \\\\////
--
-- Company:        University of Applied Sciences, Augsburg, Germany
--
-- Author:         Michael Schaeferling
-- Create Date:    18/01/2018
--
-- Version:  1.0
-- Modified:       * 10/04/2019 by Michael Schaeferling
--                   - Adjust c_CLKFBOUT_MULT_F to better fit VGA timing spec
--                 * 12/09/2019 by Michael Schaeferling
--
-- Description:    The VEARS clocking module generates all needed clocks 
--                 from a given system clock.
----------------------------------------------------------------------------------


library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.MATH_REAL.ALL;


-- Uncomment the following library declaration if instantiating
-- any Xilinx leaf cells in this code.
library UNISIM;
use UNISIM.VComponents.all;


entity clocking is
  generic (
    CLK_IN_FREQ_MHZ : real;
    CLK_OUT_FREQ_MHZ : real
  );
  port (
    clk_in : in  std_logic;
    reset  : in  std_logic;

    clk_out      : out std_logic;
    clk_out_x5   : out std_logic;
    clk_out_x2_p : out std_logic;
    clk_out_x2_n : out std_logic;

    locked : out std_logic
  );
end clocking;

architecture RTL of clocking is


signal clk_fb_out, clk_fb_in : std_logic;
signal clk_gen : std_logic;
signal clk_gen_x5 : std_logic;
signal clk_gen_x2_p, clk_gen_x2_n : std_logic;


type clk_settings_t is record
  divide_f_x1 : real;
  divide_x5 : integer;
  divide_x2 : integer;
end record clk_settings_t;

type clk_settings_array_t is array (0 to 5) of clk_settings_t;

constant c_clk_settings : clk_settings_array_t := ((30.0, 6 ,15), -- (0):  20 -  <40 MHz clk_out
                                                   (20.0, 4 ,10), -- (1):  40 -  <60 MHz clk_out
                                                   (10.0, 2 , 5), -- (2):  60 -  <80 MHz clk_out
                                                   (10.0, 2 , 5), -- (3):  80 - <100 MHz clk_out
                                                   (10.0, 2 , 5), -- (4):  80 - <120 MHz clk_out
                                                   (10.0, 2 , 5)  -- (5):        120 MHz clk_out
                                                  );

constant c_clock_out_range : integer := INTEGER(FLOOR(((CLK_OUT_FREQ_MHZ - 20.0) / 20.0)));
constant c_clk_in_period : real := 1000.0 / CLK_IN_FREQ_MHZ;
constant c_clkfbout_mult_f : real := CLK_OUT_FREQ_MHZ / CLK_IN_FREQ_MHZ * c_clk_settings(c_clock_out_range).divide_f_x1;


attribute CLOCK_BUFFER_TYPE : string;
attribute CLOCK_BUFFER_TYPE of clk_gen: signal is "NONE";
attribute CLOCK_BUFFER_TYPE of clk_gen_x5: signal is "NONE";
attribute CLOCK_BUFFER_TYPE of clk_gen_x2_p: signal is "NONE";
attribute CLOCK_BUFFER_TYPE of clk_gen_x2_n: signal is "NONE";


begin



-- Valid VCO values for Zynq7010 (Zybo): min 600 MHz / max 1200MHz;
-- Following rules must be met:
--  - HDMI clock is pixel clock * 5
--  - CH7301C clock is pixel clock * 2
--  -> thus, only a limited range of values can be set to achieve these constraints.
ASSERT ((CLK_OUT_FREQ_MHZ >= 20.0) and (CLK_OUT_FREQ_MHZ <= 120.0))
  REPORT "Output clock must be in range 20 .. 120 MHz!"
  SEVERITY FAILURE;

  

ClkGen_1: MMCME2_BASE
  generic map(
    BANDWIDTH            => "OPTIMIZED",
    STARTUP_WAIT         => FALSE,

    CLKIN1_PERIOD        => c_clk_in_period,
    REF_JITTER1          => 0.010,

    DIVCLK_DIVIDE        => 1,

    CLKFBOUT_MULT_F      => c_clkfbout_mult_f,
    CLKFBOUT_PHASE       => 0.000,

    CLKOUT0_DIVIDE_F     => c_clk_settings(c_clock_out_range).divide_f_x1,
    CLKOUT0_DUTY_CYCLE   => 0.500,
    CLKOUT0_PHASE        => 0.000,

    CLKOUT1_DIVIDE       => c_clk_settings(c_clock_out_range).divide_x5,
    CLKOUT1_DUTY_CYCLE   => 0.500,
    CLKOUT1_PHASE        => 0.000,

    CLKOUT2_DIVIDE       => c_clk_settings(c_clock_out_range).divide_x2,
    CLKOUT2_DUTY_CYCLE   => 0.500,
    CLKOUT2_PHASE        => 0.000,
    
    CLKOUT3_DIVIDE       => c_clk_settings(c_clock_out_range).divide_x2,
    CLKOUT3_DUTY_CYCLE   => 0.500,
    CLKOUT3_PHASE        => 180.000
  )
  port map
  (
    RST                 => reset,
    LOCKED              => locked,
    PWRDWN              => '0',

    CLKIN1              => Clk_in,

    CLKFBOUT            => clk_fb_out,
    CLKFBOUTB           => open,
    CLKFBIN             => clk_fb_in,

    CLKOUT0             => clk_out,
    CLKOUT0B            => open,

    CLKOUT1             => clk_out_x5,
    CLKOUT1B            => open,

    CLKOUT2             => clk_out_x2_p,
    CLKOUT2B            => open,

    CLKOUT3             => clk_out_x2_n,
    CLKOUT3B            => open,

    CLKOUT4             => open,
    CLKOUT5             => open,
    CLKOUT6             => open
  );


clk_fb_deskew: BUFR
  generic map (
    BUFR_DIVIDE => "1", 
    SIM_DEVICE => "7SERIES" 
  )
  port map (
    I => clk_fb_out,
    O => clk_fb_in,
    CE => '1',
    CLR => '0'
  );


end RTL;
