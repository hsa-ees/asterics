----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  Copyright (C) Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- File:           as_memreader.vhd
-- Entity:         as_memreader
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Andreas Gareis, Alexander Zoellner
--
-- Modified:       Philip Manke: Use new slaveregister system for as_automatics
--
-- Description:    This module reads image data from memory and outputs an image
--                 data stream with HSYNC and VSYNC signals.
--                 The module is able to access memory sectionwise 
--                 with stride for 2D operations.
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
--! @file
--! @brief This module reads data from memory and outputs a data stream.
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

library asterics;
use asterics.FIFO_FWFT;
use asterics.as_mem_address_generator;
use asterics.helpers.all;

entity AS_MEMREADER is
  generic (
    DOUT_WIDTH                      : integer := 32;        -- Default bit width of data (has to be equal to MEMORY_DATA_WIDTH)
    MEMORY_DATA_WIDTH               : integer := 32;        -- Default bit width of bus connections
    MEM_ADDRESS_BIT_WIDTH           : integer := 32;        -- Default bit width of memory address
    BURST_LENGTH_BIT_WIDTH          : integer := 12;        -- Default bit width of burst length setting (bus dependant)
    MAX_PLATFORM_BURST_LENGTH       : integer := 256;       -- Max. supported burst length in byte by platform
    FIFO_NUMBER_OF_BURSTS           : natural := 4;         -- Min. number of stored bursts in fifo, power of 2 is used for actual size
    SUPPORT_MULTIPLE_SECTIONS       : boolean := false;     -- has to be false if used for as_memio
    SUPPORT_VARIABLE_BURST_LENGTH   : boolean := true;      -- Support smaller burst lengths if possible.
    SUPPORT_INTERRUPTS              : boolean := false;     -- Activate to allow sending interrupt events
    SUPPORT_DONE_IRQ_SOURCE         : boolean := false      -- Choose done state as interrupt source
  );
  port (
    clk         : in std_logic;
    reset       : in std_logic;
    ready       : out std_logic;

    -- OUT ports
    strobe_out  : out std_logic;
    data_out    : out std_logic_vector(DOUT_WIDTH-1 downto 0);
    stall_in        : in  std_logic;
    
    interrupt_out   : out std_logic;
    
    --! Slave register interface
    slv_ctrl_reg : in slv_reg_data(0 to 6);
    slv_status_reg : out slv_reg_data(0 to 6);
    slv_reg_modify : out std_logic_vector(0 to 6);
    slv_reg_config : out slv_reg_config_table(0 to 6);

    
--! Ports for as_arbiter. Set mem_req_ack to 1 if no arbiter is used.
    mem_req            : out std_logic;
    mem_req_ack        : in  std_logic;
--! Ports for memory bus access
    mem_go             : out std_logic;
    mem_clr_go         : in  std_logic;
    mem_busy           : in  std_logic;
    mem_done           : in  std_logic;
    mem_error          : in  std_logic;
    mem_timeout        : in  std_logic;

    mem_rd_req         : out std_logic;
    mem_wr_req         : out std_logic;
    mem_bus_lock       : out std_logic;
    mem_burst          : out std_logic;
    mem_addr           : out std_logic_vector(MEM_ADDRESS_BIT_WIDTH-1 downto 0);
    mem_be             : out std_logic_vector(15 downto 0);
    mem_xfer_length    : out std_logic_vector(BURST_LENGTH_BIT_WIDTH - 1 downto 0);

    mem_in_en          : in  std_logic;
    mem_in_data        : in  std_logic_vector(MEMORY_DATA_WIDTH-1 downto 0);
    mem_out_en         : in  std_logic;
    mem_out_data       : out std_logic_vector(MEMORY_DATA_WIDTH-1 downto 0)
  );
end AS_MEMREADER;

