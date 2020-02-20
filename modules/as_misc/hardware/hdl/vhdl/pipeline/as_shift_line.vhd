----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework.
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:        as_shift_line
--
-- Company:       Efficient Embedded Systems Group
--                University of Applied Sciences, Augsburg, Germany
--
-- Author:        Philip Manke
--
-- Description:   Implements a shifting word array
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
--! @file  as_shift_line.vhd
--! @brief Implements a shifting word array
----------------------------------------------------------------------------------


library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library asterics;
use asterics.as_generic_filter.all;
use asterics.helpers.all;

--use work.as_generic_filter.all;


entity as_shift_line is
    generic (
        DATA_WIDTH : integer := 8;
        LINE_WIDTH : integer := 31
    );
    port (
        clk   : in  std_logic;
        reset : in  std_logic;

        strobe : in std_logic;
        data_in : in std_logic_vector(DATA_WIDTH - 1 downto 0);
        data_out : out std_logic_vector(DATA_WIDTH - 1 downto 0)
    );
end entity;


architecture RTL of as_shift_line is


    signal ff_line : t_generic_line(0 to LINE_WIDTH - 1, DATA_WIDTH - 1 downto 0);

begin

    p_window_shift : process(clk) is
        variable shift_temp : std_logic_vector(DATA_WIDTH - 1 downto 0);
    begin
        if rising_edge(clk) then
            if reset = '1' then
                shift_temp := (others => '0');
                for N in LINE_WIDTH - 1 downto 0 loop
                    f_set_vector_of_generic_line(ff_line, N, shift_temp);
                end loop;
            else
                if strobe = '1' then
                    for N in LINE_WIDTH - 1 downto 1 loop
                        shift_temp := f_get_vector_of_generic_line(ff_line, N - 1);
                        f_set_vector_of_generic_line(ff_line, N, shift_temp);
                    end loop;
                    f_set_vector_of_generic_line(ff_line, 0, data_in);
                end if;
            end if;
        end if;
    end process;

    data_out <= f_get_vector_of_generic_line(ff_line, LINE_WIDTH - 1);

end architecture;