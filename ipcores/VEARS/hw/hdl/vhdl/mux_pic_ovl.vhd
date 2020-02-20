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
-- File:           mux_pic_ovl.vhd
-- Entity:         mux_pic_ovl
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
-- Description:    Switches between the overlay and the image data.
----------------------------------------------------------------------------------


library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;


entity mux_pic_ovl is
  port(
    data_sel : in  std_logic_vector(1 downto 0);
    ovl_en   : in  std_logic;
    data_pic : in  std_logic_vector(23 downto 0);
    data_ovl : in  std_logic_vector(23 downto 0);
    data_out : out std_logic_vector(23 downto 0)
  );
end mux_pic_ovl;

architecture RTL of mux_pic_ovl is


begin

process (data_sel, ovl_en, data_pic, data_ovl)
begin
    if ( ovl_en = '0' ) then
        data_out <= data_pic;
    else
        case data_sel is
            when "00"   => data_out <= data_pic;   --sets picture data to data output (transparent overlay)
            when others => data_out <= data_ovl;   --sets overlay data to data output
        end case;
    end if;
end process;

end RTL;
