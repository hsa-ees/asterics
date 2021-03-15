------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2017 Hochschule Augsburg, University of Applied Sciences
------------------------ LICENSE ----------------------------------------
-- This program is free software; you can redistribute it and/or
-- modify it under the terms of the GNU Lesser General Public
-- License as published by the Free Software Foundation; either
-- version 3 of the License, or (at your option) any later version.
-- 
-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
-- Lesser General Public License for more details.
-- 
-- You should have received a copy of the GNU Lesser General Public License
-- along with this program; if not, see <http://www.gnu.org/licenses/>
-- or write to the Free Software Foundation, Inc.,
-- 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
------------------------------------------------------------------------
-- Entity:         as_cordic_direction
--
-- Company:        University of Applied Sciences, Augsburg, Germany
--                 Efficient Embedded Systems Group
--                 http://ees.hs-augsburg.de
--
-- Author:         Markus Bihler
--
-- Modified:       2017-06-07;
--                 2020-05-14: Philip Manke - Integrate reduced direction calculation
--
-- Description:    Sets gradient direction for each pixel (delay: number 
--                 of pipeline stages)
--                 INPUT: sobel x and sobel y image
--                 OUTPUT: N Bit Vector angle in degree
--                         
--                     00:          01:        10:          11:
--                         0 0 0       0 0 x        0 x 0        x 0 0
--                         x x x       0 x 0        0 x 0        0 x 0
--                         0 0 0       x 0 0        0 x 0        0 0 x      
--
--                 Expected Sobel Filter Directions:         
--                 
--                 X:       Y:
--                              |
--                   ----->     |
--                              V
--                 
--                 Example:
--                 X:       Y:
--                 -1 0 1   -1-2-1
--                 -2 0 2    0 0 0
--                 -1 0 1    1 2 1
--
------------------------------------------------------------------------
--! @file  as_cordic_direction.vhd
--! @brief This module implements the CORDIC algorithm calculating gradient direction.
--! @addtogroup asterics_modules
--! @{
--! @defgroup as_cordic_direction as_cordic_direction: Cordic Gradient Direction
--! Using two edge image streams (X and Y edges) the implemented CORDIC direction
--! pipeline computes the gradient direction. Both a reduced (resolution 45°)
--! and a full precision (ANGLE_WIDTH bits) direction angle output are available.
--! @}
----------------------------------------------------------------------------------

--! @addtogroup as_cordic_direction
--! @{
--! @defgroup as_cordic_direction_internals Internal Hardware of as_cordic_direction

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

library asterics;
use asterics.as_filter_mask.all;

use work.as_cordic_pkg.all;

entity as_cordic_direction is
  generic(
    DIN_WIDTH : integer;
    CORDIC_STEP_COUNT : natural;
    ANGLE_WIDTH : integer := c_angle_width
  );
  port(
    clk : in std_logic;
    reset : in std_logic;
    
    strobe_in : in  std_logic;
    
    -- !! SIGNED !!
    data_x_in : in  std_logic_vector(DIN_WIDTH - 1 downto 0);
    -- !! SIGNED !!
    data_y_in : in  std_logic_vector(DIN_WIDTH - 1 downto 0);
    
    -- Reduced accuracy direction with 2 bits
    data_out_reduced : out std_logic_vector(1 downto 0);
    -- Full accuracy cordic direction !! SIGNED !!
    data_out_full  : out std_logic_vector(ANGLE_WIDTH downto 0)
  );
end as_cordic_direction;

--! @}

