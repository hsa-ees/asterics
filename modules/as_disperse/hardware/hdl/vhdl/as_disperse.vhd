----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  Copyright (C) Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_disperse
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Michael Schaeferling
--
-- Modified:       
--
-- Description:    This module disperses DIN_WIDTH/DOUT_WIDTH data words to put image data and 
--                 corresponding VSYNC and HSYNC signals into one new data word.
--                 Thus, the new data words contain image data values of 4 pixels.
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
--! @file  as_disperse.vhd
--! @brief Converts a given input data length (2^x) into n data words with a smaller
--         data length (2^y; with x>y).
----------------------------------------------------------------------------------


library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use work.helpers.all;


entity as_disperse is
  generic (
    DIN_WIDTH  : integer := 32;
    DOUT_WIDTH : integer := 8
  );
  port (
    Clk         : in  std_logic;
    Reset       : in  std_logic;

    -- IN ports from previous module:
    vcomplete_in   : in std_logic;
    vsync_in    : in  std_logic;
    hsync_in    : in  std_logic;
    strobe_in   : in  std_logic;
    data_in     : in  std_logic_vector(DIN_WIDTH-1 downto 0);

    data_error_in  : in  std_logic;
    stall_out       : out std_logic;

    -- OUT ports to next module:
    vcomplete_out   : out std_logic;
    vsync_out   : out std_logic;
    hsync_out   : out std_logic;
    strobe_out  : out std_logic;
    data_out    : out std_logic_vector(DOUT_WIDTH-1 downto 0);
    
    sync_error_out  : out std_logic;
    data_error_out : out std_logic;
    stall_in        : in  std_logic
  );
end as_disperse;


