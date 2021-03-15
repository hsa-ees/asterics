----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework.
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:        as_pipeline_manager
--
-- Company:       Efficient Embedded Systems Group
--                University of Applied Sciences, Augsburg, Germany
--
-- Author:        Philip Manke
--
-- Description:   Implements a manager component for pipeline flushing, 
--                stride and stall behaviour management
--
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
--! @file  as_pipeline_manager.vhd
--! @brief Implements manager component for pipeline flushing, stride and stalling.
--! @addtogroup asterics_helpers
--! @{
--! @defgroup as_pipeline_manager as_pipeline_manager: 2D Window Pipeline Manager
--! Implements a manager component for pipeline flushing, 
--! stride and stall behaviour management.
--! @}
----------------------------------------------------------------------------------

--! @addtogroup as_pipeline_manager
--! @{


library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

library asterics;
use asterics.helpers.all;

entity as_pipeline_manager is
    generic (
        DIN_WIDTH : integer := 8;
        DOUT_WIDTH : integer := 8;
        PIPELINE_DEPTH : integer := 1281; -- Number of Pixels until the first valid result at the pipeline output
        IMAGE_WIDTH : integer := 640;
        IS_FLUSHDATA_CONSTANT : boolean := false;
        CONSTANT_DATA_VALUE : integer := 0;
        -- Set to false if pipeline modules have strobe outputs and strides are /= 1
        PIPELINE_SYNCHRONOUS : boolean := true;
        STRIDE_X : integer := 1;
        STRIDE_Y : integer := 1
    );
    port (
        clk   : in  std_logic;
        reset : in  std_logic;
        ready : out std_logic; -- Pipeline manager ready
        flush_in : in std_logic; -- pulse high to start flushing
        flush_done_out : out std_logic; -- High if pipeline empty: after flush complete or after reset
        
        input_strobe_in : in std_logic; -- Strobe input of pipeline
        input_data_in : in std_logic_vector(DIN_WIDTH - 1 downto 0); -- Pipeline input data
        input_hsync_in : in std_logic;
        input_vsync_in : in std_logic;
        input_stall_out : out std_logic;

        -- AND - bundled ready signal from all processing modules of the pipeline
        pipeline_strobe_out : out std_logic; -- Strobe for data pipeline 
        pipeline_data_out : out std_logic_vector(DIN_WIDTH - 1 downto 0); -- Data for pipeline
        pipeline_stall_in : in std_logic;
        
        result_data_in : in std_logic_vector(DOUT_WIDTH - 1 downto 0); -- Data from pipeline (filtered)
        result_strobe_in : in std_logic; 

        output_data_valid : out std_logic;
        output_stall_in : in std_logic; -- pipeline stall in signal
        output_strobe_out : out std_logic; -- Strobe for pipeline results
        output_hsync_out : out std_logic;
        output_vsync_out : out std_logic;
        output_data_out : out std_logic_vector(DOUT_WIDTH - 1 downto 0) -- Pipeline result data output
    );
end entity;

--! @}

