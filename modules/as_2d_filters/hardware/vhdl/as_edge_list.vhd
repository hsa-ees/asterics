------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
------------------------ LICENSE ----------------------------------------
-- This program is free software; you can redistribute it and/or
-- modify it under the terms of the GNU Lesser General Public
-- License as published by the Free Software Foundation; either
-- version 3 of the License, or (at your option) any later version.
-- 
-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
-- Lesser General Public License for more details.
-- 
-- You should have received a copy of the GNU Lesser General Public License
-- along with this program; if not, see <http://www.gnu.org/licenses/>
-- or write to the Free Software Foundation, Inc.,
-- 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
------------------------------------------------------------------------
-- Entity:         as_edge_list
--
-- Company:        University of Applied Sciences, Augsburg, Germany
--                 Efficient Embedded Systems Group
--                 http://ees.hs-augsburg.de
--
-- Author:         Markus Bihler, Alexander Zoellner, Julian Sarcher
--
-- Modified:       2017-06-07;
--                 2020-03-20; Philip Manke: Adapt interface names 
--                               to new ASTERICS standard; Update header
--
-- Description:    This module generates a list of edges with 
--                 coordinates from a edge image. HSYNC and VSYNC have 
--                 to arrive one STROBE earlier than the actual 
--                 synchronization signals.
--
------------------------------------------------------------------------
-- This file is part of the ChASA project, which has been supported by 
-- the German Federal Ministry for Economic Affairs and Energy, grant 
-- number ZF4102001KM5.
------------------------------------------------------------------------
--! @file  as_edge_list.vhd
--! @brief Edge position and direction feature vector generator.
--! @addtogroup asterics_modules
--! @{
--! @defgroup as_edge_list as_edge_list: Edge feature vector
--! Using synchronization signals and edge direction data a feature vector is
--! generated including the edge position (x, y) and the direction data.
--! For use in 2D Window Pipeline systems.
--! @}
----------------------------------------------------------------------------------

--! @addtogroup as_edge_list
--! @{


library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

library asterics;
use asterics.helpers.all;

entity as_edge_list is
generic(
    DIN_WIDTH               : natural := 8;
    X_COORDINATE_WIDTH      : natural := 12;
    Y_COORDINATE_WIDTH      : natural := 12;
    XRES                    : natural := 640; 
    YRES                    : natural := 480
  );
  port(
    clk : in std_logic;
    reset : in std_logic;
    
    -- IN ports
    vsync_in    : in  std_logic;
    hsync_in    : in  std_logic;
    strobe_in   : in  std_logic;
    is_edge_in  : in  std_logic_vector(1 downto 0);
    edge_data_in : in std_logic_vector(DIN_WIDTH - 1 downto 0);

    -- OUT ports
    strobe_out  : out std_logic;
    -- Feature output: MSB < y coordinate, x coordinate, weighted edge > LSB
    data_out : out std_logic_vector(31 downto 0)
  );
  
end as_edge_list;

--! @}

architecture RTL of as_edge_list is
    
    signal r_rowCnt         : unsigned(Y_COORDINATE_WIDTH - 1 downto 0); 
    signal r_pixCnt         : unsigned(X_COORDINATE_WIDTH - 1 downto 0);
    signal r_param_y_top    : unsigned(Y_COORDINATE_WIDTH - 1 downto 0);
    signal r_param_x_left   : unsigned(X_COORDINATE_WIDTH - 1 downto 0);
    signal r_param_y_bottom : unsigned(Y_COORDINATE_WIDTH - 1 downto 0);
    signal r_param_x_right  : unsigned(X_COORDINATE_WIDTH - 1 downto 0);
    
    constant border_crop_cnt  : integer := 3; 

begin            
  assert X_COORDINATE_WIDTH + Y_COORDINATE_WIDTH + DIN_WIDTH <= 32 
    report "Coordinate widths and data width of feature module MUST fit into a 32 bit word! - Out of bounds!" 
    severity Failure;           

  r_param_x_left    <= to_unsigned(border_crop_cnt, r_param_x_left'length);
  r_param_y_top     <= to_unsigned(border_crop_cnt, r_param_y_top'length);
  r_param_x_right   <= to_unsigned(XRES - border_crop_cnt, r_param_x_right'length);
  r_param_y_bottom  <= to_unsigned(YRES - border_crop_cnt, r_param_y_bottom'length);


  -- counter for X/y_out
  p_pixRowCntOut : process (clk, reset)
  begin
    if reset = '1' then
      r_rowCnt <= (others => '0');
      r_pixCnt <= (others => '0');
    elsif rising_edge(clk) then
      if strobe_in = '1' then -- new pixel
        r_pixCnt <= r_pixCnt + 1;
        if hsync_in = '1' then -- new row
          r_rowCnt <= r_rowCnt + 1;
          r_pixCnt <= to_unsigned(0, r_pixCnt'length);
        end if;
        if vsync_in = '1' then -- new frame
          r_pixCnt <= to_unsigned(0, r_pixCnt'length);
          r_rowCnt <= to_unsigned(0, r_rowCnt'length);
        end if;
      end if;
    end if;
  end process;
  
  p_strobe : process(clk, reset)
  begin
    if reset = '1' then
      strobe_out <= '0';
    elsif rising_edge(clk) then
      if strobe_in = '1' then
        if is_edge_in(1) = '1' then
        -- remove invalid detected pixels near the border
            if      r_pixCnt > (r_param_x_left - 1)
                and r_pixCnt < r_param_x_right
                and r_rowCnt > (r_param_y_top - 1)
                and r_rowCnt < r_param_y_bottom then
                strobe_out <= '1';
            else
                strobe_out <= '0';
            end if;
        else
            strobe_out <= '0';
        end if;
      end if;
    end if;
  end process;

  no_output_padding_g : if X_COORDINATE_WIDTH + Y_COORDINATE_WIDTH + DIN_WIDTH = 32 generate
    data_out <= std_logic_vector(r_rowCnt) & std_logic_vector(r_pixCnt) & edge_data_in;
  end generate;

  output_padding_g : if X_COORDINATE_WIDTH + Y_COORDINATE_WIDTH + DIN_WIDTH < 32 generate
    data_out(31 downto X_COORDINATE_WIDTH + Y_COORDINATE_WIDTH + DIN_WIDTH) <= (others => '0');
    data_out(X_COORDINATE_WIDTH + Y_COORDINATE_WIDTH + DIN_WIDTH - 1 downto 0) <= std_logic_vector(r_rowCnt) & std_logic_vector(r_pixCnt) & edge_data_in;
    
  end generate;
  
end architecture;