architecture RTL of as_cordic_direction is
  
  component AS_CORDIC_ATAN_PIPE is
  generic(
    gen_step_count  : natural;
    gen_input_width : natural
  );
  port(
    clk           : in std_logic;
    reset         : in std_logic;
    
    strobe_in     : in  std_logic;
    x_in          : in  signed(gen_input_width-1 downto 0);
    y_in          : in  signed(gen_input_width-1 downto 0);
    
    z_out         : out signed(c_angle_width-1 downto 0)
    
  );
  end component;

  signal s_x_abs    : signed(data_x_in'range);
  signal r_x_is_neg : std_logic_vector(CORDIC_STEP_COUNT-1 downto 0);
  signal r_y_is_neg : std_logic_vector(CORDIC_STEP_COUNT-1 downto 0);
  
  signal s_z_out    : signed(c_angle_width-1 downto 0);

  signal cordic_full : signed(c_angle_width downto 0);
  signal cordic_cut : std_logic_vector(c_angle_width - 3 downto 0);
  signal round_bit : unsigned(0 downto 0);
  signal coarse_dir : unsigned(1 downto 0);
  
begin
  -- Full accuracy data output
  data_out_full <= std_logic_vector(unsigned(cordic_full));

  -- Compute a reduced accuracy output
  cordic_cut <= std_logic_vector(cordic_full(c_angle_width - 1 downto 2));
  coarse_dir <= unsigned(cordic_cut(6 downto 5));
  round_bit <= unsigned(cordic_cut(4 downto 4));
  data_out_reduced <= std_logic_vector(coarse_dir + ('0' & round_bit));

  s_x_abs <= abs(signed(data_x_in));

  p_x_y_delay : process(clk)
    
  begin
    if rising_edge(clk) then
      if reset = '1' then
        r_x_is_neg <= (others => '0');
        r_y_is_neg <= (others => '0');
      else
        if strobe_in = '1' then
          -- X
          r_x_is_neg(r_x_is_neg'left-1 downto 0) <= r_x_is_neg(r_x_is_neg'left downto 1); -- shift right
          r_x_is_neg(r_x_is_neg'left) <= data_x_in(data_x_in'left); -- copy sign bit
          -- Y
          r_y_is_neg(r_y_is_neg'left-1 downto 0) <= r_y_is_neg(r_y_is_neg'left downto 1); -- shift right
          r_y_is_neg(r_y_is_neg'left) <= data_y_in(data_y_in'left); -- copy sign bit
        end if;
      end if;
    end if;
  end process; 
  
  CORDIC_PIPE: AS_CORDIC_ATAN_PIPE 
      generic map(
        gen_step_count => CORDIC_STEP_COUNT,
        gen_input_width => DIN_WIDTH
      )
      port map (
        clk           => clk,
        reset         => reset,

        strobe_in     => strobe_in,
        x_in          => s_x_abs,
        y_in          => signed(data_y_in),
        
        z_out         => s_z_out
      );
      
  -- CORDIC output is -90 to +90 degree ==> convert to -180 to 180
  p_180_to_360_deg: process(clk)
  begin
    if rising_edge(clk) then
      if reset = '1' then
        cordic_full <= (others => '0');
      else
        if strobe_in = '1' then
          -- convert to -180 to +180 degree
          if r_x_is_neg(0) = '1' and r_y_is_neg(0) = '0' then -- X was negative, Y positiv --> II Qudrant --> angle = 180-z_out
            cordic_full <= c_180_deg - resize(s_z_out,cordic_full'length);
          elsif r_x_is_neg(0) = '1' and r_y_is_neg(0) = '1' then -- X was negative, Y negative --> III Qudrant --> angle = -180-z_out
            cordic_full <= -c_180_deg - resize(s_z_out,cordic_full'length);
          else -- X was positiv --> I or IV Quadrant --> angle = z_out
            cordic_full <= resize(s_z_out,cordic_full'length);
          end if;
        end if;
      end if;
    end if;
  end process;
 
  -- Generate index for feature algorithm
  -- TODO: DOESNT WORK, use old module in parallel
  --~ p_gen_index : process(clk)
  --~ begin
    --~ if rising_edge(clk) then
      --~ if reset = '1' then
        --~ INDEX_OUT <= (others => '0');
      --~ else
        --~ if strobe_in = '1' then
--~ --                     00:          01:        10:          11:
--~ --                         0 0 0       0 0 x        0 x 0        x 0 0
--~ --                         x x x       0 x 0        0 x 0        0 x 0
--~ --                         0 0 0       x 0 0        0 x 0        0 0 x      
          --~ if c_m22_5_deg < s_z_out and s_z_out <= c_22_5_deg then -- -22.5 to 22.5 deg
            --~ INDEX_OUT <= "00";
          --~ elsif c_22_5_deg < s_z_out and s_z_out <= c_67_5_deg then -- 22.5 to 67.5 deg
            --~ INDEX_OUT <= "01";
          --~ elsif c_m67_5_deg < s_z_out and s_z_out <= c_m22_5_deg then -- -67.5 to -22.5 deg
            --~ INDEX_OUT <= "11";
          --~ else -- 67.5 to 90 deg / -90 to -67.5 deg
            --~ INDEX_OUT <= "10";
          --~ end if;
        --~ end if;
      --~ end if;
    --~ end if;
  --~ end process;
end RTL;

