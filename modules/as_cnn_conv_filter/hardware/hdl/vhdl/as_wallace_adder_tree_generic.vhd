----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_wallace_adder_tree_generic
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Philip Manke
--
-- Modified:       
--
-- Description:    This module implements a carry save adder tree
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
--! @file  as_wallace_adder_tree_generic.vhd
--! @brief Carry save adder tree.
----------------------------------------------------------------------------------


--! @addtogroup as_cnn_serial_convolution_filter_internal
--! @{

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

library asterics;
use asterics.helpers.all;
use asterics.as_generic_filter.all;
use asterics.as_cnn_helpers.all;
use asterics.as_carry_safe_adder;

entity as_wallace_adder_tree_generic is
    generic(
        DOUT_WIDTH : integer := 8;
        LARGEST_BIT_WIDTH : integer := 16;
        BIT_WIDTHS : t_integer_array;
        ELEMENT_COUNT : integer
    );
    port (
        clk         : in  std_logic;
        reset       : in  std_logic;
        strobe_in   : in  std_logic;

        data_in        : in std_logic_vector(ELEMENT_COUNT * LARGEST_BIT_WIDTH - 1 downto 0);
        data_out       : out std_logic_vector(DOUT_WIDTH - 1 downto 0)
    );
end as_wallace_adder_tree_generic;

--! @}

architecture RTL of as_wallace_adder_tree_generic is
    constant c_adder_stage_count : integer := f_get_carry_safe_adder_tree_stage_count(ELEMENT_COUNT);
    constant c_input_bit_width_mapping : t_bit_width_mapping(0 to c_adder_stage_count, 0 to ELEMENT_COUNT - 1) := f_generate_csa_tree_input_bit_widths(BIT_WIDTHS, c_adder_stage_count);
    type t_data_mapping is array(0 to c_adder_stage_count - 1) of t_integer_array(0 to ELEMENT_COUNT - 1);
    
    signal data_mapping : t_data_mapping := (others => (others => 0));
    signal sum : std_logic_vector(c_input_bit_width_mapping(c_adder_stage_count, 0) downto 0);
