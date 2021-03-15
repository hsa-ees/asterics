----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- File:           as_generic_regslice.vhd
-- Entity:         as_generic_regslice
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Philip Manke
--
-- Modified:       
--
-- Description:    This module implements a single configurable 32 bit register slice
--                 for use with the register manager module 'as_regmgr.vhd'.
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
--! @file  as_generic_regslice.vhd
--! @brief This module implements a single configurable 32 bit register.
--! @addtogroup asterics_helpers
--! @{
--! @defgroup as_generic_regslice as_generic_regslice: ASTERICS Slave Register
--! This module implements a single configurable 32 bit register slice
--! for use with the register manager module 'as_regmgr.vhd'.
--! @}
----------------------------------------------------------------------------------

--! @addtogroup as_generic_regslice
--! @{

-- Configurable Read/Write register
library IEEE;
use IEEE.std_logic_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity as_generic_regslice is
generic(
    REG_DATA_WIDTH : integer := 32);
port(
    clk : in std_logic;
    rst_n : in std_logic;
    -- Possible values (from HW view): 
    --      "00" -> No register, 
    --      "01" -> Write-Only (HW -> SW), 
    --      "10" -> Read-Only (HW <- SW), 
    --      "11" -> Read/Write (HW <=> SW)
    register_behaviour : in std_logic_vector(1 downto 0);
    sw_data_in : in std_logic_vector(REG_DATA_WIDTH - 1 downto 0);
    sw_data_out : out std_logic_vector(REG_DATA_WIDTH - 1 downto 0);
    sw_data_in_ena : in std_logic;
    sw_byte_mask : in std_logic_vector(REG_DATA_WIDTH / 8 - 1 downto 0);
    hw_data_in : in std_logic_vector(REG_DATA_WIDTH - 1 downto 0);
    hw_data_out : out std_logic_vector(REG_DATA_WIDTH - 1 downto 0);
    hw_modify : in std_logic);
end entity as_generic_regslice;

--! @}

architecture RTL of as_generic_regslice is

    signal register_content : std_logic_vector(REG_DATA_WIDTH - 1 downto 0);

begin
    -- Output data directly from the register
    sw_data_out <= register_content when register_behaviour(0) = '1' else (others => '-');
    hw_data_out <= register_content when register_behaviour(1) = '1' else (others => '-');
    
    -- Content modify behaviour
    modify_logic:
    process(clk)
    begin
        if rising_edge(clk) then
            if rst_n = '0' then
                register_content <= (others => '0');
            else
                -- May data be written from hardware (from PL)?
                if hw_modify = '1' and register_behaviour(0) = '1' then
                    register_content <= hw_data_in;
                -- May data be written from software (from PS)?
                elsif sw_data_in_ena = '1' and register_behaviour(1) = '1' then
                    for B in 0 to (REG_DATA_WIDTH / 8 - 1) loop
                        if sw_byte_mask(B) = '1' then
                            register_content(B * 8 + 7 downto B * 8) <= sw_data_in(B * 8 + 7 downto B * 8);
                        end if;
                    end loop;
                end if;
            end if;
        end if;
    end process;

end architecture RTL;
