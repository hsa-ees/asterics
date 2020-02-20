----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  Copyright (C) Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_iic
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Author:         Philip Manke
--
-- Modified:       2017-08-30 Philip Manke
--
-- Description:    Simple IP Core that behaves like an I2C master. 
--                 Supports clock stretching and variable serial clock 
--                 speeds adjustible by software from ~10kHz to ~1MHz. 
--                 Does not support arbitration (no multi master).
--                 Only supports 7 bit addresses.
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
--! @file  as_iic.vhd
--! @brief Simple IP Core that behaves like an I2C master.
----------------------------------------------------------------------------------


--! \addtogroup as_iic
--!  @{

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

library asterics;
use asterics.helpers.all;

entity as_iic is
  generic (
    SCL_DIV_REGISTER_WIDTH : integer := 12
  );
  port (
    clk   : in std_logic;
    reset : in std_logic;
    
    sda_in : in std_logic;
    sda_out : out std_logic;
    sda_out_enable : out std_logic;

    scl_in : in std_logic;
    scl_out : out std_logic;
    scl_out_enable : out std_logic;

    --! Slave register interface
    slv_ctrl_reg : in slv_reg_data(0 to 1);
    slv_status_reg : out slv_reg_data(0 to 1);
    slv_reg_modify : out std_logic_vector(0 to 1);
    slv_reg_config : out slv_reg_config_table(0 to 1)
  );
end as_iic;

--! @}

