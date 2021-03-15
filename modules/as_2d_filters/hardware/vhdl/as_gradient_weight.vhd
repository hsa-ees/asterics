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
-- Entity:         as_gradient_weight
--
-- Company:        University of Applied Sciences, Augsburg, Germany
--                 Efficient Embedded Systems Group
--                 http://ees.hs-augsburg.de
--
-- Author:         Markus Bihler
--
-- Modified:       2017-06-07
--
-- Description:    Adds two sobel values for calculating gradient 
--                 magnitude (Sx + Sy = MAGxy), delay of 1 clk cycle 
--                 !!!!EXCPECTS SIGNED VALUES AT DATA_IN!!!!
--                 !!!!RETURNS UNSIGNED VALUES AT data_out!!!!
--
------------------------------------------------------------------------
--! @file  as_gradient_weight.vhd
--! @brief X, Y gradient data weight combiner
--! @addtogroup asterics_modules
--! @{
--! @defgroup as_gradient_weight as_gradient_weight: Gradient Weight
--! Adds two sobel values for calculating gradient 
--! magnitude (Sx + Sy = MAGxy), delay of 1 clk cycle 
--! @note Expects SIGNED values at data_in!
--! @note Returns UNSIGNED values at data_out!
--! For use in 2D Window Pipeline systems.
--! @}
----------------------------------------------------------------------------------

--! @addtogroup as_gradient_weight
--! @{


library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

library asterics;
use asterics.as_filter_mask.all;

entity as_gradient_weight is
  generic(
        DIN_WIDTH : integer := 8
  );
  port(
    clk : in std_logic;
    reset : in std_logic;
      
    strobe_in : in std_logic;
    -- !!SIGNED!!
    data1_in : in  std_logic_vector(DIN_WIDTH - 1 downto 0);
    data2_in : in  std_logic_vector(DIN_WIDTH - 1 downto 0);
    -- !!SIGNED!!
  
    -- !!UNSIGNED!!
    data_out : out  std_logic_vector(DIN_WIDTH - 1 downto 0)
    -- !!UNSIGNED!!
  );
end as_gradient_weight;

--! @}

architecture RTL of as_gradient_weight is
  signal s_sum, s_data1_abs, s_data2_abs : unsigned(data1_in'RANGE); -- +1 Bit due to addition
begin 
  
  s_data1_abs <= unsigned(abs(signed(data1_in)));
  s_data2_abs <= unsigned(abs(signed(data2_in)));
  s_sum <= s_data1_abs + s_data2_abs when s_data1_abs(s_data1_abs'LENGTH-1) /= '1' 
                                     or s_data2_abs(s_data2_abs'LENGTH-1) /= '1'
                                     else (others => '1');
  --s_sum <= abs(signed(data1_in)) + abs(signed(data2_in));
  p_add_img : process(clk)
  begin
    if rising_edge(clk) then
      if reset = '1' then
        data_out <= (others => '0');
      elsif strobe_in = '1' then
        -- no overflow possible (signed bit is used for additional bit due to addition)
        data_out <= std_logic_vector(s_sum(s_sum'LENGTH-1 downto 0));
      end if;
    end if;
  end process;
end architecture;
