----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_cnn_pooling_filter
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Philip Manke
--
-- Modified:       
--
-- Description:    This module implements a pooling filter module
--                 for implementing CNNs
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
--! @file  as_cnn_pooling_filter.vhd
--! @brief This module implements a generic pooling filter for CNNs.
--! @addtogroup asterics_modules
--! @{
--! @defgroup as_cnn_pooling_filter as_cnn_pooling_filter: Convolution for CNNs
--! This module implements a pooling filter module
--! for implementing CNNs
--! @}
----------------------------------------------------------------------------------

--! @addtogroup as_cnn_pooling_filter
--! @{
--! @defgroup as_cnn_pooling_filter_internal Entities used within as_cnn_pooling_filter
--! This group contains VHDL entities used within the CNN pooling filter module.


library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library asterics;
use asterics.helpers.all;
use asterics.as_generic_filter.all;
use asterics.as_cnn_pooling_operator;

entity as_cnn_pooling_filter is
    generic(
        DATA_WIDTH : integer := 8;
        CHANNEL_COUNT : integer := 1;
        POOLING_METHOD : string := "max"
    );
    port (
        clk         : in  std_logic;
        reset       : in  std_logic;
        ready       : out std_logic;


        -- AsWindow in ports
        stall_in      : out std_logic;
        strobe_in     : in  std_logic;
        window_in     : in  t_generic_window(0 to 1, 0 to 1, (DATA_WIDTH * CHANNEL_COUNT) - 1 downto 0);

        
        -- AsStream out ports: Pooled
        data_out       : out std_logic_vector((DATA_WIDTH * CHANNEL_COUNT) - 1 downto 0);
        strobe_out     : out std_logic;
        stall_out      : in std_logic
    );
end as_cnn_pooling_filter;

--! @}

architecture RTL of as_cnn_pooling_filter is
    type t_result_array is array(0 to CHANNEL_COUNT - 1) of std_logic_vector(DATA_WIDTH - 1 downto 0);
    type t_window_array is array(0 to CHANNEL_COUNT - 1) of t_generic_window(0 to 1, 0 to 1, DATA_WIDTH - 1 downto 0);

    signal pool_data : t_result_array;
    signal window_internal : t_window_array;
begin
    ready <= not reset;
    stall_in <= stall_out;
    strobe_out <= strobe_in when rising_edge(clk);

    gen_filters : for N in 0 to CHANNEL_COUNT - 1 generate
        window_internal(N) <= f_cut_vectors_of_generic_window(window_in,  N * DATA_WIDTH, DATA_WIDTH);
        pooling_operator_N_instance : entity as_cnn_pooling_operator
        generic map(
            DATA_WIDTH => DATA_WIDTH,
            POOLING_METHOD => POOLING_METHOD
        )
        port map(
            clk => clk,
            reset => reset,
            strobe_in => strobe_in,
            window_in => window_internal(N),
            data_out => pool_data(N)
        );
        data_out(N * DATA_WIDTH + DATA_WIDTH - 1 downto N * DATA_WIDTH) <= pool_data(N);
    end generate gen_filters;
    
end RTL;
