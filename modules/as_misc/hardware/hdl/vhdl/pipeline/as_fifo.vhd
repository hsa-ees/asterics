----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
--
-- Entity:         as_fifo
--
-- Company:        Efficient Embedded Systems Group
--                 University of Applied Sciences, Augsburg, Germany
--
-- Authors:        Philip Manke
--
-- Description:    Simple First In First Out buffer.
--                 Depends on as_misc/.../ram/ram.vhd
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
--! @file  as_fifo.vhd
--! @brief Simple First In First Out buffer.
----------------------------------------------------------------------------------


library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library asterics;
use asterics.helpers.all;
use asterics.DUAL_BRAM_READ_FIRST;

--use work.helpers.all;



entity as_fifo is
generic (
    DATA_WIDTH : integer := 8;
    FIFO_DEPTH : integer := 256;
    AUTO_READ_ON_FULL : boolean := true
);
port (
    clk         : in  std_logic;
    reset       : in  std_logic;

    write_en    : in  std_logic;
    read_en     : in  std_logic;

    data_in     : in  std_logic_vector(DATA_WIDTH - 1 downto 0);
    data_out    : out std_logic_vector(DATA_WIDTH - 1 downto 0);
    
    full        : out std_logic;
    empty       : out std_logic
);
end as_fifo;


architecture RTL of as_fifo is

    --component ram is
    --generic ( 
    --      DATA_WIDTH : integer;
    --      ADDR_WIDTH : integer
    --     );
    --port (
    --      clk       : in  std_logic;
    --      wr_en     : in  std_logic;
    --      wr_addr   : in  std_logic_vector(ADDR_WIDTH-1 downto 0);
    --      rd_addr   : in  std_logic_vector(ADDR_WIDTH-1 downto 0);
    --      din       : in  std_logic_vector(DATA_WIDTH-1 downto 0);
    --      dout      : out std_logic_vector(DATA_WIDTH-1 downto 0)
    --     ); 
    --end component;
    --component DUAL_BRAM_READ_FIRST is
    --    generic ( gen_data_width : integer := 8;   -- width of each ram cell
    --            gen_data_depth : integer := 1024; -- number of ram cells
    --            gen_ram_style  : string  := "block" -- distributed | block
    --           );
    --    port (CLK_A         : in std_logic;
    --        CLK_B       : in std_logic;
    --        EN_A          : in std_logic;
    --        EN_B      : in std_logic;
    --        WE_A      : in std_logic;
    --        WE_B      : in std_logic;
    --        ADDR_A    : in std_logic_vector(log2_ceil(gen_data_depth)-1 downto 0);
    --        ADDR_B    : in std_logic_vector(log2_ceil(gen_data_depth)-1 downto 0);
    --        DI_A      : in std_logic_vector(gen_data_width-1 downto 0);
    --        DI_B      : in std_logic_vector(gen_data_width-1 downto 0);
    --        DO_A      : out std_logic_vector(gen_data_width-1 downto 0);
    --        DO_B      : out std_logic_vector(gen_data_width-1 downto 0)
    --       );   
    --end component;

    constant c_fifo_addr_width : integer := log2_ceil(FIFO_DEPTH);

    signal s_full, s_empty : std_logic;
    signal bram_write_en : std_logic;
    signal bram_read_addr, bram_write_addr : unsigned(c_fifo_addr_width - 1 downto 0) := (others => '0');
    signal s_data_out : std_logic_vector(DATA_WIDTH - 1 downto 0);

    signal s_int_read_en, auto_read_en : std_logic;

    -- FIFO is filling / emptying
    signal filling, emptying : std_logic;
