----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  Copyright (C) Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_crop
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Michael Schaeferling
--
-- Modified:       
--
-- Description:    Crops a section defined by the points (x_left,y_top)
--                 and (x_right,y_bottom) from a as_stream.
--
-- Revision 0.01 - File Created
-- Rivision 1.00 - Changed name to as_crop and made ready for git check-in
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
--! @file  as_crop.vhd
--! @brief Crops a section defined by the points (x_left,y_top)
--         and (x_right,y_bottom) from a as_stream.
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity as_crop is
  generic (
    DIN_WIDTH  : integer := 32;
    DOUT_WIDTH : integer := 32
  );
  port (
    Clk         : in  std_logic;
    Reset       : in  std_logic;
    Ready       : out std_logic;

    -- IN ports
    VSYNC_IN    : in  std_logic;
    HSYNC_IN    : in  std_logic;
    STROBE_IN   : in  std_logic;
    DATA_IN     : in  std_logic_vector(DIN_WIDTH-1 downto 0);
    
    SYNC_ERROR_IN  : in  std_logic;
    DATA_ERROR_IN : in  std_logic;
    STALL_OUT      : out std_logic;
    
    -- OUT ports
    VSYNC_OUT   : out std_logic;
    HSYNC_OUT   : out std_logic;
    STROBE_OUT  : out std_logic;
    DATA_OUT    : out std_logic_vector(DOUT_WIDTH-1 downto 0);
    
    SYNC_ERROR_OUT  : out std_logic;
    DATA_ERROR_OUT : out std_logic;
    STALL_IN        : in  std_logic;

    --! Slave register interface
    slv_ctrl_reg : in slv_reg_data(0 to 3);
    slv_status_reg : out slv_reg_data(0 to 3);
    slv_reg_modify : out std_logic_vector(0 to 3);
    slv_reg_config : out slv_reg_config_table(0 to 3)
  );
end as_crop;


architecture RTL of as_crop is

  signal int_reset : std_logic;
  
  -- Slave register configuration:
  -- Allows for "dynamic" configuration of slave registers
  -- Possible values and what they mean: 
  -- "00": Register "off". Register will not be available and won't be implemented -> No hardware resource utilization.
  -- "01": From HW view: Status register. Data transport from hardware to software. HW can only write, SW can only read.
  -- "10": From HW view: Control register. Data transport from software to hardware. HW can only read, SW can only write.
  -- "11": Combined Read/Write register. Data transport in both directions. 
  --       When both sides attempt to write simultaniously, only the HW gets to write.
  --       These registers use both the slv_ctrl_reg and slv_status_reg ports for communication.
  constant slave_register_configuration : slv_reg_config_table(0 to 3) :=
                          ("11","10","10","01");
  signal status, control, control_new, control_reset : std_logic_vector(15 downto 0);

  signal r_vsync   : std_logic;
  signal r_hsync   : std_logic;
  signal r_strobe  : std_logic;
  signal r_data    : std_logic_vector(DOUT_WIDTH-1 downto 0);

  signal x_left    : unsigned(15 downto 0);
  signal x_right   : unsigned(15 downto 0);

  signal y_top     : unsigned(15 downto 0);
  signal y_bottom  : unsigned(15 downto 0);

  signal x_cnt     : unsigned(15 downto 0);
  signal y_cnt     : unsigned(15 downto 0);

  signal r_data_counter : unsigned(31 downto 0);

begin


  -- Assign the register configuration to the register interface.
  slv_reg_config <= slave_register_configuration;
  
  -- Control portion of the status and control register
  control <= slv_ctrl_reg(0)(31 downto 16);

  -- Connect the control register ports to the respective control signals
  x_left   <= unsigned(slv_ctrl_reg(1)(31 downto 16));
  y_top    <= unsigned(slv_ctrl_reg(1)(15 downto 0));
  x_right  <= unsigned(slv_ctrl_reg(2)(31 downto 16));
  y_bottom <= unsigned(slv_ctrl_reg(2)(15 downto 0));
  
  -- Connect the status signals to the state registers
  slv_status_reg(0) <= control_new & state;
  slv_status_reg(3) <= std_logic_vector(r_data_counter);
  
  -- Enable "always-on" state register updates
  slv_reg_modify(3) <= '1';

  -- Handle the control_reset signal 
  -- and set the modify bit for the status and control register, as necessary
  status_control_update_logic: process(control, control_reset, slv_ctrl_reg, state, reset)
    variable var_control_new : std_logic_vector(15 downto 0);
  begin
    -- int_reset control and status register modify bit
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


  int_reset <= Reset or control(0);
  Ready <= not int_reset;
  
  status <= (0 <= not int_reset, (others => '0'));
  control_reset <= (others => '0');


STALL_OUT <= STALL_IN;

SYNC_ERROR_OUT <= SYNC_ERROR_IN;
DATA_ERROR_OUT <= DATA_ERROR_IN;


counter_proc: process (Clk)
begin
  if (Clk'event and Clk = '1') then

    if (int_reset = '1') then
      x_cnt <= (others => '1');
      y_cnt <= (others => '1');
      r_strobe <= '0';
      r_data_counter <= (others => '0');
    
   
    else
      
      -- defaults
      r_strobe <= '0';
      
      
      if (STROBE_IN = '1') then
        
        r_data_counter <= r_data_counter + 1;
        
        r_strobe <= '1';
        r_data   <= DATA_IN;
        
        if (HSYNC_IN = '1') then          
          x_cnt <= (others => '0');
          y_cnt <= y_cnt + 1;
        else
          x_cnt <= x_cnt + 1;
        end if;
        
        if (VSYNC_IN = '1') then
          
          y_cnt <= (others => '0');  
        end if;
        
      end if;
      
    end if;
  end if;
end process;



output_proc: process (Clk)
begin
  if (Clk'event and Clk = '1') then

    if (int_reset = '1') then
      
      STROBE_OUT <= '0';
         
    else
      
      DATA_OUT <= r_data;
      
      -- defaults for control signals
      STROBE_OUT <= '0';
      VSYNC_OUT <= '0';
      HSYNC_OUT <= '0';
      
      if (r_strobe = '1') then
      
        -- generate STROBE when in selected area:
        if (x_cnt >= x_left) and (x_cnt <= x_right) and 
           (y_cnt >= y_top)  and (y_cnt <= y_bottom) then
          STROBE_OUT <= '1';
        end if;
        
        -- generate HSYNC on first pixel in selected area:
        if (x_cnt = x_left) then
          HSYNC_OUT <= '1';
        
          -- also generate VSYNC on first lines first pixel in selected area:
          if (y_cnt = y_top) then
            VSYNC_OUT <= '1';
          end if;

        end if;

      end if;
      
    end if;
  end if;
end process;



end RTL;
