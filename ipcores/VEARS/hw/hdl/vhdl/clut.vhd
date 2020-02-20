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
-- Copyright (C) 2010-2019 Werner Landsperger and
--                         Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- File:           clut.vhd
-- Entity:         clut
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
-- Author:         Werner Landsperger
-- Create Date:    06/11/2009
--
-- Version:  1.0
-- Modified:       * 16/11/2013 by Michael Schaeferling
--                 * 12/09/2019 by Michael Schaeferling
--
-- Description:    Color look up table for the overlay:
--                 three colors are selected from input vectors, 
--                 the fourth color is 'transparent'.
----------------------------------------------------------------------------------


library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use IEEE.STD_LOGIC_UNSIGNED.ALL;


entity clut is
  port(
    color_select : in  std_logic_vector( 1 downto 0); -- Input colour to draw
    color_1      : in  std_logic_vector(23 downto 0); -- first colour defined by software
    color_2      : in  std_logic_vector(23 downto 0); -- second colour defined by software
    color_3      : in  std_logic_vector(23 downto 0); -- third colour defined by software
    color_out    : out std_logic_vector(23 downto 0)  -- output colour to draw
  );
end clut;

architecture RTL of clut is


begin

p1: process (color_select, color_1, color_2, color_3)
begin
    case color_select is
        when "00" => color_out <= (others => '0'); -- this one will be dropped in another module anyways
        when "01" => color_out <= color_1;
        when "10" => color_out <= color_2;
        when "11" => color_out <= color_3;
        when others => null;
    end case;
end process;

end RTL;
