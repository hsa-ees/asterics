----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- File:           as_sensor_ov7670.vhd
-- Entity:         as_sensor_ov7670
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Michael Schaeferling
--
-- Modified:       
--
-- Description:    OmniVision OV7670 image sensor interface:
--                 Synchronize data into internal system clock domain and
--                 generate appropriate VSYNC and HSYNC signals from camera signals
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
--! @brief OmniVision OV7670 image sensor interface, provides AS_STREAM compatible image data signals.
----------------------------------------------------------------------------------


library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;


-- for Xilinx FIFO macro
--Library UNIMACRO;
--use UNIMACRO.vcomponents.all;

-- for Xilinx XPM FIFO macro
Library xpm;
use xpm.vcomponents.all;


library asterics;
use asterics.helpers.all;

entity as_sensor_ov7670_xpm is
  generic (
    REG_DATA_WIDTH : integer := 32;
    SENSOR_DATA_WIDTH : integer := 8;
    DOUT_WIDTH : integer := 8;

    RES_X : integer := 640;
    RES_Y : integer := 480
  );
  port (
    -- sensor signals
    Sensor_Reset_n       : out std_logic;
    Sensor_PowerDown     : out std_logic;
    Sensor_PixClk        : in  std_logic;
    Sensor_Frame_Valid   : in  std_logic;
    Sensor_Line_Valid    : in  std_logic;
    Sensor_Data          : in  std_logic_vector(SENSOR_DATA_WIDTH-1 downto 0);

    -- pixel port @system_clk
    Clk                  : in  std_logic;
    Reset                : in  std_logic;
    Ready                : out std_logic;

    -- OUT ports
    VSYNC_OUT            : out std_logic;
    HSYNC_OUT            : out std_logic;
    STROBE_OUT           : out std_logic;
    DATA_OUT             : out std_logic_vector(DOUT_WIDTH-1 downto 0);
    VCOMPLETE_OUT        : out std_logic;

    SYNC_ERROR_OUT : out std_logic;
    DATA_ERROR_OUT : out std_logic;
    STALL_IN       : in  std_logic;

    --! Slave register interface
    slv_ctrl_reg : in slv_reg_data(0 to 1);
    slv_status_reg : out slv_reg_data(0 to 1);
    slv_reg_modify : out std_logic_vector(0 to 1);
    slv_reg_config : out slv_reg_config_table(0 to 1)
  );
end as_sensor_ov7670_xpm;


architecture RTL of as_sensor_ov7670_xpm is

  -- Slave register configuration:
  -- Allows for "dynamic" configuration of slave registers
  -- Possible values and what they mean: 
  -- "00": Register "off". Register will not be available and won't be implemented -> No hardware resource utilization.
  -- "01": HW -> SW, Status register only. Data transport from hardware to software. HW can only write, SW can only read.
  -- "10": HW <- SW, Control register only. Data transport from software to hardware. HW can only read, SW can only write.
  -- "11": HW <=> SW, Combined Read/Write register. Data transport in both directions. ! Higher FPGA resource utilization !
  --       When both sides attempt to write simultaniously, only the HW gets to write.
  --       These registers use both the slv_ctrl_reg and slv_status_reg ports for communication.
  constant slave_register_configuration : slv_reg_config_table(0 to 1) := ("11","10");


  ---- control/state
  signal control       : std_logic_vector(15 downto 0);
  signal control_reset : std_logic_vector(15 downto 0);
  signal state         : std_logic_vector(15 downto 0);
  signal parm0_reg     : std_logic_vector(REG_DATA_WIDTH - 1 downto 0);
  --! Signal used as an intermidiate to apply the control_reset logic and then update the register
  signal control_new : std_logic_vector(15 downto 0);

--COMPONENT as_sensor_ov7670_clkdom_fifo_16x13
--  GENERIC (
--    C_FAMILY : string  := "spartan6"
--  );
COMPONENT as_sensor_ov7670_clkdom_fifo_16x13_vivado is
  PORT (
    wr_clk : IN STD_LOGIC;
    wr_rst : IN STD_LOGIC;
    wr_en : IN STD_LOGIC;
    din : IN STD_LOGIC_VECTOR(12 DOWNTO 0);
    full : OUT STD_LOGIC;
    --
    rd_clk : IN STD_LOGIC;
    rd_rst : IN STD_LOGIC;
    rd_en : IN STD_LOGIC;
    dout : OUT STD_LOGIC_VECTOR(12 DOWNTO 0);
    empty : OUT STD_LOGIC
  );
