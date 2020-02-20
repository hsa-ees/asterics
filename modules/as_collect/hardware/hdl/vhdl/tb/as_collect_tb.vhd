----------------------------------------------------------------------
-- This file is part of the ASTERICS Framework.
-- Copyright (C) Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------
-- File:     as_collect_tb.vhd
--
-- Company:  Efficient Embedded Systems Group
--           University of Applied Sciences, Augsburg, Germany
--           http://ees.hs-augsburg.de
--
-- Author:   Julian Sarcher
-- Date:     2014-10-21
-- Modified: 
--
-- Description:
-- VHDL Test Bench Created by ISE for module: as_collect
--
-- Notes: 
-- This testbench has been automatically generated using types std_logic and
-- std_logic_vector for the ports of the unit under test.  Xilinx recommends
-- that these types always be used for the top-level I/O of a design in order
-- to guarantee that the testbench will bind correctly to the post-implementation 
-- simulation model.
--
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
 
ENTITY as_collect_tb IS
END as_collect_tb;
 
ARCHITECTURE behavior OF as_collect_tb IS 
 
    -- Component Declaration for the Unit Under Test (UUT)
  component as_collect
  generic (
    DIN_WIDTH  : integer := 8;
    DOUT_WIDTH : integer := 64 -- collects DOUT_WIDTH/DIN_WIDTH many data words to one data word
  );
  port (
    Clk         : in  std_logic;
    Reset       : in  std_logic;

    -- IN ports
    VSYNC_IN     : in  std_logic;
    HSYNC_IN     : in  std_logic;
    STROBE_IN    : in  std_logic;
    XRES_IN      : in  std_logic_vector(11 downto 0);
    YRES_IN      : in  std_logic_vector(11 downto 0);
    DATA_IN      : in  std_logic_vector(DIN_WIDTH-1 downto 0);
    VCOMPLETE_IN : in  std_logic;
    
    SYNC_ERROR_IN   : in  std_logic;
    PIXEL_ERROR_IN  : in  std_logic;
    STALL_OUT       : out std_logic;

    -- OUT ports
    VSYNC_OUT     : out std_logic;
    HSYNC_OUT     : out std_logic;
    STROBE_OUT    : out std_logic;
    DATA_OUT      : out std_logic_vector(DOUT_WIDTH-1 downto 0);
    VCOMPLETE_OUT : out std_logic;
    XRES_OUT      : out std_logic_vector(11 downto 0);
    YRES_OUT      : out std_logic_vector(11 downto 0);

    SYNC_ERROR_OUT  : out std_logic;
    PIXEL_ERROR_OUT : out std_logic;
    STALL_IN        : in  std_logic
  );
  end component;
  
  signal clk : std_logic := '0';
  signal reset : std_logic := '1';
  
   constant din_width  : natural := 8;
   constant dout_width : natural := 64;
   
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
   signal vcomplete_in : std_logic;

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
   signal vcomplete_out : std_logic;
   
   
   -- Clock period definitions
   constant Clk_period : time := 10 ns;
 