architecture RTL of AS_MEMREADER is

    -- Configure fifo to store a single data input in a single line
    constant c_fifo_bit_width                   : natural := DOUT_WIDTH;
    
    -- Determine the number of bytes of a word
    constant c_number_of_bytes_per_word : natural := MEMORY_DATA_WIDTH/8;

    -- Restrict number of bits used for fifo access to a minimum
    constant c_fifo_buff_depth_width        : natural := log2_ceil(FIFO_NUMBER_OF_BURSTS*(MAX_PLATFORM_BURST_LENGTH/c_number_of_bytes_per_word));
    constant c_fifo_buff_depth              : natural := 2**c_fifo_buff_depth_width;

    -- Slave register configuration:
    -- Allows for "dynamic" configuration of slave registers
    -- Possible values and what they mean: 
    -- "00": Register "off". Register will not be available and won't be implemented -> No hardware resource utilization.
    -- "01": From HW view: Status register. Data transport from hardware to software. HW can only write, SW can only read.
    -- "10": From HW view: Control register. Data transport from software to hardware. HW can only read, SW can only write.
    -- "11": Combined Read/Write register. Data transport in both directions. 
    --       When both sides attempt to write simultaniously, only the HW gets to write.
    --       These registers use both the slv_ctrl_reg and slv_status_reg ports for communication.
    constant slave_register_configuration : slv_reg_config_table(0 to 6) :=
                            ("11","10","10","10","10","10","01");

    --! Port for sending commands to the as_memreader.
    -- control
    -- | 15 ...    2 |     1    |     0    |
    -- |     n.c.    |    go    |   reset  |
    -- |_____________|__________|__________|
    signal control : std_logic_vector(15 downto 0);
    
    --! State of the as_memreader module (busy, done, etc.)
    -- state
    -- | 15 ...    6 |      5     |       4        |      3     |     2     |     1    |     0    |
    -- |     n.c.    | pending go |       n.c.     |     n.c.   |   n. c.   |   busy   |   done   |
    -- |_____________|____________|________________|____________|___________|__________|__________|
    signal state : std_logic_vector(15 downto 0);
    
    --! Control reset bits. Automatic reset of primarily software set control bits by hardware.
    signal control_reset : std_logic_vector(15 downto 0);
    
    --! Signal used as an intermidiate to apply the control_reset logic and then update the register
    signal control_new : std_logic_vector(15 downto 0);
    
    --! Configuration ports for read access (see corresponding hardware driver for 
    --! more information).
    signal reg_section_addr : std_logic_vector(31 downto 0);
    signal reg_section_offset : std_logic_vector(31 downto 0);
    signal reg_section_size : std_logic_vector(31 downto 0);
    signal reg_section_count : std_logic_vector(31 downto 0);
    signal reg_max_burst_length : std_logic_vector(31 downto 0);
    
    --! Current memory address the as_memreader module is performing an operation on.
    signal reg_current_hw_addr : std_logic_vector(31 downto 0);
    
    
    signal s_reset_soft, s_clr_reset    : std_logic;
    
    -- configuration register
    signal r_reg_section_addr       : std_logic_vector(31 downto 0);
    signal r_reg_section_offset     : std_logic_vector(31 downto 0);
    signal r_reg_section_size       : std_logic_vector(31 downto 0);
    signal r_reg_section_count      : std_logic_vector(31 downto 0);
    signal r_reg_max_burst_length   : std_logic_vector(31 downto 0);
    
    -- stored bus access signal register
    signal r_burst_en              : std_logic;
    signal r_mem_addr              : std_logic_vector(MEM_ADDRESS_BIT_WIDTH-1 downto 0);
    signal r_burst_len             : std_logic_vector(BURST_LENGTH_BIT_WIDTH-1 downto 0);
    
    -- input logic
    type mem_sm_state_t is (s_idle, s_init1, s_init, s_init_rx, s_init_rx1, s_mem_init_wait, s_mem_init, s_mem_wait, 
                           s_prep_next_rx, s_done, s_mem_wait_reset, s_reset);
    signal mem_sm_current_state, mem_sm_next_state : mem_sm_state_t;
  
    signal s_mem_sm_go, s_mem_sm_done, s_mem_sm_busy, s_mem_sm_clr_go : std_logic;
    signal s_addr_gen_reset : std_logic;
    signal s_set_mem_go, s_mem_sm_save_config_reg : std_logic;
    signal s_reset_mem_sm : std_logic;
    signal s_addr_gen_load_addr : std_logic;
    signal s_activate_addr_gen : std_logic;

    -- fifo
    signal s_fifo_din, s_fifo_dout  : std_logic_vector(c_fifo_bit_width-1 downto 0);
    signal s_fifo_empty, s_fifo_full, s_fifo_prog_empty, s_fifo_prog_full   : std_logic;
    signal s_fifo_reset         : std_logic;
    signal r_prog_empty_thresh, r_prog_full_thresh  : std_logic_vector(log2_ceil(c_fifo_buff_depth)-1 downto 0);
    signal s_fifo_wr_en, s_fifo_rd_en               : std_logic;
    
    -- addr_gen
    signal s_addr_gen_ready     : std_logic;
    signal s_burst_length         : std_logic_vector(BURST_LENGTH_BIT_WIDTH-1 downto 0);
    signal s_burst_en             : std_logic;
    signal s_read_mem_addr          : std_logic_vector(MEM_ADDRESS_BIT_WIDTH-1 downto 0);
    
    -- output logic
    signal s_out_reset, s_mem_sm_reset_out  : std_logic;
    signal s_fifo_fill_level                : std_logic_vector(c_fifo_buff_depth_width downto 0);
    
    -- interrupt
    signal s_done_irq                   : std_logic;
    

