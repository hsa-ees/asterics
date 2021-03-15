----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_cnn_serial_convolution_filter
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Philip Manke
--
-- Modified:       
--
-- Description:    This module implements a serial convolutional filter module
--                 with activation function, bias and quantization (TFLite)
--                 for implementing CNNs
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
--! @addtogroup asterics_modules
--! @{
--! @file  as_cnn_serial_convolution_filter.vhd
--! @brief This module implements a generic serial convolutional filter for CNNs.
--! @defgroup as_cnn_serial_convolution_filter as_cnn_serial_convolution_filter: Convolution for CNNs
--! This module implements a serial convolutional filter module
--! with activation function, bias and quantization (TFLite)
--! for implementing CNNs
--! @}
----------------------------------------------------------------------------------

--! @addtogroup as_cnn_serial_convolution_filter
--! @{
--! @defgroup as_cnn_serial_convolution_filter_internal Entities used within as_cnn_serial_convolution
--! This group contains VHDL entities used within the serial CNN convolution module.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use IEEE.math_real.all;

library asterics;
use asterics.helpers.all;
use asterics.as_generic_filter.all;
use asterics.as_cnn_helpers.all;
use asterics.as_wallace_adder_tree_generic;
use asterics.as_weighted_summand_generator;
use asterics.as_cnn_quantizer;

entity as_cnn_serial_convolution is
    generic(
        --! Bit width of the image data processed by this module.
        DIN_WIDTH : integer := 8;
        --! Number of filters implemented in this module.
        FILTER_COUNT : integer := 1;
        --! Number of input channels per filter.
        CHANNEL_COUNT: integer := 1;
        --! Bit width of the activations generated.
        DOUT_WIDTH : integer := 8;
        --! Height and width of the filters implemented.
        KERNEL_SIZE : integer := 3;
        --! Values of kernels to implement.
        --! KERNEL VALUE ORDER: (FILTER (output channel), (input) CHANNEL, VALUES (X -> Y))
        --! (VALUES(X, Y): ((0, 0), (1, 0), (2, 0), (0, 1), ..., (2, 2)))
        KERNEL_VALUES : t_generic_filter_array;
        --! Activation function to use on quantized convolution results.
        ACTIVATION_FUNCTION : string := "relu";
        --! Bias values in the same order as KERNEL_VALUES.
        BIAS_VALUES : t_integer_array;
        --! Quantization factors "M" in the same order as KERNEL_VALUES.
        QUANTIZATION_MULTIPLIERS : t_real_array;
        --! Quantization offset to apply to convolution results.
        QUANTIZATION_OFFSET : integer
    );
    port (
        clk        : in  std_logic;
        reset      : in  std_logic;

        --! AsWindow in strobe.
        strobe_in  : in  std_logic;
        --! AsWindow in data window.
        window_in  : in  t_generic_window(0 to KERNEL_SIZE - 1, 0 to KERNEL_SIZE - 1, (DIN_WIDTH * CHANNEL_COUNT) - 1 downto 0);
        --! AsWindow in stall.
        stall_in   : out std_logic;

        --! AsStream out data stream.
        data_out   : out std_logic_vector((DOUT_WIDTH * FILTER_COUNT) - 1 downto 0);
        --! AsStream out strobe.
        strobe_out : out std_logic;
        --! AsStream out stall.
        stall_out  : in  std_logic
    );
end as_cnn_serial_convolution;

--! @}

