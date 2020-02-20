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
-- Copyright (C) 2010-2019 Matthias Pohl, Markus Litzel, Werner Landsperger and
--                         Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- File:           vears_main.vhd
-- Entity:         vears_main
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
-- Author:         Matthias Pohl, Markus Litzel, Werner Landsperger
-- Create Date:    06/11/2009
--
-- Version:  1.0
-- Modified:       * 16/11/2013 by Michael Schaeferling
--                   - major cleanup, was 'ea'
--                 * 14/06/2017 by Michael Schaeferling
--                 * 05/04/2019 by Michael Schaeferling
--                   - Add TMDS (HDMI) output
--                   - Rename DVI to CH7301C as this is the actual device to connect here
--                   - Add generics for output variations
--                   - Add generic for AXI-ACLK input frequency
--                   - for submodules, use the library to avoid endless component decalarations
--                 * 10/04/2019 by Michael Schaeferling
--                   - Rename interface TMDS to HDMI
--                 * 11/04/2019 by Michael Schaeferling
--                   - Add 'generate' statements to implement HDMI and CH7301C logic only if needed
--                 * 05/07/2019 by Michael Schaeferling
--                   - Add interrupt support
--                   - rename 'vga_' prefix to 's_pix_' (pixel output from video_timing module)
--                 * 12/09/2019 by Michael Schaeferling
--
-- Description:    Interconnecting all VEARS sub-modules.
----------------------------------------------------------------------------------


library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use IEEE.STD_LOGIC_UNSIGNED.ALL;
use IEEE.MATH_REAL.ceil;
use IEEE.MATH_REAL.log2;

library vears;
use vears.clocking;
use vears.vears_mc;
use vears.linebuffer;
use vears.mux_1of16_32bit;
use vears.mux_1of4_32bit;
use vears.clut;
use vears.mux_pic_ovl;
use vears.video_timing;
use vears.CH7301C_out;
use vears.rgb2dvi;

entity vears_main is
  generic(
    CLK_MST_FREQ_HZ : integer;

    MEM_DATA_WIDTH : positive := 32;

    VIDEO_GROUP : integer;
    VIDEO_MODE  : integer;
    COLOR_MODE : integer;

    VGA_OUTPUT_ENABLE : boolean := false;
    VGA_TFT_OUTPUT_ENABLE : boolean := false;
    CH7301C_OUTPUT_ENABLE : boolean := false;
    HDMI_OUTPUT_ENABLE : boolean := false
  );
  port(
    clk_mst    : in  std_logic;
    reset_mst  : in  std_logic;
    
    clk_slv    : in  std_logic;

    ---- Interface to analog Monitor ----
    vga_red   : out std_logic_vector(7 downto 0);
    vga_green : out std_logic_vector(7 downto 0); 
    vga_blue  : out std_logic_vector(7 downto 0);
    vga_hsync : out std_logic;
    vga_vsync : out std_logic;
    ---- Interface to TFT (additional signals) ----
    tft_vga_dclk : out std_logic;
    tft_vga_enb  : out std_logic;

    ---- Interface to Chrontel CH7301C ----
    ch7301c_clk_p : out std_logic;
    ch7301c_clk_n : out std_logic;
    ch7301c_data  : out std_logic_vector(11 downto 0);
    ch7301c_de    : out std_logic;
    ch7301c_hsync : out std_logic;
    ch7301c_vsync : out std_logic;

    ---- DVI 1.0 TMDS video interface (HDMI) ----
    hdmi_clk_p  : out std_logic;
    hdmi_clk_n  : out std_logic;
    hdmi_data_p : out std_logic_vector(2 downto 0);
    hdmi_data_n : out std_logic_vector(2 downto 0);
    hdmi_out_en : out std_logic;
    hdmi_hpd    : in  std_logic;
    hdmi_cec    : in  std_logic;

    ---- Interrupt sources ----
    intr_frame : out std_logic;
    intr_line  : out std_logic;
    
    ----- Master Control signals ----- 
    mem_in_en       :    in  std_logic;
    mem_in_data     :    in  std_logic_vector(MEM_DATA_WIDTH-1 downto 0);
    
    mem_out_en      :    in  std_logic;
    mem_out_data    :    out std_logic_vector(MEM_DATA_WIDTH-1 downto 0);
    
    mem_go          :    out std_logic;
    mem_clr_go      :    in  std_logic;
    mem_busy        :    in  std_logic;
    mem_done        :    in  std_logic;
    mem_error       :    in  std_logic;
    mem_timeout     :    in  std_logic;
    
    mem_rd_req      :    out std_logic;
    mem_wr_req      :    out std_logic;
    mem_bus_lock    :    out std_logic;
    mem_burst       :    out std_logic;
    mem_addr        :    out std_logic_vector(31 downto 0);
    mem_be          :    out std_logic_vector(15 downto 0);
    mem_xfer_length :    out std_logic_vector(11 downto 0);
    
    ---- Slave register interfaces ----
    control : in std_logic_vector(31 downto 0);
    status : out std_logic_vector(31 downto 0);
    image_baseaddress : in std_logic_vector(31 downto 0);
    overlay_baseaddress : in std_logic_vector(31 downto 0);
    overlay_color1 : in std_logic_vector(23 downto 0);
    overlay_color2 : in std_logic_vector(23 downto 0);
    overlay_color3 : in std_logic_vector(23 downto 0)

  );
