------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
--  All rights reserved
------------------------------------------------------------------------
-- Entity:         as_edge_tb
--
-- Company:        University of Applied Sciences, Augsburg, Germany
--                 Efficient Embedded Systems Group
--                 http://ees.hs-augsburg.de
--
-- Author:         Philip Manke
--
-- Modified:       
--
-- Description:    
------------------------------------------------------------------------
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

-- TODO:
-- Analyse weird behaviour of BRAM module: Where do the UUs come from?

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use ieee.numeric_std.all;

library asterics;
use asterics.helpers.all;
use asterics.as_generic_filter.all;
use asterics.as_single_conv_filter;

entity as_single_conv_filter_tb is
end entity as_single_conv_filter_tb;

architecture TB of as_single_conv_filter_tb is
    constant c_line_width : integer := 64;
    constant c_window_width : integer := 3;
    constant c_window_height : integer := 3;
    constant c_data_width : integer := 8;
    constant c_min_bram_length : integer := 64;
    constant c_test_data_count : integer := 24;
    constant c_data_input_count : integer := 640 * 8;
    signal strobe_in_count : integer;
    signal strobe_out_count : integer;

    signal window : t_generic_window(0 to c_window_height - 1, 0 to c_window_width - 1, c_data_width - 1 downto 0);
    
    signal clk, reset, running, strobe_in, ready : std_logic;
    signal strobe_out, stall_out, stall_in : std_logic;
    signal data_in, data_out : std_logic_vector(c_data_width - 1 downto 0);

    signal slv_ctrl_reg : slv_reg_data(0 to 0);
    signal slv_status_reg : slv_reg_data(0 to 0);
    signal state_control_reg, sw_reg : std_logic_vector(31 downto 0);
    signal slv_reg_modify : std_logic_vector(0 downto 0);
    signal sw_reg_set : std_logic;
    signal strobe_counter_reset : std_logic;

    type byte_array is array(0 to c_test_data_count - 1) 
            of std_logic_vector(7 downto 0);
    constant test_data : byte_array := 
            (X"80", X"04", X"70", X"EF", X"13", X"37", X"29", X"FF",
             X"80", X"02", X"70", X"EF", X"13", X"37", X"29", X"FF",
             X"80", X"04", X"70", X"EF", X"13", X"37", X"29", X"FF");

begin

    dut : entity as_single_conv_filter
    generic map(
        DIN_WIDTH => c_data_width,
        DOUT_WIDTH => c_data_width,
        MINIMUM_BRAM_SIZE => c_min_bram_length,
        LINE_WIDTH => c_line_width
    )
    port map(
        clk => clk,
        reset => reset,
        ready => ready,

        strobe_in => strobe_in,
        data_in => data_in,
        stall_out => stall_out,
        strobe_out => strobe_out,
        data_out => data_out,
        stall_in => stall_in,
        slv_ctrl_reg => slv_ctrl_reg,
        slv_status_reg => slv_status_reg,
        slv_reg_modify => slv_reg_modify,
        slv_reg_config => open,
        vcomplete_out => open
    );


    p_clk : process is
    begin
        clk <= '0';
        wait for 5 ns;
        clk <= '1';
        wait for 5 ns;
        if running = '0' then
            wait;
        end if;
    end process;

    process(clk) is
    begin
        if rising_edge(clk) then
            if reset = '1' then
                state_control_reg <= (others => '0');
            else
                if slv_reg_modify(0) = '1' then
                    state_control_reg <= slv_status_reg(0);
                elsif sw_reg_set = '1' then
                    state_control_reg <= sw_reg;
                end if;
                slv_ctrl_reg(0) <= state_control_reg;  
            end if;
        end if;
    end process;

    -- strobe counter

    process(clk) is
    begin
        if rising_edge(clk) then
            if reset = '1' or strobe_counter_reset = '1' then
                strobe_out_count <= 0;
                strobe_in_count <= 0;
            else
                if strobe_out = '1' then
                    strobe_out_count <= strobe_out_count + 1;
                end if;
                if strobe_in = '1' then
                    strobe_in_count <= strobe_in_count + 1;
                end if;
            end if;
        end if;
    end process;

    test : process is
        variable data_select : integer := 0;
    begin
        report "Start";
        running <= '1';
        reset <= '1';
        wait for 10 ns;
        reset <= '0';
        for L in 0 to 7 loop
            strobe_counter_reset <= '1';
            strobe_in <= '0';
            stall_in <= '0';
            sw_reg <= (others => '0');
            data_in <= (others => '0');
            sw_reg_set <= '0';
            wait for 10 ns;
            strobe_counter_reset <= '0';
            wait for 10 ns;
            
            -- Data input
            for I in 0 to c_data_input_count loop
                strobe_in <= '1';
                data_in <= test_data(data_select);
                wait for 10 ns;
                strobe_in <= '0';
                data_select := data_select + 1;
                if data_select = c_test_data_count then
                    data_select := 0;
                end if;
                wait for 70 ns;
            end loop;
            strobe_in <= '0';
            wait for 80 ns;

            -- Start flush
            sw_reg(0) <= '1';
            sw_reg_set <= '1';
            wait for 10 ns;
            sw_reg_set <= '0';

            -- Check stall behaviour
            wait for 100 ns;
            stall_in <= '1';
            wait for 40 ns;
            stall_in <= '0';
            wait for 100 ns;
            stall_in <= '1';
            wait for 40 ns;
            stall_in <= '0';
            -- Wait until flush completes
            wait until state_control_reg(16) = '1';
            wait for 50 ns;
            report "IN: " & integer'image(strobe_in_count);
            report "OUT: " & integer'image(strobe_out_count);
            
            assert strobe_in_count = strobe_out_count report("Flush behaviour fail!")
                severity failure;
            
            wait for 300 ns;
        end loop;
        
        running <= '0';
        report "Flush behaviour pass!";
        wait;

    end process;
end architecture;
