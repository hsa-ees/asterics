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
-- Copyright (C) 2016-2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- File:           vears.vhd
-- Entity:         vears
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
-- Author:         Alexander Zoellner, Michael Schaeferling
-- Create Date:    02/01/2016
--
-- Version:  1.0
-- Modified:       * 02/01/2016 by Alexander Zoellner and Michael Schaeferling
--                   - Toplevel module created in order to split VEARS code
--                     from bus access logic (AXI Master/Slave)
--                 * 08/04/2019 by Michael Schaeferling
--                   - Add HDMI (TMDS) output
--                   - Rename DVI to CH7301C as this is the actual device to connect here
--                   - Add generics for output variations
--                   - Add generic for AXI-ACLK input frequency
--                 * 10/04/2019 by Michael Schaeferling
--                   - Rename interface TMDS to HDMI
--                 * 31/05/2019 by Michael Schaeferling
--                   - Remap slave registers
--                 * 12/09/2019 by Michael Schaeferling
--
-- Description:    VEARS top module.
----------------------------------------------------------------------------------


library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;
use IEEE.STD_LOGIC_UNSIGNED.ALL;


library vears;
use vears.AXI_Slave;
use vears.AXI_Master;
use vears.vears_main;


entity vears is
  generic
  (
    C_FAMILY : string := "zynq";

    VIDEO_GROUP : integer := 2; -- default video mode is VGA (640x480@60Hz)
    VIDEO_MODE  : integer := 4;

    COLOR_MODE : integer := 0; -- 0: default color mode is 8bit grayscale

    VGA_OUTPUT_ENABLE : boolean := true;
    VGA_TFT_OUTPUT_ENABLE : boolean := false;
    VGA_COLOR_WIDTH : integer := 8;
    CH7301C_OUTPUT_ENABLE : boolean := false;
    HDMI_OUTPUT_ENABLE : boolean := false;

    -- Parameters of Axi Slave Bus Interface
    --C_S_AXI_ACLK_FREQ_HZ : integer := 100_000_000;
    C_S_AXI_DATA_WIDTH  : integer := 32;
    C_S_AXI_ADDR_WIDTH  : integer := 5;

    -- Parameters of Axi Master Bus Interface
    C_M_AXI_ACLK_FREQ_HZ : integer := 100_000_000;
    C_M_AXI_ADDR_WIDTH  : integer := 32;
    C_M_AXI_DATA_WIDTH  : integer := 32;
    C_MAX_BURST_LEN     : integer := 16;
    C_NATIVE_DATA_WIDTH : integer := 32;
    C_LENGTH_WIDTH      : integer := 12;
    C_ADDR_PIPE_DEPTH   : integer := 1
  );
  port
  (
    ---- Interface to analog Monitor ----
    vga_red   : out std_logic_vector(VGA_COLOR_WIDTH-1 downto 0);
    vga_green : out std_logic_vector(VGA_COLOR_WIDTH-1 downto 0); 
    vga_blue  : out std_logic_vector(VGA_COLOR_WIDTH-1 downto 0);
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
    
    ---- Interrupt sources:
    intr_frame : out std_logic;
    intr_line  : out std_logic;

    -- Bus signals for AXI Slave :
    s_axi_aclk       : in std_logic;
    s_axi_aresetn    : in std_logic;
    s_axi_awaddr     : in std_logic_vector(C_S_AXI_ADDR_WIDTH-1 downto 0);
    s_axi_awprot     : in std_logic_vector(2 downto 0);
    s_axi_awvalid    : in std_logic;
    s_axi_awready    : out std_logic;
    s_axi_wdata      : in std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
    s_axi_wstrb      : in std_logic_vector((C_S_AXI_DATA_WIDTH/8)-1 downto 0);
    s_axi_wvalid     : in std_logic;
    s_axi_wready     : out std_logic;
    s_axi_bresp      : out std_logic_vector(1 downto 0);
    s_axi_bvalid     : out std_logic;
    s_axi_bready     : in std_logic;
    s_axi_araddr     : in std_logic_vector(C_S_AXI_ADDR_WIDTH-1 downto 0);
    s_axi_arprot     : in std_logic_vector(2 downto 0);
    s_axi_arvalid    : in std_logic;
    s_axi_arready    : out std_logic;
    s_axi_rdata      : out std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
    s_axi_rresp      : out std_logic_vector(1 downto 0);
    s_axi_rvalid     : out std_logic;
    s_axi_rready     : in std_logic;
    
    -- Bus signals for AXI Master:  
    m_axi_aclk       : in  std_logic;
    m_axi_aresetn    : in  std_logic;
    md_error         : out std_logic;
    m_axi_arready    : in  std_logic;
    m_axi_arvalid    : out std_logic;
    m_axi_araddr     : out std_logic_vector(C_M_AXI_ADDR_WIDTH-1 downto 0);
    m_axi_arlen      : out std_logic_vector(7 downto 0);
    m_axi_arsize     : out std_logic_vector(2 downto 0);
    m_axi_arburst    : out std_logic_vector(1 downto 0);
    m_axi_arprot     : out std_logic_vector(2 downto 0);
    m_axi_arcache    : out std_logic_vector(3 downto 0);
    m_axi_rready     : out std_logic;
    m_axi_rvalid     : in  std_logic;
    m_axi_rdata      : in  std_logic_vector(C_M_AXI_DATA_WIDTH-1 downto 0);
    m_axi_rresp      : in  std_logic_vector(1 downto 0);
    m_axi_rlast      : in  std_logic;
    m_axi_awready    : in  std_logic;
    m_axi_awvalid    : out std_logic;
    m_axi_awaddr     : out std_logic_vector(C_M_AXI_ADDR_WIDTH-1 downto 0);
    m_axi_awlen      : out std_logic_vector(7 downto 0);
    m_axi_awsize     : out std_logic_vector(2 downto 0);
    m_axi_awburst    : out std_logic_vector(1 downto 0);
    m_axi_awprot     : out std_logic_vector(2 downto 0);
    m_axi_awcache    : out std_logic_vector(3 downto 0);
    m_axi_wready     : in  std_logic;
    m_axi_wvalid     : out std_logic;
    m_axi_wdata      : out std_logic_vector(C_M_AXI_DATA_WIDTH-1 downto 0);
    m_axi_wstrb      : out std_logic_vector((C_M_AXI_DATA_WIDTH)/8 - 1 downto 0);
    m_axi_wlast      : out std_logic;
    m_axi_bready     : out std_logic;
    m_axi_bvalid     : in  std_logic;
    m_axi_bresp      : in  std_logic_vector(1 downto 0)
  );

  attribute MAX_FANOUT : string;
  attribute SIGIS : string;
  attribute MAX_FANOUT of s_axi_aclk    : signal is "10000";
  attribute MAX_FANOUT of s_axi_aresetn : signal is "10000";
  attribute SIGIS of s_axi_aclk    : signal is "Clk";
  attribute SIGIS of s_axi_aresetn : signal is "Rst";

