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
-- File:           mux_1of16_32bit.vhd
-- Entity:         mux_1of16_32bit
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
--                 * 12/09/2019 by Michael Schaeferling
--
-- Description:    Chooses one from 16 pixels in a 32 bit input word,
--                 one pixel has 2 bit.
--                 Used for overlay data demultiplexing.
----------------------------------------------------------------------------------


library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;


entity mux_1of16_32bit is
  port(
    data_sel : in  std_logic_vector( 3 downto  0); -- switch for choosing one of the 16 pixels
    data_in  : in  std_logic_vector(31 downto  0); -- one address (16 pixels) data abut on input
    data_out : out std_logic_vector( 1 downto  0)  -- one pixel (2 bit) data output
  );
end mux_1of16_32bit;


architecture RTL of mux_1of16_32bit is

begin

process (data_sel, data_in)
begin
    case data_sel is
        when "1111" => data_out(1 downto 0) <= data_in( 1 downto  0);
        when "1110" => data_out(1 downto 0) <= data_in( 3 downto  2);
        when "1101" => data_out(1 downto 0) <= data_in( 5 downto  4);
        when "1100" => data_out(1 downto 0) <= data_in( 7 downto  6);
        when "1011" => data_out(1 downto 0) <= data_in( 9 downto  8);
        when "1010" => data_out(1 downto 0) <= data_in(11 downto 10);
        when "1001" => data_out(1 downto 0) <= data_in(13 downto 12);
        when "1000" => data_out(1 downto 0) <= data_in(15 downto 14);
        when "0111" => data_out(1 downto 0) <= data_in(17 downto 16);
        when "0110" => data_out(1 downto 0) <= data_in(19 downto 18);
        when "0101" => data_out(1 downto 0) <= data_in(21 downto 20);
        when "0100" => data_out(1 downto 0) <= data_in(23 downto 22);
        when "0011" => data_out(1 downto 0) <= data_in(25 downto 24);
        when "0010" => data_out(1 downto 0) <= data_in(27 downto 26);
        when "0001" => data_out(1 downto 0) <= data_in(29 downto 28);
        when "0000" => data_out(1 downto 0) <= data_in(31 downto 30);
        when others => null;
    end case;
end process;

end RTL;