begin

    gen_input_mapping_conditional : if c_adder_stage_count > 0 generate
        gen_input_mapping : for N in 0 to ELEMENT_COUNT - 1 generate
        begin
            data_mapping(0)(N) <= to_integer(signed(data_in((N + 1) * LARGEST_BIT_WIDTH - 1 downto N * LARGEST_BIT_WIDTH)));
        end generate;
    end generate gen_input_mapping_conditional;

    gen_ripple_adder_conditional : if c_adder_stage_count = 0 generate
        p_ripple_adder : process(data_in) is
            variable temp_sum : signed(sum'range);
        begin
            temp_sum := (others => '0');
            for N in 0 to ELEMENT_COUNT - 1 loop
                temp_sum := to_signed(to_integer(temp_sum) + to_integer(signed(data_in((N + 1) * LARGEST_BIT_WIDTH - 1 downto N * LARGEST_BIT_WIDTH))), sum'length);
            end loop;
            sum <= std_logic_vector(temp_sum);
        end process;
    end generate gen_ripple_adder_conditional;

    gen_stages : for S in 1 to c_adder_stage_count generate
        constant c_adder_count_S : integer := f_get_carry_safe_adder_tree_adder_count(ELEMENT_COUNT, S);
        constant c_element_count_S : integer := f_get_carry_safe_adder_tree_element_count(ELEMENT_COUNT, S);

    begin

        gen_carry_safe_adders : if S /= c_adder_stage_count generate
            gen_adders : for A in 0 to c_adder_count_S - 1 generate
                constant c_in_index_SA : integer := A * 3;
                constant c_out_index_SA : integer := A * 2;
                constant c_input_data_widths_SA : t_integer_array(0 to 2) := (
                    0 => c_input_bit_width_mapping(S - 1, c_in_index_SA + 0),
                    1 => c_input_bit_width_mapping(S - 1, c_in_index_SA + 1),
                    2 => c_input_bit_width_mapping(S - 1, c_in_index_SA + 2)
                );
                constant c_data_in_width_SA : integer := f_get_largest_integer(c_input_data_widths_SA, 0, 2);
                signal a_raw  : std_logic_vector(c_input_data_widths_SA(0) - 1 downto 0) := (others => '0');
                signal b_raw  : std_logic_vector(c_input_data_widths_SA(1) - 1 downto 0) := (others => '0');
                signal c_raw  : std_logic_vector(c_input_data_widths_SA(2) - 1 downto 0) := (others => '0');
                
                signal a_in   : std_logic_vector(c_data_in_width_SA - 1 downto 0) := (others => '0');
                signal b_in   : std_logic_vector(c_data_in_width_SA - 1 downto 0) := (others => '0');
                signal c_in   : std_logic_vector(c_data_in_width_SA - 1 downto 0) := (others => '0');
                signal s_out  : std_logic_vector(c_data_in_width_SA - 1 downto 0) := (others => '0');
                signal cs_out : std_logic_vector(c_data_in_width_SA     downto 0) := (others => '0');
                
            begin

                a_raw <= std_logic_vector(to_signed(data_mapping(S - 1)(c_in_index_SA + 0), c_input_data_widths_SA(0)));
                b_raw <= std_logic_vector(to_signed(data_mapping(S - 1)(c_in_index_SA + 1), c_input_data_widths_SA(1)));
                c_raw <= std_logic_vector(to_signed(data_mapping(S - 1)(c_in_index_SA + 2), c_input_data_widths_SA(2)));

                a_in(c_input_data_widths_SA(0) - 1 downto 0) <= a_raw;
                a_in(c_data_in_width_SA - 1 downto c_input_data_widths_SA(0)) <= (others => a_raw(c_input_data_widths_SA(0) - 1));
                b_in(c_input_data_widths_SA(1) - 1 downto 0) <= b_raw;
                b_in(c_data_in_width_SA - 1 downto c_input_data_widths_SA(1)) <= (others => b_raw(c_input_data_widths_SA(1) - 1));
                c_in(c_input_data_widths_SA(2) - 1 downto 0) <= c_raw;
                c_in(c_data_in_width_SA - 1 downto c_input_data_widths_SA(2)) <= (others => c_raw(c_input_data_widths_SA(2) - 1));

                carry_safe_adder_SN : entity as_carry_safe_adder
                generic map(
                    DATA_WIDTH => c_data_in_width_SA
                )
                port map(
                    a => a_in,
                    b => b_in,
                    c => c_in,
                    s => s_out,
                    cs => cs_out
                );

                data_mapping(S)(c_out_index_SA + 0) <= to_integer(signed(s_out));
                data_mapping(S)(c_out_index_SA + 1) <= to_integer(signed(cs_out));

            end generate gen_adders;

            -- Elements not processed/added this stage are propagated to next stage
            gen_leftover_propagate : for N in 0 to c_element_count_S - (c_adder_count_S * 3) - 1 generate

                data_mapping(S)(2 * c_adder_count_S + N) <= data_mapping(S - 1)(3 * c_adder_count_S + N);

            end generate gen_leftover_propagate;
        end generate gen_carry_safe_adders;

        gen_ripple_adder : if S = c_adder_stage_count generate

            constant c_data_in_width_S : integer := c_input_bit_width_mapping(S, 0);
            signal a : signed(c_data_in_width_S - 1 downto 0) := (others => '0');
            signal b : signed(c_data_in_width_S - 1 downto 0) := (others => '0');
            signal sum_int : signed(c_data_in_width_S downto 0);

        begin

            a <= to_signed(data_mapping(S - 1)(0), c_data_in_width_S);
            b <= to_signed(data_mapping(S - 1)(1), c_data_in_width_S);
            sum_int <= to_signed(to_integer(a) + to_integer(b), c_data_in_width_S + 1);-- (a(c_data_in_width_S - 1) & a) + (b(c_data_in_width_S - 1) & b);
            sum <= std_logic_vector(sum_int);
        
        end generate gen_ripple_adder;
    end generate gen_stages;

    -- Output register stage
    p_output : process(clk)
    begin
        if rising_edge(clk) then
            if strobe_in = '1' then
                data_out <= sum(DOUT_WIDTH - 1 downto 0);
            end if;
        end if;
    end process;

end RTL;
    