begin

    -- sanity check for generic "FIFO_DEPTH":
    assert FIFO_DEPTH = 2**log2_ceil(FIFO_DEPTH)
    report "Generic FIFO_DEPTH must be a 2**n value"
    severity failure;
  
    ---- RAM for storage
    --FIFO_RAM : ram
    --generic map(
    --    DATA_WIDTH => DATA_WIDTH,
    --    ADDR_WIDTH => c_fifo_addr_width
    --)
    --port map(
    --    clk     => clk,
    --    wr_en   => bram_write_en,
    --    wr_addr => std_logic_vector(bram_write_addr),
    --    rd_addr => std_logic_vector(bram_read_addr),
    --    din     => data_in,
    --    dout    => s_data_out
    --); 

    FIFO_RAM : entity DUAL_BRAM_READ_FIRST 
        generic map( gen_data_width => DATA_WIDTH,
                gen_data_depth => FIFO_DEPTH,
                gen_ram_style  => "block"
               )
        port map (
            CLK_A   => clk,
            CLK_B   => clk,
            EN_A    => s_int_read_en,
            EN_B    => '1',
            WE_A    => '0',
            WE_B    => bram_write_en,
            ADDR_A  => std_logic_vector(bram_read_addr),
            ADDR_B  => std_logic_vector(bram_write_addr),
            DI_A    => (others => '0'),
            DI_B    => data_in,
            DO_A    => s_data_out,
            DO_B    => open
           );   
    
    -- Write process
    p_write : process(clk) is
    begin
        if rising_edge(clk) then
            -- FIFO starts empty
            if reset = '1' then
                bram_write_addr <= (others => '0');
                filling <= '0';
            else
                filling <= '0';
                -- Advance on valid write
                if write_en = '1' 
                        and (s_full = '0' or s_int_read_en = '1') then
                    bram_write_addr <= bram_write_addr + 1;
                end if;
                --if AUTO_READ_ON_FULL = true and (bram_write_addr + 1 = bram_read_addr or s_full = '1') and write_en = '1' then
                --    auto_read_en <= '1';
                --else
                --    auto_read_en <= '0';
                --end if;
                -- Filling if already full or writing while not reading
                if s_full = '1' or (write_en = '1' 
                                    and s_int_read_en = '0') then
                    filling <= '1';
                end if;
            end if;
        end if;
    end process;

    -- Read process
    p_read : process(clk) is
    begin
        if rising_edge(clk) then
            if reset = '1' then
                -- FIFO starts empty after reset
                bram_read_addr <= (others => '0');
                emptying <= '1';
                data_out <= (others => '0');
            else
                emptying <= '0';
                -- Advance on valid read
                if s_int_read_en = '1' and s_empty = '0' then
                    bram_read_addr <= bram_read_addr + 1;
                end if;
                -- Emptying if not writing and reading or already empty
                if s_empty = '1' or (s_int_read_en = '1'
                                     and write_en = '0') then
                    emptying <= '1';
                end if;
                if s_int_read_en = '1' then
                    data_out <= s_data_out;
                end if;
            end if;
        end if;
    end process;

    s_int_read_en <= auto_read_en or read_en;

    auto_read_en <= '0' when reset = '1' 
            else '1' when (AUTO_READ_ON_FULL = true 
                           and (bram_write_addr + 1 = bram_read_addr)
                           and write_en = '1')
            else '0';

    -- Always output data (except on reset high)
    
    --data_out <= (others => '0') when reset = '1' or s_int_read_en = '0'
    --            else s_data_out;
    -- Fast pass for write enable signal
    -- Write unless FIFO buffer is full
    bram_write_en <= '0' when reset = '1'
                    else '1' when write_en = '1' 
                                  and (s_full = '0' 
                                       or s_int_read_en = '1')
                    else '0';

    -- Empty if the read and write addresses collide while emptying
    s_empty <= '1' when bram_write_addr = bram_read_addr and emptying = '1' else '0';
    -- Full if the read and write addresses collide while filling
    s_full <= '1' when bram_write_addr = bram_read_addr and filling = '1' else '0';

    full <= s_full or auto_read_en;
    empty <= s_empty;

end RTL;