begin
    -- Assign the register configuration to the register interface.
    slv_reg_config <= slave_register_configuration;
    
    -- Control portion of the status and control register
    control <= slv_ctrl_reg(0)(31 downto 16);

    -- Connect the control register ports to the respective control signals
    reg_section_addr     <= slv_ctrl_reg(1);
    reg_section_offset   <= slv_ctrl_reg(2);
    reg_section_size     <= slv_ctrl_reg(3);
    reg_section_count    <= slv_ctrl_reg(4);
    reg_max_burst_length <= slv_ctrl_reg(5);
    
    -- Connect the status signals to the state registers
    slv_status_reg(0) <= control_new & state;
    slv_status_reg(6) <= reg_current_hw_addr;
    -- Enable "always-on" state register updates
    slv_reg_modify(6) <= '1';
    
    -- Handle the control_reset signal 
    -- and set the modify bit for the status and control register, as necessary
    status_control_update_logic: process(control, control_reset, slv_ctrl_reg, state, reset)
        variable var_control_new : std_logic_vector(15 downto 0);
    begin
        -- Reset control and status register modify bit
        slv_reg_modify(0) <= '0';
        
        -- Clear control bits of the register on module reset
        if reset = '1' then
          control_new <= (others => '0');
        else
          control_new <= control;
        end if;
        
        -- Apply control_reset bit mask
        var_control_new := control and (not control_reset);
        
        -- If either control or state was modified by hardware, set modify bit
        if control /= var_control_new then 
            control_new <= var_control_new;
            slv_reg_modify(0) <= '1';
        end if;
        if state /= slv_ctrl_reg(0)(15 downto 0) then
            slv_reg_modify(0) <= '1';
        end if;
    end process status_control_update_logic;

--! Process for copying configuration values to shadow registers to prevent them from being
--! overwritten during operation.
    COPY_CONFIGURATION : process(clk)
    begin
        if rising_edge(clk) then
            if reset = '1' then
                r_reg_section_addr      <= (others => '0');
                r_reg_section_offset    <= (others => '0');
                r_reg_section_size      <= (others => '0');
                r_reg_section_count     <= (others => '0');
                r_reg_max_burst_length  <= (others => '0');
            elsif s_mem_sm_save_config_reg = '1' then
                r_reg_section_addr      <= reg_section_addr;
                r_reg_section_offset    <= reg_section_offset;
                r_reg_section_size      <= reg_section_size;
                r_reg_section_count     <= reg_section_count;
                r_reg_max_burst_length  <= reg_max_burst_length;
            end if;
        end if;
    end process;
    
--! Process for copying signals from address generator to shadow registers to 
--! prevent them from being overwritten during bus access.
    COPY_ADDRESS : process(clk)
    begin
       if rising_edge(clk) then
           if reset  = '1' then
               r_burst_en  <= '0';
               r_burst_len <= (others => '0');
               r_mem_addr  <= (others => '0');
           elsif s_addr_gen_load_addr = '1' then
               r_burst_en  <= s_burst_en;
               r_burst_len <= s_burst_length;
               r_mem_addr  <= s_read_mem_addr;
           end if;
        end if;
    end process;
    
-- Enable the software to reset the hardware (only if not in reset state already).
    s_reset_soft <= '1' when control(0) = '1' and s_clr_reset = '0' else '0';
-- Activate read process if the software sets the corresponding bit in the control register.
    s_mem_sm_go <= control(1);

-- Have the reset bit reseted by register control unit (usually bus slave)
    control_reset(0) <= s_clr_reset;
