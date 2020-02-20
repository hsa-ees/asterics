----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework.
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
--
-- Entity:        AS_MYFILTER
--
-- Company:       Efficient Embedded Systems Group
--                University of Applied Sciences, Augsburg, Germany
--
-- Author:        Michael Schaeferling, Gundolf Kiefer, Philip Manke
--
-- Description:   This is a template module for your own ideas.
--                Functionality may be controlled by setting the
--                configuration register e.g. using a driver.
--
--                Implementation: 7x7 kernel filter example
--                                with pipelining
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
    DATA_WIDTH : integer := 8;
    RES_X : integer := 640;
    RES_Y : integer := 480
  );
  port (
    -- General ports:
    clk   : in  std_logic;    -- Clock
    reset : in  std_logic;    -- Reset
    ready : out std_logic;    -- Ready: Must be set as soon as the module is ready to operate after reset

    -- Slave register interface:
    slv_ctrl_reg   : in  slv_reg_data(0 to 11);
    slv_status_reg : out slv_reg_data(0 to 11);
    slv_reg_modify : out std_logic_vector(0 to 11);
    slv_reg_config : out slv_reg_config_table(0 to 11);

    -- AS_STREAM in port:
    strobe_in  : in  std_logic;
    data_in    : in  std_logic_vector(DATA_WIDTH - 1 downto 0);
    stall_out  : out std_logic;

    -- AS_STREAM out port:
    strobe_out : out std_logic;
    data_out   : out std_logic_vector(DATA_WIDTH - 1 downto 0);
    stall_in   : in  std_logic
  );
end entity;


--! @}



architecture RTL of AS_MYFILTER is

  -- Declarations for sliding window buffer:
  constant WIN_W : integer := 7;        -- width of the sliding window
  constant WIN_H : integer := 7;        -- height of the sliding window
  constant WBB_STROBE : integer := 8;   -- bit in which the strobe signal is transported

  -- Slave register configuration. Possible values and what they mean:
  --    AS_REG_NONE   : Register "off". Register will not be available and won't be implemented -> No hardware resource utilization.
  --    AS_REG_STATUS : HW -> SW,  Status register only. Data transport from hardware to software. HW can only write, SW can only read.
  --    AS_REG_CONTROL: HW <- SW,  Control register only. Data transport from software to hardware. HW can only read, SW can only write.
  --    AS_REG_BOTH   : HW <=> SW, Combined Read/Write register. Data transport in both directions. ! Higher FPGA resource utilization !
  --                                    When both sides attempt to write simultaniously, only the HW gets to write.
  --                                    These registers use both the slv_ctrl_reg and slv_status_reg ports for communication.
  constant slave_register_configuration : slv_reg_config_table(0 to 11)
        := (AS_REG_STATUS, AS_REG_CONTROL, others => AS_REG_NONE);
        --~ := (AS_REG_STATUS, AS_REG_CONTROL, others => AS_REG_STATUS);   -- WORKAROUND

  -- Control and status signals
  signal ready_int : std_logic;
  signal ctrl_reg_flush : std_logic;
  signal status_reg_flush_ndone : std_logic;

  -- Window buffer type: Data width is size of pixel data plus stored strobe signal
  type winbuf_t is array (0 to RES_X * (WIN_H-1) + WIN_W - 1) of std_logic_vector ((DATA_WIDTH - 1) + 1 downto 0);
  signal winbuf : winbuf_t;

  -- Function to calculate a pixel index inside the window buffer (winbuf)
  function pixel_idx (dx, dy: in integer) return integer is
  begin
    return ((WIN_H-1) / 2 + dy) * RES_X + ((WIN_W-1) / 2 + dx);
  end;

  -- Pipeline registers for partial sums
  type pixel_sum_x_t is array(-((WIN_H - 1) / 2) to ((WIN_H - 1) / 2)) of unsigned(15 downto 0);
  signal r_part_sum_x : pixel_sum_x_t;
  signal r_strobe_part_sum_x : std_logic;

