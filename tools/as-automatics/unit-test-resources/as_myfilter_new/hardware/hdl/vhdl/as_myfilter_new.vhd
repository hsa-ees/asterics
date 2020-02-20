----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework.
--  Copyright (C) Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:        as_myfilter
--
-- Company:       Efficient Embedded Systems Group
--                University of Applied Sciences, Augsburg, Germany
--
-- Author:        Michael Schaeferling, Gundolf Kiefer
--
-- Description:    This is a template module for your own ideas.
--                 Functionality may be controlled by setting the
--                 configuration register e.g. using a driver.
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
--! @file  as_myfilter.vhd
--! @brief Placeholder module which leaves room for implementing own ideas.
----------------------------------------------------------------------------------


--! @defgroup as_myfilter as_myfilter
--! @{


library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

--library asterics;
use work.helpers.all;


entity as_myfilter_new is
  generic (
    REG_DATA_WIDTH : integer := 32; -- Width of a slave register
    DIN_WIDTH    : integer := 8;
    DOUT_0_WIDTH : integer := 8;
    DOUT_1_WIDTH : integer := 8;

    RES_X : integer := 640;
    RES_Y : integer := 480
  );
  port (

    -- General ports
    clk   : in  std_logic;    -- Clock
    reset : in  std_logic;    -- Reset
    ready : out std_logic;    -- Ready: Must be set as soon as the module is ready to operate after reset

    -- AS_STREAM in port ...
    strobe_in     : in  std_logic;
    data_in       : in  std_logic_vector(DIN_WIDTH-1 downto 0);
    hsync_in      : in  std_logic;
    vsync_in      : in  std_logic;
    stall_out     : out std_logic;
    vcomplete_in  : in  std_logic;
    data_error_in : in  std_logic;

    -- AS_STREAM out port #0 ...
    strobe_out_0     : out std_logic;
    data_out_0       : out std_logic_vector(DOUT_0_WIDTH-1 downto 0);
    hsync_out_0      : out std_logic;
    vsync_out_0      : out std_logic;
    stall_in_0       : in  std_logic;
    vcomplete_out_0  : out std_logic;
    data_error_out_0 : out std_logic;

    -- AS_STREAM out port #1 ...
    strobe_out_1     : out std_logic;
    data_out_1       : out std_logic_vector(DOUT_1_WIDTH-1 downto 0);
    hsync_out_1      : out std_logic;
    vsync_out_1      : out std_logic;
    stall_in_1       : in  std_logic;
    vcomplete_out_1  : out std_logic;
    data_error_out_1 : out std_logic;
    
    --! Slave register interface:
    --! Control registers. SW -> HW data transport
    slv_ctrl_reg_par0 : in slv_reg_data(0 to 8);
    --! State registers. HW -> SW data transport
    slv_status_reg_par0 : out slv_reg_data(0 to 8);
    --! Aquivalent to a write enable signal. When HW want's to write into a register, it needs to pulse this signal.
    slv_reg_modify_par0 : out std_logic_vector(0 to 8);
    --! Slave register configuration table. Used to "configure" the slave registers (unused during "runtime" -> No dynamic data transport)
    slv_reg_config_par0 : out slv_reg_config_table(0 to 8);
	
	
    --! Control registers. SW -> HW data transport
    slv_ctrl_reg_par1 : in slv_reg_data(0 to 14);
    --! State registers. HW -> SW data transport
    slv_status_reg_par1 : out slv_reg_data(0 to 14);
    --! Aquivalent to a write enable signal. When HW want's to write into a register, it needs to pulse this signal.
    slv_reg_modify_par1 : out std_logic_vector(0 to 14);
    --! Slave register configuration table. Used to "configure" the slave registers (unused during "runtime" -> No dynamic data transport)
    slv_reg_config_par1 : out slv_reg_config_table(0 to 14)
  );
end entity;

--! @}

