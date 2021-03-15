----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- File:           as_threshold.vhd
-- Entity:         as_threshold
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Michael Schaeferling
--
-- Modified:       2019-07-10 Philip Manke - New Slaveregister interface, remove
--                       XRES, YRES, update generics
--
-- Description:    This module thresholds values of an image data stream.
--                 The module in configured by setting minimum and maximum values 
--                 (using the configuration register e.g. by using the driver).
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
--! @file as_threshold.vhd
--! @brief This module band-thresholds values of an image data stream.
--! @addtogroup asterics_modules
--! @{
--! @defgroup as_threshold as_threshold: Two-Value Thresholding
--! This module implements thresholding using two threshold values.
--! The module must be configured via software.
--! @}
----------------------------------------------------------------------------------

--! @addtogroup as_threshold
--! @{

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

library asterics;
use asterics.helpers.all;

entity as_threshold is
  generic (
    DATA_WIDTH  : integer := 8
  );
  port (
    Clk         : in  std_logic;
    Reset       : in  std_logic;
    Ready       : out std_logic;

    -- IN ports
    VSYNC_IN        : in  std_logic;
    HSYNC_IN        : in  std_logic;
    STROBE_IN       : in  std_logic;
    DATA_IN         : in  std_logic_vector(DATA_WIDTH-1 downto 0);
    
    SYNC_ERROR_IN   : in  std_logic;
    PIXEL_ERROR_IN  : in  std_logic;
    STALL_OUT       : out std_logic;

    -- OUT ports
    VSYNC_OUT       : out std_logic;
    HSYNC_OUT       : out std_logic;
    STROBE_OUT      : out std_logic;
    DATA_OUT        : out std_logic_vector(DATA_WIDTH-1 downto 0);
    
    SYNC_ERROR_OUT  : out std_logic;
    PIXEL_ERROR_OUT : out std_logic;
    STALL_IN        : in  std_logic;

    --! Slave register interface
    slv_ctrl_reg : in slv_reg_data(0 to 1);
    slv_status_reg : out slv_reg_data(0 to 1);
    slv_reg_modify : out std_logic_vector(0 to 1);
    slv_reg_config : out slv_reg_config_table(0 to 1)
  );
end as_threshold;

--! @}

architecture RTL of as_threshold is
-- Slave register configuration:
-- Allows for "dynamic" configuration of slave registers
-- Possible values and what they mean: 
-- "00": Register "off". Register will not be available and won't be implemented -> No hardware resource utilization.
-- "01": HW -> SW, Status register only. Data transport from hardware to software. HW can only write, SW can only read.
-- "10": HW <- SW, Control register only. Data transport from software to hardware. HW can only read, SW can only write.
-- "11": HW <=> SW, Combined Read/Write register. Data transport in both directions. ! Higher hardware resource utilization !
--       When both sides attempt to write simultaniously, only the HW gets to write.
--       These registers use both the slv_ctrl_reg and slv_status_reg ports for communication.
constant slave_register_configuration : slv_reg_config_table(0 to 1) := ("11","11");


-- Parameters
signal parameter_1_reg : std_logic_vector(31 downto 0);
signal parameter_2_reg : std_logic_vector(31 downto 0);
signal thresh_1 : std_logic_vector(11 downto 0);
signal thresh_2 : std_logic_vector(11 downto 0);

signal fixval_a : std_logic_vector(11 downto 0);
signal fixval_b : std_logic_vector(11 downto 0);
signal fixval_c : std_logic_vector(11 downto 0);

signal usefix_a, usefix_b, usefix_c : std_logic;


begin

slv_reg_config <= slave_register_configuration;

parameter_1_reg <= slv_ctrl_reg(0);
parameter_2_reg <= slv_ctrl_reg(1);
slv_status_reg <= (others => (others => '0'));
slv_reg_modify <= (others => '0');


assert (DATA_WIDTH <= 12) report "Data width must be less or equal 12." severity failure;

-- Stateless module, thus instantly ready:
Ready <= '1';


thresh_1 <= parameter_1_reg(11 downto  0);
thresh_2 <= parameter_1_reg(23 downto 12);

usefix_a <= parameter_1_reg(28);
usefix_b <= parameter_1_reg(29);
usefix_c <= parameter_1_reg(30);

fixval_a <= parameter_2_reg(11 downto  0);
fixval_b <= parameter_2_reg(23 downto 12);
fixval_c <= parameter_1_reg(27 downto 24) & parameter_2_reg(31 downto 24);




VSYNC_OUT  <= VSYNC_IN;
HSYNC_OUT  <= HSYNC_IN;
STROBE_OUT <= STROBE_IN;

SYNC_ERROR_OUT <= SYNC_ERROR_IN;
PIXEL_ERROR_OUT <= PIXEL_ERROR_IN;
STALL_OUT <= STALL_IN;


process (DATA_IN, usefix_a, fixval_a, usefix_b, fixval_b, usefix_c, fixval_c) 
begin
  -- a
  if (unsigned(DATA_IN) < unsigned(thresh_1)) then
    if (usefix_a = '0') then
      DATA_OUT <= DATA_IN;
    else
      DATA_OUT <= fixval_a(DATA_WIDTH-1 downto 0);
    end if;
  
  -- c
  elsif (unsigned(DATA_IN) > unsigned(thresh_2)) then
    if (usefix_c = '0') then
      DATA_OUT <= DATA_IN;
    else
      DATA_OUT <= fixval_c(DATA_WIDTH-1 downto 0);
    end if;
      
  -- b
  else 
    if (usefix_b = '0') then
      DATA_OUT <= DATA_IN;
    else
      DATA_OUT <= fixval_b(DATA_WIDTH-1 downto 0);
    end if;
  end if;
  
end process;

end RTL;
