# --------------------------------------------------------------------------
#  This file is part of the ASTERICS Framework. 
#  Copyright (C) Hochschule Augsburg, University of Applied Sciences
# --------------------------------------------------------------------------
#
#
# Company:       Hochschule Augsburg, University of Applied Sciences
# Author:        Philip Manke
#
# Modified:       2017-08-30 Philip Manke
#
# Description:   Makefile to run the testbench for the module "as_iic"

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
SRC_TB = as_edge_tb.vhd
SRC_PATH_MISC = ../../../../../as_misc/hardware/hdl/vhdl
SRC_PATH_FILTER = ../../../../../2dfilter/as_generic_filter_module/hardware/hdl/vhdl
SRC_LIBRARY = --work=asterics
SRC_HDL = $(SRC_LIBRARY) $(SRC_PATH_MISC)/pkg/helpers.vhd $(SRC_PATH_MISC)/pkg/as_generic_filter_pkg.vhd $(SRC_PATH_MISC)/pipeline/as_shift_line.vhd $(SRC_PATH_MISC)/ram/ram.vhd  $(SRC_PATH_MISC)/ram/DUAL_BRAM_READ_FIRST.vhd $(SRC_PATH_MISC)/pipeline/as_fifo.vhd $(SRC_PATH_MISC)/pipeline/as_rec_bram_line_buffer.vhd $(SRC_PATH_MISC)/pipeline/as_pipeline_row.vhd $(SRC_PATH_MISC)/pipeline/as_window_buff_nxm.vhd $(SRC_PATH_MISC)/pipeline/as_generic_filter_module.vhd $(SRC_PATH_MISC)/pipeline/as_pipeline_flush.vhd ../as_edge.vhd
#SRC_HDL = $(SRC_LIBRARY) helpers.vhd as_pipeline_flush.vhd

# as_fifo.vhd
# ram.vhd helpers.vhd
# as_generic_filter_pkg.vhd 

VHDL_STD = #--std=08
UNIT = as_edge_tb
ARCH_QUICK = TB
ARCH_GENERIC = TB

all: help
	
help:
	@echo Commands: help, check, clean\(_all\),
	@echo           elaborate_\(generic/quick\), simulate_\(generic/quick\),
	@echo           wave_\(generic/quick\), wave_nostop_\(generic/quick\).
	@echo
	@echo GHDL needs to be in the PATH environment to run this testbench!
	@echo

check:
	$(GHDL) -a $(VHDL_STD) $(SRC_HDL) 
	$(GHDL) -a $(VHDL_STD) $(SRC_TB) 

elaborate_quick: check
	$(GHDL) -e $(VHDL_STD) $(UNIT) $(ARCH_QUICK)

elaborate_generic: check
	$(GHDL) -e $(VHDL_STD) $(UNIT) $(ARCH_GENERIC)

simulate_quick: elaborate_quick
	$(GHDL) -r $(VHDL_STD) $(UNIT) $(ARCH_QUICK) 

simulate_generic: elaborate_generic
	$(GHDL) -r $(VHDL_STD) $(UNIT) $(ARCH_GENERIC) --assert-level=warning
	
wave_nostop_quick: elaborate_quick
	$(GHDL) -r $(VHDL_STD) $(UNIT) $(ARCH_QUICK) --wave=./ghdl/$(UNIT)_$(ARCH_QUICK).ghw
	gtkwave -a ./ghdl/$(UNIT)_$(ARCH_QUICK).gtkw ./ghdl/$(UNIT)_$(ARCH_QUICK).ghw

wave_nostop_generic: elaborate_generic
	$(GHDL) -r $(VHDL_STD) $(UNIT) $(ARCH_GENERIC) --wave=./ghdl/$(UNIT)_$(ARCH_GENERIC).ghw
	gtkwave -a ./ghdl/$(UNIT)_$(ARCH_GENERIC).gtkw ./ghdl/$(UNIT)_$(ARCH_GENERIC).ghw
#--assert-level=warning
wave_quick: elaborate_quick
	$(GHDL) -r $(VHDL_STD) $(UNIT) $(ARCH_QUICK)  --wave=./ghdl/$(UNIT)_$(ARCH_QUICK).ghw
	gtkwave -a ./ghdl/$(UNIT)_$(ARCH_QUICK).gtkw ./ghdl/$(UNIT)_$(ARCH_QUICK).ghw

wave_generic: elaborate_generic
	$(GHDL) -r $(VHDL_STD) $(UNIT) $(ARCH_GENERIC) --assert-level=warning --wave=./ghdl/$(UNIT)_$(ARCH_GENERIC).ghw
	gtkwave -a ./ghdl/$(UNIT)_$(ARCH_GENERIC).gtkw ./ghdl/$(UNIT)_$(ARCH_GENERIC).ghw

clean:
	rm -f ghdl/*.ghw *.o $(UNIT)*

clean_all: clean
	rm -f ghdl/*
