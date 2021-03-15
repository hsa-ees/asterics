----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_stream_adapter_tb
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Philip Manke
--
-- Modified:       
--
-- Description:    Testbench for as_stream_adapter.
--                 NOTE: Does not automatically validate funcitonality!
--                       For manual debugging and waveform generation only!
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
--! @file  as_stream_adapter_tb.vhd
--! @brief Testbench for as_stream_adapter
----------------------------------------------------------------------------------


library ieee;
use ieee.std_logic_1164.all;
use IEEE.numeric_std.all;
use IEEE.math_real.all;

library asterics;
use asterics.helpers.all;
use asterics.as_stream_adapter;


entity as_stream_adapter_tb is
end as_stream_adapter_tb;


architecture TB of as_stream_adapter_tb is

    constant c_pixel_count : integer := 16;
    constant c_din_width : integer := 32;
    constant c_dout_width : integer := 24;
    constant c_pixel_test_count : integer := 64;

    signal clk, reset, running : std_logic;
    signal strobe_in, strobe_out, hsync_in, hsync_out, vsync_in, vsync_out, stall_in, stall_out : std_logic;
    signal data_in : std_logic_vector(c_din_width - 1 downto 0);
    signal data_out : std_logic_vector(c_dout_width - 1 downto 0);
    signal data_idx : integer := 0;

    type t_pixel_array is array(0 to c_pixel_count - 1) of std_logic_vector(c_din_width - 1 downto 0);

    constant input_data : t_pixel_array := (X"76543210", X"FEDCBA98", X"87654321", X"0FEDCBA9", X"98765432", X"10FEDCBA", X"A9876543", X"210FEDCB", X"BA987654", X"3210FEDC", X"CBA98765", X"43210FED", X"DCBA9876", X"543210FE", X"EDCBA987", X"6543210F");

begin

    dut : entity as_stream_adapter
    generic map(
        DIN_WIDTH => c_din_width,
        DOUT_WIDTH => c_dout_width
    )
    port map(
        clk => clk,
        reset => reset,
        strobe_in => strobe_in,
        data_in => data_in,
        hsync_in => hsync_in,
        vsync_in => vsync_in,
        stall_in => stall_out,
        strobe_out => strobe_out,
        data_out => data_out,
        hsync_out => hsync_out,
        vsync_out => vsync_out,
        stall_out => stall_in
    );


    data_in <= input_data(data_idx);

    p_inout : process(clk) is
    begin
        if rising_edge(clk) then
            if reset = '1' then
                data_idx <= 0;
            else
                if strobe_in = '1' then
                    if data_idx = c_pixel_count - 1 then
                        data_idx <= 0;
                    else
                        data_idx <= data_idx + 1;
                    end if;
                end if;
            end if;
        end if;
    end process;

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

    test : process is
    begin
        report "Start";
        running <= '1';
        reset <= '1';
        strobe_in <= '0';
        stall_in <= '0';
        hsync_in <= '0';

        wait for 15 ns;
        reset <= '0';
        wait for 10 ns;
        wait until rising_edge(clk);
        for P in 0 to c_pixel_test_count - 1 loop
            report "Pixel " & integer'image(P);
            if P mod 5 = 0 then
                hsync_in <= '1';
            end if;
            strobe_in <= '1';
            wait until rising_edge(clk);
            hsync_in <= '0';
            strobe_in <= '0';
            if stall_out = '1' then
                wait until stall_out = '0';
            end if;
        end loop;
        strobe_in <= '0';

        wait for 300 ns;
        report "Done.";
        running <= '0';
        wait;
    end process;
    
end architecture TB;
