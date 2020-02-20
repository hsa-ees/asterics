##--------------------------------------------------------------------
## This file is part of the ASTERICS Framework.
## Copyright (C) Hochschule Augsburg, University of Applied Sciences
##--------------------------------------------------------------------
## File:     as_collect/[...]/tb/Makefile
##
## Company:  Efficient Embedded Systems Group
##           University of Applied Sciences, Augsburg, Germany
##           http://ees.hs-augsburg.de
##
## Author:   Julian Sarcher
## Date:     2014-10-21
## Modified: 
##
## Description:
## Makefile for the as_collect testbench
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


WORK_DIR = build/

CC = ghdl
WAVE = gtkwave


TB = as_collect_tb
SRCS = ../../../../../as_misc/hardware/hdl/vhdl/pkg/helpers.vhd ../../../../../as_misc/hardware/hdl/vhdl/ram/BRAM_READ_FIRST.vhd ../../../../../as_misc/hardware/hdl/vhdl/ram/DUAL_BRAM_READ_FIRST.vhd ../../../../../as_misc/hardware/hdl/vhdl/ram/BRAM_WRITE_FIRST.vhd ../../../../../as_misc/hardware/hdl/vhdl/ram/DUAL_BRAM_READ_WRITE.vhd ../../../../../as_misc/hardware/hdl/vhdl/ram/ram.vhd ../../../../../as_misc/hardware/hdl/vhdl/fifo/fifo_fwft.vhd ../as_collect.vhd as_collect_tb.vhd

all: main

main:
	mkdir -p build
	$(CC) -a --workdir=$(WORK_DIR) $(SRCS)
	$(CC) -e --workdir=$(WORK_DIR) $(TB)

sim: main
	$(CC) -r --workdir=$(WORK_DIR) $(TB) --wave=$(WORK_DIR)$(TB).ghw

wave:
	$(WAVE) --save=save.gtkw build/$(TB).ghw
clean:
	rm -rf build/
	rm -rf *.o
	rm -rf $(TB)
