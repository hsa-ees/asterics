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
        DIN_WIDTH : integer := 8;
        DOUT_WIDTH : integer := 8;
        PIPELINE_DEPTH : integer := 1281; -- Number of Pixels until the first valid result at the pipeline output
        IS_FLUSHDATA_CONSTANT : boolean := false;
        CONSTANT_DATA_VALUE : integer := 0
    );
    port (
        clk   : in  std_logic;
        reset : in  std_logic;
        ready : out std_logic;
        flush_in : in std_logic; -- pulse high to start flushing
        flush_done_out : out std_logic; 
        
        input_strobe_in : in std_logic; -- Strobe input of pipeline
        input_data_in : in std_logic_vector(DIN_WIDTH - 1 downto 0); -- Pipeline input data
        input_stall_out : out std_logic;

        pipeline_strobe_out : out std_logic; -- Strobe for pipeline
        pipeline_data_out : out std_logic_vector(DIN_WIDTH - 1 downto 0); -- Data for pipeline
        
        result_data_in : in std_logic_vector(DOUT_WIDTH - 1 downto 0); -- Data from pipeline (filtered) 

        output_data_valid : out std_logic;
        output_stall_in : in std_logic; -- pipeline stall in signal
        output_strobe_out : out std_logic; -- Strobe for pipeline results
        output_data_out : out std_logic_vector(DOUT_WIDTH - 1 downto 0) -- Pipeline result data output
    );
end entity;


architecture RTL of as_pipeline_flush is

    constant flush_count : integer := integer(ceil(real(PIPELINE_DEPTH / 2)));
    constant counter_width : integer := log2_ceil(flush_count);
    constant count_comp : unsigned := to_unsigned(flush_count, counter_width);
    
    signal counter, counter_output : unsigned(counter_width - 1 downto 0);
    signal flushing_int, flushing_data_at_output, flush_done, pipe_full : std_logic;
    signal flush_data : std_logic_vector(DIN_WIDTH - 1 downto 0);
    signal strobe_int : std_logic;
    signal pipeline_empty : std_logic;
    signal output_off_flush, output_off : std_logic;
begin

    -- Status and control signals:
    ready <= (not flushing_int) or reset;
    flush_done_out <= flush_done;
    strobe_int <= (input_strobe_in or flushing_int or ((flushing_data_at_output or pipeline_empty) and input_strobe_in)) and not output_stall_in;
    output_off_flush <= flushing_data_at_output or flush_done;
    flush_done <= '1' when counter = flush_count else '0';
    pipe_full <= '1' when counter_output = flush_count else '0';
    output_off <= output_off_flush or pipeline_empty;

    -- Propagate stall signal
    input_stall_out <= output_stall_in;

    -- Output for pipeline output (to data out of pipeline)
    output_strobe_out <= '0' when output_off = '1' else strobe_int;
    output_data_out <= result_data_in; 

    output_data_valid <= not output_off;

    -- Output for pipeline input (to pipeline filter modules)
    pipeline_strobe_out <= strobe_int;
    pipeline_data_out <= flush_data when flushing_int = '1' else input_data_in;

    pipeline_state : process(clk) is
    begin
        if rising_edge(clk) then
            if reset = '1' then
                pipeline_empty <= '1';
            else
                if output_off_flush = '1' then
                    pipeline_empty <= '0';
                end if;
            end if;
        end if;
    end process;

    -- Counter process:
    counting : process(clk) is
    begin
        if rising_edge(clk) then
            if reset = '1' then
                counter <= (others => '0');
                counter_output <= (others => '0');
            else
                if flushing_int = '1' and output_stall_in = '0' then
                    counter <= counter + 1;
                elsif flush_done = '1' then
                    counter <= (others => '1');
                elsif output_stall_in = '1' then
                    counter <= counter;
                else
                    counter <= (others => '0');
                end if;
                if (flushing_data_at_output = '1' 
                        or pipeline_empty = '1' 
                        or flush_done = '1') then
                    
                    if output_stall_in = '0' and input_strobe_in = '1' then
                        counter_output <= counter_output + 1;
                    elsif output_stall_in = '1' or input_strobe_in = '0' then
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
    
    -- Flush data output:
    counter_output_generate : if not IS_FLUSHDATA_CONSTANT generate
        -- output counter for flushing data
        data_output_big_counter : if flush_data'length <= counter_width generate
            flush_data <= std_logic_vector(counter(flush_data'range));
        end generate;
        data_output_small_counter : if flush_data'length > counter_width generate
            flush_data(counter'range) <= std_logic_vector(counter);
            flush_data(DIN_WIDTH - 1 downto counter'length) <= (others => '0');
        end generate;
    end generate;
    constant_output_generate : if IS_FLUSHDATA_CONSTANT generate
        flush_data <= std_logic_vector(to_unsigned(CONSTANT_DATA_VALUE, DIN_WIDTH));
    end generate;

end architecture;