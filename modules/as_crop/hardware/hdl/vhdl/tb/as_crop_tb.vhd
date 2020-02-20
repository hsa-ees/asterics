----------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  Copyright (C) Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Entity:         as_crop_tb
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Michael Schaeferling
--
-- Modified:       
--
-- Description:    Testbench for verification of the as_crop module.
--
-- Revision 0.01 - File Created
-- Rivision 1.00 - Changed name to as_crop and made ready for git check-in
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
--! @file  as_crop_tb.vhd
--! @brief Testbench for verification of the as_crop module.
----------------------------------------------------------------------------------
LIBRARY ieee;
USE ieee.std_logic_1164.ALL;
USE ieee.numeric_std.ALL;
 
ENTITY as_memreader_sync_crop_tb IS
END as_memreader_sync_crop_tb;
 
ARCHITECTURE behavior OF as_memreader_sync_crop_tb IS 
 
    -- Component Declaration for the Unit Under Test (UUT)
 
    COMPONENT as_memreader_sync
    PORT(
         Clk : IN  std_logic;
         Reset : IN  std_logic;
         Ready : OUT  std_logic;
         VSYNC_OUT : OUT  std_logic;
         HSYNC_OUT : OUT  std_logic;
         STROBE_OUT : OUT  std_logic;
         DATA_OUT : OUT  std_logic_vector(31 downto 0);
         XRES_OUT : OUT  std_logic_vector(11 downto 0);
         YRES_OUT : OUT  std_logic_vector(11 downto 0);
         SYNC_ERROR_OUT : OUT  std_logic;
         PIXEL_ERROR_OUT : OUT  std_logic;
         STALL_IN : IN  std_logic;
         
         control : IN  std_logic_vector(15 downto 0);
         control_reset : OUT  std_logic_vector(15 downto 0);
         state : OUT  std_logic_vector(15 downto 0);
         addr0_reg : IN  std_logic_vector(31 downto 0);
         parm0_reg : IN  std_logic_vector(31 downto 0);
         parm1_reg : IN  std_logic_vector(31 downto 0);
         
         mem_req : OUT  std_logic;
         mem_req_ack : IN  std_logic;
         mem_go : OUT  std_logic;
         mem_clr_go : IN  std_logic;
         mem_busy : IN  std_logic;
         mem_done : IN  std_logic;
         mem_error : IN  std_logic;
         mem_timeout : IN  std_logic;
         mem_rd_req : OUT  std_logic;
         mem_wr_req : OUT  std_logic;
         mem_bus_lock : OUT  std_logic;
         mem_burst : OUT  std_logic;
         mem_addr : OUT  std_logic_vector(31 downto 0);
         mem_be : OUT  std_logic_vector(15 downto 0);
         mem_xfer_length : OUT  std_logic_vector(11 downto 0);
         mem_in_en : IN  std_logic;
         mem_in_data : IN  std_logic_vector(31 downto 0);
         mem_out_en : IN  std_logic;
         mem_out_data : OUT  std_logic_vector(31 downto 0)
        );
    END COMPONENT;
    
    COMPONENT as_crop
    GENERIC (
         DIN_WIDTH  : integer := 32;
         DOUT_WIDTH : integer := 32
        );
         PORT(
         Clk         : in  std_logic;
         Reset       : in  std_logic;
         Ready       : out std_logic;
         VSYNC_IN    : in  std_logic;
         HSYNC_IN    : in  std_logic;
         STROBE_IN   : in  std_logic;
         DATA_IN     : in  std_logic_vector(DIN_WIDTH-1 downto 0);
         XRES_IN     : in  std_logic_vector(11 downto 0);
         YRES_IN     : in  std_logic_vector(11 downto 0);
         SYNC_ERROR_IN  : in  std_logic;
         PIXEL_ERROR_IN : in  std_logic;
         STALL_OUT      : out std_logic;
         VSYNC_OUT   : out std_logic;
         HSYNC_OUT   : out std_logic;
         STROBE_OUT  : out std_logic;
         DATA_OUT    : out std_logic_vector(DOUT_WIDTH-1 downto 0);
         XRES_OUT    : out std_logic_vector(11 downto 0);
         YRES_OUT    : out std_logic_vector(11 downto 0);
         SYNC_ERROR_OUT  : out std_logic;
         PIXEL_ERROR_OUT : out std_logic;
         STALL_IN        : in  std_logic;
         parm0_reg : IN  std_logic_vector(31 downto 0);
         parm1_reg : IN  std_logic_vector(31 downto 0)
        );
    END COMPONENT;

   --Inputs
   signal Clk : std_logic := '0';
   signal Reset : std_logic := '0';
   signal control : std_logic_vector(15 downto 0) := (others => '0');
   signal addr0_reg : std_logic_vector(31 downto 0) := (others => '0');
   signal parm0_reg : std_logic_vector(31 downto 0) := (others => '0');
   signal parm1_reg : std_logic_vector(31 downto 0) := (others => '0');
   signal mem_req_ack : std_logic := '0';
   signal mem_clr_go : std_logic := '0';
   signal mem_busy : std_logic := '0';
   signal mem_done : std_logic := '0';
   signal mem_error : std_logic := '0';
   signal mem_timeout : std_logic := '0';
   signal mem_in_en : std_logic := '0';
   signal mem_in_data : std_logic_vector(31 downto 0) := (others => '0');
   signal mem_out_en : std_logic := '0';

    --Outputs
   signal Ready : std_logic;
   signal control_reset : std_logic_vector(15 downto 0);
   signal state : std_logic_vector(15 downto 0);
   signal mem_req : std_logic;
   signal mem_go : std_logic;
   signal mem_rd_req : std_logic;
   signal mem_wr_req : std_logic;
   signal mem_bus_lock : std_logic;
   signal mem_burst : std_logic;
   signal mem_addr : std_logic_vector(31 downto 0);
   signal mem_be : std_logic_vector(15 downto 0);
   signal mem_xfer_length : std_logic_vector(11 downto 0);
   signal mem_out_data : std_logic_vector(31 downto 0);
   --
   signal STALL_IN : std_logic := '0';
   signal VSYNC_OUT : std_logic;
   signal HSYNC_OUT : std_logic;
   signal STROBE_OUT : std_logic;
   signal DATA_OUT : std_logic_vector(31 downto 0);
   signal XRES_OUT : std_logic_vector(11 downto 0);
   signal YRES_OUT : std_logic_vector(11 downto 0);
   signal SYNC_ERROR_OUT : std_logic;
   signal PIXEL_ERROR_OUT : std_logic;
   
   
   signal crop_par0 : std_logic_vector(31 downto 0);
   signal crop_par1 : std_logic_vector(31 downto 0);
   
