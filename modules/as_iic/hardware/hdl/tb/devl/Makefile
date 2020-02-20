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
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
# --------------------------------------------------------------------------

# GHDL needs to be in the PATH environment or 
# this variable needs to point to the executable file for GHDL
GHDL = ghdl

SRC_TB = ../vhdl/as_iic_tb.vhd
SRC_HW = ../../vhdl/
SRC_HDL = $(SRC_HW)as_iic.vhd
SRC_LIB = --work=asterics ../../../../../as_misc/hardware/hdl/vhdl/pkg/helpers.vhd

UNIT = as_iic_tb
ARCH_QUICK = testbench_quick
ARCH_GENERIC = testbench_generic

all: help
	
help:
	@echo Commands: help, check, clean\(_all\),
	@echo           elaborate_\(generic/quick\), simulate_\(generic/quick\),
	@echo           wave_\(generic/quick\), wave_nostop_\(generic/quick\).
	@echo
	@echo GHDL needs to be in the PATH environment to run this testbench!
	@echo

check:
	$(GHDL) -a $(SRC_LIB) $(SRC_HDL) 
	$(GHDL) -a $(SRC_TB)

elaborate_quick: check
	$(GHDL) -c $(SRC_LIB) $(SRC_HDL) $(SRC_TB) -e $(UNIT) $(ARCH_QUICK)

elaborate_generic: check
	$(GHDL) -c $(SRC_LIB) $(SRC_HDL) $(SRC_TB) -e $(UNIT) $(ARCH_GENERIC)

simulate_quick: elaborate_quick
	$(GHDL) -r $(UNIT) $(ARCH_QUICK) --assert-level=warning

simulate_generic: elaborate_generic
	$(GHDL) -r $(UNIT) $(ARCH_GENERIC) --assert-level=warning
	
wave_nostop_quick: elaborate_quick
	$(GHDL) -r $(UNIT) $(ARCH_QUICK) --wave=./ghdl/$(UNIT)_$(ARCH_QUICK).ghw
	gtkwave -a ./ghdl/$(UNIT)_$(ARCH_QUICK).gtkw ./ghdl/$(UNIT)_$(ARCH_QUICK).ghw

wave_nostop_generic: elaborate_generic
	$(GHDL) -r $(UNIT) $(ARCH_GENERIC) --wave=./ghdl/$(UNIT)_$(ARCH_GENERIC).ghw
	gtkwave -a ./ghdl/$(UNIT)_$(ARCH_GENERIC).gtkw ./ghdl/$(UNIT)_$(ARCH_GENERIC).ghw

wave_quick: elaborate_quick
	$(GHDL) -r $(UNIT) $(ARCH_QUICK) --assert-level=warning --wave=./ghdl/$(UNIT)_$(ARCH_QUICK).ghw
	gtkwave -a ./ghdl/$(UNIT)_$(ARCH_QUICK).gtkw ./ghdl/$(UNIT)_$(ARCH_QUICK).ghw

wave_generic: elaborate_generic
	$(GHDL) -r $(UNIT) $(ARCH_GENERIC) --assert-level=warning --wave=./ghdl/$(UNIT)_$(ARCH_GENERIC).ghw
	gtkwave -a ./ghdl/$(UNIT)_$(ARCH_GENERIC).gtkw ./ghdl/$(UNIT)_$(ARCH_GENERIC).ghw

clean:
	rm -f ghdl/*.ghw *.o $(UNIT)*

clean_all: clean
	rm -f ghdl/*