--  attribute MAX_FANOUT of m_axi_aclk    : signal is "10000";
--  attribute MAX_FANOUT of m_axi_aresetn : signal is "10000";
--  attribute SIGIS of m_axi_aclk    : signal is "Clk";
--  attribute SIGIS of m_axi_aresetn : signal is "Rst";

end entity vears;

------------------------------------------------------------------------------
-- Architecture section
------------------------------------------------------------------------------

architecture IMP of vears is

  -- AXI Master Memory Access:  
  signal axi_mst_mem_go          : std_logic;
  signal axi_mst_mem_clr_go      : std_logic;
  signal axi_mst_mem_busy        : std_logic;
  signal axi_mst_mem_done        : std_logic;
  signal axi_mst_mem_error       : std_logic;
  signal axi_mst_mem_timeout     : std_logic;
  signal axi_mst_mem_rd_req      : std_logic;
  signal axi_mst_mem_wr_req      : std_logic;
  signal axi_mst_mem_bus_lock    : std_logic;
  signal axi_mst_mem_burst       : std_logic;
  signal axi_mst_mem_addr        : std_logic_vector(31 downto 0);
  signal axi_mst_mem_be          : std_logic_vector(15 downto 0);
  signal axi_mst_mem_xfer_length : std_logic_vector(11 downto 0);
  signal axi_mst_mem_in_en       : std_logic;
  signal axi_mst_mem_in_data     : std_logic_vector(C_NATIVE_DATA_WIDTH-1 downto 0);
  signal axi_mst_mem_out_en      : std_logic;
  signal axi_mst_mem_out_data    : std_logic_vector(C_NATIVE_DATA_WIDTH-1 downto 0);
  
  signal s_reset_mst : std_logic;
  
  signal slv_reg0 : std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
  signal slv_reg1 : std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
  signal slv_reg2 : std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
  signal slv_reg3 : std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
  signal slv_reg4 : std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
  signal slv_reg5 : std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
  signal slv_reg6 : std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
  signal slv_reg7 : std_logic_vector(C_S_AXI_DATA_WIDTH-1 downto 0);
  
  signal vga_red_i   : std_logic_vector(7 downto 0);
  signal vga_green_i : std_logic_vector(7 downto 0);
  signal vga_blue_i  : std_logic_vector(7 downto 0);
  
  
