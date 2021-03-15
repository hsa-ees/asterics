----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_picam
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Thomas Izycki
--
-- Description:    This module receives image data over AXI stream, converts the image  
--                 to grayscale and provides AS_STREAM compatible image data signals.
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
--! @file  as_picam.vhd
--! @brief Connects AXI stream to AS_STREAM (converts color image to grayscale).
--! @addtogroup asterics_modules
--! @{
--! @defgroup as_picam as_picam: Raspberry Pi Camera Adapter
--! Implements an AXI-Stream to AsStream adapter.
--! For use with the Raspberry Pi Camera.
--! Converts color image to grayscale.
--! @}
----------------------------------------------------------------------------------

--! @addtogroup as_picam
--! @{
 

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

library asterics;
use asterics.helpers.all;


entity as_picam is
	generic (
        -- Width of the input and output data port
        S_AXI_DATA_WIDTH : integer := 32;
        DATA_WIDTH       : integer := 8;

        RES_X : integer := 1280;
        RES_Y : integer := 720
    );
    port (

        -- Ports of Axi Slave Bus Interface S_AXIS
        s_axis_tdata	: in  std_logic_vector(31 downto 0);
        s_axis_aclk     : in  std_logic;
        s_axis_aresetn  : in  std_logic;
        s_axis_tvalid	: in  std_logic;
        s_axis_tuser	: in  std_logic;
        s_axis_tlast	: in  std_logic;
        s_axis_tready	: out std_logic;

        -- AsStream out ports
        VSYNC_OUT      : out std_logic;
        VCOMPLETE_OUT  : out std_logic;
        HSYNC_OUT      : out std_logic;
        STROBE_OUT     : out std_logic;
        DATA_OUT       : out std_logic_vector(DATA_WIDTH - 1 downto 0);
        STALL_IN       : in  std_logic;

        -- Enable camera signal
        CAM_ENABLE_OUT  : out std_logic;

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
end as_picam;

--! @}

architecture RTL of as_picam is

    -- signal reset : std_logic;
    signal clk, reset : std_logic;

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

    constant c_data_counter_bits : natural := integer(ceil(log2(real(RES_X*RES_Y))));
    constant c_frame_width : signed(31 downto 0) := to_signed(RES_X, 32);

    signal run, run_last, run_reset, run_once, run_once_reset : std_logic;
    signal s_module_set_enabled, s_module_set_disabled, s_module_enabled : std_logic;
    signal s_state_reg_frame_done, s_state_reg_frame_done_last : std_logic;

    signal s_vsync_out, s_hsync_out, s_vcomplete_out, s_strobe_out : std_logic;
    signal r_data_out : std_logic_vector(7 downto 0);

    signal r_x_resolution_count : signed(31 downto 0);

begin

clk     <= s_axis_aclk;
reset   <= not s_axis_aresetn;


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


run       <= control(1);
run_once  <= control(2);

control_reset(1) <= run_reset;
control_reset(2) <= run_once_reset;
control_reset(15 downto 3) <= (others => '0');

state <= (
      0 => s_state_reg_frame_done,
      others => '0'
    );


frame_done_process : process(Clk)
  variable p_data_counter : unsigned(c_data_counter_bits-1 downto 0);
begin
  if (Clk'event and Clk = '1') then

    run_last <= run;

    if ( (Reset = '1') or
        -- reset counter for subsequent frames (free run mode)
        ( (s_axis_tvalid = '1') and ( s_axis_tuser = '1') ) or
        -- reset counter for first frame, especially important for single shot mode
        -- (else the old counter value would persist until a new frame arrives)
        ( ( run_last = '0' ) and ( run = '1' ) ) ) then
      p_data_counter := to_unsigned(1, p_data_counter'length);
      s_state_reg_frame_done <= '0';
      s_state_reg_frame_done_last <= '0';

    elsif ( s_axis_tvalid = '1') then
      p_data_counter := p_data_counter + 1;
    end if;

    if ( p_data_counter = to_unsigned((RES_X*RES_Y), p_data_counter'length) ) then
      s_state_reg_frame_done <= '1';
    end if;

    s_state_reg_frame_done_last <= s_state_reg_frame_done;

  end if;
end process;


-- enable data processing and forwarding at start of frame and when triggered by software
s_module_set_enabled  <= run and s_axis_tuser and s_axis_tvalid;

s_module_set_disabled <= s_state_reg_frame_done and not(run);  

-- this process keeps signal 's_module_enabled' up for a frame (to avoid frame-fragments in the pipeline)
sensor_enable : process(Clk)
begin
  if (Clk'event and Clk = '1') then
    if ( (Reset = '1') ) then
        run_reset       <= '1';
        run_once_reset  <= '1';
        s_module_enabled  <= '0';
    else
        run_reset      <= '0';
        run_once_reset <= '0';
      
      if ( s_module_set_enabled = '1' ) then
 
        s_module_enabled <= '1';

        -- if additionally the 'RunOnce' flag is set, reset both 'Run' and 'RunOnce' flags:
        if ( run_once = '1' ) then
          run_reset      <= '1';
          run_once_reset <= '1';
        end if;

      elsif ( s_module_set_disabled = '1' ) then   
        s_module_enabled <= '0';
      end if;

    end if;
  end if;
end process;

-- Convert 32 bit ABGR image data to 8 bit grayscale
grayscale_conv : process (clk)
variable p_red_result:   unsigned (7 downto 0);
variable p_green_result: unsigned (7 downto 0);
variable p_blue_result:  unsigned (7 downto 0);
variable p_result:       unsigned (7 downto 0);
begin
if rising_edge (clk) then
    if reset = '1' then
        r_data_out <= (others => '0');
    else
        p_result        := (others => '0');
        p_blue_result   := (others => '0');
        p_green_result  := (others => '0');
        p_red_result    := (others => '0');
        p_blue_result   := (unsigned(s_axis_tdata(23 downto 16)) srl 4) + (unsigned(s_axis_tdata(7 downto 0)) srl 5);
        p_green_result  := (unsigned(s_axis_tdata(15 downto 8)) srl 1) + (unsigned(s_axis_tdata(15 downto 8)) srl 4);
        p_red_result    := (unsigned(s_axis_tdata(7 downto 0)) srl 2) + (unsigned(s_axis_tdata(23 downto 16)) srl 5);
        p_result        := p_red_result + p_green_result + p_blue_result;
        r_data_out      <= std_logic_vector(p_result);
    end if;
end if;
end process;

-- Generate HSYNC signal at the beginning of every line
-- s_axis_tlast indicates last pixel of a line and is not used
hsync_gen : process(clk)
begin
    if rising_edge(clk) then
        if reset = '1' then
            s_hsync_out <= '0';
            r_x_resolution_count <= to_signed(0, r_x_resolution_count'length);
        elsif  (((s_axis_tuser = '1') and (run = '1')) or
                (s_module_enabled = '1')) then
            if (s_axis_tvalid = '1') then
                if r_x_resolution_count - 1 < 0 then
                    s_hsync_out <= '1';
                    r_x_resolution_count <= c_frame_width - 1;
                else 
                    s_hsync_out <= '0';
                    r_x_resolution_count <= r_x_resolution_count - to_signed(1, 32);
                end if;
            else
                s_hsync_out <= '0';
            end if;
        else
            s_hsync_out <= '0';
        end if;
    end if;
end process;

strobe_gen : process (clk)
begin
    if rising_edge (clk) then
        if reset = '1' then
            s_strobe_out    <= '0';
        elsif (((s_axis_tuser = '1') and (run = '1')) or (s_module_enabled = '1')) then
            if s_axis_tvalid = '1' then
                s_strobe_out   <= '1';
            else
                s_strobe_out <= '0';
            end if;
        else
            s_strobe_out <= '0';
        end if;
    end if;
end process;

vsync_gen : process (clk)
begin
    if rising_edge (clk) then
        if reset = '1' then
            s_vsync_out     <= '0';
        elsif ((s_module_set_enabled ='1') or (s_module_enabled = '1')) then
            s_vsync_out     <= s_axis_tuser;
        else
            s_vsync_out     <= '0';
        end if;
    end if;
end process;

vcomplete_gen : process (clk)
begin
    if rising_edge (clk) then
        if reset = '1' then
            s_vcomplete_out    <= '0';
        elsif ( (s_state_reg_frame_done = '1') and (s_state_reg_frame_done_last = '0') ) then
            s_vcomplete_out <= '1';
        else
            s_vcomplete_out <= '0';
        end if;
    end if;
end process;

-- output signals
VSYNC_OUT       <= s_vsync_out;
VCOMPLETE_OUT   <= s_vcomplete_out;
HSYNC_OUT       <= s_hsync_out;
STROBE_OUT      <= s_strobe_out;
DATA_OUT        <= r_data_out;

-- camera is always enabled and data can be always accepted
-- STALL_IN is ignored
CAM_ENABLE_OUT  <= '1';
s_axis_tready   <= '1';


end RTL;
