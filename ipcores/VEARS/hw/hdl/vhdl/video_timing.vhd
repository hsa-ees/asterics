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
-- Copyright (C) 2010-2019 Matthias Pohl, Markus Litzel, Werner Landsperger and
--                         Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- File:           video_timing.vhd
-- Entity:         video_timing
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
-- Author:         Matthias Pohl, Markus Litzel, Werner Landsperger,
--                 Michael Schäferling
-- Create Date:    12/10/2009
--
-- Version:  1.0
-- Modified:       * 16/11/2013 by Michael Schaeferling
--                   - major cleanup, was 'vga_timing'
--                 * 05/07/2019 by Michael Schaeferling
--                 * 12/09/2019 by Michael Schaeferling
--
-- Description:    Video timing generator.
----------------------------------------------------------------------------------


library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use IEEE.STD_LOGIC_UNSIGNED.ALL;
use IEEE.MATH_REAL.ceil;
use IEEE.MATH_REAL.log2;


entity video_timing is
  generic(
    PREBUFFER_LINES : integer;
    VIDEO_TIMING_LINEBUFF_ADDR_WIDTH : integer;
    H_Tpw : integer;    -- pulse width (horizontal)
    H_Tbp : integer;    -- back porch (horizontal)
    H_Tdisp : integer;  -- display time (horizontal)
    H_Tfp : integer;    -- front porch (horizontal)
    H_SP : std_logic;   -- sync polarity (horizontal)
    V_Tpw : integer;    -- pulse width (vertical)
    V_Tbp : integer;    -- back porch (vertical)
    V_Tdisp : integer;  -- display time (vertical)
    V_Tfp : integer;    -- front porch (vertical)
    V_SP : std_logic    -- sync polarity (vertical)
  );
  port(
    clk   : in std_logic;
    reset : in std_logic;

    pix_chg : out std_logic; -- for CH7301C_out module

    pixel_data : in std_logic_vector(23 downto 0); --data input to draw

    trigger_line : out std_logic;                      --toggles to trigger data fetch into linebuffer
    h_count      : out std_logic_vector (VIDEO_TIMING_LINEBUFF_ADDR_WIDTH - 1 downto 0); --horizontal counter
    v_sel        : out std_logic;                      --vertical selector

    pix_red   : out std_logic_vector(7 downto 0);   -- red data output
    pix_green : out std_logic_vector(7 downto 0);   -- green data output
    pix_blue  : out std_logic_vector(7 downto 0);   -- blue data output
    pix_hsync : out std_logic;                      -- hsync output
    pix_vsync : out std_logic;                      -- vsync output
    pix_de    : out std_logic                       -- data enable output
  );
end video_timing;

architecture RTL of video_timing is



signal enable : std_logic;


-- full frame counters (including blanking area)
constant c_horizontal_counter_width : integer := INTEGER(CEIL(LOG2(REAL(H_Tfp + H_Tpw + H_Tbp + H_Tdisp))));
constant c_vertical_counter_width   : integer := INTEGER(CEIL(LOG2(REAL(V_Tfp + V_Tpw + V_Tbp + V_Tdisp))));
signal r_horizontal_counter : std_logic_vector (c_horizontal_counter_width downto 0);
signal r_vertical_counter   : std_logic_vector (c_vertical_counter_width   downto 0);


-- counters for visible area:
constant c_h_vis_count_width : integer := INTEGER(CEIL(LOG2(REAL(H_Tdisp))));
constant c_v_vis_count_width   : integer := INTEGER(CEIL(LOG2(REAL(V_Tdisp))));
signal r_h_vis_count : std_logic_vector (c_h_vis_count_width-1 downto 0);
signal r_v_vis_count : std_logic_vector (c_v_vis_count_width   downto 0); -- 1 bit extra as V_Tdisp must fit into this register


signal trigger_line_0 : std_logic;

------------------------------------------------------
begin