architecture RTL of as_disperse is

  constant disperse_count   : natural := DIN_WIDTH/DOUT_WIDTH;
  constant reg_bit_width    : natural := data_in'length + 5;

  component fifo_fwft is
  generic (
    DATA_WIDTH : integer := 16;
    BUFF_DEPTH : integer := 8;
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
  end component;

  signal shift_reg : std_logic_vector(reg_bit_width-1 downto 0);

  signal strobe_counter : unsigned(log2_ceil(disperse_count) downto 0);

  signal stall_enable : std_logic;
  signal s_stall_out : std_logic;

  constant FIFO_BUFF_DEPTH : integer := 4;
  signal fifo_empty    : std_logic;
  signal s_fifo_prog_full     : std_logic;
  signal fifo_read_en  : std_logic;
  signal s_fifo_wr_en : std_logic;
  signal s_fifo_full : std_logic;

  signal s_sync_error : std_logic;
  
  signal as_fifo_in_data : std_logic_vector(reg_bit_width-1 downto 0);

  signal as_fifo_out_data : std_logic_vector(reg_bit_width-1 downto 0);

  type state_t is (s_idle, s_read);

  signal current_state, next_state : state_t;


begin
    
  -- Directly map input to output if the same bit width for both is used
  gen_no_disperse : if disperse_count = 1 generate
        
    vcomplete_out           <= vcomplete_in;
    vsync_out               <= vsync_in;
    hsync_out               <= hsync_in;
    strobe_out              <= strobe_in;
    data_out                <= data_in;
    
    sync_error_out          <= '0';
    data_error_out          <= data_error_in;
    stall_out               <= stall_in;
        
  end generate; -- gen_no_disperse
    
    
  -- Disperse input data to match the bit width of the output
  gen_disperse : if disperse_count /= 1 generate
    
    -- Instanciate a First Word Fall Through FIFO for buffering data
    as_fifo_in_data <= data_error_in & strobe_in & hsync_in & vsync_in & vcomplete_in & data_in; 
    
    s_fifo_wr_en <= strobe_in or vsync_in or hsync_in or vcomplete_in;

    as_fifo_fwft_0 : fifo_fwft
    generic map (
      DATA_WIDTH => reg_bit_width,
      BUFF_DEPTH => FIFO_BUFF_DEPTH,
      PROG_EMPTY_ENABLE => true,
      PROG_FULL_ENABLE => true
    )
    port map (
      clk => clk,
      reset => reset,
      
      din => as_fifo_in_data,
      wr_en => s_fifo_wr_en,
      rd_en => fifo_read_en,
      dout => as_fifo_out_data,
      
      level => open,
      full => s_fifo_full,
      empty => fifo_empty,
      
      prog_full_thresh => std_logic_vector(to_unsigned(1,log2_ceil(FIFO_BUFF_DEPTH))),
      prog_full => s_fifo_prog_full,
      
      prog_empty_thresh => std_logic_vector(to_unsigned(0,log2_ceil(FIFO_BUFF_DEPTH))),
      prog_empty => open
    );
        
    p_sync_error : process(clk)
    begin
      if rising_edge(clk) then
        if reset = '1' then
          s_sync_error <= '0';
        else
          if strobe_in = '1' and s_fifo_full = '1' then
            s_sync_error <= '1';
          end if;
        end if;
      end if;
    end process;

    sync_error_out  <= s_sync_error;

    stall_out       <= s_fifo_prog_full or stall_in;

        -- Control fifo read out

    p_sm : process(clk, current_state, stall_enable, fifo_empty, stall_in) 
    begin
      next_state <= current_state;
      fifo_read_en <= '0';
      case current_state is
  
        when s_idle =>
          if stall_enable = '0' and fifo_empty = '0' and stall_in = '0' then 
            next_state <= s_read;
          end if;

        when s_read =>
          fifo_read_en <= '1';
          next_state <= s_idle;
  
        when others => next_state <= s_idle;
  
      end case;
    end process;

    p_sm_update : process(clk)
    begin
      if rising_edge(clk) then
        if reset = '1' then
          current_state <= s_idle;
        else
          current_state <= next_state;
        end if;
      end if;
    end process;

    -- Output shift_reg

    p_shift_reg : process(clk)
    begin
      if rising_edge(clk) then
        if reset = '1' then
          shift_reg(reg_bit_width-1 downto 0) <= (others => '0');
          strobe_counter <= to_unsigned(disperse_count, strobe_counter'length);
          data_out <= (others => '0');
          stall_enable <= '1';
          hsync_out <= '0';
          vsync_out <= '0';
          vcomplete_out <= '0';
        else
          strobe_out <= '0';
          stall_enable <= '0';
          hsync_out <= '0';
          vsync_out <= '0';
          vcomplete_out <= '0';
          if fifo_read_en = '1' then
            stall_enable <= '1';
            if stall_in = '1' then
              strobe_counter <= (others => '0');
              shift_reg <= as_fifo_out_data;
            else
              strobe_counter <= (others => '0');
              strobe_counter(0) <= '1';
              shift_reg(reg_bit_width-1) <= as_fifo_out_data(reg_bit_width-1);
              shift_reg(reg_bit_width-2) <= as_fifo_out_data(reg_bit_width-2);
              shift_reg(reg_bit_width-DOUT_WIDTH-6 downto 0) <= as_fifo_out_data( DIN_WIDTH-1 downto DOUT_WIDTH);
              data_out                                       <= as_fifo_out_data(DOUT_WIDTH-1 downto          0);
              data_error_out     <= as_fifo_out_data(reg_bit_width-1);
              strobe_out          <= as_fifo_out_data(reg_bit_width-2);
              hsync_out           <= as_fifo_out_data(reg_bit_width-3);
              vsync_out           <= as_fifo_out_data(reg_bit_width-4);
              vcomplete_out  <= as_fifo_out_data(reg_bit_width-5);
            end if;
          end if;
          if strobe_counter /= disperse_count  then
            stall_enable <= '1';
            if stall_in = '0' then
              shift_reg(reg_bit_width-DOUT_WIDTH-6 downto 0) <= shift_reg( DIN_WIDTH-1 downto DOUT_WIDTH);
              data_out                                       <= shift_reg(DOUT_WIDTH-1 downto          0);
              data_error_out                                 <= shift_reg(reg_bit_width-1);
              strobe_out                                      <= shift_reg(reg_bit_width-2);
              strobe_counter <= strobe_counter + 1;
              if strobe_counter = disperse_count - 1 then
                stall_enable <= '0';
              end if;
            end if;
          end if;
        end if;
      end if;
    end process;
        
    end generate; -- gen_disperse

end RTL;

