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
-- Description:   Implements a single pipeline row, including BRAM and Window
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
----------------------------------------------------------------------------------


library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library asterics;
use asterics.helpers.all;
use asterics.as_generic_filter.all;
use asterics.as_rec_bram_line_buffer;


--use work.helpers.all;
--use work.as_generic_filter.all;
--use work.as_rec_bram_line_buffer;


entity as_pipeline_row is
    generic (
        DATA_WIDTH : integer := 8;
        WINDOW_WIDTH : integer := 5;
        LINE_WIDTH : integer := 640;
        MINIMUM_LENGTH_FOR_BRAM : integer := 32
    );
    port (
        clk   : in  std_logic;
        reset : in  std_logic;

        strobe : in std_logic;
        data_in : in std_logic_vector(DATA_WIDTH - 1 downto 0);
        line_out : out t_generic_line(0 to WINDOW_WIDTH - 1, DATA_WIDTH - 1 downto 0);
        data_out : out std_logic_vector(DATA_WIDTH - 1 downto 0)
    );
end entity;


architecture RTL of as_pipeline_row is
    -- Here's why we add the (- 2):
    -- There are two extra register stages somewhere in the pipeline
    -- maybe between the window and BRAM, at the output of BRAM, or elsewhere.
    -- So, to generate the right amount of buffer stages, we shrink the BRAM.
    constant c_bram_depth : integer := LINE_WIDTH - WINDOW_WIDTH - 2;

    signal ff_line : t_generic_line(0 to WINDOW_WIDTH - 1, DATA_WIDTH - 1 downto 0);
    signal bram_in : std_logic_vector(DATA_WIDTH - 1 downto 0);

begin

    bram_in <= f_get_vector_of_generic_line(ff_line, WINDOW_WIDTH - 1);
    line_out <= ff_line;

    fifo_bram : if c_bram_depth > 0 generate
        line_buffer : entity as_rec_bram_line_buffer
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

    p_window_shift : process(clk) is
        variable shift_temp : std_logic_vector(DATA_WIDTH - 1 downto 0);
    begin
        if rising_edge(clk) then
            if reset = '1' then
                shift_temp := (others => '0');
                for N in WINDOW_WIDTH - 1 downto 0 loop
                    f_set_vector_of_generic_line(ff_line, N, shift_temp);
                end loop;
            else
                if strobe = '1' then
                    for N in WINDOW_WIDTH - 1 downto 1 loop
                        shift_temp := f_get_vector_of_generic_line(ff_line, N - 1);
                        f_set_vector_of_generic_line(ff_line, N, shift_temp);
                    end loop;
                    f_set_vector_of_generic_line(ff_line, 0, data_in);
                end if;
            end if;
        end if;
    end process;



end architecture;