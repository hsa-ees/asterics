------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
------------------------------------------------------------------------
-- Entity:         as_generic_filter
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
--
-- Author:         Philip Manke
--
-- Modified:       2020-02-10
--
-- Description:    Generic filter module. Arbitrary filter size and weigths
------------------------------------------------------------------------
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
--! @file  as_generic_filter.vhd
--! @brief Generic filter module. Arbitrary filter size and weigths
--! @addtogroup asterics_helpers
--! @{
--! @defgroup as_generic_filter as_generic_filter: Convolution Filter
--! This entity implements a generic convolution filter with arbitrary weights.
--! @}
----------------------------------------------------------------------------------

--! @addtogroup as_generic_filter
--! @{


library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use ieee.numeric_std.all;
use ieee.math_real.all;

library asterics;
use asterics.helpers.all;
use asterics.as_generic_filter.all;

entity as_generic_filter_module is
    generic(
        DIN_WIDTH : integer := 8;
        FILTER_BIT_WIDTH : integer := 8;
        DOUT_WIDTH : integer := 8;
        WINDOW_X : integer := 3;
        WINDOW_Y : integer := 3;
        COMPUTATION_DATA_WIDTH_ADD : integer := 0;
        NORMALIZE_TO_HALF : boolean := false;
        OUTPUT_SIGNED : boolean := false
    );
    port(
        clk : in std_logic;
        reset : in std_logic;

        filter_values : in t_generic_window(0 to WINDOW_Y - 1, 0 to WINDOW_X - 1, FILTER_BIT_WIDTH - 1 downto 0); -- Interpreted as signed factors. Use powers of two for best (fastest) results!

        strobe   : in std_logic;
        window   : in t_generic_window(0 to WINDOW_Y - 1, 0 to WINDOW_X - 1, DIN_WIDTH - 1 downto 0);
        data_out : out std_logic_vector(DOUT_WIDTH - 1 downto 0)
    );
end entity as_generic_filter_module;

--! @}

architecture RTL of as_generic_filter_module is

    constant c_comp_bits_add : integer := COMPUTATION_DATA_WIDTH_ADD;
    -- Data width for computation:
    --   input width + filter weight (c_comp_bits_add) + delta to output if output wider
    constant c_comp_data_width : integer := DIN_WIDTH + c_comp_bits_add + f_relu(DOUT_WIDTH - DIN_WIDTH);
    -- # of bits to downscale:
    --   c_comp_bits_add + delta to output if input wider
    constant c_downscale_bits : integer := c_comp_bits_add + f_relu(DIN_WIDTH - DOUT_WIDTH);

    type t_sums is array(natural range<>) of signed(c_comp_data_width downto 0);

    signal applied_value_lines : t_sums(0 to WINDOW_Y - 1); -- signed values
    --signal debug_pix    : t_sums(0 to 8);
    --signal debug_filter : t_sums(0 to 8);
    --signal debug_res    : t_sums(0 to 8);
begin


    -- First pipeline stage
    apply_filter_values : process(clk) is
        variable factor : integer;
        variable f_sign : std_logic;
        variable pixel : unsigned(DIN_WIDTH - 1 downto 0);
        variable result_int : integer;
        variable result_vector : std_logic_vector(c_comp_data_width downto 0);
        variable line_acc : t_sums(0 to WINDOW_X - 1);
        variable acc : signed(c_comp_data_width downto 0);
    begin
        if rising_edge(clk) then
            if reset = '1' then
                applied_value_lines <= (others => (others => '0'));
            else
                if strobe = '1' then
                    for Y in 0 to WINDOW_Y - 1 loop
                        acc := (others => '0');
                        for X in 0 to WINDOW_X - 1 loop
                            -- Extract values
                            factor := to_integer(signed(f_get_vector_of_generic_window(filter_values, X, Y)));
                            pixel := unsigned(f_get_vector_of_generic_window(window, X, Y));
                            -- Multiply
                            result_int := to_integer(pixel) * factor;
                            
                            -- Debug:
                            --debug_pix(Y * 3 + X) <= to_signed(to_integer(pixel), c_comp_data_width + 1);
                            --debug_filter(Y * 3 + X) <= to_signed(factor, c_comp_data_width + 1);
                            --debug_res(Y * 3 + X) <= to_signed(result_int, c_comp_data_width + 1);

                            -- Store result
                            line_acc(X) := to_signed(result_int, c_comp_data_width + 1);
                        end loop;
                        -- Accumulate horizontally
                        for N in line_acc'range(1) loop
                            acc := acc + line_acc(N);
                        end loop;
                        -- Writeback
                        applied_value_lines(Y) <= acc;
                    end loop;
                end if;
            end if;
        end if;
    end process;

    -- Second pipeline stage
    sum_and_normalize : process(clk) is
        constant half_output : signed(c_comp_data_width downto 0) := (0 => '1', others => '0');
        variable acc : signed(c_comp_data_width downto 0);
        variable result : std_logic_vector(c_comp_data_width downto 0);
    begin
        if rising_edge(clk) then
            if reset = '1' then
                data_out <= (others => '0');
            else
                if strobe = '1' then
                    acc := (others => '0');
                    -- Sum up intermediate results 
                    for N in applied_value_lines'range(1) loop
                        acc := acc + applied_value_lines(N);
                    end loop;

                    -- Add MAX_VALUE / 2 (if configured)
                    if NORMALIZE_TO_HALF = true then
                        acc := acc + shift_left(half_output, c_comp_data_width - 2);
                    end if;
                    -- Downscale and convert to unsigned (if configured)
                    if OUTPUT_SIGNED then
                        result := std_logic_vector(shift_right(acc, c_downscale_bits + 1));
                    else
                        acc(c_comp_data_width) := '0';
                        result := std_logic_vector(shift_right(acc, c_downscale_bits));
                    end if;
                    -- Output (registered)
                    data_out <= result(data_out'range);
                end if;
            end if;
        end if;
    end process;

end architecture;