end vears_main;

architecture RTL of vears_main is




constant c_CLK_SYS_FREQ_MHZ : real := REAL(CLK_MST_FREQ_HZ) / 1000000.0;


signal c_color_mode_en : std_logic_vector(0 downto 0);


type video_settings_t is record
  vid_group_id : std_logic_vector(7 downto 0);
  vid_mode_id : std_logic_vector(7 downto 0);
  Pixel_Clock : real;
  H_Tpw   : integer;
  H_Tbp   : integer;
  H_Tdisp : integer;
  H_Tfp   : integer;
  H_SP    : std_logic;
  V_Tpw   : integer;
  V_Tbp   : integer;
  V_Tdisp : integer;
  V_Tfp   : integer;
  V_SP    : std_logic;
end record video_settings_t;

type video_settings_mode_array_t is array (1 to 35) of video_settings_t;
type video_settings_group_mode_array_t is array (1 to 2) of video_settings_mode_array_t;

constant c_video_settings : video_settings_group_mode_array_t := (
--                  VID_GROUP_ID , VID_MODE_ID , Pixel_Clock , H_Tpw , H_Tbp, H_Tdisp , H_Tfp , H_SP , V_Tpw , V_Tbp , V_Tdisp , V_Tfp , V_SP
  1 => (  4  =>    (x"01"        , x"04"       , 74.250      , 40    , 220  , 1280    , 110   , '1'  , 5     , 20    , 720     , 5     , '1' ), -- 1280x720  @ 60Hz/45kHz   (@74.250MHz PixClk)
         32  =>    (x"01"        , x"20"       , 74.250      , 44    , 148  , 1920    , 638   , '1'  , 5     , 36    , 1080    , 4     , '1' ), -- 1920x1080 @ 24Hz/26.8kHz (@74.250MHz PixClk)
         33  =>    (x"01"        , x"21"       , 74.250      , 44    , 148  , 1920    , 528   , '1'  , 5     , 36    , 1080    , 4     , '1' ), -- 1920x1080 @ 25Hz/27.9kHz (@74.250MHz PixClk)
         34  =>    (x"01"        , x"22"       , 74.250      , 44    , 148  , 1920    , 88    , '1'  , 5     , 36    , 1080    , 4     , '1' ), -- 1920x1080 @ 30Hz/33.5kHz (@74.250MHz PixClk)
         others => (x"00"        , x"00"       , 100.0       , 0     , 0    , 40      , 0     , '0'  , 0     , 0     , 20      , 0     , '0' )  -- provide some dummy values to prevent synthesis failure before assertions may catch
       ),
  2 => (  4  =>    (x"02"        , x"04"       , 25.175      , 96    , 48   , 640     , 16    , '0'  , 2     , 33    , 480     , 10    , '0' ), -- 640x480   @ 60Hz/31.5kHz (@25.175MHz PixClk) / Industry Standard
          8  =>    (x"02"        , x"08"       , 36.0        , 72    , 128  , 800     , 24    , '1'  , 2     , 22    , 600     , 1     , '1' ), -- 800x600   @ 56Hz/35.2kHz (@36MHz PixClk)     / VESA#900601
         10  =>    (x"02"        , x"0A"       , 50.0        , 120   , 64   , 800     , 56    , '1'  , 6     , 23    , 600     , 37    , '1' ), -- 800x600   @ 72Hz/48.1kHz (@50MHz PixClk)     / VESA#900603A
         16  =>    (x"02"        , x"10"       , 65.0        , 136   , 160  , 1024    , 24    , '0'  , 6     , 29    , 768     , 3     , '0' ), -- 1024x768  @ 60Hz/48.4kHz (@65MHz PixClk)     / VESA#901101A
         35  =>    (x"02"        , x"23"       , 108.0       , 112   , 248  , 1280    , 48    , '1'  , 3     , 38    , 1024    , 1     , '1' ), -- 1280x1024 @ 60Hz/64kHz   (@108MHz PixClk)    / VESA#VDMTREV
         others => (x"00"        , x"00"       , 100.0       , 0     , 0    , 40      , 0     , '0'  , 0     , 0     , 20      , 0     , '0' )  -- provide some dummy values to prevent synthesis failure before assertions may catch
       )
);


