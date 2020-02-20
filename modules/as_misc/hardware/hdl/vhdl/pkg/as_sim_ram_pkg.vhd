----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_sim_ram_pkg
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Alexander Zoellner
--
-- Modified:       
--
-- Description:    Package for providing functions, procedures and constants 
--                 for simulating memory. 
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
--! @file  as_sim_ram_pkg.vhd
--! @brief Package for providing functions, procedures and constants 
--         for simulating memory.
----------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

library std;
use std.textio.all;

package as_sim_ram_pkg is

    constant c_memory_bit_width     : integer := 8; -- Data width of a single entry (e.g. pixel data of 8 bit)
    constant c_mem_depth            : integer := 64*1024*1024; -- Number of entries, where each entry has c_memory_bit_width
    
    -- Return values 
    constant c_file_done            : integer := -2;
    constant c_ext_func_fail        : integer := -1;
    
    function write_byte (addr : integer; data : integer) return integer;
    attribute foreign of write_byte : function is "VHPIDIRECT write_byte";
    
    function read_byte (addr : integer) return integer;
    attribute foreign of read_byte : function is "VHPIDIRECT read_byte";

    

    type sim_ram is protected
    
        procedure p_init_mem ( 
            variable success : out std_logic);
        
        procedure p_write_data (
            variable address      : in integer;
            variable data         : in std_logic_vector(c_memory_bit_width-1 downto 0);
            success      : out std_logic);
        
        procedure p_read_data (
            variable address      : in integer;
            variable data         : out std_logic_vector(c_memory_bit_width-1 downto 0);
            success      : out std_logic);
        
        procedure p_write_to_disk (
            constant file_name : in string;
            signal addr : in integer;
            signal amount : in integer);

        procedure p_read_from_disk(
            constant file_name : in string;
            signal addr : in integer;
            signal amount : in integer);
            
    end protected sim_ram;
    
end package as_sim_ram_pkg;


