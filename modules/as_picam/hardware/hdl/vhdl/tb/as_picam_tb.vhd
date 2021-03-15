----------------------------------------------------------------------
-- This file is part of the ASTERICS Framework.
-- Copyright (C) Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------
-- File:     as_picam_tb.vhd
--
-- Author:   Thomas Izycki
-- Date:     2020-09-30
-- Modified: 
--
-- Description:
-- Testbench for the as_picam module.
--
-- Comment:
-- 
-- 
-- 
----------------------------------------------------------------------
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
----------------------------------------------------------------------

LIBRARY ieee;
USE ieee.std_logic_1164.ALL;
USE ieee.numeric_std.ALL;

library asterics;
use asterics.helpers.all;

ENTITY as_picam_tb IS
END as_picam_tb;

ARCHITECTURE behavior OF as_picam_tb IS


  component as_picam
  generic (
    S_AXI_DATA_WIDTH  : integer := 32;
    DATA_WIDTH : integer := 8
  );
  port (
        -- Ports of Axi Slave Bus Interface S_AXIS
        s_axis_tdata	: in  std_logic_vector(S_AXI_DATA_WIDTH - 1 downto 0);
        s_axis_aclk     : in  std_logic;
        s_axis_aresetn  : in  std_logic;
        s_axis_tvalid	: in  std_logic;
        s_axis_tuser	: in  std_logic;
        s_axis_tlast	: in  std_logic;
        s_axis_tready	: out std_logic;

        -- AS_STREAM ports
        vsync_out      : out std_logic;
        vcomplete_out  : out std_logic;
        hsync_out      : out std_logic;
        strobe_out     : out std_logic;
        data_out       : out std_logic_vector(DATA_WIDTH - 1 downto 0);
        stall_in       : in  std_logic;

        -- Enable camera signal
        cam_enable_out  : out std_logic;

        slv_ctrl_reg : in slv_reg_data(0 to 0)

  );
end component;

  signal clk, reset, data_valid, start_of_frame, end_of_line, stall_incoming, running, tready : std_logic;
  signal vsync_outgoing, hsync_outgoing, vcomplete_outgoing, strobe_outgoing : std_logic;
  signal data_incoming : std_logic_vector(31 downto 0);
  signal data_outgoing : std_logic_vector(7 downto 0);
  signal control_register : slv_reg_data(0 downto 0);
   -- Clock period
  constant period: time := 10 ns;
begin

	-- Instantiate the Unit Under Test (UUT)
unit_under_test : as_picam
PORT MAP (
s_axis_aclk => clk,
s_axis_tdata => data_incoming,
s_axis_aresetn => reset,
s_axis_tvalid => data_valid,
s_axis_tuser => start_of_frame,
s_axis_tlast => end_of_line,
s_axis_tready => tready,

data_out => data_outgoing,
vsync_out => vsync_outgoing,
vcomplete_out => vcomplete_outgoing,
hsync_out => hsync_outgoing,
strobe_out => strobe_outgoing,
stall_in => stall_incoming,
slv_ctrl_reg => control_register
);


testbench : process

procedure run_cycle is
begin
  clk <= '0';
  wait for period / 2;
  clk <= '1';
  wait for period / 2;
end procedure;

begin
  running <= '1';
  reset <= '0';
  run_cycle;

  reset <= '1';

-- some random data incoming
for n in 1 to 5 loop
    data_valid <= '0';
    run_cycle;
    data_incoming <= "00000000100000001000000011111111";
    data_valid <= '1';
    run_cycle;

    data_valid <= '0';
    run_cycle;
    data_incoming <= "00000000100000001000000010000000";
    data_valid <= '1';
    run_cycle;
end loop;

-- set control register bits run and run_once
control_register(0) <= "00000000000001100000000000000000";
data_valid <= '0';
run_cycle;
data_incoming <= "00000000100000001000000011111111";
data_valid <= '1';
run_cycle;

data_valid <= '0';
run_cycle;
data_incoming <= "00000000100000001000000010000000";
data_valid <= '1';
run_cycle;

-- start of new frame
for n in 1 to 5 loop

    data_valid <= '0';
    run_cycle;
    start_of_frame <= '1'; -- set start of frame when data valid = '1'
    data_incoming <= "00000000100000001000000011111111";
    data_valid <= '1';
    run_cycle;

    data_valid <= '0';
    start_of_frame <= '0';
    run_cycle;
    data_incoming <= "00000000100000001000000010000000";
    data_valid <= '1';
    run_cycle;

    for i in 1 to 639 loop -- 1280 pixel per line. Two pixel per loop (minus two pixel from above)
        data_valid <= '0';
        run_cycle;
        data_incoming <= "00000000100000001000000011111111";
        data_valid <= '1';
        run_cycle;

        data_valid <= '0';
        run_cycle;
        data_incoming <= "00000000100000001000000010000000";
        data_valid <= '1';
        run_cycle;
    end loop;

    for n in 1 to 719 loop -- 720 lines ( minus one line from above)

        -- 1280 pixel per line. Every second clock cycle valid data
        -- 4 clock cycles in the loop --> 1280 / 2 = 640
        for i in 1 to 640 loop -- 1280 pixel per line. Every second clock cycle valid  / 4 = 180
            data_valid <= '0';
            run_cycle;
            data_incoming <= "00000000100000001000000011111111";
            data_valid <= '1';
            run_cycle;

            data_valid <= '0';
            run_cycle;
            data_incoming <= "00000000100000001000000010000000";
            data_valid <= '1';
            run_cycle;
        end loop;

     end loop;

      -- some additional clock cycles until new frame starts
      for n in 1 to 50 loop
        data_valid <= '0';
        run_cycle;
      end loop;

end loop;


running <= '0';
wait;

end process;

END;