architecture RTL of as_iic is

  -- Slave register interface:
  signal control_new : std_logic_vector(15 downto 0);
  signal control : std_logic_vector(15 downto 0);
  signal status : std_logic_vector(15 downto 0);
  signal control_reset : std_logic_vector(15 downto 0);
  signal scl_div_data_tx : std_logic_vector(31 downto 0);

  -- Slave register configuration:
  -- Allows for "dynamic" configuration of slave registers
  -- Possible values and what they mean: 
  -- "00": Register "off". Register will not be available and won't be implemented -> No hardware resource utilization.
  -- "01": From HW view: Status register. Data transport from hardware to software. HW can only write, SW can only read.
  -- "10": From HW view: Control register. Data transport from software to hardware. HW can only read, SW can only write.
  -- "11": Combined Read/Write register. Data transport in both directions. 
  --       When both sides attempt to write simultaniously, only the HW gets to write.
  --       These registers use both the slv_ctrl_reg and slv_status_reg ports for communication.
  constant slave_register_configuration : slv_reg_config_table(0 to 1) :=
                    ("11","11");

  -- local registers:

  --! The local data register. Used to accumulate read data and write data to the bus from.
  signal local_data_register : std_logic_vector(7 downto 0);
  signal ldata_next : std_logic_vector(7 downto 0);
  
  --! Used to locally store the "scl_div" signal and compare with "scl_counter"
  signal scl_div_local : std_logic_vector(SCL_DIV_REGISTER_WIDTH-1 downto 0);  
  
  --! A counter running with the system clock, as long as "enable_sclcntr" is high
  signal scl_counter : std_logic_vector(SCL_DIV_REGISTER_WIDTH-1 downto 0);
  
  --! A 2 bit counter that increments every time the register "scl_counter" equals "scl_div".
  --! Its MSB is basically "scl" and its LSB changes every quarter period of the bus clock
  --! lbclkcr ^= "Local Bus CLocK Counter Register"
  --! ! reset state: "11" !
  signal local_bus_clkcr : std_logic_vector(1 downto 0);
  
  --! A small 4 bit counter used to track which bit is being read or written - from or to the bus.
  --! ! reset state: "0001" !
  signal bit_counter : std_logic_vector(3 downto 0);

  --! 1 Bit "register". Set after the address has been sent. 
  --! Used to distinguish between sending data and sending the address in the check ackowledge state.
  signal address_sentreg : std_logic; 

  -- Signals comprising the control and status registers from control MSB downto status LSB:
  signal tstart_continue : std_logic; --! Start or continue a transaction (driver control).
  signal tend : std_logic; --! Stop a transaction ASAP (after acknowledge or start bit) (driver control).
  signal readwrite : std_logic; --! Controls whether a transaction is read or write (driver control).
  signal data_ready : std_logic; --! Signals the hardware that the data in the data register is valid (driver control).
  signal ack_mod : std_logic; --! Modifies die behaviour of the hardware regarding the acknowledge (driver control).
  signal iic_ready : std_logic; --! Is the hardware ready to start a transaction (status)
  signal io_ready : std_logic; --! Is the data slave register ready to be written to or read from (status)
  signal bus_active : std_logic; --! Is data being written on the bus by this hardware (status)
  --! 1 Bit "register". Set after an acknowledgement signal was recieved by the slave (status).
  signal slave_ackreg : std_logic; --! Once set, the register keeps its value until reset by the signal "clear_ackreg".
  signal scl_stalled : std_logic; --! Is a slave currently slowing the bus clock (status)
  signal waiting_sw : std_logic; --! Is the hardware currently waiting on the software (status)

  -- Local signals. Mostly self explanetory:
  signal softreset : std_logic;   --! The main reset signal for the hardware (acts as soft- and hardware reset)
  signal ldata_msb : std_logic;
  signal ldata_lsb : std_logic;
  signal bitcntr_msb : std_logic;
  signal lbclk : std_logic;       --! The msb of "local_bus_clkcr" 
  signal lbclk_half : std_logic;  --! The lsb of "local_bus_clkcr"
  signal slave_ack : std_logic;   --! Helper signal for the slave acknowledgement register
  signal sda_enable : std_logic;  --! Mapped to sda tristate driver enable
  signal data_out : std_logic_vector(7 downto 0);
  signal data_in : std_logic_vector(7 downto 0);

  -- Local control signals. Should be mostly self explanetory... :
  signal left_shift_ldata : std_logic;
  signal inc_bitcntr : std_logic;
  signal clear_bitcntr : std_logic;
  signal clear_ldata : std_logic;
  signal cp_ldata_to_data : std_logic;  --! Copy local data to data rx
  signal cp_data_to_ldata : std_logic;  --! Copy data tx to local data
  signal clear_sclcntr : std_logic;
  signal enable_sclcntr : std_logic;     --! Main enable signal for the scl counter
  signal enable_sclcntr_scl : std_logic; --! Enable signal for the scl counter from the scl state machine
  signal enable_sclcntr_iic : std_logic; --! Enable signal for the scl counter from the main (sda) state machine
  signal set_ldata_lsb : std_logic;     --! Set sda to the current LSB of the local data register
  signal clear_ackreg : std_logic;      --! reset the register "slave_ackreg"
  signal inc_lbclkcr : std_logic;       --! Increment the local bus clock counter register by one
  signal clear_lbclkcr : std_logic;     --! Clear the local bus clock counter register
  signal set_sda_to_ldmsb : std_logic;  --! Set sda to the msb of the local data register
  signal set_sda_low : std_logic;       --! Controls the tristate driver for sda
  signal set_scl_low : std_logic;       --! Controls the tristate driver for scl

  -- Adder signals:
  signal scl_counter_plusone : std_logic_vector(SCL_DIV_REGISTER_WIDTH-1 downto 0);
  signal bit_counter_plusone : std_logic_vector(3 downto 0);
  signal local_bus_clkcr_plusone : std_logic_vector(1 downto 0);

  --! Status type definition for the scl state machine:
  type iic_scl_state is (s_low, s_high, s_stalled);

  --! Status type definition for the main iic state machine:
  -- "waitscll" := wait until scl goes low; "waitsclh" := wait until scl goes high
  type iic_main_state is (
    s_init, s_ready, s_ssb_check, s_ssb_send, -- ssb := Send StartBit
    s_sb_init, s_sb_setsda, s_sb_next, s_sb_waitscll, s_sb_swdata, -- sb := Send Byte (on the bus) 
    s_rb_init, s_rb_waitsclh, s_rb_readsda, s_rb_shift, s_rb_waitscll, s_rb_wait_swdata, -- rb := Receive Byte
    s_ca_init, s_ca_readsda, -- ca := Check Acknowledge
    s_sa_waitscll, s_sa_waitsclh, s_sa_setsda, -- sa := Send Acknowledge
    s_sna_waitscll, s_sna_waitsclh, s_sna_sendna, -- sna := Send Not-Acknowledged
    s_spb_check, s_spb_send); -- spb := Send stoPBit

  --! Signals for the state machines:
  signal scl_curstate, scl_nextstate : iic_scl_state;
  signal iic_curstate, iic_nextstate : iic_main_state;