-- Have the go bit reseted by register control unit (usually bus slave)
    control_reset(1) <= s_mem_sm_clr_go;
    control_reset(15 downto 2) <= (others => '0'); 

-- Signal software (or different hw module) having finished the last data transmission
    state(0)      <= s_mem_sm_done;
-- Signal software (or different hw module) that a transmission is currently processed
    state(1)      <= s_mem_sm_busy;
-- Signal software (or different hw module) that corrupted data has been detected (not supported)
    state(2)      <= '0';
-- Signal software (or different hw module) that a synchronization error has been detected (not supported)
    state(3)      <= '0';
-- Signal software (or different hw module) that no further go signal can be currently handled.
    state(5)      <= s_mem_sm_go;
-- Set all other status bits to 0 (currently not used)
    state(15 downto 6) <= (others => '0');
-- Set all other write enable bits for the status port to zeros
  
-- Signal previous hardware module being ready for operation
    ready <= not s_mem_sm_busy;
    
--! Address generator module instantiation for calculating address and control 
--! signals for read accesses.
    addr_gen : entity as_mem_address_generator
    generic map(
        ADDRESS_BIT_WIDTH   => MEM_ADDRESS_BIT_WIDTH,           -- Adopt memory bus bit width from toplevel
        MEMORY_BIT_WIDTH    => MEMORY_DATA_WIDTH,
        BURST_LENGTH_WIDTH  => BURST_LENGTH_BIT_WIDTH,          -- Adopt maximal supported burst length from toplevel
        SUPPORT_MULTIPLE_SECTIONS       => SUPPORT_MULTIPLE_SECTIONS,   -- Adopt section setting from toplevel
        SUPPORT_VARIABLE_BURST_LENGTH => SUPPORT_VARIABLE_BURST_LENGTH  -- Adopt burst length setting from toplevel
    )
    port map(
        clk                 => Clk,
        reset               => s_addr_gen_reset,
        
        go                  => s_activate_addr_gen,      -- State machine signal
        cnt_en              => mem_in_en,              -- Bus signal (data valid)
        ready               => s_addr_gen_ready,
        
        section_addr        => r_reg_section_addr,     -- Config register
        section_offset      => r_reg_section_offset,   -- Config register
        section_size        => r_reg_section_size,     -- Config register
        section_count       => r_reg_section_count,    -- Config register
        max_burst_length    => r_reg_max_burst_length, -- Config register
        
        memory_address      => s_read_mem_addr,
        burst_length        => s_burst_length,
        burst_enable        => s_burst_en
    );

-- Write address output of as_address_generator into 
-- software readable register.
-- Using the registered version of the signal here, as the slv_reg_modify bit is
-- set to a constant '1', to keep the signal constant.
    reg_current_hw_addr     <= r_mem_addr;
    
-- Reset signal for address generator
    s_addr_gen_reset        <= Reset or s_reset_soft;
    
--! Process for requesting bus access. Request gets reseted by 
--! bus after data transmission.
    mem_go_gen: process(clk)
    begin
        if rising_edge(clk) then
            if Reset = '1' then
                mem_go <= '0';
            elsif s_set_mem_go = '1' then
                mem_go <= '1';
            elsif  mem_clr_go = '1' then
                mem_go <= '0';
            end if; 
        end if;
    end process;
    
