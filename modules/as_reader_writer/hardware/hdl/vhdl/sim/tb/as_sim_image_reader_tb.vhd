----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  Copyright (C) Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_tb_image_reader_tb
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Authors:        Markus Bihler, B.Eng.
--
-- Modified:       
--
-- Description:    Testbench for the as_tb_image_reader module.
-- 
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
--! @file  as_tb_image_reader_tb.vhd
--! @brief Testbench for the as_tb_image_reader module.
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

library fileOps;

entity as_sim_image_reader_tb is
end as_sim_image_reader_tb;

architecture Behavioral of as_sim_image_reader_tb is
  component as_sim_image_reader is
    generic(
      DOUT_WIDTH : integer := 8;
      GEN_FILENAME : string := "./images/lena_greyScale.csv";
      GEN_IMAGEWIDTH : natural := 640
    );
    port(
      Clk         : in std_logic;
      Reset       : in std_logic;
      
      ENABLE_IN   : in  std_logic;
      
      -- Pixel Stream output PORTS
      VSYNC_OUT   : out std_logic;
      HSYNC_OUT   : out std_logic;
      STROBE_OUT  : out std_logic;
      DATA_OUT    : out  std_logic_vector(DOUT_WIDTH-1 downto 0)
    );
  end component;
  
  constant c_DOUT_WIDTH : natural := 8;
  
  signal Clk, Reset : std_logic;
  
  signal ENABLE_IN    : std_logic;
  signal VSYNC_OUT    : std_logic;
  signal HSYNC_OUT    : std_logic;
  signal STROBE_OUT   : std_logic;
  signal DATA_OUT     : std_logic_vector(c_DOUT_WIDTH-1 downto 0);

begin
  process
  begin
    Clk <= '1';
    wait for 5 ns;
    Clk <= '0';
    wait for 5 ns;
  end process;
  
  tb:process 
  begin
    Reset <= '1';
    wait for 100 ns;
    wait until rising_edge(Clk);
    Reset <= '0';
    ENABLE_IN <= '1';
    
    for i in 0 to 100 loop
      wait until rising_edge(Clk);
    end loop;
    
    for i in 0 to 100 loop
      wait until rising_edge(Clk);
      ENABLE_IN <= '0';
      wait until rising_edge(Clk);
      ENABLE_IN <= '1';
    end loop;
    
    for i in 0 to 100 loop
      wait until rising_edge(Clk);
      ENABLE_IN <= '0';
      wait until rising_edge(Clk);
      wait until rising_edge(Clk);
      ENABLE_IN <= '1';
    end loop;
    
    wait until VSYNC_OUT ='1';
    wait until rising_edge(Clk);
    wait until VSYNC_OUT ='1';
    
    assert false
      report "END OF SIMULATION"
      severity failure;
    wait;
  end process;
  
  READER: as_sim_image_reader
    generic map(
      DOUT_WIDTH => 8,
      GEN_FILENAME => "./images/lena_greyScale.csv",
      GEN_IMAGEWIDTH => 640
    )
    port map(
      Clk => Clk,
      Reset => Reset,
      
      ENABLE_IN => ENABLE_IN,
      
      VSYNC_OUT => VSYNC_OUT,
      HSYNC_OUT => HSYNC_OUT,
      STROBE_OUT => STROBE_OUT,
      DATA_OUT => DATA_OUT
    );
    
end Behavioral;

