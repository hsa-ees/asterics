----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- File:           AS_MEM_ADDRESS_GENERATOR.vhd
-- Entity:         AS_MEM_ADDRESS_GENERATOR
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Alexander Zoellner
--
-- Modified:       
--
-- Description:    This module determines the next address and corresponding 
--                 bus signals (burst_length and s_burst_possible) for a memory
--                 request.
--                 
--                 Parameters need to be set before running this module.
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
--! @brief This module calculates address and control signals for a memory requests.
--! @addtogroup as_memwriter as_memreader
--! @{
--! @defgroup as_mem_address_generator Memory Address Generator
--! This module generates addresses for memreader and memwriter modules.
--! @}
----------------------------------------------------------------------------------

--! @addtogroup as_mem_address_generator
--! @{

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;


entity AS_MEM_ADDRESS_GENERATOR is
generic (
    ADDRESS_BIT_WIDTH           : integer := 32;          -- Data and bus address bit width
    MEMORY_BIT_WIDTH              : integer := 64;
    BURST_LENGTH_WIDTH          : integer := 12;          -- Bit width of burst length (bus dependant)
    SUPPORT_VARIABLE_BURST_LENGTH : boolean := false;      -- Disable variable burst length (may only be set true if used with as_memreader)
    SUPPORT_MULTIPLE_SECTIONS       : boolean := false        -- Disable having multiple sections (must not be true if used with as_memio)
);
port (
    clk                 : in std_logic;
    reset               : in std_logic;
    
    go                  : in std_logic;        -- Activate address generator
    cnt_en              : in std_logic;        -- Increment current address by ADDRESS_BIT_WIDTH/8
    ready               : out std_logic;       -- Signal others being ready for next operation
    
-- Ports for configuration
    section_addr        : in std_logic_vector(ADDRESS_BIT_WIDTH-1 downto 0);  -- Start address of memory data transaction
    section_offset      : in std_logic_vector(ADDRESS_BIT_WIDTH-1 downto 0);  -- Offset in byte between to sections (start to start; don't care if SUPPORT_MULTIPLE_SECTIONS is set to false)
    section_size        : in std_logic_vector(ADDRESS_BIT_WIDTH-1 downto 0);  -- Number of bytes to be transmitted (integer multiple of c_number_of_bytes_per_word)
    section_count       : in std_logic_vector(ADDRESS_BIT_WIDTH-1 downto 0);  -- Number of sections (don't care if SUPPORT_MULTIPLE_SECTIONS is set to false)
    max_burst_length    : in std_logic_vector(ADDRESS_BIT_WIDTH-1 downto 0);  -- Maximal burst length to be used (actual burst length might be smaller if SUPPORT_VARIABLE_BURST_LENGTH was set to true)

-- Information for next bus access
    memory_address      : out std_logic_vector(ADDRESS_BIT_WIDTH-1 downto 0);     -- Memory start address for next transaction
    burst_length        : out std_logic_vector(BURST_LENGTH_WIDTH-1 downto 0);    -- Burst length for bus access (all zero if burst_enable = 0)
    burst_enable        : out std_logic                                           -- Determines if a burst is possible (single-beat otherwise)
);
end AS_MEM_ADDRESS_GENERATOR;

--! @}

architecture RTL of AS_MEM_ADDRESS_GENERATOR is

    -- Determine number of bytes of a word
    constant c_number_of_bytes_per_word : natural := MEMORY_BIT_WIDTH/8;
    
    -- address generator statemachine signals
    type address_gen_sm_state_t is (s_reset, s_idle, s_setup, s_cnt_active);
    signal address_gen_sm_next_state, address_gen_sm_current_state : address_gen_sm_state_t;
    signal s_counter_active         : std_logic;
    
    -- signals for address calculation
    signal s_address_calc_setup     : std_logic;
    signal r_current_address            : unsigned(ADDRESS_BIT_WIDTH-1 downto 0);
    
    -- signals for total number of bytes left for read requests
    signal s_byte_count_done            : std_logic;
    signal r_bytes_left             : signed(ADDRESS_BIT_WIDTH-1 downto 0);
    
    -- signals for section calculation
    signal s_section_count_done     : std_logic;
    signal r_current_section_count  : signed(ADDRESS_BIT_WIDTH-1 downto 0);
    signal r_current_section_offset   : unsigned(ADDRESS_BIT_WIDTH-1 downto 0);
    
    -- signals for burst determination
    signal s_actual_burst_length    : std_logic_vector(BURST_LENGTH_WIDTH-1 downto 0);
    signal s_burst_possible     : std_logic;

begin

--! Setting output ports for bus access. These signals have to be stored before initializing a 
--! read request since output signals may change during bus access depending on assignment on the
--! cnt_en port.
    memory_address <= std_logic_vector(r_current_address);
    burst_length <= s_actual_burst_length;
    burst_enable <= s_burst_possible;

--! Statemachine for copying configuration signals and enabling address and control signal 
--! calculation.
    address_gen_statemachine : process(address_gen_sm_current_state, go, s_section_count_done, reset)
    begin
    
        address_gen_sm_next_state <= address_gen_sm_current_state;

    --! Default values for output signals of the state machine.
        ready <= '0';
        s_address_calc_setup <= '0';
        s_counter_active <= '0';
        
        case address_gen_sm_current_state is
        
    --! State which is assumed during hardware power-up or after
    --! reset request. Output is set to all zeros (default values).
            when s_reset =>
                address_gen_sm_next_state <= s_idle;
            
    --! Signal other hw modules that address generator is ready for 
    --! operation and may accept a request for address calculation.
            when s_idle =>
                ready <= '1';
                if go = '1' then
                    address_gen_sm_next_state <= s_setup;
                end if;
                
    --! Copy configuration into shadow registers for internal 
    --! operation. Ready signal is extended for this state since 
    --! information for bus access are not valid yet.
            when s_setup =>
                ready <= '1';
                s_address_calc_setup <= '1';
                address_gen_sm_next_state <= s_cnt_active;
                
    --! Address calculation and determination of bus access type is
    --! in session. Address calculation is finished when the last 
    --! section has been processed.
            when s_cnt_active =>
                s_counter_active <= '1';
                if s_section_count_done = '1' then
                    address_gen_sm_next_state <= s_idle;
                end if;
            
            when others => address_gen_sm_next_state <= s_reset;
        end case;
    end process;
    
--! Process for state assignment of the statemachine.
    process(clk)
    begin
        if rising_edge(clk) then
            if reset = '1' then
                address_gen_sm_current_state <= s_reset;
            else
                address_gen_sm_current_state <= address_gen_sm_next_state;
            end if;
        end if;
    end process;
    
--! Process for address calculation. The address will be incremented for each cycle 
--! cnt_en holds a logic high-signal. If SUPPORT_MULTIPLE_SECTIONS (generic) was set to 
--! 'true' the configured start address will be incremented by the current section 
--! offset if no byte is left for the current section. The r_current_address is 
--! once again incremented by r_current_section_offset after the last section was processed 
--! which has to be taken into consideration if this address is used for comparison 
--! (only if SUPPORT_MULTIPLE_SECTIONS was set to 'true').
    mem_address_calc : process(clk)
    begin
        if rising_edge(clk) then
            if reset = '1' then 
                r_current_address <= to_unsigned(0, r_current_address'length);
            else
    -- Copy start address into shadow register for internal operation
                if s_address_calc_setup = '1' then
                    r_current_address <= unsigned(section_addr);
    -- Increment the current address by the number of bytes of a word (4 or 8) if the bus sends a data valid signal
                elsif cnt_en = '1' and s_counter_active = '1' then
                    r_current_address <= r_current_address + to_unsigned(c_number_of_bytes_per_word, ADDRESS_BIT_WIDTH);
    -- Increment the current address by the section size if previous section is done
                elsif s_byte_count_done = '1' and s_counter_active = '1' and SUPPORT_MULTIPLE_SECTIONS = true then
                    r_current_address <= unsigned(section_addr) + r_current_section_offset;
                end if;
            end if;
        end if; 
    end process;
    
--! Process for counting the remaining bytes of the current section. For each cycle the cnt_en
--! signal holds a '1' the counter is decremented by the bus width in byte.
    byte_counter : process(clk)
    begin
        if rising_edge(clk) then
            if reset = '1' then
                s_byte_count_done   <= '0';
                r_bytes_left        <= to_signed(0, r_bytes_left'length);
            else
    -- Copy section_size configuration into shadow register for internal operation.
                if s_address_calc_setup = '1' then
                    s_byte_count_done <= '0';
                    r_bytes_left <= signed(section_size);
    -- Start calculation of bytes remaining for determining bus access type.
                elsif s_counter_active = '1' then
        -- Check if there are bytes left to be requested, otherwise signal 'done'.
                    if (r_bytes_left-1) < 0 then
                        s_byte_count_done <= '1';
                        r_bytes_left <= signed(section_size);   -- reload r_bytes_left for next section
        -- Decrement the number of remaining bytes by the number of bytes of a word, if the memory 
        -- bus sends a valid signal for the current data.
                    elsif cnt_en = '1' then
                        s_byte_count_done <= '0';
                        r_bytes_left <= r_bytes_left - to_signed(c_number_of_bytes_per_word, ADDRESS_BIT_WIDTH);
        -- Set default to byte_counter not being done yet.
                    else
                        s_byte_count_done <= '0';
                    end if;
                end if;
            end if;
        end if;
    end process;
    
--! Process for counting the remaining sections and calculating the address offset 
--! for the next section. The number of sections is decremented every time the 
--! byte_counter is done, whereas the address offset is incremented by the configured 
--! section_offset.
    section_counter : process(clk)
    begin
        if rising_edge(clk) then
            if reset = '1' then
                s_section_count_done    <= '0';
                r_current_section_count <= to_signed(0, r_current_section_count'length);
                r_current_section_offset <= to_unsigned(0, r_current_section_offset'length);
            else
    -- Copy section_count and section_offset configuration into shadow registers for internal operation.
                if s_address_calc_setup = '1' then
                    s_section_count_done <= '0';
                    if SUPPORT_MULTIPLE_SECTIONS = true then
                        r_current_section_count <= signed(section_count);
                        r_current_section_offset <= unsigned(section_offset);
                    else
                        r_current_section_count <= to_signed(1, r_current_section_count'length);
                        r_current_section_offset <= to_unsigned(0, r_current_section_offset'length);
                    end if;
    -- Calculate the remaining number of sections and current section offset.
                elsif s_counter_active = '1' then
       -- Check if all sections have been processed
                    if (r_current_section_count-1) < 0 then
                        s_section_count_done <= '1';
       -- Update offset to section start address and the number of remaining sections
                    elsif s_byte_count_done = '1' then
                        s_section_count_done <= '0';
                        r_current_section_count <= r_current_section_count - 1;
                        r_current_section_offset <= r_current_section_offset + unsigned(section_offset);
                    else
                        s_section_count_done <= '0';
                    end if;
                end if;
            end if;
        end if;
    end process;
    
--! Process for calculating burst_length and determining if a burst is currently 
--! possible depending on the number of bytes left. If SUPPORT_VARIABLE_BURST_LENGTH 
--! (generic) was set to 'true', burst_length can range between max_burst_length 
--! and r_bytes_left > c_number_of_bytes_per_word (4 or 8). If set to 'false', 
--! burst_length can only equate to max_burst_length. In all other cases burst_length
--! and s_burst_possible is set to '0'. 
    burst_calc : process(clk)
    begin
        if rising_edge(clk) then
            if reset = '1' then
                s_actual_burst_length <= (others => '0');
                s_burst_possible <= '0';
            else
    -- Check if there are only enough bytes for a single beat left
                if unsigned(r_bytes_left) < (to_unsigned(c_number_of_bytes_per_word, ADDRESS_BIT_WIDTH) + 1) then
                    s_actual_burst_length <= (others => '0');
                    s_burst_possible <= '0';
    -- Check if configured max burst length is not sufficient for a burst (has to be at least two times the number of bytes per word)
                elsif unsigned(max_burst_length) < (to_unsigned(c_number_of_bytes_per_word*2, ADDRESS_BIT_WIDTH)) then
                    s_actual_burst_length <= (others => '0');
                    s_burst_possible <= '0';
    -- Determine burst length if variable burst length is configured
                elsif SUPPORT_VARIABLE_BURST_LENGTH = true then
        -- If the number of remaining bytes is less than max burst length, use remaining bytes as burst length
                    if unsigned(r_bytes_left) < unsigned(max_burst_length) then
                        s_actual_burst_length <= std_logic_vector(r_bytes_left(BURST_LENGTH_WIDTH-1 downto 0));
                        s_burst_possible <= '1';
        -- Otherwise, use max burst length
                    else
                        s_actual_burst_length <= max_burst_length(BURST_LENGTH_WIDTH-1 downto 0);
                        s_burst_possible <= '1';
                    end if;
    -- Otherwise, allow burst only when the number of remaining bytes is greater or equal to max burst length
                else
                    if unsigned(r_bytes_left) < unsigned(max_burst_length) then
                        s_actual_burst_length <= (others => '0');
                        s_burst_possible <= '0';
                    else
                        s_actual_burst_length <= max_burst_length(BURST_LENGTH_WIDTH-1 downto 0);
                        s_burst_possible <= '1';
                    end if;
                end if;
            end if;
        end if;
    end process;

end architecture;