constant c_prebuffer_lines : integer := 1;

constant c_addr_width_pic_linebuffer : integer := INTEGER(CEIL(LOG2(REAL(c_video_settings(VIDEO_GROUP)(VIDEO_MODE).H_Tdisp/( 4 - COLOR_MODE*4 + COLOR_MODE ))))) + c_prebuffer_lines; -- 1 pixel in 1 BRAM data word (32bit wide) for grayscale, 
constant c_addr_width_ovl_linebuffer : integer := INTEGER(CEIL(LOG2(REAL(c_video_settings(VIDEO_GROUP)(VIDEO_MODE).H_Tdisp)))) + c_prebuffer_lines - 4; 


-- in Grayscale mode: the lower 2 bits of c_addr_width_video_timing_linebuff are cut off when assigning this value to BRAM adresses
constant c_video_timing_linebuff_addr_width : integer := INTEGER(CEIL(LOG2(REAL(c_video_settings(VIDEO_GROUP)(VIDEO_MODE).H_Tdisp))));



attribute ASYNC_REG : string;

signal s_run : std_logic;
signal s_reset_soft : std_logic;
signal s_ovl_en : std_logic;
signal s_intr_frame_en : std_logic;
signal s_intr_line_en : std_logic;
signal s_intr_line_number : std_logic_vector(15 downto 0); 

signal clk_gen_x1, clk_gen_x5, clk_gen_x2, clk_gen_x2_n : std_logic;
signal clk_gen_locked : std_logic;

----------     Signals for internal use     ----------
signal video_timing_linebuff_addr : std_logic_vector(c_video_timing_linebuff_addr_width-1 downto  0);
signal video_timing_linebuff_sel  : std_logic;

signal data_pic_video_pix_mux   : std_logic_vector( 7 downto  0);
signal data_pic_video_pix_mux_3 : std_logic_vector(23 downto  0);
signal data_ovl_video_pix_mux   : std_logic_vector(23 downto  0);
signal switch_ovl_bit24_mux   : std_logic;
signal data_out_bit24_mux     : std_logic_vector(23 downto 0);

signal input_2bit_clut   : std_logic_vector( 1 downto  0);
signal output_24bit_clut : std_logic_vector(23 downto  0);
signal data_video_pix_mux  : std_logic_vector(23 downto  0);

signal data_sel_sel_ovl_pix_mux : std_logic_vector( 3 downto  0);
signal data_sel_sel_pic_pix_mux : std_logic_vector( 1 downto  0);

signal mc2pic_linebuff_addr : std_logic_vector(c_addr_width_pic_linebuffer-1 downto  0);
signal mc2ovl_linebuff_addr : std_logic_vector(c_addr_width_ovl_linebuffer-1 downto  0);
signal mc2linebuff_data     : std_logic_vector(31 downto  0);
signal mc2pic_linebuff_wr   : std_logic;
signal mc2ovl_linebuff_wr   : std_logic;

signal pic_linebuff_rd_addr : std_logic_vector(c_addr_width_pic_linebuffer-1 downto  0);
signal pic_linebuff_rd_data : std_logic_vector(31 downto  0);
signal ovl_linebuff_rd_addr : std_logic_vector(c_addr_width_ovl_linebuffer-1 downto  0);
signal ovl_linebuff_rd_data : std_logic_vector(31 downto  0);

signal line_indicator_clk_gen_x2, line_indicator_0, line_indicator_mst, line_indicator_mst_last : std_logic;
signal frame_indicator_clk_gen_x2, frame_indicator_0, frame_indicator_mst, frame_indicator_mst_last : std_logic;

-- Set the ASYNC_REG attribute to motivate Vivado to place corresponding registers close 
-- to each other (to maximize the MTBF along with clock domain crossings):
attribute ASYNC_REG of line_indicator_0: signal is "TRUE";
attribute ASYNC_REG of line_indicator_mst: signal is "TRUE";
attribute ASYNC_REG of frame_indicator_0: signal is "TRUE";
attribute ASYNC_REG of frame_indicator_mst: signal is "TRUE";

