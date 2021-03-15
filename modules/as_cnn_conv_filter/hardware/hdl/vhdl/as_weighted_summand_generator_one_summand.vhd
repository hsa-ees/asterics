----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_weighted_summand_generator_one_summand
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Philip Manke
--
-- Modified:       
--
-- Description:    This component provides an integer array of all summands generated
--                 using the KERNEL_VALUES of a single kernel and the current window_in.
--                 Requires the total number of summands and their bit widths via generics.
--                 The summand output is sorted in order of 
--                 channel, height, width, weight factors (small -> large) from slowest to fastest changing
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
--! @file  as_weighted_summand_generator_one_summand.vhd
--! @brief Provides summands for a convolution without using multipliers
--! This variant provides the sums of all partial factors from a single weight value
----------------------------------------------------------------------------------

--! @addtogroup as_cnn_serial_convolution_filter_internal
--! @{


library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library asterics;
use asterics.helpers.all;
use asterics.as_generic_filter.all;
use asterics.as_cnn_helpers.all;

entity as_weighted_summand_generator_one_summand is
    generic(
        -- Input pixel bit width
        DIN_WIDTH : integer := 8;
        -- Number of input channels
        CHANNEL_COUNT : integer := 1;
        -- Side length of the square kernel
        KERNEL_SIZE : integer := 3;
        -- Kernel values in data format: image channel, height, width
        KERNEL_VALUES : t_generic_filter; 
        -- Total number of summands expected
        SUMMAND_COUNT : integer := 148;
        -- Bit width of summands in order: image channel, height, width, weight factors (small -> large)
        SUMMAND_BIT_WIDTHS : t_integer_array;
        LARGEST_SUMMAND_BIT_WIDTH : integer
    );
    port (
        -- Current image window to convolve
        window_in     : in  t_generic_window(0 to KERNEL_SIZE - 1, 0 to KERNEL_SIZE - 1, (DIN_WIDTH * CHANNEL_COUNT) - 1 downto 0);
        -- Summands from convolution with the CURRENT image window (no clock delay!)
        data_out       : out std_logic_vector(SUMMAND_COUNT * LARGEST_SUMMAND_BIT_WIDTH - 1 downto 0)
    );
end as_weighted_summand_generator_one_summand;

--! @}

architecture RTL of as_weighted_summand_generator_one_summand is
    -- Number of total summands including sub factors of the weights
    constant c_internal_summand_count : integer := f_get_total_elements_for_weights(KERNEL_VALUES);
    constant c_summand_bit_widths : t_integer_array(0 to c_internal_summand_count - 1)
        := f_get_result_bit_widths_for_all_weights(KERNEL_VALUES, DIN_WIDTH, c_internal_summand_count);

    constant c_weights_per_channel : integer := KERNEL_SIZE * KERNEL_SIZE;
    constant c_total_weights_in_kernel : integer := c_weights_per_channel * CHANNEL_COUNT;
    -- Array of weight factors (powers of two) per weight of the convolution kernel
    constant c_elements_per_weight : t_integer_array(0 to c_total_weights_in_kernel - 1) 
        := f_get_element_count_for_weights(KERNEL_VALUES);
    -- Output array. We use an integer array, as we each value has a potentially different bit width
    -- We leave it to the synthesis tool to optimize the implemented bit width per value.
    -- We support the tool by using bit width constrained types before assigning to and after reading from the array.
    --signal unsorted_elements : t_generic_line(0 to SUMMAND_COUNT - 1, LARGEST_SUMMAND_BIT_WIDTH - 1 downto 0);
    type t_signed_array is array(0 to SUMMAND_COUNT - 1) of signed(LARGEST_SUMMAND_BIT_WIDTH - 1 downto 0);
    signal unsorted_elements : t_signed_array;