-- glue signals:
   signal STROBE0 : std_logic;
   signal STALL0 : std_logic;
   signal VSYNC0 : std_logic;
   signal HSYNC0 : std_logic;
   signal DATA0 : std_logic_vector(31 downto 0);
   signal XRES0 : std_logic_vector(11 downto 0);
   signal YRES0 : std_logic_vector(11 downto 0);
   signal SYNC_ERROR0 : std_logic;
   signal PIXEL_ERROR0 : std_logic;
   
   
-- tb signals and registers:
   signal set_go : std_logic;
   signal mem_data_counter : unsigned(9 downto 0);
   signal mem_addr_counter : unsigned(31 downto 0);
   -- global data counter vor data generation:
   signal data_counter : unsigned(31 downto 0);
   
   


  -- <Controller>
  type MEM_CTL_STATES is ( MEM_IDLE, MEM_TX_BURST);
  signal MEM_CTL_STATE: MEM_CTL_STATES := MEM_IDLE;


   -- Clock period definitions
   constant Clk_period : time := 10 ns;
 
BEGIN
 
    -- Instantiate the Unit Under Test (UUT)
   uut0: as_memreader_sync PORT MAP (
          Clk => Clk,
          Reset => Reset,
          Ready => Ready,
          -- output to disperse module
          VSYNC_OUT => VSYNC0,
          HSYNC_OUT => HSYNC0,
          STROBE_OUT => STROBE0,
          DATA_OUT => DATA0,
          XRES_OUT => XRES0,
          YRES_OUT => YRES0,
          SYNC_ERROR_OUT => SYNC_ERROR0,
          PIXEL_ERROR_OUT => PIXEL_ERROR0,
          STALL_IN => STALL0,
          --
          control => control,
          control_reset => control_reset,
          state => state,
          addr0_reg => addr0_reg,
          parm0_reg => parm0_reg,
          parm1_reg => parm1_reg,
          mem_req => mem_req,
          mem_req_ack => mem_req_ack,
          mem_go => mem_go,
          mem_clr_go => mem_clr_go,
          mem_busy => mem_busy,
          mem_done => mem_done,
          mem_error => mem_error,
          mem_timeout => mem_timeout,
          mem_rd_req => mem_rd_req,
          mem_wr_req => mem_wr_req,
          mem_bus_lock => mem_bus_lock,
          mem_burst => mem_burst,
          mem_addr => mem_addr,
          mem_be => mem_be,
          mem_xfer_length => mem_xfer_length,
          mem_in_en => mem_in_en,
          mem_in_data => mem_in_data,
          mem_out_en => mem_out_en,
          mem_out_data => mem_out_data
        );
        
    -- Instantiate the Unit Under Test (UUT)
   uut1: as_crop 
   GENERIC MAP (
          DIN_WIDTH => 32,
          DOUT_WIDTH => 32
          )
   PORT MAP (
          Clk => Clk,
          Reset => Reset,
          Ready => Ready,
          -- input from memreader
          VSYNC_IN => VSYNC0,
          HSYNC_IN => HSYNC0,
          STROBE_IN => STROBE0,
          DATA_IN => DATA0,
          XRES_IN => XRES0,
          YRES_IN => YRES0,
          SYNC_ERROR_IN => SYNC_ERROR0,
          PIXEL_ERROR_IN => PIXEL_ERROR0,
          STALL_OUT => STALL0,
          -- output to tb
          VSYNC_OUT => VSYNC_OUT,
          HSYNC_OUT => HSYNC_OUT,
          STROBE_OUT => STROBE_OUT,
          DATA_OUT => DATA_OUT,
          XRES_OUT => XRES_OUT,
          YRES_OUT => YRES_OUT,
          SYNC_ERROR_OUT => SYNC_ERROR_OUT,
          PIXEL_ERROR_OUT => PIXEL_ERROR_OUT,
          STALL_IN => STALL_IN,
          parm0_reg => crop_par0,
          parm1_reg => crop_par1
        );
 
 
   mem_proc: process(Clk)
   begin 
     if (Clk'event and Clk='0') then
       if (reset = '1') then
         data_counter <= (others => '0');
       
       else
         -- handle ctl_reg_go
         if (control_reset(1) = '1') then
           control(1) <= '0';
         elsif (set_go = '1') then
           control(1) <= '1';
         end if;
       
         -- always grant mem access as it's only one master here:
         if (mem_req = '1') then
           mem_req_ack <= '1';
         end if;
         
         -- defaults:
         mem_in_en <= '0';
         mem_busy <= '0';
         mem_done <= '0';
         
         
         case (MEM_CTL_STATE) is

            when MEM_IDLE =>
                                  if (mem_go = '1') then
                                    mem_clr_go <= '1';
                                    mem_data_counter <= unsigned(mem_xfer_length(11 downto 2));  -- mem_xfer_length is in bytes, needs to be divided by 4 for 32bit data wide access.
                                    
                                    mem_addr_counter <= unsigned(mem_addr);
                                    
                                    if (mem_rd_req = '1') and (mem_burst = '1') then
                                      MEM_CTL_STATE <= MEM_TX_BURST;
                                      mem_busy <= '1';
                                    end if;
                                  end if;

            when MEM_TX_BURST => 
                                  if (mem_data_counter = 0) then
                                    MEM_CTL_STATE <= MEM_IDLE;
                                    mem_done <= '1';
                                  else
                                    mem_busy <= '1';
                                    mem_in_en <= '1';
                                    mem_in_data <= std_logic_vector(data_counter);
                                    mem_data_counter <= mem_data_counter - 1;
                                    data_counter <= data_counter + 1;
                                  end if;
                                  
            
            when others =>
                                  MEM_CTL_STATE <= MEM_IDLE;
                                  
         end case;
         
       end if;
     
     end if;
    
   end process;
 
 

 

   -- Stimulus process
   stim_proc: process
      
      procedure run_cycles (cycles: in integer) is
      begin
        for cycle in 1 to cycles loop
          Clk <= '0';
          wait for Clk_period/2;
          Clk <= '1';
          wait for Clk_period/2;
        end loop;
      end run_cycles;
      
      
      procedure mrd_set_params(addr: in integer; words: in integer; lines: in integer; burst_length: in integer; bursts: in integer) is
      begin
        addr0_reg <= std_logic_vector(to_unsigned(addr, addr0_reg'length));
        parm0_reg <= std_logic_vector(to_unsigned(burst_length, 8)) & "00000000" & std_logic_vector(to_unsigned(bursts, 16));
        parm1_reg <= std_logic_vector(to_unsigned(words, 16)) & std_logic_vector(to_unsigned(lines, 16));
      end mrd_set_params;
      
      procedure crop_set_params(x1: in integer; y1: in integer; x2: in integer; y2: in integer) is
      begin
        crop_par0(31 downto 16) <= std_logic_vector(to_unsigned(x1, 16));
        crop_par0(15 downto  0) <= std_logic_vector(to_unsigned(y1, 16));
        crop_par1(31 downto 16) <= std_logic_vector(to_unsigned(x2, 16));
        crop_par1(15 downto  0) <= std_logic_vector(to_unsigned(y2, 16));
      end crop_set_params;
      
      
      procedure mrd_go is
      begin
        set_go <= '1';
        run_cycles(1);
        set_go <= '0';
      end mrd_go;

      
   begin
   
      -- reset
      reset <= '1';
      run_cycles(3);
      
      reset <= '0';
      run_cycles(3);
      --
      
      --
      crop_set_params(0,0,3,3);
      --crop_set_params(1,1,4,8);
      --
      
      mrd_set_params(0, 16, 16, 64, 16);
      run_cycles(2);

      mrd_go;
 
      
      
      run_cycles(8000000);
      wait;
   end process;

END;

