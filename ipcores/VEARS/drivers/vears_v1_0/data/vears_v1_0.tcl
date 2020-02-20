##############################################################################
## Filename:          ./drivers/vears_v1_0/data/vears_v1_0.tcl
## Description:       Microprocessor Driver Command (tcl)
## Date:              Tue May 27 09:35:14 2014 (by Create and Import Peripheral Wizard)
##############################################################################

#uses "xillib.tcl"

proc generate {drv_handle} {
  xdefine_include_file $drv_handle "xparameters.h" "vears" "NUM_INSTANCES" "DEVICE_ID" "C_BASEADDR" "C_HIGHADDR" 
}
