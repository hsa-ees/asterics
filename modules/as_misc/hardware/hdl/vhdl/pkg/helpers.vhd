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
--! @file  helpers.vhd
--! @brief Package providing supplemental types, subtypes, constants and functions.
----------------------------------------------------------------------------------


library ieee;
use ieee.std_logic_1164.all;

----

package helpers is

function log2_ceil ( n : in positive) return integer;
function log2_ceil_zero ( n : in positive) return integer;
function log2_floor ( n : in positive) return integer;
function maximum(a, b : in natural) return natural;
function minimum(a, b : in natural) return natural;
function f_1d_to_2d_index (index : in natural; width : in natural) return natural;

type slv_reg_data is array(natural range<>) of std_logic_vector(31 downto 0); 
type slv_reg_config_table is array(natural range<>) of std_logic_vector(1 downto 0);

constant AS_REG_NONE    : std_logic_vector := "00";
constant AS_REG_STATUS  : std_logic_vector := "01";
constant AS_REG_CONTROL : std_logic_vector := "10";
constant AS_REG_BOTH    : std_logic_vector := "11";

end helpers;

----

package body helpers is

function log2_ceil ( n : in positive) return integer is
  variable i : integer := 1;
begin
  while (2**i < n) loop
    i := i + 1;
  end loop;
  return i;
end log2_ceil;

function log2_ceil_zero ( n : in positive) return integer is
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
