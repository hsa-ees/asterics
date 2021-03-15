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
-- Entity:         AS_EDGE_NMS
--
-- Company:        University of Applied Sciences, Augsburg, Germany
--                 Efficient Embedded Systems Group
--                 http://ees.hs-augsburg.de
--
-- Author:         Markus Bihler
--
-- Modified:       2017-06-07
--
-- Description:    Non maximum supression (delay: 1 clk)
--                 INPUT: sobel weight image and edge direction
--                 OUTPUT: sobel weight image
--                 
--                 compare edge pixel with neighbour pixel
--                 ( ---, /, \, | = gradient dir; c = compare pixel)       
--            input:    00:         01:          10:          11:
--                         0 c 0       c 0 /        0 | 0        \ 0 c
--                         - - -       0 / 0        c | c        0 \ 0
--                         0 c 0       / 0 c        0 | 0        c 0 \      
--        filter(pixel,row)
--
------------------------------------------------------------------------
--! @file  as_edge_nms.vhd
--! @brief Non-Maximum-Suppression on edge data streams using edge gradients
--! @addtogroup asterics_modules
--! @{
--! @defgroup as_edge_nms as_edge_nms: Non-Maximum-Suppression for Edge Data
--! Using reduced accuracy edge gradients (45° steps) a non-maximum-suppression
--! is performed on a 3x3 window of edge data.
--! For use in 2D Window Pipeline systems.
--! @}
----------------------------------------------------------------------------------

--! @addtogroup as_edge_nms
--! @{


library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

library asterics;
use asterics.as_filter_mask.all;
use asterics.as_generic_filter.all;

entity AS_EDGE_NMS is
  generic(
    DIN_WIDTH : integer := 9
    );
    port(
        clk   : in std_logic;
        reset : in std_logic;
        
        strobe_in        : in  std_logic;
        data_dir_in      : in  std_logic_vector(1 downto 0); -- [AS]: (0, 0, direction)
        window_weight_in : in  t_generic_window(0 to 2, 0 to 2, DIN_WIDTH - 1 downto 0); -- [AS]: (1, 1, edge_weight)
        
        data_out     : out  std_logic_vector(DIN_WIDTH - 1 downto 0) -- [AS]: (0, 1, nms_out)
    );
end AS_EDGE_NMS;

--! @}

architecture RTL of AS_EDGE_NMS is

--###########Mapping Signals##############################
  signal s_window_top_left   : unsigned(DIN_WIDTH-1 downto 0) := (others => '0');
  signal s_window_top_middle : unsigned(DIN_WIDTH-1 downto 0) := (others => '0');
  signal s_window_top_right  : unsigned(DIN_WIDTH-1 downto 0) := (others => '0');
  
  signal s_window_middle_left   : unsigned(DIN_WIDTH-1 downto 0) := (others => '0');
  signal s_window_middle_middle : unsigned(DIN_WIDTH-1 downto 0) := (others => '0');
  signal s_window_middle_right  : unsigned(DIN_WIDTH-1 downto 0) := (others => '0');
  
  signal s_window_bottom_left   : unsigned(DIN_WIDTH-1 downto 0) := (others => '0');
  signal s_window_bottom_middle : unsigned(DIN_WIDTH-1 downto 0) := (others => '0');
  signal s_window_bottom_right  : unsigned(DIN_WIDTH-1 downto 0) := (others => '0');
  -- the signals above are mapped on the signals below depending on input data_dir_in
  signal s_edge_pixel      : unsigned(DIN_WIDTH-1 downto 0) := (others => '0');
  signal s_compare_pixel_1 : unsigned(DIN_WIDTH-1 downto 0) := (others => '0');
  signal s_compare_pixel_2 : unsigned(DIN_WIDTH-1 downto 0) := (others => '0');
--###########Mapping Signals End##############################  
  
--###########Signals For Logic Operations #############################
  signal s_pixelIsMax  : unsigned(DIN_WIDTH-1 downto 0) := (others => '0'); -- indicates that the current pixel is a local maximum
  signal r_pixelIsMax  : unsigned(DIN_WIDTH-1 downto 0) := (others => '0'); -- indicates that the current pixel is a local maximum
 
begin
  
  -- ############## PIXEL ALLOCATION START #################    
  s_window_top_left   <= unsigned(f_get_vector_of_generic_window(window_weight_in, 2, 2));
  s_window_top_middle <= unsigned(f_get_vector_of_generic_window(window_weight_in, 1, 2));
  s_window_top_right  <= unsigned(f_get_vector_of_generic_window(window_weight_in, 0, 2));
  
  s_window_middle_left   <= unsigned(f_get_vector_of_generic_window(window_weight_in, 2, 1)); -- pixel calculated in last clk cycle
  s_window_middle_middle <= unsigned(f_get_vector_of_generic_window(window_weight_in, 1, 1));
  s_window_middle_right  <= unsigned(f_get_vector_of_generic_window(window_weight_in, 0, 1));
  
  s_window_bottom_left   <= unsigned(f_get_vector_of_generic_window(window_weight_in, 2, 0));
  s_window_bottom_middle <= unsigned(f_get_vector_of_generic_window(window_weight_in, 1, 0));
  s_window_bottom_right  <= unsigned(f_get_vector_of_generic_window(window_weight_in, 0, 0));
    
--                         0 0 0       0 0 c        0 c 0        c 0 0
--                         c - c       0 / 0        0 | 0        0 \ 0
--                         0 0 0       c 0 0        0 c 0        0 0 c   
  s_edge_pixel <= s_window_middle_middle;
  with data_dir_in select
  s_compare_pixel_1 <= s_window_middle_left when c_0_deg,
                       s_window_bottom_left when c_135_deg,
                       s_window_top_middle when c_90_deg,
                       s_window_bottom_right when c_45_deg,
                       (others => '0') when others;  
  with data_dir_in select                     
  s_compare_pixel_2 <= s_window_middle_right when c_0_deg,
                       s_window_top_right when c_135_deg,
                       s_window_bottom_middle when c_90_deg,
                       s_window_top_left when c_45_deg,
                       (others => '0') when others;    
  
  -- ############## PIXEL ALLOCATION END ################# 
  
  -- ############## Is Maximum ##################
  s_pixelIsMax <= s_edge_pixel when s_edge_pixel > s_compare_pixel_1
                        and s_edge_pixel > s_compare_pixel_2  
                      else (others => '0');                      
                      -- problem: if s_edge_pixel = s_compare_pixel_1 = s_compare_pixel_2 
                      --          s_edge_pixel could be a maximum or not ==> scale of image
        
  
  data_out <= std_logic_vector(r_pixelIsMax);
  
  p_feature_nms : process(clk)
  begin
    
    if rising_edge(clk) then
      if Reset = '1' then
        r_pixelIsMax <= (others => '0');
      -- valid data
      elsif strobe_in = '1' then
        r_pixelIsMax <= s_pixelIsMax;
      end if;
    end if;
  end process;

end architecture;