-- make sure data widths to comply:
ASSERT VIDEO_TIMING_LINEBUFF_ADDR_WIDTH = c_h_vis_count_width
  REPORT "Width of 'VIDEO_TIMING_LINEBUFF_ADDR_WIDTH' and 'c_h_vis_count_width' do not match!"
  SEVERITY FAILURE;


--to address_calculation:
h_count <= r_h_vis_count;
v_sel <= r_v_vis_count(0);

pix_chg <= enable;

trigger_line <= trigger_line_0;

----------     drawing     ----------
process (clk)
begin
  if clk'event and clk = '1' then

    if (reset = '1') then
      pix_hsync <= '0';
      pix_vsync <= '0';
      pix_red     <= X"00";
      pix_green   <= X"00";
      pix_blue    <= X"00";
      pix_de      <= '0';

      r_horizontal_counter <= (others => '0');
      r_vertical_counter <= (others => '0');
      
      r_h_vis_count <= (others => '0');
      r_v_vis_count <= (others => '0');

      enable <= '0';
      trigger_line_0 <= '0';
    else

      enable <= not(enable);

      if ( enable = '1' ) then

        if    (r_horizontal_counter >= (H_Tpw + H_Tbp) )
          and (r_horizontal_counter <  (H_Tpw + H_Tbp + H_Tdisp) )
          and (r_vertical_counter   >= (V_Tpw + V_Tbp) )
          and (r_vertical_counter   <  (V_Tpw + V_Tbp + V_Tdisp) )
        then

          ----------     visible area     ----------
          r_h_vis_count <= r_h_vis_count + 1;

          if (r_h_vis_count = H_Tdisp-1) then
            r_h_vis_count <= (others => '0');
            r_v_vis_count <= r_v_vis_count + 1;
          end if;


          if (r_v_vis_count = V_Tdisp) then
            r_v_vis_count <= (others => '0');
          end if;

          pix_red     <= pixel_data(23 downto 16);
          pix_green   <= pixel_data(15 downto  8);
          pix_blue    <= pixel_data( 7 downto  0);
          pix_de      <= '1'; -- enable data-output when in visible area

        else
          ----------     blank area (vertical and horizontal frontporch, sync-time and backporch)     ----------
          pix_red     <= X"00";
          pix_green   <= X"00";
          pix_blue    <= X"00";
          pix_de      <= '0'; -- disable when not in visible area
          -----------------------------------------------------------------------------------------
        end if;

        -- Indicator for new line:
        -- and lines are in visible area -> toggle indicator trigger_line_0
        if    (r_horizontal_counter = 0 )
          and (r_vertical_counter >= (V_Tpw + V_Tbp - PREBUFFER_LINES) )
          and (r_vertical_counter <  (V_Tpw + V_Tbp + V_Tdisp - PREBUFFER_LINES) )
        then
          trigger_line_0 <= not(trigger_line_0);
        end if;

        ----------     HSYNC     ----------
        if (r_horizontal_counter < H_Tpw ) then
           pix_hsync <= H_SP;
        else
           pix_hsync <= not(H_SP);
        end if;
        -----------------------------------

        ----------     VSYNC     ----------
        if (r_vertical_counter < V_Tpw ) then
          pix_vsync <= V_SP;
        else
          pix_vsync <= not(V_SP);
        end if;
        -----------------------------------


        ----------     reset horizontal and vertical counter at screen end    ----------
        if (r_horizontal_counter = (H_Tpw + H_Tbp + H_Tdisp + H_Tfp - 1)) then
          r_horizontal_counter <= (others => '0');
          r_vertical_counter <= r_vertical_counter + 1;
        else
          r_horizontal_counter <= r_horizontal_counter + 1;
        end if;

        if (r_vertical_counter = (V_Tpw + V_Tbp + V_Tdisp + V_Tfp - 1)) then
          r_vertical_counter <= (others => '0');
        end if;
        ---------------------------------------------------------------------------------

      end if;
    end if;
  end if;
end process;
---------------------------------------


end RTL;
