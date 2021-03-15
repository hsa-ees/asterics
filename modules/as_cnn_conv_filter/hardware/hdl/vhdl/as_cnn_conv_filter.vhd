----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_cnn_conv_filter
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Philip Manke
--
-- Modified:       
--
-- Description:    This module implements a convolutional filter module with
--                 activation function and bias for implementing CNNs
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
--! @file  as_cnn_conv_filter.vhd
--! @brief This module implements a generic convolutional filter for CNNs.
----------------------------------------------------------------------------------


library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library asterics;
use asterics.helpers.all;
use asterics.as_generic_filter.all;
use asterics.as_2d_conv_filter_external;

entity as_cnn_conv_filter is
    generic(
        DIN_WIDTH : integer := 8;
        WEIGHTS_BIT_WIDTH : integer := 8;
        CHANNEL_COUNT: integer := 1;
        DOUT_WIDTH : integer := 8;
        KERNEL_SIZE : integer := 3;
        KERNEL_VALUES : t_generic_filter;
        ACTIVATION_FUNCTION : string := "relu";
        BIAS_VALUE : integer := 0;
        STRIDE_X : integer := 1;
        STRIDE_Y : integer := 1
    );
    port (
        clk         : in  std_logic;
        reset       : in  std_logic;

        hsync : in std_logic;

        -- AsWindow in ports
        strobe_in     : in  std_logic;
        window_in     : in  t_generic_window(0 to KERNEL_SIZE - 1, 0 to KERNEL_SIZE - 1, (DIN_WIDTH * CHANNEL_COUNT) - 1 downto 0);
        
        -- AsStream out ports: Filtered
        strobe_out     : out std_logic;
        data_out       : out std_logic_vector(DOUT_WIDTH - 1 downto 0)
    );
end as_cnn_conv_filter;


architecture RTL of as_cnn_conv_filter is
    constant c_weights_per_kernel : integer := KERNEL_SIZE * KERNEL_SIZE;
    constant c_comp_data_width_add : integer := log2_ceil_zero(CHANNEL_COUNT);
    constant c_max_output_bits : unsigned(DOUT_WIDTH - 1 downto 0) := (others => '1');

    type t_window_array is array(0 to CHANNEL_COUNT - 1) of t_generic_window(0 to KERNEL_SIZE - 1, 0 to KERNEL_SIZE - 1, DIN_WIDTH - 1 downto 0);
    type t_result_array is array(0 to CHANNEL_COUNT - 1) of std_logic_vector(DOUT_WIDTH - 1 downto 0);

    signal window_internal : t_window_array;

    signal strobe_sx, strobe_sy : std_logic;
    signal conv_data : t_result_array;
    signal stride_x_counter : std_logic_vector(STRIDE_X - 1 downto 0);
    signal stride_y_counter : std_logic_vector(STRIDE_Y - 1 downto 0);
begin

    gen_filter : for N in 0 to CHANNEL_COUNT - 1 generate
        
        -- Assign channel of input window to filter's window port
        window_internal(N) <= f_cut_vectors_of_generic_window(window_in, N * DIN_WIDTH, DIN_WIDTH);
        
        -- Instantiate filter module and pass the kernel to it
        filter : entity as_2d_conv_filter_external
        generic map(
            DIN_WIDTH => DIN_WIDTH,
            FILTER_BIT_WIDTH => WEIGHTS_BIT_WIDTH,
            DOUT_WIDTH => DOUT_WIDTH,
            KERNEL_SIZE => KERNEL_SIZE,
            KERNEL_WEIGHTS => f_get_line_of_generic_filter(KERNEL_VALUES, N),
            NORMALIZE_TO_HALF => false,
            OUTPUT_SIGNED => true
        )
        port map(
            clk => clk,
            reset => reset,
            strobe_in => strobe_in,
            window_in => window_internal(N),
            data_out => conv_data(N)
        );
    end generate;

    p_activation : process(clk)
        variable data_out_no_bias : signed(DOUT_WIDTH + c_comp_data_width_add - 1 downto 0);
        variable conv_data_sum : signed(DOUT_WIDTH + c_comp_data_width_add - 1 downto 0);
        variable data_out_int : std_logic_vector(DOUT_WIDTH + c_comp_data_width_add - 1 downto 0);
    begin
        if rising_edge(clk) then
            if reset = '1' then
                data_out <= (others => '0');
                data_out_no_bias := (others => '0');
                conv_data_sum := (others => '0');
                data_out_int := (others => '0');
            else
                conv_data_sum := (others => '0');
                for N in 0 to CHANNEL_COUNT - 1 loop
                    conv_data_sum := conv_data_sum + signed(conv_data(N));
                end loop;
                if ACTIVATION_FUNCTION = "relu" then
                    data_out_no_bias := to_signed(f_relu(to_integer(conv_data_sum)), DOUT_WIDTH + c_comp_data_width_add);
                elsif ACTIVATION_FUNCTION = "none" then
                    data_out_no_bias := conv_data_sum;
                end if;
                data_out_int := std_logic_vector(data_out_no_bias + BIAS_VALUE);
                if abs(to_integer(signed(data_out_int))) <= to_integer(c_max_output_bits) then 
                    data_out <= data_out_int(DOUT_WIDTH - 1 downto 0);
                else
                    data_out(DOUT_WIDTH - 1) <= data_out_int(data_out_int'length - 1);
                    data_out(DOUT_WIDTH - 2 downto 0) <= (others => '1');
                end if;
            end if;
        end if;
    end process;

    p_strobe_gen : process(clk) is
    begin
        if rising_edge(clk) then
            if reset = '1' then
                stride_x_counter <= (0 => '1', others => '0');
                stride_y_counter <= (0 => '1', others => '0');
            else
                if strobe_in = '1' then
                    stride_x_counter <= rotate_right(stride_x_counter, 1);
                    if hsync = '1' then
                        stride_y_counter <= rotate_right(stride_y_counter, 1);
                    end if;
                end if;
            end if;
        end if;
    end process;

    strobe_sx <= stride_x_counter(0) and strobe_in;
    strobe_sy <= stride_y_counter(0) and strobe_in;
    strobe_out <= strobe_sx and strobe_sy;
end RTL;
    
    