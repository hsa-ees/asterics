----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_edge
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
--! @file  as_edge.vhd
--! @brief Implements an edge filter.
----------------------------------------------------------------------------------


library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

library asterics;
use asterics.helpers.all;
use asterics.as_generic_filter.all;
use asterics.as_window_buff_nxm;
use asterics.as_generic_filter_module;
use asterics.as_pipeline_flush;

entity as_edge is
    generic (
        -- Width of the input and output data port
        DATA_WIDTH : integer := 8;
        LINE_WIDTH : integer := 640;
        MINIMUM_BRAM_SIZE : integer := 64;
        FILTER_KERNEL_SIZE : integer := 5;
        FILTER_KERNEL_TYPE : string := "laplace"
    );
    port (
        clk         : in  std_logic;
        reset       : in  std_logic;
        ready       : out std_logic;

        -- AsStream in ports
        vsync_in      : in  std_logic;
        vcomplete_in  : in  std_logic;
        hsync_in      : in  std_logic;
        hcomplete_in  : in  std_logic;
        strobe_in     : in  std_logic;
        data_in       : in  std_logic_vector(DATA_WIDTH - 1 downto 0);
        data_error_in : in  std_logic;
        sync_error_in : in  std_logic;
        stall_out     : out std_logic;

        -- AsStream out ports: Filtered
        vsync_out      : out std_logic;
        vcomplete_out  : out std_logic;
        hsync_out      : out std_logic;
        hcomplete_out  : out std_logic;
        strobe_out     : out std_logic;
        data_out       : out std_logic_vector(DATA_WIDTH - 1 downto 0);
        data_error_out : out std_logic;
        sync_error_out : out std_logic;
        stall_in       : in  std_logic;
        
        -- Debug output: Data directly from data pipeline's output 
        strobe_pipe_out     : out std_logic;
        data_pipe_out       : out std_logic_vector(DATA_WIDTH - 1 downto 0);
        stall_pipe_in       : in  std_logic;


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
end as_edge;

--! @}

