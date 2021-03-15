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
use asterics.as_cnn_pooling_filter;
use asterics.as_window_buff_nxm;

entity as_cnn_conv_filter_tb is
end entity as_cnn_conv_filter_tb;

architecture TB of as_cnn_conv_filter_tb is
    constant c_line_width : integer := 17;
    constant c_window_width : integer := 2;
    constant c_window_height : integer := 2;
    constant c_data_width : integer := 8;
    constant c_min_bram_length : integer := 64;
    constant c_test_data_count : integer := 32;
    constant c_data_input_count : integer := 320 * 4;
    signal window : t_generic_window(0 to c_window_width - 1, 0 to c_window_height - 1, c_data_width - 1 downto 0);
    
    signal clk, reset, running, strobe_in, hsync : std_logic;
    signal strobe_out : std_logic;
    signal data_in : std_logic_vector(c_data_width - 1 downto 0);
    signal data_out : std_logic_vector(7 downto 0);


    type byte_array is array(0 to c_test_data_count - 1) 
            of std_logic_vector(7 downto 0);
    constant test_data : byte_array := 
            (X"80", X"04", X"70", X"EF", X"13", X"37", X"29", X"FF",
             X"80", X"02", X"70", X"EF", X"13", X"37", X"29", X"FF",
             X"80", X"04", X"70", X"EF", X"13", X"37", X"29", X"FF",
             X"80", X"02", X"70", X"EF", X"13", X"37", X"29", X"FF");

begin

    dut : entity as_cnn_pooling_filter
    generic map(
        DATA_WIDTH => 4,
        CHANNEL_COUNT => 2,
        --DOUT_WIDTH => 4,
        KERNEL_SIZE => 2
        --ACTIVATION_FUNCTION => "relu",
        --BIAS_VALUE => 4,
        --STRIDE_X => 2,
        --STRIDE_Y => 2
    )
    port map(
        clk => clk,
        reset => reset,
        hsync => hsync,
        strobe_in => strobe_in,
        window_in => window,
        --kernel_values => (1,2,2,1,2,4,4,2),
        strobe_out => strobe_out,
        data_out => data_out
    );
--
    pipeline : entity as_window_buff_nxm
    generic map(
        DATA_WIDTH => c_data_width,
        LINE_WIDTH => c_line_width,
        WINDOW_X => c_window_width,
        WINDOW_Y => c_window_height,
        MINIMUM_LENGTH_FOR_BRAM => c_min_bram_length
    )
    port map(
        clk => clk,
        reset => reset,
        strobe => strobe_in,
        data_in => data_in,
        window_out => window,
        data_out => open
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

    test : process is
    begin
        report "Start";
        running <= '1';
        reset <= '1';
        data_in <= (others => '0');
        hsync <= '0';
        strobe_in <= '0';

        wait for 10 ns;
        reset <= '0';

        for DL in 0 to c_data_input_count / c_test_data_count - 1 loop
            for TDC in 0 to c_test_data_count - 1 loop
                data_in <= test_data(TDC);
                hsync <= '0';
                if TDC = 15 or TDC = 31 then
                    hsync <= '1';
                end if;
                strobe_in <= '1';
                wait for 10 ns;

            end loop;
        end loop;

        strobe_in <= '0';
        wait for 40 ns;

        

        wait for 300 ns;
        
        running <= '0';
        wait;

    end process;
end architecture;
