##--------------------------------------------------------------------
## This file is part of the ASTERICS Framework.
## Copyright (C) Hochschule Augsburg, University of Applied Sciences
##--------------------------------------------------------------------
## File:     image_sensor_ov7670.xdc
##
## Company:  Efficient Embedded Systems Group
##           University of Applied Sciences, Augsburg, Germany
##           http://ees.hs-augsburg.de
##
## Author:   Michael Schaeferling <michael.schaeferling@hs-augsburg.de>
## Date:     2018-08-27
## Modified: 
##
## Description:
## Image Sensor - OV7670 
## 
## Target Board: ZYBO Board
## with Board-Adaptor (v0.3) on Pmod-ports JB and JC 
##
##--------------------------------------------------------------------
##  This program is free software: you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation, either version 3 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License
##  along with this program.  If not, see <http://www.gnu.org/licenses/>.
##--------------------------------------------------------------------


#create_generated_clock -name clk_ov7670_0_refclk [get_pins design_1_i/processing_system7_0/inst/PS7_i/FCLKCLK[2]]
#create_generated_clock -name clk_ov7670_0_refclk [get_ports ov7670_0_refclk]
#create_generated_clock -name clk_ov7670_0_refclk [get_clocks -of_objects [get_ports ov7670_0_refclk]]
#create_clock -name clk_ov7670_0_refclk -period 42.000 [get_ports ov7670_0_refclk];
#set_clock_groups -asynchronous -group [get_clocks -of_objects [get_pins design_1_i/processing_system7_0/inst/PS7_i/FCLKCLK[0]]] -group [get_clocks -of_objects [get_pins design_1_i/processing_system7_0/inst/PS7_i/FCLKCLK[2]]]
#set_clock_groups -asynchronous -group clk_fpga_0 -group clk_ov7670_0_refclk
#set_clock_groups -asynchronous -group clk_fpga_0 -group clk_fpga_2


# Reference clock output
set_property IOSTANDARD LVCMOS33  [get_ports ov7670_0_refclk];
set_property PACKAGE_PIN  T20     [get_ports ov7670_0_refclk];
set_property DRIVE 8              [get_ports ov7670_0_refclk];
set_property SLEW SLOW            [get_ports ov7670_0_refclk];


# Pixel clock
set_property IOSTANDARD LVCMOS33  [get_ports ov7670_0_pixclk];
set_property PACKAGE_PIN  U20     [get_ports ov7670_0_pixclk];
# ov7670_0_pixclk is constrained to 42ns (is 24MHz):
create_clock -name clk_ov7670_0_pixclk -period 42.000 [get_ports ov7670_0_pixclk];
set_property CLOCK_DEDICATED_ROUTE FALSE [get_nets ov7670_0_pixclk];
# Mark this clock and the system clock domain asynchronous:
set_clock_groups -asynchronous -group clk_fpga_0 -group [get_clocks clk_ov7670_0_pixclk]

# Data
set_property IOSTANDARD LVCMOS33  [get_ports {ov7670_0_data}];
set_property PACKAGE_PIN  T10     [get_ports {ov7670_0_data[0]}];
set_property PACKAGE_PIN  U12     [get_ports {ov7670_0_data[1]}];
set_property PACKAGE_PIN  T11     [get_ports {ov7670_0_data[2]}];
set_property PACKAGE_PIN  T12     [get_ports {ov7670_0_data[3]}];
set_property PACKAGE_PIN  W15     [get_ports {ov7670_0_data[4]}];
set_property PACKAGE_PIN  Y14     [get_ports {ov7670_0_data[5]}];
set_property PACKAGE_PIN  V15     [get_ports {ov7670_0_data[6]}];
set_property PACKAGE_PIN  W14     [get_ports {ov7670_0_data[7]}];
#set_input_delay -clock clk_ov7670_0_pixclk 0 [get_ports ov7670_0_data];
set_input_delay -clock clk_ov7670_0_pixclk -min 0.000 [get_ports ov7670_0_data];
set_input_delay -clock clk_ov7670_0_pixclk -max 2.000 [get_ports ov7670_0_data];

