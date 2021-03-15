----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework.
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:        as_pipeline_row
--
-- Company:       Efficient Embedded Systems Group
--                University of Applied Sciences, Augsburg, Germany
--
-- Author:        Philip Manke
--
-- Description:   Implements a single pipeline row, including BRAM and Window.
--                If LINE_WIDTH - WINDOW_WIDTH <= 0, only the window will be generated as a fifo.
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
--! @file  as_pipeline_row.vhd
--! @brief Implements a single pipeline row, including BRAM and Window
--! @addtogroup asterics_helpers
--! @{
--! @defgroup as_pipeline_row as_pipeline_row: Image Row Buffer with Filter Window
--! This entity implements the image row buffer used in 2D Window Pipelines.
--! Provides a buffer output and a row of the image filter window.
--! Implements the buffer memory either as registers or using BRAM.
--! @}
----------------------------------------------------------------------------------

--! @addtogroup as_pipeline_row
--! @{


library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library asterics;
use asterics.helpers.all;
use asterics.as_generic_filter.all;
use asterics.as_line_buffer;

entity as_pipeline_row is
    generic (
        DATA_WIDTH : integer := 0;
        WINDOW_WIDTH : integer := 0;
        LINE_WIDTH : integer := 0;
        MINIMUM_LENGTH_FOR_BRAM : integer := 32
    );
    port (
        clk   : in  std_logic;
        reset : in  std_logic;

        strobe : in std_logic;
        buff_in : in std_logic_vector(DATA_WIDTH - 1 downto 0);
        line_out : out t_generic_line(0 to WINDOW_WIDTH - 1, DATA_WIDTH - 1 downto 0);
        data_out : out std_logic_vector(DATA_WIDTH - 1 downto 0)
    );
end entity;

--! @}

architecture RTL of as_pipeline_row Is

    constant c_bram_depth : integer := (LINE_WIDTH - WINDOW_WIDTH);

    signal ff_line : t_generic_line(0 to WINDOW_WIDTH - 1, DATA_WIDTH - 1 downto 0) := (others => (others => '0'));
    signal bram_in : std_logic_vector(DATA_WIDTH - 1 downto 0) := (others => '0');

begin

    bram_in <= f_get_vector_of_generic_line(ff_line, WINDOW_WIDTH - 1);
    line_out <= ff_line;

    -- BRAM buffer
    gen_fifo_bram : if c_bram_depth > 0 generate

        line_buffer : entity as_line_buffer
        generic map(
            DATA_WIDTH => DATA_WIDTH,
            LINE_WIDTH => c_bram_depth,
            MINIMUM_LENGTH_FOR_BRAM => MINIMUM_LENGTH_FOR_BRAM
        )
        port map(
            clk => clk,
            reset => reset,
            strobe => strobe,
            data_in => bram_in,
            data_out => data_out
        );
    end generate;

    -- As the smallest BRAM we can generate is 2 pixels long (see c_bram_depth)
    -- This coveres the case where we need a BRAM of size 1 (c_bram_depth == 0)
    gen_fifo_exception : if c_bram_depth = 0 generate
        p_single_strobe_delay : process(clk) is
        begin
            if rising_edge(clk) then
                if reset = '1' then
                    data_out <= (others => '0');
                else
                    if strobe = '1' then
                        data_out <= bram_in;
                    end if;
                end if;
            end if;
        end process;
    end generate;

    -- For single strobe delay buffers (Delay is handled by p_window_shift)
    gen_no_fifo : if c_bram_depth = -1 generate
        data_out <= bram_in;
    end generate;

    -- Update FIFO: Shift all values to next register
    --              Load new input value to register 0
    p_window_shift : process(clk) is
        variable shift_temp : std_logic_vector(DATA_WIDTH - 1 downto 0);
    begin
        if rising_edge(clk) then
            if reset = '1' then
                -- DEBUG:                
                -- report "c_bram_depth: " & integer'image(c_bram_depth);
                -- report "window width: " & integer'image(ff_line'length(1));
                shift_temp := (others => '0');
                for N in WINDOW_WIDTH - 1 downto 0 loop
                    f_set_vector_of_generic_line(ff_line, N, shift_temp);
                end loop;
            else
                if strobe = '1' then
                --report "c_bram_depth: " & integer'image(c_bram_depth);
                    for N in WINDOW_WIDTH - 1 downto 1 loop
                        shift_temp := f_get_vector_of_generic_line(ff_line, N - 1);
                        f_set_vector_of_generic_line(ff_line, N, shift_temp);
                    end loop;
                    f_set_vector_of_generic_line(ff_line, 0, buff_in);
                end if;
            end if;
        end if;
    end process;

end architecture;
