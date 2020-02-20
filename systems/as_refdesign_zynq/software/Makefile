##--------------------------------------------------------------------
## This file is part of the ASTERICS Framework.
## Copyright (C) Hochschule Augsburg, University of Applied Sciences
##--------------------------------------------------------------------
## File:     software/Makefile
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
## demo software project.
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

# Force using 'bash' as Linux distributions nowadays prefer 'dash' which doesn't know 'source' (used below)
SHELL:=/bin/bash


HW_PROJ_DIR=../hardware/build/

APP_NAME=asterics_demo
APP_EXECUTABLE=$(APP_NAME)/executable.elf


all: build_project


# Generate the application project (based on the hello-world template):
generate_project: $(APP_NAME)
$(APP_NAME):
	ln -sf $(HW_PROJ_DIR)system.runs/impl_1/design_1_wrapper.sysdef system.hdf
	ln -sf $(HW_PROJ_DIR)system.runs/impl_1/design_1_wrapper.bit system.bit
	ees-swtool -a system.hdf $(APP_NAME) hello_world && \
	cd $(APP_NAME) && \
	rm -rf hello_world_bsp/ helloworld.c && \
	ln -s ../asterics-demo.c $(APP_NAME).c && \
	ees-swtool -b ../system.hdf $(APP_NAME)_bsp ../../vivado_cores/ && \
	sed -i.bak s/hello_world_bsp/$(APP_NAME)_bsp/g Makefile && \
	sed -i.bak s/'_SIZE : 0x2000'/'_SIZE : 0x2000000'/g lscript.ld


# Build the executable (sourcing '$EES_VIVADO_SETTINGS' is needed as it provides Xilinx' arm-gcc):
build_project: $(APP_EXECUTABLE)
$(APP_EXECUTABLE): $(APP_NAME) $(APP_NAME)/$(APP_NAME).c
	@echo -e "###########################################################################"; \
	echo -e "#"; \
	echo -e "#          Build application ..."; \
	echo -e "#"; \
	echo -e "###########################################################################"
	cd $(APP_NAME) && \
	source $${EES_VIVADO_SETTINGS} && \
	make


program: $(APP_EXECUTABLE)
	ees-program -b system.bit -r system.hdf $(APP_EXECUTABLE)


clean:
	rm -rf $(APP_NAME) system.hdf system.bit