begin


  -- Handle general ports ...
  ready_int <= not (reset);    -- Module is always ready on no reset
  ready <= ready_int;


  -- Handle slave registers ...
  --    Configuration ...
  slv_reg_config <= slave_register_configuration;

  --    Register 0 (state register) ...
  slv_status_reg(0) <= (
    0 => ctrl_reg_flush,
    1 => status_reg_flush_ndone,
    2 => strobe_in,
    3 => ready_int,
    4 => stall_in,
    others => '0'
  );
  slv_reg_modify(0) <= '1';     -- constantly update register 0 from HW

  --    Register 1 (control register) ...
  ctrl_reg_flush <= slv_ctrl_reg(1)(0);

  --   Additional registers can be configured by modifying the constant 'slave_register_configuration'
  --   Access via slv_control_reg(N) for data from SW and slv_status_reg(N) to send data to SW
  --   Notice: To update a status register, the associated slv_reg_modify(N) bit
  --           must be set to '1' for at least one clock cycle! (Can also set it to a constant '1')
  --   Examples:
  --     my_sw_data <= slv_control_reg(3);
  --     slv_status_reg(5) <= my_hw_data;
  --     slv_reg_modify(5) <= '1';


  -- Feed-through stall signal ...
  stall_out <= stall_in;


  -- Filter logic ...
  process (clk)
    variable i, dx, dy: integer;
    -- Intermediate variable to accumulate the filter result (adapt width as necessary)
    variable v_part_sum_x : pixel_sum_x_t;
    variable sum : unsigned (15 downto 0);
    -- Global weight factor: The final filter result is divided by 2^WEIGHT_SHIFT;
    -- Must be adapted to the filter function!
    constant WEIGHT_SHIFT: integer := 6;
  begin
    if rising_edge (clk) then

      -- Reset (must dominate over sliding window buffer forwarding) ...
      if reset = '1' then

        winbuf <= (others => (WBB_STROBE => '0', others => '-'));
        r_strobe_part_sum_x <= '0';
        strobe_out <= '0';

      else
        -- The filter only operates if not being stalled and
        -- if image data is coming in or if the module is being flushed.
        if ((strobe_in = '1' or ctrl_reg_flush = '1') and (stall_in = '0')) then

          -- Move sliding window buffer forward ...
          winbuf (1 to winbuf'high) <= winbuf (0 to winbuf'high - 1);
          winbuf (0) <= (strobe_in and not ctrl_reg_flush) & data_in;

          -- Compute filter (window buffer size must be set accordingly) ...

          -- 1st pipeline stage: calculate sum over window buffer lines ...
          --    (generates r_part_sum_x, r_strobe_part_sum_x)
          for dy in -3 to 3 loop
            v_part_sum_x(dy) := (others => '0');
            for dx in -3 to 3 loop
              v_part_sum_x(dy) := v_part_sum_x(dy) + unsigned (winbuf (pixel_idx (dx, dy)) (7 downto 0));
            end loop;
            r_part_sum_x(dy) <= v_part_sum_x(dy);
          end loop;
          r_strobe_part_sum_x <= winbuf (pixel_idx (0, 0)) (WBB_STROBE);

          -- 2nd pipeline stage: calculate sum over partial sums, weight and saturate the final result:
          --   (reads r_part_sum_x, r_strobe_part_sum_x; generates outputs)
          sum := (others => '0');
          for dy in -3 to 3 loop
            sum := sum + r_part_sum_x(dy);
          end loop;

          --    Divide by 2^WEIGHT_SHIFT ...
          sum (sum'left-WEIGHT_SHIFT-1 downto 0) := sum (sum'left-1 downto WEIGHT_SHIFT);
          sum (sum'left-1 downto sum'left-WEIGHT_SHIFT) := (others => sum(sum'left));

          --    Saturate the result to the range 0 .. 255 ...
          if sum(sum'left) = '1' then   -- < 0?
            sum (7 downto 0) := (others => '0');  -- 0
          elsif sum(sum'left downto 8) /= to_unsigned (0, sum'left - 8) then
            sum (7 downto 0) := (others => '1');  -- 255
          end if;

        end if; -- move filter forward

        -- Output (registered) ...
        data_out <= std_logic_vector (sum (7 downto 0));
        strobe_out <= r_strobe_part_sum_x and (strobe_in or ctrl_reg_flush) and not(stall_in);
          -- 2nd pipeline stage ends here with the assignment of the final result to data_out and the (unconditional!) assignment of strobe_out.

        status_reg_flush_ndone <= r_strobe_part_sum_x;

      end if; -- reset = '1'
    end if; -- rising_edge (clk)
  end process;

end RTL;