architecture RTL of as_cnn_serial_convolution is

    --! Width of the unsigned mux index vectors.
    constant c_control_index_width : integer := log2_ceil(FILTER_COUNT);
    --! Number of summands per filter.
    constant c_total_weighted_summand_counts : t_integer_array(0 to FILTER_COUNT - 1)
        := f_get_total_elements_for_weights_of_filters(KERNEL_VALUES);
    --! Maximum number of summands of any of the filters.
    constant c_max_summand_count : integer := f_get_largest_integer(c_total_weighted_summand_counts, 0, FILTER_COUNT - 1);
    --! Maximum bit widths for all summands of all filters (pixel bit width + weight factor bit width).
    constant c_filter_bit_widths : t_generic_filter(0 to FILTER_COUNT - 1, 0 to c_max_summand_count - 1) 
        := f_get_bit_widths_for_all_filters(KERNEL_VALUES, DIN_WIDTH, c_max_summand_count);
    constant c_largest_summand_bit_width : integer := f_get_filter_max(c_filter_bit_widths);
    --! Mappings from unsorted summand arrays to sorted arrays by bitwidth for all filters.
    constant c_sort_mappings : t_generic_filter(0 to FILTER_COUNT - 1, 0 to c_max_summand_count - 1)
        := f_get_sort_mappings_for_all_filters(c_filter_bit_widths);
    --! Largest summand bit width.
    constant c_largest_input_bit_width : integer := f_get_filter_max(c_filter_bit_widths);
    --! Output bit width of the shared adder.
    constant c_adder_output_bit_width : integer := c_largest_input_bit_width + log2_ceil_zero(c_max_summand_count);
    --! Sorted bit width arrays (low to high).
    constant c_sorted_bit_widths : t_generic_filter(0 to FILTER_COUNT - 1, 0 to c_max_summand_count - 1)
        := f_apply_sort_mapping_to_arrays(c_filter_bit_widths, c_sort_mappings);
    --! Largest bit widths occurring in each bit width array .
    constant c_largest_bit_width_by_position : t_integer_array(0 to c_max_summand_count - 1)
        := f_collapse_generic_filter_to_max_line(c_sorted_bit_widths);

    --! Compare 'M' value origins and splitting to M0 and n in the publication: 
    --! B. Jacob, S. Kligys, B. Chen, et al. 
    --! "Quantization and Training of Neural Networks for Efficient Integer-Arithmetic-Only Inference", 2017: 
    --! From the paper: M = 2^(−n) * M0
    --! @brief Array of the 'M0' part of the quantization factors.
    constant c_quant_m_zeros : t_unsigned_24_array(0 to FILTER_COUNT - 1) := f_get_mzero_array(QUANTIZATION_MULTIPLIERS);
    --! Array of the 'n' part of the quantization factors.
    constant c_quant_n_shifts : t_integer_array(0 to FILTER_COUNT - 1) := f_get_nshift_array(QUANTIZATION_MULTIPLIERS);
    --! Value of the largest 'n' in c_quant_n_shifts.
    constant c_largest_n_shift : integer := log2_ceil_zero(f_get_largest_integer(c_quant_n_shifts, 0, FILTER_COUNT - 1)) + 1;
    
    
    --! ASCII register stage overview: ( || ^= register stage )
    --! @verbatim
    --!               summand_gen             adder       quant_pipe
    --! data_in -||->[----------]->[MUX]-||->[----]--||->[----||--|6|--]->[DEMUX]--||--> data_out
    --!                                bias_ROM-->[MUX]->[->/   /    / ]
    --!                                mzero_ROM->[MUX]->[-||->/    /  ]
    --!                                n_ROM----->[MUX]->[-------->/   ]
    --! => 11 register stages
    --! Delay from serially calculating multiple convolutions = FILTER_COUNT - 1
    --! => Total delay to deliver a result = 11 + FILTER_COUNT - 1
    --! clock cycles per result = FILTER_COUNT
    --! Overhead = pipeline stages = 11
    --! @endverbatim
    --! @brief Number of pipeline/register stages in this module.
    constant c_pipeline_stage_count : integer := 11;
    --! Clocks per result. Describes the latency of this module in clock cycles.
    constant c_clocks_per_result : integer := c_pipeline_stage_count + FILTER_COUNT - 1;

    --! @brief Controls internal dataflow using (de-)multiplexers and enable signals.
    --! Control scheme:
    --! The register 'runtime_control' holds one or more '1's that start at position 0 and move up with every clock cycle
    --! Each 1 represents a received data word and its control flow through the module
    --! @verbatim
    --! Visual overview  : (4 filters per module)
    --! runtime_control  : [0|1|2|3|4|5|6|7|8|9|A|B|C|D|E] (width: c_clocks_per_result = 11 + 4 = 15)
    --! 
    --!                       Active for filter #
    --! 1's Direction                  ---->
    --! strobe_in        : [H|L|L|L|L|L|L|L|L|L|L|L|L|L|L]
    --! stall            : [H|H|H|L|L|L|L|L|L|L|L|L|L|L|L]
    --! Input regs       : [L|H|L|L|L|L|L|L|L|L|L|L|L|L|L]
    --! Adder input MUX  : [-|-|0|1|2|3|-|-|-|-|-|-|-|-|-]
    --! Adder input regs : [L|L|H|H|H|H|L|L|L|L|L|L|L|L|L]
    --! Adder reg strobe : [L|L|L|H|H|H|H|L|L|L|L|L|L|L|L]
    --! Quant strobe     : [-|-|-|-|H|H|H|H|H|H|H|H|H|H|H]
    --! Quant bias       : [-|-|-|-|0|1|2|3|-|-|-|-|-|-|-]
    --! Quant q_m_zero   : [-|-|-|-|0|1|2|3|-|-|-|-|-|-|-]
    --! Quant q_n        : [-|-|-|-|-|-|-|-|-|-|-|0|1|2|3]
    --! Quant DEMUX      : [-|-|-|-|-|-|-|-|-|-|-|0|1|2|3]
    --! Output regs      : [L|L|L|L|L|L|L|L|L|L|L|H|H|H|H]
    --! strobe_out       : [L|L|L|L|L|L|L|L|L|L|L|L|L|L|L|H]
    --! @endverbatim
    --! strobe_out is the last bit of runtime_control delayed by an additional cycle
    signal runtime_control : std_logic_vector(0 to c_clocks_per_result);
    --! Next and partial (current) state of runtime_control.
    signal runtime_control_next, runtime_control_int : std_logic_vector(0 to c_clocks_per_result - 1);

    --! Stall control offsets of runtime_control. 
    --! 'stall_in' is triggered if a 1 is within [0 to FILTER_COUNT - 2] of runtime_control
    --! The suffixes "lb" and "ub" stand for "lower bound" and "upper bound" respectively
    constant c_ctrl_stall_active_lb : integer := 0;
    --! Upper bound to c_ctrl_stall_active_lb.
    constant c_ctrl_stall_active_ub : integer := FILTER_COUNT - 2;

    -- Input registers control offsets of runtime_control. 
    -- The input registers are controlled by the strobe_in signal (= runtime_control(0))
    -- The registers serve to lower possible net delays for large designs

    --! Adder MUX and registers control offsets of runtime_control. 
    --! The multiplexer in front of the shared adder along with the input registers 
    --! are controlled by [2 to FILTER_COUNT + 1] of runtime_control
    --! selecting the weighted_sum_array entry of the filters in ascending order.
    --! Compare: index = log2(unsigned(runtime_control(2 to FILTER_COUNT + 1)))
    constant c_ctrl_adder_in_mux_lb : integer := 2;
    --! Upper bound to c_ctrl_adder_in_mux_lb.
    constant c_ctrl_adder_in_mux_ub : integer := FILTER_COUNT + 1;
    --! Adder output register control offsets of runtime_control. 
    --! The output registers are active when there is a 1 within [3 to FILTER_COUNT + 2]
    constant c_ctrl_adder_out_lb : integer := 3;
    --! Upper bound to c_ctrl_adder_out_lb.
    constant c_ctrl_adder_out_ub : integer := FILTER_COUNT + 2;
    --! Quantization pipeline control offsets of runtime_control.
    --! The quantization_pipeline needs to be fed with three different values at staggered intervals:
    --! The bias value is provided with the associated result from the adder [4 to FILTER_COUNT + 3]
    --! The quant_m_zero multiplier factor is required internally one clock cycle after the bias
    --! though, to lower net delays, the register is internal and the value is provided along with the bias
    constant c_ctrl_quant_bias_mzero_lb : integer := 4;
    --! Upper bound to c_ctrl_quant_bias_mzero_lb.
    constant c_ctrl_quant_bias_mzero_ub : integer := FILTER_COUNT + 3;
    --! Quantization shift parameter 'n' mulitplexer control offsets of runtime_control. 
    --! The multiplier, inferred as DSP slices may take multiple clock cycles to provide a result
    --! We give the synthesis tool 6 pipeline stages to optimize timing
    --! and correctly implement the large 24 bit * 56 bit multiplier
    --! Therefore the quant_n_shift value is provided four clock cycle after the bias [11 to FILTER_COUNT + 10]
    constant c_ctrl_quant_nshift_lb : integer := 11;
    --! Upper bound to c_ctrl_quant_nshift_lb.
    constant c_ctrl_quant_nshift_ub : integer := FILTER_COUNT + 10;
    --! Quantization results DEMUX control offsets of runtime_control. 
    --! The demultiplexer after the quantization pipeline stores the results of multiple convolutions
    --! in parallel registers so they can be output all at once. 
    --! As the output of the quant pipe is not registered it is controlled by [11 to FILTER_COUNT + 10]
    constant c_ctrl_quant_demux_lb : integer := 11;


    --! Index for the adder input multiplexer.
    signal adder_mux_ctrl_index : unsigned(c_control_index_width - 1 downto 0);
    --! Index for the bias and mzero multiplexers.
    signal quant_bias_mzero_ctrl_index : unsigned(c_control_index_width - 1 downto 0);
    --! Index for the shift parameter 'n' multiplexer.
    signal quant_nshift_ctrl_index : unsigned(c_control_index_width - 1 downto 0);
    
    --! Strobe signals for the quantization pipeline and internal register stages.
    signal strobe_quant, strobe_adder_in, strobe_adder_out, strobe_input_regs : std_logic;
    --! Stall output signal (inverted ready).
    signal stall_out_int : std_logic;
    --! Input registers for image window data.
    signal input_window_regs : t_generic_window(0 to KERNEL_SIZE - 1, 0 to KERNEL_SIZE - 1, (DIN_WIDTH * CHANNEL_COUNT) - 1 downto 0);
    --! Type for an array of summand arrays (each summand array is implemented as a std_logic_vector).
    type t_summand_array is array(0 to FILTER_COUNT - 1) of std_logic_vector(c_largest_summand_bit_width * c_max_summand_count - 1 downto 0);
    --! Bitwidth-sorted summand arrays (input for the adder multiplexer).
    signal weighted_summand_arrays : t_summand_array;
    --! Adder data input.
    signal adder_tree_data_in : std_logic_vector(c_largest_summand_bit_width * c_max_summand_count - 1 downto 0);
    --! Quantization pipeline input (output of adder).
    signal quant_data_in : std_logic_vector(c_adder_output_bit_width - 1 downto 0);
    --! Quantization pipeline bias input.
    signal quant_bias_in : signed(31 downto 0);
    --! Quantization pipeline M0 input.
    signal quant_mzero_in : unsigned(23 downto 0);
    --! Quantization pipeline n input.
    signal quant_n_shift_in : unsigned(c_largest_n_shift - 1 downto 0);
    --! Quantization pipeline data output.
    signal quant_data_out : std_logic_vector(DOUT_WIDTH - 1 downto 0);
    --! Internal pipeline stall signal. Stalls all internal execution if high.
    signal stall_int : std_logic;

    --! Type for output_regs, a simple array of FILTER_COUNT std_logic_vectors with DOUT_WIDTH bits.
    type t_output_registers is array(0 to FILTER_COUNT - 1) of std_logic_vector(DOUT_WIDTH - 1 downto 0);
    --! Output register array, mapped onto 'data_out'.
    signal output_regs : t_output_registers;

