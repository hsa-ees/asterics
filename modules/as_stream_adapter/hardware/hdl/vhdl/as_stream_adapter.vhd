----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_stream_adapter
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Philip Manke
--
-- Modified:       
--
-- Description:    This module modifies the width of the data signal of an as_stream.
--                 The resource efficiency is based on the least common multiple
--                 of the data width values.
--                 Limitation: Will stall when the internal buffer is full until it is emptied.
--                             For lowering the data width severely, consider using as_disperse.
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
--! @file  as_stream_adapter.vhd
--! @brief Modify AsStream data width.
--! @addtogroup asterics_modules
--! @{
--! @defgroup as_stream_adapter as_stream_adapter: AsStream Data Width Adapter
--! This module modifies the width of the data signal of an as_stream.
--! The resource efficiency is based on the least common multiple
--! of the data width values.
--! Limitation: Will stall when the internal buffer is full until it is emptied.
--!             For lowering the data width severely, consider using as_disperse.
--! @}
----------------------------------------------------------------------------------

--! @addtogroup as_stream_adapter
--! @{


    library ieee;
    use ieee.std_logic_1164.all;
    use IEEE.numeric_std.all;
    use IEEE.math_real.all;
    
    library asterics;
    use asterics.helpers.all;
    
    
    entity as_stream_adapter is
        generic(
            DIN_WIDTH : integer := 32;
            DOUT_WIDTH : integer := 24;
            FLIP_OUTPUT_DATA : boolean := false;
            --! PIXEL_BITWIDTH is only relevant when FLIP_OUTPUT_DATA is active
            PIXEL_BITWIDTH : integer := 0;
            -- Adds strobe counters for strobe_in and strobe_out to this module. Readable via software.
            GENERATE_STROBE_COUNTERS : boolean := false
        );
        port (
            clk : in std_logic;
            reset : in std_logic;
    
            sync_error : out std_logic;
    
            --! AsStream in ports
            strobe_in    : in std_logic;
            data_in      : in  std_logic_vector(DIN_WIDTH - 1 downto 0);
            hsync_in     : in  std_logic;
            vsync_in     : in  std_logic;
            stall_in     : out std_logic;
    
            --! AsStream out ports:
            strobe_out : out std_logic;
            data_out   : out std_logic_vector(DOUT_WIDTH - 1 downto 0);
            hsync_out  : out std_logic;
            vsync_out  : out std_logic;
            stall_out  : in  std_logic;
    
            --! Slave register interface
            --! This module uses a status register @ offset 0 and a control register @ offset 1
            --! If GENERATE_STROBE_COUNTERS is set to true, two more status registers are generated @ 2 and 3 
            slv_ctrl_reg : in slv_reg_data(0 to 3);
            slv_status_reg : out slv_reg_data(0 to 3);
            slv_reg_modify : out std_logic_vector(0 to 3);
            slv_reg_config : out slv_reg_config_table(0 to 3)
        );
    end as_stream_adapter;
    
    --! @}
    
    architecture RTL of as_stream_adapter is
    
        -- Slave register configuration:
        -- Allows for "dynamic" configuration of slave registers
        -- Possible values and what they mean: 
        -- "00", AS_REG_NONE:    Register "off". Register will not be available and won't be implemented -> No hardware resource utilization.
        -- "01", AS_REG_STATUS:  From HW view: Status register. Data transport from hardware to software. HW can only write, SW can only read.
        -- "10", AS_REG_CONTROL: From HW view: Control register. Data transport from software to hardware. HW can only read, SW can only write.
        -- "11", AS_REG_BOTH:    Combined Read/Write register. Data transport in both directions. 
        --       When both sides attempt to write simultaniously, only the HW gets to write.
        --       These registers use both the slv_ctrl_reg and slv_status_reg ports for communication.
        constant slave_register_configuration : slv_reg_config_table(0 to 3) := (AS_REG_STATUS, AS_REG_CONTROL, AS_REG_STATUS, AS_REG_STATUS);
    
        --! Buffer size is determined by the least common multiple 
        --! between both data widths (input and output)
        --! This allows this design to operate entirely without shifting or moving data
        constant c_buffer_width : integer := f_least_common_multiple(DIN_WIDTH, DOUT_WIDTH);
        --! Width of buffer index registers
        constant c_idx_width : integer := log2_ceil(c_buffer_width);
        --! Ensure that an invalid value exists to "disable" sync signal output
        constant c_idx_sync_width : integer := log2_ceil(c_buffer_width + 1);
        constant c_sync_off : integer := c_buffer_width + 1;
    
        --! Buffer for all incoming data
        signal data_buffer : std_logic_vector(c_buffer_width - 1 downto 0);
        --! Reference / Pointer to the starting position of where in the buffer the next incoming data will be stored
        signal in_buf_idx : unsigned(c_idx_width - 1 downto 0) := (others => '0');
        --! Reference / Pointer to the ending position of where from the buffer the next outgoing data will be accessed
        signal out_buf_idx : unsigned(c_idx_width - 1 downto 0) := (others => '0');
        --! Is the buffer full?
        signal buff_full_int, buff_full, buff_full_reg : std_logic;
        --! Input buffer indexes of when a sync signal was received (hsync, vsync)
        --! Default value is the buffer size + 1 (not valid as an index value)
        signal hsync_buf_idx, vsync_buf_idx : unsigned(c_idx_sync_width - 1 downto 0);
        --! Internal strobe_out signal
        signal strobe_out_int : std_logic;
        signal sw_reset : std_logic;
        signal reset_int : std_logic;
        signal buff_empty : std_logic;
        signal buff_empty_int : std_logic;
        signal strobe_counter_reset : std_logic;
        signal strobe_in_counter, strobe_out_counter : unsigned(31 downto 0);
    
        signal stall_in_int : std_logic;
        signal data_out_int : std_logic_vector(DOUT_WIDTH - 1 downto 0);
    
        type t_operation_mode is (opmode_collect, opmode_passthrough, opmode_disperse);
    
        type t_stall_buffer_state is (sbs_empty, sbs_full);
        signal s_stall_buffer_state : t_stall_buffer_state;
        signal stall_buffer_data_reg : std_logic_vector(DIN_WIDTH - 1 downto 0);
        signal stall_buffer_sync_reg : std_logic_vector(1 downto 0);
        signal stall_buffer_providing : std_logic;
    
        function f_assign_opmode(in_width : in integer; out_width : in integer) return t_operation_mode is
        begin
            if in_width = out_width then
                return opmode_passthrough;
            elsif in_width < out_width then 
                return opmode_collect;
            else
                return opmode_disperse;
            end if;
        end function;
    
        constant c_opmode : t_operation_mode := f_assign_opmode(DIN_WIDTH, DOUT_WIDTH);
    
        function f_assign_pixelwidth(out_width : in integer; pwidth : in integer) return integer is
        begin
            if pwidth = 0 then
                return out_width;
            else
                return pwidth;
            end if;
        end function;
    
        constant c_pixel_bitwidth : integer := f_assign_pixelwidth(DOUT_WIDTH, PIXEL_BITWIDTH);
    
        -- Register config:
        -- Reg 0: Status register
        -- Bit 0: buffer full; Stall is set to high while buffer is full
        -- Bit 1: buffer empty; No more strobes will be send when buffer is empty
        -- Bit 2 .. 6: Unused
        -- Bit 7: Is '1' if strobe counters are included else '0'
        -- Bit 8 ..31: Total configured buffer size; unsigned integer; constant; To double check buffer size
    
        -- Reg 1: Control register
        -- Bit 0: Reset module; Clears buffer and strobe registers (if enabled)
        -- Bit 1: Reset strobe counters if enabled
        -- Bit 2 .. 31: Unused
    
        -- Reg 2: Status register if GENERATE_STROBE_COUNTERS == true
        -- Bit 0 .. 31: Number of input strobes received since last counter reset
    
        -- Reg 3: Status register if GENERATE_STROBE_COUNTERS == true
        -- Bit 0 .. 31: Number of output strobes generated since last counter reset
    
    begin
    
    
        slv_reg_config <= slave_register_configuration;
        slv_reg_modify(0) <= '1';
        slv_reg_modify(1) <= '0';
        slv_status_reg(0)(0) <= buff_full;
        slv_status_reg(0)(1) <= buff_empty;
        slv_status_reg(0)(6 downto 2) <= (others => '0');
        slv_status_reg(0)(31 downto 8) <= std_logic_vector(to_unsigned(c_buffer_width, 24));
    
        sw_reset <= slv_ctrl_reg(1)(0);
        strobe_counter_reset <= slv_ctrl_reg(0)(1);
    
        slv_status_reg(1) <= (others => '-');
     
        -- Count strobes if configured
        gen_no_strobe_counters : if GENERATE_STROBE_COUNTERS = false generate
            slv_reg_modify(2 to 3) <= (others => '-');
            slv_status_reg(2 to 3) <= (others => (others => '-'));
            slv_status_reg(0)(7) <= '0';
        end generate;
    
        gen_strobe_counters : if GENERATE_STROBE_COUNTERS = true generate
            slv_status_reg(0)(7) <= '1';
            slv_reg_modify(2 to 3) <= (others => '1');
            slv_status_reg(2) <= std_logic_vector(strobe_in_counter);
            slv_status_reg(3) <= std_logic_vector(strobe_out_counter);
    
            -- Strobe counting process
            p_count_strobes : process(clk) is
            begin
                if rising_edge(clk) then
                    if reset_int = '1' or strobe_counter_reset = '1' then
                        strobe_in_counter <= (others => '0');
                        strobe_out_counter <= (others => '0');
                    else
                        if strobe_in = '1' then
                            strobe_in_counter <= strobe_in_counter + 1;
                        end if;
                        if strobe_out_int = '1' then
                            strobe_out_counter <= strobe_out_counter + 1;
                        end if;
                    end if;
                end if;
            end process;
        end generate;
    
        reset_int <= sw_reset or reset;
    
        strobe_out <= strobe_out_int;
    
        stall_in <= '1' when (
                stall_in_int = '1'
                or s_stall_buffer_state = sbs_full
                or stall_buffer_providing = '1'
            ) else '0';
    
    
        gen_passthrough_mode : if c_opmode = opmode_passthrough generate
            stall_in_int <= stall_out;
            buff_full <= strobe_in;
            buff_empty <= not strobe_in;
            s_stall_buffer_state <= sbs_empty;
            stall_buffer_providing <= '0';
    
            p_buffer : process(clk) is
            begin
                if rising_edge(clk) then
                    if reset_int = '1' then
                        data_out_int <= (others => '0');
                        strobe_out_int <= '0';
                        hsync_out <= '0';
                        vsync_out <= '0';
                    else
                        if strobe_in = '1' and stall_out = '0' then
                            strobe_out_int <= strobe_in;
                            data_out_int <= data_in;
                            hsync_out <= hsync_in;
                            vsync_out <= vsync_in;
                        end if;
                    end if;
                end if;
            end process;
        end generate;
    
        gen_flipped_data : if FLIP_OUTPUT_DATA = true generate
            p_flip_data : process(data_out_int) is
                constant c_pixelcount : integer := DOUT_WIDTH / c_pixel_bitwidth;
            begin
                if (c_opmode = opmode_collect and (DOUT_WIDTH mod c_pixel_bitwidth) = 0)
                    or c_opmode = opmode_passthrough then
                    
                    for N in 0 to c_pixelcount - 1 loop
                        data_out((N + 1) * c_pixel_bitwidth - 1 downto N * c_pixel_bitwidth)
                            <= data_out_int((DOUT_WIDTH - (N * c_pixel_bitwidth)) - 1 downto DOUT_WIDTH - ((N + 1) * c_pixel_bitwidth));
                    end loop;
                else
                    data_out <= data_out_int;
                end if;
            end process;
        end generate;
    
        gen_unflipped_data : if FLIP_OUTPUT_DATA = false generate
            data_out <= data_out_int;
        end generate;
    
    
        gen_collect_disperse_mode : if c_opmode /= opmode_passthrough generate
            -- Stall if previous modules call for it and the buffer is full
            stall_in_int <= (stall_out or buff_full_reg) and (not buff_empty_int);
    
            buff_empty_int <= '1' when (to_integer(in_buf_idx) = 0) and (to_integer(out_buf_idx) = 0) else '0';
            buff_empty <= '1' when buff_empty_int = '1' and (buff_full = '0') else '0';
            
            -- Buffer is full if 'in buffer idx' rolls over
            -- Goes high in the strobe cycle that fills the buffer to help prevent overflows
            --gen_buf_full_int_disparate : if DIN_WIDTH /= DOUT_WIDTH generate
            buff_full_int <= '1' when (
                    strobe_in = '1'
                    and (to_integer(in_buf_idx) + DIN_WIDTH) >= c_buffer_width
                ) else '0';
            --end generate;
            --gen_buf_full_int_passthrough : if DIN_WIDTH = DOUT_WIDTH generate
            --    buff_full_int <= '0';
            --end generate;
    
    
    
            -- Keep buff_full state until it is empty registered
            --p_buff_state : process(clk) is
            --begin
            --    if rising_edge(clk) then
            --        if reset_int = '1' then
            --            buff_full <= '0';
            --        else
            --            if (buff_full_int = '1') or (buff_full_reg = '1') 
            --                    or ((to_integer(in_buf_idx) = 0) and (to_integer(out_buf_idx) > 0)) then 
            --                buff_full <= '1';
            --            
            --            elsif (strobe_out_int = '1') and (stall_out = '0')
            --                    and (to_integer(out_buf_idx) mod c_buffer_width) = 0 then
            --                buff_full <= buff_full_int;
            --            else
            --                buff_full <= '0';
            --            end if;
            --        end if;
            --    end if;
            --end process;
    
            -- Keep buff_full state until it is empty
            p_buff_state : process(reset_int, buff_full_reg, buff_full_int, in_buf_idx, out_buf_idx, strobe_out_int, stall_out) is
            begin
                if reset_int = '1' then
                    buff_full <= '0';
                else
                    if (buff_full_int = '1')
                            or ((to_integer(in_buf_idx) = 0) and (to_integer(out_buf_idx) > 0)) then 
                        buff_full <= '1';
                    
                    elsif (strobe_out_int = '1') and (stall_out = '0')
                            and (to_integer(out_buf_idx) mod c_buffer_width) = 0 then
                        buff_full <= buff_full_int;
                    else
                        buff_full <= '0';
                    end if;
                end if;
            end process;
    
            -- Remember that the buffer was filled if we receive a strobe_in while stall_out is high
            p_buff_reg_state : process(clk) is
                --variable v_buf_full_last_cycle : std_logic;
            begin
                if rising_edge(clk) then
                    if reset_int = '1' then
                        buff_full_reg <= '0';
                        --v_buf_full_last_cycle := '0';
                    else
                        buff_full_reg <= buff_full;
                        --if v_buf_full_last_cycle = '1' and buff_full = '1' then
                        --if buff_full_reg = '1' and strobe_out_int = '1' then
                        --    buff_full_reg <= '0';
                        --elsif buff_full = '1' then
                        --    buff_full_reg <= '1';
                        --end if;
    
                        --if buff_full = '1' then
                        --    v_buf_full_last_cycle := '1';
                        --else
                        --    v_buf_full_last_cycle := '0';
                        --end if;
                    end if;
                end if;
            end process;
    
            -- Remember that the buffer was filled if we receive a strobe_in while stall_out is high
            --p_buff_reg_state : process(clk) is
            --begin
            --    if rising_edge(clk) then
            --        if reset_int = '1' then
            --            buff_full_reg <= '0';
            --        else
            --            if buff_full_int = '1' and stall_out = '1' then
            --                buff_full_reg <= '1';
            --            elsif strobe_out_int = '1' then
            --                buff_full_reg <= '0';
            --            end if;
            --        end if;
            --    end if;
            --end process;
    
    
            p_buffer_io : process(clk) is
                variable next_in_buf_idx : integer;
                variable next_out_buf_idx : integer;
                variable v_load_data : std_logic_vector(DIN_WIDTH - 1 downto 0);
    
                variable v_stall_buffer_providing : std_logic;
                variable v_stall_buffer_storing : std_logic;
            begin
                if rising_edge(clk) then
                    if reset_int = '1' then
                        data_buffer <= (others => '0');
                        in_buf_idx <= (others => '0');
                        out_buf_idx <= (others => '0');
                        hsync_buf_idx <= to_unsigned(c_sync_off, c_idx_sync_width);
                        vsync_buf_idx <= to_unsigned(c_sync_off, c_idx_sync_width);
                        
                        s_stall_buffer_state <= sbs_empty;
                        stall_buffer_data_reg <= (others => '0');
                        stall_buffer_sync_reg <= (others => '0');
                        v_stall_buffer_providing := '0';
                        v_stall_buffer_storing := '0';
                        sync_error <= '0';
                    else
    
                        s_stall_buffer_state <= s_stall_buffer_state;
                        stall_buffer_data_reg <= stall_buffer_data_reg;
                        stall_buffer_sync_reg <= stall_buffer_sync_reg;
                        v_stall_buffer_providing := '0';
                        v_stall_buffer_storing := '0';
                        sync_error <= '0';
    
                        case s_stall_buffer_state is
        
                            -- The stall buffer is empty
                            -- Stores a data word if a strobe is received while we are sending a stall signal
                            -- Then move to either sbs_full, if STALL_BUFFER_SIZE == 1 else sbs_has_data
                            when sbs_empty =>
                                if stall_in_int = '1' and strobe_in = '1' and buff_empty_int = '0' then
                                    v_stall_buffer_storing := '1';
        
                                    s_stall_buffer_state <= sbs_full;
                                end if;
                            -- The stall buffer is full
                            when sbs_full => 
                                -- Behaviour for: New data arriving
                                if strobe_in = '1' then
                                    -- If we cannot output while the buffer is full, raise a sync_error!
                                    if buff_full = '1' then
                                        sync_error <= '1';
                                    else   -- Output data from buffer ...
                                        v_stall_buffer_providing := '1';
                                        v_stall_buffer_storing := '1';
                                    end if;
        
                                -- Behaviour for: No new data, output data to pipeline
                                elsif buff_full = '0' and strobe_in = '0' then
                                    v_stall_buffer_providing := '1';
                                    s_stall_buffer_state <= sbs_empty;
                                end if;
        
                        end case;
        
                        
                        -- Data buffer management
                        if v_stall_buffer_storing = '1' then
                            -- Store new data, increment stored data count
                            stall_buffer_data_reg <= data_in;
                            stall_buffer_sync_reg(0) <= hsync_in;
                            stall_buffer_sync_reg(1) <= vsync_in;
                        end if;
        
                        stall_buffer_providing <= v_stall_buffer_providing;
    
    
                        -- !Outside of if clause to provide up-to-date values within the output if clause!
                        next_in_buf_idx := to_integer(in_buf_idx);
    
                        -- On data input:
                        if (strobe_in = '1' and stall_in_int = '0') or v_stall_buffer_providing = '1' or (strobe_in = '1' and buff_empty_int = '1') then
                            if v_stall_buffer_providing = '1' then
                                v_load_data := stall_buffer_data_reg;
                            else 
                                v_load_data := data_in;
                            end if;
                            -- Store the incoming data word in the data buffer
                            data_buffer(
                                    to_integer(in_buf_idx) + DIN_WIDTH - 1
                                    downto to_integer(in_buf_idx)
                                ) <= v_load_data;
    
                            -- Calculate the location of the next incoming data word and update the register.
                            -- Note: 'DIN_WIDTH' is guaranteed to evenly divide 'c_buffer_width'
                            next_in_buf_idx := (to_integer(in_buf_idx) + DIN_WIDTH) mod c_buffer_width;
                            in_buf_idx <= to_unsigned(next_in_buf_idx, c_idx_width);
    
                            -- For sync signals: Store the 'in buffer idx' when the signal ocurred
                            if ((hsync_in = '1') 
                                    or (v_stall_buffer_providing = '1' 
                                        and stall_buffer_sync_reg(0) = '1')
                                    ) then
    
                                if next_in_buf_idx = 0 then
                                    hsync_buf_idx <= to_unsigned(c_buffer_width - 1, c_idx_sync_width);
                                else
                                    hsync_buf_idx <= to_unsigned(next_in_buf_idx, c_idx_sync_width);
                                end if;
                            end if;
    
                            if ((vsync_in = '1') 
                                    or (v_stall_buffer_providing = '1' 
                                        and stall_buffer_sync_reg(1) = '1')
                                    ) then
                                if next_in_buf_idx = 0 then
                                    vsync_buf_idx <= to_unsigned(c_buffer_width - 1, c_idx_sync_width);
                                else
                                    vsync_buf_idx <= to_unsigned(next_in_buf_idx, c_idx_sync_width);
                                end if;
                            end if;
                        end if;
    
                        strobe_out_int <= '0';
                        hsync_out <= '0';
                        vsync_out <= '0';
    
                        -- Output when enough data is stored for output or the buffer is full
                        -- Also listen to the stall signal, only output if it is low!
                        if (next_in_buf_idx >= to_integer(out_buf_idx) + DOUT_WIDTH or buff_full = '1' or v_stall_buffer_providing = '1')
                                and stall_out = '0' then
                            -- Every time we have enough data stored to output a data word, send 'strobe_out_int' for one cycle
                            strobe_out_int <= '1';
    
                            -- Calculate the next 'out buffer idx' and update the register
                            -- Note: 'DOUT_WIDTH' is guaranteed to evenly divide 'c_buffer_width'
                            next_out_buf_idx := (to_integer(out_buf_idx) + DOUT_WIDTH) mod c_buffer_width;
                            out_buf_idx <= to_unsigned(next_out_buf_idx, c_idx_width);
                            
                            -- For sync signals: When we reach a 'out buffer idx' higher or equal to the stored 
                            -- 'in buffer idx' of when we got the sync signal, send the signal on the output
                            -- Edge case: The next 'out buffer idx' is 0, i.e. the register rolls over 
                            -- before it reaches a higher or equal value to the stored 'in buffer idx'.
                            -- In that case, also send the sync signal.
    
                            -- For 'hsync_out':
                            if next_out_buf_idx >= hsync_buf_idx 
                                    or (next_out_buf_idx = 0 
                                        and buff_full = '1'
                                        and hsync_buf_idx < c_sync_off
                                    ) then
                                hsync_out <= '1';
                                -- Reset the stored buffer index to the maximum buffer width (to disable signal output)
                                hsync_buf_idx <= to_unsigned(c_sync_off, c_idx_sync_width);
                            end if;
    
                            -- For 'vsync_out':
                            if next_out_buf_idx >= vsync_buf_idx 
                                    or (next_out_buf_idx = 0 
                                        and buff_full = '1'
                                        and vsync_buf_idx < c_sync_off
                                    ) then
                                vsync_out <= '1';
                                -- Reset the stored buffer index to the maximum buffer width (to disable signal output)
                                vsync_buf_idx <= to_unsigned(c_sync_off, c_idx_sync_width);
                            end if;
                            
                        end if;
                    end if;
                end if;
            end process;
    
            -- Data output:
            -- As the 'out buffer idx' lags behind by one clock cycle,
            -- it will be updated by the time strobe is generated
            -- Therefore it defines the end of the data word to output: 
            --   (out_buf_idx - 1 downto out_buf_idx - DOUT_WIDTH) 
            -- instead of (out_buf_idx + DOUT_WIDTH - 1 downto out_buf_idx), as indexing for data input works, as it is handled BEFORE the idx update.
            -- Edge case: When the buffer rolls over, we need to output the last possible data word at the high end of the buffer.
            --            As 'out buffer idx' is zero in that case, the before indexing scheme does not work, hence the extra case.
            data_out_int <= (others => '0') when reset_int = '1' 
                else data_buffer(to_integer(out_buf_idx) - 1 downto to_integer(out_buf_idx) - DOUT_WIDTH) when out_buf_idx > 0
                else data_buffer(c_buffer_width - 1 downto c_buffer_width - DOUT_WIDTH); -- For rolled over buffer
        end generate;
    
    end architecture RTL;
    