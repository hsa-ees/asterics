----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_single_conv_filter
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Philip Manke
--
-- Modified:       
--
-- Description:    This module implements one of three types of edge filter:
--                 Sobel X, Sobel Y or Laplace in size 3x3 or 5x5
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
--! @file  as_single_conv_filter.vhd
--! @brief Implements a simple convolution filter with a built-in selection of kernels.
--! @addtogroup asterics_modules
--! @{
--! @defgroup as_single_conv_filter as_single_conv_filter: Convolution Filter
--! This module packages 'as_2d_conv_filter_internal' as an AsStream pixel streaming module.
--! One of the following convolution kernels can be selected using generics:
--! Laplace edge filter ('laplace'), Sobel X or Y edge filter ('sobel_x', 'sobel_y'),
--! Gauss blurring filter ('gauss').
--! @}
----------------------------------------------------------------------------------

--! @addtogroup as_single_conv_filter
--! @{


library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

library asterics;
use asterics.helpers.all;
use asterics.as_generic_filter.all;
use asterics.as_window_buff_nxm;
use asterics.as_2d_conv_filter_internal;
use asterics.as_pipeline_flush;

entity as_single_conv_filter is
    generic (
        -- Width of the input and output data port
        DIN_WIDTH : integer := 8;
        DOUT_WIDTH : integer := 8;
        LINE_WIDTH : integer := 640;
        MINIMUM_BRAM_SIZE : integer := 64;
        FILTER_KERNEL_SIZE : integer := 5;
        FILTER_KERNEL_TYPE : string := "laplace";
        NORMALIZE_OUTPUT : boolean := true;
        OUTPUT_SIGNED : boolean := false
    );
    port (
        clk         : in  std_logic;
        reset       : in  std_logic;
        ready       : out std_logic;

        -- AsStream in ports
        strobe_in     : in  std_logic;
        data_in       : in  std_logic_vector(DIN_WIDTH - 1 downto 0);
        stall_out     : out std_logic;

        -- AsStream out ports: Filtered
        strobe_out     : out std_logic;
        data_out       : out std_logic_vector(DOUT_WIDTH - 1 downto 0);
        stall_in       : in  std_logic;
        vcomplete_out  : out std_logic;

        --! Slave register interface:
        --! Control registers. SW -> HW data transport
        slv_ctrl_reg : in slv_reg_data(0 to 0);
        --! Status registers. HW -> SW data transport
        slv_status_reg : out slv_reg_data(0 to 0);
        --! Aquivalent to a write enable signal. When HW want's to write into a register, it needs to pulse this signal.
        slv_reg_modify : out std_logic_vector(0 to 0);
        --! Slave register configuration table.
        slv_reg_config : out slv_reg_config_table(0 to 0)
    );
end as_single_conv_filter;

--! @}

