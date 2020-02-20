
----------------------------------------------------------------------
-- This file is part of the ASTERICS Framework.
-- Copyright (C) Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------
-- File:     as_sim_image_reader.vhd
--
-- Company:  Efficient Embedded Systems Group
--           University of Applied Sciences, Augsburg, Germany
--           http://ees.hs-augsburg.de
--
-- Author:   Markus Bihler
--           Alexander Zoellner
--           Michael Schaeferling <michael.schaeferling@hs-augsburg.de>
-- Date:     2013-11-13
-- Modified: 
--
-- Description: writes image data to csv file
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


library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
--use IEEE.STD_LOGIC_TEXTIO.ALL;

library std;
use std.textio.all;

use work.as_sim_ram_pkg.all;

entity AS_SIM_IMAGE_WRITER is
  generic (
    SIM_FILE_NAME : string := "./tb/images/lenaScaled.csv";
    REGISTER_BIT_WIDTH : integer := 32;
    DIN_WIDTH : integer := 64;
    MEMORY_DATA_WIDTH : integer := 64;
    MEM_ADDRESS_BIT_WIDTH : integer := 32;
    BURST_LENGTH_BIT_WIDTH : integer := 12;
    MAX_PLATFORM_BURST_LENGTH  : integer := 256;
    FIFO_NUMBER_OF_BURSTS      : natural := 4;            -- max. number of stored bursts in fifo
    SUPPORT_MULTIPLE_SECTIONS : boolean := true;               -- has to be false if used for as_memio
    ENABLE_BIG_ENDIAN : boolean := true                 -- Enables big endian data interpretation
  );
  port (
    Clk         : in  std_logic;
    Reset       : in  std_logic;
    Ready       : out std_logic;
    
    FORCE_DONE  : in std_logic;     -- force memwriter to write its received data to file

    -- IN ports
    STROBE_IN   : in  std_logic;
    DATA_IN     : in  std_logic_vector(DIN_WIDTH-1 downto 0);
    
    STALL_OUT      : out std_logic;

    -- PLB part
    --! Register for sending commands to the as_memreader.
    control       : in  std_logic_vector(15 downto 0);
    --! Request reset of target control bits set by different hw module or software.
    control_reset : out std_logic_vector(15 downto 0);
    --! State of the as_memwriter module (busy, done, etc.)
    state         : out std_logic_vector(15 downto 0);
    
    --! Configuration ports for read access (see corresponding hardware driver for 
    --! more information).
    reg_section_addr        : in std_logic_vector(REGISTER_BIT_WIDTH-1 downto 0);
    reg_section_offset      : in std_logic_vector(REGISTER_BIT_WIDTH-1 downto 0);
    reg_section_size        : in std_logic_vector(REGISTER_BIT_WIDTH-1 downto 0);
    reg_section_count       : in std_logic_vector(REGISTER_BIT_WIDTH-1 downto 0);
    reg_max_burst_length    : in std_logic_vector(REGISTER_BIT_WIDTH-1 downto 0);
    --! Current memory address the as_memreader module is performing an operation on.
    reg_current_hw_addr     : out std_logic_vector(REGISTER_BIT_WIDTH-1 downto 0)
  );
end AS_SIM_IMAGE_WRITER;

architecture RTL of AS_SIM_IMAGE_WRITER is
    type t_state is (s_idle, s_store_data, s_write_disk_data, s_stop);
    signal r_state : t_state;

    

    constant NUMBER_OF_MEM_FIELDS : natural := DIN_WIDTH/c_memory_bit_width;
    constant init_val   : std_logic_vector(7 downto 0) := "00000000";
    
    signal r_pixelCnt       : natural;
--    signal mem              : mem_type := init_mem(SIM_FILE_NAME);
    signal s_mem_sm_go      : std_logic;
    signal r_reg_section_addr   : integer;
    signal r_reg_data_amount          : integer;
    signal s_data_count         : integer;
    signal s_current_address    : integer;

    shared variable mem_write: sim_ram;
  
begin

  stall_out <= '0';
  WRITE_FILE: process(Clk, Reset)
    file file_imageDataOut : text;-- open write_mode is SIM_FILE_NAME;
    variable success          : std_logic;
    variable v_imageLine      : line;
    variable v_imagePixel     : integer; --bit_vector(7 downto 0);
    
    variable v_data           : std_logic_vector(c_memory_bit_width-1 downto 0);
    variable v_addr           : integer;
  begin
  

  -- state(0) <= s_mem_sm_done; Signal software (or different hw module) having finished the last data transmission
  -- state(1) <= s_mem_sm_busy; Signal software (or different hw module) that a transmission is currently processed
  -- state(2) <= s_mem_sm_error; Signal software (or different hw module) that an error has been detected
  

  
    s_mem_sm_go <= control(1);
    
    if rising_edge(Clk) then
      if Reset = '1' or control(0) = '1' then
        state(0) <= '0';
        state(1) <= '0';
        state(2) <= '0';
        state(15 downto 3) <= (others=>'0');
--        p_init_mem(s_memory);
      else
        state(0) <= '0';
        state(1) <= '0';
        state(2) <= '0';
        state(15 downto 3) <= (others=>'0');
        case r_state is
        
            when s_idle => 
                state(0) <= '1';
                state(1) <= '0';
                r_pixelCnt <= 0;
                r_reg_section_addr      <= to_integer(unsigned(reg_section_addr));
                r_reg_data_amount             <= to_integer(unsigned(reg_section_size));
                s_data_count            <= 0;
                if s_mem_sm_go = '1' then
                    r_state <= s_store_data;
                end if;

            when s_store_data =>
                state(0) <= '0';
                state(1) <= '1';
                if s_data_count = (r_reg_data_amount) or FORCE_DONE = '1' then
                    r_state <= s_write_disk_data;
                elsif STROBE_IN = '1' then 
                    for i in 0 to NUMBER_OF_MEM_FIELDS-1 loop
                        v_addr := r_reg_section_addr + s_data_count + i;
                        if ENABLE_BIG_ENDIAN then
                          v_data := DATA_IN(DIN_WIDTH - (c_memory_bit_width*i) - 1 downto DIN_WIDTH - (c_memory_bit_width+c_memory_bit_width*i));
                        else
                          v_data := DATA_IN(c_memory_bit_width*(i+1) - 1 downto c_memory_bit_width*i);
                        end if;
                        mem_write.p_write_data(v_addr, v_data, success);
                    end loop;
                   s_data_count <= s_data_count + NUMBER_OF_MEM_FIELDS;
                end if;
          
          when s_write_disk_data =>
            state(0) <= '0';
            state(1) <= '1';
            mem_write.p_write_to_disk(SIM_FILE_NAME, r_reg_section_addr, s_data_count);
            r_state <= s_stop;
          
          when s_stop =>
            state(0) <= '1';
            state(1) <= '0';
            r_state <= s_idle;
            
        end case;
      end if;
    end if;
  end process WRITE_FILE;

end architecture;

