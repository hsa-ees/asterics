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
-- File:           linebuffer.vhd
-- Entity:         linebuffer
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
-- Create Date:    11/11/2009
--
-- Version:  1.0
-- Modified:       * 16/11/2013 by Michael Schaeferling
--                 * 12/09/2019 by Michael Schaeferling
--
-- Description:    Buffer for (image and overlay) lines in BlockRAM.
----------------------------------------------------------------------------------


library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use IEEE.STD_LOGIC_UNSIGNED.ALL;


entity linebuffer is
  generic (
    ADDR_WIDTH: integer
  );
  port (
    clk_wr  : in  std_logic;
    clk_rd  : in  std_logic;

    wr_en   : in  std_logic;
    wr_addr : in  std_logic_vector(ADDR_WIDTH-1 downto  0);
    wr_data : in  std_logic_vector(31 downto  0);

    rd_addr : in  std_logic_vector(ADDR_WIDTH-1 downto  0);
    rd_data : out std_logic_vector(31 downto  0)
  );
end linebuffer;


architecture RTL of linebuffer is

constant words: integer := (2 ** ADDR_WIDTH);
type ram_type is array (0 to words-1) of std_logic_vector (31 downto 0);

-- memory test pattern: this should be visible when VEARS gets the correct clocks but yet isn't enabled to read data from memory
signal RAM : ram_type := (
16#0000# => X"ff00ff00",
16#0001# => X"ffff0000",
16#0002# => X"ffffffff",
16#0003# => X"00000000",
16#0004# => X"ffffffff",
16#0005# => X"ffffffff",
16#0006# => X"ffffffff",
16#0007# => X"ffffffff",
16#0008# => X"ffffffff",
16#0009# => X"00000000",
16#000A# => X"00000000",
16#000B# => X"00000000",
16#000C# => X"00000000",
16#000D# => X"ffffffff",
16#000E# => X"ffffffff",
16#000F# => X"ffffffff",
16#0010# => X"ffffffff",
16#0011# => X"00000000",
16#0012# => X"00000000",
16#0013# => X"ffffffff",
16#0014# => X"ffffffff",
16#0015# => X"00000000",
16#0016# => X"ffffffff",
16#0017# => X"0000ffff",
16#0018# => X"00ff00ff",
others => X"00000000");

begin


process (clk_wr) 
begin
    if (clk_wr'event and clk_wr = '1') then
        if (wr_en = '1') then
            RAM(conv_integer(wr_addr)) <= wr_data;
        end if;
    end if;
end process;


process (clk_rd) 
begin
    if (clk_rd'event and clk_rd = '1') then
        rd_data <= RAM(conv_integer(rd_addr));
    end if;
end process;


end RTL;
