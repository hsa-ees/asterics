----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework.
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:        window_buff_nxm
--
-- Company:       Efficient Embedded Systems Group
--                University of Applied Sciences, Augsburg, Germany
--
-- Author:        Philip Manke
--
-- Description:   Implements a N by M window buffer.
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
--! @file  window_buff_nxm.vhd
--! @brief Implements a N by M window buffer.
--! @addtogroup asterics_helpers
--! @{
--! @defgroup window_buff_nxm window_buff_nxm: Standalone Window Buffer
--! Standalone 2D Window Pipeline - style window buffer.
--! Implements a N by M window buffer.
--! Meant mainly for testing purposes, such as testbenches.
--! @}
----------------------------------------------------------------------------------

--! @addtogroup window_buff_nxm
--! @{


library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library asterics;
use asterics.helpers.all;
use asterics.as_generic_filter.all;
use asterics.as_pipeline_row;

--use work.helpers.all;
--use work.as_generic_filter.all;
--use work.as_pipeline_row;


entity as_window_buff_nxm is
    generic (
        DATA_WIDTH : integer := 32;
        LINE_WIDTH : integer := 1080;
        WINDOW_X : integer := 17;
        WINDOW_Y : integer := 17;
        MINIMUM_LENGTH_FOR_BRAM : integer := 64
    );
    port (
        clk   : in  std_logic;
        reset : in  std_logic;

        strobe : in std_logic;
        data_in : in std_logic_vector(DATA_WIDTH - 1 downto 0);
        window_out : out t_generic_window(0 to WINDOW_Y - 1, 0 to WINDOW_X - 1, DATA_WIDTH - 1 downto 0);
        data_out : out std_logic_vector(DATA_WIDTH - 1 downto 0)
    );
end entity;

--! @}

architecture RTL of as_window_buff_nxm is
    type word_array is array(0 to WINDOW_Y - 1) 
            of std_logic_vector(DATA_WIDTH - 1 downto 0);
    type t_generic_line_array is array(natural range<>) 
            of t_generic_line(0 to WINDOW_X -  1, DATA_WIDTH - 1 downto 0);
    
    -- Array for window area (lines) 
    signal window_line_array : t_generic_line_array(0 to WINDOW_Y - 1) := (others => (others => (others => '0')));
    -- Array for connecting the window line buffer in and outputs
    signal buffer_in_array : word_array := (others => (others => '0'));

begin

    buffer_in_array(0) <= data_in;
    data_out <= f_get_vector_of_generic_line(window_line_array(WINDOW_Y - 1), WINDOW_X - 1);

    -- Map the window line array from the pipeline line buffers to the output window
    window_output : process(window_line_array) is
    begin
        for Y in window_out'range(1) loop
            for X in window_out'range(2) loop
                for N in window_out'range(3) loop
                    window_out(X, Y, N) <= window_line_array(Y)(X, N);
                end loop;
            end loop;
        end loop;
    end process;

    -- Line buffers: 
    buffer_lines_generator : if WINDOW_Y > 1 generate
        buffer_lines_generator_loop : for N in 0 to WINDOW_Y - 2 generate
            buffer_line_N : entity as_pipeline_row
            generic map(
                DATA_WIDTH => DATA_WIDTH,
                WINDOW_WIDTH => WINDOW_X,
                -- Plus 1 as pipeline row expects a register between data_out and buff_in!
                LINE_WIDTH => LINE_WIDTH + 1,
                MINIMUM_LENGTH_FOR_BRAM => MINIMUM_LENGTH_FOR_BRAM
            )
            port map(
                clk => clk,
                reset => reset,
                strobe => strobe,
                buff_in => buffer_in_array(N),
                line_out => window_line_array(N),
                data_out => buffer_in_array(N + 1)
            );
        end generate;
    end generate;
    
    -- Last line of window, implemented as flipflops
    shift_last_line : process(clk) is
        variable temp_shift : std_logic_vector(DATA_WIDTH - 1 downto 0);
    begin
        if rising_edge(clk) then
            if reset = '1' then
                temp_shift := (others => '0');
                for N in 0 to WINDOW_X - 1 loop
                    f_set_vector_of_generic_line(window_line_array(WINDOW_Y - 1), N, temp_shift);
                end loop;
            else
                if strobe = '1' then
                    f_set_vector_of_generic_line(window_line_array(WINDOW_Y - 1), 0, buffer_in_array(WINDOW_Y - 1));
                    for N in 1 to WINDOW_X - 1 loop
                        temp_shift := f_get_vector_of_generic_line(window_line_array(WINDOW_Y - 1), N - 1);
                        f_set_vector_of_generic_line(window_line_array(WINDOW_Y - 1), N, temp_shift);
                    end loop;
                end if;
            end if;
        end if;
    end process;

end architecture;