-------------------------------------------------
-- State machine for handling bus access
-------------------------------------------------
    mem_statemachine: process(mem_sm_current_state, s_mem_sm_go, s_reset_soft, s_fifo_prog_full, mem_busy, mem_done, s_addr_gen_ready, r_burst_en, 
                               r_burst_len, r_mem_addr, mem_req_ack)
    begin
    
    --! Set default state to current state. May be overwritten by 
    --! case assignment of state machine.
        mem_sm_next_state <= mem_sm_current_state;

    --! Default values for output signals of mem_statemachine.
    -- Signals for memory bus
        mem_req <= '0';
        mem_addr <= (others => '0');
        mem_xfer_length <= (others => '0');
        mem_burst <= '0';
        s_mem_sm_busy <= '0';
        s_mem_sm_done <= '0';
        s_set_mem_go <= '0';
        mem_rd_req <= '0';
        mem_be <= x"FFFF";
        mem_wr_req <= '0';
        mem_bus_lock <= '0';
    -- Signal for copying config registers
        s_mem_sm_save_config_reg <= '0';
    -- Signals for address calculator
        s_addr_gen_load_addr <= '0';
        s_activate_addr_gen <= '0';
    -- Signal for reseting output (strobe and data)
        s_mem_sm_reset_out <= '0';
    -- Signal for reseting current go signal
        s_mem_sm_clr_go <= '0';
    -- Signal for clearing software reset
        s_clr_reset <= '0';
    -- Signal for interrupt request
        s_done_irq <= '0';
        
    
        case mem_sm_current_state is
        
        --! Reset state after initializing hw module, after 
        --! error handling or if software sends a reset request 
        --! by setting the corresponding bit in the control 
        --! register.
            when s_reset =>
                s_clr_reset <= '1';
                s_mem_sm_reset_out <= '1';
                s_mem_sm_clr_go <= '1';
                mem_sm_next_state <= s_idle;
                
        --! Default state of as_memreader if hw module is ready 
        --! for receiving order to conduct reading memory data.
        --! During idle state, config parameters are continuously 
        --! copied into shadow registers to begin memory access 
        --! right away after receiving "go" signal.
            when s_idle =>
                s_mem_sm_done <= '1';
                s_mem_sm_save_config_reg <= '1';
                if s_mem_sm_go = '1' then
                    mem_sm_next_state <= s_init;
                end if;
                
        --! Wait for as_address_generator 
        --! being ready (s_addr_gen_ready) before initializing 
        --! memory bus access.
            when s_init =>
                s_mem_sm_busy <= '1';
                s_mem_sm_clr_go <= '1';
                if s_addr_gen_ready = '1' then
                    mem_sm_next_state <= s_init1;
                end if;

        --! This state sets the "go" signal for the as_
        --! address_generator to have it calculate the next address 
        --! and determine the type of memory bus access (burst or 
        --! single-beat access). Valid data of as_address_generator
        --! is assumed when it is operating (add_gen_ready = 0).
            when s_init1 =>
                s_activate_addr_gen <= '1';
                s_mem_sm_busy <= '1';
                if s_addr_gen_ready = '0' then
                    mem_sm_next_state <= s_init_rx;
                end if;

        --! Copy the information of the as_address_generator 
        --! into shadow registers to keep them on a constant value 
        --! during bus access (some bus interfaces may require constant 
        --! values).
            when s_init_rx =>
                s_mem_sm_busy <= '1';
                s_addr_gen_load_addr <= '1';
                if s_fifo_prog_full = '0' then
                    mem_sm_next_state <= s_init_rx1;
                end if;

        --! Check if enough space is available in the fifo buffer for 
        --! receiving data. Furthermore, check if memory bus is currently 
        --! handling a transaction and therefore is busy.
            when s_init_rx1 =>
                mem_req <= '1';
                s_mem_sm_busy <= '1';
                if mem_req_ack = '1' then
                    if mem_busy = '1' then
                        mem_sm_next_state <= s_mem_init_wait;
                    else
                        mem_sm_next_state <= s_mem_init;
                    end if;
                end if;

        --! The fifo buffer has enough space available but the memory 
        --! bus is currently busy and cannot receive another request.
        --! Wait until memory bus can receive a new request.
            when s_mem_init_wait =>
                mem_req <= '1';
                s_mem_sm_busy <= '1';
                if mem_busy = '0' then
                    mem_sm_next_state <= s_mem_init;
                end if;

        --! Set necessary control bits and signals acquired from 
        --! AS_MEM_ADDRESS_GENERATOR for initializing a read 
        --! request.
                
            when s_mem_init =>
                mem_req <= '1';
                s_mem_sm_busy <= '1';
                s_set_mem_go <= '1';
                mem_rd_req <= '1';
                mem_be <= x"ffff";
                mem_xfer_length <= r_burst_len;
                mem_addr <= r_mem_addr;
                mem_burst <= r_burst_en;
                mem_sm_next_state <= s_mem_wait;

        --! Keep control bits and required signals until the read 
        --! request is finished. If the AS_MEM_ADDRESS_GENERATOR 
        --! signals that no more data has to be requested return to 
        --! "idle" state, otherwise setup next read request.            
            when s_mem_wait =>
                mem_req <= '1';
                s_mem_sm_busy <= '1';
                mem_rd_req <= '1';
                mem_be <= x"ffff";
                mem_xfer_length <= r_burst_len;
                mem_addr <= r_mem_addr;
                mem_burst <= r_burst_en;
                if mem_done = '1' then
                    if s_addr_gen_ready = '1' then
                        mem_sm_next_state <= s_done;
                    else
                        mem_sm_next_state <= s_prep_next_rx;
                    end if;
                end if;

        --! Give the address generator one cycle time for internal 
        --! operation (maybe remove this state and have "s_mem_wait" 
        --! directly go to "s_init_rx").
            when s_prep_next_rx =>
                s_mem_sm_busy <= '1';
                mem_sm_next_state <= s_init_rx;

        --! Signal that all data was acquired. This state is mainly 
        --! for for as_memreader operating with other hardware modules 
        --! which may require information about bus access completion.
            when s_done =>
                if SUPPORT_DONE_IRQ_SOURCE then
                    s_done_irq <= '1';
                end if;
                s_mem_sm_busy <= '1';              
                s_mem_sm_done <= '1';              
                mem_sm_next_state <= s_idle;

            when others => mem_sm_next_state <= s_reset;
        
        end case;
    end process;
    
    -- Reset signal for state machine
    s_reset_mem_sm <= Reset or s_reset_soft;
    
    -- Process for updating state
    process(clk)
    begin
        if rising_edge(clk) then
            if s_reset_mem_sm = '1' then
                mem_sm_current_state <= s_reset;
            else
                mem_sm_current_state <= mem_sm_next_state;
            end if;
        end if;
    end process;
    
    
