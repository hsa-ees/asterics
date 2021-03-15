----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework.
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
--
-- Package:       HELPERS
--
-- Company:       Efficient Embedded Systems Group
--                University of Applied Sciences, Augsburg, Germany
--
-- Authors:       
--
-- Modified:      Philip Manke: Add custom types for the new slaveregister interface
--
-- Description:   This package defines supplemental types, subtypes,
--                constants and functions which may be used within other 
--                modules.
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

-------------------------------- DOXYGEN -----------------------------------------
--
--! @defgroup asterics_helpers ASTERICS VHDL Helper Modules
--! @{
--! This Doxygen group contains all ASTERICS VHDL packages and helpers modules
--! not specific to any ASTERICS hardware module.
--! @}
--
--! @file  helpers.vhd
--! @brief Package providing supplemental types, subtypes, constants and functions.
--! @addtogroup asterics_helpers
--! @{
--! @defgroup helpers helpers: Standard ASTERICS Helper Package
--! This package contains constants, functions and data types used frequently
--! throughout VHDL code in ASTERICS.
--! @}
----------------------------------------------------------------------------------

--! @addtogroup helpers
--! @{


library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

----

package helpers is

--! Log2 function for any _positive_ number. Implements (int) ceil(log2(n))
function log2_ceil ( n : in positive) return integer;
--! Log2 function including 0 as input (returns 0). Implements (int) ceil(log2(n))
function log2_ceil_zero ( n : in natural) return integer;
--! Alternative Log2 function accepting integers (uses absolute value of input). Implements (int) ceil(log2(n))
function log2_ceil_alt( n : in integer ) return integer;
--! Alternative Log2 variant implemented without while loops. Maximum input is 2^64. Implements (int) ceil(log2(n))
function log2_ceil_max_64( n : in integer ) return integer;
--! Alternative Log2 function using the absolute value of the input integer. Implements (int) ceil(log2(n))
function log2_ceil_zero_abs ( num : in integer) return integer;
--! Log2 function for any _positive_ number. Implements (int) floor(log2(n))
function log2_floor ( n : in positive) return integer;

function maximum(a, b : in natural) return natural;
function minimum(a, b : in natural) return natural;
function f_1d_to_2d_index (index : in natural; width : in natural) return natural;
function rotate_right(vector : in std_logic_vector; nbit : in natural) return std_logic_vector;
--! Returns the greatest common divisor between a and b. Both must be greater than 0.
function f_greatest_common_divisor(a, b : in positive) return natural;
--! Returns the least common multiple between a and b. Both must be greater than 0.
function f_least_common_multiple(a, b : in positive) return natural;

--! Slave register data vector
type slv_reg_data is array(natural range<>) of std_logic_vector(31 downto 0); 
--! Slave register configuration data vector
type slv_reg_config_table is array(natural range<>) of std_logic_vector(1 downto 0);

constant AS_REG_NONE    : std_logic_vector := "00";
constant AS_REG_STATUS  : std_logic_vector := "01";
constant AS_REG_CONTROL : std_logic_vector := "10";
constant AS_REG_BOTH    : std_logic_vector := "11";

end helpers;

--! @}

package body helpers is

function f_greatest_common_divisor(a, b : in positive) return natural is
  variable r, aa, bb : integer;
  constant maxloops : integer := 1000;
begin
  aa := a;
  bb := b;
  r := 0;
  for N in 0 to maxloops loop
    --report "aa: " & integer'image(aa) & " | bb: " & integer'image(bb);
    r := aa mod bb;
    aa := bb;
    bb := r;
    if bb = 0 then
      return aa;
    end if;
  end loop;
  report "f_greatest_common_divisor: maximum loop count reached! Failed to complete calculation." severity failure;
  return 0;
end function;

function f_least_common_multiple(a, b : in positive) return natural is 
  variable gcd : integer;
begin
  gcd := f_greatest_common_divisor(a, b);
  --report "Got gcd: " &integer'image(gcd);
  if gcd = 0 then
    return 0;
  end if;

  return (a / gcd) * b;
end function;


function log2_ceil ( n : in positive) return integer is
  variable i : integer := 1;
begin
  while (2**i < n) loop
    i := i + 1;
  end loop;
  return i;
end log2_ceil;

function log2_ceil_zero ( n : in natural) return integer is
  variable i : integer := 1;
begin
  if n < 2 then
    return 0;
  end if;
  while (2**i < n) loop
    i := i + 1;
  end loop;
  return i;
end log2_ceil_zero;

function log2_ceil_max_64( n : in integer ) return integer is
  variable temp : unsigned(63 downto 0);
begin
  temp := to_unsigned(abs(n), 64);
  if temp < 2 then
    return to_integer(temp);
  end if;
  for I in 0 to 63 loop
    temp := temp / 2;
    if temp < 2 then
      return I + 1;
    end if;
  end loop;
  return 64;
end function log2_ceil_max_64;

function log2_ceil_alt( n : in integer ) return integer is
  variable temp, log_out : integer;
begin
  temp := abs(n);
  if temp < 2 then
    return temp;
  end if;
  log_out := 0;
  while(temp > 1) loop
    temp := temp / 2;
    log_out := log_out + 1;
  end loop;
  return log_out + 1;
end function log2_ceil_alt;

function log2_ceil_zero_abs ( num : in integer) return integer is
  variable i : integer := 1;
  variable n : integer; 
begin
  n := abs(num);
  if n < 2 then
    return 0;
  end if;
  while (2**i < n) loop
    i := i + 1;
  end loop;
  return i;
end log2_ceil_zero_abs;

function log2_floor ( n : in positive) return integer is
  variable i : integer := 1;
begin
  while (2**i <= n) loop
    i := i + 1;
  end loop;
  return i - 1;
end log2_floor;

function maximum(a, b : in natural) return natural is
begin
  if a > b then return a;
  else return b;
  end if;
end;

function minimum(a, b : in natural) return natural is
begin
  if a < b then return a;
  else return b;
  end if;
end;

function rotate_right(vector : in std_logic_vector; nbit : in natural) return std_logic_vector is
begin
  return vector(nbit - 1 downto 0) & vector(vector'length - 1 downto nbit);
end rotate_right;

function f_1D_to_2D_index (index : in natural; width : in natural) return natural is
  variable v_2D_index : natural ;
  constant c_1DindexModWidth : natural := index mod width;
begin
  v_2D_index := 0;
  if c_1DindexModWidth = 0 then
    v_2D_index := (index/width) - 1;
  else
    v_2D_index := (index/width);
  end if;
  return v_2D_index;
end f_1D_to_2D_index;

end helpers;
