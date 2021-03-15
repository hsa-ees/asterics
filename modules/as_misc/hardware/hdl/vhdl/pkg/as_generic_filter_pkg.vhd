----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_generic_filter_pkg
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Philip Manke, Tobias Schwarz
--
-- Description:    Package for generic filter functions and constants
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
--! @file  as_generic_filter.vhd
--! @brief Helper package for 2D Window Pipeline systems.
--! @addtogroup asterics_helpers
--! @{
--! @defgroup as_generic_filter as_generic_filter: ASTERICS Helpers for 2D Window Pipelines
--! This helper package contains data types and functions for 2D Window Pipeline systems.
--! @}
----------------------------------------------------------------------------------

--! @addtogroup as_generic_filter
--! @{

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

library asterics;
use asterics.helpers.all;

package as_generic_filter is
    type t_generic_window is array(natural range<>, natural range<>, natural range<>) of std_logic;
    type t_generic_line is array(natural range<>, natural range<>) of std_logic;
    type t_generic_filter is array(natural range<>, natural range<>) of integer;
    type t_integer_array is array(natural range<>) of integer;

    function f_make_generic_line(signal int_array : in t_integer_array; constant bit_width : in integer) return t_generic_line;

    function f_get_int_array_part_sum(constant int_array : in t_integer_array; constant from_idx : in integer; constant to_idx : in integer) return integer;
    function f_get_filter_sum_abs(constant gfilter : in t_generic_filter) return natural;
    function f_get_int_array_sum(constant int_array : in t_integer_array) return integer;
    function f_get_window_sum_abs(constant gwindow : in t_generic_window) return natural;
    function f_get_filter_max(constant gfilter : in t_generic_filter) return natural; 
    function f_get_filter_elements_count(constant gfilter: in t_generic_filter) return integer; -- number of elements in generic filter
    function f_relu(constant value : in integer) return integer;
    function f_get_vector_of_generic_window(signal gwindow : in t_generic_window; constant x : in integer; constant y : in integer) return std_logic_vector;
    procedure f_set_vector_of_generic_window(signal gwindow : out t_generic_window; constant x : in integer; constant y : in integer; constant vector : in std_logic_vector);
    function f_get_vector_of_generic_line(signal gline : in t_generic_line; constant x : in integer) return std_logic_vector;
    procedure f_set_vector_of_generic_line(signal gline : out t_generic_line; constant x : in integer; constant vector : in std_logic_vector);

    function f_make_generic_window(constant x : in integer; constant y : in integer; constant values : in t_integer_array; constant data_width : in integer) return t_generic_window;

    function f_get_line_of_generic_window(signal gwindow : in t_generic_window; constant y : in integer) return t_generic_line;
    function f_get_part_of_generic_line(signal gline : in t_generic_line; constant from_x : in integer; constant width_part : in integer) return t_generic_line;
    function f_get_part_line_of_generic_window(signal gwindow : in t_generic_window; constant y : in integer; constant from_x : in integer; constant width_part : in integer) return t_generic_line;

    function f_cut_vectors_of_generic_window(constant gwindow : in t_generic_window; constant from_b : in integer; constant width_b : in integer) return t_generic_window;
    function f_cut_vectors_of_generic_line(constant gline : in t_generic_line; constant from_b : in integer; constant width_b : in integer) return t_generic_line;
    procedure f_set_line_of_generic_window(signal gwindow : out t_generic_window; constant y : in integer; constant line_in : in t_generic_line);
    function select_kernel(size : integer; filter_type : string) return t_integer_array;
    function f_get_line_of_generic_filter(constant gfilter : in t_generic_filter; constant y : in integer) return t_integer_array;
    function f_convert_generic_window_to_vector(signal gwindow : in t_generic_window) return std_logic_vector;
    function f_convert_vector_to_generic_window(signal vector : in std_logic_vector; constant window_width : in integer; constant window_height : in integer) return t_generic_window;
    procedure f_set_line_of_generic_filter(signal gfilter : out t_generic_filter; constant values : in t_integer_array; constant line_num : in integer);

    procedure f_set_line_of_generic_filter_variable(variable gfilter : out t_generic_filter; constant values : in t_integer_array; constant line_num : in integer);
    function f_collapse_generic_filter_to_max_line(constant gfilter : in t_generic_filter) return t_integer_array;

end package as_generic_filter;

--! @}

