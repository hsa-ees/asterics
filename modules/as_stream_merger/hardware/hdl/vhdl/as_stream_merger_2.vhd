----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_stream_merger_2
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Philip Manke
--
-- Modified:       
--
-- Description:    This module merges two as_stream data streams.
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
--! @file  as_stream_merger_2.vhd
--! @brief Merge two as_stream data streams.
--! @addtogroup asterics_modules
--! @{
--! @defgroup as_stream_merger_2 as_stream_merger_2: AsStream Channel Merger
--! This module merges 2 AsStream data signals into a single AsStream.
--! Strobe and sync signals are carried from stream 0 ONLY!
--! Stall is distributed forward to all input streams.
--! @}
----------------------------------------------------------------------------------

--! @addtogroup as_stream_merger_2
--! @{


library ieee;
use ieee.std_logic_1164.all;


entity as_stream_merger_2 is
    generic(
        DIN_WIDTH : integer := 8
    );
    port (
        -- AsStream in ports
        strobe_in_0    : in  std_logic;
        data_in_0      : in  std_logic_vector(DIN_WIDTH - 1 downto 0);
        hsync_in_0     : in  std_logic;
        vsync_in_0     : in  std_logic;
        stall_in_0     : out std_logic;
        strobe_in_1    : in  std_logic;
        data_in_1      : in  std_logic_vector(DIN_WIDTH - 1 downto 0);
        hsync_in_1     : in  std_logic;
        vsync_in_1     : in  std_logic;
        stall_in_1     : out std_logic;

        -- AsStream out ports:
        strobe_out : out std_logic;
        data_out   : out std_logic_vector((DIN_WIDTH * 2) - 1 downto 0);
        hsync_out   : out std_logic;
        vsync_out   : out std_logic;
        stall_out  : in  std_logic
    );
end as_stream_merger_2;

--! @}

architecture RTL of as_stream_merger_2 is
    type t_data_array is array(0 to 1) of std_logic_vector(DIN_WIDTH - 1 downto 0);
    signal data_in_array : t_data_array;
begin
    data_in_array(0) <= data_in_0;
    data_in_array(1) <= data_in_1;

    gen_merger : for N in 0 to 1 generate
        data_out(DIN_WIDTH - 1 + N * DIN_WIDTH downto N * DIN_WIDTH) <= data_in_array(N);
    end generate;

    strobe_out <= strobe_in_0;
    hsync_out <= hsync_in_0;
    vsync_out <= vsync_in_0;
    stall_in_0 <= stall_out;
    stall_in_1 <= stall_out;
end RTL;
    