END COMPONENT;

-- Sensor Clock Domain:
signal s_Sensor_Data       : std_logic_vector(SENSOR_DATA_WIDTH-1 downto 0);
signal s_Sensor_Data_delay : std_logic_vector(SENSOR_DATA_WIDTH-1 downto 0);

signal s_Sensor_Frame_Valid, s_Sensor_Frame_Valid_delayed, s_Sensor_Frame_Valid_last : std_logic;
signal s_Sensor_Line_Valid, s_Sensor_Line_Valid_delayed, s_Sensor_Line_Valid_last : std_logic;


signal HSYNC_gen  : std_logic;
signal VSYNC_gen  : std_logic;


signal FIFO_reset             : std_logic;
signal FIFO_Wr_En, FIFO_Rd_En : std_logic;
signal FIFO_Data_In           : std_logic_vector(12 downto 0);  -- 2xSYNC  + DATA
signal FIFO_Data_Out          : std_logic_vector(12 downto 0);  --
signal FIFO_empty             : std_logic;


signal FRAME_DETECT, FRAME_DETECT_last  : std_logic;

signal Reset_Sensor_PixClk : std_logic;
signal Ready_Sensor_PixClk : std_logic;

signal Reset_unsynced, Ready_Sensor_unsynced, Ready_Sensor : std_logic;

signal softreset, softreset_reset : std_logic;
signal run, run_last, run_reset, run_once, run_once_reset : std_logic;
signal sensor_set_enabled, sensor_set_disabled, sensor_enabled : std_logic;

signal s_stobe_out,s_vsync_out, s_hsync_out, s_vcomplete_out : std_logic;

signal s_drop : std_logic;

constant DATA_COUNTER_BITS : natural := integer(ceil(log2(real(RES_X*RES_Y))));
signal state_reg_frame_done, state_reg_frame_done_last : std_logic;


begin

  slv_reg_config <= slave_register_configuration;

  control <= slv_ctrl_reg(0)(31 downto 16);
  slv_status_reg(0) <= control_new & state;
  
  parm0_reg <= slv_ctrl_reg(1);
  
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

assert (SENSOR_DATA_WIDTH = 8) and (DOUT_WIDTH = 8) report "SENSOR_DATA_WIDTH and DOUT_WIDTH must be set to 8. The module processes all 8 bits provided by the OV7670 image sensor." severity failure;


  -- FIFO_DUALCLOCK_MACRO: Dual-Clock First-In, First-Out (FIFO) RAM Buffer
  --                       Artix-7
  -----------------------------------------------------------------
  -- DATA_WIDTH | FIFO_SIZE | FIFO Depth | RDCOUNT/WRCOUNT Width --
  -- ===========|===========|============|=======================--
  --   37-72    |  "36Kb"   |     512    |         9-bit         --
  -----------------------------------------------------------------
--  FIFO_DUALCLOCK_MACRO_inst : FIFO_DUALCLOCK_MACRO
--  generic map (
--      DEVICE                  => "ULTRASCALE", -- Target Device: "VIRTEX5", "VIRTEX6", "7SERIES"
--      ALMOST_FULL_OFFSET      => X"0004",   -- Sets almost full threshold
--      ALMOST_EMPTY_OFFSET     => X"0006",   -- Sets the almost empty threshold
--      DATA_WIDTH              => 13,        -- Valid values are 1-72 (37-72 only valid when FIFO_SIZE="36Kb")
--      FIFO_SIZE               => "18Kb",    -- Target BRAM, "18Kb" or "36Kb"
--      FIRST_WORD_FALL_THROUGH => TRUE       -- Sets the FIFO FWFT to TRUE or FALSE
--  )
--  port map (
--      RST         => FIFO_reset,         -- 1-bit input reset
--      WRCLK       => Sensor_PixClk,      -- 1-bit input write clock
--      WREN        => FIFO_Wr_En,         -- 1-bit input write enable
--      DI          => FIFO_Data_In,       -- Input data, width defined by DATA_WIDTH parameter
--      ALMOSTFULL  => open,               -- 1-bit output almost full
--      FULL        => open,               -- 1-bit output full
--      WRCOUNT     => open,               -- Output write count, width determined by FIFO depth
--      WRERR       => open,               -- 1-bit output write error
      
--      RDCLK       => Clk,                -- 1-bit input read clock
--      RDEN        => FIFO_Rd_En,         -- 1-bit input read enable
--      DO          => FIFO_Data_Out,      -- Output data, width defined by DATA_WIDTH parameter
--      ALMOSTEMPTY => open,               -- 1-bit output almost empty
--      EMPTY       => FIFO_empty,         -- 1-bit output empty
--      RDCOUNT     => open,               -- Output read count, width determined by FIFO depth
--      RDERR       => open                -- 1-bit output read error    
--  );
  -- End of FIFO_DUALCLOCK_MACRO_inst instantiation


