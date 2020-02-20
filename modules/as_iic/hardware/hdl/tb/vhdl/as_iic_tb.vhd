----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_iic_tb
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Author:         Philip Manke
--
-- Modified:       2017-08-30 Philip Manke
--
-- Description:    This is a generic testbench for the as_iic asterics
--                 module.
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
--! @file  as_iic_tb.vhd
--! @brief The testbench for the as_iic asterics module.
----------------------------------------------------------------------------------


--! \addtogroup as_iic_tb
--!  @{

library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

library asterics;
use asterics.helpers.all;

entity as_iic_tb is
end entity;


-- Quick testbench running tests with eight preselected bytes: 
-- A testbench run consists of: 16 write tests, 16 read tests
-- 16 tests: 8 simple (one-byte: address & data byte) transactions with different bytes
-- 		       every test checks: start&stop bit, correct read/write, sending and receiving (n)acks
-- 2 tests using simulated clock stretching: very long and very short clock stretching
-- 2 tests checking for correct behaviour of the "master ack after address" capability
-- 4 tests using longer transactions with 3 data bytes each (also from the eight selected bytes)

architecture testbench_quick of as_iic_tb is

constant SCL_DIV_WIDTH : integer := 12; -- serial bus clock accuracy
constant SYS_CLK : integer := 500;      -- in MHz; maximum of 500 MHz 
constant SCL_CLK : integer := 5000;    -- in kHz. This value is used to calculate the value of scl_div

constant TC_MASTER_ACK : unsigned := "101";
constant TC_CLOCK_STRETCHING : unsigned := "100";
constant TC_MULTI_BYTE : unsigned := "11";

component as_iic is
  generic(
    SCL_DIV_REGISTER_WIDTH : integer );
  port(
    Clk   : in std_logic;
    Reset : in std_logic;
  
    sda_in : in std_logic;
    sda_out : out std_logic;
    sda_out_enable : out std_logic;

    scl_in : in std_logic;
    scl_out : out std_logic;
    scl_out_enable : out std_logic;
  
    slv_ctrl_reg : in slv_reg_data(0 to 1);
    slv_status_reg : out slv_reg_data(0 to 1);
    slv_reg_modify : out std_logic_vector(0 to 1);
    slv_reg_config : out slv_reg_config_table(0 to 1));
end component;

type TB_DATASET is array(7 downto 0) of std_logic_vector(7 downto 0);

signal clk, reset, sda, scl : std_logic;
signal sda_in_iic, sda_out_iic, sda_out_enable : std_logic;

signal scl_in_iic, scl_out_iic, scl_out_enable : std_logic;

signal data_rx, data_tx, tb_data : std_logic_vector(7 downto 0);
signal control : std_logic_vector(5 downto 0);
signal status : std_logic_vector(5 downto 0);
signal div : std_logic_vector(SCL_DIV_WIDTH - 1 downto 0);

signal sim_end : std_logic;
signal sda_in, sda_out : std_logic;

signal data_zero : std_logic_vector(23 downto 0);
signal scl_div_zero : std_logic_vector(23 downto SCL_DIV_WIDTH);
signal status_zero : std_logic_vector(1 downto 0);

signal iic_ready, io_ready, bus_active, ackrec, stalled, waiting_sw : std_logic;

signal scycle_counter : integer;

begin

  -- model tristate:
  sda <= sda_out_iic when sda_out_enable = '1';
  sda_in_iic <= sda_out;
  sda_in_iic <= sda_out_iic when sda_out_enable = '1';

  scl_in_iic <= scl;
  scl <= scl_out_iic when scl_out_enable = '1' else 'H';
  -- Data Register logic
  
  data_rx <= (others => 'L');
  scl_div_zero <= (others => '0');
  status_zero <= (others => '0');

-- controls: ack_mod, data_ready, reset, rw, end, start

  sda_in <= '1' when sda = 'H' else sda;
  sda <= 'H' when sda_out = '1' else sda_out; 
  
  test_iic : as_iic
    generic map(
       SCL_DIV_REGISTER_WIDTH => SCL_DIV_WIDTH)
    port map(
      Clk => clk,
      Reset => reset,
      sda_in => sda_in_iic,
      sda_out => sda_out_iic,
      sda_out_enable => sda_out_enable,
      scl_in => scl_in_iic,
      scl_out => scl_out_iic,
      scl_out_enable => scl_out_enable,
      slv_ctrl_reg(0)(5 downto 0) => control,
      slv_ctrl_reg(0)(31 downto 6) => (others => '0'),
      slv_ctrl_reg(1) => (others => '0'),
      slv_status_reg(0)(21 downto 16) => status,
      slv_status_reg(0)(31 downto 24) => data_rx,
      slv_status_reg(1)(SCL_DIV_WIDTH - 1 downto 0) => div,
      slv_status_reg(1)(31 downto 24) => data_tx);
  
  iic_ready <= status(0);
  io_ready <= status(1);
  bus_active <= status(2);
  ackrec <= status(3);
  stalled <= status(4);
  waiting_sw <= status(5);

  --! Clock generator process:
  clkgen : process
  variable clk_waitmult : integer;
  begin
    clk_waitmult := 500 / SYS_CLK; 
    report "Clock simulation started! Simulating " & integer'image(SYS_CLK) & " MHz clock. Using T/2 of " & integer'image(clk_waitmult) & " ns.";
  
    -- Clock loop:
    while not (sim_end = '1') loop 
      clk <= '1';
      wait for clk_waitmult * 1 ns;
      clk <= '0';
      wait for clk_waitmult * 1 ns;
    end loop;
    wait;
  end process;

--! Main process for the generic testbench:
  quick_testbench_process : process
    variable wait_mult : integer;
    variable scl_div : integer;
    variable crt_ctrl : std_logic_vector(5 downto 0);
    variable thalf : integer;

    variable databytes : TB_DATASET;
    variable cycle_counter : unsigned(4 downto 0);
    variable start_controls, mid_controls, stop_controls : std_logic_vector(5 downto 0);

  begin
    
    -- Initialize testbench
    report "Initializing testbench environment...";
    cycle_counter := (others => '0');
    start_controls := "000001";
    mid_controls :=   "010001";
    stop_controls :=  "010010";
    -- a selection of bytes to run the tests with:
    databytes := (x"00", x"FF", x"AA", x"55", x"0F", x"F0", x"3B", x"B3");
    data_tx <= (others => '0');
    tb_data <= (others => '0');
    reset <= '1';
    scl_div := ((SYS_CLK * 1000) / (4 * (SCL_CLK))) - 2;
    div <= std_logic_vector(to_unsigned(scl_div, div'length));
    sda_out <= 'H';
    --scl <= 'H';
    thalf := scl_div * 2;
    scycle_counter <= 0;
    report "Done. SCL_DIV set to " & integer'image(scl_div) & ".";
    wait for 1 us;
    reset <= '0'; 
    report "Using a SCL of " & integer'image(SCL_CLK) & " kHz.";
    
    for COUNT in 0 to 31 loop
      wait for scl_div * 1 ns;
      
      -- check if the hardware is ready:
      if iic_ready = '0' then
        wait until iic_ready = '1';
      end if;
      assert iic_ready = '1' report "Hardware not ready! Test failed after cycle: " 
				      & integer'image(to_integer(cycle_counter - 1));
    
      -- prepare transaction & determine which test will be run:
      crt_ctrl := start_controls;
      tb_data <= databytes(to_integer(cycle_counter(2 downto 0)));
      data_tx <= databytes(to_integer(cycle_counter(2 downto 0)));
      
      -- start transaction:
      control <= crt_ctrl; -- set the control bits
      wait until iic_ready = '0'; -- and let the simulation start
      
      -- check for start bit:
      wait until sda_in = '0';
      assert scl = 'H' report "Start bit was sent too late. sda => 0 while scl = 0";
      wait until scl = '0';
      assert sda_in = '0' report "Start bit was 'stopped' too early. sda => 1 while scl = 1";
           
      -- check if the address is sent correctly:
      for BITCOUNT in 0 to 7 loop
        wait until scl = 'H';
        wait for scl_div * 1 ns;
        assert sda_in = tb_data(7 - BITCOUNT) report "Received " & std_logic'image(sda_in)
            & ", Bit " & integer'image(BITCOUNT) & " of address " 
            & integer'image(to_integer(unsigned(tb_data)));
        wait until scl = '0';
      end loop; 
      
      -- check if the hardware is in the correct wait state
      if waiting_sw = '0' then
        wait until waiting_sw = '1';
      end if;
      
      -- prepare the next transaction
      tb_data <= databytes(7 - to_integer(cycle_counter(2 downto 0)));
      if cycle_counter(4) = '1' then
        crt_ctrl := mid_controls or "000100";
      else
        crt_ctrl := mid_controls;
        data_tx <= databytes(7 - to_integer(cycle_counter(2 downto 0)));
      end if;
      if cycle_counter(3 downto 1) = TC_MASTER_ACK then
        crt_ctrl := crt_ctrl or "100000";
      end if;
      
      -- start the next transaction
      control <= crt_ctrl;
      wait until waiting_sw = '0';
      -- disable the "data_ready" control signal
      control <= crt_ctrl and "101111";

      -- check for master ack (if needed), else ...
      if cycle_counter(3 downto 1) = TC_MASTER_ACK  then
        wait until scl = 'H';
        wait for scl_div * 1 ns;
        assert sda_in = '0' report "Master acknowledge was not sent correctly!";
      else -- ... send an acknowledge or don't
        if cycle_counter(0) = '0' then -- send an acknowledge
          sda_out <= '0';
          wait until scl = 'H';
          wait until scl = '0';
          sda_out <= 'H';
        else -- don't send an acknowledge
          wait until scl = 'H';
          wait until scl = '0';
        end if;
      end if; 
            
      -- send/check the data byte; 
      if cycle_counter(4) = '1' then -- switch for read/write
        -- send every bit
        for BITCOUNT in 0 to 7 loop
          wait for scl_div * 1 ns;
          sda_out <= tb_data(7 - BITCOUNT);
          -- check clock stretching behaviour:
          if cycle_counter(3 downto 1) = TC_CLOCK_STRETCHING then
            -- very long stretching
            if cycle_counter(0) = '1' then
              wait until scl = 'H';
              scl <= '0';
              wait for scl_div * 100 ns;
              scl <= 'H';
            else -- very short stretching
              wait until scl = 'H';
              scl <= '0';
              wait for scl_div * 1 ns;
              scl <= 'H';
            end if;
          else -- no clock stretching
            wait until scl = 'H';
          end if;
          if BITCOUNT < 7 then
            wait until scl = '0';
          else
            wait until waiting_sw = '1';
          end if;
        end loop;
        sda_out <= 'H';
        -- check if the byte was received correctly:
        if io_ready = '0' then
          wait until io_ready = '1';
        end if;
        wait for scl_div * 1 ns;
        assert data_rx = tb_data report "Sent " & integer'image(to_integer(unsigned(tb_data)))
              & " but HW got " & integer'image(to_integer(unsigned(tb_data)));
      else
        -- check every sent bit
        for BITCOUNT in 0 to 7 loop
          -- check clock stretching behaviour:
          if cycle_counter(3 downto 1) = TC_CLOCK_STRETCHING then
            -- very long stretching
            if cycle_counter(0) = '1' then
              wait until scl = 'H';
              scl <= '0';
              wait for scl_div * 100 ns;
              scl <= 'H';
            else -- very short stretching
              wait until scl = 'H';
              scl <= '0';
              wait for scl_div * 1 ns;
              scl <= 'H';
            end if;
          else -- no clock stretching
            wait until scl = 'H';
          end if;
          wait for scl_div * 1 ns;
          assert sda_in = tb_data(7 - BITCOUNT) report "Received " & std_logic'image(sda_in)
              & " for Bit " & integer'image(BITCOUNT) & " of Byte " 
              & integer'image(to_integer(unsigned(tb_data)));
          wait until scl = '0';
        end loop;
      end if;
          
      -- check / wait for the hardware to be in the correct wait state
      if waiting_sw = '0' then
        wait until waiting_sw = '1';
      end if;
      
      -- if the test is for multiple bytes, continue with more reads/writes
      if cycle_counter(3 downto 2) = TC_MULTI_BYTE then
        for MBCOUNT in 0 to 1 loop
        
          -- check if the last acknowledge was received correctly
          -- do we even need to check for an acknowledge (write)?
          if cycle_counter(4) = '0' then
          -- depending on if an acknowledge was sent, 
            -- check if the hardware state matches 
            assert (ackrec xor cycle_counter(0)) = '1' 
              report "Acknowledge was not received correctly after address in cycle "
                & integer'image(COUNT);
          end if;
        
          -- prepare the next transaction
          tb_data <= databytes((7 - to_integer(cycle_counter(2 downto 0)) + MBCOUNT));
          if cycle_counter(4) = '1' then
            crt_ctrl := mid_controls or "000100";
          else
            crt_ctrl := mid_controls;
            data_tx <= databytes((7 - to_integer(cycle_counter(2 downto 0)) + MBCOUNT));
          end if;
          
          -- start the next read/write
          control <= crt_ctrl;
          wait until waiting_sw = '0';
          -- disable the "data_ready" control signal
          control <= crt_ctrl and "101111";

          -- send the (N)ACK
          if cycle_counter(0) = '0' then -- send an acknowledge
            sda_out <= '0';
            wait until scl = 'H';
            wait until scl = '0';
            sda_out <= 'H';
          else -- don't send an acknowledge
            wait until scl = 'H';
            wait until scl = '0';
          end if;
                
          -- send/check the data byte; 
          if cycle_counter(4) = '1' then -- switch for read/write
            -- send every bit
            for BITCOUNT in 0 to 7 loop
              wait for scl_div * 1 ns;
              sda_out <= tb_data(7 - BITCOUNT);
              wait until scl = 'H';
              if BITCOUNT < 7 then
                wait until scl = '0';
              else
                wait until waiting_sw = '1';
              end if;
            end loop;
            sda_out <= 'H';
            -- check if the byte was received correctly:
            if io_ready = '0' then
              wait until io_ready = '1';
            end if;
            wait for scl_div * 1 ns;
            assert data_rx = tb_data report "Sent " & integer'image(to_integer(unsigned(tb_data)))
                  & " but HW got " & integer'image(to_integer(unsigned(tb_data)));
          else
            -- check every sent bit
            for BITCOUNT in 0 to 7 loop
              wait until scl = 'H';
              wait for scl_div * 1 ns;
              assert sda_in = tb_data(7 - BITCOUNT) report "Received " & std_logic'image(sda_in)
                  & " for Bit " & integer'image(BITCOUNT) & " of Byte " 
                  & integer'image(to_integer(unsigned(tb_data)));
              wait until scl = '0';
            end loop;
          end if;
          
          -- check if the hardware is in the correct wait state
          if waiting_sw = '0' then
            wait until waiting_sw = '1';
          end if;
          
        end loop;
      else
        -- check if the previous acknowledge was received correctly
        -- do we even need to check for an acknowledge (write & no master ack)?
        if cycle_counter(4) = '0' and not (cycle_counter(3 downto 1) = TC_MASTER_ACK) then
          -- depending on if an acknowledge was sent, 
          -- check if the hardware state matches 
          assert (ackrec xor cycle_counter(0)) = '1' 
            report "Acknowledge was not received correctly after address in cycle "
              & integer'image(COUNT);
        end if;
      end if;
      
      -- prepare to stop the current transaction
      crt_ctrl := stop_controls;
      
      -- stop the transaction
      control <= crt_ctrl;
      wait until waiting_sw = '0';
          
      -- check/send the last acknowledgement:
      if cycle_counter(4) = '0' then
        -- send NACK
        if cycle_counter(0) = '0' then -- send an acknowledge
          sda_out <= '0';
          wait until scl = 'H';
          wait until scl = '0';
          sda_out <= 'H';
        else -- don't send an acknowledge
          wait until scl = 'H';
          wait until scl = '0';
        end if;
      else -- check for the NACK after last read:
        wait until scl = 'H';
        assert sda_in = '1' report "NACK after last read of cycle: "
          & integer'image(COUNT) & " was not sent correctly!";
        wait until scl = '0';
      end if;
    
      -- check for the stop bit
      wait until scl = 'H';
      assert sda_in = '0' report "Stop bit wasn't sent correctly (scl => 1, sda = 1)"
                      & " in cycle " & integer'image(COUNT);
      wait until sda_in = '1';
      assert scl = 'H' report "Stop bit was held to long (sda => 1, scl = 0)"
                      & " in cycle " & integer'image(COUNT);
      
      -- wait for the hardware to enter the ready state
      if iic_ready = '0' then
        wait until iic_ready = '1';
      end if;
      
      -- check if the last acknowledge was received correctly
      -- do we even need to check for an acknowledge (write)?
      if cycle_counter(4) = '0' then
      -- depending on if an acknowledge was sent, 
        -- check if the hardware state matches 
        assert (ackrec xor cycle_counter(0)) = '1' 
          report "Acknowledge was not received correctly after address in cycle "
            & integer'image(COUNT);
      end if;
      report "Cycle " & integer'image(COUNT) & " finished.";
      -- cycle done. NEXT!
      cycle_counter := cycle_counter + 1;
      scycle_counter <= to_integer(cycle_counter);
    end loop;

    report "+~~~~~~~~~~~~~~~~~~~~~~+";
    report "| Simulation finished! |";
    report "+~~~~~~~~~~~~~~~~~~~~~~+";
    wait for 1 us;
    sim_end <= '1';
    wait;
  end process;

end architecture;


-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-- Generic testbench
-- This testbench runs tests with every possible byte combination.
-- Tests for each byte: Simple write, simple read, 
-- write and read with master acknowledge 
-- and write and read with clock stretching.

architecture testbench_generic of as_iic_tb is

constant SCL_DIV_WIDTH : integer := 13; -- serial bus clock accuracy
constant SYS_CLK : integer := 500;      -- in MHz; maximum of 500 MHz 
constant SCL_CLK : integer := 25000;    -- in kHz. This value is used to calculate the value of scl_div
constant BYTE_COUNT : integer := 300;   -- Number of bytes to test with, starting from 0

constant TC_MASTER_ACK : unsigned := "01";
constant TC_CLOCK_STRETCHING : unsigned := "10";

component as_iic is
  generic(
    SCL_DIV_REGISTER_WIDTH : integer );
  port(
    Clk   : in std_logic;
    Reset : in std_logic;
  
    SDA : inout std_logic;
    SCL : inout std_logic;
  
    control : in std_logic_vector(15 downto 0);
    control_reset : out std_logic_vector(15 downto 0);
    status : out std_logic_vector(15 downto 0);
    scl_div_data_tx : in std_logic_vector(31 downto 0));
end component;

signal clk, reset, sda, scl : std_logic;

signal data_rx, data_tx, tb_data : std_logic_vector(7 downto 0);
signal control : std_logic_vector(5 downto 0);
signal status : std_logic_vector(5 downto 0);
signal div : std_logic_vector(SCL_DIV_WIDTH - 1 downto 0);

signal sim_end : std_logic;
signal sda_in, sda_out : std_logic;

signal data_zero : std_logic_vector(23 downto 0);
signal scl_div_zero : std_logic_vector(23 downto SCL_DIV_WIDTH);
signal status_zero : std_logic_vector(1 downto 0);

signal iic_ready, io_ready, bus_active, ackrec, stalled, waiting_sw : std_logic;

signal scycle_counter : integer;

begin
  -- Data Register logic
  
  data_rx <= (others => 'L');
  scl_div_zero <= (others => '0');
  status_zero <= (others => '0');

-- controls: ack_mod, data_ready, reset, rw, end, start

  sda_in <= '1' when sda = 'H' else sda;
  sda <= 'H' when sda_out = '1' else sda_out; 
  
  test_iic : as_iic
    generic map(
       SCL_DIV_REGISTER_WIDTH => SCL_DIV_WIDTH)
    port map(
      Clk => clk,
      Reset => reset,
      SDA => sda,
      SCL => scl,
      control(15 downto 6) => (others => '0'),
      control(5 downto 0) => control,
      status(15 downto 8) => data_rx,
      status(7 downto 6) => status_zero,
      status(5 downto 0) => status,
      scl_div_data_tx(31 downto 24) => data_tx,
      scl_div_data_tx(23 downto SCL_DIV_WIDTH) => scl_div_zero,
      scl_div_data_tx(SCL_DIV_WIDTH - 1 downto 0) => div);
  
  iic_ready <= status(0);
  io_ready <= status(1);
  bus_active <= status(2);
  ackrec <= status(3);
  stalled <= status(4);
  waiting_sw <= status(5);

  --! Clock generator process:
  clkgen : process
  variable clk_waitmult : integer;
  begin
    clk_waitmult := 500 / SYS_CLK; 
    report "Clock simulation started! Simulating " & integer'image(SYS_CLK) & " MHz clock. Using T/2 of " & integer'image(clk_waitmult) & " ns.";
  
    -- Clock loop:
    while not (sim_end = '1') loop 
      clk <= '1';
      wait for clk_waitmult * 1 ns;
      clk <= '0';
      wait for clk_waitmult * 1 ns;
    end loop;
    wait;
  end process;

--! Main process for the generic testbench:
  generic_testbench_process : process
    variable wait_mult : integer;
    variable scl_div : integer;
    variable crt_ctrl : std_logic_vector(5 downto 0);

    variable databyte : std_logic_vector(7 downto 0);
    variable cycle_counter : unsigned(2 downto 0);
    variable byte_counter, tr_bytes, bc_temp: integer;
    variable start_controls, mid_controls, stop_controls : std_logic_vector(5 downto 0);
    
  begin
    
    -- Initialize testbench
    report "Initializing testbench environment...";
    cycle_counter :=  (others => '0');
    byte_counter :=   0;
    start_controls := "000001";
    mid_controls :=   "010001";
    stop_controls :=  "010010";
    databyte := (others => '0');
    data_tx <= (others => '0');
    tb_data <= (others => '0');
    reset <= '1';
    scl_div := ((SYS_CLK * 1000) / (4 * (SCL_CLK))) - 2;
    div <= std_logic_vector(to_unsigned(scl_div, div'length));
    sda_out <= 'H';
    scl <= 'H';
    scycle_counter <= 0;
    report "Done. SCL_DIV set to " & integer'image(scl_div) & ".";
    wait for 1 us;
    reset <= '0'; 
    report "Using a SCL of " & integer'image(SCL_CLK) & " kHz.";
    
    for byte_counter in 0 to BYTE_COUNT loop
      cycle_counter := (others => '0');
      for TESTNR in 0 to 5 loop
      
        -- check if the hardware is ready:
        if iic_ready = '0' then
          wait until iic_ready = '1';
        end if;
        assert iic_ready = '1' report "Hardware not ready! Failed in test: " 
                & integer'image(TESTNR) & " for byte: " & integer'image(byte_counter);
      
        -- prepare transaction & determine which test will be run:
        crt_ctrl := start_controls;
        tb_data <= std_logic_vector(to_unsigned(byte_counter mod 256, 8));
        data_tx <= std_logic_vector(to_unsigned(byte_counter mod 256, 8));
        
        -- start transaction:
        control <= crt_ctrl; -- set the control bits
        wait until iic_ready = '0'; -- and let the simulation start
        
        -- check for start bit:
        wait until sda_in = '0';
        assert scl = 'H' report "Start bit was sent too late. sda => 0 while scl = 0";
        wait until scl = '0';
        assert sda_in = '0' report "Start bit was 'stopped' too early. sda => 1 while scl = 1";
             
        -- check if the address is sent correctly:
        for BITCOUNT in 0 to 7 loop
          wait until scl = 'H';
          wait for scl_div * 1 ns;
          assert sda_in = tb_data(7 - BITCOUNT) report "Received " & std_logic'image(sda_in)
              & ", Bit " & integer'image(BITCOUNT) & " of address "
              & integer'image(to_integer(unsigned(tb_data)));
          wait until scl = '0';
        end loop;
        
        -- check if the hardware is in the correct wait state
        if waiting_sw = '0' then
          wait until waiting_sw = '1';
        end if;
        
        -- number of bytes this in this transmission
        bc_temp := byte_counter;
        tr_bytes := 0;
        for N in 0 to 3 loop
          if bc_temp > 0 then tr_bytes := tr_bytes + 1; end if;
          bc_temp := bc_temp / 8;
        end loop;
        
        bc_temp := 8;
        for TRBYTE_COUNT in 0 to tr_bytes loop
          -- prepare the next transaction
          tb_data <= std_logic_vector(to_unsigned((byte_counter / bc_temp) mod 256, 8));
          if cycle_counter(0) = '1' then
            crt_ctrl := mid_controls or "000100";
          else
            crt_ctrl := mid_controls;
            data_tx <= std_logic_vector(to_unsigned((byte_counter / bc_temp) mod 256, 8));
          end if;
          if cycle_counter(2 downto 1) = TC_MASTER_ACK then
            crt_ctrl := crt_ctrl or "100000";
          end if;
          
          -- start the next transaction
          control <= crt_ctrl;
          wait until waiting_sw = '0';
          -- disable the "data_ready" control signal
          control <= crt_ctrl and "101111";

          -- check for acknowledge (write or master ack), else ...
          if (cycle_counter(0) = '1' or cycle_counter(2 downto 1) = TC_MASTER_ACK) and TRBYTE_COUNT > 0  then
            wait until scl = 'H';
            wait for scl_div * 1 ns;
            assert sda_in = '0' report "Acknowledge was not sent correctly in test "
                  & integer'image(TESTNR) & " for byte " & integer'image(byte_counter);
            wait until scl = '0';
          else -- ... send an acknowledge
            sda_out <= '0';
            wait until scl = 'H';
            wait until scl = '0';
            sda_out <= 'H';
          end if; 
                
          -- send/check the data byte; 
          if cycle_counter(0) = '1' then -- switch for read/write
            -- send every bit
            for BITCOUNT in 0 to 7 loop
              wait for scl_div * 1 ns;
              sda_out <= tb_data(7 - BITCOUNT);
              -- check clock stretching behaviour:
              if cycle_counter(2 downto 1) = TC_CLOCK_STRETCHING then
                wait until scl = 'H';
                scl <= '0';
                wait for scl_div * 50 ns;
                scl <= 'H';
              else -- no clock stretching
                wait until scl = 'H';
              end if;
              if BITCOUNT < 7 then
                wait until scl = '0';
              else
                wait until waiting_sw = '1';
              end if;
            end loop;
            sda_out <= 'H';
            -- check if the byte was received correctly:
            if io_ready = '0' then
              wait until io_ready = '1';
            end if;
            wait for scl_div * 1 ns;
            assert data_rx = tb_data report "Sent " & integer'image(to_integer(unsigned(tb_data)))
                  & " but HW got " & integer'image(to_integer(unsigned(data_rx)));
          else
            -- check every sent bit
            for BITCOUNT in 0 to 7 loop
              -- check clock stretching behaviour:
              if cycle_counter(2 downto 1) = TC_CLOCK_STRETCHING then
                wait until scl = 'H';
                scl <= '0';
                wait for scl_div * 50 ns;
                scl <= 'H';
              else -- no clock stretching
                wait until scl = 'H';
              end if;
              wait for scl_div * 1 ns;
              assert sda_in = tb_data(7 - BITCOUNT) report "Received " & std_logic'image(sda_in)
                  & " for Bit " & integer'image(BITCOUNT) & " in test "
                  & integer'image(TESTNR) & " for byte " & integer'image(byte_counter);
              wait until scl = '0';
            end loop;
          end if;
              
          -- check / wait for the hardware to be in the correct wait state
          if waiting_sw = '0' then
            wait until waiting_sw = '1';
          end if;
          bc_temp := bc_temp * 2;
        end loop;
        
        -- check if the previous acknowledge was received correctly
        -- do we even need to check for an acknowledge (write & no master ack)?
        if cycle_counter(0) = '1' and not (cycle_counter(2 downto 1) = TC_MASTER_ACK) then
          -- depending on if an acknowledge was sent, 
          -- check if the hardware state matches 
          assert ackrec = '1' 
            report "Acknowledge was not received correctly after address in test "
              & integer'image(TESTNR) & " for byte " & integer'image(byte_counter);
        end if;
          
        -- prepare to stop the current transaction
        crt_ctrl := stop_controls;
        
        -- stop the transaction
        control <= crt_ctrl;
        wait until waiting_sw = '0';
            
        -- check/send the last acknowledgement:
        if cycle_counter(0) = '1' then
          -- send ACK
          sda_out <= '0';
          wait until scl = 'H';
          wait until scl = '0';
          sda_out <= 'H';
        else -- check for the acknowledge
          wait until scl = 'H';
          wait until scl = '0';
        end if;
      
        -- check for the stop bit
        wait until scl = 'H';
        assert sda_in = '0' report "Stop bit wasn't sent correctly (scl => 1, sda = 1)"
                        & " in test " & integer'image(TESTNR) & " for byte " 
                        & integer'image(byte_counter);
        wait until sda_in = '1';
        assert scl = 'H' report "Stop bit was held to long (sda => 1, scl = 0)"
                        & " in test " & integer'image(TESTNR) & " for byte " 
                        & integer'image(byte_counter);
        
        -- wait for the hardware to enter the ready state
        if iic_ready = '0' then
          wait until iic_ready = '1';
        end if;
        
        -- check if the last acknowledge was received correctly
        -- do we even need to check for an acknowledge (write)?
        if cycle_counter(0) = '1' and not (cycle_counter(2 downto 1) = TC_MASTER_ACK) then
        -- depending on if an acknowledge was sent, 
          -- check if the hardware state matches 
          assert ackrec = '1' 
            report "Acknowledge was not received correctly in test "
              & integer'image(TESTNR) & " for byte " & integer'image(byte_counter);
        end if;
        -- cycle done. NEXT!
        cycle_counter := cycle_counter + 1;
        scycle_counter <= to_integer(cycle_counter);
      end loop;
      report "Tests for byte " & integer'image(byte_counter) & " finished.";
    end loop;

    report "+~~~~~~~~~~~~~~~~~~~~~~+";
    report "| Simulation finished! |";
    report "+~~~~~~~~~~~~~~~~~~~~~~+";
    wait for 1 us;
    sim_end <= '1';
    wait;
  end process;

end architecture;


-- vim: et ts=2 sw=2
