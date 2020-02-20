----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  Copyright (C) Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_sim_image_writer_tb
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Authors:        Markus Bihler, B.Eng.
--
-- Modified:       
--
-- Description:    Testbench for the as_tb_image_writer module.
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
--! @file  as_sim_image_writer_tb.vhd
--! @brief Testbench for the as_tb_image_writer module.
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

library fileOps;

entity as_sim_image_writer_tb is
end as_sim_image_writer_tb;

architecture Behavioral of as_sim_image_writer_tb is
  component as_sim_image_writer is
    generic(
      DOUT_WIDTH : integer := 8;
      GEN_FILENAME : string := "./tb/images/lenaScaled.csv"
    );
    port(
      Clk : in std_logic;
      Reset : in std_logic;
      
      VM_IF_IN : in vm_interface;
      DATA_IN     : in  std_logic_vector(DOUT_WIDTH-1 downto 0);
      
      DONE_OUT  : out std_logic
    );
  end component;
  
  constant c_dout_width : natural := 8;
  
  signal Clk, Reset : std_logic;
  signal VM_IF_IN   : vm_interface;
  signal DATA_IN    : std_logic_vector(c_dout_width-1 downto 0);
  signal DONE_OUT   : std_logic;

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
    VM_IF_IN <= c_vm_interface_default;
    DATA_IN <= (others => '1');
    wait for 100 ns;
    wait until rising_edge(Clk);
    Reset <= '0';
    wait until rising_edge(Clk);
    VM_IF_IN.STROBE <= '1';
    VM_IF_IN.VSYNC <= '1';
    for line in 0 to 11 loop
      VM_IF_IN.HSYNC <= '1';
      for pixel in 0 to 15 loop
        DATA_IN <= std_logic_vector(to_unsigned(pixel, DATA_IN'LENGTH));
        wait until rising_edge(Clk);
        VM_IF_IN.HSYNC <= '0';
        VM_IF_IN.VSYNC <= '0';
      end loop;
    end loop;
    VM_IF_IN.VSYNC <= '1';
    VM_IF_IN.HSYNC <= '1';
    DATA_IN <= (others => '1');
    wait until rising_edge(Clk);
    VM_IF_IN.VSYNC <= '0';
    VM_IF_IN.HSYNC <= '0';
    
    wait until DONE_OUT = '1';
    wait until rising_edge(Clk);
    wait until rising_edge(Clk);
    wait until rising_edge(Clk);
    
    assert false
      report "End of Simulation"
      severity failure;
    wait;
  end process;
  
  WRITER: as_sim_image_writer
    generic map(
      DOUT_WIDTH => c_dout_width,
      GEN_FILENAME => "./tb/images/imageWriterTest.csv"
    )
    port map(
      Clk => Clk,
      Reset =>Reset,
      
      VM_IF_IN => VM_IF_IN,
      DATA_IN => DATA_IN,
      
      DONE_OUT => DONE_OUT
    );
    
end Behavioral;

