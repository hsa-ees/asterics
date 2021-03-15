----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_stream_merger_8_dynamic
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Philip Manke
--
-- Modified:       
--
-- Description:    This module merges eight as_stream data streams.
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
--! @file  as_stream_merger_8_dynamic.vhd
--! @brief Merge eight as_stream data streams.
--! @addtogroup asterics_modules
--! @{
--! @defgroup as_stream_merger_8_dynamic as_stream_merger_8_dynamic: Dynamic AsStream Channel Merger
--! This module merges up to 8 AsStream data signals into a single AsStream.
--! This module allows up to 8 AsStreams of differing data widths to be merged.
--! Set data width of unconnected streams to 0.
--! Strobe and sync signals are carried from stream 0 ONLY!
--! Stall is distributed forward to all input streams.
--! @}
----------------------------------------------------------------------------------

--! @addtogroup as_stream_merger_8_dynamic
--! @{


library ieee;
use ieee.std_logic_1164.all;


entity as_stream_merger_dynamic_8 is
    generic(
        DIN_WIDTH_0 : integer := 8;
        DIN_WIDTH_1 : integer := 8;
        DIN_WIDTH_2 : integer := 8;
        DIN_WIDTH_3 : integer := 8;
        DIN_WIDTH_4 : integer := 8;
        DIN_WIDTH_5 : integer := 8;
        DIN_WIDTH_6 : integer := 8;
        DIN_WIDTH_7 : integer := 8
    );
    port (
        -- Incoming AsStreams:
        -- AsStream "0"
        strobe_in_0    : in  std_logic;
        data_in_0      : in  std_logic_vector(DIN_WIDTH_0 - 1 downto 0);
        hsync_in_0     : in  std_logic;
        vsync_in_0     : in  std_logic;
        stall_in_0     : out std_logic;

        -- AsStream "1"
        strobe_in_1    : in  std_logic;
        data_in_1      : in  std_logic_vector(DIN_WIDTH_1 - 1 downto 0);
        hsync_in_1     : in  std_logic;
        vsync_in_1     : in  std_logic;
        stall_in_1     : out std_logic;
        
        -- AsStream "2"
        strobe_in_2    : in  std_logic;
        data_in_2      : in  std_logic_vector(DIN_WIDTH_2 - 1 downto 0);
        hsync_in_2     : in  std_logic;
        vsync_in_2     : in  std_logic;
        stall_in_2     : out std_logic;
        
        -- AsStream "3"
        strobe_in_3    : in  std_logic;
        data_in_3      : in  std_logic_vector(DIN_WIDTH_3 - 1 downto 0);
        hsync_in_3     : in  std_logic;
        vsync_in_3     : in  std_logic;
        stall_in_3     : out std_logic;
        
        -- AsStream "4"
        strobe_in_4    : in  std_logic;
        data_in_4      : in  std_logic_vector(DIN_WIDTH_4 - 1 downto 0);
        hsync_in_4     : in  std_logic;
        vsync_in_4     : in  std_logic;
        stall_in_4     : out std_logic;
        
        -- AsStream "5"
        strobe_in_5    : in  std_logic;
        data_in_5      : in  std_logic_vector(DIN_WIDTH_5 - 1 downto 0);
        hsync_in_5     : in  std_logic;
        vsync_in_5     : in  std_logic;
        stall_in_5     : out std_logic;
        
        -- AsStream "6"
        strobe_in_6    : in  std_logic;
        data_in_6      : in  std_logic_vector(DIN_WIDTH_6 - 1 downto 0);
        hsync_in_6     : in  std_logic;
        vsync_in_6     : in  std_logic;
        stall_in_6     : out std_logic;
        
        -- AsStream "7"
        strobe_in_7    : in  std_logic;
        data_in_7      : in  std_logic_vector(DIN_WIDTH_7 - 1 downto 0);
        hsync_in_7     : in  std_logic;
        vsync_in_7     : in  std_logic;
        stall_in_7     : out std_logic;

        -- Outgoing AsStream "out" ports:
        strobe_out : out std_logic;
        data_out   : out std_logic_vector((DIN_WIDTH_0 + DIN_WIDTH_1 + DIN_WIDTH_2 + DIN_WIDTH_3 + DIN_WIDTH_4 + DIN_WIDTH_5 + DIN_WIDTH_6 + DIN_WIDTH_7) - 1 downto 0);
        hsync_out   : out std_logic;
        vsync_out   : out std_logic;
        stall_out  : in  std_logic
    );
end as_stream_merger_dynamic_8;

--! @}

architecture RTL of as_stream_merger_dynamic_8 is
    constant c_width_0 : integer := DIN_WIDTH_0;
    constant c_width_1 : integer := c_width_0 + DIN_WIDTH_1;
    constant c_width_2 : integer := c_width_1 + DIN_WIDTH_2;
    constant c_width_3 : integer := c_width_2 + DIN_WIDTH_3;
    constant c_width_4 : integer := c_width_3 + DIN_WIDTH_4;
    constant c_width_5 : integer := c_width_4 + DIN_WIDTH_5;
    constant c_width_6 : integer := c_width_5 + DIN_WIDTH_6;
    constant c_width_7 : integer := c_width_6 + DIN_WIDTH_7;

begin

    data_out(c_width_0 - 1 downto 0) <= data_in_0;
    data_out(c_width_1 - 1 downto c_width_0) <= data_in_1;
    data_out(c_width_2 - 1 downto c_width_1) <= data_in_2;
    data_out(c_width_3 - 1 downto c_width_2) <= data_in_3;
    data_out(c_width_4 - 1 downto c_width_3) <= data_in_4;
    data_out(c_width_5 - 1 downto c_width_4) <= data_in_5;
    data_out(c_width_6 - 1 downto c_width_5) <= data_in_6;
    data_out(c_width_7 - 1 downto c_width_6) <= data_in_7;

    strobe_out <= strobe_in_0;
    hsync_out <= hsync_in_0;
    vsync_out <= vsync_in_0;
    stall_in_0 <= stall_out;
    stall_in_1 <= stall_out;
    stall_in_2 <= stall_out;
    stall_in_3 <= stall_out;
    stall_in_4 <= stall_out;
    stall_in_5 <= stall_out;
    stall_in_6 <= stall_out;
    stall_in_7 <= stall_out;
end RTL;
    
    