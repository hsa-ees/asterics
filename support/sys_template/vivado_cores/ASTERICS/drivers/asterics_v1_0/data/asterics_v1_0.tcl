##############################################################################
## Filename:          ./drivers/asterics_v1_0/data/asterics_v1_0.tcl
## Description:       Microprocessor Driver Command (tcl)
## Date:              Fri May 30 13:37:28 2014 (by Create and Import Peripheral Wizard)
##############################################################################

#uses "xillib.tcl"

proc generate {drv_handle} {
  xdefine_include_file $drv_handle "xparameters.h" "asterics" "NUM_INSTANCES" "DEVICE_ID" "C_BASEADDR" "C_HIGHADDR" 
}