begin


  AXI_Slave_inst : entity AXI_Slave
    generic map (
        C_S_AXI_DATA_WIDTH => C_S_AXI_DATA_WIDTH,
        C_S_AXI_ADDR_WIDTH => C_S_AXI_ADDR_WIDTH
    )
    port map (
        S_AXI_ACLK      => s_axi_aclk,
        S_AXI_ARESETN   => s_axi_aresetn,
        S_AXI_AWADDR    => s_axi_awaddr,
        S_AXI_AWPROT    => s_axi_awprot,
        S_AXI_AWVALID   => s_axi_awvalid,
        S_AXI_AWREADY   => s_axi_awready,
        S_AXI_WDATA     => s_axi_wdata,
        S_AXI_WSTRB     => s_axi_wstrb,
        S_AXI_WVALID    => s_axi_wvalid,
        S_AXI_WREADY    => s_axi_wready,
        S_AXI_BRESP     => s_axi_bresp,
        S_AXI_BVALID    => s_axi_bvalid,
        S_AXI_BREADY    => s_axi_bready,
        S_AXI_ARADDR    => s_axi_araddr,
        S_AXI_ARPROT    => s_axi_arprot,
        S_AXI_ARVALID   => s_axi_arvalid,
        S_AXI_ARREADY   => s_axi_arready,
        S_AXI_RDATA     => s_axi_rdata,
        S_AXI_RRESP     => s_axi_rresp,
        S_AXI_RVALID    => s_axi_rvalid,
        S_AXI_RREADY    => s_axi_rready,
        
        slv_reg_0 => slv_reg0,
        slv_reg_1 => slv_reg1,
        slv_reg_2 => slv_reg2,
        slv_reg_3 => slv_reg3,
        slv_reg_4 => slv_reg4,
        slv_reg_5 => slv_reg5,
        slv_reg_6 => slv_reg6,
        slv_reg_7 => slv_reg7
    );


  AXI_Master_inst : entity AXI_Master
    generic map (
        C_FAMILY                 => C_FAMILY,
        C_M_AXI_ADDR_WIDTH       => C_M_AXI_ADDR_WIDTH,
        C_M_AXI_DATA_WIDTH       => C_M_AXI_DATA_WIDTH,
        C_MAX_BURST_LEN          => C_MAX_BURST_LEN,
        C_NATIVE_DATA_WIDTH      => C_NATIVE_DATA_WIDTH,
        C_LENGTH_WIDTH           => C_LENGTH_WIDTH,
        C_ADDR_PIPE_DEPTH        => C_ADDR_PIPE_DEPTH
    )
    port map (
        m_axi_aclk               => m_axi_aclk,
        m_axi_aresetn            => m_axi_aresetn,
        md_error                 => md_error,
        m_axi_arready            => m_axi_arready,
        m_axi_arvalid            => m_axi_arvalid,
        m_axi_araddr             => m_axi_araddr,
        m_axi_arlen              => m_axi_arlen,
        m_axi_arsize             => m_axi_arsize,
        m_axi_arburst            => m_axi_arburst,
        m_axi_arprot             => m_axi_arprot,
        m_axi_arcache            => m_axi_arcache,
        m_axi_rready             => m_axi_rready,
        m_axi_rvalid             => m_axi_rvalid,
        m_axi_rdata              => m_axi_rdata,
        m_axi_rresp              => m_axi_rresp,
        m_axi_rlast              => m_axi_rlast,
        m_axi_awready            => m_axi_awready,
        m_axi_awvalid            => m_axi_awvalid,
        m_axi_awaddr             => m_axi_awaddr,
        m_axi_awlen              => m_axi_awlen,
        m_axi_awsize             => m_axi_awsize,
        m_axi_awburst            => m_axi_awburst,
        m_axi_awprot             => m_axi_awprot,
        m_axi_awcache            => m_axi_awcache,
        m_axi_wready             => m_axi_wready,
        m_axi_wvalid             => m_axi_wvalid,
        m_axi_wdata              => m_axi_wdata,
        m_axi_wstrb              => m_axi_wstrb,
        m_axi_wlast              => m_axi_wlast,
        m_axi_bready             => m_axi_bready,
        m_axi_bvalid             => m_axi_bvalid,
        m_axi_bresp              => m_axi_bresp,

        ----- Master Control signals -----       
        mem_go          => axi_mst_mem_go,
        mem_clr_go      => axi_mst_mem_clr_go,
        mem_busy        => axi_mst_mem_busy,
        mem_done        => axi_mst_mem_done,
        mem_error       => axi_mst_mem_error,
        mem_timeout     => axi_mst_mem_timeout,
        
        mem_rd_req      => axi_mst_mem_rd_req,
        mem_wr_req      => axi_mst_mem_wr_req,
        mem_bus_lock    => axi_mst_mem_bus_lock,
        mem_burst       => axi_mst_mem_burst,
        mem_addr        => axi_mst_mem_addr,
        mem_be          => axi_mst_mem_be,
        mem_xfer_length => axi_mst_mem_xfer_length,
        
        mem_in_en       => axi_mst_mem_in_en,
        mem_in_data     => axi_mst_mem_in_data,
        
        mem_out_en      => axi_mst_mem_out_en,
        mem_out_data    => axi_mst_mem_out_data
    );


