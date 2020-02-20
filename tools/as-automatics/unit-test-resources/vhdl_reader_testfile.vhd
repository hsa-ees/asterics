----------------------------------------------------------------------
-- This file is part of the ASTERICS Framework.
-- Copyright (C) Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------
-- File:     vhdl_reader_testfile.vhd
--
-- Company:  Efficient Embedded Systems Group
--           University of Applied Sciences, Augsburg, Germany
--           http://ees.hs-augsburg.de
--
-- Author:   Philip Manke - <philip.manke@hs-augsburg.de>
-- Date:     
-- Modified: 
--
-- Description:
-- This is a testfile for the ASTERICS chain generator, Automatics.
-- It is used to evaluate the built-in parser for VHDL code.
--
----------------------------------------------------------------------
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
----------------------------------------------------------------------



entity as_filter_permissive is
    generic   ( 
        MAX_REGS_PER_MODULE         : data_type := genericvalue;
        IMAGENERIC :                                    string := "andthisismyvalue";
        ANOTHERONE : expression := 4 ** 3 - 1;
        LASTONE     : intrusionattempt := eval("__import__('os').listdir('/etc/')")
    );
    port (
        clk         : in  std_logic;
        reset       : inout  std_logic;
        ready       : out std_logic;
                        mem_out_data       : out std_logic_vector(MEMORY_DATA_WIDTH - 1 downto 0);
        wideport : out bitvector(2 * 16 * 32 - 1 downto 0);
        invwideport : in vector(0 to 24 * 11 - 9 + MAX_REGS_PER_MODULE);
        expdatatest : out anothervector(2**16 - 1 downto 0)
    );
end as_filter_permissive;



architecture RTL of as_filter_permissive is
  
component this_components_name is
      generic(
              AGENERICNAME : integer := 21;
              ANOTHERONE : string := "nothingspecial"
              );
      port(
              clk:in std_logic;
              portname    :  out std_logic_vector(31 downto 0)
              );
end component;

  
    -- Slave register configuration:
    constant wonderful_constant_name : slv_reg_config_table(0 to MAX_REGS_PER_MODULE - 1) :=
                            
                            
                            
                            
                            ("11"
                            ,"10"
                            ,"10"
                            ,"10"
                            ,"10","10","01","01", -- Register 0  to 7
  
                    "01","02","10","03","10","04","20","50", -- Register 8  to 15
                             "02","10","00","30","60","02",
  
                             "01","02", -- Register 16 to 23
  
                        "11"
                        ,"01"
                        ,"10"
                        ,
                        "01",
                        
                        
                        -- The VHDLReader shouldn't have any problems 
                        -- with this scattered constant definition
                        
                        
                        
                        "30","02","04","05", -- Register 24 to 31
                             
                             
                             "01","30","55","20","04","01","10","02", -- Register 32 to 39
                             
               "42","55","21","22","11","23","44","01", -- Register 40 to 47
                             "11","20","30","01","01","02","03","10", -- Register 48 to 55
                   "24","86","88","10","22","24","10","42"
                             
                             -- This gap is to test whether the semicolon detection works properly :)
       -- Scattering some comments in here to fill the void
                             
                             );-- Register 56 to 63
constant thisisaconstant : integer := 24;
    
begin

 -- No need for anything in here
    
end architecture;

