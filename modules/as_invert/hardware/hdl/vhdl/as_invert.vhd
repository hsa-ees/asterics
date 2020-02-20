----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_invert
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Michael Schaeferling
--
-- Modified:       20.11.2018: Philip Manke: Update for new slave register
--                   interface. Remove x/yres ports. Add v/hcomplete. Unify port names
--
-- Description:    This module inverts an image data stream.
--                 Functionality can be enabled or disabled (by setting the 
--                 configuration register e.g. using the driver).
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
--! @file  as_invert.vhd
--! @brief Invert an image data stream (function can be en- or disabled).
----------------------------------------------------------------------------------


--! \addtogroup as_invert
--!  @{

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

--library asterics;
--use asterics.helpers.all;

use work.helpers.all;

entity as_invert is
    generic (
        -- Width of the input and output data port
        DATA_WIDTH : integer := 8
    );
    port (
        clk         : in  std_logic;
        reset       : in  std_logic;
        ready       : out std_logic;

        -- AsStream in ports
        vsync_in      : in  std_logic;
        vcomplete_in  : in  std_logic;
        hsync_in      : in  std_logic;
        hcomplete_in  : in  std_logic;
        strobe_in     : in  std_logic;
        data_in       : in  std_logic_vector(DATA_WIDTH - 1 downto 0);
        data_error_in : in  std_logic;
        sync_error_in : in  std_logic;
        stall_out     : out std_logic;

        -- AsStream out ports
        vsync_out      : out std_logic;
        vcomplete_out  : out std_logic;
        hsync_out      : out std_logic;
        hcomplete_out  : out std_logic;
        strobe_out     : out std_logic;
        data_out       : out std_logic_vector(DATA_WIDTH - 1 downto 0);
        data_error_out : out std_logic;
        sync_error_out : out std_logic;
        stall_in       : in  std_logic;


        --! Slave register interface:
        --! Control registers. SW -> HW data transport
        slv_ctrl_reg : in slv_reg_data(0 to 0);
        --! Status registers. HW -> SW data transport
        slv_status_reg : out slv_reg_data(0 to 0);
        --! Aquivalent to a write enable signal. When HW want's to write into a register, it needs to pulse this signal.
        slv_reg_modify : out std_logic_vector(0 to 0);
        --! Slave register configuration table.
        slv_reg_config : out slv_reg_config_table(0 to 0)
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
    constant slave_register_configuration : slv_reg_config_table(0 to 0) := (0 => "11");
    -- State and control signals
    signal control : std_logic_vector(15 downto 0);
    signal state   : std_logic_vector(15 downto 0);
    signal control_new   : std_logic_vector(15 downto 0);
    signal control_reset : std_logic_vector(15 downto 0);
    signal ready_internal : std_logic;
    
begin

    -- Register interface logic --
    
    -- Assign the register configuration to the register interface.
    slv_reg_config <= slave_register_configuration;
    
    -- Control portion of the status and control register
    control <= slv_ctrl_reg(0)(31 downto 16);

    -- Connect the state signals to the status registers
    slv_status_reg(0) <= control_new & state;

    -- Handle the control_reset signal 
    -- and set the modify bit for the status and control register, as necessary
    status_control_update_logic: process(control, control_reset, slv_ctrl_reg, state, reset)
        variable var_control_new : std_logic_vector(15 downto 0);
    begin
        -- Reset control and status register modify bit
        slv_reg_modify(0) <= '0';
        
        -- Clear control bits of the register on module reset
        if reset = '1' then
            control_new <= (others => '0');
        else
            control_new <= control;
        end if;
        
        -- Apply control_reset bit mask
        var_control_new := control and (not control_reset);
        
        -- If either control or state was modified by hardware, set modify bit
        if control /= var_control_new then 
            control_new <= var_control_new;
            slv_reg_modify(0) <= '1';
        end if;
        if state /= slv_ctrl_reg(0)(15 downto 0) then
            slv_reg_modify(0) <= '1';
        end if;
    end process status_control_update_logic;
    
    -- Module logic --

    ready_internal <= not reset;
    ready <= ready_internal;
    

    -- Control reset not utilized in this module
    control_reset <= (others => reset);
    -- Report ready state to software
    state <= (ready_internal, others => '0');


    vsync_out  <= vsync_in;
    vcomplete_out <= vcomplete_in;
    hsync_out  <= hsync_in;
    hcomplete_out <= hcomplete_in;
    strobe_out <= strobe_in;
    -- Invert the data stream, if the respective control bit is set by software
    data_out   <= not data_in when control(1) = '1' else data_in;

    sync_error_out <= sync_error_in;
    data_error_out <= data_error_in;
    stall_out <= stall_in;

end RTL;