architecture RTL of as_pipeline_manager is

    -- Number of pixels to flush to empty pipeline == Number of pixels to wait before valid data at output
    -- (- 1) as this module counts from 0
    constant c_flush_count : integer := PIPELINE_DEPTH + 1;
    -- Width of counter to count to c_flush_count
    constant c_counter_width : integer := log2_ceil(c_flush_count);
    constant c_counter_out_width : integer := log2_ceil(IMAGE_WIDTH);
    -- Unsigned value to compare data_counter to
    constant c_count_comp : unsigned := to_unsigned(c_flush_count, c_counter_width);
    -- Remainder when dividing flush count by image width.
    -- If data_counter MODULO image width reaches this value, 
    -- image width pixels have been flushed, thus hsync must be triggered
    constant c_flush_rem_comp : integer := c_flush_count rem IMAGE_WIDTH;

    -- Pipeline conditions
    signal pipeline_empty, pipeline_full : std_logic;
    -- Pipeline states
    signal is_flushing, is_filling, invalid_data_at_output: std_logic;
    -- Internal pipeline strobe signal (for data buffers and processing modules)
    signal pipeline_strobe_int : std_logic;
    -- Stride states and strobe enable signals
    signal stride_x_strobe, stride_y_strobe, stride_strobe_enable : std_logic;
    -- Stride counters
    signal stride_x_counter : std_logic_vector(STRIDE_X - 1 downto 0);
    signal stride_y_counter : std_logic_vector(STRIDE_Y - 1 downto 0);
    -- Pixel input and output counter
    signal data_counter : unsigned(c_counter_width - 1 downto 0) := (others => '0');
    -- Counter for correct handling of strides if the pipeline does not output in sync with the input
    signal data_counter_out : unsigned(c_counter_out_width - 1 downto 0) := (others => '0');
    -- Data signal for flush data input into pipeline
    signal flush_data : std_logic_vector(DIN_WIDTH - 1 downto 0);
    -- Internally generated hsync signal to correctly apply row-wise stride during flush process
    signal flush_hsync : std_logic;
    -- Buffer for data incase input_strobe_in goes to '1' while output_stall_in is '1'
    signal stall_buffer_data_regs : std_logic_vector(DIN_WIDTH - 1 downto 0);
    -- Buffer for hsync and vsync along with the stall_buffer_data_regs
    signal stall_buffer_ctrl_signal_regs : std_logic_vector(1 downto 0);
    -- Indicates that valid data is in the stall_buffer_data_regs
    signal stall_buffer_active : std_logic;
    -- Indicates that data is put into the pipeline from the stall_buffer_data_regs
    -- instead of input_data_in
    signal stall_buffer_output : std_logic;
    signal input_stall_out_int : std_logic;
    signal pipeline_strobe_inhibit : std_logic;
    signal pipeline_stall_out_int : std_logic;
