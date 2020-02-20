----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework.
--  Copyright (C) Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
--
-- Entity:        AS_MYFILTER
--
-- Company:       Efficient Embedded Systems Group
--                University of Applied Sciences, Augsburg, Germany
--
-- Author:        Michael Schaeferling, Gundolf Kiefer
--
-- Description:   This is a template module for your own ideas.
--                Functionality may be controlled by setting the
--                configuration register e.g. using a driver.
--
--                Implementation: 3x3 kernel filter example
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

library asterics;
use asterics.helpers.all;


entity AS_MYFILTER is
  generic (
    DIN_WIDTH    : integer := 8;
    DOUT_0_WIDTH : integer := 8;
    DOUT_1_WIDTH : integer := 8;

    RES_X : integer := 640;
    RES_Y : integer := 480
  );
  port (

    -- General ports ...
    clk   : in  std_logic;    -- Clock
    reset : in  std_logic;    -- Reset
    ready : out std_logic;    -- Ready: Must be set as soon as the module is ready to operate after reset

    --! Slave register interface
    slv_ctrl_reg : in slv_reg_data(0 to 11);
    slv_status_reg : out slv_reg_data(0 to 11);
    slv_reg_modify : out std_logic_vector(0 to 11);
    slv_reg_config : out slv_reg_config_table(0 to 11);

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
    data_error_out_1 : out std_logic
  );
end entity;


--! @}



architecture RTL of AS_MYFILTER is

  -- Declarations for sliding window buffer...
  constant WIN_W : integer := 3;        -- width of the sliding window
  constant WIN_H : integer := 3;        -- height of the sliding window
  constant WBB_STROBE : integer := 8;   -- bit in which the strobe signal is transported

  -- Slave register configuration:
  -- Allows for "dynamic" configuration of slave registers
  -- Possible values and what they mean: 
  -- "00": Register "off". Register will not be available and won't be implemented -> No hardware resource utilization.
  -- "01": HW -> SW, Status register only. Data transport from hardware to software. HW can only write, SW can only read.
  -- "10": HW <- SW, Control register only. Data transport from software to hardware. HW can only read, SW can only write.
  -- "11": HW <=> SW, Combined Read/Write register. Data transport in both directions. ! Higher FPGA resource utilization !
  --       When both sides attempt to write simultaniously, only the HW gets to write.
  --       These registers use both the slv_ctrl_reg and slv_status_reg ports for communication.
  constant slave_register_configuration : slv_reg_config_table(0 to 11) := ("11","10","10","10","10","10","10","10","10","10","10","10");

  --! Signal used as an intermidiate to apply the control_reset logic and then update the register
  signal control_new : std_logic_vector(15 downto 0);

  -- control
  -- | 15 ...    1 |         0          |
  -- |     n.c.    |       flush        |
  -- |_____________|____________________|
  
  signal control       : std_logic_vector(15 downto 0);
  signal control_reset : std_logic_vector(15 downto 0);
  
  -- state
  -- | 15 ...    6 |        5        |        4        |        3        |        2        |        1        |        0        |
  -- |     n.c.    |     stall_1     |     stall_0     |      ready      |    strobe_in    | flush not done  |    flushing     |
  -- |_____________|_________________|_________________|_________________|_________________|_________________|_________________|
  
  signal state         : std_logic_vector(15 downto 0);

  type winbuf_t is array (0 to RES_X * (WIN_H-1) + WIN_W - 1) of std_logic_vector (8 downto 0);
  signal winbuf : winbuf_t;

  function pixel_idx (dx, dy: in integer) return integer is
  begin
    return ((WIN_H-1) / 2 + dy) * RES_X + ((WIN_W-1) / 2 + dx);
  end;

  -- Control and status bits mapped to slave registers...
  signal ctrl_reg_flush, status_reg_flush_ndone : std_logic;



begin


slv_reg_config <= slave_register_configuration;

control <= slv_ctrl_reg(0)(31 downto 16);
slv_status_reg(0) <= control_new & state;

