----------------------------------------------------------------------
-- This file is part of the ASTERICS Framework.
-- (C) 2013 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------
-- File:     as_sim_file_reader.vhd
--
-- Company:  Efficient Embedded Systems Group
--           University of Applied Sciences, Augsburg, Germany
--           http://ees.hs-augsburg.de
--
-- Author:   Markus Bihler
--           Alexander Zoellner
--           Michael Schaeferling <michael.schaeferling@hs-augsburg.de>
-- Date:     2013-11-13
-- Modified: 2020-06-08 (MS)
--
-- Description: Reads data from a file for simulation.
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
--! @file as_sim_image_reader.vhd
--! @brief Reads data from a file for simulation.
--! @addtogroup asterics_helpers
--! @{
--! @defgroup as_sim_image_reader as_sim_image_reader: as_memreader Simulation Module
--! This module simulates the behaviour of an as_memreader module for hardware simulation.
--! @}
----------------------------------------------------------------------------------

--! @addtogroup as_sim_image_reader
--! @{

library ieee;
use ieee.std_logic_1164.ALL;
use ieee.numeric_std.ALL;

library std;
use std.textio.all;

use work.as_sim_ram_pkg.all;

entity as_sim_file_reader is
  generic(
    SIM_FILE_NAME : string := "./tb/images/data_in.dat";
    REGISTER_BIT_WIDTH : integer := 32;              -- default bit width of slave registers (for configuration)
    DOUT_WIDTH : integer := 32;                      -- default bit width of data (has to be equal to MEMORY_DATA_WIDTH)
    MEMORY_DATA_WIDTH : integer := 32;               -- default bit width of bus connections
    MEM_ADDRESS_BIT_WIDTH : integer := 32;           -- default bit width of memory address
    BURST_LENGTH_BIT_WIDTH : integer := 12;          -- default bit width of burst length setting (bus dependant)
    FIFO_FILL_BIT_WIDTH : integer := 10;             -- default bit width for fifo fill level
    MAX_PLATFORM_BURST_LENGTH  : integer := 256;     -- max. supported burst length in byte by platform
    SUPPORT_MULTIPLE_SECTIONS : boolean := true;     -- has to be false if used for as_memio
    SUPPORT_VARIABLE_BURST_LENGTH : boolean := true; -- Support smaller burst lengths if possible.
    ENABLE_BIG_ENDIAN : boolean := true              -- Enables big endian data interpretation
  );
  port(
    clk   : in std_logic;
    reset : in std_logic;
    ready : out std_logic;

    strobe_out : out std_logic;
    data_out   : out std_logic_vector(DOUT_WIDTH-1 downto 0);
    stall_in   : in  std_logic;

    control       : in  std_logic_vector(15 downto 0);
    control_reset : out std_logic_vector(15 downto 0);
    state         : out std_logic_vector(15 downto 0);

    reg_section_addr     : in  std_logic_vector(REGISTER_BIT_WIDTH-1 downto 0);
    reg_section_offset   : in  std_logic_vector(REGISTER_BIT_WIDTH-1 downto 0);  -- not implemented yet
    reg_section_size     : in  std_logic_vector(REGISTER_BIT_WIDTH-1 downto 0);
    reg_section_count    : in  std_logic_vector(REGISTER_BIT_WIDTH-1 downto 0);  -- not implemented yet
    reg_max_burst_length : in  std_logic_vector(REGISTER_BIT_WIDTH-1 downto 0);  -- not needed in simulation
    reg_current_hw_addr  : out std_logic_vector(REGISTER_BIT_WIDTH-1 downto 0)
  );
end as_sim_file_reader;

architecture SIM of as_sim_file_reader is

  constant c_number_of_mem_fields : natural := DOUT_WIDTH/c_memory_bit_width;
  constant init_val   : std_logic_vector(7 downto 0) := "00000000";

  shared variable mem_read: sim_ram;

  type t_state is (s_idle, s_read, s_done);
  signal r_state : t_state;

  signal r_cur_addr : natural;
  signal s_data_count : integer;
  
  signal r_reg_section_addr        : integer := 0;
  signal r_reg_section_size        : integer := 0;

  signal file_start_addr           : integer := 0;
  signal read_whole_file           : integer := 0;
  
  signal s_copy_input              : std_logic;

begin

  reg_current_hw_addr <= std_logic_vector(to_unsigned(r_cur_addr,reg_current_hw_addr'length));

  control_reset <= (others=>'0');


  p_read_file : process(clk, reset)

    variable success : std_logic;
    variable v_addr : integer;
    variable v_data : std_logic_vector(c_memory_bit_width-1 downto 0);

  begin
    if rising_edge(clk) then
      if reset = '1' or control(0) = '1' then
        STROBE_OUT <= '0';
        DATA_OUT <= (others => '0');
        r_cur_addr <= 0;
        r_state <= s_idle;
        state(0) <= '0'; -- DONE
        state(1) <= '1'; -- BUSY
        state(2) <= '0'; -- ERROR
        s_copy_input <= '0';
        -- Read in whole file during reset, both values have to be zero -> Results in reading whole file
        report "mem_read.p_read_from_disk start..." severity note;
        mem_read.p_read_from_disk(SIM_FILE_NAME, file_start_addr, read_whole_file);  
        report "mem_read.p_read_from_disk finished." severity note;
      else
        -- Default
        s_copy_input <= '0';
        STROBE_OUT <= '0';
        DATA_OUT <= (others => '0');
        state(0) <= '0'; -- DONE
        state(1) <= '0'; -- BUSY
        state(2) <= '0'; -- ERROR
          case r_state is
            when s_idle =>
              state(0) <= '1'; -- DONE
              state(1) <= '0'; -- BUSY
              state(2) <= '0'; -- ERROR
              r_reg_section_addr <= to_integer(unsigned(reg_section_addr));
              r_reg_section_size <= to_integer(unsigned(reg_section_size));
              s_data_count       <= 0;
              if control(1) = '1' then
                r_state <= s_read;
              end if;

            when s_read =>
              if STALL_IN = '0' then
                state(0) <= '0'; -- DONE
                state(1) <= '1'; -- BUSY
                state(2) <= '0'; -- ERROR
                if s_data_count = (r_reg_section_size) then -- - c_number_of_mem_fields) then
                    r_state <= s_done;
                else
                    STROBE_OUT <= '1';

                    for i in c_number_of_mem_fields - 1 downto 0 loop
                        v_addr := r_reg_section_addr + s_data_count + i;
                        mem_read.p_read_data(v_addr, v_data, success);
                        if ENABLE_BIG_ENDIAN then
                          DATA_OUT(DOUT_WIDTH-c_memory_bit_width*i-1 downto DOUT_WIDTH-(c_memory_bit_width+c_memory_bit_width*i)) <= v_data;
                        else
                          DATA_OUT(c_memory_bit_width*(i+1)-1 downto c_memory_bit_width*i) <= v_data;
                        end if;
                    end loop;
                    s_data_count <= s_data_count + c_number_of_mem_fields;
                end if;
              end if;

            when s_done =>
                state(0) <= '1'; -- DONE
                state(1) <= '1'; -- BUSY
                state(2) <= '0'; -- ERROR
                STROBE_OUT <= '0';
                r_cur_addr <= 0;
                DATA_OUT <= (others => '0');

              r_state <= s_idle;
          end case;
        end if;
    end if;

  end process p_read_file;

end architecture;
