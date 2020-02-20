----------------------------------------------------------------------
-- This file is part of the ASTERICS Framework.
-- Copyright (C) Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------
-- File:     as_disperse_tb.vhd
--
-- Company:  Efficient Embedded Systems Group
--           University of Applied Sciences, Augsburg, Germany
--           http://ees.hs-augsburg.de
--
-- Author:   Julian Sarcher, Alexander Zoellner
-- Date:     2018-01-17
-- Modified: 
--
-- Description:
-- Testbench for the as_disperse module.
--
-- Comment:
-- This file is part of the ChASA project, which has been supported by 
-- the German Federal Ministry for Economic Affairs and Energy, grant 
-- number ZF4102001KM5.
----------------------------------------------------------------------
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
----------------------------------------------------------------------

LIBRARY ieee;
USE ieee.std_logic_1164.ALL;
USE ieee.numeric_std.ALL;

ENTITY as_disperse_tb IS
END as_disperse_tb;
 
ARCHITECTURE behavior OF as_disperse_tb IS 
 
 
  constant X_RES : integer := 32;
  constant Y_RES : integer := 24;
  constant IMAGE_SIZE : integer := X_RES*Y_RES;
 
 
    -- Component Declaration for the Unit Under Test (UUT)
  component as_disperse
  generic (
    DIN_WIDTH  : integer := 32;
    DOUT_WIDTH : integer := 8 -- collects DOUT_WIDTH/DIN_WIDTH many data words to one data word
  );
  port (
    Clk         : in  std_logic;
    Reset       : in  std_logic;

    -- IN ports
    VCOMPLETE_IN : in std_logic;
    VSYNC_IN     : in  std_logic;
    HSYNC_IN     : in  std_logic;
    STROBE_IN    : in  std_logic;
    XRES_IN      : in  std_logic_vector(11 downto 0);
    YRES_IN      : in  std_logic_vector(11 downto 0);
    DATA_IN      : in  std_logic_vector(DIN_WIDTH-1 downto 0);
    
    DATA_ERROR_IN   : in  std_logic;
    STALL_OUT       : out std_logic;

    -- OUT ports
    VCOMPLETE_OUT   : out std_logic;
    VSYNC_OUT       : out std_logic;
    HSYNC_OUT       : out std_logic;
    STROBE_OUT      : out std_logic;
    DATA_OUT        : out std_logic_vector(DOUT_WIDTH-1 downto 0);
    XRES_OUT        : out std_logic_vector(11 downto 0);
    YRES_OUT        : out std_logic_vector(11 downto 0);

    SYNC_ERROR_OUT  : out std_logic;
    DATA_ERROR_OUT  : out std_logic;
    STALL_IN        : in  std_logic
  );
  end component;
  
  
  component AS_SIM_IMAGE_WRITER is
  generic (
    SIM_FILE_NAME : string := "./tb/images/lenaScaled.csv";
    REGISTER_BIT_WIDTH : integer := 32;
    DIN_WIDTH : integer := 64;
    MEMORY_DATA_WIDTH : integer := 64;
    MEM_ADDRESS_BIT_WIDTH : integer := 32;
    BURST_LENGTH_BIT_WIDTH : integer := 12;
    MAX_PLATFORM_BURST_LENGTH  : integer := 256;
    FIFO_NUMBER_OF_BURSTS      : natural := 4;            -- max. number of stored bursts in fifo
    SUPPORT_MULTIPLE_SECTIONS : boolean := false               -- has to be false if used for as_memio
  );
  port (
    Clk         : in  std_logic;
    Reset       : in  std_logic;
    Ready       : out std_logic;

    FORCE_DONE  : in std_logic; 
    
    -- IN ports
    STROBE_IN   : in  std_logic;
    DATA_IN     : in  std_logic_vector(DIN_WIDTH-1 downto 0);
    
    STALL_OUT      : out std_logic;

    -- PLB part
    --! Register for sending commands to the as_memreader.
    control       : in  std_logic_vector(15 downto 0);
    --! Request reset of target control bits set by different hw module or software.
    control_reset : out std_logic_vector(15 downto 0);
    --! State of the as_memwriter module (busy, done, etc.)
    state         : out std_logic_vector(15 downto 0);
    
    --! Configuration ports for read access (see corresponding hardware driver for 
    --! more information).
    reg_section_addr        : in std_logic_vector(REGISTER_BIT_WIDTH-1 downto 0);
    reg_section_offset      : in std_logic_vector(REGISTER_BIT_WIDTH-1 downto 0);
    reg_section_size        : in std_logic_vector(REGISTER_BIT_WIDTH-1 downto 0);
    reg_section_count       : in std_logic_vector(REGISTER_BIT_WIDTH-1 downto 0);
    reg_max_burst_length    : in std_logic_vector(REGISTER_BIT_WIDTH-1 downto 0);
    --! Current memory address the as_memreader module is performing an operation on.
    reg_current_hw_addr     : out std_logic_vector(REGISTER_BIT_WIDTH-1 downto 0)
  );
  end component;
   
   constant din_width  : natural := 64;
   constant dout_width : natural := 8;
  
   signal clk : std_logic := '0';
   signal reset : std_logic := '1';
   
   --Inputs
   signal vsync_in  : std_logic := '0';
   signal hsync_in  : std_logic := '0';
   signal strobe_in : std_logic := '0';
   signal xres_in   : std_logic_vector(11 downto 0) := (others => '0');
   signal yres_in   : std_logic_vector(11 downto 0) := (others => '0');
   signal data_in   : std_logic_vector(din_width-1 downto 0) := (others => '0');
   signal sync_error_in : std_logic := '0';
   signal pixel_error_in : std_logic := '0';
   signal stall_out : std_logic := '0';

 	--Outputs
   signal vsync_out  : std_logic := '0';
   signal hsync_out  : std_logic := '0';
   signal strobe_out : std_logic := '0';
   signal xres_out   : std_logic_vector(11 downto 0) := (others => '0');
   signal yres_out   : std_logic_vector(11 downto 0) := (others => '0');
   signal data_out   : std_logic_vector(dout_width-1 downto 0) := (others => '0');
   signal sync_error_out : std_logic := '0';
   signal pixel_error_out : std_logic := '0';
   signal stall_in : std_logic := '0';

   -- Clock period definitions
   constant Clk_period : time := 10 ns;
 
  signal as_memwriter_0_control                      : std_logic_vector(15 downto 0);
  signal as_memwriter_0_control_reset                : std_logic_vector(15 downto 0);
  signal as_memwriter_0_state                        : std_logic_vector(15 downto 0);
 
 
  constant DATA_TO_GENERATE : integer := 8192;
 
