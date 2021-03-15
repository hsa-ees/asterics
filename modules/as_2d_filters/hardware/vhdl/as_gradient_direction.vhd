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
-- Entity:         as_gradient_direction
--
-- Company:        University of Applied Sciences, Augsburg, Germany
--                 Efficient Embedded Systems Group
--                 http://ees.hs-augsburg.de
--
-- Author:         Markus Bihler
--
-- Modified:       2017-06-07
--
-- Description:    Sets coarse gradient direction for each pixel (delay: 1 clk)
--                 INPUT: sobel x and sobel y image
--                 OUTPUT: 2Bit Vector (00 = 0/180, 01 = 45/225, 10 = 90/270, 11=135/315)
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
--! @file  as_gradient_direction.vhd
--! @brief Coarse gradient calculator
--! @addtogroup asterics_modules
--! @{
--! @defgroup as_gradient_direction as_gradient_direction: Gradient Direction Calculator
--! Sets coarse gradient direction for each pixel (delay: 1 clk)
--! INPUT: sobel x and sobel y image
--! OUTPUT: 2Bit Vector (00 = 0/180, 01 = 45/225, 10 = 90/270, 11=135/315)
--! For use in 2D Window Pipeline systems.
--! @}
----------------------------------------------------------------------------------

--! @addtogroup as_gradient_direction
--! @{

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

library asterics;
use asterics.as_filter_mask.all;

entity as_gradient_direction is
  generic(
    DIN_WIDTH : integer := 8
    );
    port(
        clk   : in std_logic;
        reset : in std_logic;
        
        strobe_in : in  std_logic;
        data_x_in : in  std_logic_vector(DIN_WIDTH - 1 downto 0);
        data_y_in : in  std_logic_vector(DIN_WIDTH - 1 downto 0);
        
        data_out  : out  std_logic_vector(1 downto 0)
    );
end as_gradient_direction;

--! @}

architecture RTL of as_gradient_direction is
  -- tan(22,5) = 0.4142135624 (10) =  0,0110101 (2)
  -- arctan(0.5) = 26.565; delta = 4,065
  -- arctan(0.375) = 20.556; delta = 1,944
  
  -- 1/tan(22,5) = 2.4142135624 (10) = 10,0110101 (2)
  -- arctan(1/2) = 26.565; delta = 4,065
  -- ====> arctan(1/2,5) = 21,801; delta = +0,699 <====
  -- for 67.5 :
  -- ====> arctan(2,5) = 68,199; delta = -0,699 <====
  -- ==> 
  
  -- signals for multiplying DATA_IN by 2.5
  signal s_dataX_abs     : unsigned(DIN_WIDTH-1 downto 0); -- |data_x_in|
  signal s_dataX_mul_2   : unsigned(DIN_WIDTH   downto 0); -- |data_x_in| * 2
  signal s_dataX_mul_0_5 : unsigned(DIN_WIDTH-2 downto 0); -- |data_x_in| * 0.5
  signal s_dataX_mul_2_5 : unsigned(DIN_WIDTH-2 downto 0); -- |data_x_in| * 2.5
  signal s_dataY_abs     : unsigned(DIN_WIDTH-1 downto 0); -- |data_y_in|
  signal s_dataY_mul_2   : unsigned(DIN_WIDTH   downto 0); -- |data_y_in| * 2
  signal s_dataY_mul_0_5 : unsigned(DIN_WIDTH-2 downto 0); -- |data_y_in| * 0.5
  signal s_dataY_mul_2_5 : unsigned(DIN_WIDTH+1 downto 0); -- |data_y_in| * 2.5
  
begin
  s_dataX_abs <= unsigned(abs(signed(data_x_in)));
  s_dataX_mul_0_5 <= s_dataX_abs(s_dataX_abs'LENGTH-1 downto 1);
  s_dataX_mul_2 <= resize(s_dataX_abs*2, s_dataX_mul_2'LENGTH);
--  s_dataX_mul_0_5 <= s_dataX_abs(DIN_WIDTH-1 downto 1); -- divide by 2 (right shift)
  s_dataX_mul_2_5 <= resize(s_dataX_mul_2, s_dataX_mul_2_5'LENGTH) + resize(s_dataX_mul_0_5, s_dataX_mul_2_5'LENGTH);
  
  s_dataY_abs <= unsigned(abs(signed(data_y_in)));
  s_dataY_mul_0_5 <= s_dataY_abs(s_dataY_abs'LENGTH-1 downto 1);
  s_dataY_mul_2 <= resize(s_dataY_abs*2, s_dataX_mul_2'LENGTH);
--  s_dataY_mul_0_5 <= s_dataY_abs(DIN_WIDTH-1 downto 1); -- divide by 2 (right shift)
  s_dataY_mul_2_5 <= resize(s_dataY_mul_2, s_dataY_mul_2_5'LENGTH) + resize(s_dataY_mul_0_5, s_dataY_mul_2_5'LENGTH);
  
  
  p_feature_direction : process(clk)
  begin
    if rising_edge(clk) then
      if reset = '1' then
        data_out <= c_0_deg;
    
    -- |data_y_in| < tan(22.5) * |data_x_in| => 0/180 => 00
    -- |data_y_in| * 1/tan(22.5) < |data_x_in| => 0/180 => 00
    --
    -- |data_x_in| < tan(22.5) * |data_y_in| => 90/270 => 10
    -- |data_x_in| * 1/tan(22.5) < |data_y_in| => 90/270 => 10
    --
    -- |data_x_in| < 0 AND |data_y_in| < 0
    --      OR |data_x_in| < 0 AND |data_y_in| < 0 => 45/225 => 01
    --
    -- |data_x_in| > 0 AND |data_y_in| < 0
    --      OR |data_x_in| < 0 AND |data_y_in| > 0 => 45/225 => 01
      elsif strobe_in = '1' then
      -- |data_y_in| < tan(22.5) * |data_x_in| => 0/180 => 00
      -- |data_y_in| * 1/tan(22.5) < |data_x_in| => 0/180 => 00
        --if s_dataY_abs <= s_dataX_mul_0_5 then
        if s_dataY_mul_2_5 <= s_dataX_abs then -- 0 gradient / 90 edge
          data_out <= c_0_deg;
          
      -- |data_x_in| < tan(22.5) * |data_y_in| => 90/270 => 10
      -- |data_x_in| * 1/tan(22.5) < |data_y_in| => 90/270 => 10
        elsif s_dataX_mul_2_5 <= s_dataY_abs then -- 90 gradient / 0 edge
          data_out <= c_90_deg;
          
      -- data_x_in < 0 AND data_y_in < 0
      --      OR data_x_in < 0 AND data_y_in < 0 => 45/225 => 01
        elsif (data_x_in(data_x_in'LENGTH-1) = data_y_in(data_y_in'LENGTH-1)) then
          data_out <= c_45_deg;

      -- data_x_in > 0 AND data_y_in < 0
      --      OR data_x_in < 0 AND data_y_in > 0 => 45/225 => 01
      --  elsif (data_x_in(data_x_in'LENGTH-1) = not data_y_in(data_y_in'LENGTH-1)) then
        else
          data_out <= c_135_deg;
        end if;
      end if;
    end if;
  end process;
 
 

end architecture;

