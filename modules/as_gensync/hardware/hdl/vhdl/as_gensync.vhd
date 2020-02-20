----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_gensync
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Alexander Zoellner
--
-- Modified:       2019-02-18, Philip Manke: New slaveregister interface
--
-- Description:    This module receives an image data stream with STROBE 
--                 signals and generates VSYNC and HSYNC signals according 
--                 to image size configuration.
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
--! @file  as_gensync.vhd
--! @brief This module generates VSYNC and HSYNC signals for a given image data stream.
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

library asterics;
use asterics.helpers.all;

--! \addtogroup as_gensync
--!  @{

entity as_gensync is
generic(
    DATA_WIDTH              : integer := 32;
    MEM_ADDRESS_BIT_WIDTH   : integer := 32
);
port(
    Clk             : in std_logic;
    Reset           : in std_logic;

    DATA_IN         : in std_logic_vector(DATA_WIDTH-1 downto 0);
    STROBE_IN       : in std_logic;
    STALL_OUT       : out std_logic;

    DATA_OUT        : out std_logic_vector(DATA_WIDTH-1 downto 0);
    STROBE_OUT      : out std_logic;
    STALL_IN        : in std_logic;
    HSYNC_OUT       : out std_logic;
    VSYNC_OUT       : out std_logic;

    --! Slave register interface
    slv_ctrl_reg : in slv_reg_data(0 to 2);
    slv_status_reg : out slv_reg_data(0 to 2);
    slv_reg_modify : out std_logic_vector(0 to 2);
    slv_reg_config : out slv_reg_config_table(0 to 2)
);
end as_gensync;

--! @}

architecture RTL of as_gensync is

constant MEM_NUMBER_OF_BYTES_PER_WORD   : natural := DATA_WIDTH/8;

-- signal declaration
signal reg_x_resolution_config : std_logic_vector(MEM_ADDRESS_BIT_WIDTH - 1 downto 0);
signal reg_frame_size_config : std_logic_vector(MEM_ADDRESS_BIT_WIDTH - 1 downto 0);
  -- Slave register configuration:
  -- Allows for "dynamic" configuration of slave registers
  -- Possible values and what they mean: 
  -- "00": Register "off". Register will not be available and won't be implemented -> No hardware resource utilization.
  -- "01": From HW view: Status register. Data transport from hardware to software. HW can only write, SW can only read.
  -- "10": From HW view: Control register. Data transport from software to hardware. HW can only read, SW can only write.
  -- "11": Combined Read/Write register. Data transport in both directions. 
  --       When both sides attempt to write simultaniously, only the HW gets to write.
  --       These registers use both the slv_ctrl_reg and slv_status_reg ports for communication.
constant slave_register_configuration : slv_reg_config_table(0 to 2) :=
                    ("11","10","10");

signal r_frame_size_count : signed(MEM_ADDRESS_BIT_WIDTH - 1 downto 0);
signal r_x_resolution_count : signed(MEM_ADDRESS_BIT_WIDTH - 1 downto 0);
signal r_hsync, r_vsync, r_strobe, r_enable : std_logic;
signal r_data   : std_logic_vector(DATA_WIDTH-1 downto 0);
signal s_stall : std_logic;
signal enable_sync_signals : std_logic;

begin

    slv_reg_config <= slave_register_configuration;
    slv_reg_modify <= (others => '0');
    slv_status_reg <= (others => (others => '0'));
    reg_x_resolution_config <= slv_ctrl_reg(1);
    reg_frame_size_config <= slv_ctrl_reg(2);

    s_stall <= STALL_IN;
    enable_sync_signals <= slv_ctrl_reg(0)(16);

    
--! Only allow output signals if no STALL is set. If STALL is set, all
--! currently available output signals are stored until STALL is repealed.
    gen_enable : process(clk)
    begin
        if rising_edge(clk) then
            if Reset = '1' then
                r_enable <= '0';
            else 
                r_enable <= not s_stall;
            end if;
        end if;
    end process;

--! Generate VSYNC signal at the beginning of every frame depending on 
--! configured framesize in reg_frame_size_config (e.g. 307200 for a 
--! 640x480 frame).
    vsync_gen : process(clk)
    begin
        if rising_edge(clk) then
            if Reset = '1' then
                r_vsync <= '0';
                r_frame_size_count <=  to_signed(0, r_frame_size_count'length);
            elsif r_enable = '1' then
                if enable_sync_signals = '1' and STROBE_IN = '1' then
                    if r_frame_size_count - 1 < 0 then
                        r_vsync <= '1';
                        r_frame_size_count <= signed(reg_frame_size_config) - MEM_NUMBER_OF_BYTES_PER_WORD;
                    else
                        r_vsync <= '0';
                        r_frame_size_count <= r_frame_size_count - to_signed(MEM_NUMBER_OF_BYTES_PER_WORD, MEM_ADDRESS_BIT_WIDTH);
                    end if;
                else
                   r_vsync <= '0';
                end if;
            end if;
        end if;
    end process;

--! Generate HSYNC signal at the beginning of every line depending on 
--! configured linesize in reg_x_resolution config (e.g. 640 for a 
--! 640x480 frame).
    hsync_gen : process(clk)
    begin
        if rising_edge(clk) then
            if Reset = '1' then
                r_hsync <= '0';
                r_x_resolution_count <= to_signed(0, r_x_resolution_count'length);
            elsif r_enable = '1' then
                if enable_sync_signals = '1' and STROBE_IN = '1' then
                    if r_x_resolution_count - 1 < 0 then
                        r_hsync <= '1';
                        r_x_resolution_count <= signed(reg_x_resolution_config) - MEM_NUMBER_OF_BYTES_PER_WORD;
                    else 
                        r_hsync <= '0';
                        r_x_resolution_count <= r_x_resolution_count - to_signed(MEM_NUMBER_OF_BYTES_PER_WORD, MEM_ADDRESS_BIT_WIDTH);
                    end if;
                else
                    r_hsync <= '0';
                end if;
            end if;
        end if;
    end process;

--! Delay output STROBE signal by one cycle to synchronize it with 
--! possible VSYNC or HSYNC signals (since both signals depend on 
--! input STROBE).
    strobe_gen : process(clk)
    begin
        if rising_edge(clk) then
            if Reset = '1' then
                r_strobe <= '0';
            elsif r_enable = '1' then
                r_strobe <= STROBE_IN;
            end if;
        end if;
    end process;
    
--! Delay output DATA by one cycle to synchronize it with sync
--! signals (VSYNC, HSYNC and STROBE).  
    data : process(clk)
    begin
       if rising_edge(clk) then
           if Reset = '1' then
               r_data <= (others => '0');
           elsif r_enable = '1' then
               r_data <= DATA_IN;
           end if;
       end if;
    end process;
    
--! Only allow output signals if this module was not given a STALL
--! signal by the following module.
    STROBE_OUT  <= r_strobe and r_enable;
    HSYNC_OUT   <= r_hsync and r_enable;
    VSYNC_OUT   <= r_vsync and r_enable;
    DATA_OUT    <= r_data;
    
--! Propagate STALL signal to prior module. The STALL signal must 
--! not contain any additional logic or combinatoric assignments
--! to keep signal delay to a minimum.
    STALL_OUT   <= s_stall;
    

end architecture;