architecture RTL of as_single_conv_filter is

    -- Slave register configuration:
    -- Allows for "dynamic" configuration of slave registers
    -- Possible values and what they mean: 
    -- AS_REG_NONE    / "00": Register "off". Register will not be available and won't be implemented -> No hardware resource utilization.
    -- AS_REG_STATUS  / "01": From HW view: Status register. Data transport from hardware to software. HW can only write, SW can only read.
    -- AS_REG_CONTROL / "10": From HW view: Control register. Data transport from software to hardware. HW can only read, SW can only write.
    -- AS_REG_BOTH    / "11": Combined Read/Write register. Data transport in both directions. 
    --       When both sides attempt to write simultaniously, only the HW gets to write.
    --       These registers use both the slv_ctrl_reg and slv_status_reg ports for communication.
    constant slave_register_configuration : slv_reg_config_table(0 to 0) := (0 => AS_REG_BOTH);
    
    -- Filter input window
    signal window : t_generic_window(0 to FILTER_KERNEL_SIZE - 1, 0 to FILTER_KERNEL_SIZE - 1, DIN_WIDTH - 1 downto 0);

    -- State and control signals
    signal flush_in : std_logic; -- Flush control reg
    signal flush_complete : std_logic;
    signal ready_internal : std_logic; -- Internal ready signal
    signal pipeline_data : std_logic_vector(DIN_WIDTH - 1 downto 0);
    signal filter_data : std_logic_vector(DOUT_WIDTH - 1 downto 0);
    signal reg_reset, reset_int : std_logic;
    signal strobe_int : std_logic; -- Internal strobe signal
    signal reg_update_enable : std_logic; -- Enable signal for status register updates
    signal status_reg_int : std_logic_vector(1 downto 0); -- Internal version of the status register; used to determine when an update is required (we can't continually update, that would override data from software!)
begin

    -- Check for valid filter width and type...
    assert ((FILTER_KERNEL_SIZE = 3) or (FILTER_KERNEL_SIZE = 5) or (FILTER_KERNEL_SIZE = 7) or (FILTER_KERNEL_SIZE = 9) or (FILTER_KERNEL_SIZE = 11) or (FILTER_KERNEL_SIZE = 13))
        report "Kernel size invalid! Must be one of: (3, 5) or (7, 9, 11, 13) for 'gauss' kernel only!"
        severity failure;
    assert ((FILTER_KERNEL_TYPE = "sobel_x") or (FILTER_KERNEL_TYPE = "sobel_y") or (FILTER_KERNEL_TYPE = "laplace") or (FILTER_KERNEL_TYPE = "gauss"))
        report "Kernel type invalid! Must be one of: (gauss, sobel_x, sobel_y, laplace)!"
        severity failure;
    
    -- Register interface logic --
    
    -- Assign the register configuration to the register interface. 
    slv_reg_config <= slave_register_configuration;
    
    flush_in <= slv_ctrl_reg(0)(0);
    reg_reset <= slv_ctrl_reg(0)(1);
    slv_status_reg(0)(17 downto 16) <= status_reg_int;
    status_reg_int <= (0 => ready_internal,
                       1 => stall_in);
    slv_reg_modify(0) <= reg_update_enable;

    -- Update the status register
    reg_update : process(clk) is
    begin
        if rising_edge(clk) then
            if reset = '1' then
                slv_status_reg(0)(31 downto 18) <= (others => '0');
                slv_status_reg(0)(15 downto 0) <= (others => '0');
                reg_update_enable <= '1';
            else
                reg_update_enable <= '0';
                if flush_in = '1' and ready_internal = '0' then
                    slv_status_reg(0)(0) <= '0';
                    reg_update_enable <= '1';
                end if;
                if slv_ctrl_reg(0)(17 downto 16) /= status_reg_int then
                    reg_update_enable <= '1';
                end if;
            end if;
        end if;
    end process;

    -- Module logic --
    -- Instantiate flush control module
    flush_control : entity as_pipeline_flush
    generic map(
        DIN_WIDTH => DIN_WIDTH,
        DOUT_WIDTH => DOUT_WIDTH,
        PIPELINE_DEPTH => LINE_WIDTH * (FILTER_KERNEL_SIZE - 1) + FILTER_KERNEL_SIZE,
        FILTER_DELAY => 2,
        IS_FLUSHDATA_CONSTANT => true,
        CONSTANT_DATA_VALUE => 128
    )
    port map(
        clk => clk,
        reset => reset_int,
        ready => ready_internal,
        flush_in => flush_in,

        input_strobe_in => strobe_in,
        input_data_in => data_in,
        input_stall_out => stall_out,
        flush_done_out => flush_complete,

        pipeline_strobe_out => strobe_int,
        pipeline_data_out => pipeline_data,
                
        result_data_in => filter_data,
                
        output_stall_in => stall_in,
        output_strobe_out => strobe_out,
        output_data_out => data_out
    );

    -- Instantiate data pipeline to provide filter window
    pipeline : entity as_window_buff_nxm
    generic map(
        DATA_WIDTH => DIN_WIDTH,
        WINDOW_X => FILTER_KERNEL_SIZE,
        WINDOW_Y => FILTER_KERNEL_SIZE,
        LINE_WIDTH => LINE_WIDTH,
        MINIMUM_LENGTH_FOR_BRAM => MINIMUM_BRAM_SIZE
    )
    port map(
        clk => clk,
        reset => reset_int,
        strobe => strobe_int,
        data_in => pipeline_data,
        data_out => open,
        window_out => window
    );

    -- Instantiate filter module and pass the kernel to it
    filter : entity as_2d_conv_filter_internal
    generic map(
        DIN_WIDTH => DIN_WIDTH,
        DOUT_WIDTH => DOUT_WIDTH,
        KERNEL_SIZE => FILTER_KERNEL_SIZE,
        KERNEL_TYPE => FILTER_KERNEL_TYPE,
        NORMALIZE_TO_HALF => NORMALIZE_OUTPUT,
        OUTPUT_SIGNED => OUTPUT_SIGNED
    )
    port map(
        clk => clk,
        reset => reset_int,
        strobe_in => strobe_int,
        window_in => window,
        data_out => filter_data
    );

    -- Internal reset signal (controllable via software as well)
    reset_int <= reset or reg_reset;
    vcomplete_out <= flush_complete;

end RTL;
