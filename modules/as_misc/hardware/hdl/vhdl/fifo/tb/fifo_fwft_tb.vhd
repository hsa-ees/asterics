----------------------------------------------------------------------
-- This file is part of the ASTERICS Framework.
-- Copyright (C) Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------
-- File:     fifo_fwft_tb.vhd
--
-- Company:  Efficient Embedded Systems Group
--           University of Applied Sciences, Augsburg, Germany
--           http://ees.hs-augsburg.de
--
-- Author:   Michael Schaeferling <michael.schaeferling@hs-augsburg.de>
-- Date:     2014-10-10
-- Modified: 
--
-- Description: VHDL Test Bench Created by ISE for module: fifo_fwft
--
-- Comment:  This testbench has been automatically generated using types std_logic and
--           std_logic_vector for the ports of the unit under test.  Xilinx recommends
--           that these types always be used for the top-level I/O of a design in order
--           to guarantee that the testbench will bind correctly to the post-implementation 
--           simulation model.
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
use IEEE.NUMERIC_STD.ALL;


use work.helpers.all;
 

ENTITY fifo_fwft_tb IS
END fifo_fwft_tb;
 
ARCHITECTURE behavior OF fifo_fwft_tb IS 
 
  -- Component Declaration for the Unit Under Test (UUT) 
  component fifo_fwft is
  generic (
      DATA_WIDTH : integer := 8;
      BUFF_DEPTH : integer := 256;
      PROG_EMPTY_ENABLE : boolean := true
    );
    port (
      clk         : in  std_logic;
      reset       : in  std_logic;

      din         : in  std_logic_vector(DATA_WIDTH-1 downto 0);
      wr_en       : in  std_logic;
      rd_en       : in  std_logic;
      dout        : out std_logic_vector(DATA_WIDTH-1 downto 0);

      level       : out std_logic_vector(log2_ceil(BUFF_DEPTH) downto 0);
      full        : out std_logic;
      empty       : out std_logic;
      
      prog_full_thresh  : in std_logic_vector(log2_ceil(BUFF_DEPTH)-1 downto 0);
      prog_full         : out std_logic;
      
      prog_empty_thresh : in std_logic_vector(log2_ceil(BUFF_DEPTH)-1 downto 0);
      prog_empty        : out std_logic
    );
  end component;


   constant DATA_WIDTH : integer := 8;
   constant BUFF_DEPTH : integer := 16;
   constant PROG_EMPTY_ENABLE : boolean := true;
  

   --Inputs
   signal clk : std_logic := '0';
   signal reset : std_logic := '0';
   signal din : std_logic_vector(DATA_WIDTH-1 downto 0) := (others => 'X');
   signal wr_en : std_logic := '0';
   signal rd_en : std_logic := '0';
   signal prog_empty_thresh, prog_full_thresh : std_logic_vector(log2_ceil(BUFF_DEPTH)-1 downto 0) := (others => '0');

 	--Outputs
   signal dout : std_logic_vector(DATA_WIDTH-1 downto 0);
   signal full : std_logic;
   signal empty : std_logic;
   --signal empty_next : std_logic;
   signal prog_empty : std_logic;
   signal prog_full : std_logic;

   -- Clock period definitions
   constant clk_period : time := 10 ns;
 
BEGIN
 
	-- Instantiate the Unit Under Test (UUT)
   uut: fifo_fwft
   GENERIC MAP (
          DATA_WIDTH => DATA_WIDTH,
          BUFF_DEPTH => BUFF_DEPTH,
          PROG_EMPTY_ENABLE => PROG_EMPTY_ENABLE
        )
   PORT MAP (
          clk => clk,
          reset => reset,
          din => din,
          wr_en => wr_en,
          rd_en => rd_en,
          dout => dout,
          full => full,
          empty => empty,
          prog_full_thresh => prog_full_thresh,
          prog_full => prog_full,
          prog_empty_thresh => prog_empty_thresh,
          prog_empty => prog_empty
        );

--   -- Clock process definitions
--   clk_process :process
--   begin
--		clk <= '0';
--		wait for clk_period/2;
--		clk <= '1';
--		wait for clk_period/2;
--   end process;


   -- Stimulus process
   stim_proc: process

      procedure run_cycles (cycles: in integer) is
      begin
        for cycle in 1 to cycles loop
          clk <= '1';
          wait for clk_period/2;
          clk <= '0';
          wait for clk_period/2;
        end loop;
      end run_cycles;
     

      procedure fifo_wr(data: in integer) is
      begin
        din <= std_logic_vector(to_unsigned(data, din'length));
        wr_en <= '1';
        
        run_cycles(1);
        
        wr_en <= '0';
        din <= (others => 'X');
        
      end fifo_wr;

      procedure fifo_rd is
      begin
        rd_en <= '1';
        run_cycles(1);
        rd_en <= '0';
      end fifo_rd;
      
      procedure fifo_rd_wr(data: in integer) is
      begin
        rd_en <= '1';

        din <= std_logic_vector(to_unsigned(data, din'length));
        wr_en <= '1';
        
        run_cycles(1);
        
        rd_en <= '0';
        
        wr_en <= '0';
        din <= (others => 'X');
        
      end fifo_rd_wr;

   begin
   
      reset <= '1';
      run_cycles(3);
      
      reset <= '0';
      run_cycles(3);
      
      prog_empty_thresh <= std_logic_vector(to_unsigned(1, prog_empty_thresh'length));
      prog_full_thresh <= std_logic_vector(to_unsigned(BUFF_DEPTH-1, prog_empty_thresh'length));
      
      -- check overflow
      for i in 1 to BUFF_DEPTH+2 loop
        fifo_wr(i);
      end loop;
      
      
      -- check read and write when full
      fifo_rd_wr(255);
      -- check read when full
      for i in 0 to BUFF_DEPTH-1 loop
        fifo_rd;
      end loop;
      -- check read when empty
      fifo_rd;
      -- check read and write when empty
      fifo_rd_wr(127);
      fifo_rd_wr(255);
      
      run_cycles(5);
      wait;
   end process;

END;
