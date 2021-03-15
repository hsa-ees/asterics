----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_cnn_helpers
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Philip Manke
--
-- Description:    Package providing constants and functions for CNN implementations in ASTERICS
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
--! @file  as_cnn_helpers.vhd
--! @brief Package for CNN implementations in ASTERICS
--! @addtogroup asterics_helpers
--! @{
--! @defgroup as_cnn_helpers as_cnn_helpers: ASTERICS Helper Package for CNN Hardware Modules
--! This package contains constants, functions and data types used frequently
--! throughout VHDL code of modules implementing functionality related to CNNs in ASTERICS.
--! @}
----------------------------------------------------------------------------------

--! @addtogroup as_cnn_helpers
--! @{


library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use IEEE.math_real.all;

library asterics;
use asterics.helpers.all;
use asterics.as_generic_filter.all;

package as_cnn_helpers is

  --! Data type used to encode a shift operator
  type t_operator_encoding is array(0 to 1) of std_logic_vector(8 downto 0);
  --! Data type used to store the shift operator lookup table
  type t_operator_table is array(0 to 255) of t_operator_encoding;
  
  --! Operators are encoded according to this scheme:
  --! The first vector defines left shift -> add operations
  --! Every '1' in the vector defines a shift operation
  --! The number of bits to shift is defined by the position of the '1' in the vector
  --! A '1' at the leftmost position defines a shift by 0 bits i.e. a multiplication by 1
  --! The second vector defines left shift -> subtract operations in the same manner
  --! Examples: 
  --! ("000100000", "000000100") =>
  --! result = (input << 5) - (input << 2)
  --! This is equivalent to: result = input * "11100" = input * 28
  --!
  --! ("000100000", "000000101") => 
  --! result = (input << 5) - ((input << 2) + (input << 0))
  --!        = (input << 5) + ((-1) * ((input << 2) + input))
  --! This is equivalent to: result = input * "11011" = input * 27
  constant c_weight_operator_table : t_operator_table := (
    ("000000000", "000000000"),  -- 0 : +[] -[]
    ("000000001", "000000000"),  -- 1 : +[1] -[]
    ("000000010", "000000000"),  -- 2 : +[2] -[]
    ("000000011", "000000000"),  -- 3 : +[1, 2] -[]
    ("000000100", "000000000"),  -- 4 : +[4] -[]
    ("000000101", "000000000"),  -- 5 : +[1, 4] -[]
    ("000000110", "000000000"),  -- 6 : +[2, 4] -[]
    ("000001000", "000000001"),  -- 7 : +[8] -[1]
    ("000001000", "000000000"),  -- 8 : +[8] -[]
    ("000001001", "000000000"),  -- 9 : +[1, 8] -[]
    ("000001010", "000000000"),  -- 10 : +[2, 8] -[]
    ("000001011", "000000000"),  -- 11 : +[1, 2, 8] -[]
    ("000001100", "000000000"),  -- 12 : +[4, 8] -[]
    ("000001101", "000000000"),  -- 13 : +[1, 4, 8] -[]
    ("000010000", "000000010"),  -- 14 : +[16] -[2]
    ("000010000", "000000001"),  -- 15 : +[16] -[1]
    ("000010000", "000000000"),  -- 16 : +[16] -[]
    ("000010001", "000000000"),  -- 17 : +[1, 16] -[]
    ("000010010", "000000000"),  -- 18 : +[2, 16] -[]
    ("000010011", "000000000"),  -- 19 : +[1, 2, 16] -[]
    ("000010100", "000000000"),  -- 20 : +[4, 16] -[]
    ("000010101", "000000000"),  -- 21 : +[1, 4, 16] -[]
    ("000010110", "000000000"),  -- 22 : +[2, 4, 16] -[]
    ("000011000", "000000001"),  -- 23 : +[8, 16] -[1]
    ("000011000", "000000000"),  -- 24 : +[8, 16] -[]
    ("000011001", "000000000"),  -- 25 : +[1, 8, 16] -[]
    ("000011010", "000000000"),  -- 26 : +[2, 8, 16] -[]
    ("000100000", "000000101"),  -- 27 : +[32] -[4, 1]
    ("000100000", "000000100"),  -- 28 : +[32] -[4]
    ("000100001", "000000100"),  -- 29 : +[32, 1] -[4]
    ("000100000", "000000010"),  -- 30 : +[32] -[2]
    ("000100000", "000000001"),  -- 31 : +[32] -[1]
    ("000100000", "000000000"),  -- 32 : +[32] -[]
    ("000100001", "000000000"),  -- 33 : +[1, 32] -[]
    ("000100010", "000000000"),  -- 34 : +[2, 32] -[]
    ("000100011", "000000000"),  -- 35 : +[1, 2, 32] -[]
    ("000100100", "000000000"),  -- 36 : +[4, 32] -[]
    ("000100101", "000000000"),  -- 37 : +[1, 4, 32] -[]
    ("000100110", "000000000"),  -- 38 : +[2, 4, 32] -[]
    ("000101000", "000000001"),  -- 39 : +[8, 32] -[1]
    ("000101000", "000000000"),  -- 40 : +[8, 32] -[]
    ("000101001", "000000000"),  -- 41 : +[1, 8, 32] -[]
    ("000101010", "000000000"),  -- 42 : +[2, 8, 32] -[]
    ("000101011", "000000000"),  -- 43 : +[1, 2, 8, 32] -[]
    ("000101100", "000000000"),  -- 44 : +[4, 8, 32] -[]
    ("000101101", "000000000"),  -- 45 : +[1, 4, 8, 32] -[]
    ("000110000", "000000010"),  -- 46 : +[16, 32] -[2]
    ("000110000", "000000001"),  -- 47 : +[16, 32] -[1]
    ("000110000", "000000000"),  -- 48 : +[16, 32] -[]
    ("000110001", "000000000"),  -- 49 : +[1, 16, 32] -[]
    ("000110010", "000000000"),  -- 50 : +[2, 16, 32] -[]
    ("000110011", "000000000"),  -- 51 : +[1, 2, 16, 32] -[]
    ("000110100", "000000000"),  -- 52 : +[4, 16, 32] -[]
    ("000110101", "000000000"),  -- 53 : +[1, 4, 16, 32] -[]
    ("001000000", "000001010"),  -- 54 : +[64] -[8, 2]
    ("001000000", "000001001"),  -- 55 : +[64] -[8, 1]
    ("001000000", "000001000"),  -- 56 : +[64] -[8]
    ("001000001", "000001000"),  -- 57 : +[64, 1] -[8]
    ("001000010", "000001000"),  -- 58 : +[64, 2] -[8]
    ("001000000", "000000101"),  -- 59 : +[64] -[4, 1]
    ("001000000", "000000100"),  -- 60 : +[64] -[4]
    ("001000001", "000000100"),  -- 61 : +[64, 1] -[4]
    ("001000000", "000000010"),  -- 62 : +[64] -[2]
    ("001000000", "000000001"),  -- 63 : +[64] -[1]
    ("001000000", "000000000"),  -- 64 : +[64] -[]
    ("001000001", "000000000"),  -- 65 : +[1, 64] -[]
    ("001000010", "000000000"),  -- 66 : +[2, 64] -[]
    ("001000011", "000000000"),  -- 67 : +[1, 2, 64] -[]
    ("001000100", "000000000"),  -- 68 : +[4, 64] -[]
    ("001000101", "000000000"),  -- 69 : +[1, 4, 64] -[]
    ("001000110", "000000000"),  -- 70 : +[2, 4, 64] -[]
    ("001001000", "000000001"),  -- 71 : +[8, 64] -[1]
    ("001001000", "000000000"),  -- 72 : +[8, 64] -[]
    ("001001001", "000000000"),  -- 73 : +[1, 8, 64] -[]
    ("001001010", "000000000"),  -- 74 : +[2, 8, 64] -[]
    ("001001011", "000000000"),  -- 75 : +[1, 2, 8, 64] -[]
    ("001001100", "000000000"),  -- 76 : +[4, 8, 64] -[]
    ("001001101", "000000000"),  -- 77 : +[1, 4, 8, 64] -[]
    ("001010000", "000000010"),  -- 78 : +[16, 64] -[2]
    ("001010000", "000000001"),  -- 79 : +[16, 64] -[1]
    ("001010000", "000000000"),  -- 80 : +[16, 64] -[]
    ("001010001", "000000000"),  -- 81 : +[1, 16, 64] -[]
    ("001010010", "000000000"),  -- 82 : +[2, 16, 64] -[]
    ("001010011", "000000000"),  -- 83 : +[1, 2, 16, 64] -[]
    ("001010100", "000000000"),  -- 84 : +[4, 16, 64] -[]
    ("001010101", "000000000"),  -- 85 : +[1, 4, 16, 64] -[]
    ("001010110", "000000000"),  -- 86 : +[2, 4, 16, 64] -[]
    ("001011000", "000000001"),  -- 87 : +[8, 16, 64] -[1]
    ("001011000", "000000000"),  -- 88 : +[8, 16, 64] -[]
    ("001011001", "000000000"),  -- 89 : +[1, 8, 16, 64] -[]
    ("001011010", "000000000"),  -- 90 : +[2, 8, 16, 64] -[]
    ("001100000", "000000101"),  -- 91 : +[32, 64] -[4, 1]
    ("001100000", "000000100"),  -- 92 : +[32, 64] -[4]
    ("001100001", "000000100"),  -- 93 : +[32, 1, 64] -[4]
    ("001100000", "000000010"),  -- 94 : +[32, 64] -[2]
    ("001100000", "000000001"),  -- 95 : +[32, 64] -[1]
    ("001100000", "000000000"),  -- 96 : +[32, 64] -[]
    ("001100001", "000000000"),  -- 97 : +[1, 32, 64] -[]
    ("001100010", "000000000"),  -- 98 : +[2, 32, 64] -[]
    ("001100011", "000000000"),  -- 99 : +[1, 2, 32, 64] -[]
    ("001100100", "000000000"),  -- 100 : +[4, 32, 64] -[]
    ("001100101", "000000000"),  -- 101 : +[1, 4, 32, 64] -[]
    ("001100110", "000000000"),  -- 102 : +[2, 4, 32, 64] -[]
    ("001101000", "000000001"),  -- 103 : +[8, 32, 64] -[1]
    ("001101000", "000000000"),  -- 104 : +[8, 32, 64] -[]
    ("001101001", "000000000"),  -- 105 : +[1, 8, 32, 64] -[]
    ("001101010", "000000000"),  -- 106 : +[2, 8, 32, 64] -[]
    ("010000000", "000010101"),  -- 107 : +[128] -[16, 4, 1]
    ("010000000", "000010100"),  -- 108 : +[128] -[16, 4]
    ("010000001", "000010100"),  -- 109 : +[128, 1] -[16, 4]
    ("010000000", "000010010"),  -- 110 : +[128] -[16, 2]
    ("010000000", "000010001"),  -- 111 : +[128] -[16, 1]
    ("010000000", "000010000"),  -- 112 : +[128] -[16]
    ("010000001", "000010000"),  -- 113 : +[128, 1] -[16]
    ("010000010", "000010000"),  -- 114 : +[128, 2] -[16]
    ("010000100", "000010001"),  -- 115 : +[128, 4] -[16, 1]
    ("010000100", "000010000"),  -- 116 : +[128, 4] -[16]
    ("010000101", "000010000"),  -- 117 : +[128, 1, 4] -[16]
    ("010000000", "000001010"),  -- 118 : +[128] -[8, 2]
    ("010000000", "000001001"),  -- 119 : +[128] -[8, 1]
    ("010000000", "000001000"),  -- 120 : +[128] -[8]
    ("010000001", "000001000"),  -- 121 : +[128, 1] -[8]
    ("010000010", "000001000"),  -- 122 : +[128, 2] -[8]
    ("010000000", "000000101"),  -- 123 : +[128] -[4, 1]
    ("010000000", "000000100"),  -- 124 : +[128] -[4]
    ("010000001", "000000100"),  -- 125 : +[128, 1] -[4]
    ("010000000", "000000010"),  -- 126 : +[128] -[2]
    ("010000000", "000000001"),  -- 127 : +[128] -[1]
    ("010000000", "000000000"),  -- 128 : +[128] -[]
    ("010000001", "000000000"),  -- 129 : +[1, 128] -[]
    ("010000010", "000000000"),  -- 130 : +[2, 128] -[]
    ("010000011", "000000000"),  -- 131 : +[1, 2, 128] -[]
    ("010000100", "000000000"),  -- 132 : +[4, 128] -[]
    ("010000101", "000000000"),  -- 133 : +[1, 4, 128] -[]
    ("010000110", "000000000"),  -- 134 : +[2, 4, 128] -[]
    ("010001000", "000000001"),  -- 135 : +[8, 128] -[1]
    ("010001000", "000000000"),  -- 136 : +[8, 128] -[]
    ("010001001", "000000000"),  -- 137 : +[1, 8, 128] -[]
    ("010001010", "000000000"),  -- 138 : +[2, 8, 128] -[]
    ("010001011", "000000000"),  -- 139 : +[1, 2, 8, 128] -[]
    ("010001100", "000000000"),  -- 140 : +[4, 8, 128] -[]
    ("010001101", "000000000"),  -- 141 : +[1, 4, 8, 128] -[]
    ("010010000", "000000010"),  -- 142 : +[16, 128] -[2]
    ("010010000", "000000001"),  -- 143 : +[16, 128] -[1]
    ("010010000", "000000000"),  -- 144 : +[16, 128] -[]
    ("010010001", "000000000"),  -- 145 : +[1, 16, 128] -[]
    ("010010010", "000000000"),  -- 146 : +[2, 16, 128] -[]
    ("010010011", "000000000"),  -- 147 : +[1, 2, 16, 128] -[]
    ("010010100", "000000000"),  -- 148 : +[4, 16, 128] -[]
    ("010010101", "000000000"),  -- 149 : +[1, 4, 16, 128] -[]
    ("010010110", "000000000"),  -- 150 : +[2, 4, 16, 128] -[]
    ("010011000", "000000001"),  -- 151 : +[8, 16, 128] -[1]
    ("010011000", "000000000"),  -- 152 : +[8, 16, 128] -[]
    ("010011001", "000000000"),  -- 153 : +[1, 8, 16, 128] -[]
    ("010011010", "000000000"),  -- 154 : +[2, 8, 16, 128] -[]
    ("010100000", "000000101"),  -- 155 : +[32, 128] -[4, 1]
    ("010100000", "000000100"),  -- 156 : +[32, 128] -[4]
    ("010100001", "000000100"),  -- 157 : +[32, 1, 128] -[4]
    ("010100000", "000000010"),  -- 158 : +[32, 128] -[2]
    ("010100000", "000000001"),  -- 159 : +[32, 128] -[1]
    ("010100000", "000000000"),  -- 160 : +[32, 128] -[]
    ("010100001", "000000000"),  -- 161 : +[1, 32, 128] -[]
    ("010100010", "000000000"),  -- 162 : +[2, 32, 128] -[]
    ("010100011", "000000000"),  -- 163 : +[1, 2, 32, 128] -[]
    ("010100100", "000000000"),  -- 164 : +[4, 32, 128] -[]
    ("010100101", "000000000"),  -- 165 : +[1, 4, 32, 128] -[]
    ("010100110", "000000000"),  -- 166 : +[2, 4, 32, 128] -[]
    ("010101000", "000000001"),  -- 167 : +[8, 32, 128] -[1]
    ("010101000", "000000000"),  -- 168 : +[8, 32, 128] -[]
    ("010101001", "000000000"),  -- 169 : +[1, 8, 32, 128] -[]
    ("010101010", "000000000"),  -- 170 : +[2, 8, 32, 128] -[]
    ("010101011", "000000000"),  -- 171 : +[1, 2, 8, 32, 128] -[]
    ("010101100", "000000000"),  -- 172 : +[4, 8, 32, 128] -[]
    ("010101101", "000000000"),  -- 173 : +[1, 4, 8, 32, 128] -[]
    ("010110000", "000000010"),  -- 174 : +[16, 32, 128] -[2]
    ("010110000", "000000001"),  -- 175 : +[16, 32, 128] -[1]
    ("010110000", "000000000"),  -- 176 : +[16, 32, 128] -[]
    ("010110001", "000000000"),  -- 177 : +[1, 16, 32, 128] -[]
    ("010110010", "000000000"),  -- 178 : +[2, 16, 32, 128] -[]
    ("010110011", "000000000"),  -- 179 : +[1, 2, 16, 32, 128] -[]
    ("010110100", "000000000"),  -- 180 : +[4, 16, 32, 128] -[]
    ("010110101", "000000000"),  -- 181 : +[1, 4, 16, 32, 128] -[]
    ("011000000", "000001010"),  -- 182 : +[64, 128] -[8, 2]
    ("011000000", "000001001"),  -- 183 : +[64, 128] -[8, 1]
    ("011000000", "000001000"),  -- 184 : +[64, 128] -[8]
    ("011000001", "000001000"),  -- 185 : +[64, 1, 128] -[8]
    ("011000010", "000001000"),  -- 186 : +[64, 2, 128] -[8]
    ("011000000", "000000101"),  -- 187 : +[64, 128] -[4, 1]
    ("011000000", "000000100"),  -- 188 : +[64, 128] -[4]
    ("011000001", "000000100"),  -- 189 : +[64, 1, 128] -[4]
    ("011000000", "000000010"),  -- 190 : +[64, 128] -[2]
    ("011000000", "000000001"),  -- 191 : +[64, 128] -[1]
    ("011000000", "000000000"),  -- 192 : +[64, 128] -[]
    ("011000001", "000000000"),  -- 193 : +[1, 64, 128] -[]
    ("011000010", "000000000"),  -- 194 : +[2, 64, 128] -[]
    ("011000011", "000000000"),  -- 195 : +[1, 2, 64, 128] -[]
    ("011000100", "000000000"),  -- 196 : +[4, 64, 128] -[]
    ("011000101", "000000000"),  -- 197 : +[1, 4, 64, 128] -[]
    ("011000110", "000000000"),  -- 198 : +[2, 4, 64, 128] -[]
    ("011001000", "000000001"),  -- 199 : +[8, 64, 128] -[1]
    ("011001000", "000000000"),  -- 200 : +[8, 64, 128] -[]
    ("011001001", "000000000"),  -- 201 : +[1, 8, 64, 128] -[]
    ("011001010", "000000000"),  -- 202 : +[2, 8, 64, 128] -[]
    ("011001011", "000000000"),  -- 203 : +[1, 2, 8, 64, 128] -[]
    ("011001100", "000000000"),  -- 204 : +[4, 8, 64, 128] -[]
    ("011001101", "000000000"),  -- 205 : +[1, 4, 8, 64, 128] -[]
    ("011010000", "000000010"),  -- 206 : +[16, 64, 128] -[2]
    ("011010000", "000000001"),  -- 207 : +[16, 64, 128] -[1]
    ("011010000", "000000000"),  -- 208 : +[16, 64, 128] -[]
    ("011010001", "000000000"),  -- 209 : +[1, 16, 64, 128] -[]
    ("011010010", "000000000"),  -- 210 : +[2, 16, 64, 128] -[]
    ("011010011", "000000000"),  -- 211 : +[1, 2, 16, 64, 128] -[]
    ("011010100", "000000000"),  -- 212 : +[4, 16, 64, 128] -[]
    ("011010101", "000000000"),  -- 213 : +[1, 4, 16, 64, 128] -[]
    ("100000000", "000101010"),  -- 214 : +[256] -[32, 8, 2]
    ("100000000", "000101001"),  -- 215 : +[256] -[32, 8, 1]
    ("100000000", "000101000"),  -- 216 : +[256] -[32, 8]
    ("100000001", "000101000"),  -- 217 : +[256, 1] -[32, 8]
    ("100000010", "000101000"),  -- 218 : +[256, 2] -[32, 8]
    ("100000000", "000100101"),  -- 219 : +[256] -[32, 4, 1]
    ("100000000", "000100100"),  -- 220 : +[256] -[32, 4]
    ("100000001", "000100100"),  -- 221 : +[256, 1] -[32, 4]
    ("100000000", "000100010"),  -- 222 : +[256] -[32, 2]
    ("100000000", "000100001"),  -- 223 : +[256] -[32, 1]
    ("100000000", "000100000"),  -- 224 : +[256] -[32]
    ("100000001", "000100000"),  -- 225 : +[256, 1] -[32]
    ("100000010", "000100000"),  -- 226 : +[256, 2] -[32]
    ("100000100", "000100001"),  -- 227 : +[256, 4] -[32, 1]
    ("100000100", "000100000"),  -- 228 : +[256, 4] -[32]
    ("100000101", "000100000"),  -- 229 : +[256, 1, 4] -[32]
    ("100001000", "000100010"),  -- 230 : +[256, 8] -[32, 2]
    ("100001000", "000100001"),  -- 231 : +[256, 8] -[32, 1]
    ("100001000", "000100000"),  -- 232 : +[256, 8] -[32]
    ("100001001", "000100000"),  -- 233 : +[256, 1, 8] -[32]
    ("100001010", "000100000"),  -- 234 : +[256, 2, 8] -[32]
    ("100000000", "000010101"),  -- 235 : +[256] -[16, 4, 1]
    ("100000000", "000010100"),  -- 236 : +[256] -[16, 4]
    ("100000001", "000010100"),  -- 237 : +[256, 1] -[16, 4]
    ("100000000", "000010010"),  -- 238 : +[256] -[16, 2]
    ("100000000", "000010001"),  -- 239 : +[256] -[16, 1]
    ("100000000", "000010000"),  -- 240 : +[256] -[16]
    ("100000001", "000010000"),  -- 241 : +[256, 1] -[16]
    ("100000010", "000010000"),  -- 242 : +[256, 2] -[16]
    ("100000100", "000010001"),  -- 243 : +[256, 4] -[16, 1]
    ("100000100", "000010000"),  -- 244 : +[256, 4] -[16]
    ("100000101", "000010000"),  -- 245 : +[256, 1, 4] -[16]
    ("100000000", "000001010"),  -- 246 : +[256] -[8, 2]
    ("100000000", "000001001"),  -- 247 : +[256] -[8, 1]
    ("100000000", "000001000"),  -- 248 : +[256] -[8]
    ("100000001", "000001000"),  -- 249 : +[256, 1] -[8]
    ("100000010", "000001000"),  -- 250 : +[256, 2] -[8]
    ("100000000", "000000101"),  -- 251 : +[256] -[4, 1]
    ("100000000", "000000100"),  -- 252 : +[256] -[4]
    ("100000001", "000000100"),  -- 253 : +[256, 1] -[4]
    ("100000000", "000000010"),  -- 254 : +[256] -[2]
    ("100000000", "000000001")   -- 255 : +[256] -[1]
  );

  type t_bit_width_mapping is array(natural range<>, natural range<>) of integer;
  type t_real_array is array(natural range<>) of real;
  type t_generic_filter_array is array(natural range<>, natural range<>, natural range<>) of integer;
  type t_unsigned_24_array is array(natural range<>) of unsigned(23 downto 0);


  function f_get_index_of_value_in_array(constant values : in t_integer_array; constant find_value : in integer; constant from_idx : in integer; constant to_idx : in integer) return integer;

  function f_get_largest_integer(constant factors : in t_integer_array; constant from_idx : in integer; constant to_idx : in integer) return integer;
  
  function f_get_smallest_integer(constant values : in t_integer_array; constant from_idx : in integer; constant to_idx : in integer) return integer;

  --! Looks up a weight value in the operator table
  function f_get_weight_shift_operators(constant weight_value : in integer) return t_operator_encoding;

  --! Factorizes a weight factor into an array of powers of two
  function f_get_weight_shift_factors(constant weight_value : in integer) return t_integer_array;

  --! Extracts the M0 value from the quantization factor M (compare: M = M0 * 2^(-n))
  function f_get_m_zero_from_quant_factor(constant quantization_factor : in real) return unsigned;

  --! Extracts the n value from the quantization factor M (compare: M = M0 * 2^(-n))
  function f_get_n_from_quant_factor(constant quantization_factor : in real) return integer;

  --! Performs a rounding right shift and returns the result with the shifted bits missing
  function f_rounding_right_shift(constant number : in signed; constant shift_bits : in natural) return signed;

  --! Performs a rounding right shift and returns the result in the same bit width as the input
  function f_rounding_right_shift_non_reducing(constant number : in signed; constant shift_bits : in natural) return signed;

  --! Runs f_get_m_zero_from_quant_factor on an array
  function f_get_mzero_array(constant quant_mults : in t_real_array) return t_unsigned_24_array;

  --! Runs f_get_n_from_quant_factor on an array
  function f_get_nshift_array(constant quant_mults : in t_real_array) return t_integer_array;

  --! Calculates the number of stages of a carry safe adder tree required to add 'elements' numbers
  --! Includes the final full adder required as the last stage 
  function f_get_carry_safe_adder_tree_stage_count(constant elements : in integer) return integer;

  --! Calculates the number of carry safe adder components required in stage number 'stage' 
  --! of a carry safe adder tree for a total of 'total_elements' of inputs
  function f_get_carry_safe_adder_tree_adder_count(constant total_elements : in integer; constant stage : in integer) return integer;

  --! Calculates the total number of numbers that are processed (not propagated) in stage 'stage' 
  --! of a carry safe adder tree for a total of 'total_elements' of inputs
  function f_get_carry_safe_adder_tree_element_count(constant total_elements : in integer; constant stage : in integer) return integer;

  --! Returns the total number of power of two factors of 'factor'
  function f_get_element_add_sub_count(constant factor : integer) return integer;

  --! Performs f_get_element_add_sub_count on a weight kernel returning an array with the factor counts
  function f_get_element_count_for_weights(constant weights: t_generic_filter) return t_integer_array;

  --! Totals the number of weight's power of two factors over a weight kernel
  function f_get_total_elements_for_weights(constant weights: t_generic_filter) return integer;

  --! Returns an array with the bit widths for the result of each power of two factor per weight
  function f_get_result_bit_widths_for_all_weights(constant weights : in t_generic_filter; constant value_data_width : in integer; constant max_summands : in integer) return t_integer_array;

  function f_get_result_bit_widths_for_all_weights_one_summand(constant weights : in t_generic_filter; constant value_data_width : in integer; constant weight_count : in integer) return t_integer_array;

  --! Returns a mapping array in ascending order for the input array
  --! The mapping array describes how the original array should be sorted:
  --! Each position of the mapping array holds the index of the original array which should be moved here.
  --! e.g.: array: (20, 42, 3, 16) results in the mapping array: (2, 3, 0, 1).
  --! The mapping array should be interpreted as 
  --! "To sort the original array, move index 2 to 0, index 3 to 1, index 0 to 2 and index 1 to 3"
  function f_get_sorting_mapping_for_array(constant bit_widths : in t_integer_array) return t_integer_array;

  --! Apply a sort mapping array (obtained from f_get_sorting_mapping_for_array)
  --! to the array 'values' and return the reordered array
  function f_get_sorted_list_by_mapping(constant values : in t_integer_array; constant mapping : in t_integer_array) return t_integer_array;
  
  --! Apply a sort mapping array (obtained from f_get_sorting_mapping_for_array)
  --! to the signal array 'values' and return the reordered array
  function f_get_sorted_signal_list_by_mapping(signal values : in t_integer_array; constant mapping : in t_integer_array) return t_integer_array;

  --! Generate a bit width matrix for a carry safe adder tree topology given an array of input bit widths
  --! The resulting matrix moves from stage 0 (data input, equal to input array 'bit_widths') by one stage per 
  --! matrix row. Each row will have less columns as the numbers are added up.
  --! It is assumed that each stage will add one bit to the data type - this could be further optimized.
  --! For example by keeping track of carry outputs of the csa's.
  function f_generate_csa_tree_input_bit_widths(constant bit_widths : in t_integer_array; constant stage_count : integer) return t_bit_width_mapping;

  --! Extract a single kernel from a t_generic_filter_array (array of kernels) by the kernel (filter) number
  function f_get_kernel_values_for_single_filter(constant kernel_values : in t_generic_filter_array; constant filter_number : in integer) return t_generic_filter;
  
  --! Apply f_get_total_elements_for_weights to an array of weight kernels
  function f_get_total_elements_for_weights_of_filters(constant filter_kernel_values : in t_generic_filter_array) return t_integer_array;
  
  --! Return an array with the number of weights per filter
  function f_get_total_elements_for_weights_of_filters_one_summand(constant filter_kernel_values : in t_generic_filter_array) return t_integer_array;

  --! Apply f_get_result_bit_widths_for_all_weights to an array of weight kernels
  function f_get_bit_widths_for_all_filters(constant filter_kernel_values : in t_generic_filter_array; constant value_data_width : in integer; constant max_summands : in integer) return t_generic_filter;

  function f_get_bit_widths_for_all_filters_one_summand(constant filter_kernel_values : in t_generic_filter_array; constant value_data_width : in integer; constant max_summands : in integer) return t_generic_filter;
  
  --! Apply f_get_sorting_mapping_for_array to an array of weight kernels
  function f_get_sort_mappings_for_all_filters(constant bit_widths : in t_generic_filter) return t_generic_filter;

  --! Apply f_get_sorted_list_by_mapping to an array of arrays
  function f_apply_sort_mapping_to_arrays(constant input_arrays : in t_generic_filter; constant sort_mappings : in t_generic_filter) return t_generic_filter;

end package as_cnn_helpers;

--! @}

package body as_cnn_helpers is

  function f_get_mzero_array(constant quant_mults : in t_real_array) return t_unsigned_24_array is
    variable mzeros : t_unsigned_24_array(quant_mults'range);
  begin
    for N in quant_mults'range loop
      mzeros(N) := f_get_m_zero_from_quant_factor(quant_mults(N));
    end loop;
    return mzeros;
  end function;

  function f_get_nshift_array(constant quant_mults : in t_real_array) return t_integer_array is
    variable nshifts : t_integer_array(quant_mults'range);
  begin
    for N in quant_mults'range loop
      nshifts(N) := f_get_n_from_quant_factor(quant_mults(N));
    end loop;
    return nshifts;
  end function;

  function f_apply_sort_mapping_to_arrays(constant input_arrays : in t_generic_filter; constant sort_mappings : in t_generic_filter) return t_generic_filter is
    variable output_arrays : t_generic_filter(input_arrays'range(1), input_arrays'range(2));
    variable single_line : t_integer_array(input_arrays'range(2));
    variable single_mapping : t_integer_array(sort_mappings'range(2));
    variable sorted_line : t_integer_array(input_arrays'range(2));
  begin
    for N in input_arrays'range(1) loop
      for I in input_arrays'range(2) loop
        single_line(I) := input_arrays(N, I);
      end loop;
      for I in sort_mappings'range(2) loop
        single_mapping(I) := sort_mappings(N, I);
      end loop;
      sorted_line := f_get_sorted_list_by_mapping(single_line, single_mapping);
      for I in input_arrays'range(2) loop
        output_arrays(N, I) := sorted_line(I);
      end loop;
    end loop;
    return output_arrays;
  end function;

  function f_get_sort_mappings_for_all_filters(constant bit_widths : in t_generic_filter) return t_generic_filter is
    variable mappings : t_generic_filter(bit_widths'range(1), bit_widths'range(2));
    variable bit_widths_for_single_filter : t_integer_array(bit_widths'range(2));
    variable sort_mapping_for_single_filter : t_integer_array(bit_widths'range(2));
  begin
    for F in bit_widths'range(1) loop
      for N in bit_widths'range(2) loop
        bit_widths_for_single_filter(N) := bit_widths(F, N);
      end loop;
      sort_mapping_for_single_filter := f_get_sorting_mapping_for_array(bit_widths_for_single_filter);
      for N in bit_widths'range(2) loop
        mappings(F, N) := sort_mapping_for_single_filter(N);
      end loop;
    end loop;

    return mappings;
  end function;

  function f_get_bit_widths_for_all_filters(constant filter_kernel_values : in t_generic_filter_array; constant value_data_width : in integer; constant max_summands : in integer) return t_generic_filter is
    variable bit_widths_out : t_generic_filter(filter_kernel_values'range(1), 0 to max_summands - 1);
    variable single_filter_values : t_generic_filter(filter_kernel_values'range(2), filter_kernel_values'range(3));
    variable bit_widths_for_single_filter : t_integer_array(0 to max_summands - 1);
  begin

    for F in filter_kernel_values'range(1) loop
      single_filter_values := f_get_kernel_values_for_single_filter(filter_kernel_values, F);
      bit_widths_for_single_filter := f_get_result_bit_widths_for_all_weights(single_filter_values, value_data_width, max_summands);

      for N in 0 to max_summands - 1 loop
        bit_widths_out(F, N) := bit_widths_for_single_filter(N);
      end loop;
    end loop;

    return bit_widths_out;
  end function;

  function f_get_bit_widths_for_all_filters_one_summand(constant filter_kernel_values : in t_generic_filter_array; constant value_data_width : in integer; constant max_summands : in integer) return t_generic_filter is
    variable bit_widths_out : t_generic_filter(filter_kernel_values'range(1), 0 to max_summands - 1);
    variable single_filter_values : t_generic_filter(filter_kernel_values'range(2), filter_kernel_values'range(3));
    variable bit_widths_for_single_filter : t_integer_array(0 to max_summands - 1);
  begin

    for F in filter_kernel_values'range(1) loop
      single_filter_values := f_get_kernel_values_for_single_filter(filter_kernel_values, F);
      bit_widths_for_single_filter := f_get_result_bit_widths_for_all_weights_one_summand(single_filter_values, value_data_width, max_summands);

      for N in 0 to max_summands - 1 loop
        bit_widths_out(F, N) := bit_widths_for_single_filter(N);
      end loop;
    end loop;

    return bit_widths_out;
  end function;

  function f_get_total_elements_for_weights_of_filters(constant filter_kernel_values : in t_generic_filter_array) return t_integer_array is
    variable element_counts_out : t_integer_array(filter_kernel_values'range(1));
  begin
    for F in filter_kernel_values'range(1) loop
      element_counts_out(F) := f_get_total_elements_for_weights(f_get_kernel_values_for_single_filter(filter_kernel_values, F));
    end loop;
    return element_counts_out;
  end function;

  function f_get_total_elements_for_weights_of_filters_one_summand(constant filter_kernel_values : in t_generic_filter_array) return t_integer_array is
    variable element_counts_out : t_integer_array(filter_kernel_values'range(1));
    constant weights_per_filter : integer := filter_kernel_values'length(2) * filter_kernel_values'length(3);
  begin
    for F in filter_kernel_values'range(1) loop
      element_counts_out(F) := weights_per_filter;
    end loop;
    return element_counts_out;
  end function;

  function f_get_kernel_values_for_single_filter(constant kernel_values : in t_generic_filter_array; constant filter_number : in integer) return t_generic_filter is
    variable filter_out : t_generic_filter(kernel_values'range(2), kernel_values'range(3));
  begin
    assert filter_number < kernel_values'length(1) report "Filter number passed to 'f_get_kernel_values_for_single_filter' is out of bounds!" severity failure;
    for C in kernel_values'range(2) loop
      for N in kernel_values'range(3) loop
        filter_out(C, N) := kernel_values(filter_number, C, N);
      end loop;
    end loop;
    return filter_out;
  end function;

  function f_generate_csa_tree_input_bit_widths(constant bit_widths : in t_integer_array; constant stage_count : integer) return t_bit_width_mapping is
    constant total_elements : integer := bit_widths'length;
    variable bit_mapping : t_bit_width_mapping(0 to stage_count, 0 to total_elements - 1) := (others => (others => 0));
    variable elements_this_stage : integer;
    variable elements_propagate : integer;
    variable adders_this_stage : integer;
    variable current_elements : t_integer_array(0 to 2);
    variable largest_bit_width : integer;
  begin
    -- First stage: data inputs
    for N in bit_widths'range loop
      bit_mapping(0, N) := bit_widths(N);
    end loop;
    if total_elements < 2 then
      return bit_mapping;
    end if;
    -- Compute control values for first stage
    elements_this_stage := total_elements;
    elements_propagate := elements_this_stage mod 3;
    adders_this_stage := elements_this_stage / 3;

    -- Stages 1 to S - 1:
    for S in 1 to stage_count - 1 loop
      -- For every Carry Safe Adder:
      for N in 0 to adders_this_stage - 1 loop
        -- Get input bit widths  
        current_elements := (
          0 => bit_mapping(S - 1, N * 3 + 0),
          1 => bit_mapping(S - 1, N * 3 + 1),
          2 => bit_mapping(S - 1, N * 3 + 2)
        );
        -- Get largest input bit width
        largest_bit_width := f_get_largest_integer(current_elements, 0, 2);
        -- Sum output will have same output bit width (input of next stage)
        bit_mapping(S, N * 2 + 0) := largest_bit_width;
        -- Carry output will have largest input + 1 bit width
        bit_mapping(S, N * 2 + 1) := largest_bit_width + 1;
      end loop;
      -- For element propagations:
      for N in 0 to elements_propagate - 1 loop
        -- Carry bit width to next stage
        bit_mapping(S, adders_this_stage * 2 + N) := bit_mapping(S - 1, adders_this_stage * 3 + N);
      end loop;
      -- Update values for next stage
      elements_propagate := elements_this_stage mod 3;
      adders_this_stage := elements_this_stage / 3;
      elements_this_stage := (adders_this_stage * 2) + elements_propagate;
    end loop;

    
    -- Last stage (Carry ripple adder):
    current_elements := (
      0 => bit_mapping(stage_count - 1, 0),
      1 => bit_mapping(stage_count - 1, 1),
      2 => 0
    );
    largest_bit_width := f_get_largest_integer(current_elements, 0, 1);
    bit_mapping(stage_count, 0) := largest_bit_width + 1;
    return bit_mapping;
  end function;

  function f_get_index_of_value_in_array(constant values : in t_integer_array; constant find_value : in integer; constant from_idx : in integer; constant to_idx : in integer) return integer is
  begin
    for N in from_idx to to_idx loop
      if find_value = values(N) then
        return N;
      end if;
    end loop;
    return -1;
  end function;

  function f_get_sorting_mapping_for_array(constant bit_widths : in t_integer_array) return t_integer_array is
    constant total_values : integer := bit_widths'length;
    constant handled_value : integer := f_get_largest_integer(bit_widths, 0, total_values - 1) + 1;

    variable working_list : t_integer_array(bit_widths'range) := bit_widths;
    variable index_mapping : t_integer_array(bit_widths'range);

    variable comp : integer := f_get_smallest_integer(bit_widths, 0, total_values - 1);
    variable idx : integer;
    variable sorted_values_count : integer := 0;
  begin
    -- While not every value in the working list was handled
    while comp < handled_value loop
      -- Get the index of the first occurance of the current smallest value in the working list
      idx := f_get_index_of_value_in_array(working_list, comp, 0, total_values - 1);
      -- While there are occurrances of the current comparison value in the working list
      while idx > -1 loop
        -- Map the value at idx to the sorted list and increment the sorted count
        index_mapping(sorted_values_count) := idx;
        sorted_values_count := sorted_values_count + 1;
        -- Update the value at the index of the working list with the handled "tag"/value
        working_list(idx) := handled_value;
        -- Get the index of the next occurrance
        idx := f_get_index_of_value_in_array(working_list, comp, idx, total_values - 1);
      end loop;
      -- When all occurrances are handled, use the next smallest value in the working list as the comparison value
      comp := f_get_smallest_integer(working_list, 0, total_values - 1);
    end loop;
    return index_mapping;
  end function;

  function f_get_sorted_list_by_mapping(constant values : in t_integer_array; constant mapping : in t_integer_array) return t_integer_array is
    variable sorted_list : t_integer_array(values'range);
  begin
    for N in values'range loop
      sorted_list(N) := values(mapping(N));
    end loop;
    return sorted_list;
  end function;

  function f_get_sorted_signal_list_by_mapping(signal values : in t_integer_array; constant mapping : in t_integer_array) return t_integer_array is
    variable sorted_list : t_integer_array(values'range);
  begin
    
    for N in values'range loop
      sorted_list(N) := values(mapping(N));
    end loop;
    return sorted_list;
  end function;

  function f_get_smallest_integer(constant values : in t_integer_array; constant from_idx : in integer; constant to_idx : in integer) return integer is
    variable smallest : integer := values(from_idx);
  begin
    for N in from_idx + 1 to to_idx loop
      if smallest > values(N) then
        smallest := values(N);
      end if;
    end loop;
    return smallest;
  end function;

  function f_get_largest_integer(constant factors : in t_integer_array; constant from_idx : in integer; constant to_idx : in integer) return integer is
    variable largest : integer := factors(from_idx);
  begin
    for N in from_idx + 1 to to_idx loop
      if largest < factors(N) then
        largest := factors(N);
      end if;
    end loop;
    return largest;
  end function;

  function f_get_carry_safe_adder_tree_stage_count(constant elements : in integer) return integer is
    variable stages : integer := 1;
    variable count : integer := elements;
  begin
    if count < 2 then
      return 0;
    end if;
    while count > 2 loop
      count := (2 * (count / 3)) + (count rem 3);
      stages := stages + 1;
    end loop;
    return stages;
  end function;

  function f_get_carry_safe_adder_tree_adder_count(constant total_elements : in integer; constant stage : in integer) return integer is
    variable count : integer := total_elements;
  begin
    if count < 2 then
      return 0;
    end if;

    for N in 0 to stage - 2 loop
      count := (2 * (count / 3)) + (count mod 3);
    end loop;
    return count / 3;
  end function;

  function f_get_carry_safe_adder_tree_element_count(constant total_elements : in integer; constant stage : in integer) return integer is
    variable count : integer := total_elements;
  begin
    for N in 0 to stage - 2 loop
      count := (2 * (count / 3)) + (count rem 3);
    end loop;
    return count;
  end function;

  function f_get_weight_shift_operators(constant weight_value : in integer) return t_operator_encoding is
    variable weight : integer;
    variable operator_out : t_operator_encoding;
    variable temp_operator : std_logic_vector(8 downto 0);
  begin
    weight := abs(weight_value);
    operator_out := c_weight_operator_table(weight);

    -- For negative weights the positive and negative operators of the operator table
    -- can be simply swapped to receive the corresponding inverted factor
    if weight_value < 0 then
      operator_out := (0 => operator_out(1), 1 => operator_out(0));
    end if;
    return operator_out;
  end function;

  function f_get_element_add_sub_count(constant factor : integer) return integer is
    variable bit_akk : integer := 0;
    constant operators : t_operator_encoding := f_get_weight_shift_operators(factor);
    constant p_op : std_logic_vector := operators(0);
    constant n_op : std_logic_vector := operators(1);
  begin
    for B in p_op'range loop
      if p_op(B) = '1' then
        bit_akk := bit_akk + 1;
      end if;
      if n_op(B) = '1' then
        bit_akk := bit_akk + 1;
      end if;
    end loop;
    return bit_akk;
  end function;

  function f_get_element_count_for_weights(constant weights: t_generic_filter) return t_integer_array is
    constant weight_count : integer := f_get_filter_elements_count(weights);
    variable array_out : t_integer_array(0 to weight_count - 1);
  begin
    for Y in weights'range(1) loop
      for X in weights'range(2) loop
        array_out(Y * weights'length(2) + X) := f_get_element_add_sub_count(weights(Y, X));
      end loop;
    end loop;
    return array_out;
  end function;

  function f_get_total_elements_for_weights(constant weights: t_generic_filter) return integer is
    variable element_count : integer := 0;
  begin
    for Y in weights'range(1) loop
      for X in weights'range(2) loop
        element_count := element_count + f_get_element_add_sub_count(weights(Y, X));
      end loop;
    end loop;
    return element_count;
  end function;

  function f_get_weight_shift_factors(constant weight_value : in integer) return t_integer_array is
    constant c_factor_count : integer := f_get_element_add_sub_count(weight_value);
    constant operators : t_operator_encoding := f_get_weight_shift_operators(weight_value);
    constant p_op : std_logic_vector := operators(0);
    constant n_op : std_logic_vector := operators(1);
    
    variable factors : t_integer_array(0 to c_factor_count - 1) := (others => 0);
    variable count : integer := 0;
    variable bit_count : integer := 0;
  begin
    for N in 0 to p_op'length - 1 loop
      if p_op(N) = '1' then
        factors(count) := 2 ** bit_count;
        count := count + 1;
      end if;
      if n_op(N) = '1' then
        factors(count) := (2 ** bit_count) * (-1);
        count := count + 1;
      end if;
      if count = c_factor_count then
        return factors;
      end if;
      bit_count := bit_count + 1;
    end loop;
    return factors;
  end function;

  function f_get_result_bit_widths_for_all_weights_one_summand(constant weights : in t_generic_filter; constant value_data_width : in integer; constant weight_count : in integer) return t_integer_array is
    variable bit_widths : t_integer_array(0 to weight_count - 1) := (others => 0);
    variable weight : integer;
  begin
    for Y in weights'range(1) loop
      for X in weights'range(2) loop
        weight := weights(Y, X);
        if weight /= 0 then
          bit_widths(Y * weights'length(2) + X) := log2_ceil_zero(abs(weight)) + value_data_width;
        else
          bit_widths(Y * weights'length(2) + X) := 1;
        end if;
        --report "W: " & integer'image(weight) & " | BW: " & integer'image(bit_widths(Y * weights'length(2) + X));
      end loop;
    end loop;
    return bit_widths;
  end function;

  function f_get_result_bit_widths_for_all_weights(constant weights : in t_generic_filter; constant value_data_width : in integer; constant max_summands : in integer) return t_integer_array is

    variable operators : t_operator_encoding;
    variable p_op : std_logic_vector(8 downto 0);
    variable n_op : std_logic_vector(8 downto 0);
    
    variable index : integer := 0;
    variable bit_count : integer := 0;
    
    variable bit_widths : t_integer_array(0 to max_summands - 1) := (others => 0);
  begin
    for Y in weights'range(1) loop
      for X in weights'range(2) loop
        bit_count := 0;
        operators := f_get_weight_shift_operators(weights(Y, X));
        p_op := operators(0);
        n_op := operators(1);
        for N in 0 to p_op'length - 1 loop
          if p_op(N) = '1' then
            bit_widths(index) := bit_count + value_data_width;
            index := index + 1;
          end if;
          if n_op(N) = '1' then
            bit_widths(index) := bit_count + value_data_width + 1;
            index := index + 1;
          end if;
          bit_count := bit_count + 1;
        end loop;
      end loop;
    end loop;
    if index < max_summands - 1 then
      bit_widths(index to max_summands - 1) := (others => 0);
    end if;
    return bit_widths;
  end function;

  function f_rounding_right_shift(constant number : in signed; constant shift_bits : in natural) return signed is
    constant result_bit_width : integer := number'length - shift_bits;
    constant shift_factor : integer := 2 ** shift_bits;
    constant half_shift_value : integer := shift_factor - (shift_factor / 2);
    variable result : signed(result_bit_width - 1 downto 0);
    variable is_negative : std_logic;
    variable comp_val : integer;
  begin
    is_negative := number(number'length - 1);

    -- "Regular" shift; Cut of shift_bits number of bits
    result := to_signed(to_integer(number) / shift_factor, result_bit_width);
    
    if is_negative = '1' then
      comp_val := abs(to_integer(not unsigned(number(shift_bits downto 0))));
    else
      comp_val := abs(to_integer(number(shift_bits downto 0)) mod shift_factor);
    end if;
    
    -- Decide wether to round up or not
    if comp_val >= half_shift_value then
      if is_negative = '1' then
        return result - 1;
      else
        return result + 1;
      end if;
    else
      return result;
    end if;
  end function;

  -- Same as f_rounding_right_shift but does not reduce the bitwidth of the returned value
  function f_rounding_right_shift_non_reducing(constant number : in signed; constant shift_bits : in natural) return signed is
    variable result : signed(number'range);
    variable is_negative : std_logic;
    variable temp : integer;
  begin
    if shift_bits > 0 then
      result := shift_right(number, shift_bits);
      is_negative := number(number'length - 1);
      if is_negative = '1' and number(shift_bits - 1) = '0' then
        return result - 1;
      elsif number(shift_bits - 1) = '1' then
        return result + 1;
      else 
        return result;
      end if;
    else
      return number;
    end if;
  end function;

  function f_get_m_zero_from_quant_factor(constant quantization_factor : in real) return unsigned is
    variable m_zero : real := quantization_factor;
    variable m_zero_int : unsigned(23 downto 0);
  begin
    while m_zero < 0.5 loop
      m_zero := m_zero * 2.0;
    end loop;
    m_zero := m_zero * real(2**23);
    m_zero_int := to_unsigned(integer(m_zero), 24);
    return m_zero_int;
  end function;

  function f_get_n_from_quant_factor(constant quantization_factor : in real) return integer is
    variable m_zero : real := quantization_factor;
    variable n : integer := 0;
  begin
    while m_zero < 0.5 loop
      m_zero := m_zero * 2.0;
      n := n + 1;
    end loop;
    return n;
  end function;

end as_cnn_helpers;