--XilinxParameterizedMacro,version2018.1
	xpm_fifo_async_inst : xpm_fifo_async
	generic map(
		--DECIMAL
		WRITE_DATA_WIDTH=>13,--DECIMAL
		READ_DATA_WIDTH=>13,--DECIMAL
		FIFO_WRITE_DEPTH=>128,--DECIMAL --2048
		READ_MODE=>"fwft",
		DOUT_RESET_VALUE =>"0",--String
		FULL_RESET_VALUE=>0,--DECIMAL

		WR_DATA_COUNT_WIDTH=>1,--DECIMAL
		RD_DATA_COUNT_WIDTH=>1,--DECIMAL

		CDC_SYNC_STAGES => 2,--DECIMAL
		ECC_MODE => "no_ecc",--String
		FIFO_MEMORY_TYPE=>"auto",--String
		FIFO_READ_LATENCY=>1,--DECIMAL
		PROG_EMPTY_THRESH=>28,--DECIMAL
		PROG_FULL_THRESH=>100,--DECIMAL
		--String
		RELATED_CLOCKS=>0,--DECIMAL
		USE_ADV_FEATURES=>"0707",--String
		WAKEUP_TIME=>0
	)
	port map(

		rst=>FIFO_reset,
		wr_clk=>Sensor_PixClk,
		wr_en=>FIFO_Wr_En,
		din=>FIFO_Data_In,

		rd_clk=>Clk,
		rd_en=>FIFO_Rd_En,
		dout=>FIFO_Data_Out,
		empty=>FIFO_empty,

		almost_empty=>open,
		almost_full=>open,
		data_valid=>open,
		dbiterr=>open,
		full=>open,
		overflow=>open,
		prog_empty=>open,
		prog_full=>open,
		rd_data_count=>open,
		rd_rst_busy=>open,
		sbiterr=>open,
		underflow=>open,
		wr_ack=>open,
		wr_data_count=>open,
		wr_rst_busy=>open,
		injectdbiterr=>'0',
		injectsbiterr=>'0',
		sleep=>'0'
	);
--Endofxpm_fifo_async_instinstantiation




-- PowerDown mode is not supported yet:
Sensor_PowerDown <= '0';

-- Reset to OV7670 sensor:
Sensor_Reset_n <= not(control(3));


softreset <= control(0);
run       <= control(1);
run_once  <= control(2);

control_reset(0) <= softreset_reset;
control_reset(1) <= run_reset;
control_reset(2) <= run_once_reset;
control_reset(15 downto 3) <= (others => '0');

state <= (
      0 => state_reg_frame_done,
      others => '0'
    );



--- **** Synchronous to Sensor_PixClk ****
-- FIFO In ports:
FIFO_reset <= Reset_Sensor_PixClk or Sensor_Frame_Valid;
FIFO_Wr_En <= s_Sensor_Line_Valid_delayed and not(s_drop);

process(s_Sensor_Data)
begin
  FIFO_Data_In(9 downto 0) <= (others => '0');
  FIFO_Data_In(SENSOR_DATA_WIDTH-1 downto 0) <= s_Sensor_Data;
end process;

FIFO_Data_In(10) <= HSYNC_gen;
FIFO_Data_In(11) <= VSYNC_gen;
FIFO_Data_In(12) <= '0';
--- ****