signal line_indicator_slv_0, line_indicator_slv, line_indicator_slv_last, frame_indicator_slv_0, frame_indicator_slv, frame_indicator_slv_last : std_logic;
attribute ASYNC_REG of line_indicator_slv_0: signal is "TRUE";
attribute ASYNC_REG of line_indicator_slv: signal is "TRUE";
attribute ASYNC_REG of frame_indicator_slv_0: signal is "TRUE";
attribute ASYNC_REG of frame_indicator_slv: signal is "TRUE";

signal vs_det_last : std_logic;
signal trigger_frame, trigger_line : std_logic;

signal ovl_en_clk_gen_x2, ovl_en_clk_gen_x2_0, ovl_en_clk_mst_0 : std_logic;
signal reset_clk_gen_x2, reset_detect_clk_gen_x2_last, reset_detect_clk_gen_x2, reset_detect_0 : std_logic;
signal reset_mst_last, reset_mst_detect : std_logic;
signal ovl_color1_clk_gen_x2, ovl_color1_clk_gen_x2_0, ovl_color1_clk_mst_0 : std_logic_vector(23 downto  0);
signal ovl_color2_clk_gen_x2, ovl_color2_clk_gen_x2_0, ovl_color2_clk_mst_0 : std_logic_vector(23 downto  0);
signal ovl_color3_clk_gen_x2, ovl_color3_clk_gen_x2_0, ovl_color3_clk_mst_0 : std_logic_vector(23 downto  0);

-- Set the ASYNC_REG attribute to motivate Vivado to place corresponding registers close 
-- to each other (to maximize the MTBF along with clock domain crossings):
--~ attribute ASYNC_REG of reset_detect_0: signal is "TRUE";
--~ attribute ASYNC_REG of reset_detect_clk_gen_x2: signal is "TRUE";

--~ attribute ASYNC_REG of ovl_en_clk_mst_0: signal is "TRUE";
--~ attribute ASYNC_REG of ovl_en_clk_gen_x2_0: signal is "TRUE";
--~ attribute ASYNC_REG of ovl_en_clk_gen_x2: signal is "TRUE";

--~ attribute ASYNC_REG of ovl_color1_clk_mst_0: signal is "TRUE";
--~ attribute ASYNC_REG of ovl_color1_clk_gen_x2_0: signal is "TRUE";
--~ attribute ASYNC_REG of ovl_color1_clk_gen_x2: signal is "TRUE";
--~ attribute ASYNC_REG of ovl_color2_clk_mst_0: signal is "TRUE";
--~ attribute ASYNC_REG of ovl_color2_clk_gen_x2_0: signal is "TRUE";
--~ attribute ASYNC_REG of ovl_color2_clk_gen_x2: signal is "TRUE";
--~ attribute ASYNC_REG of ovl_color3_clk_mst_0: signal is "TRUE";
--~ attribute ASYNC_REG of ovl_color3_clk_gen_x2_0: signal is "TRUE";
--~ attribute ASYNC_REG of ovl_color3_clk_gen_x2: signal is "TRUE";

signal r_intr_line  : std_logic;
signal r_intr_frame : std_logic;

--------------------------------------------------------
--------------------------------------------------------------------------------

signal s_pix_chg    : std_logic;
signal s_pix_hsync  : std_logic;
signal s_pix_vsync  : std_logic;
signal s_pix_red    : std_logic_vector(7 downto 0);
signal s_pix_blue   : std_logic_vector(7 downto 0);
signal s_pix_green  : std_logic_vector(7 downto 0);
signal s_pix_de     : std_logic;


begin


--ASSERT (0=1)
--  REPORT "Just an assertion test ... GROUP=" & integer'image(VIDEO_GROUP) & " MODE=" & integer'image(VIDEO_MODE)
--  SEVERITY FAILURE;


ASSERT ( (VIDEO_GROUP=1 and VIDEO_MODE=32) or (VIDEO_GROUP=1 and VIDEO_MODE=33) or (VIDEO_GROUP=1 and VIDEO_MODE=34) or 
         (VIDEO_GROUP=2 and VIDEO_MODE= 4) or (VIDEO_GROUP=2 and VIDEO_MODE= 8) or (VIDEO_GROUP=2 and VIDEO_MODE=10) or (VIDEO_GROUP=2 and VIDEO_MODE= 16) or (VIDEO_GROUP=2 and VIDEO_MODE=35) 
       )
  REPORT "VEARS: No valid VIDEO GROUP (" & integer'image(VIDEO_GROUP) & ") and VIDEO MODE (" & integer'image(VIDEO_MODE) & ") combination selected. See the manual for supported modes."
  SEVERITY FAILURE;


