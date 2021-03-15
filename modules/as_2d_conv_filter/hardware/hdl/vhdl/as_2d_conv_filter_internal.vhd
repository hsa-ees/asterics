----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_2d_conv_filter_internal
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Philip Manke
--
-- Modified:       
--
-- Description:    This module implements a convolutional filter module with
--                 several internal filter kernels, which can be selected using generics
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
--! @file  as_2d_conv_filter_internal.vhd
--! @brief This module implements a generic convolutional filter.
--! @addtogroup asterics_modules
--! @{
--! @defgroup as_2d_conv_filter_internal as_2d_conv_filter_internal: 2D Convolution (Preset Kernels)
--! This module implements 2D convolution using a built-in kernel selected via generics.
--! For use in 2D Window Pipeline systems.
--! @}
----------------------------------------------------------------------------------

--! @addtogroup as_2d_conv_filter_internal
--! @{

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

library asterics;
use asterics.helpers.all;
use asterics.as_generic_filter.all;
use asterics.as_generic_filter_module;

entity as_2d_conv_filter_internal is
    generic (
        DIN_WIDTH : integer := 8;
        DOUT_WIDTH : integer := 8;
        --! Both height and width of the kernel
        KERNEL_SIZE : integer := 5;
        --! Select built-in kernel
        KERNEL_TYPE : string := "gauss";
        --! Add 2^DOUT_WIDTH to the convolution result
        --! prevents overflows for kernels returning negative numbers
        NORMALIZE_TO_HALF : boolean := False;
        --! Interpret convolution results as signed numbers
        OUTPUT_SIGNED : boolean := False
    );
    port (
        clk         : in  std_logic;
        reset       : in  std_logic;

        --! AsWindow in strobe
        strobe_in     : in  std_logic;
        --! AsWindow in data
        window_in     : in  t_generic_window(0 to KERNEL_SIZE - 1, 0 to KERNEL_SIZE - 1, DIN_WIDTH - 1 downto 0);
        
        --! AsStream out data: convolved (filtered)
        data_out       : out std_logic_vector(DOUT_WIDTH - 1 downto 0)
    );
end as_2d_conv_filter_internal;

--! @}

architecture RTL of as_2d_conv_filter_internal is

    --! Convert filter kernel to window data type:
    constant c_filter_port : t_generic_window(0 to KERNEL_SIZE - 1, 0 to KERNEL_SIZE - 1, DIN_WIDTH downto 0) :=
                 f_make_generic_window(KERNEL_SIZE, KERNEL_SIZE, select_kernel(KERNEL_SIZE, KERNEL_TYPE), DIN_WIDTH + 1);

    --! Internal compute data width
    constant c_comp_data_width_add : integer := log2_ceil_zero(f_get_window_sum_abs(c_filter_port));
    

begin

    --! Instantiate filter module and pass the kernel to it
    filter : entity as_generic_filter_module
    generic map(
        DIN_WIDTH => DIN_WIDTH,
        FILTER_BIT_WIDTH => DIN_WIDTH + 1,
        DOUT_WIDTH => DOUT_WIDTH,
        WINDOW_X => KERNEL_SIZE,
        WINDOW_Y => KERNEL_SIZE,
        COMPUTATION_DATA_WIDTH_ADD => c_comp_data_width_add,
        NORMALIZE_TO_HALF => NORMALIZE_TO_HALF,
        OUTPUT_SIGNED => OUTPUT_SIGNED
    )
    port map(
        clk => clk,
        reset => reset,
        filter_values => c_filter_port,
        strobe => strobe_in,
        window => window_in,
        data_out => data_out
    );

end RTL;
    
    
