# --------------------------------------------------------------------------
#  This file is part of the ASTERICS Framework. 
#  (C) 2020 Hochschule Augsburg, University of Applied Sciences
# --------------------------------------------------------------------------
#
#
# Company:       Hochschule Augsburg, University of Applied Sciences
# Author:        Philip Manke
#
# Modified:       
#
# Description:   Makefile to run the testbench for the module "as_stream_adapter"

# --------------------------------------------------------------------------
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>
# or write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# --------------------------------------------------------------------------

# GHDL needs to be in the PATH environment or 
# this variable needs to point to the executable file for GHDL
GHDL = ghdl
SRC_TB = as_stream_adapter_tb.vhd
SRC_PATH_MISC = ../../../../../as_misc/hardware/hdl/vhdl
SRC_LIBRARY = --work=asterics
SRC_HDL = $(SRC_LIBRARY) $(SRC_PATH_MISC)/pkg/helpers.vhd ../as_stream_adapter.vhd


VHDL_STD = #--std=08
UNIT = as_stream_adapter_tb
ARCH = TB

all: help
	
help:
	@echo Commands: help, check, clean\(_all\),
	@echo           elaborate, simulate, wave, view.
	@echo
	@echo GHDL needs to be in the PATH environment to run this testbench!
	@echo

check_sources:
	$(GHDL) -a $(VHDL_STD) $(SRC_HDL) 

check: check_sources
	$(GHDL) -a $(VHDL_STD) $(SRC_TB) 

elaborate: check
	$(GHDL) -e $(VHDL_STD) $(UNIT) $(ARCH)

simulate: elaborate
	$(GHDL) -r $(VHDL_STD) $(UNIT) $(ARCH) 

wave: elaborate
	$(GHDL) -r $(VHDL_STD) $(UNIT) $(ARCH) --max-stack-alloc=256 --wave=./ghdl/$(UNIT)_$(ARCH).ghw
	gtkwave -a ./ghdl/$(UNIT)_$(ARCH).gtkw ./ghdl/$(UNIT)_$(ARCH).ghw

view:
	gtkwave -a ./ghdl/$(UNIT)_$(ARCH).gtkw ./ghdl/$(UNIT)_$(ARCH).ghw

clean:
	rm -f ghdl/*.ghw *.o 

clean_all: clean
	rm -f ghdl/*