ASSERT ( ( COLOR_MODE = 0 ) or (COLOR_MODE = 1 ) )
  REPORT "VEARS: No valid COLOR MODE (" & integer'image(COLOR_MODE) & ") selected. See the manual for supported modes."
  SEVERITY FAILURE;



c_color_mode_en <= std_logic_vector(to_unsigned(COLOR_MODE, 1));


-- Status signals:
status(15 downto 0) <= c_video_settings(VIDEO_GROUP)(VIDEO_MODE).vid_mode_id &
                       c_video_settings(VIDEO_GROUP)(VIDEO_MODE).vid_group_id;
status(16) <= c_color_mode_en(0);
status(31 downto 17) <= (others => '0'); -- reserved


-- Control signals:
s_reset_soft <= control(0);
s_run        <= control(1);
s_ovl_en     <= control(2);

-- Interrupt control:
s_intr_frame_en <= control(6);
s_intr_line_en  <= control(7);



vga_red   <= s_pix_red;
vga_green <= s_pix_green;
vga_blue  <= s_pix_blue;
vga_hsync <= s_pix_hsync;
vga_vsync <= s_pix_vsync;
tft_vga_enb  <= s_pix_de;
tft_vga_dclk <= s_pix_chg;



clocking_1 : entity clocking
  generic map (
    CLK_IN_FREQ_MHZ => c_CLK_SYS_FREQ_MHZ,
    CLK_OUT_FREQ_MHZ => c_video_settings(VIDEO_GROUP)(VIDEO_MODE).Pixel_Clock
  )
  port map (
    clk_in       => clk_mst,
    reset        => reset_mst,
    clk_out      => clk_gen_x1,
    clk_out_x5   => clk_gen_x5,
    clk_out_x2_p => clk_gen_x2,
    clk_out_x2_n => clk_gen_x2_n,
    locked       => clk_gen_locked
  );


vears_mc_1 : entity vears_mc
  generic map (
    DATA_WIDTH  => MEM_DATA_WIDTH,
    PIXELS      => c_video_settings(VIDEO_GROUP)(VIDEO_MODE).H_Tdisp, 
    BYTES_PER_PIXEL => 4**COLOR_MODE,
    LINES       => c_video_settings(VIDEO_GROUP)(VIDEO_MODE).V_Tdisp,
    ADDR_WIDTH_PIC_LINEBUFFER => c_addr_width_pic_linebuffer,
    ADDR_WIDTH_OVL_LINEBUFFER => c_addr_width_ovl_linebuffer
  )
  port map (
    clk   => clk_mst,
    reset => reset_mst,

    run => s_run,
    reset_soft => s_reset_soft,
    ovl_en => s_ovl_en,

    base_addr_pic => image_baseaddress,
    base_addr_ovl => overlay_baseaddress,

    ----------     Communication-with-linebuffer     ----------
    trigger_line       => trigger_line,
    trigger_frame      => trigger_frame,
    pic_linebuff_write => mc2pic_linebuff_wr,
    ovl_linebuff_write => mc2ovl_linebuff_wr,
    linebuff_data      => mc2linebuff_data,
    pic_linebuff_addr  => mc2pic_linebuff_addr,
    ovl_linebuff_addr  => mc2ovl_linebuff_addr,
    -----------------------------------------------------------

    ----------     PLB-MASTER-Signals     ----------
    mem_in_en    => mem_in_en,
    mem_in_data  => mem_in_data,
    mem_out_en   => mem_out_en,
    mem_out_data => mem_out_data,
    mem_go       => mem_go,
    mem_clr_go   => mem_clr_go,
    mem_busy     => mem_busy,
    mem_done     => mem_done,
    mem_error    => mem_error,
    mem_timeout  => mem_timeout,
    mem_rd_req   => mem_rd_req,
    mem_wr_req   => mem_wr_req,
    mem_bus_lock => mem_bus_lock,
    mem_burst    => mem_burst,
    mem_addr     => mem_addr,
    mem_be       => mem_be,
    mem_xfer_length => mem_xfer_length
  );


linebuff_ovl : entity linebuffer 
  generic map (
    ADDR_WIDTH => c_addr_width_ovl_linebuffer
  )
  port map (
    clk_wr   => clk_mst,
    clk_rd   => clk_gen_x2,

    ----------     input/output for fears_mc     ----------
    wr_en    => mc2ovl_linebuff_wr,
    wr_addr  => mc2ovl_linebuff_addr(c_addr_width_ovl_linebuffer-1 downto 0),
    wr_data  => mc2linebuff_data,
    --------------------------------------------------------

    -----------     input/output for address logic     -----------
    rd_addr  => ovl_linebuff_rd_addr,
    rd_data  => ovl_linebuff_rd_data
    --------------------------------------------------------------
  );
