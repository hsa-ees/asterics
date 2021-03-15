----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework.
--  (C) 2021 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:        as_pipeline_manager
--
-- Company:       Efficient Embedded Systems Group
--                University of Applied Sciences, Augsburg, Germany
--
-- Author:        Philip Manke
--
-- Description:   Implements a component for pipeline flushing, 
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
            IMAGE_WIDTH : integer := 640;
            --! Number of Pixels until the first valid result at the pipeline output
            PIPELINE_DEPTH : integer := 1281;
            IS_FLUSHDATA_CONSTANT : boolean := false;
            CONSTANT_DATA_VALUE : integer := 0;
            --! Set to false if pipeline modules have strobe outputs and strides are /= 1
            PIPELINE_SYNCHRONOUS : boolean := true;
            --! Number of strobes the pipeline should be able to absorb while subsequent modules are stalling
            STALL_BUFFER_SIZE : integer := 1;
            STRIDE_X : integer := 1;
            STRIDE_Y : integer := 1
        );
        port (
            clk   : in  std_logic;
            reset : in  std_logic;
            
            ready : out std_logic; -- Pipeline manager ready
            flush_in : in std_logic; -- pulse high to start flushing
            flush_done_out : out std_logic; -- High if pipeline empty: after flush complete or after reset
            output_data_valid : out std_logic;
    
            sync_error : out std_logic;
            
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
    
            output_stall_in : in std_logic; -- pipeline stall in signal
            output_strobe_out : out std_logic; -- Strobe for pipeline results
            output_hsync_out : out std_logic;
            output_vsync_out : out std_logic;
            output_data_out : out std_logic_vector(DOUT_WIDTH - 1 downto 0) -- Pipeline result data output
        );
    end entity;
    
    --! @}
    
    architecture RTL of as_pipeline_manager is
    
        -- Width of strobe counters for flushing or sync signal generation
        constant c_counter_width : integer := log2_ceil(PIPELINE_DEPTH);
        -- Comparison value for flush counters
        constant c_count_comp : unsigned := to_unsigned(PIPELINE_DEPTH, c_counter_width);
    
        constant c_stride_x_counter_width : integer := log2_ceil(STRIDE_X);
        constant c_stride_y_counter_width : integer := log2_ceil(STRIDE_Y);
    
        constant c_hsync_gen_counter_comp : integer := IMAGE_WIDTH - 1;
        constant c_hsync_gen_counter_width : integer := log2_ceil(c_hsync_gen_counter_comp);
    
        constant c_stall_buffer_counter_width : integer := log2_ceil_zero(STALL_BUFFER_SIZE);
    
        -- ##### Stall buffer data types and registers #####
    
        type t_stall_buffer_data is array(0 to STALL_BUFFER_SIZE - 1) of std_logic_vector(DIN_WIDTH - 1 downto 0);
        type t_stall_buffer_sync_data is array(0 to STALL_BUFFER_SIZE - 1) of std_logic_vector(1 downto 0);
        signal stall_buffer_data_regs : t_stall_buffer_data;
        signal stall_buffer_sync_regs : t_stall_buffer_sync_data;
    
        -- ##### Stall buffer counters and signals #####
    
        signal stall_buffer_stored_count : unsigned(c_stall_buffer_counter_width downto 0);
        signal stall_buffer_providing : std_logic;
        signal stall_buffer_storing : std_logic;
        
        -- ##### Pipeline state pixel counters #####
    
        signal incoming_data_count : unsigned(c_counter_width - 1 downto 0);
        signal outgoing_data_count : unsigned(c_counter_width - 1 downto 0);
        signal pipeline_data_count : unsigned(c_counter_width - 1 downto 0);
    
        -- ##### Sync signal counters #####
    
        signal hsync_gen_counter : unsigned(c_hsync_gen_counter_width - 1 downto 0);
        signal vsync_gen_counter : unsigned(c_counter_width - 1 downto 0);
    
        -- ##### Control signals #####
    
        -- INPUT REALM
        
        signal input_strobe_in_int : std_logic;
        -- Generated stall signal
        signal input_stall_out_int : std_logic;
        signal input_hsync_in_int : std_logic;
        signal input_vsync_in_int : std_logic;
    
        -- PIPELINE REALM
    
        -- == pipeline_strobe_out
        signal pipeline_strobe_out_int : std_logic;
        signal pipeline_stall_in_int : std_logic;
    
        -- RESULT REALM
        -- Internal version of result_strobe_in
        signal result_strobe_in_int : std_logic;
    
        -- OUTPUT REALM
    
        -- == output_data_valid
        signal output_data_valid_int : std_logic;
        -- == output_strobe_out
        signal output_strobe_out_int : std_logic;
        -- Internally generated hsync
        signal output_hsync_out_int : std_logic;
        -- Internally generated vsync
        signal output_vsync_out_int : std_logic;
        -- Both stride machines are in state ss_valid
        signal stride_strobe_enable : std_logic;
    
        -- ##### Data signals #####
    
        signal generated_flush_data : std_logic_vector(DIN_WIDTH - 1 downto 0);
    
    
        -- ##### State machine types and signals #####
    
        type t_pipeline_state is (pls_empty, pls_filling, pls_full, pls_flushing);
        type t_stride_state is (ss_valid, ss_invalid);
        type t_stall_buffer_state is (sbs_empty, sbs_has_data, sbs_full);
    
        signal s_pipeline_state : t_pipeline_state;
        signal s_stride_x_state : t_stride_state;
        signal s_stride_y_state : t_stride_state;
        signal s_stall_buffer_state : t_stall_buffer_state;
    
    begin
        -- PIPELINE MANAGER:
        -- 
        -- INPUT REALM [ IN -> MNGR ] :
        --
        -- input_strobe_in  IN -> MNGR
        -- input_data_in    IN -> MNGR
        -- input_hsync_in   IN -> MNGR
        -- input_vsync_in   IN -> MNGR
        -- input_stall_out  IN <- MNGR
        --
        -- PIPELINE REALM [ MNGR -> PIPE ] :
        --
        -- pipeline_strobe_out    MNGR -> PIPE
        -- pipeline_data_out      MNGR -> PIPE
        -- pipeline_stall_in      MNGR <- PIPE
        --         
        -- RESULT REALM [ PIPE -> MNGR ] :
        --
        -- result_data_in    PIPE -> MNGR
        -- result_strobe_in  PIPE -> MNGR
        --
        -- OUTPUT REALM [ MNGR -> OUT ] :
        --
        -- output_data_valid      MNGR -> OUT
        -- output_strobe_out      MNGR -> OUT
        -- output_hsync_out       MNGR -> OUT
        -- output_vsync_out       MNGR -> OUT
        -- output_data_out        MNGR -> OUT
        -- output_stall_in        MNGR <- OUT
    
        -- ##### Output signals #####
        -- Registered
        p_registered_output : process(clk) is
        begin
            if rising_edge(clk) then
                if (s_pipeline_state = pls_full) or (s_pipeline_state = pls_empty) then
                    ready <= '1';
                else
                    ready <= '0';
                end if;
            end if;
        end process;
    
    
    
        -- Immediate
        input_stall_out <= input_stall_out_int;
        output_data_valid <= output_data_valid_int;
        output_strobe_out <= output_strobe_out_int and output_data_valid_int;
        output_hsync_out <= output_hsync_out_int;
        output_vsync_out <= output_vsync_out_int;
        output_data_out <= result_data_in;
        pipeline_strobe_out <= pipeline_strobe_out_int;
    
        -- ##### Internal signals #####
        p_internal_clocked_signals : process(clk) is
        begin
            if rising_edge(clk) then
                if reset = '1' then
                    input_strobe_in_int <= '0';
                    output_data_valid_int <= '0';
                else
                    input_strobe_in_int <= '0';
                    if input_strobe_in = '1' then
                        if PIPELINE_SYNCHRONOUS = true then
                            if output_stall_in = '0' then
                                input_strobe_in_int <= '1';
                            end if;
                        else
                            input_strobe_in_int <= '1';
                        end if;
                    end if;
                    if (s_pipeline_state = pls_full) or (s_pipeline_state = pls_flushing) then
                        output_data_valid_int <= '1';
                    else
                        output_data_valid_int <= '0';
                    end if;
                end if;
            end if;
        end process;
    
        input_hsync_in_int <= stall_buffer_sync_regs(0)(0) when stall_buffer_providing = '1'
                         else input_hsync_in;
        
        input_vsync_in_int <= stall_buffer_sync_regs(0)(1) when stall_buffer_providing = '1'
                         else input_vsync_in;
    
        input_stall_out_int 
            <= '1' when (
                output_stall_in = '1' 
                or pipeline_stall_in = '1'
                or s_stall_buffer_state /= sbs_empty 
                or s_pipeline_state = pls_flushing
            ) else '0';
    
    
        pipeline_strobe_out_int 
            <= '1' when (
                    pipeline_stall_in = '0' 
                    and (
                        output_stall_in = '0' 
                        or PIPELINE_SYNCHRONOUS = false
                    )
                     and (
                        input_strobe_in_int = '1'
                        or s_pipeline_state = pls_flushing
                        or stall_buffer_providing = '1'
                    )
                ) else '0';
    
        stride_strobe_enable 
            <= '1' when (
                s_stride_x_state = ss_valid
                and s_stride_y_state = ss_valid
                ) else '0';
    
        pipeline_stall_in_int <= pipeline_stall_in when PIPELINE_SYNCHRONOUS = false 
                            else pipeline_stall_in or output_stall_in;
    
        result_strobe_in_int <= pipeline_strobe_out_int when PIPELINE_SYNCHRONOUS = true
                                else result_strobe_in;
    
    
        output_strobe_out_int <= result_strobe_in_int and stride_strobe_enable;
    
    
        gen_constant_flush_data : if IS_FLUSHDATA_CONSTANT = true generate
            generated_flush_data <= std_logic_vector(to_unsigned(CONSTANT_DATA_VALUE, DIN_WIDTH));
        end generate;
        
        gen_flush_data : if IS_FLUSHDATA_CONSTANT = false generate
            p_flush_data : process(clk) is
            begin
                if rising_edge(clk) then
                    if reset = '1' then
                        generated_flush_data <= (others => '0');
                    else
                        if pipeline_strobe_out_int = '1' then
                            generated_flush_data <= std_logic_vector(unsigned(generated_flush_data) + 1);
                        end if;
                    end if;
                end if;
            end process;
        end generate;
    
    
        -- ##### State machines #####
    
        p_pipeline_state_machine : process(clk) is
        begin
            if rising_edge(clk) then
                if reset = '1' then
                    s_pipeline_state <= pls_empty;
                    incoming_data_count <= (others => '0');
                    pipeline_data_count <= (others => '0');
                    outgoing_data_count <= (others => '0');
                    flush_done_out <= '0';
                else
    
                    s_pipeline_state    <= s_pipeline_state; 
                    incoming_data_count <= incoming_data_count;
                    pipeline_data_count <= pipeline_data_count;
                    outgoing_data_count <= outgoing_data_count;
                    flush_done_out <= '0';
    
                    case s_pipeline_state is
    
                        -- The pipeline is empty
                        -- Move to pls_filling when we receive a valid data word
                        when pls_empty =>
                            if pipeline_strobe_out_int = '1' then
                                incoming_data_count <= incoming_data_count + 1;
                                s_pipeline_state <= pls_filling;
                            end if;
    
                        -- The pipeline has received some data is being filled
                        -- We increment incoming_data_count for each received data word
                        -- Move to pls_full, when the pipeline is full of valid data
                        -- or move to pls_flushing, when we receive a flush request (flush_in = '1')
                        when pls_filling => 
                            if to_integer(incoming_data_count) = (c_count_comp - 1)
                                    and pipeline_strobe_out_int = '1' then
                                incoming_data_count <= incoming_data_count + 1;
                                s_pipeline_state <= pls_full;
                            elsif pipeline_strobe_out_int = '1' then
                                incoming_data_count <= incoming_data_count + 1;
                            end if;
    
                            if flush_in = '1' then
                                pipeline_data_count <= (others => '0');
                                outgoing_data_count <= (others => '0');
                                s_pipeline_state <= pls_flushing;
                            end if;
    
                        -- The pipeline is full of valid data -> Valid result data is being output
                        -- We stay in this state, until a flush request is received,
                        -- then move to pls_flushing
                        when pls_full =>
                            if flush_in = '1' then
                                pipeline_data_count <= (others => '0');
                                outgoing_data_count <= (others => '0');
                                s_pipeline_state <= pls_flushing;
                            end if;
    
                        -- The pipeline is being flushed -> We deliberately insert invalid data
                        -- so that remaining valid data is "pushed" through the pipeline.
                        -- Move to pls_empty after all valid data words are output
                        when pls_flushing =>
                        
                            if to_integer(pipeline_data_count) < (c_count_comp)
                                    and pipeline_strobe_out_int = '1' then
                                pipeline_data_count <= pipeline_data_count + 1;
                            end if;
                            if to_integer(outgoing_data_count) < (c_count_comp)
                                    and result_strobe_in_int = '1' then
                                outgoing_data_count <= outgoing_data_count + 1;
                            end if;
    
                            if pipeline_data_count = (c_count_comp) 
                                    and outgoing_data_count = (c_count_comp) then
                                s_pipeline_state <= pls_empty;
                                flush_done_out <= '1';
                            end if;
                    end case;
                end if;
            end if;
        end process;
    
        gen_stall_buffers : if STALL_BUFFER_SIZE > 0 generate
    
        p_stall_buffer_state_machine : process(clk) is
            variable v_stall_buffer_providing : std_logic;
            variable v_stall_buffer_storing : std_logic;
        begin
            if rising_edge(clk) then
                if reset = '1' or flush_in = '1' then
                    s_stall_buffer_state <= sbs_empty;
                    stall_buffer_data_regs <= (others => (others => '0'));
                    stall_buffer_sync_regs <= (others => (others => '0'));
                    stall_buffer_stored_count <= (others => '0');
                    stall_buffer_providing <= '0';
                    v_stall_buffer_providing := '0';
                    v_stall_buffer_storing := '0';
                    sync_error <= '0';
                else
                    s_stall_buffer_state <= s_stall_buffer_state;
                    stall_buffer_data_regs <= stall_buffer_data_regs;
                    stall_buffer_sync_regs <= stall_buffer_sync_regs;
                    stall_buffer_stored_count <= stall_buffer_stored_count;
                    stall_buffer_providing <= '0';
                    v_stall_buffer_providing := '0';
                    v_stall_buffer_storing := '0';
                    sync_error <= '0';
    
                    case s_stall_buffer_state is
    
                        -- The stall buffer is empty
                        -- Stores a data word if a strobe is received while we are sending a stall signal
                        -- Then move to either sbs_full, if STALL_BUFFER_SIZE == 1 else sbs_has_data
                        when sbs_empty =>
                            if pipeline_stall_in_int = '1' and input_strobe_in = '1' then
                                v_stall_buffer_storing := '1';
    
                                if STALL_BUFFER_SIZE = 1 then
                                    s_stall_buffer_state <= sbs_full;
                                else
                                    s_stall_buffer_state <= sbs_has_data;
                                end if;
                            end if;
    
                        -- There is some data in the stall buffer
                        -- 4 situations can occur:
                        --    - New data is stored: Can lead to state sbs_full
                        --    - The oldest data is send to the pipeline: Can lead to sbs_empty
                        --    - New data is stored and the oldest data is send to the pipeline: State is preserved
                        --    - Nothing can happen: State is preserved
                        when sbs_has_data => 
                            -- Behaviour for: New data arriving and pipeline can accept data
                            if pipeline_stall_in_int = '0' and input_strobe_in = '1' then
                                v_stall_buffer_providing := '1';
                                v_stall_buffer_storing := '1';
                                
                                -- Stored data count doesn't change; state doesn't change
    
                            -- Behaviour for: New data arriving and pipeline cannot accept data
                            elsif pipeline_stall_in_int = '1' and input_strobe_in = '1' then
                                v_stall_buffer_storing := '1';
                                
                                -- Move to sbs_full if buffer is full
                                if to_integer(stall_buffer_stored_count) + 1 = STALL_BUFFER_SIZE then
                                    s_stall_buffer_state <= sbs_full;
                                end if;
                            
                            -- Behaviour for: No new data arriving and pipeline can accept data
                            elsif pipeline_stall_in_int = '0' and input_strobe_in = '0' then
                                v_stall_buffer_providing := '1';
    
                                -- Move to sbs_empty if this was the last stored data
                                if to_integer(stall_buffer_stored_count) - 1 = 0 then
                                    s_stall_buffer_state <= sbs_empty;
                                end if;
    
                            end if;
    
                        -- The stall buffer is full
                        when sbs_full => 
                            -- Behaviour for: New data arriving
                            if input_strobe_in = '1' then
                                -- If we cannot output while the buffer is full, raise a sync_error!
                                if pipeline_stall_in_int = '1' then
                                    sync_error <= '1';
                                else   -- Output data from buffer ...
                                    v_stall_buffer_providing := '1';
                                    v_stall_buffer_storing := '1';
                                end if;
    
                            -- Behaviour for: No new data, output data to pipeline
                            elsif pipeline_stall_in_int = '0' and input_strobe_in = '0' then
                                v_stall_buffer_providing := '1';
    
                                -- Move to sbs_empty if this buffer has only one slot, else sbs_has_data
                                if STALL_BUFFER_SIZE = 1 then
                                    s_stall_buffer_state <= sbs_empty;
                                else
                                    s_stall_buffer_state <= sbs_has_data;
                                end if;
                            end if;
    
                    end case;
    
                    stall_buffer_providing <= v_stall_buffer_providing;
                    
                    -- Data buffer management
                    if v_stall_buffer_providing = '1' and v_stall_buffer_storing = '1' then
                        -- Shift buffer registers for output
                        if STALL_BUFFER_SIZE > 1 then
                            for N in 0 to STALL_BUFFER_SIZE - 2 loop
                                stall_buffer_data_regs(N) <= stall_buffer_data_regs(N + 1);
                                stall_buffer_sync_regs(N) <= stall_buffer_sync_regs(N + 1);
                            end loop;
                        end if;
    
                        -- ... and store incoming data in buffer
                        stall_buffer_data_regs(to_integer(stall_buffer_stored_count) - 1)
                            <= input_data_in;
                        stall_buffer_sync_regs(to_integer(stall_buffer_stored_count) - 1)
                            <= input_hsync_in & input_vsync_in;
    
                    elsif v_stall_buffer_providing = '1' then
                        -- Output and decrement stored data counter
                        stall_buffer_stored_count <= stall_buffer_stored_count - 1;
    
                        -- Shift buffer registers for output
                        if STALL_BUFFER_SIZE > 1 then
                            for N in 0 to STALL_BUFFER_SIZE - 2 loop
                                stall_buffer_data_regs(N) <= stall_buffer_data_regs(N + 1);
                                stall_buffer_sync_regs(N) <= stall_buffer_sync_regs(N + 1);
                            end loop;
                        end if;
    
                    elsif v_stall_buffer_storing = '1' then
                        -- Store new data, increment stored data count
                        stall_buffer_stored_count <= stall_buffer_stored_count + 1;
                        stall_buffer_data_regs(to_integer(stall_buffer_stored_count))
                            <= input_data_in;
                        stall_buffer_sync_regs(to_integer(stall_buffer_stored_count))(0)
                            <= input_hsync_in;
                        stall_buffer_sync_regs(to_integer(stall_buffer_stored_count))(1)
                            <= input_vsync_in;
                    end if;
    
                    -- Pipeline data output:
                    if v_stall_buffer_providing = '1' then
                        pipeline_data_out <= stall_buffer_data_regs(0);
                    elsif s_pipeline_state = pls_flushing then
                        pipeline_data_out <=  generated_flush_data;
                    else
                        pipeline_data_out <= input_data_in;
                    end if;
    
                end if;
            end if;
        end process;
        end generate gen_stall_buffers;
    
        gen_no_stall_buffers : if STALL_BUFFER_SIZE = 0 generate
            s_stall_buffer_state <= sbs_full;
            stall_buffer_data_regs <= (others => (others => '0'));
            stall_buffer_sync_regs <= (others => (others => '0'));
            stall_buffer_stored_count <= (others => '0');
            stall_buffer_providing <= '0';
            p_generate_sync_error : process(clk) is
            begin
                if rising_edge(clk) then
                    if reset = '1' then
                        sync_error <= '0';
                    else
                        if pipeline_stall_in = '1' and input_strobe_in = '1' then
                            sync_error <= '1';
                        else
                            sync_error <= '0';
                        end if;
                    end if;
                end if;
            end process;
        end generate gen_no_stall_buffers;
    
    
        gen_stride_machine : if STRIDE_X > 1 and STRIDE_Y > 1 generate
    
        p_stride_state_machine : process(clk) is
            variable v_stride_x_count : unsigned(c_stride_x_counter_width - 1 downto 0);
            variable v_stride_y_count : unsigned(c_stride_y_counter_width - 1 downto 0);
        begin
            if rising_edge(clk) then
                if reset = '1' then
                    s_stride_x_state <= ss_invalid;
                    s_stride_y_state <= ss_invalid;
                    v_stride_x_count := (others => '0');
                    v_stride_y_count := (others => '0');
                else
                    -- Horizontal stride generation (X)
                    case s_stride_x_state is
    
                        -- Let a single pixel through
                        -- Move to ss_invalid
                        when ss_valid =>
                            if result_strobe_in_int = '1' and output_data_valid_int = '1' then
                                v_stride_x_count := (others => '0');
                                s_stride_x_state <= ss_invalid;
                            end if;
    
                        -- Block STRIDE_X - 1 pixels
                        -- After that, move to ss_valid
                        when ss_invalid => 
                            if result_strobe_in_int = '1' and output_data_valid_int = '1' then
                                v_stride_x_count := v_stride_x_count + 1;
                                if to_integer(v_stride_x_count) = (STRIDE_X - 1) then
                                    s_stride_x_state <= ss_valid;
                                end if;
                            end if;
                    
                    end case;
                    
                    case s_stride_y_state is
    
                        -- Let a single row of pixels through
                        -- Move to ss_invalid after one row of pixels
                        when ss_valid => 
                            if output_hsync_out_int = '1' then
                                v_stride_y_count := (others => '0');
                                s_stride_y_state <= ss_invalid;
                            end if;
    
                        -- Block STRIDE_Y - 1 rows of pixels
                        -- After that, move to ss_valid
                        when ss_invalid => 
                            if output_hsync_out_int = '1' then
                                v_stride_y_count := v_stride_y_count + 1;
                                if to_integer(v_stride_y_count) = (STRIDE_Y - 1) then
                                    s_stride_y_state <= ss_valid;
                                end if;
                            end if;
    
                    end case;
    
                end if;
            end if;
        end process;
    
        end generate gen_stride_machine;
    
        gen_stride_static : if STRIDE_X = 1 and STRIDE_Y = 1 generate
            s_stride_x_state <= ss_valid;
            s_stride_y_state <= ss_valid;
        end generate gen_stride_static;
    
    
        p_sync_signal_generator : process(clk) is
        begin
            if rising_edge(clk) then
                if reset = '1' then
                    hsync_gen_counter <= (others => '0');
                    vsync_gen_counter <= (others => '0');
                    output_hsync_out_int <= '0';
                    output_vsync_out_int <= '0';
                else
                    -- Reset generated sync signals
                    output_hsync_out_int <= '0';
                    output_vsync_out_int <= '0';
                    
                    -- On send pixel
                    if result_strobe_in_int = '1' and output_data_valid_int = '1' then
    
                        -- Only generate when output data is valid
                        if output_data_valid_int = '1' then
                            -- hsync generation: If counter is zero, generate an hsync
                            if to_integer(hsync_gen_counter) = 0 then
                                output_hsync_out_int <= '1';
                            end if;
                            -- Reset counter when it reaches comparison value, else count
                            if to_integer(hsync_gen_counter) = c_hsync_gen_counter_comp then
                                hsync_gen_counter <= (others => '0');
                            else
                                hsync_gen_counter <= hsync_gen_counter + 1;
                            end if;
                        end if;
    
                        -- vsync generation: Start when we receive a vsync on input
                        if input_vsync_in = '1' then
                            -- Start counting: Set counter to 1
                            vsync_gen_counter <= to_unsigned(1, c_counter_width);
                        -- If the counter is not zero (idle state)
                        elsif to_integer(vsync_gen_counter) > 0 then
                            -- When counter reaches comparison value (pipeline depth):
                            -- Generate a vsync and reset to idle state else count
                            if to_integer(vsync_gen_counter) = c_count_comp - 1 then
                                output_vsync_out_int <= '1';
                                vsync_gen_counter <= (others => '0');
                            else
                                vsync_gen_counter <= vsync_gen_counter + 1;
                            end if;
                        end if;
                    end if;
                end if;
            end if;
        end process;
    
    end architecture;
    