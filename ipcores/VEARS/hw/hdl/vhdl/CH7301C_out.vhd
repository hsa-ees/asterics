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
-- Copyright (C) 2010-2019 Hochschule Augsburg, University of Applied Sciences
--                         and Stefan Durner
----------------------------------------------------------------------------------
-- File:           CH7301C_out.vhd
-- Entity:         CH7301C_out
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
-- Author:         Michael Schaeferling, Stefan Durner
-- Create Date:    06/11/2010
--
-- Version:  1.0
-- Modified:       * 16/11/2013 by Michael Schaeferling
--                 * 14/06/2017 by Michael Schaeferling
--                 * 05/07/2019 by Michael Schaeferling
--                 * 12/09/2019 by Michael Schaeferling
--
-- Description:    Multiplexes the 24-bit RGB-Input to 12-bit 
--                 DVI-Output for Chrontel CH7301C.
----------------------------------------------------------------------------------


library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use IEEE.STD_LOGIC_UNSIGNED.ALL;



entity CH7301C_out is
  port(
    clk       : in std_logic;
    data_sel  : in std_logic;
    pix_red   : in std_logic_vector(7 downto 0);
    pix_green : in std_logic_vector(7 downto 0);
    pix_blue  : in std_logic_vector(7 downto 0);
    pix_hsync : in std_logic;
    pix_vsync : in std_logic;
    ch7301c_enable_in  : in std_logic;
    -- outputs:
    ch7301c_enable_out : out std_logic;
    ch7301c_data_out   : out std_logic_vector(11 downto 0);
    ch7301c_hsync      : out std_logic;
    ch7301c_vsync      : out std_logic
  );
end CH7301C_out;

architecture RTL of CH7301C_out is

----------     signals for internal use     ---------
signal muxdata : std_logic_vector(11 downto 0) := (others => '0');
----------


begin
    
-- multiplex 24-bit rgb-data to 12-bit dvi-data
-- -> this is done with double pix clock (pix clock is clk/2, using data_sel here for pos/neg edge):
process (data_sel, pix_red, pix_green, pix_blue) 
begin
    if (data_sel = '0') then
        muxdata <= pix_green(3 downto 0) & pix_blue(7 downto 0);
    else
        muxdata <= pix_red(7 downto 0) & pix_green(7 downto 4);
    end if;
end process;


-- final dvi-data for Chrontel CH7301C
process (clk)
begin
    if(clk'event and clk = '1') then
        ch7301c_hsync <= pix_hsync;
        ch7301c_vsync <= pix_vsync;
        ch7301c_enable_out <= ch7301c_enable_in;
        ch7301c_data_out <= muxdata;
    end if;
end process; 

end RTL;