-- [3..0] select 1 of 16 values in 32-bit word
ovl_linebuff_rd_addr <= video_timing_linebuff_sel & video_timing_linebuff_addr(c_addr_width_ovl_linebuffer+2 downto 4);






linebuff_pic : entity linebuffer 
  generic map (
    addr_width => c_addr_width_pic_linebuffer
  )
  port map (
    clk_wr => clk_mst,
    clk_rd => clk_gen_x2,

    ----------     input/output for fears_mc     ----------
    wr_en   => mc2pic_linebuff_wr,
    wr_addr => mc2pic_linebuff_addr(c_addr_width_pic_linebuffer-1 downto 0),
    wr_data => mc2linebuff_data,
    --------------------------------------------------------

    -----------     input/output for address logic     -----------
    rd_addr => pic_linebuff_rd_addr,
    rd_data => pic_linebuff_rd_data
    --------------------------------------------------------------
    );




g_Grayscale_8bit_per_Pix : if COLOR_MODE = 0 generate
  -- video_timing_linebuff_addr[1..0] select 1 of 4 values in 32-bit word
  pic_linebuff_rd_addr <= video_timing_linebuff_sel & video_timing_linebuff_addr(c_addr_width_pic_linebuffer downto 2);

  -- selects one of the 4 8-bit pixel values, which are contained in a 32-bit word read from pic-linebuffer
  -- and uses this value to output for each R, G and B channel (each 8-bit, resulting in 24-bit)
  sel_pic_pix_mux : entity mux_1of4_32bit
    port map  (
      data_sel => data_sel_sel_pic_pix_mux,
      data_in  => pic_linebuff_rd_data,
      data_out => data_pic_video_pix_mux
    );

  -- in grayscale mode: replicate gray value to all channels
  data_pic_video_pix_mux_3 <= data_pic_video_pix_mux & data_pic_video_pix_mux & data_pic_video_pix_mux;
end generate;



g_Color_32bit_per_Pix : if COLOR_MODE = 1 generate
  -- 
  pic_linebuff_rd_addr <= video_timing_linebuff_sel & video_timing_linebuff_addr(c_addr_width_pic_linebuffer-2 downto 0);
  
  -- in color mode: RGB channels are directly given to video output
  data_pic_video_pix_mux_3 <= pic_linebuff_rd_data(31 downto 8);
end generate;




-- selects one of 16 2-bit values, which are contained in a 32-bit word read from ovl-linebuffer
sel_ovl_pix_mux : entity mux_1of16_32bit
  port map (
    data_sel => data_sel_sel_ovl_pix_mux,
    data_in  => ovl_linebuff_rd_data,
    data_out => input_2bit_clut
  );

-- with the 2-bit value, select the corresponding color to display
clut_ovl_pix : entity clut
  port map (
    color_select => input_2bit_clut,
    color_1   => ovl_color1_clk_gen_x2,
    color_2   => ovl_color2_clk_gen_x2,
    color_3   => ovl_color3_clk_gen_x2,
    color_out => data_ovl_video_pix_mux
  );
    
-- merge picture and overlay data
pix_mux : entity mux_pic_ovl
  port map (
    data_sel => input_2bit_clut,
    ovl_en   => ovl_en_clk_gen_x2,
    data_pic => data_pic_video_pix_mux_3,
    data_ovl => data_ovl_video_pix_mux,
    data_out => data_video_pix_mux
  );