begin

    -- Single register buffer for sudden stalling:
    -- When a stall signal is generated, sometimes the modules infront
    -- of the pipeline don't react fast enough and send another data word
    -- This buffer captures the data and feeds it to the pipeline 
    -- before releasing the stall signal.
    p_stall_buffer : process(clk) is
    begin
        if rising_edge(clk) then
            if reset = '1' then
                stall_buffer_ctrl_signal_regs <= (others => '0');
                stall_buffer_data_regs <= (others => '0');
                stall_buffer_active <= '0';
                stall_buffer_output <= '0';
            else
                if input_strobe_in = '1' and output_stall_in = '1' then
                    stall_buffer_active <= '1';
                    stall_buffer_data_regs <= input_data_in;
                    stall_buffer_ctrl_signal_regs <= input_hsync_in & input_vsync_in;
                elsif output_stall_in = '1' and stall_buffer_active = '1' then
                    stall_buffer_output <= '0';
                    stall_buffer_active <= '1';
                elsif output_stall_in = '0' and pipeline_stall_in = '0' and stall_buffer_active = '1' then
                    stall_buffer_output <= '1';
                    stall_buffer_active <= '0';
                end if;
                if stall_buffer_output = '1' and pipeline_strobe_int = '1' then
                    stall_buffer_output <= '0';
                end if;
            end if;
        end if;
    end process;


    output_vsync_out <= stall_buffer_ctrl_signal_regs(1) when stall_buffer_output = '1' else input_vsync_in;
    output_hsync_out <= stall_buffer_ctrl_signal_regs(0) and stride_y_strobe when stall_buffer_output = '1' else input_hsync_in and stride_y_strobe;

    -- Only apply flush_hsync during flush, while a strobe signal is active 
    -- and after a multiple of IMAGE WIDTH pixels have been flushed
    flush_hsync <= '1' when (pipeline_strobe_int = '1' and is_flushing = '1' 
                            and ((to_integer(data_counter) mod IMAGE_WIDTH) = c_flush_rem_comp))
                       else '0';

    
    -- Pipeline is empty after reset or after complete flush
    --pipeline_empty <= '1' when (data_counter = 0) else '0';


    -- Pipeline is full after 'c_flush_count' number of pixels (input_strobe_in) are inserted
    pipeline_full <= '1' when (data_counter = c_count_comp) else '0';
    -- While pipeline not full (i.e. during filling) data at output is invalid
    --invalid_data_at_output <= is_filling or (pipeline_empty and (not is_flushing));
    invalid_data_at_output <= not pipeline_full and not is_flushing;

    -- Internal pipeline strobe signal:
    -- Either strobe from external input or during flushing
    -- Inhibited by external stall or if pipeline processing modules report not ready
    pipeline_strobe_int <= 
        '1' when (input_strobe_in = '1' or is_flushing = '1' or stall_buffer_output = '1')
                and pipeline_strobe_inhibit = '0' and output_stall_in = '0'
                and (to_integer(data_counter) > 0 or is_flushing = '0') 
        else '0';

    -- Strobe signal to external (output):
    -- Source is internal pipeline strobe signal
    -- Inhibited by stride (reducing output resolution) 
    -- or if invalid (flushing / pipeline not full) data is at output
    output_strobe_out <= pipeline_strobe_int and (not invalid_data_at_output) and stride_strobe_enable;

    -- Output signal to control strobe signals of pipeline modules
    output_data_valid <= (not invalid_data_at_output) and stride_strobe_enable;

    -- Propagate stall signal
    input_stall_out_int <= output_stall_in or pipeline_stall_in or stall_buffer_active or stall_buffer_output;

    -- Pipeline strobe stall signal
    pipeline_stall_out_int <= output_stall_in or pipeline_stall_in or stall_buffer_active;

    input_stall_out <= input_stall_out_int;
    pipeline_strobe_inhibit <= pipeline_stall_out_int when rising_edge(clk);

    -- Report completed flush (pipeline_empty has no register stage => too quick
    --   goes low in same clk as data_counter reaches 0)
    flush_done_out <= pipeline_empty when rising_edge(clk);
    -- Report "ready" in initial state (empty / after reset) 
    -- or when fully operational (i.e. pipeline full ^= ready to be flushed)
    -- Register stage insertion for same reason as for flush_done_out
    ready <= pipeline_full or pipeline_empty when rising_edge(clk);

    pipeline_strobe_out <= pipeline_strobe_int;
    -- Mux for pipeline input data
    pipeline_data_out <= flush_data when is_flushing = '1' else stall_buffer_data_regs when stall_buffer_output = '1' else input_data_in;
    -- Pipeline manager has access to pipeline result data. Currently unused.
    -- (for future implementations of border management, etc.)
    output_data_out <= result_data_in; 

    -- Logic for strides: Use only every X column and every Y row of the image
    gen_stride_counters : if STRIDE_X > 1 or STRIDE_Y > 1 generate
        p_stride_state : process(clk) is
        begin
            if rising_edge(clk) then
                if reset = '1' then
                    -- Initialize so that after filling the pipeline, 
                    -- the first valid row and pixel are let through
                    stride_x_counter <= std_logic_vector(to_unsigned(2 ** ((PIPELINE_DEPTH rem IMAGE_WIDTH) mod STRIDE_X), STRIDE_X));
                    stride_y_counter <= std_logic_vector(to_unsigned(2 ** ((PIPELINE_DEPTH / IMAGE_WIDTH) mod STRIDE_Y), STRIDE_Y));
                    data_counter_out <= (others => '0');
                else
                    
                    if PIPELINE_SYNCHRONOUS then
                        if pipeline_strobe_int = '1' then
                            stride_x_counter <= rotate_right(stride_x_counter, 1);
                        end if;
                        if input_hsync_in = '1' or flush_hsync = '1' then
                            stride_y_counter <= rotate_right(stride_y_counter, 1);
                        end if;
                    else -- PIPELINE_SYNCHRONOUS = false
                        -- If the pipeline produces results at a different time
                        -- than the pipeline receives inputs,
                        -- we need to track the outputs seperately
                        if result_strobe_in = '1' and is_filling = '0' then
                            stride_x_counter <= rotate_right(stride_x_counter, 1);
                            data_counter_out <= data_counter_out + 1;
                        end if;
                        if data_counter_out = IMAGE_WIDTH then
                            data_counter_out <= (others => '0');
                            stride_y_counter <= rotate_right(stride_y_counter, 1);
                        end if;
                    end if;
                end if;
            end if;
        end process;
        
        -- Stride counters use "one-hot" encoding to enable simple shift implementation in HW
        -- If stride counters are in initial state (== 1) strobe output is enabled
        stride_y_strobe <= stride_y_counter(0);
        stride_x_strobe <= stride_x_counter(0);
        -- Strobe output is only enabled if both stride counters allow output (counter == 1)
        stride_strobe_enable <= stride_x_strobe and stride_y_strobe;
    end generate;

    -- Stride control logic can be disabled when both are 1 (all pixels valid)
    gen_no_stride : if STRIDE_X = 1 and STRIDE_Y = 1 generate
        stride_strobe_enable <= '1';
        stride_x_counter <= (others => '-');
        stride_y_counter <= (others => '-');
        data_counter_out <= (others => '-');
        stride_x_strobe <= '1';
        stride_y_strobe <= '1';
    end generate;

    p_pipe_empty : process(data_counter, reset, is_filling, is_flushing, data_counter_out) is
    begin
        if reset = '1' then
            pipeline_empty <= '1';
        else
            if is_filling = '1' or (is_flushing = '1' and PIPELINE_SYNCHRONOUS) then
                if to_integer(data_counter) = 0 then
                    pipeline_empty <= '1';
                else
                    pipeline_empty <= '0';
                end if;
            elsif PIPELINE_SYNCHRONOUS = false then
                if to_integer(data_counter_out) = 0 and to_integer(data_counter) = 0 then
                    pipeline_empty <= '1';
                else
                    pipeline_empty <= '0';
                end if;
            end if;
        end if;
    end process;

    -- Keep track of pipeline fill state signals
    p_flush_state : process(clk) is
    begin
        if rising_edge(clk) then
            if reset = '1' then
                is_flushing <= '0';
                is_filling <= '0';
            else
                -- Condition for flushing complete
                if is_flushing = '1' and pipeline_empty = '1' then
                    is_flushing <= '0';
                -- Condition for pipeline filling complete
                elsif is_filling = '1' and pipeline_full = '1' then
                    is_filling <= '0';
                -- Flushing process
                elsif flush_in = '1' or is_flushing = '1' then
                    -- Stays high during flush
                    is_flushing <= '1';
                    -- Interrupt filling process to keep a clean state
                    is_filling <= '0';
                -- Filling process
                elsif pipeline_empty = '1' or is_filling = '1' then
                    -- Stays high during filling
                    is_filling <= '1';
                end if;
            end if;
        end if;
    end process;

    -- Count pixels when filling / flushing pipeline
    p_pipeline_fill_state : process(clk) is
    begin
        if rising_edge(clk) then
            if reset = '1' then
                data_counter <= (others => '0');
            else
                if (pipeline_strobe_int = '1' and (PIPELINE_SYNCHRONOUS or is_flushing = '1')) 
                        or (result_strobe_in = '1' and PIPELINE_SYNCHRONOUS = false and is_flushing = '0') then
                    -- Process complete conditions take one clk => don't count!
                    if (is_flushing = '1' and pipeline_empty = '1') 
                        or (is_filling = '1' and pipeline_full = '1') then
                        data_counter <= data_counter;
                    -- Count during flushing process
                    elsif flush_in = '1' or is_flushing = '1' then
                        if to_integer(data_counter) > 0 then
                            -- Decrement data counter during flush
                            data_counter <= data_counter - 1;
                        end if;
                    -- Count during filling process
                    elsif pipeline_empty = '1' or is_filling = '1' then
                        -- Increment data counter during filling
                        data_counter <= data_counter + 1;
                    end if;
                end if;
            end if;
        end if;
    end process;

    -- Flush data output:
    counter_output_generate : if not IS_FLUSHDATA_CONSTANT generate
        -- output data_counter for flushing data
        data_output_big_counter : if flush_data'length <= c_counter_width generate
            flush_data <= std_logic_vector(data_counter(flush_data'range));
        end generate;
        data_output_small_counter : if flush_data'length > c_counter_width generate
            flush_data(data_counter'range) <= std_logic_vector(data_counter);
            flush_data(DIN_WIDTH - 1 downto data_counter'length) <= (others => '0');
        end generate;
    end generate;
    constant_output_generate : if IS_FLUSHDATA_CONSTANT generate
        flush_data <= std_logic_vector(to_unsigned(CONSTANT_DATA_VALUE, DIN_WIDTH));
    end generate;

end architecture;
