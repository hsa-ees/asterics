----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- File:           as_collect.vhd
-- Entity:         as_collect
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Authors:        Michael Schaeferling, Julian Sarcher
--
-- Modified:       
--
-- Description:    This module collects DOUT_WIDTH/DIN_WIDTH data words and 
--                 corresponding VSYNC and HSYNC signals into one new data word.
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
--! @file
--! @brief This module collects data words, combining them into one new word.
----------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.helpers.all;

entity as_collect is
  generic (
    DIN_WIDTH : integer := 8;
    COLLECT_COUNT : integer := 4; -- collects this many data words to one data word
    DOUT_ORDER_ASCENDING : boolean := false -- defines the order of the collected data words within the new word ('false' is what you ususally want for collecting data for a mem-writer in a little-endian system)
  );
  port (
    clk         : in  std_logic;
    reset       : in  std_logic;

    -- IN ports
    vsync_in     : in  std_logic;
    hsync_in     : in  std_logic;
    strobe_in    : in  std_logic;
    data_in      : in  std_logic_vector(DIN_WIDTH - 1 downto 0);
    vcomplete_in : in  std_logic;
    
    data_error_in : in  std_logic;
    stall_out     : out std_logic;

    -- OUT ports
    vsync_out     : out std_logic;
    hsync_out     : out std_logic;
    strobe_out    : out std_logic;
    data_out      : out std_logic_vector(DIN_WIDTH * COLLECT_COUNT - 1 downto 0);
    vcomplete_out : out std_logic;

    data_error_out : out std_logic;
    stall_in       : in  std_logic
  );
end as_collect;


architecture RTL of as_collect is

  constant collect_count_internal    : natural := COLLECT_COUNT;
  constant reg_bit_width    : natural := data_in'length + 3;

  signal reg_in : std_logic_vector(reg_bit_width-1 downto 0);

  signal shift_reg : std_logic_vector(collect_count_internal*reg_bit_width-1 downto 0);

  signal strobe_counter : unsigned(log2_ceil(collect_count_internal) downto 0);

  signal pixel_error : unsigned(collect_count_internal-1 downto 0);

  signal pending_strobe : std_logic;
  
  signal shift_en : std_logic;
  signal flush_en : std_logic;
  signal flush_en_last_cycle : std_logic;
    
begin

  -- Directly map input to output if the same bit width for both is used
  gen_no_collect : if collect_count_internal = 1 generate
  
    vsync_out     <= vsync_in;
    hsync_out     <= hsync_in;
    strobe_out    <= strobe_in;
    data_out      <= data_in;
    vcomplete_out <= vcomplete_in;
    data_error_out  <= data_error_in;
    stall_out       <= stall_in;
  end generate; -- gen_no_collect


  -- Collect input data to match the bit width of the output
  gen_collect : if collect_count_internal /= 1 generate
  
    reg_in(0) <= vsync_in;
    reg_in(1) <= hsync_in;
    reg_in(2) <= data_error_in;
    reg_in(reg_bit_width-1 downto 3) <= data_in;

    shift_en <= strobe_in or flush_en;

    SHIFT_REGISTERS : for i in 0 to collect_count_internal-1 generate 

      shif_register : process(clk)
      begin
        if rising_edge(clk) then
          if reset = '1' then
            shift_reg((i+1)*reg_bit_width-1 downto i*reg_bit_width) <= (others => '0');
          else
            if shift_en = '1' then 
              if DOUT_ORDER_ASCENDING = true then -- old behaviour: first word is located on the upper part of the new word
                if i = 0 then
                  shift_reg((i+1)*reg_bit_width-1 downto i*reg_bit_width) <= reg_in;
                else
                  shift_reg((i+1)*reg_bit_width-1 downto (i)*reg_bit_width) <= shift_reg((i)*reg_bit_width-1 downto (i-1)*reg_bit_width);
                end if;
              else -- new behaviour:  last word is located on the upper part of the new word
                if i = collect_count_internal-1 then
                  shift_reg((i+1)*reg_bit_width-1 downto i*reg_bit_width) <= reg_in;
                else
                  shift_reg((i+1)*reg_bit_width-1 downto (i)*reg_bit_width) <= shift_reg((i+2)*reg_bit_width-1 downto (i+1)*reg_bit_width);
                end if;
              end if;
            end if;
          end if;
        end if;
      end process;
      pixel_error(i) <= shift_reg(i*reg_bit_width+2);
      data_out((i+1)*DIN_WIDTH-1 downto i*DIN_WIDTH) <= shift_reg((i+1)*reg_bit_width-1 downto i*reg_bit_width+3);
    
    end generate;

    out_p : process(clk)
    begin
      if rising_edge(clk) then
        strobe_out <= '0';
        if reset = '1' then
          pending_strobe <= '0';
          strobe_counter <= (others => '0');
          vcomplete_out <= '0';
          flush_en <= '0';
        else
          -- flush at vcomplete_in and generate correct vcomplete_out
          vcomplete_out <= '0';
          flush_en_last_cycle <= flush_en;
          if strobe_counter = to_unsigned(collect_count_internal-1, strobe_counter'length) then
            if flush_en = '1' then
              flush_en <= '0';
            end if;
          end if;
          if vcomplete_in = '1' then
            if strobe_counter = to_unsigned(0, strobe_counter'length) then
              flush_en <= '0';
              vcomplete_out <= '1';
            else
              flush_en <= '1';
            end if;
          end if;
          if flush_en = '0' and flush_en_last_cycle = '1' then
            vcomplete_out <= '1';
          end if;
          
          if shift_en = '1' then
            if stall_in = '0' then
              if strobe_counter = to_unsigned(collect_count_internal-1, strobe_counter'length) then
                strobe_counter <= (others =>'0');
                strobe_out <= '1';
              else
                strobe_counter <= strobe_counter + 1;
              end if;
            else
              if strobe_counter = to_unsigned(collect_count_internal-1, strobe_counter'length) then
                strobe_counter <= (others => '0');
                pending_strobe <= '1';
              else
                strobe_counter <= strobe_counter + 1;
              end if;
            end if;
          end if;
          if pending_strobe = '1' and stall_in = '0' then
            pending_strobe <= '0';
            strobe_out <= '1';
          end if;
          
        end if;
      end if;
    end process;

    vsync_out <= shift_reg((collect_count_internal-1)*reg_bit_width+0);
    hsync_out <= shift_reg((collect_count_internal-1)*reg_bit_width+1);
    data_error_out <= '0' when pixel_error = 0 else '1';
    stall_out <= stall_in or vcomplete_in or flush_en;
    
  end generate; -- gen_collect
  
end RTL;
