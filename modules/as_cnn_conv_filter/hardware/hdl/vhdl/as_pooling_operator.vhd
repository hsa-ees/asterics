----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_pooling_operator
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Philip Manke
--
-- Modified:       
--
-- Description:    This module implements a pooling filter operation
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
--! @file  as_cnn_pooling_operator.vhd
--! @brief This module implements a generic convolutional filter for CNNs.
----------------------------------------------------------------------------------

--! @addtogroup as_cnn_pooling_filter_internal
--! @{


library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library asterics;
use asterics.helpers.all;
use asterics.as_generic_filter.all;

entity as_cnn_pooling_operator is
    generic(
        DATA_WIDTH : integer := 8;
        POOLING_METHOD : string := "max"
    );
    port (
        clk         : in  std_logic;
        reset       : in  std_logic;

        -- AsWindow ports
        strobe_in     : in  std_logic;
        window_in     : in  t_generic_window(0 to 1, 0 to 1, DATA_WIDTH - 1 downto 0);
        data_out       : out std_logic_vector(DATA_WIDTH - 1 downto 0)
    );
end as_cnn_pooling_operator;

--! @}

architecture RTL of as_cnn_pooling_operator is
begin
    -- Max pooling method
    gen_max_pooling : if POOLING_METHOD = "max" generate
        p_max_pooling : process(clk)
            variable max_val : std_logic_vector(DATA_WIDTH - 1 downto 0);
            variable larger_y0, larger_y1 : integer;
            variable comp_0, comp_1 : std_logic_vector(DATA_WIDTH - 1 downto 0);
        begin
            if rising_edge(clk) then
                if reset = '1' then
                    data_out <= (others => '0');
                else
                    larger_y0 := 0;
                    larger_y1 := 0;
                    -- Compare (0, 0) and (0, 1)
                    if (to_integer(signed(f_get_vector_of_generic_window(window_in, 0, 0))) 
                        < to_integer(signed(f_get_vector_of_generic_window(window_in, 1, 0)))) then
                        larger_y0 := 1;
                    end if;
                    -- Compare (0, 1) and (1, 1)
                    if (to_integer(signed(f_get_vector_of_generic_window(window_in, 0, 1))) 
                        < to_integer(signed(f_get_vector_of_generic_window(window_in, 1, 1)))) then
                        larger_y1 := 1;
                    end if;
                    -- Compare the larger values of both previous comparisons
                    if (to_integer(signed(f_get_vector_of_generic_window(window_in, larger_y0, 0))) 
                        < to_integer(signed(f_get_vector_of_generic_window(window_in, larger_y1, 1)))) then
                        max_val := f_get_vector_of_generic_window(window_in, larger_y1, 1);
                    else
                        max_val := f_get_vector_of_generic_window(window_in, larger_y0, 0);
                    end if;
                    
                    data_out <= max_val;
                end if;
            end if;
        end process p_max_pooling;
    end generate gen_max_pooling;

    gen_non_pooling : if POOLING_METHOD = "none" generate
        p_non_pooling : process(clk) is
        begin
            if rising_edge(clk) then
                if reset = '1' then
                    data_out <= (others => '0');
                else
                    data_out <= f_get_vector_of_generic_window(window_in, 0, 0);
                end if;
            end if;
        end process p_non_pooling;
    end generate gen_non_pooling;
end RTL;
    