architecture RTL of AS_MYFILTER is

  -- Template for slave regs...
  --~ mod_reset <= slreg_in (0) (0);
  --~ -- ...
  --~ ioreg_out <= (others => (others => '-'));
  --~ ioreg_out (0) (0) <= mod_ready;
  --~ -- ...

  -- Declarations for sliding window buffer...
  constant WIN_W : integer := 7;
  constant WIN_H : integer := 7;
  constant WBB_STROBE : integer := 8;    -- bit in which the strobe signal is transported
  
  -- The amount of bits a result is shifted right. This value depends on the filter size and weights.
  constant SUM_SHIFT: integer := 4;

  type winbuf_t is array (0 to RES_X * (WIN_H-1) + WIN_W - 1) of std_logic_vector (8 downto 0);
  signal winbuf : winbuf_t;

  signal flush_in, flush_ndone: std_logic;
  
  -- Slave register configuration:
  -- Allows for "dynamic" configuration of slave registers
  -- Possible values and what they mean: 
  -- "00": Register "off". Register will not be available and won't be implemented -> No hardware resource utilization.
  -- "01": From HW view: Status register. Data transport from hardware to software. HW can only write, SW can only read.
  -- "10": From HW view: Control register. Data transport from software to hardware. HW can only read, SW can only write.
  -- "11": Combined Read/Write register. Data transport in both directions. 
  --       When both sides attempt to write simultaniously, only the HW gets to write.
  --       These registers use both the slv_ctrl_reg and slv_state_reg ports for communication.
  constant slave_register_configuration_par0 : slv_reg_config_table(0 to 8) :=
                    ("11","10","10","10","10","10","10","10", -- Register 0  to 8
                     "10");-- Register 57 to 64
  
  constant slave_register_configuration_par1 : slv_reg_config_table(0 to 14) :=
                    ("11","10","10","10","10","10","10","10", -- Register 0  to 8
                     "10","10","10","10","11","11","11");-- Register 57 to 64
  
  --! Status of this hardware module
  signal state : std_logic_vector(15 downto 0);
  --! Control bits set by software
  signal control : std_logic_vector(15 downto 0);
  signal control_reset : std_logic_vector(15 downto 0);
  --! Signal used as an intermidiate to apply the control_reset logic and then update the register
  signal control_new : std_logic_vector(15 downto 0);
  
  --! Data registers set by software
  signal sw_register_0 : std_logic_vector(REG_DATA_WIDTH - 1 downto 0);
  signal sw_register_1 : std_logic_vector(REG_DATA_WIDTH - 1 downto 0);
  signal sw_register_2 : std_logic_vector(REG_DATA_WIDTH - 1 downto 0);
  signal sw_register_3 : std_logic_vector(REG_DATA_WIDTH - 1 downto 0);
  signal sw_register_4 : std_logic_vector(REG_DATA_WIDTH - 1 downto 0);
  signal sw_register_5 : std_logic_vector(REG_DATA_WIDTH - 1 downto 0);
  signal sw_register_6 : std_logic_vector(REG_DATA_WIDTH - 1 downto 0);
  signal sw_register_7 : std_logic_vector(REG_DATA_WIDTH - 1 downto 0);
  signal sw_register_8 : std_logic_vector(REG_DATA_WIDTH - 1 downto 0);
  signal sw_register_9 : std_logic_vector(REG_DATA_WIDTH - 1 downto 0);
  signal sw_register_10 : std_logic_vector(REG_DATA_WIDTH - 1 downto 0);
  
  function pixel_idx (dx, dy: in integer) return integer is
  begin
    return ((WIN_H-1) / 2 + dy) * RES_X + ((WIN_W-1) / 2 + dx);
  end;

