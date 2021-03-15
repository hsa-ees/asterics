##--------------------------------------------------------------------
## This file is part of the ASTERICS Framework.
## Copyright (C) Hochschule Augsburg, University of Applied Sciences
##--------------------------------------------------------------------
## File:     hardware/Makefile
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
## This makefile provides targets to generate and build the 
## ASTERICS demo hardware project, based on a given blockdesign.
## This makefile is to be called from within the directory where 
## the project is to be built: 
##   usually, within 'as_refdesign_zynq/hardware' call
##   > make -f ./Makefile
##   or just
##   > make
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


BUILD_DIR=./build/
VIVADO_PROJECT=$(BUILD_DIR)system.xpr


.PHONY: all
all: build_project


# The target 'generate_project' calls a board dependent Makefile to 
# generate the appropriate Vivado system
.PHONY: generate_project
generate_project: $(VIVADO_PROJECT)
$(VIVADO_PROJECT):
	make -f boards/${BOARD}/Makefile generate_project



# The target 'build_project' runs the steps to generate a bitfile for a 
# previously generated Vivado project (either "hand-made" using Vivado-GUI
# or the 'generate' target from this Makefile).
.PHONY: build_project
build_project: $(VIVADO_PROJECT)
	( echo "open_project $(VIVADO_PROJECT)"; \
	echo "reset_project"; \
	echo "launch_runs impl_1 -to_step write_bitstream -jobs 4"; \
	echo "wait_on_run impl_1"; \
	echo "close_project"; \
	echo "exit" ) \
	| ees-vivado -mode tcl
	rm -f *.log *.jou


.PHONY: clean
clean:
	rm -rf build build.bd
	rm -rf .Xil vivado*.jou vivado*.log