package body as_sim_ram_pkg is

    function write_byte (addr : integer; data : integer) return integer is
    begin
        return c_ext_func_fail;
    end write_byte;
        
    function read_byte (addr : integer) return integer is
    begin
        return c_ext_func_fail;
    end read_byte;

    type sim_ram is protected body
        type mem is array (0 to c_mem_depth-1) of std_logic_vector(c_memory_bit_width-1 downto 0);
        type string_pointer is access string;
        variable v_memory   : mem;
        
        -- Init memory block with 0
        procedure p_init_mem ( 
            variable success : out std_logic
        ) is
        begin
            v_memory := (others => (others => '0'));
        end p_init_mem;
        
        -- Read data from memory block
        procedure p_read_data (
            variable address      : in integer;
            variable data         : out std_logic_vector(c_memory_bit_width-1 downto 0);
            success               : out std_logic
        ) is
        begin
            if address < c_mem_depth or address > c_mem_depth then
                data := v_memory(address);
                success := '1';
            else
                data := (others=>'0');
                success := '0';
            end if;
        end p_read_data;
        
        -- Write data to memory block
        procedure p_write_data (
            variable address      : in integer;
            variable data         : in std_logic_vector(c_memory_bit_width-1 downto 0);
            success      : out std_logic
        ) is
        begin
            if address < 0 or address > (c_mem_depth-1) then
                success := '0';
            else
                v_memory(address) := data;
                success := '1';
            end if;
        end p_write_data;
        
        -- Read data from hard drive; amount of 0 results in reading the whole file
        procedure p_read_from_disk (
            constant file_name : in string;
            signal addr : in integer;
            signal amount : in integer
        ) is 
            file     temp_file : text;
            file     read_file : text;
            variable v_temp_line : line;
            variable v_return_val : integer;
            variable v_hex_val : integer;
            variable v_mem_index : integer;
            variable v_read_return : boolean;
        begin
            -- Write target file name in temp file to be accessible by C-function
            file_open(temp_file, "temp.file", WRITE_MODE);
            write(v_temp_line, file_name);
            writeline(temp_file, v_temp_line); -- write line in buffer to file
            file_close(temp_file);
            
            -- Try to read binary file with external C-function
            if amount = 0 then -- Read in the whole file if specified data amount is zero
                v_mem_index := addr;
                Read_File_loop : while(true) loop
                    v_return_val := read_byte(v_mem_index);
                    exit Read_File_loop when v_return_val = c_file_done or v_return_val = c_ext_func_fail;
                    v_memory(v_mem_index) := std_logic_vector(to_unsigned(v_return_val, c_memory_bit_width));
                    v_mem_index := v_mem_index + 1;
                end loop Read_File_loop;
            else
                Read_Loop : for i in 0 to amount-1 loop
                    v_return_val := read_byte(i);
                    exit Read_Loop when  v_return_val = c_file_done or v_return_val = c_ext_func_fail;
                    v_memory(addr+i) := std_logic_vector(to_unsigned(v_return_val, c_memory_bit_width));
                end loop Read_Loop;
            end if;
            
            -- Read .pgm file-format if external C-function fails or does not exist
            if v_return_val = c_ext_func_fail then
                file_open(read_file, file_name, READ_MODE);
                readline(read_file, v_temp_line); -- skip compression info
                readline(read_file, v_temp_line); -- skip image resolution info
                readline(read_file, v_temp_line); -- skip gray val range info
                readline(read_file, v_temp_line);
                v_mem_index := 0;
                if amount = 0 then -- Read in the whole file if specified data amount is zero
                    while not endfile(read_file) loop
                        if v_temp_line'length < 1 then
                        readline(read_file, v_temp_line);
                        end if;
                        read(v_temp_line, v_hex_val, v_read_return);
                        if v_read_return = true then
                            v_memory(addr+v_mem_index) := std_logic_vector(to_unsigned(v_hex_val, c_memory_bit_width));
                            v_mem_index := v_mem_index + 1;
                        end if;
                    end loop;
                else
                    while (amount) > v_mem_index loop
                        if v_temp_line'length < 1 then
                            readline(read_file, v_temp_line);
                        end if;
                        read(v_temp_line, v_hex_val, v_read_return);
                        if v_read_return = true then
                            v_memory(addr+v_mem_index) := std_logic_vector(to_unsigned(v_hex_val, c_memory_bit_width));
                            v_mem_index := v_mem_index + 1;
                        end if;
                    end loop;
                end if;
                file_close(read_file);
            end if;
        end p_read_from_disk;
        
        -- Write data to hard drive
        procedure p_write_to_disk (
            constant file_name : in string;
            signal addr : in integer;
            signal amount : in integer
        ) is
            file     temp_file : text;
            file     write_file : text;
            variable v_temp_line : line;
            variable v_return_val : integer;
            variable v_hex_val : integer;
            variable v_tmp_string : string_pointer;
        begin
            -- Write target file name in temp file to be accessible by C-function
            file_open(temp_file, "temp.file", WRITE_MODE);
            write(v_temp_line, file_name);
            writeline(temp_file, v_temp_line); -- write line in buffer to file
            file_close(temp_file);
            
            -- Try to write data to binary file with external C-function
            Write_Loop : for i in 0 to amount-1 loop
                v_return_val := write_byte(i, to_integer(unsigned(v_memory(addr+i))));
                exit Write_Loop when v_return_val = c_ext_func_fail;
            end loop;
            
            -- Write .pgm file-format if external C-function fails or does not exist
            if v_return_val = c_ext_func_fail then
                file_open(write_file, file_name, WRITE_MODE);
                write(v_temp_line, (string'("P2")));
                writeline(write_file, v_temp_line);
                write(v_temp_line, amount);
                write(v_temp_line, (string'(" 1")));
                writeline(write_file, v_temp_line);
                write(v_temp_line, (string'("255")));
                writeline(write_file, v_temp_line);
                for i in 0 to amount - 1 loop
                    v_hex_val := to_integer(unsigned(v_memory(addr+i)));
                    write(v_temp_line, v_hex_val);
                    write(v_temp_line, ' ');
                end loop;
                writeline(write_file, v_temp_line);
                file_close(write_file);
            end if;
        end p_write_to_disk;  
        
    end protected body sim_ram;
end as_sim_ram_pkg;