begin
    --! Only generate the stall logic if more than one filter is implemented (out-of-bounds access error otherwise).
    gen_stall_logic : if FILTER_COUNT > 1 generate
        stall_out_int <= '1' when unsigned(runtime_control(c_ctrl_stall_active_lb to c_ctrl_stall_active_ub)) > 0 or stall_int = '1' else '0';
    end generate;
    gen_no_stall_logic : if FILTER_COUNT = 1 generate
        stall_out_int <= stall_int;
    end generate;

    stall_in <= stall_out_int;

    -- Stall internal execution when both external stall is high and the next cycle would produce an output
    -- Otherwise, if external stall is high and further internal execution does not produce results, it is safe to continue processing
    stall_int <= '1' when ((stall_out = '1') and (runtime_control(runtime_control'length - 1) = '1')) else '0';

    -- strobe_in functions as the first bit of runtime_control
    runtime_control <= strobe_in & runtime_control_int;
    runtime_control_next <= runtime_control(0 to runtime_control'length - 2);

    --! Update control status register.
    p_conv_control : process(clk) is
        variable v_next_runtime_control : std_logic_vector(runtime_control'range);
        constant c_start : unsigned(FILTER_COUNT - 1 downto 0) := shift_left(to_unsigned(1, FILTER_COUNT), FILTER_COUNT - 1);
    begin
        if rising_edge(clk) then
            if reset = '1' then
                strobe_out <= '0';
                runtime_control_int <= (others => '0');
            else
                -- Halt when internal stall is high
                if stall_int = '0' then
                    -- Shift runtime_control every clock cycle
                    runtime_control_int <= runtime_control_next;

                    -- Update multiplexer control index signals
                    -- The mutliplexer indices are generated using small counters
                    if (unsigned(runtime_control_next(c_ctrl_adder_in_mux_lb - 1 to c_ctrl_adder_in_mux_ub - 1)) = c_start)
                            or (unsigned(runtime_control_next(c_ctrl_adder_in_mux_lb - 1 to c_ctrl_adder_in_mux_ub - 1)) = 0) then
                        adder_mux_ctrl_index <= (others => '0');
                    elsif unsigned(runtime_control_next(c_ctrl_adder_in_mux_lb - 1 to c_ctrl_adder_in_mux_ub - 1)) > 0 then
                        adder_mux_ctrl_index <= adder_mux_ctrl_index + 1;
                    end if;

                    if (unsigned(runtime_control_next(c_ctrl_quant_bias_mzero_lb - 1 to c_ctrl_quant_bias_mzero_ub - 1)) = c_start)
                            or (unsigned(runtime_control_next(c_ctrl_quant_bias_mzero_lb - 1 to c_ctrl_quant_bias_mzero_ub - 1)) = 0) then
                        quant_bias_mzero_ctrl_index <= (others => '0');
                    elsif unsigned(runtime_control_next(c_ctrl_quant_bias_mzero_lb - 1 to c_ctrl_quant_bias_mzero_ub - 1)) > 0 then
                        quant_bias_mzero_ctrl_index <= quant_bias_mzero_ctrl_index + 1;
                    end if;

                    if (unsigned(runtime_control_next(c_ctrl_quant_nshift_lb - 1 to c_ctrl_quant_nshift_ub - 1)) = c_start)
                            or (unsigned(runtime_control_next(c_ctrl_quant_nshift_lb - 1 to c_ctrl_quant_nshift_ub - 1)) = 0) then
                        quant_nshift_ctrl_index <= (others => '0');
                    elsif unsigned(runtime_control_next(c_ctrl_quant_nshift_lb - 1 to c_ctrl_quant_nshift_ub - 1)) > 0 then
                        quant_nshift_ctrl_index <= quant_nshift_ctrl_index + 1;
                    end if;

                    strobe_out <= runtime_control_int(runtime_control_int'length - 1);
                end if;
            end if;
        end if;
    end process;

    -- Internal strobe signals: 
    -- Active while quantization pipeline processes data: Input from adder output, to output to quant DEMUX
    strobe_quant <= '1' when unsigned(runtime_control(c_ctrl_quant_bias_mzero_lb to c_ctrl_quant_nshift_ub - 1)) > 0 
                             and stall_int = '0' else '0';

    -- Strobe for register stage internal to adder tree component
    strobe_adder_out <= '1' when unsigned(runtime_control(c_ctrl_adder_out_lb to c_ctrl_adder_out_ub)) > 0 
                                 and stall_int = '0' else '0';
    strobe_adder_in <= '1' when unsigned(runtime_control(c_ctrl_adder_in_mux_lb to c_ctrl_adder_in_mux_ub)) > 0
                                and stall_int = '0' else '0';
    
    -- Strobe for input registers
    strobe_input_regs <= '1' when runtime_control(1) = '1' and stall_int = '0' else '0';

    --! Input register stage.
    p_input_registers : process(clk) is
    begin
        if rising_edge(clk) then
            if strobe_input_regs = '1' then
                input_window_regs <= window_in;
            end if;
        end if;
    end process;


    --! Summand generators.
    gen_summand_generators : for F in 0 to FILTER_COUNT - 1 generate
        -- Get kernel values per filter
        constant c_kernel_values_F : t_generic_filter(KERNEL_VALUES'range(2), KERNEL_VALUES'range(3)) 
            := f_get_kernel_values_for_single_filter(KERNEL_VALUES, F);
        -- Total summands expected for this filter kernel
        constant c_total_weighted_summands_F : integer := c_total_weighted_summand_counts(F);
        -- Array of bit widths for each summand
        constant c_summand_bit_widths_F : t_integer_array := f_get_line_of_generic_filter(c_filter_bit_widths, F);
        -- Mapping of indices when mapping unsorted summands to sorted summands arrays
        constant c_sort_mapping_F : t_integer_array := f_get_line_of_generic_filter(c_sort_mappings, F);
        
        -- Generated summands
        signal weighted_summands_nonzero_F : std_logic_vector(c_total_weighted_summands_F * c_largest_summand_bit_width - 1 downto 0);
        -- Array the size of the maximum amount of summands for all filters
        -- (weighted_summands_nonzero_F filled up with zeros)
        signal weighted_summands_F : t_integer_array(0 to c_max_summand_count - 1);
        -- weighted_summands_F with the sort mapping applied
        signal weighted_summands_sorted_F : t_integer_array(0 to c_max_summand_count - 1);
    begin

        summand_generator_F : entity as_weighted_summand_generator
        generic map(
            DIN_WIDTH => DIN_WIDTH,
            CHANNEL_COUNT => CHANNEL_COUNT,
            KERNEL_SIZE => KERNEL_SIZE,
            KERNEL_VALUES => c_kernel_values_F,
            SUMMAND_COUNT => c_total_weighted_summands_F,
            SUMMAND_BIT_WIDTHS => c_summand_bit_widths_F,
            LARGEST_SUMMAND_BIT_WIDTH => c_largest_summand_bit_width
        )
        port map(
            window_in => input_window_regs,
            data_out => weighted_summands_nonzero_F
        );

        --! Assign generated summands.
        p_retrieve_summands : process(weighted_summands_nonzero_F) is
        begin
            for N in 0 to c_total_weighted_summands_F - 1 loop
                weighted_summands_F(N) <= to_integer(signed(weighted_summands_nonzero_F((N + 1) * c_largest_summand_bit_width - 1 downto N * c_largest_summand_bit_width)));
            end loop;
        end process;

        -- Fill the remaining array with zeros, to align with the filter with the most summands
        weighted_summands_F(c_total_weighted_summands_F to c_max_summand_count - 1) <= (others => 0);
        -- Sort the summands by bitwidth (reorder them only by wiring) from low to high
        weighted_summands_sorted_F <= f_get_sorted_signal_list_by_mapping(weighted_summands_F, c_sort_mapping_F);

        --! Assign to the array of summand arrays.
        p_assign_summands : process(weighted_summands_sorted_F) is
        begin
            for N in 0 to c_max_summand_count - 1 loop
                weighted_summand_arrays(F)((N + 1) * c_largest_summand_bit_width - 1 downto N * c_largest_summand_bit_width) 
                    <= std_logic_vector(to_signed(weighted_summands_sorted_F(N), c_largest_summand_bit_width));
            end loop;
        end process;
        --weighted_summand_arrays(F) <= weighted_summands_sorted_F;
    end generate gen_summand_generators;

    --! Adder multiplexer and input register stage.
    p_adder_input_register_stage : process(clk) is
    begin
        if rising_edge(clk) then
            if strobe_adder_in = '1' then
                adder_tree_data_in <= weighted_summand_arrays(to_integer(adder_mux_ctrl_index));
            end if;
        end if;
    end process;

    shared_adder_tree : entity as_wallace_adder_tree_generic
    generic map(
        DOUT_WIDTH => c_adder_output_bit_width,
        BIT_WIDTHS => c_largest_bit_width_by_position,
        ELEMENT_COUNT => c_max_summand_count,
        LARGEST_BIT_WIDTH => c_largest_summand_bit_width
    )
    port map(
        clk => clk,
        reset => reset,
        strobe_in => strobe_adder_out,
        data_in => adder_tree_data_in,
        data_out => quant_data_in
    );

    -- Multiplexers for quantization pipeline data inputs (bias, quant_mzero, quant_n)
    quant_bias_in <= to_signed(BIAS_VALUES(to_integer(quant_bias_mzero_ctrl_index)), 32);
    quant_mzero_in <= c_quant_m_zeros(to_integer(quant_bias_mzero_ctrl_index));
    quant_n_shift_in <= to_unsigned(c_quant_n_shifts(to_integer(quant_nshift_ctrl_index)), c_largest_n_shift);

    shared_quantization_pipeline : entity as_cnn_quantizer
    generic map(
        DIN_WIDTH => c_adder_output_bit_width,
        DOUT_WIDTH => DOUT_WIDTH,
        ACTIVATION_FUNCTION => ACTIVATION_FUNCTION,
        QUANT_N_SHIFT_BITWIDTH => c_largest_n_shift,
        QUANTIZATION_OFFSET => QUANTIZATION_OFFSET
    )
    port map(
        clk => clk,
        reset => reset,
        strobe_in => strobe_quant,
        data_in => quant_data_in,
        bias_value => quant_bias_in,
        quant_m_zero => quant_mzero_in,
        quant_n_shift => quant_n_shift_in,
        data_out => quant_data_out
    );

    --! Assign results from the quantization pipe to the output registers.
    --! Results from the serial computation are gathered and output together
    p_output_registers : process(clk) is
    begin
        if rising_edge(clk) then
            if reset = '1' then
                output_regs <= (others => (others => '0'));
            else
                -- Only apply the result from the filter that just finished computing
                -- Keep all other results
                for F in 0 to FILTER_COUNT - 1 loop
                    if runtime_control(c_ctrl_quant_demux_lb + F) = '1' then
                        output_regs(F) <= quant_data_out;
                    end if;
                end loop;
            end if;
        end if;
    end process;

    gen_wire_output : for F in 0 to FILTER_COUNT - 1 generate
        -- Assign output registers in correct order (filter 0 must start at DOUT_WIDTH - 1)
        data_out((F + 1) * DOUT_WIDTH - 1 downto F * DOUT_WIDTH) <= output_regs(F);
    end generate;

end architecture;