package body as_generic_filter is

  function f_collapse_generic_filter_to_max_line(constant gfilter : in t_generic_filter) return t_integer_array is
    variable array_out : t_integer_array(gfilter'range(2));
    variable comp : integer;
  begin
    for X in gfilter'range(2) loop
      comp := 0;
      for Y in gfilter'range(1) loop
        comp := maximum(abs(gfilter(Y, X)), comp);
      end loop;
      array_out(X) := comp;
    end loop;
    return array_out;
  end function;

  procedure f_set_line_of_generic_filter_variable(variable gfilter : out t_generic_filter; constant values : in t_integer_array; constant line_num : in integer) is
  begin
    for N in values'range loop
      gfilter(line_num, N) := values(N);
    end loop;
  end procedure;

  procedure f_set_line_of_generic_filter(signal gfilter : out t_generic_filter; constant values : in t_integer_array; constant line_num : in integer) is
  begin
    for N in values'range loop
      gfilter(line_num, N) <= values(N);
    end loop;
  end procedure;

  function f_convert_generic_window_to_vector(signal gwindow : in t_generic_window) return std_logic_vector is
    constant vector_width : integer := gwindow'length(1) * gwindow'length(2) * gwindow'length(3);
    variable vector_out : std_logic_vector(vector_width - 1 downto 0);
    variable vector_idx : integer := 0;
  begin
    for X in gwindow'range(1) loop
      for Y in gwindow'range(2) loop
        for N in gwindow'range(3) loop
          vector_out(vector_idx) := gwindow(X, Y, N);
          vector_idx := vector_idx + 1;
        end loop; 
      end loop; 
    end loop; 
    return vector_out;
  end function;

  function f_convert_vector_to_generic_window(signal vector : in std_logic_vector; constant window_width : in integer; constant window_height : in integer) return t_generic_window is
    constant vector_bit_width : integer := vector'length / (window_height * window_width);
    variable window_out : t_generic_window(0 to window_width - 1, 0 to window_height - 1, vector_bit_width - 1 downto 0);
    variable vector_idx : integer := 0;
  begin
    for X in window_out'range(1) loop
      for Y in window_out'range(2) loop
        for N in window_out'range(3) loop
          window_out(X, Y, N) := vector(vector_idx);
          vector_idx := vector_idx + 1;
        end loop; 
      end loop; 
    end loop; 
    return window_out;
  end function;

  function f_get_int_array_sum(constant int_array : in t_integer_array) return integer is
  begin
    return f_get_int_array_part_sum(int_array, 0, int_array'length - 1);
  end function;

  function f_get_int_array_part_sum(constant int_array : in t_integer_array; constant from_idx : in integer; constant to_idx : in integer) return integer is
    variable akk : integer := 0;
  begin
    for N in from_idx to to_idx loop
      akk := akk + int_array(N);
    end loop;
    return akk;
  end function;

  function f_get_filter_sum_abs(constant gfilter : in t_generic_filter) return natural is
    variable sum : integer := 0; 
    constant width : integer := gfilter'length(1);
    constant height : integer := gfilter'length(2);
  begin
    for i in 0 to width-1 loop
      for j in 0 to height-1 loop
        sum := sum + abs(gfilter(i,j));
      end loop;
    end loop;
    return sum;
  end f_get_filter_sum_abs;

  function f_get_window_sum_abs(constant gwindow : in t_generic_window) return natural is
    variable sum : natural := 0;
    variable value : signed(gwindow'range(3));
  begin
    for x in gwindow'range(1) loop
      for y in gwindow'range(2) loop
        value := (others => '0');
        for n in gwindow'range(3) loop
          value(n) := gwindow(x, y, n);
        end loop;
        sum := sum + abs(to_integer(value));
      end loop;
    end loop;
    return sum;
  end f_get_window_sum_abs;
  
  function f_get_filter_max(constant gfilter : in t_generic_filter) return natural is
    variable max : natural := 0;
    constant width : integer := gfilter'length(1);
    constant height : integer := gfilter'length(2);
  begin
    for i in 0 to width-1 loop
      for j in 0 to height-1 loop
        if abs(gfilter(i,j)) > max then
          max := abs(gfilter(i,j));
        end if;
      end loop;
    end loop;
    return max;
  end f_get_filter_max;
  
  function f_get_filter_elements_count(constant gfilter : in t_generic_filter) return integer is
  begin
    return gfilter'length(1) * gfilter'length(2);
  end f_get_filter_elements_count;

  function f_relu(constant value : in integer) return integer is
  begin
    if value < 0 then
      return 0;
    end if;
    return value;
  end f_relu;

  function f_get_vector_of_generic_window(signal gwindow : in t_generic_window; constant x : in integer; constant y : in integer) return std_logic_vector is
    variable vector : std_logic_vector(gwindow'range(3));
  begin
    for i in gwindow'range(3) loop
      vector(i) := gwindow(x, y, i);
    end loop;
    return vector;
  end f_get_vector_of_generic_window;
  
  procedure f_set_vector_of_generic_window(signal gwindow : out t_generic_window; constant x : in integer; constant y : in integer; constant vector : in std_logic_vector) is
  begin
      for i in gwindow'range(3) loop
          gwindow(x,y,i) <= vector(i);
      end loop;
  end f_set_vector_of_generic_window;

  procedure f_set_vector_of_generic_line(signal gline : out t_generic_line; constant x : in integer; constant vector : in std_logic_vector) is
  begin
      for i in gline'range(2) loop
          gline(x,i) <= vector(i);
      end loop;
  end f_set_vector_of_generic_line;

  function f_make_generic_line(signal int_array : in t_integer_array; constant bit_width : in integer) return t_generic_line is
    variable line_out : t_generic_line(int_array'range, bit_width - 1 downto 0);
    variable vector : std_logic_vector(bit_width - 1 downto 0);
  begin
    for X in int_array'range loop
      vector := std_logic_vector(to_signed(int_array(X), bit_width));
      for B in vector'range loop
        line_out(X, B) := vector(B);
      end loop;
    end loop;
    return line_out;
  end function;

  function f_get_vector_of_generic_line(signal gline : in t_generic_line; constant x : in integer) return std_logic_vector is
    variable vector : std_logic_vector(gline'length(2)-1 downto 0);
  begin
    for i in gline'range(2) loop
      vector(i) := gline(x, i);
    end loop;
    return vector;
  end f_get_vector_of_generic_line;


  function f_make_generic_window(constant x : in integer; constant y : in integer; constant values : in t_integer_array; constant data_width : in integer) return t_generic_window is
    variable window_out : t_generic_window(0 to x - 1, 0 to y - 1, data_width - 1 downto 0);
    variable value : std_logic_vector(data_width - 1 downto 0);
    variable value_signed : signed(data_width - 1 downto 0);
  begin
    for x_it in window_out'range(1) loop
      for y_it in window_out'range(2) loop
        -- Prepare the value to write to the window
        value_signed := to_signed(values(x_it + y_it * window_out'length(1)), data_width);
        
        value := std_logic_vector(value_signed);
        for n in window_out'range(3) loop
          window_out(x_it, y_it, n) := value(n);
        end loop;
      end loop;
    end loop;
    return window_out;
  end f_make_generic_window;

  function f_get_line_of_generic_window(signal gwindow : in t_generic_window; constant y : in integer) return t_generic_line is
    variable line_out : t_generic_line(gwindow'range(1), gwindow'range(3));
  begin
    for x in gwindow'range(1) loop
      for i in gwindow'range(3) loop
        line_out(x, i) := gwindow(x, y, i);
      end loop;
    end loop;
    return line_out;
  end f_get_line_of_generic_window;


  function f_get_line_of_generic_filter(constant gfilter : in t_generic_filter; constant y : in integer) return t_integer_array is
    variable line_out : t_integer_array(gfilter'range(2));
  begin
    for x in gfilter'range(2) loop
      line_out(x) := gfilter(y, x);
    end loop;
    return line_out;
  end f_get_line_of_generic_filter;

  function f_get_part_of_generic_line(signal gline : in t_generic_line; constant from_x : in integer; constant width_part : in integer) return t_generic_line is
    variable gline_out : t_generic_line(0 to width_part - 1, gline'range(2));
  begin
    for x in gline_out'range(1) loop
      for b in gline_out'range(2) loop
        gline_out(x, b) := gline(from_x + x, b);
      end loop;
    end loop;
    return gline_out;
  end f_get_part_of_generic_line;

  function f_get_part_line_of_generic_window(signal gwindow : in t_generic_window; constant y : in integer; constant from_x : in integer; constant width_part : in integer) return t_generic_line is
    variable line_out : t_generic_line(0 to width_part - 1, gwindow'range(3));
  begin
    assert gwindow'length(1) >= from_x + width_part
        report "Access to generic window out of bounds!"
        severity failure;

    for x in line_out'range(1) loop
      for i in gwindow'range(3) loop
        line_out(x, i) := gwindow(x + from_x, y, i);
      end loop;
    end loop;
    return line_out;

  end f_get_part_line_of_generic_window;
  
  procedure f_set_line_of_generic_window(signal gwindow : out t_generic_window; constant y : in integer; constant line_in : in t_generic_line) is
  begin
      for x in gwindow'range(1) loop
        for i in gwindow'range(3) loop
            gwindow(x, y, i) <= line_in(x, i);
        end loop;
      end loop;
  end f_set_line_of_generic_window;

  function f_cut_vectors_of_generic_line(constant gline : in t_generic_line; constant from_b : in integer; constant width_b : in integer) return t_generic_line is
    variable gline_out : t_generic_line(gline'range, width_b - 1 downto 0);
  begin
    for x in gline'range(1) loop
      for b in gline_out'range(2) loop
        gline_out(x, b) := gline(x, b + from_b);
      end loop;
    end loop;
    return gline_out;
  end f_cut_vectors_of_generic_line;

  function f_cut_vectors_of_generic_window(constant gwindow : in t_generic_window; constant from_b : in integer; constant width_b : in integer) return t_generic_window is
    variable gwindow_out : t_generic_window(gwindow'range(1), gwindow'range(2), width_b - 1 downto 0);
  begin
    for x in gwindow'range(1) loop
      for y in gwindow'range(2) loop
        for b in gwindow_out'range(3) loop
          gwindow_out(x, y, b) := gwindow(x, y, b + from_b);
        end loop;
      end loop;
    end loop;
    return gwindow_out;
  end f_cut_vectors_of_generic_window;
  
  -- Filter kernels:

  function select_kernel(size : integer; filter_type : string) return t_integer_array is
  begin
    if filter_type = "sobel_x" then
      if size = 3 then
        return (1, 0, -1,
                2, 0, -2,
                1, 0, -1);
      elsif size = 5 then
        return (2, 1, 0, -1, -2,
                2, 1, 0, -1, -2,
                4, 2, 0, -2, -4,
                2, 1, 0, -1, -2,
                2, 1, 0, -1, -2);
      end if;
    elsif filter_type = "sobel_y" then
      if size = 3 then
        return ( 1,  2,  1,
                 0,  0,  0,
                -1, -2, -1);
      elsif size = 5 then
        return ( 2,  2,  4,  2,  2,
                 1,  1,  2,  1,  1,
                 0,  0,  0,  0,  0,
                -1, -1, -2, -1, -1,
                -2, -2, -4, -2, -2);
      end if;
  elsif filter_type = "laplace" then
      if size = 3 then
        return (-1, -1, -1,
                -1,  8, -1,
                -1, -1, -1);
      elsif size = 5 then
        return ( 0,  0, -1,  0,  0,
                 0, -1, -2, -1,  0,
                -1, -2, 16, -2, -1,
                 0, -1, -2, -1,  0,
                 0,  0, -1,  0,  0);
      end if;
    elsif filter_type = "gauss" then
      if size = 3 then
        return (1, 2, 1,
                2, 4, 2,
                1, 2, 1);
      elsif size = 5 then
        return (1, 2,  4, 2, 1,
                2, 4,  8, 4, 2,
                4, 8, 16, 8, 4,
                2, 4,  8, 4, 2,
                1, 2,  4, 2, 1);
      elsif size = 7 then
        return (1,  2,  4,  8,  4,  2, 1,
                2,  4,  8, 16,  8,  4, 2,
                4,  8, 16, 32, 16,  8, 4,
                8, 16, 32, 64, 32, 16, 8,
                4,  8, 16, 32, 16,  8, 4,
                2,  4,  8, 16,  8,  4, 2,
                1,  2,  4,  8,  4,  2, 1);
      elsif size = 9 then
        return ( 1,  2,  4,   8,  16,   8,  4,  2,  1,
                 2,  4,  8,  16,  32,  16,  8,  4,  2,
                 4,  8, 16,  32,  64,  32, 16,  8,  4,
                 8, 16, 32,  64, 128,  64, 32, 16,  8,
                16, 32, 64, 128, 256, 128, 64, 32, 16,
                 8, 16, 32,  64, 128,  64, 32, 16,  8,
                 4,  8, 16,  32,  64,  32, 16,  8,  4,
                 2,  4,  8,  16,  32,  16,  8,  4,  2,
                 1,  2,  4,   8,  16,   8,  4,  2,  1);
      elsif size = 11 then
        return ( 1,  2,   4,   8,  16,   32,  16,   8,   4,  2,  1,
                 2,  4,   8,  16,  32,   64,  32,  16,   8,  4,  2,
                 4,  8,  16,  32,  64,  128,  64,  32,  16,  8,  4,
                 8, 16,  32,  64, 128,  256, 128,  64,  32, 16,  8,
                16, 32,  64, 128, 256,  512, 256, 128,  64, 32, 16,
                32, 64, 128, 256, 512, 1024, 512, 256, 128, 64, 32,
                16, 32,  64, 128, 256,  512, 256, 128,  64, 32, 16,
                 8, 16,  32,  64, 128,  256, 128,  64,  32, 16,  8,
                 4,  8,  16,  32,  64,  128,  64,  32,  16,  8,  4,
                 2,  4,   8,  16,  32,   64,  32,  16,   8,  4,  2,
                 1,  2,   4,   8,  16,   32,  16,   8,   4,  2,  1);
      elsif size = 13 then
        return ( 
          1,   2,   4,   8,   16,   32,   64,   32,   16,   8,   4,   2,  1,
          2,   4,   8,  16,   32,   64,  128,   64,   32,  16,   8,   4,  2,
          4,   8,  16,  32,   64,  128,  256,  128,   64,  32,  16,   8,  4,
          8,  16,  32,  64,  128,  256,  512,  256,  128,  64,  32,  16,  8,
         16,  32,  64, 128,  256,  512, 1024,  512,  256, 128,  64,  32, 16,
         32,  64, 128, 256,  512, 1024, 1024, 1024,  512, 256, 128,  64, 32,
         64, 128, 256, 512, 1024, 1024, 2048, 1024, 1024, 512, 256, 128, 64, 
         32,  64, 128, 256,  512, 1024, 1024, 1024,  512, 256, 128,  64, 32,
         16,  32,  64, 128,  256,  512, 1024,  512,  256, 128,  64,  32, 16,
          8,  16,  32,  64,  128,  256,  512,  256,  128,  64,  32,  16,  8,
          4,   8,  16,  32,   64,  128,  256,  128,   64,  32,  16,   8,  4,
          2,   4,   8,  16,   32,   64,  128,   64,   32,  16,   8,   4,  2,
          1,   2,   4,   8,   16,   32,   64,   32,   16,   8,   4,   2,  1
        );
      end if;
    end if;
    report "Invalid kernel arguments passed! Kernel of this size or name does not exist! Available kernels: sobel_x, sobel_y, laplace: of sizes 3, 5; gauss: of sizes 3, 5, 7, 9, 11." severity Failure;
  end function;

end as_generic_filter;

