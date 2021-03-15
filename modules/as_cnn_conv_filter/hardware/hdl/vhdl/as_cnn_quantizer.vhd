----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_cnn_quantizer
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Philip Manke
--
-- Modified:       
--
-- Description:    This module implements the "postprocessing" steps for 
--                 "raw" convolution results of convolution filters of CNNs.
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
--! @file  as_cnn_quantizer.vhd
--! @brief Quantization, activation, type casting and BIAS handling for CNNs.
----------------------------------------------------------------------------------

--! @addtogroup as_cnn_serial_convolution_filter_internal
--! @{

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use IEEE.math_real.all;

library asterics;
use asterics.helpers.all;
use asterics.as_generic_filter.all;
use asterics.as_cnn_helpers.all;

entity as_cnn_quantizer is
    generic(
        DIN_WIDTH : integer := 8;
        DOUT_WIDTH : integer := 8;
        ACTIVATION_FUNCTION : string := "relu";
        QUANT_N_SHIFT_BITWIDTH : integer := 4;
        QUANTIZATION_OFFSET : integer := 0
    );
    port (
        clk         : in  std_logic;
        reset       : in  std_logic;
        strobe_in   : in  std_logic;

        -- Interpreted as SIGNED
        -- !Clock cycle offset 0!
        data_in     : in  std_logic_vector(DIN_WIDTH - 1 downto 0);
        -- !Clock cycle offset 0!
        bias_value  : in signed(31 downto 0);
        -- !Clock cycle offset 0 (internal register stage)!
        quant_m_zero  : in unsigned(23 downto 0);
        -- !Clock cycle offset 6!
        quant_n_shift : in unsigned(QUANT_N_SHIFT_BITWIDTH - 1 downto 0);

        -- Output after 7 clock cycles (signed value)
        data_out    : out std_logic_vector(DOUT_WIDTH - 1 downto 0)
    );
end as_cnn_quantizer;

--! @}

architecture RTL of as_cnn_quantizer is
    -- Register stage signals
    signal data_with_bias     : signed(55 downto 0);
    signal mzero_register     : signed(23 downto 0);
    signal data_with_mzero    : signed(79 downto 0);
    signal data_with_mzero_s1 : signed(data_with_mzero'range);
    signal data_with_mzero_s2 : signed(data_with_mzero'range);
    signal data_with_mzero_s3 : signed(data_with_mzero'range);
    signal data_with_mzero_s4 : signed(data_with_mzero'range);
    signal data_with_mzero_s5 : signed(data_with_mzero'range);
begin

    p_bias_add : process(clk)
        variable sum : signed(31 downto 0);
        variable integer_result : integer;
    begin   
        if rising_edge(clk) then
            if reset = '1' then
                data_with_bias <= (others => '0');
                mzero_register <= (others => '0');
            else
                if strobe_in = '1' then
                    -- Store raw convolution result in 32 bits for processing
                    sum := resize(signed(data_in), 32);
                    -- Apply BIAS
                    sum := sum + bias_value; 
                    data_with_bias(55 downto 24) <= sum; -- !register stage!
                    data_with_bias(23 downto 0) <= (others => '0');
                    -- Hold M0 value (Reduces signal delay to multiplier)
                    mzero_register <= signed(quant_m_zero); -- !register stage!
                end if;
            end if;
        end if;
    end process;

    p_quantization_multiplier_stage_0 : process(clk)
    begin   
        if rising_edge(clk) then
            if strobe_in = '1' then
                data_with_mzero_s5 <= data_with_mzero_s4; --  !register stage!
                data_with_mzero_s4 <= data_with_mzero_s3; --  !register stage!
                data_with_mzero_s3 <= data_with_mzero_s2; --  !register stage!
                data_with_mzero_s2 <= data_with_mzero_s1; --  !register stage!
                data_with_mzero_s1 <= data_with_mzero;    --  !register stage!
                -- Multiply with quantization scaling factor M0
                data_with_mzero <= data_with_bias * mzero_register; --  !register stage!
            end if;
        end if;
    end process;

    p_activation : process(quant_n_shift, data_with_mzero_s5)
        constant clamping_value_p : integer := (2 ** (DOUT_WIDTH - 1)) - 1;
        constant clamping_value_n : integer := (2 ** (DOUT_WIDTH - 1)) * (-1);
        constant c_quant_offset : signed(31 downto 0) := to_signed(QUANTIZATION_OFFSET, 32);
        
        variable scaled_result_signed : signed(31 downto 0);
        variable data_shifted : signed(31 downto 0) := (others => '0');
        variable data_quantized : signed(31 downto 0) := (others => '0');
        variable data_saturated : signed(DOUT_WIDTH - 1 downto 0) := (others => '0');
        variable data_activated : signed(DOUT_WIDTH - 1 downto 0) := (others => '0');
    begin
        scaled_result_signed := data_with_mzero_s5(78 downto 47);
        -- Rounding right_shift by n (c_n)
        -- Equivalent to multiplication by 2^(-c_n) + data_with_mzero(c_n - 1)
        data_shifted := f_rounding_right_shift_non_reducing(scaled_result_signed, to_integer(quant_n_shift));
        -- Apply offset defined by QUANTIZATION_OFFSET
        data_quantized := data_shifted + c_quant_offset;
        -- Clamp values to value domain of signed DOUT_WIDTH bits
        if to_integer(data_quantized) > clamping_value_p then
            data_saturated := to_signed(clamping_value_p, DOUT_WIDTH);
        elsif to_integer(data_quantized) < clamping_value_n then
            data_saturated := to_signed(clamping_value_n, DOUT_WIDTH);
        else
            data_saturated := data_quantized(DOUT_WIDTH - 1 downto 0);
        end if;
        -- Apply activation function
        if ACTIVATION_FUNCTION = "relu" then
            data_activated := to_signed(f_relu(to_integer(data_saturated)), DOUT_WIDTH);
        elsif ACTIVATION_FUNCTION = "none" then
            data_activated := data_saturated;
        end if;
        -- Output register stage
        data_out <= std_logic_vector(data_activated);
    end process;

end architecture;
    