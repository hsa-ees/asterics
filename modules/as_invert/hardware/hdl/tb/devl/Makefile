##--------------------------------------------------------------------
## This file is part of the ASTERICS Framework.
## Copyright (C) Hochschule Augsburg, University of Applied Sciences
##--------------------------------------------------------------------
## File:     as_invert/[...]/devl/tb/Makefile
##
## Company:  Efficient Embedded Systems Group
##           University of Applied Sciences, Augsburg, Germany
##           http://ees.hs-augsburg.de
##
## Author:   Michael Schaeferling
## Date:     
## Modified: 
##
## Description:
## Makefile for the as_invert testbench
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


# == User Configuration ===========================

# Set input png image and dimensions:
IMG_INFILE_PNG = images/test_images/lenna_640x480_gray.png
IMG_INFILE_WIDTH = 640
IMG_INFILE_HEIGHT = 480

# Set default simulation environment:
DEFAULT_SIM = sim-ghdl
#DEFAULT_SIM = sim-ise

# Set ISE_ISIM_GUI to '-gui' if waveform generation is needed (e.g. needed for target 'sim-ise-view'):
ISE_ISIM_GUI = -gui
#ISE_ISIM_GUI = 

# -- Software reference:
SW_REF_DIR = ../../../model/python/
SW_REF = $(SW_REF_DIR)ref_wrapper.py

# =================================================




# == Internal Configuration =======================

# -- Import list of involved HDL files:
include hdl_files.mk


# -- General HDL settings:
TOP_MODULE=as_sim_top


# -- GHDL settings:
GHDL_DIR = ghdl/
GHDL_EXEC = $(TOP_MODULE)
GHDL_EXEC_PATH = $(GHDL_DIR)$(TOP_MODULE)
GHDL_WAVEFILE = waveout.ghw
GHDL_WAVEFILE_PATH = $(GHDL_DIR)$(GHDL_WAVEFILE)
GHDL_HDL_FILES=$(shell grep HDL_FILES= hdl_files.mk | sed -n '/HDL_FILES=/s/HDL_FILES=//p' | sed 's/ *$$//' | sed 's/^/\.\.\//' | sed 's/\ /\ \.\.\//g')
GTKWAVE_SAVEFILE = asterics_sim.gtkw

# -- Xilinx ISIM settings:
XILINX_ENV=/opt/Xilinx/Xilinx_ISE_settings.sh
ISE_DIR = ise/
ISE_ISIM_PRJ  = $(TOP_MODULE)_isim_beh.prj
ISE_ISIM_CMD  = $(TOP_MODULE)_isim_beh_cmdline.cmd
ISE_ISIM_WCFG = $(TOP_MODULE)_isim_beh.wcfg
ISE_ISIM_WDB  = $(TOP_MODULE)_isim_beh.wdb
ISE_ISIM_WDB_PATH = $(ISE_DIR)$(ISE_ISIM_WDB)
ISE_ISIM_EXEC = $(TOP_MODULE)_isim_beh.exe
ISE_ISIM_EXEC_PATH = $(ISE_DIR)$(ISE_ISIM_EXEC)


# -- Image settings:
IMG_DIR = images/
IMG_INFILE_CSV = $(IMG_DIR)img_in.csv
IMG_OUTFILE_HW_CSV = $(IMG_DIR)img_out_hw.csv
IMG_OUTFILE_SW_CSV = $(IMG_DIR)img_out_sw.csv

IMG_CSV_DELIMITER = ;

IMG_CSVs = $(IMG_INFILE_CSV) $(IMG_OUTFILE_HW_CSV) $(IMG_OUTFILE_SW_CSV)
IMG_PNGs = $(IMG_CSVs:.csv=.png)

# -- Python image preparation scripts:
PY_SCRIPT_DIR = images/scripts/

# =================================================



# Default target:
all: images



#----- GHDL Simulation -----

sim-ghdl: $(IMG_INFILE_CSV) $(GHDL_EXEC_PATH)
	cd $(GHDL_DIR) ; \
	./$(TOP_MODULE) --wave=$(GHDL_WAVEFILE) ; \
	cd -
	
$(GHDL_EXEC_PATH): $(HDL_FILES)
	cd $(GHDL_DIR) ; \
	ghdl -a $(GHDL_HDL_FILES) ; \
	ghdl -e $(TOP_MODULE) ; \
	cd -

$(GHDL_WAVEFILE_PATH): $(IMG_INFILE_CSV) $(HDL_FILES)
	$(MAKE) sim-ghdl
	
