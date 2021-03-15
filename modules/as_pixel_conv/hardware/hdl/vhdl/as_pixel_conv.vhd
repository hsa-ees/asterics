----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_pixel_conv
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Philip Manke
--
-- Modified:       
--
-- Description:    Perform linear modifications of streaming pixel data.
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
--! @file  as_pixel_conv.vhd
--! @brief Perform linear modifications of streaming pixel data.
--! @addtogroup asterics_modules
--! @{
--! @defgroup as_pixel_conv as_pixel_conv: AsStream Data Expansion
--! Repeat input AsStream data over the entire output data width.
--! Useful for data expansion (eg. grayscale to RGB)
--! @}
----------------------------------------------------------------------------------

--! @addtogroup as_pixel_conv
--! @{


library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity as_pixel_conv is
    generic (
        DATA_WIDTH_IN : integer := 8;
        DATA_WIDTH_OUT : integer := 8
    );
    port (
        clk         : in  std_logic;
        reset       : in  std_logic;
        ready       : out std_logic;

        -- AsStream in ports
        vsync_in      : in  std_logic;
        vcomplete_in  : in  std_logic;
        hsync_in      : in  std_logic;
        hcomplete_in  : in  std_logic;
        strobe_in     : in  std_logic;
        data_in       : in  std_logic_vector(DATA_WIDTH_IN - 1 downto 0);
        data_error_in : in  std_logic;
        sync_error_in : in  std_logic;
        stall_out     : out std_logic;

        -- AsStream out ports
        vsync_out      : out std_logic;
        vcomplete_out  : out std_logic;
        hsync_out      : out std_logic;
        hcomplete_out  : out std_logic;
        strobe_out     : out std_logic;
        data_out       : out std_logic_vector(DATA_WIDTH_OUT - 1 downto 0);
        data_error_out : out std_logic;
        sync_error_out : out std_logic;
        stall_in       : in  std_logic
    );
end as_pixel_conv;

--! @}

architecture RTL of as_pixel_conv is

    constant c_fact : integer := DATA_WIDTH_OUT / DATA_WIDTH_IN;

begin

    ready <= not reset;

    vsync_out  <= vsync_in;
    vcomplete_out <= vcomplete_in;
    hsync_out  <= hsync_in;
    hcomplete_out <= hcomplete_in;
    strobe_out <= strobe_in;
    sync_error_out <= sync_error_in;
    data_error_out <= data_error_in;
    stall_out <= stall_in;
    
    data_output : process
    begin
        output_expansion : for N in 0 to c_fact - 1 loop
            data_out(N * DATA_WIDTH_IN + DATA_WIDTH_IN - 1 downto N * DATA_WIDTH_IN) <= data_in;
        end loop;
    end process;

end RTL;
