----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_carry_safe_adder
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Philip Manke
--
-- Modified:       
--
-- Description:    This component implements a carry save adder for 3 N bit numbers
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
--! @file  as_carry_safe_adder.vhd
--! @brief N bit carry safe adder
----------------------------------------------------------------------------------


--! @addtogroup as_cnn_serial_convolution_filter_internal
--! @{

library ieee;
use ieee.std_logic_1164.all;

library asterics;
use asterics.as_carry_safe_operator;

entity as_carry_safe_adder is
    generic (
        --! Adder bit width.
        DATA_WIDTH : integer := 8
    );
    port (
        --! Number \c a.
        a : in std_logic_vector(DATA_WIDTH - 1 downto 0);
        --! Number \c b.
        b : in std_logic_vector(DATA_WIDTH - 1 downto 0);
        --! Number \c c.
        c : in std_logic_vector(DATA_WIDTH - 1 downto 0);

        --! Sum word.
        s : out std_logic_vector(DATA_WIDTH - 1 downto 0);
        --! Carry word.
        cs : out std_logic_vector(DATA_WIDTH downto 0)
    );
end as_carry_safe_adder;

--! @}

architecture RTL of as_carry_safe_adder is
begin

    cs(0) <= '0';
    gen_adder : for N in 0 to DATA_WIDTH - 1 generate
        bit_adder_N : entity as_carry_safe_operator
        port map(
            a => a(N),
            b => b(N),
            c => c(N),
            s => s(N),
            cs => cs(N + 1)
        );
    end generate;

end RTL;
    