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
-- Entity:         AS_CORDIC_PKG
--
-- Company:        University of Applied Sciences, Augsburg, Germany
--                 Efficient Embedded Systems Group
--                 http://ees.hs-augsburg.de
--
-- Author:         Markus Bihler
--
-- Modified:       2017-06-07
--
-- Description:    Defines angles and constants for the 
--                 as_cordic_direction module.
--
------------------------------------------------------------------------
--! @file  as_cordic_pkg.vhd
--! @brief Support package for as_cordic_direction.
----------------------------------------------------------------------------------

--! @addtogroup as_cordic_direction_internals
--! @{

library IEEE;
use IEEE.STD_LOGIC_1164.all;
use IEEE.NUMERIC_STD.ALL;

package AS_CORDIC_PKG is
  function addBits(constant step : natural) return natural;

constant c_max_steps : natural := 9;
constant c_angle_width : natural := 10;
constant c_angle_point_pos : natural := 8;
constant c_90_deg :signed(c_angle_width downto 0) :=  to_signed(256,c_angle_width+1); -- 90*0.711111111111*2**(10-7)
constant c_180_deg :signed(c_angle_width downto 0) :=  to_signed(512,c_angle_width+1); -- 90*0.711111111111*2**(10-7)
constant c_22_5_deg :signed(c_angle_width downto 0) :=  to_signed(64,c_angle_width+1); -- 90*0.711111111111*2**(10-7)
constant c_67_5_deg :signed(c_angle_width downto 0) :=  to_signed(192,c_angle_width+1); -- 90*0.711111111111*2**(10-7)
constant c_m22_5_deg :signed(c_angle_width downto 0) :=  to_signed(-64,c_angle_width+1); -- 90*0.711111111111*2**(10-7)
constant c_m67_5_deg :signed(c_angle_width downto 0) :=  to_signed(-192,c_angle_width+1); -- 90*0.711111111111*2**(10-7)
type t_atan_list is array(0 to c_max_steps-1) of signed(c_angle_width-1 downto 0);
constant c_atan_list : t_atan_list := (to_signed(128,c_angle_width),
                                       to_signed(76,c_angle_width),
                                       to_signed(40,c_angle_width),
                                       to_signed(20,c_angle_width),
                                       to_signed(10,c_angle_width),
                                       to_signed(5,c_angle_width),
                                       to_signed(3,c_angle_width),
                                       to_signed(1,c_angle_width),
                                       to_signed(1,c_angle_width));

end AS_CORDIC_PKG;

--! @}

package body AS_CORDIC_PKG is
  
  function addBits(constant step : natural) return natural is
    variable v_bit_counter : natural := 0;
  begin
    for i in 0 to step loop
      v_bit_counter := v_bit_counter + i;
    end loop;
    return v_bit_counter;
  end addBits;
 
end AS_CORDIC_PKG;