# V-Sync
set_property IOSTANDARD LVCMOS33  [get_ports ov7670_0_frame_valid];
set_property PACKAGE_PIN  W20     [get_ports ov7670_0_frame_valid]; 
#set_input_delay -clock clk_ov7670_0_pixclk 0 [get_ports ov7670_0_frame_valid];
set_input_delay -clock clk_ov7670_0_pixclk -min 0.000 [get_ports ov7670_0_frame_valid];
set_input_delay -clock clk_ov7670_0_pixclk -max 2.000 [get_ports ov7670_0_frame_valid];

# H-Sync
set_property IOSTANDARD LVCMOS33  [get_ports ov7670_0_line_valid];
set_property PACKAGE_PIN  V20     [get_ports ov7670_0_line_valid]; 
#set_input_delay -clock clk_ov7670_0_pixclk 0 [get_ports ov7670_0_line_valid];
set_input_delay -clock clk_ov7670_0_pixclk -min 0.000 [get_ports ov7670_0_line_valid];
set_input_delay -clock clk_ov7670_0_pixclk -max 2.000 [get_ports ov7670_0_line_valid];

# Reset
set_property IOSTANDARD LVCMOS33  [get_ports ov7670_0_reset_n];
set_property PACKAGE_PIN  Y19     [get_ports ov7670_0_reset_n];
set_property DRIVE 8              [get_ports ov7670_0_reset_n];
set_property SLEW SLOW            [get_ports ov7670_0_reset_n];
#set_output_delay -clock clk_ov7670_0_pixclk 0 [get_ports ov7670_0_reset_n];
set_output_delay -clock [get_clocks -of_objects [get_pins design_1_i/processing_system7_0/inst/PS7_i/FCLKCLK[0]]] -min -2.000 [get_ports ov7670_0_reset_n];
set_output_delay -clock [get_clocks -of_objects [get_pins design_1_i/processing_system7_0/inst/PS7_i/FCLKCLK[0]]] -max 0.000 [get_ports ov7670_0_reset_n];

# PowerDown
set_property IOSTANDARD LVCMOS33  [get_ports ov7670_0_powerdown];
set_property PACKAGE_PIN  Y18     [get_ports ov7670_0_powerdown];
set_property DRIVE 8              [get_ports ov7670_0_powerdown];
set_property SLEW SLOW            [get_ports ov7670_0_powerdown];
#set_output_delay -clock clk_ov7670_0_pixclk 0 [get_ports ov7670_0_powerdown];
set_output_delay -clock clk_ov7670_0_pixclk -min -2.000 [get_ports ov7670_0_powerdown];
set_output_delay -clock clk_ov7670_0_pixclk -max 0.000 [get_ports ov7670_0_powerdown];


# I2C for sensor configuration
set_property IOSTANDARD LVCMOS33  [get_ports ov7670_0_iic_scl_io];
set_property PACKAGE_PIN  W18     [get_ports ov7670_0_iic_scl_io];
set_property DRIVE 8              [get_ports ov7670_0_iic_scl_io];
set_property SLEW SLOW            [get_ports ov7670_0_iic_scl_io];
#set_property PULLUP true          [get_ports ov7670_0_iic_scl_io];  // pull-up is done externally, using a resistor
set_input_delay  -clock clk_fpga_0 -min  0.000 [get_ports ov7670_0_iic_scl_io];
set_input_delay  -clock clk_fpga_0 -max  1.000 [get_ports ov7670_0_iic_scl_io];
set_output_delay -clock clk_fpga_0 -min -2.000 [get_ports ov7670_0_iic_scl_io];
set_output_delay -clock clk_fpga_0 -max -1.000 [get_ports ov7670_0_iic_scl_io];


set_property IOSTANDARD LVCMOS33  [get_ports ov7670_0_iic_sda_io];
set_property PACKAGE_PIN  W19     [get_ports ov7670_0_iic_sda_io];
set_property DRIVE 8              [get_ports ov7670_0_iic_sda_io];
set_property SLEW SLOW            [get_ports ov7670_0_iic_sda_io];
#set_property PULLUP true          [get_ports ov7670_0_iic_sda_io];  // pull-up is done externally, using a resistor
set_input_delay  -clock clk_fpga_0 -min  0.000 [get_ports ov7670_0_iic_sda_io];
set_input_delay  -clock clk_fpga_0 -max  1.000 [get_ports ov7670_0_iic_sda_io];
set_output_delay -clock clk_fpga_0 -min -2.000 [get_ports ov7670_0_iic_sda_io];
set_output_delay -clock clk_fpga_0 -max -1.000 [get_ports ov7670_0_iic_sda_io];