begin
  -- Pass the register configuration table
  slv_reg_config <= slave_register_configuration;
  
  -- Update the combined status/control register
  slv_status_reg(0) <= control_new & state;
  
  -- Extract control bits
  control <= slv_ctrl_reg(0)(31 downto 16);
  
  -- Connect internal software written registers
  sw_register_0  <= slv_ctrl_reg(1);
  sw_register_1  <= slv_ctrl_reg(2);
  sw_register_2  <= slv_ctrl_reg(3);
  sw_register_3  <= slv_ctrl_reg(4);
  sw_register_4  <= slv_ctrl_reg(5);
  sw_register_5  <= slv_ctrl_reg(6);
  sw_register_6  <= slv_ctrl_reg(7);
  sw_register_7  <= slv_ctrl_reg(8);
  sw_register_8  <= slv_ctrl_reg(9);
  sw_register_9  <= slv_ctrl_reg(10);
  sw_register_10 <= slv_ctrl_reg(11);
  
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
  
  -- Unused ports of out ports #0 and #1 ...
  hsync_out_0 <= hsync_in;
  vsync_out_0 <= vsync_in;
  vcomplete_out_0 <= vcomplete_in;
  data_error_out_0 <= data_error_in;

  hsync_out_1 <= '0';
  vsync_out_1 <= '0';
  vcomplete_out_1 <= '0';
  data_error_out_1 <= '0';

  -- Handle general signals ...
  ready <= not (reset);
  stall_out <= stall_in_0 or stall_in_1;    -- no internal stall

  -- Generate status signals to software...
  state <= (0 => flush_in, 1 => flush_ndone, 2 => strobe_in, 4 => stall_in_0, 5 => stall_in_1, others => '0');
  flush_in <= control(0);
  
  -- Control reset (unused)
  control_reset <= (others => '0');

  -- Path 0: Direct feed-through from in port to out port #0
  strobe_out_0 <= strobe_in;
  data_out_0 <= data_in;

  -- Path 1: Path with user logic ...
  --~ strobe_out_1 <= strobe_in;
  --~ data_out_1 <= not data_in;

  process (clk)
    variable i, dx, dy: integer;
    variable sum : unsigned (15 downto 0);
  begin
    if rising_edge (clk) then

      -- Move sliding window buffer forward...
      if ((strobe_in = '1' or flush_in = '1') and (stall_in_1 = '0')) then
        winbuf (1 to winbuf'high) <= winbuf (0 to winbuf'high - 1);
        winbuf (0) <= (strobe_in and not flush_in) & data_in;
      end if;

      -- Reset (must dominate over SWB forwarding) ...
      if reset = '1' then
        winbuf <= (others => (WBB_STROBE => '0', others => '-'));
      end if;

      -- Compute filter...
      -- Window buffer size must be set accordingly
      sum := (others => '0');
      for dy in -3 to 3 loop
        for dx in 1 to 3 loop
          sum := sum + unsigned (winbuf (pixel_idx (dx, dy)) (7 downto 0));
          sum := sum - unsigned (winbuf (pixel_idx (-dx, dy)) (7 downto 0));
        end loop;
      end loop;


      -- Divide, saturate and add offset ...

      -- Divide by 2^RES_SHIFT
      sum(sum'left-SUM_SHIFT-1 downto 0) := sum (sum'left-1 downto SUM_SHIFT);
      sum(sum'left-1 downto sum'left-SUM_SHIFT) := (others => sum(sum'left));

      if sum(sum'left) = '0' then   -- positive...
        if sum (sum'left-1 downto 7) /= to_unsigned (0, sum'left - 7) then
          sum(7 downto 0) := (7 => '0', others => '1');   -- +127
        end if;
      else                          -- negative...
        if sum (sum'left-1 downto 7) /= unsigned (to_signed (-1, sum'left - 7)) then
          sum(7 downto 0) := (7 => '1', others => '0');   -- -128
        end if;
      end if;

      sum(7) := not sum(7);   -- add 128

      -- Output (registered) ...
      strobe_out_1 <= winbuf (pixel_idx (0, 0)) (WBB_STROBE) and (strobe_in or flush_in) and not(stall_in_1);
      data_out_1 <= std_logic_vector (sum (7 downto 0));

      flush_ndone <=  winbuf (pixel_idx (0, 0)) (WBB_STROBE);
    end if;
  end process;


end RTL;

