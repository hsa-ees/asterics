----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework.
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:        as_line_buffer
--
-- Company:       Efficient Embedded Systems Group
--                University of Applied Sciences, Augsburg, Germany
--
-- Author:        Philip Manke
--
-- Description:   Implements the line/row buffer for 2D Window Pipelines.
--
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
--! @file  as_line_buffer.vhd
--! @brief Implements the line/row buffer for 2D Window Pipelines.
--! @addtogroup asterics_helpers
--! @{
--! @defgroup as_line_buffer as_line_buffer: Image Row Buffer
--! This module implements the internal image row buffer used in 2D Window Pipelines.
--! @}
----------------------------------------------------------------------------------

--! @addtogroup as_line_buffer
--! @{


library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library asterics;
use asterics.helpers.all;
use asterics.as_fifo;
use asterics.as_shift_line;


entity as_line_buffer is
    generic (
        DATA_WIDTH : integer := 8;
        LINE_WIDTH : integer := 480;
        MINIMUM_LENGTH_FOR_BRAM : integer := 32
    );
    port (
        clk   : in  std_logic;
        reset : in  std_logic;

        strobe : in std_logic;
        data_in : in std_logic_vector(DATA_WIDTH - 1 downto 0);
        data_out : out std_logic_vector(DATA_WIDTH - 1 downto 0)
    );
end entity;

--! @}

architecture RTL of as_line_buffer is

    signal fifo_full : std_logic;
    signal fifo_read : std_logic;

begin

    -- If line is greater or equal to the minimum length required for BRAM
    gen_bram_fifo : if LINE_WIDTH >= MINIMUM_LENGTH_FOR_BRAM generate
        
        fifo_read <= '1' when strobe = '1' and fifo_full = '1' else '0';
        -- Use only BRAM
        bram_fifo : entity as_fifo
        generic map(
            DATA_WIDTH => DATA_WIDTH,
            FIFO_DEPTH => LINE_WIDTH
        )
        port map(
            clk => clk,
            reset => reset,

            data_in => data_in,
            data_out => data_out,

            write_en => strobe,
            read_en => fifo_read,

            full => fifo_full,
            empty => open
        );
    end generate;
    
    -- Line is smaller than required for BRAM instantiation: Use shift registers!
    gen_shift_fifo : if LINE_WIDTH < MINIMUM_LENGTH_FOR_BRAM generate
        shift_fifo : entity as_shift_line
        generic map(
            DATA_WIDTH => DATA_WIDTH,
            LINE_WIDTH => LINE_WIDTH
        )
        port map(
            clk => clk,
            reset => reset,
            strobe => strobe,
            data_in => data_in,
            data_out => data_out
        );
    end generate;
    
end architecture;
