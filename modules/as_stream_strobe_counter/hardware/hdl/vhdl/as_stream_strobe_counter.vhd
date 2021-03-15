----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2021 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_stream_strobe_counter
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Philip Manke
--
-- Modified:       
--
-- Description:    This module simply counts the number of strobes passed through
--                 the AsStream interface.
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
--! @file  as_stream_strobe_counter.vhd
--! @brief Count strobes passed through an AsStream interface
--! @addtogroup asterics_modules
--! @{
--! @defgroup as_stream_strobe_counter as_stream_strobe_counter: Strobe counter
--! This module simply counts the number of strobes passed through
--! the AsStream interface.
--! @}
----------------------------------------------------------------------------------

--! @addtogroup as_stream_strobe_counter
--! @{

library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

library asterics;
use asterics.helpers.all;



entity as_stream_strobe_counter is
generic(
    DATA_WIDTH : integer := 8
);
port(
    clk : in std_logic;
    reset : in std_logic;

    -- Input AsStream
    strobe_in : in std_logic;
    data_in : in std_logic_vector(DATA_WIDTH - 1 downto 0);
    hsync_in : in std_logic;
    vsync_in : in std_logic;
    hcomplete_in : in std_logic;
    vcomplete_in : in std_logic;
    stall_in : out std_logic;

    -- Output AsStream
    strobe_out : out std_logic;
    data_out : out std_logic_vector(DATA_WIDTH - 1 downto 0);
    hsync_out : out std_logic;
    vsync_out : out std_logic;
    hcomplete_out : out std_logic;
    vcomplete_out : out std_logic;   
    stall_out : in std_logic;

    -- Slave register interface
    -- This module uses a status register @ offset 0 and a control register @ offset 1
    slv_ctrl_reg : in slv_reg_data(0 to 1);
    slv_status_reg : out slv_reg_data(0 to 1);
    slv_reg_modify : out std_logic_vector(0 to 1);
    slv_reg_config : out slv_reg_config_table(0 to 1)
);
end entity as_stream_strobe_counter;

--! @}

architecture RTL of as_stream_strobe_counter is

    constant slave_register_configuration : slv_reg_config_table(0 to 1) := (
            AS_REG_STATUS, AS_REG_CONTROL
        );

    signal counter_reg : unsigned(31 downto 0);
    signal counter_enable : std_logic;
    signal counter_reset : std_logic;

begin

    -- Slave registers:
    slv_reg_config <= slave_register_configuration;
    slv_reg_modify(0) <= '1';
    slv_reg_modify(1) <= '0';

    slv_status_reg(0) <= std_logic_vector(counter_reg);
    slv_status_reg(1) <= (others => '0');

    counter_reset <= slv_ctrl_reg(1)(0);
    counter_enable <= slv_ctrl_reg(1)(1);

    -- Counter process:
    p_count : process(clk) is
    begin
        if rising_edge(clk) then
            if reset = '1' or counter_reset = '1' then
                counter_reg <= (others => '0');
            else
                if strobe_in = '1' and counter_enable = '1' then
                    counter_reg <= counter_reg + 1;
                end if;
            end if;
        end if;
    end process;

    -- Passthrough the AsStream interface:
    strobe_out <= strobe_in;
    data_out <= data_in;
    hsync_out <= hsync_in;
    vsync_out <= vsync_in;
    hcomplete_out <= hcomplete_in;
    vcomplete_out <= vcomplete_in;
    stall_in <= stall_out;

end architecture RTL;
