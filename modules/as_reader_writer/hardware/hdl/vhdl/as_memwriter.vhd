----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  Copyright (C) Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- File:           as_memwriter.vhd
-- Entity:         as_memwriter
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Andreas Gareis, Alexander Zoellner
--
-- Modified:       2017-09-12 by Alexander Zoellner: Add data unit logic
--                 Philip Manke: Use new slaveregister system for as_automatics
--
-- Description:    This module receives an image data stream with HSYNC and 
--                 VSYNC signals and writes e.g. to local system memory 
--                 (using burst access).
--                 
--                 Parameters need to be set before running this module.
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
--! @brief This module writes (image) data using a data bus master interface; input needs to be as_stream compatible.
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

use work.helpers.all;

entity AS_MEMWRITER is
    generic (
        DIN_WIDTH                   : integer := 64;            -- Data bit width
        MEMORY_DATA_WIDTH           : integer := 64;            -- Bit width of the memory port (currently has to match MEMORY_DATA_WIDTH)
        MEM_ADDRESS_BIT_WIDTH       : integer := 32;            -- Bit width of memory address bus
        BURST_LENGTH_BIT_WIDTH      : integer := 12;            -- Default bit width of burst length setting (bus dependant)
        MAX_PLATFORM_BURST_LENGTH   : integer := 256;           -- Max. supported burst length in byte by platform
        FIFO_NUMBER_OF_BURSTS       : natural := 4;             -- Min. number of stored bursts in fifo, power of 2 is used for actual size
        SUPPORT_MULTIPLE_SECTIONS   : boolean := false;         -- Has to be false if used for as_memio
        SUPPORT_INTERRUPTS          : boolean := false;         -- Activate to send interrupt requests
        SUPPORT_DONE_IRQ_SOURCE     : boolean := false;         -- Choose done state as interrupt source
        SUPPORT_DUC_IRQ_SOURCE      : boolean := false;         -- Choose data unit complete as interrupt source
        SUPPORT_DATA_UNIT_COMPLETE  : boolean := false;         -- Activate data unit complete logic
        UNIT_COUNTER_WITDH          : integer := 8              -- Set bit width for data unit complete counter (SUPPORT_DATA_UNIT_COMPLETE has to be set to "true")
    );
    port (
        clk         : in  std_logic;
        reset       : in  std_logic;
        ready       : out std_logic;

        -- IN ports
        strobe_in           : in  std_logic;
        data_in             : in  std_logic_vector(DIN_WIDTH-1 downto 0);
        --! Signal for indicating the end of a logical data unit
        data_unit_complete_in  : in std_logic;
        --! Request to write remaining data in fifo buffer to memory
        flush_in          : in std_logic;

        -- OUT ports
        interrupt_out       : out std_logic;
        stall_out           : out std_logic;
        
        --! Error port
        sync_error_out          : out std_logic;

        --! Slave register interface
        slv_ctrl_reg : in slv_reg_data(0 to 8);
        slv_status_reg : out slv_reg_data(0 to 8);
        slv_reg_modify : out std_logic_vector(0 to 8);
        slv_reg_config : out slv_reg_config_table(0 to 8);

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
end AS_MEMWRITER;



architecture RTL of AS_MEMWRITER is

    -- Configure fifo to store a single data input in a single line
    constant c_fifo_bit_width                 : natural := DIN_WIDTH;
  
    -- Determine the number of bytes of a word
    constant c_number_of_bytes_per_word   : natural := DIN_WIDTH / 8;
  
    -- Restrict number of bits used for fifo access to a minimum
    constant c_fifo_buff_depth_width       : natural := log2_ceil(FIFO_NUMBER_OF_BURSTS*(MAX_PLATFORM_BURST_LENGTH/c_number_of_bytes_per_word));
    constant c_fifo_buff_depth             : natural := 2**c_fifo_buff_depth_width;
    -- Program fifo level for setting stall signal 
    constant c_fifo_prog_full              : natural := c_fifo_buff_depth - 1;


    component FIFO_FWFT is
    generic (
        DATA_WIDTH : integer := MEMORY_DATA_WIDTH;
        BUFF_DEPTH : integer := c_fifo_buff_depth;
        PROG_EMPTY_ENABLE : boolean := true;
        PROG_FULL_ENABLE : boolean := true
    );
    port (
        clk         : in  std_logic;
        reset       : in  std_logic;
        
        din         : in  std_logic_vector(DATA_WIDTH-1 downto 0);
        wr_en       : in  std_logic;
        rd_en       : in  std_logic;
        dout        : out std_logic_vector(DATA_WIDTH-1 downto 0);
        
        level       : out std_logic_vector(log2_ceil(BUFF_DEPTH) downto 0);
        full        : out std_logic;
        empty       : out std_logic;
        
        prog_full_thresh  : in std_logic_vector(log2_ceil(BUFF_DEPTH)-1 downto 0);
        prog_full         : out std_logic;
        
        prog_empty_thresh : in std_logic_vector(log2_ceil(BUFF_DEPTH)-1 downto 0);
        prog_empty        : out std_logic
    );
    end component;
  

    component AS_MEM_ADDRESS_GENERATOR is
    generic (
        ADDRESS_BIT_WIDTH           : integer := 32;
        MEMORY_BIT_WIDTH            : integer := 32;
        BURST_LENGTH_WIDTH          : integer := 12;
        SUPPORT_MULTIPLE_SECTIONS       : boolean := false;
        SUPPORT_VARIABLE_BURST_LENGTH : boolean := false
    );
    port (
        clk                 : in std_logic;
        reset               : in std_logic;
        
        go                  : in std_logic;
        cnt_en              : in std_logic;
        ready               : out std_logic;
        
        section_addr        : in std_logic_vector(31 downto 0);
        section_offset      : in std_logic_vector(31 downto 0);
        section_size        : in std_logic_vector(31 downto 0);
        section_count       : in std_logic_vector(31 downto 0);
        max_burst_length    : in std_logic_vector(31 downto 0);

        memory_address      : out std_logic_vector(ADDRESS_BIT_WIDTH-1 downto 0);
        burst_length        : out std_logic_vector(BURST_LENGTH_WIDTH-1 downto 0);
        burst_enable        : out std_logic
    );
    end component;
    
    -- Slave register configuration:
    -- Allows for "dynamic" configuration of slave registers
    -- Possible values and what they mean: 
    -- "00": Register "off". Register will not be available and won't be implemented -> No hardware resource utilization.
    -- "01": HW -> SW, Status register only. Data transport from hardware to software. HW can only write, SW can only read.
    -- "10": HW <- SW, Control register only. Data transport from software to hardware. HW can only read, SW can only write.
    -- "11": W <=> SW, Combined Read/Write register. Data transport in both directions. ! Higher FPGA resource utilization !
    --       When both sides attempt to write simultaniously, only the HW gets to write.
    --       These registers use both the slv_ctrl_reg and slv_status_reg ports for communication.
    constant slave_register_configuration : slv_reg_config_table(0 to 8) :=
                            ("11","10","10","10","10","10","01","01","01");
    
    --! Register for sending commands to the as_memwriter (usually by software)
    -- control
    -- | 15 ...    8 |     7     |         6        |      5      |              4               |    3     |    2     |     1    |     0    |
    -- |     n.c.    |   flush   | disable on no go | single shot | enable on data unit complete | disable  |  enable  |    go    |   reset  |
    -- |_____________|___________|__________________|_____________|______________________________|__________|__________|__________|__________|
    signal control : std_logic_vector(15 downto 0);

    --! Request reset of target control bits set by different hw module or software.
    -- control_reset
    -- | 15 ...    8 |      7      |            6           |         5         |                4                   |       3        |      2       |     1    |      0      |
    -- |     n.c.    | clear flush | clear disable on no go | clear single shot | clear enable on data unit complete | clear disable  | clear enable | clear go | clear reset |
    -- |_____________|_____________|________________________|___________________|____________________________________|________________|______________|__________|_____________|
    
    signal control_reset : std_logic_vector(15 downto 0);
    --! Status information of the memwriter to software
    -- state
    -- | 15 ...    7 |      6     |      5     |       4        |      3     |     2     |     1    |     0    |
    -- |     n.c.    | enable set | pending go | flushable data | sync error |   n. c.   |   busy   |   done   |
    -- |_____________|____________|____________|________________|____________|___________|__________|__________|
    signal state : std_logic_vector(15 downto 0);
    

    --! Signal used as an intermidiate to apply the control_reset logic and then update the register
    signal control_new : std_logic_vector(15 downto 0);
    
    --! Configuration ports for write access (see corresponding hardware driver for 
    --! more information).
    signal reg_section_addr            : std_logic_vector(31 downto 0);
    signal reg_section_offset          : std_logic_vector(31 downto 0);
    signal reg_section_size            : std_logic_vector(31 downto 0);
    signal reg_section_count : std_logic_vector(31 downto 0);
    signal reg_max_burst_length : std_logic_vector(31 downto 0);
    --! Current memory address the as_memreader module is performing an operation on.
    signal reg_current_hw_addr : std_logic_vector(31 downto 0);
    --! Address of the last successfully written unit
    signal reg_last_data_unit_complete_addr : std_logic_vector(31 downto 0);
    --! The current amount of units which have been received
    signal reg_current_unit_count : std_logic_vector(31 downto 0);
  
  
  
    signal s_reset_soft, s_clr_reset : std_logic;
  
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
  
    -- synchronization error
    signal s_sync_error : std_logic;
  
    -- fifo
    signal s_fifo_din, s_fifo_dout : std_logic_vector(c_fifo_bit_width-1 downto 0);
    signal s_fifo_wr_en, s_fifo_rd_en : std_logic;
    signal s_fifo_empty, s_fifo_full, s_fifo_prog_empty, s_fifo_prog_full : std_logic;
    signal s_fifo_reset : std_logic;
    signal s_flush_input_data : std_logic;
    signal r_prog_empty_thresh : std_logic_vector(log2_ceil(c_fifo_buff_depth)-1 downto 0);
    signal s_fifo_level        : std_logic_vector(log2_ceil(c_fifo_buff_depth) downto 0);
    signal r_prog_full_thresh  : std_logic_vector(log2_ceil(c_fifo_buff_depth)-1 downto 0);

  
    -- output statemachine logic
    type mem_sm_state_t is (s_idle, s_init1, s_init, s_init_tx, s_init_tx1, s_mem_init_wait_sbeat, s_mem_init_wait_burst, 
                            s_mem_init_sbeat, s_mem_init_burst, s_mem_wait_sbeat, s_mem_wait_burst, s_prep_next_tx, s_done, 
                            s_disable, s_discard_data, s_unit_align, s_mem_wait_reset, s_reset);
    signal mem_sm_current_state, mem_sm_next_state : mem_sm_state_t;
  
    signal s_mem_sm_go, s_mem_sm_done, s_mem_sm_busy, s_mem_sm_clr_go : std_logic;
    signal s_addr_gen_reset : std_logic;
    signal s_burst_calc_reset : std_logic;
    signal s_set_mem_go, s_mem_sm_save_config_reg : std_logic;
    signal s_mem_sm_disable_on_no_go    : std_logic;
    signal s_mem_sm_flush               : std_logic;
    signal s_mem_sm_clr_enable          : std_logic;
    signal s_reset_mem_sm : std_logic;
    signal s_mem_sm_reset_fifo : std_logic;
    signal s_activate_addr_gen : std_logic;
    signal s_addr_gen_load_addr : std_logic;
    signal s_mem_sm_clr_disable_on_no_go : std_logic;
    
    
    -- input statemachine logic
    type input_sm_state_t is (st_input_sm_reset, st_input_sm_idle, st_input_sm_trigger, st_input_sm_enable, st_input_sm_prep_disable, 
                              st_input_sm_reset_mem_sm);
    signal input_sm_current_state, input_sm_next_state : input_sm_state_t;
    signal s_sm_trigger_enable          : std_logic;
    signal s_input_sm_clr_enable_on_data_unit_complete  : std_logic;
    signal s_input_sm_clr_single_shot   : std_logic;
    signal s_input_sm_trigger_enable    : std_logic;
    signal s_input_sm_trigger_disable   : std_logic;
    signal s_input_sm_reset_mem_sm      : std_logic;
    signal s_input_sm_enable_on_data_unit_complete  : std_logic;
    signal s_input_sm_single_shot       : std_logic;
    signal s_reset_input_sm             : std_logic;
    
    -- input enable logic
    signal s_enable                     : std_logic;
    signal s_sw_enable                  : std_logic;
    signal s_sw_disable                 : std_logic;
    signal s_sw_clr_enable              : std_logic;
    signal s_sw_clr_disable             : std_logic;
    
    -- address generator
    signal s_burst_en   : std_logic;
    signal s_burst_length : std_logic_vector(BURST_LENGTH_BIT_WIDTH-1 downto 0);
    signal s_write_mem_addr : std_logic_vector(MEM_ADDRESS_BIT_WIDTH-1 downto 0);
    signal s_addr_gen_ready : std_logic;
    
    -- unit counter
    signal s_last_data_unit_complete_addr   : std_logic_vector(31 downto 0);
    signal s_current_fifo_level         : unsigned(log2_ceil(c_fifo_buff_depth) downto 0);
    signal s_unit_count                 : unsigned(UNIT_COUNTER_WITDH-1 downto 0);
    signal s_enable_count               : std_logic;
    signal s_unit_flush                 : std_logic;
    signal s_unit_flush_complete        : std_logic;
    
    signal s_flush                      : std_logic;
    signal s_clr_flush                  : std_logic;
    signal s_flush_stall                : std_logic;
    
    -- interrupt
    signal s_duc_irq                    : std_logic;
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
    slv_status_reg(7) <= reg_last_data_unit_complete_addr;
    slv_status_reg(8) <= reg_current_unit_count;
    
    -- Enable "always-on" state register updates
    slv_reg_modify(6 to 8) <= (others => '1');

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
               r_mem_addr  <= s_write_mem_addr;
           end if;
        end if;
    end process;
        
------------------------------------------------------------------------
-- Control Bits
------------------------------------------------------------------------
-- Enable the software to reset the hardware (only if not in reset state already).
    s_reset_soft <= '1' when ( ( control(0) = '1' ) AND ( s_clr_reset = '0' ) ) else '0';
-- Activate read process if the software sets the corresponding bit in the control register.
    s_mem_sm_go                             <= control(1);
-- Allow memwriter to accept data and store it in fifo buffer
    s_sw_enable                             <= control(2);
-- Discard incoming data without storing them into fifo buffer    
    s_sw_disable                            <= control(3);
-- Synchronizes the memwriter on receiving a high value on its "data_unit_complete_in" port
    s_input_sm_enable_on_data_unit_complete <= control(4); -- also set enable signal
-- Have the memwriter only process a single data unit; Only takes effect if 
-- enable_on_data_unit_complete is also set
    s_input_sm_single_shot                  <= control(5);
-- Disable the memwriter after finishing its current operation if no "go" signal ("control(1)")
-- has been set
    s_mem_sm_disable_on_no_go               <= control(6);
-- Enable writting all remaining data in fifo buffer to memwriter by setting "control(5)" (by software)
-- or "flush_in" (by hardware module) to a high value. Setting either signals to a high value results 
-- in setting the port "stall_out" of the memwriter to a high value. 
    s_flush                                 <= control(7) or flush_in;

------------------------------------------------------------------------
-- Reset for Control Bits
------------------------------------------------------------------------
-- Have the reset bit reseted by register control unit (usually bus slave)
    control_reset(0) <= s_clr_reset;
-- Request to reset the go bit set by software
    control_reset(1) <= s_mem_sm_clr_go;
-- Request to reset the enable bit set by software
    control_reset(2) <= s_sw_clr_enable;
-- Request to reset the disable bit set by software
    control_reset(3) <= s_sw_clr_disable;
-- Request to reset the enable_on_data_unit_complete bit set by software
    control_reset(4) <= s_input_sm_clr_enable_on_data_unit_complete;
-- Request to reset the single_shot bit set by software
    control_reset(5) <= s_input_sm_clr_single_shot;
-- Request to reset the disable_on_no_go bit set by software
    control_reset(6) <= s_mem_sm_clr_disable_on_no_go;
-- Request to reset the flush bit set by software
    control_reset(7) <= s_clr_flush;
-- Set all other reset bits to 0 (no operation, only for precaution)
    control_reset(15 downto 8) <= (others => '0');
    
------------------------------------------------------------------------
-- Status Information for Software
------------------------------------------------------------------------
-- Signal software (or different hw module) having finished the last data transmission
    state(0) <= s_mem_sm_done;
-- Signal software (or different hw module) that a transmission is currently processed
    state(1) <= s_mem_sm_busy;
    state(2) <= '0';
-- Signal software (or different hw module) that a synchronization error has been detected.
    state(3) <= s_sync_error;
-- Signal software that the buffer of the memwriter currently holds data which may be flushed
    state(4) <= not s_fifo_empty;
-- Signal software (or different hw module) that no further go signal can be currently handled (pending go).
    state(5) <= s_mem_sm_go;
-- Signal software if enable is currently set
    state(6) <= s_enable;
-- Set all other status bits to 0 (currently not used)
    state(15 downto 7) <= (others => '0');
    
-- Write address output of as_address_generator into software readable register.
-- Using the registered version of the signal here, as the slv_reg_modify bit is
-- set to a constant '1', to keep the signal constant.
    reg_current_hw_addr <= r_mem_addr;
-- Write current number of received data units into software readable register.
    reg_current_unit_count <= std_logic_vector(resize(s_unit_count, reg_current_unit_count'length));
-- Write last successfully written data unit end address into software readable register.
    reg_last_data_unit_complete_addr <= s_last_data_unit_complete_addr;
    
------------------------------------------------------------------------
-- Status Information for Hardware
------------------------------------------------------------------------
-- Signal previous hardware module being ready for operation
    ready           <= not s_mem_sm_busy;
-- Signal other hardware modules that a sync error has been detected
    sync_error_out  <= s_sync_error;
    
    
------------------------------------------------------------------------
-- Address Generator
------------------------------------------------------------------------
--! Address generator module instantiation for calculating address and control 
--! signals for read accesses.
    addr_gen : AS_MEM_ADDRESS_GENERATOR
    generic map(
        ADDRESS_BIT_WIDTH   => MEM_ADDRESS_BIT_WIDTH,               -- Adopt memory bus bit width from toplevel
        MEMORY_BIT_WIDTH    => MEMORY_DATA_WIDTH,
        BURST_LENGTH_WIDTH  => BURST_LENGTH_BIT_WIDTH,              -- Adopt maximal supported burst length from toplevel
        SUPPORT_MULTIPLE_SECTIONS       => SUPPORT_MULTIPLE_SECTIONS,       -- Adopt section setting from toplevel
        SUPPORT_VARIABLE_BURST_LENGTH   => false                       -- Feature not supported for as_memwriter
    )
    port map(
        clk                 => clk,
        reset               => s_addr_gen_reset,
        
        go                  => s_activate_addr_gen,     -- State machine signal
        cnt_en              => mem_out_en,              -- Bus signal (data valid)
        ready               => s_addr_gen_ready,
        
        section_addr        => r_reg_section_addr,      -- Config register
        section_offset      => r_reg_section_offset,    -- Config register
        section_size        => r_reg_section_size,      -- Config register
        section_count       => r_reg_section_count,     -- Config register
        max_burst_length    => r_reg_max_burst_length,  -- Config register
        
        memory_address      => s_write_mem_addr,
        burst_length        => s_burst_length,
        burst_enable        => s_burst_en
    );
    
-- reset signal for address generator
    s_addr_gen_reset <= reset or s_reset_soft;
    
    
------------------------------------------------------------------------
-- Fifo Buffer
------------------------------------------------------------------------
    fifo : FIFO_FWFT
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
        
        level => s_fifo_level,
        full => s_fifo_full,
        empty => s_fifo_empty,
        
        prog_full_thresh => r_prog_full_thresh,
        prog_full => s_fifo_prog_full,
        
        prog_empty_thresh => r_prog_empty_thresh,
        prog_empty => s_fifo_prog_empty
    );
    
    --! reset the fifo if the as_memwriter is reseted.
    s_fifo_reset <= reset or s_reset_soft or s_mem_sm_reset_fifo;
    --! Set threshold of fifo. 
    r_prog_empty_thresh <= std_logic_vector(resize(unsigned(s_burst_length(s_burst_length'length -1 downto log2_ceil_zero(c_number_of_bytes_per_word))) - 1,log2_ceil(c_fifo_buff_depth)));
    --! Set programmed threshold to number of fifo entries minus 1 for setting stall_out in time.
    r_prog_full_thresh <= std_logic_vector(to_unsigned(c_fifo_prog_full, r_prog_full_thresh'length));

    -- Generally generate STALL if fifo is full  or a flush operation is performed:
    stall_out <= s_fifo_prog_full or s_flush_stall;

    -- FIFO write: Write incoming data if the "enable" bit is set and the fifo buffer 
    -- is currently not full. Alternatively, write the first data word accompanied by 
    -- the "data_unit_complete".
    s_fifo_wr_en <= (strobe_in and not(s_fifo_full) and s_enable) or (s_input_sm_trigger_enable and strobe_in and data_unit_complete_in);
    s_fifo_din <= data_in;
    --! Read next data word from fifo if memory bus sends a valid signal.
    s_fifo_rd_en <= mem_out_en;
    mem_out_data <= s_fifo_dout;
    
    
------------------------------------------------------------------------
-- Process for Detecting Synchronization Error
------------------------------------------------------------------------
    --! A sync_error is detected when a strobe is received despite the fifo buffer 
    --! being full. The error can only be lifted by resetting the memwriter.
    SYNC_ERROR : process(clk)
    begin
        if rising_edge(clk) then
            if reset = '1' or s_reset_soft = '1' then
                s_sync_error <= '0';
            else
                if strobe_in = '1' and s_fifo_full = '1' then
                    s_sync_error <= '1';
                end if;
            end if;
        end if;
    end process;
    
    
------------------------------------------------------------------------
-- Process for Flushing Data (Write to Memory)
------------------------------------------------------------------------
    --! Write all currently stored data in the fifo buffer to memory up to
    --! the end of the programmed section. The "stall_out" port is set to 
    --! "1" during the flush process.
    FLUSH : process(clk)
    begin
        if rising_edge(clk) then
            if reset = '1' or s_reset_soft = '1' then
                s_flush_stall <= '0';
                s_mem_sm_flush <= '0';
            else
                if s_flush = '1' then
                    s_flush_stall <= '1';
                    s_mem_sm_flush <= '1';
                    s_clr_flush <= '1';
                else 
                    s_clr_flush <= '0';
                end if;
                if s_fifo_empty = '1' or (s_mem_sm_done = '1' and s_mem_sm_go = '0') then
                    s_flush_stall <= '0';
                    s_mem_sm_flush <= '0';
                end if;
            end if;
        end if;
    end process;


------------------------------------------------------------------------
-- State Machine for Handling Bus Access
------------------------------------------------------------------------
    MEM_STATEMACHINE : process(mem_sm_current_state, s_mem_sm_go, s_fifo_prog_empty, r_burst_en, mem_busy, mem_done, 
                               r_reg_max_burst_length, s_addr_gen_ready, s_fifo_empty, r_mem_addr, s_mem_sm_disable_on_no_go, s_mem_sm_flush, s_unit_flush, mem_req_ack)
    begin
    
    --! Set default state to current state. May be overwritten by 
    --! case assignment of state machine.
        mem_sm_next_state <= mem_sm_current_state;
        
    --! Default values for output signals of mem_statemachine
    -- Signals for memory bus
        mem_req <= '0';
        mem_burst <= '0';
        mem_xfer_length <= (others => '0');
        mem_addr <= (others => '0');
        s_mem_sm_busy <= '0';
        s_mem_sm_done <= '0';
        s_set_mem_go <= '0';
        mem_rd_req <= '0';
        mem_be <= x"FFFF";
        mem_wr_req <= '0';
        mem_bus_lock <= '0';
    -- Signal for interrupt request
        s_done_irq <= '0';
    -- Signal for copying config registers
        s_mem_sm_save_config_reg <= '0';
    -- Signals for address calculator
        s_addr_gen_load_addr <= '0';
        s_activate_addr_gen <= '0';
    -- Signal for flushing fifo buffer
        s_mem_sm_reset_fifo <= '0';
    -- Signal for reseting current go signal
        s_mem_sm_clr_go <= '0';
    -- Signal for clearing software reset
        s_clr_reset <= '0';
        s_mem_sm_clr_enable <= '0';
        s_mem_sm_clr_disable_on_no_go <= '0';
        

        case mem_sm_current_state is
        
        --! Reset state after initializing hw module, after 
        --! error handling, request by the input statemachine 
        --! or if software sends a reset request by setting 
        --! the corresponding bit in the control register.
            when s_reset =>
                s_clr_reset <= '1';
                s_mem_sm_clr_enable <= '1';
                s_mem_sm_clr_go <= '1';
                s_mem_sm_clr_disable_on_no_go <= '1';
                mem_sm_next_state <= s_idle;
                
        --! Default state of as_memwriter if hw module is ready 
        --! for receiving order to conduct writing memory data.
        --! During idle state config parameters are continuously 
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
                s_mem_sm_busy <= '1';
                s_activate_addr_gen <= '1';
                if s_addr_gen_ready = '0' then
                    mem_sm_next_state <= s_init_tx;
                end if;

        --! Copy the information of the as_address_generator 
        --! into shadow registers to keep them on a constant value 
        --! during bus access (some bus interfaces may require constant 
        --! values).
            when s_init_tx =>
                s_mem_sm_busy <= '1';
                s_addr_gen_load_addr <= '1';
                if s_addr_gen_load_addr = '1' then
                    if (s_fifo_prog_empty = '0' and r_burst_en = '1') or (s_fifo_empty = '0' and (r_burst_en = '0' or s_mem_sm_flush = '1' or s_unit_flush = '1')) then
                        mem_sm_next_state <= s_init_tx1;
                    end if;
                end if;
                
        --! State for determining the type of bus access depending on 
        --! information provided by as_address_generator and available
        --! data in fifo. If there is no data in the fifo the state machine 
        --! will remain in this state until at least a single word is 
        --! available (no burst available or flush).
            when s_init_tx1 =>
                mem_req <= '1';
                s_mem_sm_busy <= '1';
                if mem_req_ack = '1' then
                    -- Set up burst if enough data in fifo is available and as_address_generator permits burst
                    if s_fifo_prog_empty = '0' and r_burst_en = '1' then
                        if mem_busy = '1' then
                        -- Go into wait-state until bus is available
                            mem_sm_next_state <= s_mem_init_wait_burst;
                        else
                        -- Start bus access right away if bus is available
                            mem_sm_next_state <= s_mem_init_burst;
                        end if;
                    -- Setup up single-beat transmission if no burst is possible or a flush request has been set
                    elsif s_fifo_empty = '0' and (r_burst_en = '0' or s_mem_sm_flush = '1' or s_unit_flush = '1') then
                        if mem_busy = '1' then
                        -- Go into wait-state until bus is available
                            mem_sm_next_state <= s_mem_init_wait_sbeat;
                        else
                        -- Start bus access right away if bus is available
                            mem_sm_next_state <= s_mem_init_sbeat;
                        end if;
                    end if;
                end if;

        --! The fifo buffer has enough data available but the memory 
        --! bus is currently busy and cannot receive another request.
        --! Wait until memory bus can receive a new request. (Single 
        --! Beat Transmission).
            when s_mem_init_wait_sbeat =>
                mem_req <= '1';
                s_mem_sm_busy <= '1';
                if mem_busy = '0' then
                    mem_sm_next_state <= s_mem_init_sbeat;
                end if;
                
        --! The fifo buffer has enough data available but the memory 
        --! bus is currently busy and cannot receive another request.
        --! Wait until memory bus can receive a new request. (Burst 
        --! Transmission).
            when s_mem_init_wait_burst =>
                mem_req <= '1';
                s_mem_sm_busy <= '1';
                if mem_busy = '0' then
                    mem_sm_next_state <= s_mem_init_burst;
                end if;
                
        --! Set necessary control bits and signals acquired from 
        --! as_address_generator for initializing a single-beat 
        --! write request.
            when s_mem_init_sbeat =>
                mem_req <= '1';
                mem_addr <= r_mem_addr;
                s_mem_sm_busy <= '1';
                s_set_mem_go <= '1';
                mem_wr_req <= '1';
                mem_xfer_length <= (others => '0');
                mem_burst <= '0';
                mem_be <= x"ffff";
                mem_sm_next_state <= s_mem_wait_sbeat;
                
        --! Set necessary control bits and signals acquired from 
        --! as_address_generator for initializing a burst 
        --! write request.
            when s_mem_init_burst => 
                mem_req <= '1';
                mem_addr <= r_mem_addr;
                s_mem_sm_busy <= '1';
                s_set_mem_go <= '1';
                mem_wr_req <= '1';
                mem_xfer_length <= r_reg_max_burst_length(BURST_LENGTH_BIT_WIDTH-1 downto 0);
                mem_burst <= '1';
                mem_be <= x"ffff";
                mem_sm_next_state <= s_mem_wait_burst;
                
        --! Keep control bits and required signals until the single-beat 
        --! write request is finished. If the as_address_generator 
        --! signals that no more data has to be transmitted return to 
        --! "idle" state, otherwise setup next write request.    
            when s_mem_wait_sbeat =>
                mem_addr <= r_mem_addr;
                s_mem_sm_busy <= '1';
                mem_wr_req <= '1';
                mem_xfer_length <= (others => '0');
                mem_burst <= '0';
                mem_be <= x"ffff";
                mem_req <= '1';
                if mem_done = '1' then
                    if s_addr_gen_ready = '1' then
                        mem_sm_next_state <= s_done;
                    else
                        mem_sm_next_state <= s_prep_next_tx;
                    end if;
                end if;
                
        --! Keep control bits and required signals until the burst
        --! write request is finished. If the as_address_generator 
        --! signals that no more data has to be transmitted return to 
        --! "idle" state, otherwise setup next write request. 
            when s_mem_wait_burst =>
                mem_addr <= r_mem_addr;
                s_mem_sm_busy <= '1';
                mem_wr_req <= '1';
                mem_xfer_length <= r_reg_max_burst_length(BURST_LENGTH_BIT_WIDTH-1 downto 0);
                mem_burst <= '1';
                mem_be <= x"ffff";
                mem_req <= '1';
                if mem_done = '1' then
                    if s_addr_gen_ready = '1' then
                        mem_sm_next_state <= s_done;
                    else
                        mem_sm_next_state <= s_prep_next_tx;
                    end if;
                end if;
                
        --! Required for the address generator for updating its current 
        --! status.
            when s_prep_next_tx =>
                s_mem_sm_busy <= '1';
                mem_sm_next_state <= s_init_tx;
                

        --! Signal that all data was transmitted. This state is mainly 
        --! for as_memwriter operating with other hardware modules 
        --! which may require information about bus access completion.
        --! Changes in in "s_disable" state if no further transmission 
        --! is currently requested (go = 0) and the control bit for disabling
        --! the memwriter has been set (disable_on_no_go = 1)
            when s_done =>
                if SUPPORT_DONE_IRQ_SOURCE then
                    s_done_irq <= '1';
                end if;
                s_mem_sm_busy <= '1';
                s_mem_sm_done <= '1';
                if s_mem_sm_disable_on_no_go = '1' and s_mem_sm_go = '0' then 
                    mem_sm_next_state <= s_disable;
                else
                    mem_sm_next_state <= s_idle;
                end if;
               
        --! Clear enable signal to prevent further data being stored in the fifo
        --! buffer. 
            when s_disable =>
                s_mem_sm_busy <= '1';
                s_mem_sm_clr_enable <= '1';
                s_mem_sm_clr_disable_on_no_go <= '1';
                s_mem_sm_reset_fifo <= '1';
                mem_sm_next_state <= s_idle;
                
            when others => mem_sm_next_state <= s_reset;
            
        end case;
    end process;
    
    -- reset signal for state machine
    s_reset_mem_sm <= reset or s_reset_soft or s_input_sm_reset_mem_sm;
    
    -- Process for updating state
    UPDATE_MEM_STATE : process(clk)
    begin
        if rising_edge(clk) then
            if s_reset_mem_sm = '1' then
                mem_sm_current_state <= s_reset;
            else
                mem_sm_current_state <= mem_sm_next_state;
            end if;
        end if;
    end process;
    
    --! Process for requesting bus access. Request gets reseted by 
    --! bus after data transmission.
    mem_go_gen: process(clk)
    begin
        if rising_edge(clk) then
            if reset = '1' or s_reset_soft = '1' then
                mem_go <= '0';
            elsif s_set_mem_go = '1' then
                mem_go <= '1';
            elsif  mem_clr_go = '1' then
                mem_go <= '0';
            end if; 
        end if;
    end process;
    

------------------------------------------------------------------------
-- Process for Controlling Data Input to Fifo Buffer
------------------------------------------------------------------------
    --! This process controls the input data flow to the fifo buffer. Depending on 
    --! software and hardware settings, data is stored in the fifo buffer or is 
    --! discarded without storing. The hardware setting is dominant.
    ENABLE_LOGIC : process(clk)
    begin
        if rising_edge(clk) then
            if reset = '1' or s_reset_soft = '1' then
                s_enable <= '0';
                s_sw_clr_enable <= '1';
                s_sw_clr_disable <= '1';
            else
                s_sw_clr_enable <= '0';
                s_sw_clr_disable <= '0';
                if s_sw_enable = '1' then
                    s_enable <= '1';
                    s_sw_clr_enable <= '1';
                end if;
                if s_sw_disable = '1' then
                    s_enable <= '0';
                    s_sw_clr_disable <= '1';
                end if;
                
                -- Only available if data unit complete logic is set active
                if SUPPORT_DATA_UNIT_COMPLETE = true then 
                    if s_input_sm_trigger_enable = '1' and data_unit_complete_in = '1' then
                        s_enable <= '1';
                    end if;
                    if s_input_sm_trigger_disable = '1' and data_unit_complete_in = '1' then
                        s_enable <= '0';
                    end if;
                end if;
                
                if s_mem_sm_clr_enable = '1' then
                    s_enable <= '0';
                end if;
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
        interrupt_out <= s_duc_irq or s_done_irq;
    
    end generate;

------------------------------------------------------------------------
-- Switch off data unit complete logic
------------------------------------------------------------------------
    DEACTIVATE_DATA_UNIT_COMPLETE : if SUPPORT_DATA_UNIT_COMPLETE = false generate
        -- Set signals to a zero-value which must not hold a high-value if 
        -- data unit complete logic is not used.
        s_input_sm_reset_mem_sm             <= '0';
        s_input_sm_trigger_enable           <= '0';
        
    end generate;
    
    
------------------------------------------------------------------------
-- Switch on data unit complete logic
------------------------------------------------------------------------
    ACTIVATE_DATA_UNIT_COMPLETE : if SUPPORT_DATA_UNIT_COMPLETE = true generate
    ------------------------------------------------------------------------
    -- State Machine for Handling Data Input
    ------------------------------------------------------------------------
        INPUT_STATEMACHINE : process(input_sm_current_state, s_input_sm_enable_on_data_unit_complete, data_unit_complete_in, 
                                    s_input_sm_single_shot, s_unit_flush_complete)
        begin
        
        --! Set default state to current state. May be overwritten by 
        --! case assignment of state machine.
            input_sm_next_state <= input_sm_current_state;
        --! Default values for output signals of input statemachine
            s_input_sm_trigger_enable <= '0';
            s_input_sm_trigger_disable <= '0';
            s_input_sm_clr_enable_on_data_unit_complete <= '0';
            s_input_sm_clr_single_shot <= '0';
            s_input_sm_reset_mem_sm <= '0';
            
        
            case input_sm_current_state is
            
            --! Reset state after initializing hw module, after 
            --! error handling or if software sends a reset request 
            --! by setting the corresponding bit in the control 
            --! register.
                when st_input_sm_reset =>
                    s_input_sm_clr_enable_on_data_unit_complete <= '1';
                    s_input_sm_clr_single_shot <= '1';
                    s_input_sm_reset_mem_sm <= '1';
                    input_sm_next_state <= st_input_sm_idle;
                    
            --! This state is assumed after the reset has been performed. 
            --! The statemachine switches to the "st_input_sm_trigger" state 
            --! if the "enable_on_data_unit_complete" control bit is set to 
            --! align incoming data with the start of the next data unit.
                when st_input_sm_idle =>
                    if s_input_sm_enable_on_data_unit_complete = '1' then
                        input_sm_next_state <= st_input_sm_trigger;
                    end if;
                    
            --! Activate the trigger signal for storing the first data word 
            --! which is accompanied with a "data_unit_complete". The trigger 
            --! takes no effect, if no data is provided with the "data_unit_complete" 
            --! signal. Transitions to next state upon receiving a "data_unit_complete".
                when st_input_sm_trigger =>
                    s_input_sm_trigger_enable <= '1';
                    if data_unit_complete_in = '1' then
                        input_sm_next_state <= st_input_sm_enable;
                    end if;
                    
            --! Prepare to disable the "enable" bit for the fifo buffer if the 
            --! "single_shot" control bit is set for only storing a single 
            --! data unit. Otherwise, the statemachine returns to its idle 
            --! state. Further, the "enable_on_data_unit_complete" control bit is reset.
                when st_input_sm_enable =>
                    s_input_sm_clr_enable_on_data_unit_complete <= '1';
                    if s_input_sm_single_shot = '1' then
                        input_sm_next_state <= st_input_sm_prep_disable;
                    else
                        input_sm_next_state <= st_input_sm_idle;
                    end if;
                    
            --! Set trigger signal for disabling the "enable" bit upon receiving 
            --! the next "data_unit_complete" signal. Switch to next state if all 
            --! data of the current data unit has been written to memory. The 
            --! "single_shot" control bit is requested to be cleared.
                when st_input_sm_prep_disable =>
                    s_input_sm_clr_single_shot <= '1';
                    s_input_sm_trigger_disable <= '1';
                    if s_unit_flush_complete = '1' then
                        input_sm_next_state <= st_input_sm_reset_mem_sm;
                    end if;
                    
            --! Reset the mem_statemachine after writing the data unit to memory. 
            --! The reset process will result in clearing all control bits for 
            --! the mem_statemachine, such as "go" or "pending_go".
                when st_input_sm_reset_mem_sm =>
                    s_input_sm_reset_mem_sm <= '1';
                    input_sm_next_state <= st_input_sm_idle;
                    
            end case;
        end process;
        
        s_reset_input_sm <= reset or s_reset_soft;
                        
        -- Process for updating state
        UPDATE_INPUT_STATE : process(clk)
        begin
            if rising_edge(clk) then
                if s_reset_input_sm = '1' then
                    input_sm_current_state <= st_input_sm_reset;
                else
                    input_sm_current_state <= input_sm_next_state;
                end if;
            end if;
        end process;


    ------------------------------------------------------------------------
    -- Process for Data Unit Processing
    ------------------------------------------------------------------------
    --! This process takes a snapshot of the current amount of data stored 
    --! in the fifo buffer upon receiving a data_unit_complete signal. The 
    --! amount of is copied to the counter "s_current_fifo_level" which is 
    --! decremented each time data is written to memory. The current data 
    --! unit is considered completed if the counter reaches "0". Subsequently, 
    --! the "s_unit_count" counter is incremented by 1 and the register which 
    --! holds the memory address of the lastly written data unit is updated.
        UNIT_COUNTER : process(clk)
        begin
            if rising_edge(clk) then
                if reset = '1' or s_reset_soft = '1' then
                    s_unit_flush_complete <= '0';
                    s_unit_flush <= '0';
                    s_unit_count <= to_unsigned(0, s_unit_count'length);
                    s_enable_count <= '0';
                    s_duc_irq <= '0';
                    s_current_fifo_level <= to_unsigned(0, s_current_fifo_level'length);
                    s_last_data_unit_complete_addr <= (others => '0');
                else
                    s_unit_flush_complete <= '0';
                    s_duc_irq <= '0';
                    -- Increment unit counter directly if fifo buffer is empty
                    if s_fifo_empty = '1' and data_unit_complete_in = '1' then
                        s_unit_count <= s_unit_count + 1;
                        -- Only update address if a complete data unit has been written to memory
                        if s_input_sm_trigger_enable = '0' then
                            s_last_data_unit_complete_addr <= s_write_mem_addr;
                        end if;
                    -- Take snapshot of the amount of data stored in fifo and activate down-counter
                    elsif s_fifo_empty = '0' and data_unit_complete_in = '1' then
                        s_current_fifo_level <= unsigned(s_fifo_level);
                        s_enable_count <= '1';
                    end if;
                    
                    if s_enable_count = '1' then
                        -- Force memwriter to write all data to memory during single shot modus
                        if s_input_sm_trigger_disable = '1' then
                            s_unit_flush <= '1';
                        end if;
                        -- Increment unit counter and update address as soon as all data of the 
                        -- current unit has been written to memory.
                        if s_current_fifo_level = 0 then
                            s_unit_flush <= '0';
                            s_unit_flush_complete <= '1';
                            s_unit_count <= s_unit_count + 1;
                            s_last_data_unit_complete_addr <= s_write_mem_addr;
                            s_enable_count <= '0';
                            if SUPPORT_DUC_IRQ_SOURCE then
                                s_duc_irq <= '1';
                            end if;
                        -- Decrement snapshot fifo level counter each time data is written to memory
                        elsif s_fifo_rd_en = '1' then
                            s_current_fifo_level <= s_current_fifo_level - 1;
                        end if;
                    end if;
                end if;
            end if;
        end process;
    
    end generate;
    
end architecture;


