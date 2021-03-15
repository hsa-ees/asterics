------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
------------------------------------------------------------------------
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
------------------------------------------------------------------------
-- Entity:         as_feature_counter
--
-- Company:        University of Applied Sciences, Augsburg, Germany
--                 Efficient Embedded Systems Group
--                 http://ees.hs-augsburg.de
--
-- Author:         Philip Manke
--
-- Modified:       
--
-- Description:    Simple module to count the number of clock cycles that a
--                 signal is high (mainly the strobe signal)
------------------------------------------------------------------------
--! @file  as_feature_counter.vhd
--! @brief Simple generic counter module
--! @addtogroup asterics_modules
--! @{
--! @defgroup as_feature_counter as_feature_counter: Feature Counter
--! Simple module to count the number of clock cycles that a
--! signal is high (mainly the strobe signal)
--! For use in 2D Window Pipeline systems.
--! @}
----------------------------------------------------------------------------------

--! @addtogroup as_feature_counter
--! @{

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity as_feature_counter is
  generic(
    COUNTER_WIDTH : integer := 32
  );
  port(
    clk   : in std_logic;
    reset : in std_logic;
    
    trigger_in : in  std_logic;
    frame_done : in std_logic;
    count_out : out std_logic_vector(COUNTER_WIDTH - 1 downto 0)
  );
end as_feature_counter;

--! @}

architecture RTL of as_feature_counter is
  signal counter : unsigned(COUNTER_WIDTH - 1 downto 0);
  signal reset_counter : std_logic;
begin

  count_out <= std_logic_vector(counter);

  p_set_reset_signal : process(clk) is
  begin
    if rising_edge(clk) then
      if reset = '1' then
        reset_counter <= '0';
      else
        if reset_counter = '1' and trigger_in = '1' then
          reset_counter <= '0';
        elsif frame_done = '1' then
          reset_counter <= '1';
        end if;
      end if;
    end if;
  end process;

  p_feature_count : process(clk)
  begin
    if rising_edge(clk) then
      if reset = '1' then
        counter <= (others => '0');
      else
        if trigger_in = '1' then
          if reset_counter = '1' then
            counter <= to_unsigned(1, COUNTER_WIDTH);
          else
            counter <= counter + 1;
          end if;
        end if;
      end if;
    end if;
  end process;

end architecture;
