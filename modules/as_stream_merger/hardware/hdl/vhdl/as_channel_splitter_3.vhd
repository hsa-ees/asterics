----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_channel_splitter_3
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Philip Manke
--
-- Modified:       
--
-- Description:    This module splits a color data signal into its individual channels
----------------------------------------------------------------------------------
--  This program is free software; you can redistribute it and/or
--  modify it under the terms of the GNU Lesser General Public
--  License as published by the Free Software Foundation; either
--  version 3 of the License, or (at your option) any later version.
--  
--  This program is distributed in the hope that it will be useful,
--  but WITHOUT ANY WARRANTY; without even the implied warranty of
--  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
--  Lesser General Public License for more details.
--  
--  You should have received a copy of the GNU Lesser General Public License
--  along with this program; if not, see <http://www.gnu.org/licenses/>
--  or write to the Free Software Foundation, Inc.,
--  51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
----------------------------------------------------------------------------------
--! @file  as_channel_splitter_3.vhd
--! @brief Split an AsStream data signal into 3 channels
--! @addtogroup asterics_modules
--! @{
--! @defgroup as_channel_splitter_3 as_channel_splitter_3: AsStream Channel Splitter
--! This module splits the data signal of the input AsStream into 3 separate 
--! AsStream interfaces.
--! Useful for splitting, for example, an RGB data stream into its components.
--! @}
----------------------------------------------------------------------------------

--! @addtogroup as_channel_splitter_3
--! @{


library ieee;
use ieee.std_logic_1164.all;


entity as_channel_splitter_3 is
    generic(
        DIN_WIDTH : integer := 8;
        DOUT_WIDTH : integer := 8
    );
    port (
        clk         : in  std_logic;
        reset       : in  std_logic;


        -- AsWindow in ports
        strobe_in    : in  std_logic;
        data_in      : in  std_logic_vector(DIN_WIDTH - 1 downto 0);
        hsync_in     : in  std_logic;
        vsync_in     : in  std_logic;
        stall_in     : out std_logic;
        
        -- AsStream out ports:
        strobe_out_0 : out std_logic;
        data_out_0   : out std_logic_vector(DOUT_WIDTH - 1 downto 0);
        hsync_in_0   : out std_logic;
        vsync_in_0   : out std_logic;
        stall_out_0  : in  std_logic;

        strobe_out_1 : out std_logic;
        data_out_1   : out std_logic_vector(DOUT_WIDTH - 1 downto 0);
        hsync_in_1   : out std_logic;
        vsync_in_1   : out std_logic;
        stall_out_1  : in  std_logic;

        strobe_out_2 : out std_logic;
        data_out_2   : out std_logic_vector(DOUT_WIDTH - 1 downto 0);
        hsync_in_2   : out std_logic;
        vsync_in_2   : out std_logic;
        stall_out_2  : in  std_logic

    );
end as_channel_splitter_3;

--! @}

architecture RTL of as_channel_splitter_3 is
begin

    strobe_out_0 <= strobe_in;
    data_out_0   <= data_in(DOUT_WIDTH - 1 downto 0);
    hsync_in_0   <= hsync_in;
    vsync_in_0   <= vsync_in;

    strobe_out_1 <= strobe_in;
    data_out_1   <= data_in(DOUT_WIDTH - 1 + DOUT_WIDTH downto DOUT_WIDTH);
    hsync_in_1   <= hsync_in;
    vsync_in_1   <= vsync_in;

    strobe_out_2 <= strobe_in;
    data_out_2   <= data_in(DOUT_WIDTH - 1 + 2 * DOUT_WIDTH downto 2 * DOUT_WIDTH);
    hsync_in_2   <= hsync_in;
    vsync_in_2   <= vsync_in;

    stall_in <= stall_out_0 or stall_out_1 or stall_out_2;
end RTL;
    