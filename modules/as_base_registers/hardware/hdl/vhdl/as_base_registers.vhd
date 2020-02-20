----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_base_registers
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Philip Manke
--
-- Modified:       
--
-- Description:    This module implements the base registers for ASTERICS systems.
--                 These provide basic information such as the ASTERICS version
--                 number, and other internal values to reduce the amount of
--                 manual software configuration necessary to run ASTERICS.
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
--! @file  as_base_registers.vhd
--! @brief Provide internal configuration data to software.
----------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library asterics;
use asterics.helpers.all;

entity as_base_registers is
    generic (
        VERSION_NUMBER : integer := X#01001000#;
        REQ_DRIVER_VERSION : integer := X#00100000#;
        ASTERICS_CONFIG : integer := X#00000000#;
        ASTERICS_MODULES : integer := X#00000000#

    );
    port (
        clk         : in  std_logic;
        reset       : in  std_logic;
        ready       : in  std_logic;
        reset_out   : out std_logic;

        --! Slave register interface:
        --! Control registers. SW -> HW data transport
        slv_ctrl_reg : in slv_reg_data(0 to 6);
        --! Status registers. HW -> SW data transport
        slv_status_reg : out slv_reg_data(0 to 6);
        --! Aquivalent to a write enable signal. When HW want's to write into a register, it needs to pulse this signal.
        slv_reg_modify : out std_logic_vector(0 to 6);
        --! Slave register configuration table.
        slv_reg_config : out slv_reg_config_table(0 to 6)
    );
end as_invert;

--! @}

architecture RTL of as_invert is



    -- Slave register configuration:
    -- Allows for "dynamic" configuration of slave registers
    -- Possible values and what they mean: 
    -- "00": Register "off". Register will not be available and won't be implemented -> No hardware resource utilization.
    -- "01": From HW view: Status register. Data transport from hardware to software. HW can only write, SW can only read.
    -- "10": From HW view: Control register. Data transport from software to hardware. HW can only read, SW can only write.
    -- "11": Combined Read/Write register. Data transport in both directions. 
    --       When both sides attempt to write simultaniously, only the HW gets to write.
    --       These registers use both the slv_ctrl_reg and slv_status_reg ports for communication.
    constant slave_register_configuration : slv_reg_config_table(0 to 6) := (AS_REG_STATUS, AS_REG_STATUS, AS_REG_STATUS,
                AS_REG_CONTROL, AS_REG_STATUS, AS_REG_STATUS, AS_REG_STATUS);
    -- State and control signals
    signal control : std_logic_vector(31 downto 0);
    signal status   : std_logic_vector(31 downto 0);
    

    constant asterics_id : std_logic_vector(31 downto 0) := X"a57e61c5";

    signal ready_internal : std_logic;

begin

    -- Register interface logic --
    
    -- Assign the register configuration to the register interface.
    slv_reg_config <= slave_register_configuration;
    
    -- Control signal
    control <= slv_ctrl_reg(3);

    -- Connect the state signals to the status registers
    slv_status_reg(0) <= asterics_id;
    slv_status_reg(1) <= std_logic_vector(to_unsigned(VERSION_NUMBER, 32));
    slv_status_reg(2) <= std_logic_vector(to_unsigned(REQ_DRIVER_VERSION, 32));
    slv_status_reg(4) <= status;
    slv_status_reg(5) <= std_logic_vector(to_unsigned(ASTERICS_CONFIG, 32));
    slv_status_reg(6) <= std_logic_vector(to_unsigned(ASTERICS_MODULES, 32));

    -- ready signal
    ready_internal <= not reset;
    ready <= ready_internal;
    
    -- TODO: Handle reset_out, control signals and 

    -- Report ready state to software
    status <= (ready_internal, others => '0');

end RTL;