-------------------------------------------------
-- Fifo
-------------------------------------------------

    fifo : entity FIFO_FWFT
    generic map (
        DATA_WIDTH => c_fifo_bit_width,
        BUFF_DEPTH => c_fifo_buff_depth,
        PROG_EMPTY_ENABLE => true,
        PROG_FULL_ENABLE => true
    )
    port map (
        clk => clk,
        reset => s_fifo_reset,
        
        din => s_fifo_din,
        wr_en => s_fifo_wr_en,
        rd_en => s_fifo_rd_en,
        dout => s_fifo_dout,
        
        level => s_fifo_fill_level,
        full => s_fifo_full,
        empty => s_fifo_empty,
        
        prog_full_thresh => r_prog_full_thresh,
        prog_full => s_fifo_prog_full,
        
        prog_empty_thresh => r_prog_empty_thresh,
        prog_empty => s_fifo_prog_empty
    );
    
    
    --! Reset the fifo if the as_memreader is reseted.
    s_fifo_reset <= Reset or s_reset_soft;
    --! Set threshold to fifo size/2. (Maybe set to other value)
    r_prog_full_thresh <= std_logic_vector(to_unsigned(c_fifo_buff_depth/2, c_fifo_buff_depth_width));
    
    --! Write next data word into fifo if memory bus sends a valid signal.
    s_fifo_wr_en <= mem_in_en;
    s_fifo_din <= mem_in_data;
    --! Send next word in fifo to following hardware module if it does not send a 
    --! "stall" signal and there is remaining data in the fifo.
    s_fifo_rd_en <= '1' when STALL_IN = '0' and s_fifo_empty = '0' else '0';

-------------------------------------------------
-- output logic
-------------------------------------------------

    --! Synchronize data output with clock.
    process(clk)
    begin
        if rising_edge(clk) then
            DATA_OUT <= s_fifo_dout;
        end if;
    end process;
    
    s_out_reset <= reset or s_mem_sm_reset_out or s_reset_soft;
    
    --! Synchronize strobe with clock (since STALL might be asynchronous).
    sync_gen : process(clk)
    begin
        if rising_edge(clk) then
            if s_out_reset = '1' then
                STROBE_OUT <= '0';
            else
                STROBE_OUT <= s_fifo_rd_en;
            end if;
        end if;
    end process;
    
------------------------------------------------------------------------
-- Switch off interrupt logic
------------------------------------------------------------------------
    DEACTIVATE_INTERRUPT_REQUESTS : if SUPPORT_INTERRUPTS = false generate
        interrupt_out <= '0';
    
    end generate;

------------------------------------------------------------------------
-- Switch on interrupt logic
------------------------------------------------------------------------
    ACTIVATE_INTERRUPT_REQUESTS : if SUPPORT_INTERRUPTS = true generate
        interrupt_out <= s_done_irq;
    
    end generate;
        
end architecture;