--- **** Synchronous to Clk ****
-- FIFO Out ports
FIFO_Rd_En <= not(FIFO_empty);

s_vsync_out <= FIFO_Data_Out(11) and s_stobe_out;
VSYNC_OUT <= s_vsync_out;

s_hsync_out <= FIFO_Data_Out(10) and s_stobe_out;
HSYNC_OUT <= s_hsync_out;

DATA_OUT <= FIFO_Data_Out(SENSOR_DATA_WIDTH-1 downto SENSOR_DATA_WIDTH-DOUT_WIDTH);

-- Generating STROBE_OUT from 'not(FIFO_empty)' only works this way if this FIFO is a First-Word-Fall-Through FIFO.
-- This also drops all data (by not enabling 's_stobe_out') until a new (valid) frame comes by (using 'sensor_enabled' and respective signals):
s_stobe_out <= ( not(FIFO_empty) and ( sensor_set_enabled or (sensor_enabled and not(sensor_set_disabled))) );
STROBE_OUT <= s_stobe_out;

s_vcomplete_out <= '1' when ( (state_reg_frame_done = '1') and (state_reg_frame_done_last = '0') ) else '0';
VCOMPLETE_OUT <= s_vcomplete_out;

SYNC_ERROR_OUT <= '0';
DATA_ERROR_OUT <= '0';
-- STALL_IN is ignored yet, but may be used to generate SYNC_ERROR_OUT and/or PIXEL_ERROR_OUT



DATA_COUNTER_PROCESS: process(Clk)
  variable data_counter : unsigned(DATA_COUNTER_BITS-1 downto 0);
