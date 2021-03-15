------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2017 Hochschule Augsburg, University of Applied Sciences
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
-- Entity:         AS_EDGE_THRESHOLD
--
-- Company:        University of Applied Sciences, Augsburg, Germany
--                 Efficient Embedded Systems Group
--                 http://ees.hs-augsburg.de
--
-- Author:         Markus Bihler
--
-- Modified:       2017-06-07;
--                 2020-05-12; Philip Manke - Use generic window interface
--
-- Description:    Non maximum supression (delay: 1 clk)
--                 INPUT: feature nms
--                 OUTPUT: edge image
--                 
--                 compare edge pixel with all top neighbours and left 
--                 neighbour pixels  
--
------------------------------------------------------------------------
--! @file  as_edge_threshold.vhd
--! @brief Canny-style thresholding on edge data streams
--! @addtogroup asterics_modules
--! @{
--! @defgroup as_edge_threshold as_edge_threshold: Canny-style Thresholding
--! compare edge pixel with all top neighbours and left neighbour pixels.
--! For use in 2D Window Pipeline systems.
--! @}
----------------------------------------------------------------------------------

--! @addtogroup as_edge_threshold
--! @{

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

library asterics;
use asterics.as_filter_mask.all;
use asterics.as_generic_filter.all;

entity as_edge_threshold is
  generic(
    DIN_WIDTH : integer := 9;
    THRESHOLD_WIDTH : natural := 8
    );
    port(
      clk   : in std_logic;
      reset : in std_logic;
      
      strobe_in         : in  std_logic;
      nms_in            : in  std_logic_vector(DIN_WIDTH-1 downto 0);
      thr_low_in        : in  std_logic_vector(THRESHOLD_WIDTH-1 downto 0);
      thr_high_in       : in  std_logic_vector(THRESHOLD_WIDTH-1 downto 0);
      first_row_is_edge : in  t_generic_window(0 to 2, 0 to 1, 1 downto 0);

      data_out          : out std_logic_vector(1 downto 0)
    );
end as_edge_threshold;

--! @}

architecture RTL of as_edge_threshold is
  signal s_neighbourIsEdge : std_logic; -- indicates that a neighbour pixel is an edge
  signal s_pixelIsEdge     : std_logic; -- indicates that the current pixel is an edge
  signal r_pixelIsEdge     : std_logic; -- indicates that the pixel calculated before, was an edge
  
  signal s_window_top_IsEdge      : std_logic;
  signal s_edge_pixel_IsEdge_low  : std_logic;
  signal s_edge_pixel_IsEdge_high : std_logic;

begin

  -- ############## Is Edge ##################
  s_window_top_IsEdge <= f_get_vector_of_generic_window(first_row_is_edge, 0, 1)(1)
                      or f_get_vector_of_generic_window(first_row_is_edge, 1, 1)(1)
                      or f_get_vector_of_generic_window(first_row_is_edge, 2, 1)(1);
  s_edge_pixel_IsEdge_low <= '1' when unsigned(nms_in) > unsigned(thr_low_in) else '0';
  s_edge_pixel_IsEdge_high <= '1' when unsigned(nms_in) > unsigned(thr_high_in) else '0';
  s_neighbourIsEdge <= s_window_top_IsEdge
                       or r_pixelIsEdge; -- pixel calculated in last clk cycle
                    
  
  s_pixelIsEdge <= (s_edge_pixel_IsEdge_low and s_neighbourIsEdge)
                   or s_edge_pixel_IsEdge_high;
  -- ############## Is Edge END ##################
  
  p_feature_nms : process(clk)
  begin
    if rising_edge(clk) then
 
      if reset = '1' then
        r_pixelIsEdge <= '0';
        data_out <= "00";
      -- valid data
      elsif strobe_in = '1' then
        r_pixelIsEdge <= s_pixelIsEdge;
        if s_pixelIsEdge = '1' then
          data_out <= "11";
        elsif s_edge_pixel_IsEdge_low = '1' then
          data_out <= "01";
        else
          data_out <= "00";
        end if;
      end if;
    end if;
  end process;
end architecture;
