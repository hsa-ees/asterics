----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  Copyright (C) Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
--
-- Entity:         fifo_fwft
--
-- Company:        Efficient Embedded Systems Group
--                 University of Applied Sciences, Augsburg, Germany
--
-- Authors:        Michael Schaeferling, Markus Bihler
--
-- Description:    First Word Fall Through FIFO:
--                 If data is written into the empty fifo, it is presented
--                 on the output ports one clock cycle later.
--                 The read_in port confirms the data at the output ports. The 
--                 FIFO will present the next data package, if available.
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
--! @file  fifo_fwft.vhd
--! @brief First Word Fall Through FIFO.
----------------------------------------------------------------------------------


library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;


use work.helpers.all;


entity fifo_fwft is
generic (
    DATA_WIDTH : integer := 8;
    BUFF_DEPTH : integer := 256;
    PROG_EMPTY_ENABLE : boolean := true;
    PROG_FULL_ENABLE : boolean := true
);
port (
    clk         : in  std_logic;
    reset       : in  std_logic;

    din         : in  std_logic_vector(DATA_WIDTH-1 downto 0);
    wr_en       : in  std_logic;
    rd_en       : in  std_logic;
    dout        : out std_logic_vector(DATA_WIDTH-1 downto 0);
    
    level       : out std_logic_vector(log2_ceil(BUFF_DEPTH) downto 0);
    full        : out std_logic;
    empty       : out std_logic;
    
    prog_full_thresh  : in std_logic_vector(log2_ceil(BUFF_DEPTH)-1 downto 0);
    prog_full         : out std_logic;
    
    prog_empty_thresh : in std_logic_vector(log2_ceil(BUFF_DEPTH)-1 downto 0);
    prog_empty        : out std_logic
);
end fifo_fwft;


architecture RTL of fifo_fwft is

  
    component ram is
    generic ( 
          DATA_WIDTH : integer;
          ADDR_WIDTH : integer
         );
    port (
          clk       : in  std_logic;
          wr_en     : in  std_logic;
          wr_addr   : in  std_logic_vector(ADDR_WIDTH-1 downto 0);
          rd_addr   : in  std_logic_vector(ADDR_WIDTH-1 downto 0);
          din       : in  std_logic_vector(DATA_WIDTH-1 downto 0);
          dout      : out std_logic_vector(DATA_WIDTH-1 downto 0)
         ); 
    end component;


    signal s_rd_addr, r_rd_addr, s_rd_addr_plus1, r_wr_addr: unsigned(log2_ceil(BUFF_DEPTH)-1 downto 0);
    signal s_wr_en, s_rd_en : std_logic;
    signal r_level : unsigned(log2_ceil(BUFF_DEPTH) downto 0); -- use leftmost bit as full signal
    signal s_full, s_empty : std_logic;

    signal ram_din, ram_dout : std_logic_vector(DATA_WIDTH-1 downto 0);

    signal dout_passthru_en : std_logic;
    signal dout_passthru : std_logic_vector(DATA_WIDTH-1 downto 0);
    signal ram_dout_stored_en : std_logic;
    signal ram_dout_stored : std_logic_vector(DATA_WIDTH-1 downto 0);


begin

    -- sanity check for generic "BUFF_DEPTH":
    assert BUFF_DEPTH = 2**log2_ceil(BUFF_DEPTH)
    report "Generic BUFF_DEPTH must be a 2**n value"
    severity failure;
  
    -- RAM for storage
    RAM0 : ram
    generic map(
        DATA_WIDTH => DATA_WIDTH,
        ADDR_WIDTH => log2_ceil(BUFF_DEPTH)
    )
    port map(
        clk     => clk,
        wr_en   => s_wr_en,
        wr_addr => std_logic_vector(r_wr_addr),
        rd_addr => std_logic_vector(s_rd_addr),
        din     => ram_din,
        dout    => ram_dout
    );
    -- 
    ram_din <= din;

    level <= std_logic_vector(r_level);

    s_full <= r_level(r_level'left);
    full <= s_full;

    s_empty <= '1' when r_level = 0 else '0';
    empty <= s_empty;

    prog_full  <= '1' when (PROG_FULL_ENABLE = true) and (r_level >= unsigned(prog_full_thresh)) else '0';
    prog_empty <= '1' when (PROG_EMPTY_ENABLE = true) and (r_level <= unsigned(prog_empty_thresh)) else '0';

    s_wr_en <= '1' when ( wr_en='1' and s_full = '0' ) else '0'; -- discard write signal when fifo is full
    s_rd_en <= '1' when ( rd_en='1' and s_empty = '0' ) else '0'; -- discard read signal when fifo is empty

    s_rd_addr_plus1 <= r_rd_addr+1;
    s_rd_addr <= r_rd_addr when s_rd_en='0' else s_rd_addr_plus1;
    dout <= ram_dout when (dout_passthru_en = '0') else dout_passthru;

  
    process(clk)
    begin
        if ( clk'event and clk='1' ) then
            if reset = '1' then
                dout_passthru_en <= '0';
                ram_dout_stored_en <= '0';
                r_level   <= (others => '0');
                r_rd_addr <= (others => '0');--to_unsigned(1, r_rd_addr'length);
                r_wr_addr <= (others => '0');
            else

                -- write  
                if ( s_wr_en='1' ) then
                    r_wr_addr <= r_wr_addr + 1;
                -- on empty fifo write, pass data input directly to output (fwft behavioral):
                    if (s_empty = '1') then
                        dout_passthru_en <= '1';
                        dout_passthru <= din;
                    end if;
                end if;

                -- read
                if ( s_rd_en='1' ) then
                    r_rd_addr <= r_rd_addr + 1;
                    ram_dout_stored <= ram_dout;
                    if (dout_passthru_en = '1') then
                      dout_passthru_en <= '0';
                    end if;
                end if;

                if    ( s_wr_en='1' and s_rd_en='0') then
                    r_level <= r_level+1;
                elsif ( s_wr_en='0' and s_rd_en='1') then
                    r_level <= r_level-1;
                end if;
            end if;
        end if;
    end process;


end RTL;

