----------------------------------------------------------------------------------
-- This file is part of V.E.A.R.S.
--
-- V.E.A.R.S. is free software: you can redistribute it and/or modify
-- it under the terms of the GNU Lesser General Public License as published by
-- the Free Software Foundation, either version 3 of the License, or
-- (at your option) any later version.
--
-- V.E.A.R.S. is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
-- GNU Lesser General Public License for more details.
--
-- You should have received a copy of the GNU Lesser General Public License
-- along with V.E.A.R.S. If not, see <http://www.gnu.org/licenses/lgpl.txt>.
--
-- Copyright (C) 2010-2019 Matthias Pohl and
--                         Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- File:           vears_mc.vhd
-- Entity:         vears_mc
--
-- Project Name:   VEARS
--  \\        // ////////     //\\     //////\\    ///////         ////\\\\
--   \\      //  //          //  \\    //    //   /              //  ///   \\
--    \\    //   /////      //    \\   ///////    \\\\\\        ||  |      ||
--     \\  //    //        /////\\\\\  //   \\         /         \\  \\\   //
--      \\//     //////// //        \\ //    \\ ///////            \\\\////
--
-- Company:        University of Applied Sciences, Augsburg, Germany
--
-- Author:         Matthias Pohl
-- Create Date:    12/10/2009
--
-- Version:  1.0
-- Modified:       * 16/11/2013 by Michael Schaeferling
--                   - major cleanup, was 'fears_mc'
--                 * 05/04/2019 by Michael Schaeferling
--                   - Code cleanup (better readability due to naming conventions (prefixes, ...)
--                 * 12/09/2019 by Michael Schaeferling
--
-- Description:    Control memory data access to fetch image and overlay data.
----------------------------------------------------------------------------------


library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use IEEE.STD_LOGIC_UNSIGNED.ALL;


entity vears_mc is
  generic(
    DATA_WIDTH : positive;
    PIXELS : integer;
    BYTES_PER_PIXEL : integer;
    LINES  : integer;
    ADDR_WIDTH_PIC_LINEBUFFER : integer;
    ADDR_WIDTH_OVL_LINEBUFFER : integer
  );
  port (
    clk   : in std_logic;
    reset : in std_logic;

    run           : in  std_logic;
    reset_soft    : in  std_logic;
    ovl_en        : in  std_logic;
    
    base_addr_pic : in  std_logic_vector(31 downto 0);
    base_addr_ovl : in  std_logic_vector(31 downto 0);
    
    ---------Communication with linebuffer---------------------
    trigger_line       : in  std_logic;
    trigger_frame      : in  std_logic;
    
    pic_linebuff_write : out std_logic;
    ovl_linebuff_write : out std_logic;
    
    pic_linebuff_addr  : out std_logic_vector(ADDR_WIDTH_PIC_LINEBUFFER-1 downto 0);  --address output for linebuffer
    ovl_linebuff_addr  : out std_logic_vector(ADDR_WIDTH_OVL_LINEBUFFER-1 downto 0);  --address output for overlay-linebuffer
    
    linebuff_data      : out std_logic_vector(31 downto 0);  --common data output for linebuffers
    ---------Communication-with-linebuffer---------------------
    
    ---------PLB-MASTER-Signals--------------------------------
    mem_in_en       : in  std_logic;
    mem_in_data     : in  std_logic_vector(DATA_WIDTH-1 downto 0);
    
    mem_out_en      : in  std_logic;
    mem_out_data    : out std_logic_vector(DATA_WIDTH-1 downto 0);
    
    mem_go          : out std_logic;
    mem_clr_go      : in  std_logic;
    mem_busy        : in  std_logic;
    mem_done        : in  std_logic;
    mem_error       : in  std_logic;
    mem_timeout     : in  std_logic;
    
    mem_rd_req      : out std_logic;
    mem_wr_req      : out std_logic;
    mem_bus_lock    : out std_logic;
    mem_burst       : out std_logic;
    mem_addr        : out std_logic_vector(31 downto 0);
    mem_be          : out std_logic_vector(15 downto 0);
    mem_xfer_length : out std_logic_vector(11 downto 0)
    ---------PLB-MASTER-Signals--------------------------------
  );
end vears_mc;


architecture Behavioral of vears_mc is

signal r_pic_linebuff_write : std_logic;
signal r_ovl_linebuff_write : std_logic;
signal r_inc_pic_linebuff_addr : std_logic;
signal r_inc_ovl_linebuff_addr : std_logic;
signal r_linebuff_data : std_logic_vector(31 downto 0);


type state_t is (
    IDLE,
    MEM_WAIT_1,
    INIT_BURST_OVL,
    GET_DATA_OVL,
    MEM_WAIT_2,
    INIT_BURST_PIC_1,
    GET_DATA_PIC_1,
    INIT_BURST_PIC_2,
    GET_DATA_PIC_2,
    ERROR_MEM
);
signal r_current_state : state_t;


signal r_pic_linebuff_addr : std_logic_vector(ADDR_WIDTH_PIC_LINEBUFFER-1 downto 0);
signal r_ovl_linebuff_addr : std_logic_vector(ADDR_WIDTH_OVL_LINEBUFFER-1 downto 0);
signal r_buffer_select : std_logic;

signal r_inc_pic_ram_addr : std_logic;
signal r_inc_ovl_ram_addr : std_logic;
signal r_pic_ram_addr : std_logic_vector(31 downto 0);
signal r_ovl_ram_addr : std_logic_vector(31 downto 0);

signal r_burst_ovl : std_logic;
signal r_run_last : std_logic;


signal c_pic_2_bursts : boolean;
signal c_pic_burst_size : integer;

--~ attribute mark_debug : string;
--~ attribute mark_debug of current_state : signal is "true";
--~ attribute mark_debug of base_addr_pic : signal is "true";
--~ attribute mark_debug of base_addr_ovl : signal is "true";



begin


pic_linebuff_write <= r_pic_linebuff_write;
ovl_linebuff_write <= r_ovl_linebuff_write;
pic_linebuff_addr <= r_pic_linebuff_addr;
ovl_linebuff_addr <= r_ovl_linebuff_addr;
linebuff_data <= r_linebuff_data;

mem_out_data <= (others => '0');




LINEBUFFER_ADDR_COUNTER : process (clk)
begin
    if (clk'event and clk = '1') then  
    
        if ( reset = '1') then
            r_buffer_select <= '0';
            
            -- reset linebuffer addresses
            r_pic_linebuff_addr <= (others => '0');
            r_ovl_linebuff_addr <= (others => '0');
            
            r_pic_ram_addr <= base_addr_pic; -- caution! may be 0x0 after reset as sw-registers are not written at this point
            r_ovl_ram_addr <= base_addr_ovl; -- caution! may be 0x0 after reset as sw-registers are not written at this point
        
        else
            -- Linebuffer address calculation
            if (r_inc_pic_linebuff_addr = '1') then -- address-increment during picture burst-transfer            
                r_pic_linebuff_addr <= r_pic_linebuff_addr + 1;
            end if;
            
            if (r_inc_ovl_linebuff_addr = '1') then --address-increment during overlay burst-transfer
                r_ovl_linebuff_addr  <= r_ovl_linebuff_addr + 1;
            end if;
            
            -- RAM address calculation (move on 1 line):
            -- overlay: 4 overlay pixels in 8 bit
            if (r_inc_ovl_ram_addr = '1') then
                r_ovl_ram_addr <= r_ovl_ram_addr + (PIXELS/4);
            end if;
            
            -- image: 1 (color) or 4 (grayscale) image pixels in 32 bit
            if(r_inc_pic_ram_addr = '1') then
                r_pic_ram_addr <= r_pic_ram_addr + PIXELS * BYTES_PER_PIXEL;
            end if;
            
            -- on frame or line change, reset address counters:
            
            r_run_last <= run;
            -- reset to baseaddress on new frame or when run was set:
            if ((trigger_frame = '1') or ((run = '1') and (r_run_last='0'))) then
                r_pic_ram_addr <= base_addr_pic;
                r_ovl_ram_addr <= base_addr_ovl;
                
                r_buffer_select <= '0';
            end if;
            
            if (trigger_line = '1') then
                r_pic_linebuff_addr <= (others => '0');
                r_pic_linebuff_addr(ADDR_WIDTH_PIC_LINEBUFFER-1) <= r_buffer_select;
                
                r_ovl_linebuff_addr <= (others => '0');
                r_ovl_linebuff_addr(ADDR_WIDTH_OVL_LINEBUFFER-1) <= r_buffer_select;
                
                r_buffer_select <= not(r_buffer_select);
            end if;
            
        end if;
    end if;
end process;




is1burst: if PIXELS*BYTES_PER_PIXEL < 4096 generate
 c_pic_burst_size <= PIXELS*BYTES_PER_PIXEL;
 c_pic_2_bursts <= false;
end generate;



is2bursts: if PIXELS*BYTES_PER_PIXEL >= 4096 generate
 c_pic_burst_size <= PIXELS*BYTES_PER_PIXEL/2;
 c_pic_2_bursts <= true;
end generate;



STATE_MACHINE : process (clk)
begin
    if (clk'event and clk = '1') then
        if (reset = '1') then
            mem_go <= '0';
            mem_rd_req <= '0';
            mem_wr_req <= '0'; 
            mem_bus_lock <= '0';
            mem_burst <= '0';
            mem_be <= x"FFFF";
            
            r_pic_linebuff_write <= '0';
            r_ovl_linebuff_write <= '0';
            
            r_inc_pic_linebuff_addr <= '0';
            r_inc_ovl_linebuff_addr <= '0';
            r_inc_pic_ram_addr <= '0';
            r_inc_ovl_ram_addr <= '0';
            
            r_burst_ovl <= '0';
            
            r_current_state <= IDLE;

        else
        
            --Set default values
            mem_rd_req <= '0';
            mem_wr_req <= '0'; 
            mem_bus_lock <= '0';
            mem_burst <= '0';
            mem_xfer_length <= (others => '0');
            mem_be <= x"FFFF";
            
            -- mem_go reset
            if (mem_clr_go = '1') then  
                mem_go <= '0';
            end if;
            
            -------------------
            r_pic_linebuff_write <= '0';
            r_ovl_linebuff_write <= '0';
            
            r_inc_pic_linebuff_addr <= '0';
            r_inc_ovl_linebuff_addr <= '0';
            r_inc_pic_ram_addr <= '0';
            r_inc_ovl_ram_addr <= '0';
            
            r_burst_ovl <= '0';
            
            ------------Receive Data---------------------
            if (mem_in_en = '1') then
            
                if (r_burst_ovl = '0') then -- data to picture linebuffer
                    r_pic_linebuff_write <= '1';
                    r_inc_pic_linebuff_addr <= '1'; -- increment address for next pixel (delayed by 1 clock in process ADDR_COUNTER)
                    
                    -- The memory module performs a 32bit (int32) access for the data (although it's basically 8bit grayscale data), 
                    -- which results on little endian (AXI) systems in undesired byte swapping. 
                    -- The re-ordering is done here:
                    r_linebuff_data(31 downto 24) <= mem_in_data( 7 downto  0);
                    r_linebuff_data(23 downto 16) <= mem_in_data(15 downto  8);
                    r_linebuff_data(15 downto  8) <= mem_in_data(23 downto 16);
                    r_linebuff_data( 7 downto  0) <= mem_in_data(31 downto 24);
                    
                else --data to overlay linebuffer
                    r_ovl_linebuff_write <= '1';
                    r_inc_ovl_linebuff_addr <= '1'; -- increment address for next pixel (delayed by 1 clock in process ADDR_COUNTER)
                    
                    r_linebuff_data <= mem_in_data;
                    
                end if;
            end if;
           
           
            case r_current_state is 

                when IDLE =>                    -- fetch new pair of overlay and image data if the memcontroller is triggered to do so
                                                if( (run = '1') and (trigger_line = '1') ) then
                                                    r_current_state <= MEM_WAIT_1;
                                                end if;
                                                
                when MEM_WAIT_1 =>              -- first make sure the memory interface is ready for new transactions
                                                if(mem_busy = '0') then
                                                    if (ovl_en = '1') then
                                                        r_current_state <= INIT_BURST_OVL;
                                                    else
                                                        r_current_state <= INIT_BURST_PIC_1;
                                                    end if;
                                                end if;

                -- fetch overlay data:
                when INIT_BURST_OVL =>          -- initialize burst transaction for one overlay line
                                                mem_go <= '1';
                                                mem_rd_req <= '1';
                                                mem_burst <= '1';
                                                mem_addr <= r_ovl_ram_addr;
                                                mem_xfer_length <= std_logic_vector( to_unsigned( (PIXELS/4), 12) ); -- one full overlay line, 2 bit per pixel
                                                --mem_bus_lock <= '1';
                                                r_burst_ovl <= '1';
                                                r_current_state <= GET_DATA_OVL;

                when GET_DATA_OVL =>            
                                                mem_rd_req <= '1';
                                                mem_burst <= '1';
                                                mem_addr <= r_ovl_ram_addr;
                                                mem_xfer_length <= std_logic_vector( to_unsigned( (PIXELS/4), 12) ); -- one full overlay line, 2 bit per pixel
                                                --mem_bus_lock <= '1';
                                                r_burst_ovl <= '1';
                                                
                                                if ((mem_error = '1') or (mem_timeout = '1')) then
                                                    r_current_state <= ERROR_MEM;
                                                
                                                elsif (mem_done = '1') then
                                                    r_current_state <= MEM_WAIT_2;
                                                
                                                end if;

                when MEM_WAIT_2 =>              
                                                if(mem_busy = '0') then
                                                    r_current_state <= INIT_BURST_PIC_1;
                                                end if;






                when INIT_BURST_PIC_1 =>          
                                                mem_go <= '1';
                                                mem_rd_req <= '1';
                                                mem_burst <= '1';
                                                mem_addr <= r_pic_ram_addr;
                                                mem_xfer_length <= std_logic_vector( to_unsigned( c_pic_burst_size, 12) ); -- one full line per burst
                                                mem_bus_lock <= '1';
                                                r_current_state <= GET_DATA_PIC_1;

                when GET_DATA_PIC_1 =>            
                                                mem_rd_req <= '1';
                                                mem_burst <= '1';
                                                mem_addr <= r_pic_ram_addr;
                                                mem_xfer_length <= std_logic_vector( to_unsigned( c_pic_burst_size, 12) ); -- one full line per burst
                                                mem_bus_lock <= '1';
                                                
                                                if ((mem_error = '1') or (mem_timeout = '1')) then
                                                    r_current_state <= ERROR_MEM;
                                                elsif (mem_done = '1') then
                                                    if (c_pic_2_bursts = true) then
                                                      r_current_state <= INIT_BURST_PIC_2;
                                                    else
                                                      r_inc_ovl_ram_addr <= '1';
                                                      r_inc_pic_ram_addr <= '1';
                                                      r_current_state <= IDLE;
                                                    end if;
                                                end if;

                when INIT_BURST_PIC_2 =>          
                                                mem_go <= '1';
                                                mem_rd_req <= '1';
                                                mem_burst <= '1';
                                                mem_addr <= r_pic_ram_addr + c_pic_burst_size;
                                                mem_xfer_length <= std_logic_vector(to_unsigned( c_pic_burst_size, 12) ); -- one full line per burst
                                                mem_bus_lock <= '1';
                                                r_current_state <= GET_DATA_PIC_2;

                when GET_DATA_PIC_2 =>            
                                                mem_rd_req <= '1';
                                                mem_burst <= '1';
                                                mem_addr <= r_pic_ram_addr + c_pic_burst_size;
                                                mem_xfer_length <= std_logic_vector( to_unsigned( c_pic_burst_size, 12 ) ); -- one full line per burst
                                                mem_bus_lock <= '1';
                                                
                                                if ((mem_error = '1') or (mem_timeout = '1')) then
                                                    r_current_state <= ERROR_MEM;
                                                elsif (mem_done = '1') then
                                                    r_inc_ovl_ram_addr <= '1';
                                                    r_inc_pic_ram_addr <= '1';
                                                    r_current_state <= IDLE;
                                                end if;

              
              



                when ERROR_MEM  =>              r_current_state <= IDLE;
                                                --null;

                when others =>                  --null;
            end case;
        end if;
    end if;
end process;


end Behavioral;