architecture RTL of as_edge is

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
    

    -- Convert filter kernel to window data type:
    constant c_filter_port : t_generic_window(0 to FILTER_KERNEL_SIZE - 1, 0 to FILTER_KERNEL_SIZE - 1, DATA_WIDTH downto 0) := f_make_generic_window(FILTER_KERNEL_SIZE, FILTER_KERNEL_SIZE, select_edge_kernel(FILTER_KERNEL_SIZE, FILTER_KERNEL_TYPE), DATA_WIDTH + 1);

    -- Internal computation data width
    constant c_comp_data_width_add : integer := log2_ceil_zero(f_get_window_sum_abs(c_filter_port));
    
    -- Filter input window
    signal window : t_generic_window(0 to FILTER_KERNEL_SIZE - 1, 0 to FILTER_KERNEL_SIZE - 1, DATA_WIDTH - 1 downto 0);

    -- State and control signals
    signal flush_in : std_logic; -- Flush control reg
    signal flushing : std_logic; -- Flush state signal from component
    signal flush_ready : std_logic; -- Ready state from flush component
    signal flush_strobe : std_logic; -- Strobe from flush component
    signal ready_internal : std_logic; -- Internal ready signal
    signal output_off, output_off_flush : std_logic; -- Invalid data at output
    signal pipeline_data, flush_data, edge_data : std_logic_vector(DATA_WIDTH - 1 downto 0);
    signal reg_reset, reset_int : std_logic;
    signal strobe_int : std_logic; -- Internal strobe signal
    signal stall_int : std_logic;  -- Internal Stall signal
    signal reg_update_enable : std_logic; -- Enable signal for status register updates
    signal pipeline_empty, pipeline_empty_enable : std_logic; -- Status and enable signals for an empty data pipeline
    signal strobe_out_int : std_logic; -- Internal strobe signal for the data output
    signal status_reg_int : std_logic_vector(6 downto 0); -- Internal version of the status register; used to determine when an update is required (we can't continually update, that would override data from software!)
begin

    -- Check for valid filter width and type...
    assert ((FILTER_KERNEL_SIZE = 3) or (FILTER_KERNEL_SIZE = 5))
        report "Kernel size invalid! Must be one of: (3, 5)!"
        severity failure;
    assert ((FILTER_KERNEL_TYPE = "sobel_x") or (FILTER_KERNEL_TYPE = "sobel_y") or (FILTER_KERNEL_TYPE = "laplace"))
        report "Kernel type invalid! Must be one of: (sobel_x, sobel_y, laplace)!"
        severity failure;
    
    -- Register interface logic --
    
    -- Assign the register configuration to the register interface. 
    slv_reg_config <= slave_register_configuration;
    
    flush_in <= slv_ctrl_reg(0)(0);
    reg_reset <= slv_ctrl_reg(0)(1);
    slv_status_reg(0)(22 downto 16) <= status_reg_int;
    status_reg_int <= (0 => flush_ready,
                        1 => stall_in,
                        2 => output_off_flush,
                        3 => strobe_in,
                        4 => strobe_int,
                        5 => strobe_out_int,
                        6 => stall_int);
    slv_reg_modify(0) <= reg_update_enable;

    -- Update the status register
    reg_update : process(clk) is
    begin
        if rising_edge(clk) then
            if reset = '1' then
                slv_status_reg(0)(31 downto 23) <= (others => '0');
                slv_status_reg(0)(15 downto 0) <= (others => '0');
                reg_update_enable <= '1';
            else
                reg_update_enable <= '0';
                if flush_in = '1' and flushing = '1' then
                    slv_status_reg(0)(0) <= '0';
                    reg_update_enable <= '1';
                end if;
                if slv_ctrl_reg(0)(22 downto 16) /= status_reg_int then
                    reg_update_enable <= '1';
                end if;
            end if;
        end if;
    end process;

    -- Module logic --
    -- Instantiate flush control module
    flush_control : entity as_pipeline_flush
    generic map(
        DATA_WIDTH => DATA_WIDTH,
        LINE_WIDTH => LINE_WIDTH,
        WINDOW_X => FILTER_KERNEL_SIZE,
        WINDOW_Y => FILTER_KERNEL_SIZE,
        FILTER_DELAY => 1,
        IS_FLUSHDATA_CONSTANT => true,
        CONSTANT_FLUSHDATA => 128
    )
    port map(
        clk => clk,
        reset => reset_int,
        ready => flush_ready,
        
        strobe_in => strobe_in,
        flush_in => flush_in,
        pipeline_empty => pipeline_empty,
        flushing_out => flushing,
        output_off => output_off_flush,

        stall_in => stall_int,
        strobe_out => flush_strobe,
        data_out => flush_data
    );

    -- Instantiate data pipeline to provide filter window
    pipeline : entity as_window_buff_nxm
    generic map(
        DATA_WIDTH => DATA_WIDTH,
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
        data_out => data_pipe_out,
        window_out => window
    );

    -- Instantiate filter module and pass the kernel to it
    filter : entity as_generic_filter_module
    generic map(
        DIN_WIDTH => DATA_WIDTH,
        DOUT_WIDTH => DATA_WIDTH,
        WINDOW_X => FILTER_KERNEL_SIZE,
        WINDOW_Y => FILTER_KERNEL_SIZE,
        COMPUTATION_DATA_WIDTH_ADD => c_comp_data_width_add,
        NORMALIZE_TO_HALF => true
    )
    port map(
        clk => clk,
        reset => reset_int,
        filter_values => c_filter_port,
        strobe => strobe_int,
        flush_in => '0',
        flush_done => open,
        window => window,
        data_out => edge_data
    );

    -- Keep track of the pipeline flush state
    flush_state : process(clk) is
    begin
        if rising_edge(clk) then
            if reset = '1' then
                pipeline_empty <= '1';
                pipeline_empty_enable <= '0';
            else
                if output_off_flush = '1' then
                    pipeline_empty_enable <= '0';
                end if;
                if strobe_in = '1' and pipeline_empty = '1' then
                    pipeline_empty <= '0';
                    pipeline_empty_enable <= '1';
                end if;
            end if;
        end if;
    end process;
    
    -- Turn data output off while flushing or when pipeline is in an empty state
    output_off <= output_off_flush or pipeline_empty or pipeline_empty_enable;
    -- Pipeline data input: Use "real" data or flushing data
    pipeline_data <= flush_data when flushing = '1' else data_in;
    -- Data output
    data_out <= edge_data;

    -- Internal reset signal (controllable via software also)
    reset_int <= reset or reg_reset;
    -- Internal ready signal
    ready_internal <= not reset_int and not flushing;
    -- Ready signal output
    ready <= ready_internal;

    -- !! TODO - Synchronization and data state signals: Not delayed - TODO !! 
    vsync_out  <= vsync_in;
    vcomplete_out <= vcomplete_in;
    hsync_out  <= hsync_in;
    hcomplete_out <= hcomplete_in;
    sync_error_out <= sync_error_in;
    data_error_out <= data_error_in;

    -- Internal strobe output signal
    strobe_out_int <= '0' when output_off = '1' else strobe_int;
    -- Strobe output
    strobe_out <= strobe_out_int;
    -- Internal strobe input signal for data pipeline
    strobe_int <= strobe_in or flush_strobe;
    
    strobe_pipe_out <= '0' when output_off = '1' else strobe_int;

    -- Internal stall input signal
    stall_int <= stall_in or stall_pipe_in;
    -- Stall output signal
    stall_out <= stall_int or flushing;
    
        

end RTL;