begin

    -- For all channels
    gen_produce_summands : for N in 0 to CHANNEL_COUNT - 1 generate
        -- Input window (single channel)
        signal crt_window_N : t_generic_window(0 to KERNEL_SIZE - 1,
                                               0 to KERNEL_SIZE - 1,
                                               DIN_WIDTH - 1 downto 0) := (others => (others => (others => '0')));

    begin
        -- Cut the input window along the channel dimension (extract a single channel)
        crt_window_N <= f_cut_vectors_of_generic_window(window_in, N * DIN_WIDTH, DIN_WIDTH);
        
        -- For each row of pixels in each channel
        gen_produce_summands_N : for Y in 0 to KERNEL_SIZE - 1 generate
        
            -- For each pixel in each row
            gen_produce_summands_NY : for X in 0 to KERNEL_SIZE - 1 generate
                
                -- Number of the current weight (if they were in a 1D array)
                constant c_current_index_NYX : integer := (N * (c_weights_per_channel)) + (Y * KERNEL_SIZE) + X;
                -- Integer value of the current weight
                constant c_weight_value_NYX : integer := KERNEL_VALUES(N, (Y * KERNEL_SIZE) + X);
                -- Number of summands generated from this weight (number of unique power of two factors that it can be split into)
                constant c_result_element_count_NYX : integer := c_elements_per_weight(c_current_index_NYX);
                -- Array of unique powers of two this weight is expressed as 
                constant c_weight_shift_factors_NYX : t_integer_array(0 to c_result_element_count_NYX - 1) 
                    := f_get_weight_shift_factors(c_weight_value_NYX);
                -- Start index of the first summand generated from this weight in the output array
                constant c_result_element_index_NYX : integer 
                    := f_get_int_array_part_sum(c_elements_per_weight, 0, c_current_index_NYX - 1);
                -- Input pixel from the image for this weight
                signal input_value_NYX : std_logic_vector(DIN_WIDTH - 1 downto 0);
                constant c_result_width : integer := SUMMAND_BIT_WIDTHS(c_current_index_NYX);
                --signal summand_result : signed(LARGEST_SUMMAND_BIT_WIDTH - 1 downto 0);
            begin
                -- Retrieve the pixel from the input window
                input_value_NYX <= f_get_vector_of_generic_window(crt_window_N, X, Y);
                
                
                p_generate_and_accumulate_summands : process(input_value_NYX) is
                    -- Index in the output array for the summand generated from this factor 
                    variable shifted_value_index_NYX : integer;
                    -- Integer value of the current factor
                    variable shift_factor_NYX : integer;
                    -- Expected maximum bit width of the generated summand
                    variable shifted_value_width_NYX : integer;
                    -- Result value (summand)
                    variable summand : integer;
                    
                    -- Accumulated result value, weighted input pixel
                    variable summand_accumulator : signed(c_result_width - 1 downto 0);
                    variable summand_result_fullbw : signed(LARGEST_SUMMAND_BIT_WIDTH - 1 downto 0);
                    variable summand_result_vector : std_logic_vector(LARGEST_SUMMAND_BIT_WIDTH - 1 downto 0);
                begin
                    summand_accumulator := (others => '0');
                    -- For all power of two factors of this weight
                    for Z in 0 to c_result_element_count_NYX - 1 loop
                        shifted_value_index_NYX := c_result_element_index_NYX + Z;
                        shift_factor_NYX := c_weight_shift_factors_NYX(Z);
                        shifted_value_width_NYX := c_summand_bit_widths(shifted_value_index_NYX);

                        -- Multiply the input value with the current weight factor (guaranteed powers of two +/-)
                        summand := shift_factor_NYX * to_integer(signed(input_value_NYX));
                        if Z = 0 then
                            summand_accumulator := to_signed(summand, c_result_width);
                        else
                            summand_accumulator := summand_accumulator + to_signed(summand, c_result_width);
                        end if;
                    end loop;
                    if LARGEST_SUMMAND_BIT_WIDTH > c_result_width then
                        summand_result_fullbw(LARGEST_SUMMAND_BIT_WIDTH - 1 downto c_result_width) := (others => summand_accumulator(summand_accumulator'length - 1));
                    end if;
                    summand_result_fullbw(summand_accumulator'range) := summand_accumulator;
                    
                    unsorted_elements(c_current_index_NYX) <= summand_result_fullbw;
                end process p_generate_and_accumulate_summands;
            end generate gen_produce_summands_NY;
        end generate gen_produce_summands_N;
    end generate gen_produce_summands;

    -- !No register stage!
    p_data_out : process(unsorted_elements) is
    begin
        for N in 0 to SUMMAND_COUNT - 1 loop
            data_out((N + 1) * LARGEST_SUMMAND_BIT_WIDTH - 1 downto N * LARGEST_SUMMAND_BIT_WIDTH) 
                <= std_logic_vector(unsorted_elements(N));
        end loop;
    end process;


end architecture;
    