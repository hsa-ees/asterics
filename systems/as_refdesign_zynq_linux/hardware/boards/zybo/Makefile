##--------------------------------------------------------------------
## This file is part of the ASTERICS Framework.
## Copyright (C) Hochschule Augsburg, University of Applied Sciences
##--------------------------------------------------------------------
## File:     hardware/boards/zybo/Makefile
##
## Company:  Efficient Embedded Systems Group
##           University of Applied Sciences, Augsburg, Germany
##           http://ees.hs-augsburg.de
##
## Author:   Michael Schaeferling <michael.schaeferling@hs-augsburg.de>
## Date:     2019
## Modified: 
##
## Description:
## This makefile provides a target to generate a ASTERICS demo 
## hardware project, based on a given blockdesign.
## This makefile is to be called from within the directory where 
## the project is to be built: 
##   usually, within 'as_refdesign_zynq/hardware' call
##   > make -f boards/${BOARD}/Makefile generate_project
##
##--------------------------------------------------------------------
##  This program is free software; you can redistribute it and/or
##  modify it under the terms of the GNU Lesser General Public
##  License as published by the Free Software Foundation; either
##  version 3 of the License, or (at your option) any later version.
##  
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
##  Lesser General Public License for more details.
##  
##  You should have received a copy of the GNU Lesser General Public License
##  along with this program; if not, see <http://www.gnu.org/licenses/>
##  or write to the Free Software Foundation, Inc.,
##  51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
##--------------------------------------------------------------------

.PHONY: all
all: generate_project

# The target 'generate_project' generates a Vivado project (.xpr) from 
#   - a given .bd-file and 
#   - a set of additional source files (e.g. constraints)
.PHONY: generate_project
generate_project:
	mkdir build.bd
	ln -s ../boards/zybo/bd/design_1.bd build.bd/design_1.bd
	( echo 'create_project -force system ./build -part xc7z010clg400-1'; \
	echo 'set_property -name "board_part" -value "digilentinc.com:zybo:part0:1.0" -objects [current_project]'; \
	echo 'set_property -name "target_language" -value "VHDL" -objects [current_project]'; \
	echo 'set_property -name "ip_cache_permissions" -value "read write" -objects [current_project]'; \
	echo 'set_property -name "ip_output_repo" -value "build/design_1.cache/ip" -objects [current_project]'; \
	echo 'set_property "ip_repo_paths" "../vivado_cores" [current_fileset]'; \
	echo 'update_ip_catalog -rebuild'; \
	echo 'add_files build.bd/design_1.bd'; \
	echo 'make_wrapper -top [get_files design_1.bd]'; \
	echo 'set_property top design_1_wrapper [current_fileset]'; \
	echo 'add_files build.bd/hdl/design_1_wrapper.vhd'; \
	echo 'add_files ../vivado_cores/VEARS/constraints/zybo/vga.xdc'; \
	echo 'add_files ../vivado_cores/VEARS/constraints/zybo/hdmi.xdc'; \
	echo 'add_files ../vivado_cores/VEARS/constraints/zybo/zybo_timing.xdc' ) \
	| ees-vivado -mode tcl
	rm -f *.log *.jou
