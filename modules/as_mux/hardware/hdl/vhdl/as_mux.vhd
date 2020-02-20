----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  Copyright (C) Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_mux
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Michael Schaeferling
--
-- Modified:       2019-02-21 Philip Manke: Remove ResX&ResY, add hcomplete signal
--                 2019-07-23 Philip Manke: Rename signals and ports
--
-- Description:    Multiplexes between two input ports.
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
--! @file  as_mux.vhd
--! @brief Multiplexes between two input ports.
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity as_mux is
generic (
    DATA_WIDTH  : integer := 32
);
port (
    clk             : in  std_logic;

    -- IN ports A ( 0 )
    vcomplete_0_in  : in std_logic;
    hcomplete_0_in  : in std_logic;
    vsync_0_in      : in  std_logic;
    hsync_0_in      : in  std_logic;
    strobe_0_in     : in  std_logic;
    data_0_in       : in  std_logic_vector(DATA_WIDTH-1 downto 0);
    
    data_error_0_in : in  std_logic;
    stall_0_out     : out std_logic;
    
    -- IN ports B ( 1 )
    vcomplete_1_in  : in std_logic;
    hcomplete_1_in  : in std_logic;
    vsync_1_in      : in  std_logic;
    hsync_1_in      : in  std_logic;
    strobe_1_in     : in  std_logic;
    data_1_in       : in  std_logic_vector(DATA_WIDTH-1 downto 0);
    
    data_error_1_in : in  std_logic;
    stall_1_out     : out std_logic;
    
    -- OUT ports
    vcomplete_out   : out std_logic;
    hcomplete_out   : out std_logic;
    vsync_out       : out std_logic;
    hsync_out       : out std_logic;
    strobe_out      : out std_logic;
    data_out        : out std_logic_vector(DATA_WIDTH-1 downto 0);
    
    data_error_out  : out std_logic;
    stall_in        : in  std_logic;

    sel_reg         : in  std_logic
  );
end as_mux;


architecture RTL of as_mux is

begin

    vcomplete_out   <= vcomplete_0_in   when sel_reg = '0' else vcomplete_1_in;
    hcomplete_out   <= hcomplete_0_in   when sel_reg = '0' else hcomplete_1_in;
    vsync_out       <= vsync_0_in       when sel_reg = '0' else vsync_1_in;
    hsync_out       <= hsync_0_in       when sel_reg = '0' else hsync_1_in;

    strobe_out      <= strobe_0_in      when sel_reg = '0' else strobe_1_in;
    data_out        <= data_0_in        when sel_reg = '0' else data_1_in;
    
    data_error_out <= data_error_0_in   when sel_reg = '0' else data_error_1_in;
    stall_0_out     <= stall_in         when sel_reg = '0' else '0';
    stall_1_out     <= stall_in         when sel_reg = '1' else '0';

end RTL;
