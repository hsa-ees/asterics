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
-- Copyright (C) 2010-2019 Markus Litzel and
--                         Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- File:           mux_1of4_32bit.vhd
-- Entity:         mux_1of4_32bit
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
-- Author:         Markus Litzel
-- Create Date:    28/10/2009 
--
-- Version:  1.0
-- Modified:       * 16/11/2013 by Michael Schaeferling
--                   - major cleanup, was 'bit32to24_mux'
--                 * 12/09/2019 by Michael Schaeferling
--
-- Description:    Chooses one from 4 pixels in a 32 bit input word,
--                 one pixel has 8 bit.
--                 Used for grayscale image data demultiplexing.
----------------------------------------------------------------------------------


library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;


entity mux_1of4_32bit is
  port(
    data_sel : in  std_logic_vector( 1 downto 0);
    data_in  : in  std_logic_vector(31 downto 0);
    data_out : out std_logic_vector( 7 downto 0)
  );
end mux_1of4_32bit;


architecture RTL of mux_1of4_32bit is

begin

process (data_sel, data_in)
begin
    case data_sel is
        when "00" => data_out <= data_in(31 downto 24);
        when "01" => data_out <= data_in(23 downto 16);
        when "10" => data_out <= data_in(15 downto  8);
        when "11" => data_out <= data_in( 7 downto  0);
        when others => null;
    end case;
end process;

end RTL;
