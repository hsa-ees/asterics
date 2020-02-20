# VGA - VEARS
#
# Target Board: ZYBO Board (VGA Connector) 
#
# Author: Michael Schaeferling
# Date:   2018-01-18


create_generated_clock -name clk_vears_x1 [get_pins design_1_i/vears_0/U0/vears_main_inst/clocking_1/ClkGen_1/CLKOUT0]
create_generated_clock -name clk_vears_x5 [get_pins design_1_i/vears_0/U0/vears_main_inst/clocking_1/ClkGen_1/CLKOUT1]
create_generated_clock -name clk_vears_x2 [get_pins design_1_i/vears_0/U0/vears_main_inst/clocking_1/ClkGen_1/CLKOUT2]

set_clock_groups -asynchronous -group { clk_fpga_0 } -group { clk_vears_x2 }
set_clock_groups -asynchronous -group { clk_fpga_1 } -group { clk_vears_x2 }
set_clock_groups -asynchronous -group { clk_vears_x1 } -group { clk_vears_x2 }


set_property  IOSTANDARD LVCMOS33 [get_ports vga_vsync];
set_property  PACKAGE_PIN  R19    [get_ports vga_vsync];
set_output_delay -clock clk_vears_x1 -min -2.000 [get_ports vga_vsync];
set_output_delay -clock clk_vears_x1 -max  0.000 [get_ports vga_vsync];

set_property  IOSTANDARD LVCMOS33 [get_ports vga_hsync];
set_property  PACKAGE_PIN  P19    [get_ports vga_hsync];
set_output_delay -clock clk_vears_x1 -min -2.000 [get_ports vga_hsync];
set_output_delay -clock clk_vears_x1 -max  0.000 [get_ports vga_hsync];

set_property  IOSTANDARD LVCMOS33 [get_ports {vga_blue}];
set_property  PACKAGE_PIN  G19    [get_ports {vga_blue[4]}];
set_property  PACKAGE_PIN  J18    [get_ports {vga_blue[3]}];
set_property  PACKAGE_PIN  K19    [get_ports {vga_blue[2]}];
set_property  PACKAGE_PIN  M20    [get_ports {vga_blue[1]}];
set_property  PACKAGE_PIN  P20    [get_ports {vga_blue[0]}];
set_output_delay -clock clk_vears_x1 -min -2.000 [get_ports vga_blue];
set_output_delay -clock clk_vears_x1 -max  0.000 [get_ports vga_blue];

set_property  IOSTANDARD LVCMOS33 [get_ports {vga_green}];
set_property  PACKAGE_PIN  F20    [get_ports {vga_green[4]}]; # was VGA_GREEN[5]
set_property  PACKAGE_PIN  H20    [get_ports {vga_green[3]}]; # was VGA_GREEN[4]
set_property  PACKAGE_PIN  J19    [get_ports {vga_green[2]}]; # was VGA_GREEN[3]
set_property  PACKAGE_PIN  L19    [get_ports {vga_green[1]}]; # was VGA_GREEN[2]
set_property  PACKAGE_PIN  N20    [get_ports {vga_green[0]}]; # was VGA_GREEN[1]
#set_property  PACKAGE_PIN  H18    [get_ports {vga_green[0]}];
set_output_delay -clock clk_vears_x1 -min -2.000 [get_ports vga_green];
set_output_delay -clock clk_vears_x1 -max  0.000 [get_ports vga_green];

set_property  IOSTANDARD LVCMOS33 [get_ports {vga_red}];
set_property  PACKAGE_PIN  F19    [get_ports {vga_red[4]}];
set_property  PACKAGE_PIN  G20    [get_ports {vga_red[3]}];
set_property  PACKAGE_PIN  J20    [get_ports {vga_red[2]}];
set_property  PACKAGE_PIN  L20    [get_ports {vga_red[1]}];
set_property  PACKAGE_PIN  M19    [get_ports {vga_red[0]}];
set_output_delay -clock clk_vears_x1 -min -2.000 [get_ports vga_red];
set_output_delay -clock clk_vears_x1 -max  0.000 [get_ports vga_red];
