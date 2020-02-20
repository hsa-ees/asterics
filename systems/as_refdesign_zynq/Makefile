##--------------------------------------------------------------------
## This file is part of the ASTERICS Framework.
## Copyright (C) Hochschule Augsburg, University of Applied Sciences
##--------------------------------------------------------------------
## File:     Makefile
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
## Main makefile for the ASTERICS demo system.
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

# Set the board here:
BOARD=zybo

# Set the ASTERICS reference design here:
ASTERICS_DESIGN=image_differencing

DIR_ASTERICS_CORE=asterics_core
DIR_VIVADO_CORES=vivado_cores


# The lazy target: 
# Do everything automatically, no more interaction needed.
# Just make sure to connect the board, as it will be programmed right after hardware and software are built.
.PHONY: all
all: build_and_run


# Generate a general ASTERICS core using "as_automatics":
.PHONY: asterics_core
asterics_core:
	rm -rf ${DIR_ASTERICS_CORE} && mkdir -p ${DIR_ASTERICS_CORE} && \
	python3 asterics/${ASTERICS_DESIGN}/asterics-gen.py core ./${DIR_ASTERICS_CORE}


# Generate the ASTERICS IP core for Xilinx Vivado using "as_automatics"
# and populate the software reference implementation:
.PHONY: asterics_vivado_cores
asterics_vivado_cores:
	rm -rf ${DIR_VIVADO_CORES} && mkdir -p ${DIR_VIVADO_CORES} && \
	python3 asterics/${ASTERICS_DESIGN}/asterics-gen.py vivado ./${DIR_VIVADO_CORES} && \
	cp asterics/${ASTERICS_DESIGN}/asterics-demo.c software/


# build the whole demo system (hardware + software)
.PHONY: build_system
build_system:
	# Generate and build the system (hardware + software):
	cd hardware/ && \
	make BOARD=${BOARD}
	cd software/ && \
	make


# run the demo on the board:
.PHONY: run
run:
	cd software/ && \
	make program


.PHONY: build_and_run
build_and_run:
	make asterics_vivado_cores && \
	make build_system && \
	make run



.PHONY: clean
clean:
	# clean vivado_cores and demo software:
	rm -rf ${DIR_ASTERICS_CORE}
	rm -rf ${DIR_VIVADO_CORES}
	rm -f as_automatics.log
	rm -f software/asterics-demo.c
	# clean hardware:
	cd hardware/ && \
	make clean && \
	cd -
	# clean software:
	cd software/ && \
	make clean && \
	cd -
