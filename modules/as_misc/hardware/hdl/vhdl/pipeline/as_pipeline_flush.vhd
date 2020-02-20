----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework.
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:        as_pipeline_flush
--
-- Company:       Efficient Embedded Systems Group
--                University of Applied Sciences, Augsburg, Germany
--
-- Author:        Philip Manke
--
-- Description:   Implements a data generator component for pipeline flushing
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
--! @file  as_pipeline_flush.vhd
--! @brief Implements a data generator component for pipeline flushing
----------------------------------------------------------------------------------


library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

library asterics;
use asterics.helpers.all;

entity as_pipeline_flush is
    generic (
        DATA_WIDTH : integer := 8;
        LINE_WIDTH : integer := 640;
        WINDOW_X : integer := 3;
        WINDOW_Y : integer := 3;
        FILTER_DELAY : integer := 1;
        IS_FLUSHDATA_CONSTANT : boolean := false;
        CONSTANT_FLUSHDATA : integer := 0
    );
    port (
        clk   : in  std_logic;
        reset : in  std_logic;
        ready : out std_logic;

        strobe_in : in std_logic; -- Strobe input of pipeline
        flush_in : in std_logic; -- pulse high to start flushing
        pipeline_empty : in std_logic; -- Pulse high to generate output_off
        flushing_out : out std_logic; -- indicates a flush in progress
        output_off : out std_logic; -- control signal notifying that invalid flush-data is at the output of the pipeline (intended to switch of output strobe)
        
        stall_in : in std_logic; -- pipeline stall in signal
        strobe_out : out std_logic; -- pipeline flush strobe, reacts to stall in
        data_out : out std_logic_vector(DATA_WIDTH - 1 downto 0) -- flush data
    );
end entity;


architecture RTL of as_pipeline_flush is
    -- TODO: What if LINE_WIDTH is uneven?
    constant full_flush_count : integer := LINE_WIDTH * (WINDOW_Y - 1) + WINDOW_X;

    constant flush_count : integer := integer(ceil(real(full_flush_count / 2))) + FILTER_DELAY;
    constant counter_width : integer := log2_ceil(flush_count);
    constant count_comp : unsigned := to_unsigned(flush_count, counter_width);
    
    signal counter, counter_output : unsigned(counter_width - 1 downto 0);
    signal flushing_int, flushing_data_at_output, flush_done, pipe_full : std_logic;
begin

    -- Status and control signals:
    ready <= not flushing_int;
    strobe_out <= (flushing_int or ((flushing_data_at_output or pipeline_empty) and strobe_in)) and not stall_in;
    flushing_out <= flushing_int;
    output_off <= flushing_data_at_output or flush_done;

    flush_done <= '1' when counter = flush_count else '0';
    pipe_full <= '1' when counter_output = flush_count else '0';

    -- Counter process:
    counting : process(clk) is
    begin
        if rising_edge(clk) then
            if reset = '1' then
                counter <= (others => '0');
                counter_output <= (others => '0');
            else
                if flushing_int = '1' and stall_in = '0' then
                    counter <= counter + 1;
                elsif stall_in = '1' then
                    counter <= counter;
                else
                    counter <= (others => '0');
                end if;
                if (flushing_data_at_output = '1' 
                        or pipeline_empty = '1' 
                        or flush_done = '1') then
                    
                    if stall_in = '0' and strobe_in = '1' then
                        counter_output <= counter_output + 1;
                    elsif stall_in = '1' or strobe_in = '0' then
                        counter_output <= counter_output;
                    end if;
                else
                    counter_output <= (others => '0');
                end if;
            end if;
        end if;
    end process;

    -- Status update process:
    status : process(clk) is
    begin
        if rising_edge(clk) then
            if reset = '1' then
                flushing_int <= '0';
                flushing_data_at_output <= '0';
            else
                if flush_done = '1' or pipeline_empty = '1' then
                    flushing_int <= '0';
                    flushing_data_at_output <= '1';
                elsif flushing_int = '1' or flush_in = '1' then
                    flushing_int <= '1';
                end if;

                if pipe_full = '1' then
                    flushing_data_at_output <= '0';
                end if;
            end if;
        end if;
    end process;
    
    -- Output:
    counter_output_generate : if not IS_FLUSHDATA_CONSTANT generate
        -- output counter for flushing data
        data_output_big_counter : if data_out'length <= counter_width generate
            data_out <= std_logic_vector(counter(data_out'range));
        end generate;
        data_output_small_counter : if data_out'length > counter_width generate
            data_out(counter'range) <= std_logic_vector(counter);
            data_out(DATA_WIDTH - 1 downto counter'length) <= (others => '0');
        end generate;
    end generate;
    constant_output_generate : if IS_FLUSHDATA_CONSTANT generate
        data_out <= std_logic_vector(to_unsigned(CONSTANT_FLUSHDATA, DATA_WIDTH));
    end generate;

end architecture;