sim-ghdl-view: $(GHDL_WAVEFILE_PATH)
	cd $(GHDL_DIR) ; \
	gtkwave -f $(GHDL_WAVEFILE) -a $(GTKWAVE_SAVEFILE)

clean-ghdl:
	cd $(GHDL_DIR) ; \
	rm -rf $(TOP_MODULE) *.ghw *.o *.cf; \
	cd -


#----- Xilinx ISE Simulation -----

sim-ise: $(IMG_INFILE_CSV) $(ISE_ISIM_EXEC_PATH)
	source ${XILINX_ENV} ; \
	cd $(ISE_DIR) ; \
	./$(ISE_ISIM_EXEC) -intstyle ise -tclbatch $(ISE_ISIM_CMD) -wdb $(ISE_ISIM_WDB) -view $(ISE_ISIM_WCFG) $(ISE_ISIM_GUI); \
	cd -

$(ISE_ISIM_EXEC_PATH): $(HDL_FILES)
	source ${XILINX_ENV} ; \
	cd $(ISE_DIR) ; \
	fuse -intstyle ise -incremental -o $(ISE_ISIM_EXEC) -prj $(ISE_ISIM_PRJ) work.as_sim_top -generic_top "GEN_FILE_IN_NAME=../$(IMG_INFILE_CSV)" -generic_top "GEN_FILE_IN_WIDTH=$(IMG_INFILE_WIDTH)" -generic_top "GEN_FILE_IN_HEIGHT=$(IMG_INFILE_HEIGHT)"  -generic_top "GEN_FILE_OUT_NAME=../$(IMG_OUTFILE_HW_CSV)" -generic_top "GEN_DELIMITER='$(IMG_CSV_DELIMITER)'"; \
	cd -

$(ISE_ISIM_WDB_PATH): $(IMG_INFILE_CSV) $(ISE_ISIM_EXEC_PATH) $(HDL_FILES)
	$(MAKE) sim-ise

sim-ise-view: $(ISE_ISIM_WDB_PATH)
	source ${XILINX_ENV} ; \
	cd $(ISE_DIR) ; \
	isimgui -view $(ISE_ISIM_WCFG) ; \
	cd -

clean-ise: 
	cd $(ISE_DIR) ; \
	rm -rf *.exe *.wdb *log *.txt *.csv *.xmsgs *.html *.xst *.ncd *.ngr *.ngc *.ngd *.ngm *.pad *.par *.pcf *.twr *.twx *.ptwx *.map *.mrp *.unroutes *.bld *.xrpt *.lso *.syr *.stx *.xml *.xpi *.ini fuseRelaunch.cmd isim _ngo _xmsgs xlnx_auto_0_xdb xst iseconfig ; \
	cd -


#----- General (generate and show input and output files) -----

# Hardware generates output file:
$(IMG_OUTFILE_HW_CSV) : $(IMG_INFILE_CSV) $(HDL_FILES)
	$(MAKE) $(DEFAULT_SIM)

# Software generates output files (as reference):
$(IMG_OUTFILE_SW_CSV) $(IMG_OUTFILE_SW_CSV:.csv=.png) : $(IMG_INFILE_PNG) $(SW_REF)
	python $(SW_REF) -i $(IMG_INFILE_PNG) -o $(@:.csv=.png)
	python $(PY_SCRIPT_DIR)image2csv.py -i $(@:.csv=.png) -o $(@:.png=.csv) -d "$(IMG_CSV_DELIMITER)"
	
clean-software:
	rm -f $(SW_REF_DIR)*.pyc

#----- Helpers -----

$(IMG_INFILE_CSV) : $(IMG_INFILE_PNG)
	python $(PY_SCRIPT_DIR)image2csv.py -i $< -o $@ -d "$(IMG_CSV_DELIMITER)"

%.png : %.csv
	python $(PY_SCRIPT_DIR)csv2image.py -i $< -o $@ -d "$(IMG_CSV_DELIMITER)"

#----- Targets to call -----

images: $(IMG_PNGs)

view: $(IMG_PNGs)
	python $(PY_SCRIPT_DIR)display_image.py $^

test: $(IMG_OUTFILE_HW_CSV) $(IMG_OUTFILE_SW_CSV)
	diff --brief $(IMG_OUTFILE_HW_CSV) $(IMG_OUTFILE_SW_CSV)

clean-images: 
	rm -f $(IMG_CSVs) $(IMG_PNGs)

clean: clean-ghdl clean-ise clean-software clean-images