video_timing_1 : entity video_timing
  generic map(
    PREBUFFER_LINES => c_prebuffer_lines,
    VIDEO_TIMING_LINEBUFF_ADDR_WIDTH => c_video_timing_linebuff_addr_width,
    H_Tpw   => c_video_settings(VIDEO_GROUP)(VIDEO_MODE).H_Tpw ,
    H_Tbp   => c_video_settings(VIDEO_GROUP)(VIDEO_MODE).H_Tbp,
    H_Tdisp => c_video_settings(VIDEO_GROUP)(VIDEO_MODE).H_Tdisp,
    H_Tfp   => c_video_settings(VIDEO_GROUP)(VIDEO_MODE).H_Tfp,
    H_SP    => c_video_settings(VIDEO_GROUP)(VIDEO_MODE).H_SP,
    V_Tpw   => c_video_settings(VIDEO_GROUP)(VIDEO_MODE).V_Tpw,
    V_Tbp   => c_video_settings(VIDEO_GROUP)(VIDEO_MODE).V_Tbp,
    V_Tdisp => c_video_settings(VIDEO_GROUP)(VIDEO_MODE).V_Tdisp,
    V_Tfp   => c_video_settings(VIDEO_GROUP)(VIDEO_MODE).V_Tfp,
    V_SP    => c_video_settings(VIDEO_GROUP)(VIDEO_MODE).V_SP
    )
  port map (
    clk             => clk_gen_x2,
    reset           => reset_clk_gen_x2,

    trigger_line    => line_indicator_clk_gen_x2,

    pixel_data      => data_video_pix_mux,

    h_count         => video_timing_linebuff_addr,
    v_sel           => video_timing_linebuff_sel,

    pix_red         => s_pix_red,
    pix_green       => s_pix_green,
    pix_blue        => s_pix_blue,
    pix_hsync       => s_pix_hsync,
    pix_vsync       => s_pix_vsync,
    pix_de          => s_pix_de,
    pix_chg         => s_pix_chg
  );
  


g_ch7301c_out_enable: if CH7301C_OUTPUT_ENABLE = true generate
  CH7301C_out_1 : entity CH7301C_out 
    port map(
      clk       => clk_gen_x2,
      data_sel  => s_pix_chg,
      pix_red   => s_pix_red,
      pix_green => s_pix_green,
      pix_blue  => s_pix_blue,
      pix_hsync => s_pix_hsync,
      pix_vsync => s_pix_vsync,
      CH7301C_enable_in  => s_pix_de,
      CH7301C_data_out   => ch7301c_data,
      CH7301C_enable_out => ch7301c_de,
      CH7301C_hsync      => ch7301c_hsync,
      CH7301C_vsync      => ch7301c_vsync
    );
  CH7301C_CLK_p <= clk_gen_x2;
  CH7301C_CLK_n <= clk_gen_x2_n;
end generate g_ch7301c_out_enable;

g_ch7301c_out_disable: if CH7301C_OUTPUT_ENABLE = false generate
  ch7301c_clk_p <= '0';
  ch7301c_clk_n <= '0';
  ch7301c_data <= (others => '0');
  ch7301c_de <= '0';
  ch7301c_hsync <= '0';
  ch7301c_vsync <= '0';
end generate g_ch7301c_out_disable;



g_hdmi_out_enable: if HDMI_OUTPUT_ENABLE = true generate
  rgb2dvi_1 : entity rgb2dvi
    generic map(
      kGenerateSerialClk => false
    )
    port map(
      -- DVI 1.0 HDMI video interface
      TMDS_Clk_p => hdmi_clk_p,
      TMDS_Clk_n => hdmi_clk_n,
      TMDS_Data_p => hdmi_data_p,
      TMDS_Data_n => hdmi_data_n,
      
      -- Auxiliary signals 
      aRst => reset_mst, --asynchronous reset; must be reset when RefClk is not within spec
      aRst_n => '0', --asynchronous reset; must be reset when RefClk is not within spec
      
      -- Video in
      vid_pData => s_pix_red & s_pix_blue & s_pix_green,
      vid_pVDE => s_pix_de,
      vid_pHSync => s_pix_hsync,
      vid_pVSync => s_pix_vsync,
      PixelClk => clk_gen_x1,
      SerialClk => clk_gen_x5
   );

  -- output to enable HDMI:
  hdmi_out_en <= clk_gen_locked;
  -- inputs (unused):
  -- hdmi_hpd
  -- hdmi_cec
end generate g_hdmi_out_enable;

g_hdmi_out_disable: if HDMI_OUTPUT_ENABLE = false generate
  hdmi_clk_p <= '0';
  hdmi_clk_n <= '0';
  hdmi_data_p <= (others => '0');
  hdmi_data_n <= (others => '0');
  hdmi_out_en <= '0';
end generate g_hdmi_out_disable;



