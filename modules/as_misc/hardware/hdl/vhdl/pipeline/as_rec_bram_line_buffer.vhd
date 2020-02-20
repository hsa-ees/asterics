----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework.
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:        as_rec_bram_line_buffer
--
-- Company:       Efficient Embedded Systems Group
--                University of Applied Sciences, Augsburg, Germany
--
-- Author:        Philip Manke
--
-- Description:   Implements the line buffer for the 2d window pipeline.
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
--! @file  as_rec_bram_line_buffer.vhd
--! @brief Implements the line buffer for the 2d window pipeline.
----------------------------------------------------------------------------------


library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library asterics;
use asterics.helpers.all;
use asterics.as_generic_filter.all;
use asterics.as_fifo;
use asterics.as_shift_line;

--use work.helpers.all;
--use work.as_generic_filter.all;
--use work.as_fifo;
--use work.as_shift_line;


entity as_rec_bram_line_buffer is
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


architecture RTL of as_rec_bram_line_buffer is

    component as_rec_bram_line_buffer is
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
    end component;

    constant c_this_bram_depth : integer := 2**log2_floor(LINE_WIDTH);
    constant c_remaining_words : integer := LINE_WIDTH - c_this_bram_depth;

    constant c_bram_depth_is_pot : boolean := 2**log2_ceil(LINE_WIDTH) = LINE_WIDTH;

    signal fifo_full : std_logic;
    signal fifo_read : std_logic;
    signal bram_out : std_logic_vector(DATA_WIDTH - 1 downto 0);

begin

    fifo_read <= '1' when strobe = '1' and fifo_full = '1' else '0';
    
    -- If LINE_WIDTH (buffer size) is a power of 2:

    only_bram_fifo : if c_bram_depth_is_pot generate
        -- And is greater or equal to the minimum length required for BRAM
        bram_fifo : if LINE_WIDTH >= MINIMUM_LENGTH_FOR_BRAM generate
            -- Use only BRAM
            bram_fifo_line_buffer : entity as_fifo
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
        -- Buffer size if power of two but smaller than required
        -- for BRAM instantiation: Use shift registers!
        shift_fifo : if LINE_WIDTH < MINIMUM_LENGTH_FOR_BRAM generate
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
    end generate;
    
    -- If buffer size is not a power of two: Use two values for instantiation:
    -- c_this_bram_depth: part to instantiate as BRAM;
    -- c_remaining_words: rest of the desired buffer
    recursive_bram : if not c_bram_depth_is_pot generate
        -- If the BRAM part is larger than the minimum size for bram, generate BRAM
        bram_fifo : if c_this_bram_depth >= MINIMUM_LENGTH_FOR_BRAM generate
            bram_fifo_line_buffer : entity as_fifo
            generic map(
                DATA_WIDTH => DATA_WIDTH,
                FIFO_DEPTH => c_this_bram_depth
            )
            port map(
                clk => clk,
                reset => reset,

                data_in => data_in,
                data_out => bram_out,

                write_en => strobe,
                read_en => fifo_read,

                full => fifo_full,
                empty => open
            );
        end generate;
        -- Else, connect the BRAM input signals to the signals coming from BRAM
        no_bram_fifo : if  c_this_bram_depth < MINIMUM_LENGTH_FOR_BRAM generate
            fifo_full <= '1';
            bram_out <= data_in;
        end generate;

        -- If the remaining buffer size is large enough to have 
        -- another BRAM instantiated, instantiate this entity again
        remaining_data_bram : if c_remaining_words >= MINIMUM_LENGTH_FOR_BRAM generate
            this_again : as_rec_bram_line_buffer
            generic map(
                DATA_WIDTH => DATA_WIDTH,
                LINE_WIDTH => c_remaining_words,
                MINIMUM_LENGTH_FOR_BRAM => MINIMUM_LENGTH_FOR_BRAM
            )
            port map(
                clk => clk,
                reset => reset,
                strobe => fifo_read,
                data_in => bram_out,
                data_out => data_out
            );
        end generate;
        -- Else: Implement the remaining buffer as shift registers in FPGA logic
        remaining_data_fifo : if c_remaining_words < MINIMUM_LENGTH_FOR_BRAM and LINE_WIDTH > 2 generate
            shift_fifo : entity as_shift_line
            generic map(
                DATA_WIDTH => DATA_WIDTH,
                LINE_WIDTH => c_remaining_words
            )
            port map(
                clk => clk,
                reset => reset,
                strobe => fifo_read,
                data_in => bram_out,
                data_out => data_out
            );
        end generate;

        -- Exception: LINE_WIDTH = 1
        -- Math for c_this_bram_depth doesn't work out correctly!
        single_word_buffer : if LINE_WIDTH < 3 generate
            shift_fifo : entity as_shift_line
            generic map(
                DATA_WIDTH => DATA_WIDTH,
                LINE_WIDTH => LINE_WIDTH
            )
            port map(
                clk => clk,
                reset => reset,
                strobe => fifo_read,
                data_in => bram_out,
                data_out => data_out
            );
        end generate;
        
    end generate;
end architecture;