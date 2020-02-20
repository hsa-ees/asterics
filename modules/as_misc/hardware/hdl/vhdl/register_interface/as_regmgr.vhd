----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  Copyright (C) Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- File:           as_regmgr.vhd
-- Entity:         as_regmgr
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Philip Manke
--
-- Modified:       
--
-- Description:    This module implements the registers for any module within
--                 an ASTERICS system. It instantiates and manages a configurable
--                 number of 'as_generic_regslice' modules, each a single 32 bit
--                 register with potentially different read/write access.
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
--! @file as_regmgr.vhd
--! @brief This module instantiates and manages a variable number of 32 bit registers.
----------------------------------------------------------------------------------

library IEEE;
use IEEE.std_logic_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

library asterics;
use asterics.helpers.all;
--use work.helpers.all;

entity as_regmgr is
generic(
    -- Width of the 'sw_address' port
    REG_ADDR_WIDTH : integer := 12;
    -- Width of the register data port 'sw_data_[in/out]'
    REG_DATA_WIDTH : integer := 32;
    -- Width of the portion of the address,
    -- that distinguishes between different modules / register managers
    MODULE_ADDR_WIDTH : integer := 6;
    -- Number of registers associated per manager
    REG_COUNT : integer := 32;
    -- Address of this module / register manager
    MODULE_BASEADDR : integer
    );
port(
    clk : in std_logic;
    rst_n : in std_logic;

    -- Signals from / to AXI Slave (regmgr <=> SW)
    -- Address from software [unused | module address | register address]
    sw_address : in std_logic_vector(REG_ADDR_WIDTH - 1 downto 0);
    -- Data sent to software
    sw_data_out : out std_logic_vector(REG_DATA_WIDTH - 1 downto 0);
    -- Data received from software
    sw_data_in : in std_logic_vector(REG_DATA_WIDTH - 1 downto 0);
    -- Enable signal for HW -> SW transfers
    sw_data_out_ena : in std_logic;
    -- Enable signal for SW -> HW transfers
    sw_data_in_ena : in std_logic;
    -- Byte accurate masking for SW -> HW transfers
    sw_byte_mask : in std_logic_vector(REG_DATA_WIDTH / 8 - 1 downto 0);
    
    -- Signals from / to hardware modules (HW <=> regmgr)
    -- IN and OUT registers facing hardware
    hw_reg_data_out : out slv_reg_data(0 to REG_COUNT - 1);
    hw_reg_data_in : in slv_reg_data(0 to REG_COUNT - 1);
    -- Modify (write enable) bit mask per register
    hw_reg_modify : in std_logic_vector(0 to REG_COUNT - 1);
    -- Constant signal defining in/out capabilities per register
    hw_reg_config : in slv_reg_config_table(0 to REG_COUNT - 1)
    );
end entity as_regmgr;

architecture RTL of as_regmgr is
    
    component as_generic_regslice is
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
    end component;

    constant c_reg_addr_width : integer := REG_ADDR_WIDTH - MODULE_ADDR_WIDTH;

    -- Collection of the data_in_enable inputs of the registers
    signal arr_sw_data_in_ena : std_logic_vector(0 to REG_COUNT - 1);
    
    -- sw_data_out <= register contents
    -- Collection of data outputs from all registers of this module
    signal arr_sw_data_out : slv_reg_data(0 to REG_COUNT - 1);
    
    
begin
    
    -- Handle requests:
    reg_address_decode: process(sw_address, sw_data_in_ena, arr_sw_data_out, sw_data_out_ena, hw_reg_config)
        variable module_address : integer;
        variable register_number : integer;
    begin
        
        -- Set all enable signals to '0'
        arr_sw_data_in_ena <= (others => '0');
        -- Clear data output to software
        sw_data_out <= (others => '0');
        
        -- Split address into module address and register address:
        module_address := to_integer(unsigned(
            sw_address(REG_ADDR_WIDTH - 1 downto 
                       c_reg_addr_width)));
        register_number := to_integer(unsigned(
            sw_address(c_reg_addr_width - 1 downto 0)));
        -- On modify request:
        if sw_data_in_ena = '1' then
        
            -- Check module address - is this the addressed module?
            if module_address = MODULE_BASEADDR and register_number < REG_COUNT then
                
                -- Make sure the addressed register is modifiable by software
                if hw_reg_config(register_number)(1) = '1' then
                    -- Set data in enable for the addressed register
                    arr_sw_data_in_ena(register_number) <= '1';
                else
                    -- For simulation purposes: Complain on "failed" write by software
                    report("Out of bounds write detected for register number: " & integer'image(register_number)
                            & " of module with address: " & integer'image(module_address));
                end if;
            end if;
        
        -- On data request by software
        elsif sw_data_out_ena = '1' then
            
            -- Check module address - is this the addressed module?
            if module_address = MODULE_BASEADDR and register_number < REG_COUNT then
        
                -- Make sure the addressed register is readable by software
                if hw_reg_config(register_number)(0) = '1' then
                    -- Set the sw_data_out port to the addressed registers data output
                    sw_data_out <= arr_sw_data_out(register_number);
                else
                    -- For simulation purposes: Complain on "failed" read by software
                    report("Out of bounds read detected for register number: " & integer'image(register_number)
                            & " of module with address: " & integer'image(module_address));
                end if;
            end if;
        end if;
    end process reg_address_decode;

    -- Register generator:
    -- Generate the maximum register number according to the register configuration table
    -- Registers configured as "00" should be optimized out during optimization phases of synthesis
    module_registers: for N in 0 to REG_COUNT - 1 generate
        
        generic_register_slice: as_generic_regslice
        generic map(
            REG_DATA_WIDTH => REG_DATA_WIDTH
            )
        port map(
            clk => clk,
            rst_n => rst_n,
            register_behaviour => hw_reg_config(N),
            sw_data_in => sw_data_in,
            sw_data_out => arr_sw_data_out(N),
            sw_byte_mask => sw_byte_mask,
            sw_data_in_ena => arr_sw_data_in_ena(N),
            hw_data_in => hw_reg_data_in(N),
            hw_data_out => hw_reg_data_out(N),
            hw_modify => hw_reg_modify(N));
            
    end generate;
    
end architecture RTL;



