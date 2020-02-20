----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_filter_mask_pkg
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Markus Bihler, Alexander Zoellner
--
-- Modified:       2019-04-08; Philip Manke: Rename to "as_filter_mask"
--
-- Description:    Package for edge detection
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
--! @file  as_filter_mask.vhd
--! @brief Package for edge detection
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

package as_filter_mask is
        --constant c_XRES : natural := 640;
        --constant c_YRES : natural := 480;
        
        constant c_bitsPerPixel : natural := 8;
        --subtype   t_pixel                 is std_logic_vector(natural range <>);--(c_bitsPerPixel-1 downto 0); 
    
    type        t_pixelVector8Bit is array (natural range <>) of std_logic_vector(7 downto 0);
    type        t_pixelVector9Bit is array (natural range <>) of std_logic_vector(8 downto 0);
        
    type        t_frame             is array(natural range <>, natural range <>) of std_logic_vector(c_bitsPerPixel-1 downto 0);
      
    
    constant c_filterWidth  : natural := 3; -- width/heigth of filter matrix (nxn-Matrix)
    constant c_filterElements : natural := c_filterWidth*c_filterWidth; -- number of elements
    type  t_filter  is array (0 to c_filterWidth-1, 0 to c_filterWidth-1) of integer;

    -- Data of the 2D-window pipeline is shifted from bottom right to top left. In literature an orientation of left top to bottom right 
    -- is most common. Therefore, filter masks are mirrored vertically and horizontally in regard to filter masks found in literature. 
    constant c_filterSobelX : t_filter := ((1, 0, -1),
                                           (2, 0, -2),
                                           (1, 0, -1));
    constant c_filterSobelY : t_filter := ((1, 2, 1),
                                           ( 0,  0,  0),
                                           ( -1, -2, -1));
    constant c_filterGauss3x3 : t_filter := ((1, 2, 1),
                                             (2, 4, 2),
                                             (1, 2, 1));
    constant c_0_deg : std_logic_vector(1 downto 0) := "00";
    constant c_45_deg : std_logic_vector(1 downto 0) := "01";
    constant c_90_deg : std_logic_vector(1 downto 0) := "10";
    constant c_135_deg : std_logic_vector(1 downto 0) := "11";
    
    type    t_window3x3x8   is array (2 downto 0) of t_pixelVector8Bit(2 downto 0);
    type    t_window3x3x9   is array (2 downto 0) of t_pixelVector9Bit(2 downto 0);
    type    t_window4x4x8   is array (3 downto 0) of t_pixelVector8Bit(3 downto 0);
    
    function f_filterGetMax(constant filter : in t_filter) return natural; 
    function f_filterGetSumAbs(constant filter : in t_filter) return natural; 
    function f_filterGetSum(constant filter : in t_filter) return integer;
    -- function <function_name>  (signal <signal_name> : in <type_declaration>) return <type_declaration>;

    type as_interface is record
      VSYNC    : std_logic;
      HSYNC    : std_logic;
      STROBE   : std_logic;
      XRES     : std_logic_vector(11 downto 0);
      YRES     : std_logic_vector(11 downto 0); 
    end record;
    constant c_as_interface_default : as_interface := (
      VSYNC  => '0',
      HSYNC  => '0',
      STROBE => '0',
      XRES => (others => '0'),
      YRES => (others => '0')
    );
    

end package as_filter_mask;

package body as_filter_mask is
    
    function f_filterGetMax(constant filter : in t_filter) return natural is
      variable max : integer := 0;
    begin
      for i in 0 to c_filterWidth-1 loop
        for j in 0 to c_filterWidth-1 loop
          if abs(filter(i,j)) > max then
            max := abs(filter(i,j));
          end if;
        end loop;
      end loop;
      return max;
    end f_filterGetMax;
    
    function f_filterGetSumAbs(constant filter : in t_filter) return natural is
      variable sum : integer := 0;
    begin
      for i in 0 to c_filterWidth-1 loop
        for j in 0 to c_filterWidth-1 loop
          sum := sum + abs(filter(i,j));
        end loop;
      end loop;
      return sum;
    end f_filterGetSumAbs;
    
    function f_filterGetSum(constant filter : in t_filter) return integer is
      variable sum : integer := 0;
    begin
      for i in 0 to c_filterWidth-1 loop
        for j in 0 to c_filterWidth-1 loop
          sum := sum + filter(i,j);
        end loop;
      end loop;
      return sum;
    end f_filterGetSum; 
end as_filter_mask;