BEGIN
 
	-- Instantiate the Unit Under Test (UUT)
   uut1: as_collect 
   GENERIC MAP (
          DIN_WIDTH => din_width,
          DOUT_WIDTH => dout_width
          )
   PORT MAP (
          Clk => Clk,
          Reset => Reset,
          -- input
          VSYNC_IN => vsync_in,
          HSYNC_IN => hsync_in,
          STROBE_IN => strobe_in,
          DATA_IN => data_in,
          VCOMPLETE_IN => vcomplete_in,
          XRES_IN => xres_in,
          YRES_IN => yres_in,
          SYNC_ERROR_IN => sync_error_in,
          PIXEL_ERROR_IN => pixel_error_in,
          STALL_OUT => stall_out,
          -- output
          VSYNC_OUT => VSYNC_OUT,
          HSYNC_OUT => HSYNC_OUT,
          STROBE_OUT => STROBE_OUT,
          DATA_OUT => DATA_OUT,
          VCOMPLETE_OUT => vcomplete_out,
          XRES_OUT => XRES_OUT,
          YRES_OUT => YRES_OUT,
          SYNC_ERROR_OUT => SYNC_ERROR_OUT,
          PIXEL_ERROR_OUT => PIXEL_ERROR_OUT,
          STALL_IN => STALL_IN
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


   begin
        
      -- reset
      reset <= '1';
      stall_in <= '0';
      run_cycles(3);
      
      reset <= '0';
      vcomplete_in <= '0';
      run_cycles(3);
      --
      

      vsync_in <= '1'; hsync_in <= '0'; strobe_in <= '0'; data_in <= "00111101"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);  -- no strobe
      -- Sending two (x,y) (8,2) pixel sized images
      vsync_in <= '1'; hsync_in <= '1'; strobe_in <= '1'; data_in <= "00000000"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '0'; data_in <= "10101010"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);  -- no strobe
      strobe_in <= '0'; stall_in <= '1'; run_cycles(3); stall_in <= '0';
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '0'; data_in <= "10101010"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);  -- no strobe
      strobe_in <= '0'; stall_in <= '1'; run_cycles(3); stall_in <= '0';
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00000001"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);
      strobe_in <= '0'; stall_in <= '1'; run_cycles(3); stall_in <= '0';
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00000010"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);
      strobe_in <= '0'; stall_in <= '1'; run_cycles(3); stall_in <= '0';
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00000011"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);

      strobe_in <= '0'; stall_in <= '1'; run_cycles(3); stall_in <= '0';
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '0'; data_in <= "10101010"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);  -- no strobe
      strobe_in <= '0'; stall_in <= '1'; run_cycles(3); stall_in <= '0';
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '0'; data_in <= "10101010"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);  -- no strobe
      strobe_in <= '0'; stall_in <= '1'; run_cycles(3); stall_in <= '0';
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00000100"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);
      strobe_in <= '0'; stall_in <= '1'; run_cycles(3); stall_in <= '0';
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '0'; data_in <= "10101010"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);  -- no strobe
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00000101"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00000110"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);
      stall_in <= '1';
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00000111"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);
      strobe_in <= '0';
      run_cycles(1);
      stall_in <= '0';
      run_cycles(1);
      vsync_in <= '0'; hsync_in <= '1'; strobe_in <= '1'; data_in <= "00001000"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '0'; data_in <= "10101010"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);  -- no strobe
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '0'; data_in <= "10101010"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);  -- no strobe
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '0'; data_in <= "10101010"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);  -- no strobe
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00001001"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '0'; data_in <= "10101010"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);  -- no strobe
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00001010"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00001011"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);

      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00001100"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '0'; data_in <= "10101010"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);  -- no strobe
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '0'; data_in <= "10101010"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);  -- no strobe
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00001101"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '0'; data_in <= "10101010"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);  -- no strobe
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '0'; data_in <= "10101010"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);  -- no strobe
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00001110"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00001111"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);

      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '0'; data_in <= "10101010"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);  -- no strobe
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '0'; data_in <= "10101010"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);  -- no strobe
      vsync_in <= '1'; hsync_in <= '1'; strobe_in <= '1'; data_in <= "00010000"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00010001"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '0'; data_in <= "10101010"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);  -- no strobe
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '0'; data_in <= "10101010"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);  -- no strobe
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00010010"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00010011"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);

      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '0'; data_in <= "10101010"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);  -- no strobe
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '0'; data_in <= "10101010"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);  -- no strobe
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '0'; data_in <= "10101010"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);  -- no strobe
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00010100"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00010101"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00010110"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '0'; data_in <= "10101010"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);  -- no strobe
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '0'; data_in <= "10101010"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);  -- no strobe
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00010111"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);

      vsync_in <= '0'; hsync_in <= '1'; strobe_in <= '1'; data_in <= "00011000"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00011001"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00011010"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00011011"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00011100"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00011101"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00011110"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00011111"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);
      
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00100000"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);      
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00100001"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);      
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00100010"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);      
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00100011"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);      
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00100100"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);      
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00100101"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);      
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00100110"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);      
      vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00100111"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);      

      --vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00101000"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);      
      --vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00101001"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);      
      --vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "00101010"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);      
      --vsync_in <= '0'; hsync_in <= '0'; strobe_in <= '1'; data_in <= "11111111"; sync_error_in <= '0'; pixel_error_in <= '0'; xres_in <= "101010101010"; yres_in <= "101010101010"; run_cycles(1);      
      
      strobe_in <= '0'; vcomplete_in <= '1'; run_cycles(1); vcomplete_in <= '0';
      
      run_cycles(80);
      wait;
   end process;

END;