begin

  -- Slave register logic:

  slv_reg_config <= slave_register_configuration;

  control <= slv_ctrl_reg(0)(31 downto 16);
  slv_status_reg(0) <= control_new & status;
  slv_status_reg(1) <= (others => '0');
  slv_reg_modify(1) <= '0';
  scl_div_data_tx <= slv_ctrl_reg(1);
  
  -- Handle the control_reset signal 
  -- and set the modify bit for the status and control register, as necessary
  status_control_update_logic: process(control, control_reset, slv_ctrl_reg, status, reset)
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
      if status /= slv_ctrl_reg(0)(15 downto 0) then
          slv_reg_modify(0) <= '1';
      end if;
  end process status_control_update_logic;


  -- Module logic:

  sda_out <= '0';
  sda_out_enable <= not sda_enable;
  scl_out <= '0';
  scl_out_enable <= not set_scl_low;

  -- Mapping of the control register to the local signals:
  tstart_continue <= control(0);
  tend            <= control(1);
  readwrite       <= control(2);
  softreset       <= control(3) or reset;
  data_ready      <= control(4);
  ack_mod         <= control(5);
  
  --! Mapping of the status register to the local signals and the data rx signal:
  status(0) <= iic_ready;
  status(1) <= io_ready;
  status(2) <= bus_active;
  status(3) <= not slave_ackreg;
  status(4) <= scl_stalled;
  status(5) <= waiting_sw;
  status(6) <= set_scl_low;
  status(7) <= sda_enable;
  status(15 downto 8) <= data_out;
  
  --! Mapping of the control-reset register of the AXI bus system:
  -- reset tstart_continue after sending/receiveing a byte and on tend.
  -- reset tend on iic_ready.
  -- reset readwrite on transaction end.
  -- reset the softreset and data_ready on the next clock cycle.
  -- reset ack_mod after sending/receiving a byte and on tend.
  control_reset(0) <= bitcntr_msb or tend or softreset;
  control_reset(1) <= iic_ready or softreset;
  control_reset(2) <= tend or softreset;
  control_reset(3) <= softreset;
  control_reset(4) <= data_ready;
  control_reset(5) <= bitcntr_msb or tend or softreset;
  control_reset(15 downto 6) <= (others => '0');

  -- Mapping of additional local status signals and data registers:
  ldata_msb <= local_data_register(7);
  ldata_lsb <= local_data_register(0);
  bitcntr_msb <= bit_counter(3);
  lbclk <= local_bus_clkcr(1);
  lbclk_half <= local_bus_clkcr(0);
  data_in <= scl_div_data_tx(31 downto 24);
  local_data_register <= ldata_next;

  -- Enable signal for the sda tristate driver
  sda_enable <= not ldata_msb when set_sda_to_ldmsb = '1' else '1' when set_sda_low = '1' else '0';

  -- enable_sclcntr driver signal
  enable_sclcntr <= enable_sclcntr_scl and enable_sclcntr_iic;

  -- Adders for incrementing the local counters:
  scl_counter_plusone <= std_logic_vector(unsigned(scl_counter) + 1);
  bit_counter_plusone <= std_logic_vector(unsigned(bit_counter) + 1);
  local_bus_clkcr_plusone <= std_logic_vector(unsigned(local_bus_clkcr) + 1);

  --! State and output logic for the scl generator:
  scl_gen_logic: process(clk)
  begin
    if rising_edge(clk) then
      -- Clear and increment logic for the scl counter register
      if clear_sclcntr = '1' then 
        scl_counter <= (others => '0');
        inc_lbclkcr <= '0';
      elsif (scl_counter >= scl_div_local) and (enable_sclcntr = '1') then 
        scl_counter <= (others => '0');
        inc_lbclkcr <= '1';
      elsif enable_sclcntr = '1' then 
        scl_counter <= scl_counter_plusone; 
        inc_lbclkcr <= '0';
      else scl_counter <= scl_counter;
        inc_lbclkcr <= '0'; 
      end if;
      
      -- Set local scl_div signal 
      scl_div_local <= scl_div_data_tx(SCL_DIV_REGISTER_WIDTH - 1 downto 0);
      
      -- Clear and increment logic for the local bus clock counter register
      if clear_lbclkcr = '1' then
        local_bus_clkcr <= "11";
      elsif inc_lbclkcr = '1' then
        local_bus_clkcr <= local_bus_clkcr_plusone;
      else
        local_bus_clkcr <= local_bus_clkcr;
      end if;

      -- Synchronous state transitions 
      scl_curstate <= scl_nextstate; 
    end if;
  end process;

  --! State transitions for the scl generator:
  scl_gen_state_trans: process(scl_curstate, softreset, scl_in, lbclk)
  begin
    -- reset control signals
    set_scl_low <= '0';
    enable_sclcntr_scl <= '0';
    scl_stalled <= '0';
    
    -- Keep current state
    scl_nextstate <= scl_curstate;
    
    if softreset = '1' then scl_nextstate <= s_high; -- reset state
    else
      case scl_curstate is -- State transitions:

        -- scl is low
        when s_low =>
          set_scl_low <= '1';
          enable_sclcntr_scl <= '1';
          
          if lbclk = '1' then scl_nextstate <= s_high; end if;
    
        -- scl is high
        when s_high =>
          enable_sclcntr_scl <= '1';

          if lbclk = '0' then scl_nextstate <= s_low;
          elsif lbclk = '1' and scl_in = '0' then scl_nextstate <= s_stalled; end if;

        -- scl is pulled low by the slave: clock stretching!
        when s_stalled =>
          scl_stalled <= '1';

          if scl_in = '1' then scl_nextstate <= s_high; end if;

      end case;
    end if;
  end process;

  --! State and output logic for the main iic state machine:
  main_iic_logic : process(clk)
  begin
    if rising_edge(clk) then
      -- Operations on the local data register
      if clear_ldata = '1' then 
        ldata_next <= (others => '0');
      elsif cp_data_to_ldata = '1' then 
        ldata_next <= data_in;
      elsif set_ldata_lsb = '1' then 
        ldata_next(7 downto 1) <= local_data_register(7 downto 1);
        ldata_next(0) <= sda_in;
      elsif left_shift_ldata = '1' then 
        ldata_next(7 downto 1) <= local_data_register(6 downto 0);
        ldata_next(0) <= '0';
      else 
        ldata_next <= local_data_register;
      end if;

      -- Clear and increment logic for the bit counter register
      if clear_bitcntr = '1' then bit_counter <= "0001";
      elsif inc_bitcntr = '1' then bit_counter <= bit_counter_plusone; end if;

      -- Data register driver
      if cp_ldata_to_data = '1' then data_out <= local_data_register;
      else data_out <= data_out; end if;

      -- Acknowledgement register logic
      if clear_ackreg = '1' then slave_ackreg <= '1';
      elsif slave_ack = '0' or slave_ackreg = '0' then slave_ackreg <= '0';
      else slave_ackreg <= '1'; end if;
      
      -- Synchronous state transitions
      iic_curstate <= iic_nextstate;
    end if;
  end process;

  --! State transitions for the main iic state machine:
  main_iic_state_trans : process(iic_curstate, softreset, sda_in, scl_in, lbclk_half, bitcntr_msb,
                                   ldata_msb, tstart_continue, tend, readwrite, data_ready, ack_mod)
  begin
    -- reset control signals
    left_shift_ldata <= '0';
    inc_bitcntr <= '0';
    clear_bitcntr <= '0';
    clear_ldata <= '0';
    cp_ldata_to_data <= '0';
    cp_data_to_ldata <= '0';
    clear_sclcntr <= '0';
    clear_lbclkcr <= '0';
    set_sda_low <= '0';
    set_ldata_lsb <= '0';
    enable_sclcntr_iic <= '1';
    iic_ready <= '0';
    io_ready <= '1';
    bus_active <= '0';
    slave_ack <= '1';
    waiting_sw <= '0'; 
    clear_ackreg <= '0';
    set_sda_to_ldmsb <= '0';

    -- Keep current state
    iic_nextstate <= iic_curstate;

    if softreset = '1' then iic_nextstate <= s_init;
    else
      case iic_curstate is

        -- Initialize
        when s_init =>
          clear_bitcntr <= '1';
          clear_ldata <= '1';
          clear_sclcntr <= '1';
          clear_lbclkcr <= '1';
          clear_ackreg <= '1';

          iic_nextstate <= s_ready;

        -- Ready
        when s_ready =>
          clear_sclcntr <= '1';
          enable_sclcntr_iic <= '0';

          iic_ready <= '1';
          
          if tstart_continue = '1' then iic_nextstate <= s_ssb_check; end if;

        -- Send Start Bit
        when s_ssb_check =>
          clear_ackreg <= '1';
          io_ready <= '0';  
          
          if scl_in = '1' and lbclk_half = '1' then iic_nextstate <= s_ssb_send; end if;
                
        when s_ssb_send =>
          set_sda_low <= '1';
          bus_active <= '1';
          io_ready <= '0';
          
          if scl_in = '0' and lbclk_half = '1' then
            if tend = '1' then iic_nextstate <= s_spb_check;
            else iic_nextstate <= s_sb_init; end if;
          end if;
           
        -- Send Byte
        when s_sb_init =>
          cp_data_to_ldata <= '1';
          clear_bitcntr <= '1';
          bus_active <= '1';
          io_ready <= '0';

          iic_nextstate <= s_sb_setsda;

        when s_sb_setsda =>
          bus_active <= '1';
          set_sda_to_ldmsb <= '1';
          
          if scl_in = '1' then iic_nextstate <= s_sb_waitscll; end if;

        when s_sb_waitscll =>
          bus_active <= '1';
          set_sda_to_ldmsb <= '1';
        
          if scl_in = '0' and lbclk_half = '1' then iic_nextstate <= s_sb_next; end if;

        when s_sb_next =>
          bus_active <= '1';
          left_shift_ldata <= '1';
          set_sda_to_ldmsb <= '1';
          inc_bitcntr <= '1';

          if bitcntr_msb = '1' then iic_nextstate <= s_sb_swdata;
          else iic_nextstate <= s_sb_setsda; end if;

        when s_sb_swdata =>
          waiting_sw <= '1';
          clear_bitcntr <= '1';
          enable_sclcntr_iic <= '0';
          
          if data_ready = '1' then
            if ack_mod = '0' then iic_nextstate <= s_ca_init;
            else iic_nextstate <= s_sa_waitscll; end if;
          end if;

        -- Receive Byte
        when s_rb_init =>
          clear_bitcntr <= '1';
          clear_ldata <= '1';
          io_ready <= '0';
          
          if scl_in = '0' then iic_nextstate <= s_rb_waitsclh; end if;

        when s_rb_waitsclh =>
          io_ready <= '0';
          
          if scl_in = '1' and lbclk_half = '1' then iic_nextstate <= s_rb_readsda; end if;
  
        when s_rb_readsda =>
          io_ready <= '0';
          set_ldata_lsb <= '1';
          inc_bitcntr <= '1';

          if bitcntr_msb = '1' then iic_nextstate <= s_rb_wait_swdata;
          else iic_nextstate <= s_rb_shift; end if;

        when s_rb_shift =>
          io_ready <= '0';
          left_shift_ldata <= '1';

          iic_nextstate <= s_rb_waitscll;

        when s_rb_waitscll =>
          io_ready <= '0';

          if scl_in = '0' then iic_nextstate <= s_rb_waitsclh; end if;

        when s_rb_wait_swdata =>
          clear_bitcntr <= '1';
          cp_ldata_to_data <= '1';
          waiting_sw <= '1';
          enable_sclcntr_iic <= '0';
          
          if data_ready = '1' then
            if tstart_continue = '0' or tend = '1' then iic_nextstate <= s_sna_waitscll;
            else iic_nextstate <= s_sa_waitscll; end if;
          end if;
          
        -- Check for acknowledge
        when s_ca_init =>
          clear_ackreg <= '1';
          
          if scl_in = '1' then iic_nextstate <= s_ca_readsda; end if;

        when s_ca_readsda =>
          slave_ack <= sda_in;

          if scl_in = '0' and lbclk_half = '1' then
            if tend = '1' or tstart_continue = '0' then iic_nextstate <= s_spb_check;
            elsif readwrite = '1' then iic_nextstate <= s_rb_init;
            else iic_nextstate <= s_sb_init; end if;
          end if;
          
        -- Send acknowledge
        when s_sa_waitscll =>
          if scl_in = '0' and lbclk_half = '1' then iic_nextstate <= s_sa_setsda; end if;

        when s_sa_setsda =>
          set_sda_low <= '1';
          bus_active <= '1';

          if scl_in = '1' then iic_nextstate <= s_sa_waitsclh; end if;
		  
        when s_sa_waitsclh =>
          set_sda_low <= '1';
          bus_active <= '1';
		  
          if scl_in = '0' and lbclk_half = '1' then
            if readwrite = '1' then iic_nextstate <= s_rb_init; 
            else iic_nextstate <= s_sb_init; end if;
          end if;

        -- Send not acknowledge
        when s_sna_waitscll =>
          if scl_in = '0' then iic_nextstate <= s_sna_waitsclh; end if;
        
        when s_sna_waitsclh =>
          if scl_in = '1' then iic_nextstate <= s_sna_sendna; end if;

        when s_sna_sendna =>
          if scl_in = '0' and lbclk_half = '1' then iic_nextstate <= s_spb_check; end if;

        -- Send stop bit
        when s_spb_check =>
          if scl_in = '0' then iic_nextstate <= s_spb_send; end if;
        
        when s_spb_send =>
          set_sda_low <= '1';
          bus_active <= '1';
		
          if scl_in = '1' and lbclk_half = '1' then iic_nextstate <= s_ready; end if;

      end case;
    end if;
  end process;

end RTL;

-- vim: et ts=2 sw=2:
