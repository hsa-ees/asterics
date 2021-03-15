----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_carry_safe_operator
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Philip Manke
--
-- Modified:       
--
-- Description:    This component implements a carry save adder for 3 1 bit numbers
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
--! @file  as_carry_safe_operator.vhd
--! @brief 1 bit carry safe adder
----------------------------------------------------------------------------------

--! @addtogroup as_cnn_serial_convolution_filter_internal
--! @{

library ieee;
use ieee.std_logic_1164.all;

entity as_carry_safe_operator is
    port (
        a : in std_logic;
        b : in std_logic;
        c : in std_logic;
        s : out std_logic;
        cs : out std_logic
    );
end as_carry_safe_operator;

--! @}

architecture RTL of as_carry_safe_operator is
begin

    s <= (a xor b) xor c;
    cs <= ((a xor b) and c) or (a and b);
    
end RTL;
    