-- Ten usable registers (SW -> HW) configurable via constant 'slave_register_configuration'!
-- slv_control_reg(1 to 11);

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

  control_reset <= (others => '0');

  -- Map I/O register bits to named signals ...
  state <= (
      0 => ctrl_reg_flush,
      1 => status_reg_flush_ndone,
      2 => strobe_in,
      3 => not reset,
      4 => stall_in_0,
      5 => stall_in_1,
      others => '0'
    );


  ctrl_reg_flush <= control(0);


  -- Unused ports of out ports #0 and #1 ...
  hsync_out_0 <= hsync_in;
  vsync_out_0 <= vsync_in;
  vcomplete_out_0 <= vcomplete_in;
  data_error_out_0 <= data_error_in;

  hsync_out_1 <= '0';
  vsync_out_1 <= '0';
  vcomplete_out_1 <= '0';
  data_error_out_1 <= '0';


  -- General signals ...
  ready <= not (reset);
  stall_out <= stall_in_0 or stall_in_1;

  -- Path 0: Direct feed-through from in port to out port #0
  strobe_out_0 <= strobe_in;
  data_out_0 <= data_in;


  -- Path 1: Path with user logic ...
  process (clk)
    variable i, dx, dy: integer;
    variable sum_x : unsigned (15 downto 0);
    variable sum_y : unsigned (15 downto 0);
    variable sum : unsigned (15 downto 0);
      -- intermediate variable to accumulate the filter result (adapt width as necessary)
    constant WEIGHT_SHIFT: integer := 0;
      -- global weight factor: the final filter result is divided by 2^WEIGHT_SHIFT;
      -- must be adapted to the filter function!
  begin
    if rising_edge (clk) then

      -- Move sliding window buffer forward...
      if ((strobe_in = '1' or ctrl_reg_flush = '1') and (stall_in_1 = '0')) then
        winbuf (1 to winbuf'high) <= winbuf (0 to winbuf'high - 1);
        winbuf (0) <= (strobe_in and not ctrl_reg_flush) & data_in;
      end if;

      -- Reset (must dominate over sliding window buffer forwarding) ...
      if reset = '1' then
        winbuf <= (others => (WBB_STROBE => '0', others => '-'));
      end if;

      -- Compute filter...
      --   Window buffer size must be set accordingly.
      sum_x := (others => '0');
      for dy in 0 to 0 loop
        for dx in -1 to -1 loop
          sum_x := sum_x - unsigned (winbuf (pixel_idx (dx, dy)) (7 downto 0));
        end loop;
        for dx in 1 to 1 loop
          sum_x := sum_x + unsigned (winbuf (pixel_idx (dx, dy)) (7 downto 0));
        end loop;
      end loop;

      sum_y := (others => '0');
      for dx in 0 to 0 loop
        for dy in -1 to -1 loop
          sum_y := sum_y - unsigned (winbuf (pixel_idx (dx, dy)) (7 downto 0));
        end loop;
        for dy in 1 to 1 loop
          sum_y := sum_y + unsigned (winbuf (pixel_idx (dx, dy)) (7 downto 0));
        end loop;
      end loop;

      -- Divide by 2^WEIGHT_SHIFT ...
      sum_x(sum_x'left-WEIGHT_SHIFT-1 downto 0) := sum_x (sum_x'left-1 downto WEIGHT_SHIFT);
      sum_x(sum_x'left-1 downto sum_x'left-WEIGHT_SHIFT) := (others => sum_x(sum_x'left));
      
      sum_y(sum_y'left-WEIGHT_SHIFT-1 downto 0) := sum_y (sum_y'left-1 downto WEIGHT_SHIFT);
      sum_y(sum_y'left-1 downto sum_y'left-WEIGHT_SHIFT) := (others => sum_y(sum_y'left));

      --sum := unsigned( abs(signed(sum_x)));
      sum := unsigned( abs(signed(sum_x)) + abs(signed(sum_y)) );

      -- Saturate the result to the range 0 .. 255 ...
      if sum(sum'left) = '1' then   -- < 0?
        sum (7 downto 0) := (others => '0');  -- 0
      elsif sum(sum'left downto 8) /= to_unsigned (0, sum'left - 8) then
        sum (7 downto 0) := (others => '1');  -- 255
      end if;

      -- Output (registered) ...
      strobe_out_1 <= winbuf (pixel_idx (0, 0)) (WBB_STROBE) and (strobe_in or ctrl_reg_flush) and not(stall_in_1);
      data_out_1 <= std_logic_vector (sum (7 downto 0));

      status_reg_flush_ndone <=  winbuf (pixel_idx (0, 0)) (WBB_STROBE);

    end if;
  end process;


end RTL;