begin
  if (Clk'event and Clk = '1') then

    run_last <= run;

    if ( (Reset = '1') or 
         (softreset = '1') or 
         ( (s_stobe_out = '1') and ( s_vsync_out = '1') ) or -- reset counter for subsequent frames (free run mode)
         ( ( run_last = '0' ) and ( run = '1' ) ) ) then -- reset counter for first frame, especially important for single shot mode (else the old counter value would persist until a new frame arrives)
      data_counter := to_unsigned(1, data_counter'length);
      state_reg_frame_done <= '0';
      state_reg_frame_done_last <= '0';

    elsif ( s_stobe_out = '1' ) then
      data_counter := data_counter + 1;
    end if;

    if ( data_counter = to_unsigned(RES_X*RES_Y, data_counter'length) ) then
      state_reg_frame_done <= '1';
    end if;

    state_reg_frame_done_last <= state_reg_frame_done;
  end if;
end process;



-- Recognize a frame start at FIFO out:
-- 1) When run is set, the next frame / module output is to be enabled:
sensor_set_enabled  <= FIFO_Data_Out(11) and not(FIFO_empty) and run;       -- VSYNC (only valid if FIFO not empty) and RUN
-- 2) When run is not set, the next frame / module output is to be disabled:
sensor_set_disabled <= FIFO_Data_Out(11) and not(FIFO_empty) and not(run);  -- VSYNC (only valid if FIFO not empty) and not(RUN)


-- this process keeps signal 'sensor_enabled' up for a frame (to avoid frame-fragments in the pipeline)
process(Clk)
begin
  if (Clk'event and Clk = '1') then
    if ( (Reset = '1') or (softreset = '1') ) then
      Ready           <= '0';
      softreset_reset <= '1';
      run_reset       <= '1';
      run_once_reset  <= '1';
      sensor_enabled  <= '0';
    else
      Ready <= Ready_Sensor;
      softreset_reset <= '0';
      run_reset      <= '0';
      run_once_reset <= '0';
      
      -- at frame start (VSYNC high and RUN at FIFO out), this frame is to be enabled by setting the persistent 'sensor_enabled' signal:
      if ( sensor_set_enabled = '1' ) then
 
        sensor_enabled <= '1';

        -- if additionally the 'RunOnce' flag is set, reset both 'Run' and 'RunOnce' flags:
        if ( run_once = '1' ) then
          run_reset      <= '1';
          run_once_reset <= '1';
        end if;

      -- at frame start (VSYNC high but NOT RUN at FIFO out), this frame is to be disabled by unsetting the persistent 'sensor_enabled' signal:
      elsif ( sensor_set_disabled = '1' ) then   
        sensor_enabled <= '0';
      end if;

    end if;
  end if;
end process;


-- ==============================================================================
-- Synchronize and store incoming data
-- ==============================================================================
SYNCHRONIZE_INCOMING_DATA : process(Sensor_PixClk)
begin
  if(Sensor_PixClk'event and Sensor_PixClk = '1') then
    s_Sensor_Frame_Valid <= Sensor_Frame_Valid; -- used for VSync generation.
    -- s_Sensor_Frame_Valid_delayed <= s_Sensor_Frame_Valid; -- not used.
    s_Sensor_Line_Valid <= Sensor_Line_Valid; -- used for HSync generation.
    s_Sensor_Line_Valid_delayed <= s_Sensor_Line_Valid; -- delayed line valid value is used for FIFO write enable.

    -- create 1 cycle delay so that incoming pixel is synchronous with VSYNC_gen and HSYNC_gen (as sync generation in 'GENERATE_SYNCS' takes 1 clock cycle)
    s_Sensor_Data_delay <= Sensor_Data;
    s_Sensor_Data <= s_Sensor_Data_delay;
  end if;
end process;


-- ==============================================================================
-- Generate VSYNC and HSYNC signals (1 clock cycle delay to data, see above)
-- ==============================================================================
GENERATE_SYNCS : process(Sensor_PixClk)
variable v_FRAME_DETECT : std_logic;
begin
  if ( Sensor_PixClk'event and Sensor_PixClk = '1' ) then
    if ( Reset_Sensor_PixClk = '1' ) then
      Ready_Sensor_PixClk <= '0';

      FRAME_DETECT <= '0';
      FRAME_DETECT_last <= '0';

      s_Sensor_Frame_Valid_last <= '1';
      s_Sensor_Line_Valid_last <= '1';

      VSYNC_gen <= '0';
      HSYNC_gen <= '0';

    else
      VSYNC_gen <= '0';
      HSYNC_gen <= '0';

      -- drop every second arriving value (pixel format is Y-Cr-Y-Cb-... and we just want Y values, Cr and Cb have to be dropped)
      s_drop <= not(s_drop);

      -- Save recent Frame/Line_Valid for next cycle to detect a change (rising/falling edge):
      s_Sensor_Frame_Valid_last <= s_Sensor_Frame_Valid;
      s_Sensor_Line_Valid_last <= s_Sensor_Line_Valid;


      -- Recognize the frame start (which may happen not at the same clock cycle of line change):
      if ((s_Sensor_Frame_Valid_last = '0') and (s_Sensor_Frame_Valid = '1')) then
        v_FRAME_DETECT := not(FRAME_DETECT);
        -- Store frame detection information:
        FRAME_DETECT <= v_FRAME_DETECT;
      end if;

      -- Detect a line change (-> HSYNC generated, optionally genrate VSYNC if also frame valid changes or changed beforehand)
      if (s_Sensor_Line_Valid_last = '0' and s_Sensor_Line_Valid = '1') then

        HSYNC_gen <= '1';
        s_drop <= '0'; -- never drop first pixel as it is accompanied by sync information. If pixels arrive in unpleasant order, change behaviour in the sensor config (I2C sensor config).

        -- Generate VSYNC if there's a frame change signalled in the recent cycle or beforehand:
        if (((v_FRAME_DETECT xor FRAME_DETECT_last) or (FRAME_DETECT xor FRAME_DETECT_last)) = '1') then
          VSYNC_gen <= '1';
          Ready_Sensor_PixClk <= '1'; -- we are ready when the first frame comes in
        end if;

        -- Handle frame change evaluation (VS happened before HS):
        FRAME_DETECT_last <= v_FRAME_DETECT;

      end if;

    end if;
  end if;
end process;


process (Clk)
begin
  if (Clk'event and Clk = '1') then
    Ready_Sensor_unsynced <= Ready_Sensor_PixClk;
    Ready_Sensor <= Ready_Sensor_unsynced;
  end if;
end process;


process(Sensor_PixClk)
begin
  if(Sensor_PixClk'event and Sensor_PixClk = '1') then
    Reset_unsynced <= Reset;
    Reset_Sensor_PixClk <= Reset_unsynced;
  end if;
end process;

end RTL;