BEGIN
 
	-- Instantiate the Unit Under Test (UUT)
   as_disperse_0 : as_disperse 
   GENERIC MAP (
          DIN_WIDTH => din_width,
          DOUT_WIDTH => dout_width
          )
   PORT MAP (
          Clk => Clk,
          Reset => Reset,
          -- input
          VCOMPLETE_IN => '0',
          VSYNC_IN => vsync_in,
          HSYNC_IN => hsync_in,
          STROBE_IN => strobe_in,
          DATA_IN => data_in,
          XRES_IN => xres_in,
          YRES_IN => yres_in,
          DATA_ERROR_IN => pixel_error_in,
          STALL_OUT => stall_out,
          -- output
          VCOMPLETE_OUT => open,
          VSYNC_OUT => VSYNC_OUT,
          HSYNC_OUT => HSYNC_OUT,
          STROBE_OUT => STROBE_OUT,
          DATA_OUT => DATA_OUT,
          XRES_OUT => XRES_OUT,
          YRES_OUT => YRES_OUT,
          SYNC_ERROR_OUT => SYNC_ERROR_OUT,
          DATA_ERROR_OUT => PIXEL_ERROR_OUT,
          STALL_IN => STALL_IN
    );
        
    WRITER_0 : AS_SIM_IMAGE_WRITER
    generic map(
      SIM_FILE_NAME => "./images/disperse_out.raw",
      REGISTER_BIT_WIDTH  => 32,
      DIN_WIDTH   => dout_width,
      MEMORY_DATA_WIDTH  => 8,
      MEM_ADDRESS_BIT_WIDTH  => 32,
      BURST_LENGTH_BIT_WIDTH  => 32,
      MAX_PLATFORM_BURST_LENGTH  => 256,
      SUPPORT_MULTIPLE_SECTIONS => false
    )
    port map (
      Clk   => Clk,
      Reset => Reset,
      Ready => open,
      
      FORCE_DONE => '0',
      
      -- IN ports
      STROBE_IN       => STROBE_OUT,
      DATA_IN         => DATA_OUT,
      
      STALL_OUT       => open,

      -- control / state
      control       => as_memwriter_0_control,
      control_reset => as_memwriter_0_control_reset,
      state         => as_memwriter_0_state,
      reg_section_addr        => std_logic_vector(to_unsigned(0, 32)),
      reg_section_offset      => std_logic_vector(to_unsigned(0, 32)),
      reg_section_size        => std_logic_vector(to_unsigned(DATA_TO_GENERATE+1, 32)),
      reg_section_count       => std_logic_vector(to_unsigned(1, 32)),
      reg_max_burst_length    => std_logic_vector(to_unsigned(256, 32)),
      reg_current_hw_addr     => open
    );
    
 
 
   -- Stimulus process
   stim_proc: process
            
      procedure run_cycles (cycles: in integer) is
      begin
        for cycle in 1 to cycles loop
          Clk <= '0';
          wait for Clk_period/2;
          Clk <= '1';
          wait for Clk_period/2;
        end loop;
      end run_cycles;
      

      variable i : integer;
   begin
   
      -- Global Hardware Reset
      reset           <= '1';
      -- Reset memwriter_0
      as_memwriter_0_control(0) <= '1'; --Reset
      as_memwriter_0_control(15 downto 1) <= (others=>'0');
      
      run_cycles(5);
      
      as_memwriter_0_control(0) <= '0';
      reset <= '0';

      run_cycles(5);


      report "Start Memwriter 0";
      -- Start MEMWRITER_0
      as_memwriter_0_control(1) <= '1'; --GO
      run_cycles(2);

      as_memwriter_0_control(1) <= '0';
      run_cycles(2);
      
      
      strobe_in <= '0';
         
      run_cycles(3);
     

      vsync_in <= '0';
      hsync_in <= '0';
      strobe_in <= '0';
      data_in <= (others => '0');
      sync_error_in <= '0';
      pixel_error_in <= '0';
      xres_in <= "101010101010"; 
      yres_in <= "101010101010";
      
      i := 0;
      while i < DATA_TO_GENERATE+100 loop

        -- Apply hsync/vsync
        if i mod Y_RES = 0 then
            --vsync_in <= '1';
        end if;
        if i mod X_RES = 0 then
            --hsync_in <= '1';
        end if;

        if i mod 5 = 0 then
            run_cycles(i mod 3);
        end if;
        
        -- Forward some data
        while stall_out = '1' loop 
            run_cycles(1); 
        end loop;
        
        data_in <= std_logic_vector(to_unsigned(i,data_in'length));
        strobe_in <= '1';
        run_cycles(1);
        strobe_in <= '0';
        i := i + 1;

        if i mod 13 = 0 then
            data_in <= std_logic_vector(to_unsigned(i,data_in'length));
            strobe_in <= '1';
            run_cycles(1);
            strobe_in <= '0';
            i := i + 1;
        end if;

      end loop;

      run_cycles(80);
      wait;
   end process;

   p_stall : process(clk)
       variable i : integer := 0;
   begin
        if rising_edge(clk) then
            if i mod 3 = 0 or i mod 5 = 0 or i mod 7 = 0 or i mod 13 = 0 then
            --if i mod 31 = 0 then
                stall_in <= '1';
            else
                stall_in <= '0';
            end if;
            i := i + 1; 
        end if;     
   end process;

END;

