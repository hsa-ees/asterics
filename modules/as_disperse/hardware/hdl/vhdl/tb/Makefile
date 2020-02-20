##--------------------------------------------------------------------
## This file is part of the ASTERICS Framework.
## Copyright (C) Hochschule Augsburg, University of Applied Sciences
##--------------------------------------------------------------------
## File:     as_disperse/[...]/tb/Makefile
##
## Company:  Efficient Embedded Systems Group
##           University of Applied Sciences, Augsburg, Germany
##           http://ees.hs-augsburg.de
##
## Author:   Julian Sarcher, Alexander Zoellner
## Date:     2018-01-17
## Modified: 
##
## Description:
## Makefile for the as_disperse testbench
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


TB = as_disperse_tb
SRCS = ../../../../../as_misc/hardware/hdl/vhdl/pkg/helpers.vhd ../../../../../as_misc/hardware/hdl/vhdl/ram/ram.vhd ../../../../../as_misc/hardware/hdl/vhdl/pkg/as_sim_ram_pkg.vhd ../../../../../as_reader_writer/hardware/hdl/vhdl/sim/as_sim_image_writer.vhd ../../../../../as_misc/hardware/hdl/vhdl/fifo/fifo_fwft.vhd ../as_disperse.vhd as_disperse_tb.vhd

MODULES = ../../../../..
C_READER_SRCS = read_byte.c
C_WRITER_SRCS = write_byte.c

C_SRCS = $(C_READER_SRCS) $(C_WRITER_SRCS)
C_OBJS = ${C_SRCS:.c=.o}

C_READER_PATH = $(MODULES)/as_reader_writer/hardware/hdl/vhdl/sim/
C_WRITER_PATH = $(MODULES)/as_reader_writer/hardware/hdl/vhdl/sim/

all: main

main:
	mkdir -p build
	gcc -Wall -c $(C_READER_PATH)$(C_READER_SRCS) $(C_WRITER_PATH)$(C_WRITER_SRCS)
	ar ruv libsim.a $(C_OBJS)
	$(CC) -a --std=08 --workdir=$(WORK_DIR) $(SRCS)
	$(CC) -e --std=08 -Wl,-L. -Wl,-lsim --workdir=$(WORK_DIR) $(TB)

sim: main
	$(CC) -r --std=08 --workdir=$(WORK_DIR) $(TB) --wave=$(WORK_DIR)$(TB).ghw

wave:
	$(WAVE) --save=save.gtkw build/$(TB).ghw
clean:
	rm -rf build/
	rm -rf *.o
	rm -rf *.a
	rm -rf $(TB)
	rm -rf images/*.raw
	rm -rf images/*.png
	rm -rf images/*.pgm