s_reset_mst <= not(m_axi_aresetn);

  vears_main_inst : entity vears_main
    generic map (
      CLK_MST_FREQ_HZ => C_M_AXI_ACLK_FREQ_HZ,
      
      VIDEO_GROUP => VIDEO_GROUP,
      VIDEO_MODE  => VIDEO_MODE,
      COLOR_MODE => COLOR_MODE,
      VGA_OUTPUT_ENABLE => VGA_OUTPUT_ENABLE,
      VGA_TFT_OUTPUT_ENABLE => VGA_TFT_OUTPUT_ENABLE,  
      CH7301C_OUTPUT_ENABLE => CH7301C_OUTPUT_ENABLE,
      HDMI_OUTPUT_ENABLE => HDMI_OUTPUT_ENABLE
    )
    port map (
      clk_mst    => m_axi_aclk,
      reset_mst  => s_reset_mst,

      clk_slv    => s_axi_aclk,

      vga_red   => vga_red_i,
      vga_green => vga_green_i,
      vga_blue  => vga_blue_i,

      vga_hsync => vga_hsync,
      vga_vsync => vga_vsync,

      tft_vga_dclk => tft_vga_dclk,
      tft_vga_enb  => tft_vga_enb,

      ch7301c_clk_p => ch7301c_clk_p,
      ch7301c_clk_n => ch7301c_clk_n,
      ch7301c_data  => ch7301c_data,
      ch7301c_de    => ch7301c_de,
      ch7301c_hsync => ch7301c_hsync,
      ch7301c_vsync => ch7301c_vsync,

      hdmi_clk_p  => hdmi_clk_p,
      hdmi_clk_n  => hdmi_clk_n,
      hdmi_data_p => hdmi_data_p,
      hdmi_data_n => hdmi_data_n,
      hdmi_out_en => hdmi_out_en,
      hdmi_hpd    => hdmi_hpd,
      hdmi_cec    => hdmi_cec,

      intr_frame => intr_frame,
      intr_line  => intr_line,
      
      ---- Parameter and Control signals -----
      control => slv_reg0,
      status  => slv_reg1,
      image_baseaddress => slv_reg2,
      overlay_baseaddress => slv_reg3,
      overlay_color1 => slv_reg4(23 downto 0),
      overlay_color2 => slv_reg5(23 downto 0),
      overlay_color3 => slv_reg6(23 downto 0),

      ----- Master Control signals -----       
      mem_go          => axi_mst_mem_go,
      mem_clr_go      => axi_mst_mem_clr_go,
      mem_busy        => axi_mst_mem_busy,
      mem_done        => axi_mst_mem_done,
      mem_error       => axi_mst_mem_error,
      mem_timeout     => axi_mst_mem_timeout,

      mem_rd_req      => axi_mst_mem_rd_req,
      mem_wr_req      => axi_mst_mem_wr_req,
      mem_bus_lock    => axi_mst_mem_bus_lock,
      mem_burst       => axi_mst_mem_burst,
      mem_addr        => axi_mst_mem_addr,
      mem_be          => axi_mst_mem_be,
      mem_xfer_length => axi_mst_mem_xfer_length,

      mem_in_en       => axi_mst_mem_in_en,
      mem_in_data     => axi_mst_mem_in_data,

      mem_out_en      => axi_mst_mem_out_en,
      mem_out_data    => axi_mst_mem_out_data
    );


  vga_red  (VGA_COLOR_WIDTH-1 downto 0) <= vga_red_i  (7 downto 8-VGA_COLOR_WIDTH);
  vga_green(VGA_COLOR_WIDTH-1 downto 0) <= vga_green_i(7 downto 8-VGA_COLOR_WIDTH);
  vga_blue (VGA_COLOR_WIDTH-1 downto 0) <= vga_blue_i (7 downto 8-VGA_COLOR_WIDTH);


end IMP;