--As BRAM has 1 cycle delay, the select signals for pixel-multiplexers get 1 cycle delay as well:
process (clk_gen_x2)
begin
  if(clk_gen_x2'event and clk_gen_x2 = '1') then
    data_sel_sel_pic_pix_mux <= video_timing_linebuff_addr(1 downto 0);
    data_sel_sel_ovl_pix_mux <= video_timing_linebuff_addr(3 downto 0);
  end if;
end process;



--clock domain transition: sys->clk_gen_x2
process (clk_gen_x2)
begin
  if(clk_gen_x2'event and clk_gen_x2 = '1') then
    ---- reset transition, also for short impulses:
    reset_detect_0 <= reset_mst_detect;
    reset_detect_clk_gen_x2 <= reset_detect_0;
    
    reset_detect_clk_gen_x2_last <= reset_detect_clk_gen_x2;
    if ( ( reset_detect_clk_gen_x2_last xor reset_detect_clk_gen_x2 ) = '1' ) then
        reset_clk_gen_x2 <= '1';
    else
        reset_clk_gen_x2 <= '0';
    end if;
    ----
    
    ---- generate frame indicator: toggle on change of vsync (-> on vsync active, both low or high)
    vs_det_last <= s_pix_vsync xor c_video_settings(VIDEO_GROUP)(VIDEO_MODE).V_SP;
    if ( ((s_pix_vsync xor c_video_settings(VIDEO_GROUP)(VIDEO_MODE).V_SP) = '0') and (vs_det_last = '1') ) then
        frame_indicator_clk_gen_x2 <= not(frame_indicator_clk_gen_x2);
    end if;
    ----
    
    --
    ovl_en_clk_gen_x2_0 <= s_ovl_en; --ovl_en_clk_mst_0;
    ovl_en_clk_gen_x2 <= ovl_en_clk_gen_x2_0;
    
    ovl_color1_clk_gen_x2_0 <= overlay_color1; --ovl_color1_clk_mst_0;
    ovl_color1_clk_gen_x2 <= ovl_color1_clk_gen_x2_0;
    
    ovl_color2_clk_gen_x2_0 <= overlay_color2; --ovl_color2_clk_mst_0;
    ovl_color2_clk_gen_x2 <= ovl_color2_clk_gen_x2_0;
    
    ovl_color3_clk_gen_x2_0 <= overlay_color3; --ovl_color3_clk_mst_0;
    ovl_color3_clk_gen_x2 <= ovl_color3_clk_gen_x2_0;
  end if;
end process;


--clock domain transition: clk_gen_x2->mst
process (clk_mst)
begin
  if(clk_mst'event and clk_mst = '1') then
    --
    line_indicator_0 <= line_indicator_clk_gen_x2;
    line_indicator_mst <= line_indicator_0;
    --
    frame_indicator_0 <= frame_indicator_clk_gen_x2;
    frame_indicator_mst <= frame_indicator_0;
  end if;
end process;


process (clk_mst)
begin
  if(clk_mst'event and clk_mst = '1') then

    reset_mst_last <= reset_mst;

    if ( reset_mst = '1' ) then

      trigger_frame <= '0';
      trigger_line <= '0';

      -- detect pos'edge of reset to toggle signal, provided to other clock domain
      if ( reset_mst_last = '0' ) then
        reset_mst_detect <= not (reset_mst_detect);
      end if;


    else
      -- Line detect: on change -> generate trigger signal for memcontrol:
      if ( ( line_indicator_mst xor line_indicator_mst_last ) = '1' ) then
        trigger_line <= '1';
      else
        trigger_line <= '0';
      end if;
      line_indicator_mst_last <= line_indicator_mst;

      -- Frame detect: on change -> generate trigger signal for memcontrol:
      if ( ( frame_indicator_mst xor frame_indicator_mst_last ) = '1' ) then
        trigger_frame <= '1';
      else
        trigger_frame <= '0';
      end if;
      frame_indicator_mst_last <= frame_indicator_mst;

    end if;

  end if;
end process;



--clock domain transition: clk_gen_x2->slv
process (clk_slv)
begin
  if(clk_slv'event and clk_slv = '1') then
    line_indicator_slv_0 <= line_indicator_clk_gen_x2;
    line_indicator_slv <= line_indicator_slv_0;

    frame_indicator_slv_0 <= frame_indicator_clk_gen_x2;
    frame_indicator_slv <= frame_indicator_slv_0;
  end if;
end process;


process (clk_slv)
begin
  if(clk_slv'event and clk_slv = '1') then
  
    -- Line detect: on change -> generate line interrupt:
    r_intr_line <= '0';
    if ( ( line_indicator_slv xor line_indicator_slv_last ) = '1' ) then
      r_intr_line <= '1';
    end if;
    line_indicator_slv_last <= line_indicator_slv;

    -- Frame detect: on change -> generate frame interrupt:
    r_intr_frame <= '0';
    if ( ( frame_indicator_slv xor frame_indicator_slv_last ) = '1' ) then
      r_intr_frame <= '1';
    end if;
    frame_indicator_slv_last <= frame_indicator_slv;
  end if;
end process;


intr_line  <= r_intr_line and s_intr_line_en;
intr_frame <= r_intr_frame and s_intr_frame_en;


end RTL;
