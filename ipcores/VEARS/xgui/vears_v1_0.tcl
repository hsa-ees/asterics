# Definitional proc to organize widgets for parameters.
proc init_gui { IPINST } {

  #ipgui::add_param $IPINST -name "Component_Name"
  #Adding Page
  set Page_0 [ipgui::add_page $IPINST -name "Page 0"]

  # Group "Video Settings"
  set Video_Mode [ipgui::add_group $IPINST -name "Video Settings" -parent ${Page_0}]
  ipgui::add_param $IPINST -name "VIDEO_GROUP" -parent ${Video_Mode}
  ipgui::add_param $IPINST -name "VIDEO_MODE"  -parent ${Video_Mode}
  
  # Group "Color Settings"
  set Color_Mode [ipgui::add_group $IPINST -name "Color Settings" -parent ${Page_0}]
  ipgui::add_param $IPINST -name "COLOR_MODE"  -parent ${Color_Mode}

  # Group "VGA Setup"
  set VGA_Setup [ipgui::add_group $IPINST -name "VGA Setup" -parent ${Page_0} -display_name {VGA Analog Output}]
  ipgui::add_param $IPINST -name "VGA_OUTPUT_ENABLE" -parent ${VGA_Setup}
  ipgui::add_param $IPINST -name "VGA_COLOR_WIDTH" -parent ${VGA_Setup}
  ipgui::add_param $IPINST -name "VGA_TFT_OUTPUT_ENABLE" -parent ${VGA_Setup}

  # Group "HDMI Output"
  set HDMI_Output [ipgui::add_group $IPINST -name "HDMI Output" -parent ${Page_0}]
  ipgui::add_param $IPINST -name "HDMI_OUTPUT_ENABLE" -parent ${HDMI_Output}

  # Group "Chrontel CH7301C Output"
  set Chrontel_CH7301C_Output [ipgui::add_group $IPINST -name "Chrontel CH7301C Output" -parent ${Page_0}]
  ipgui::add_param $IPINST -name "CH7301C_OUTPUT_ENABLE" -parent ${Chrontel_CH7301C_Output}

  # Group "General"
  set General [ipgui::add_group $IPINST -name "General" -parent ${Page_0}]
  ipgui::add_param $IPINST -name "AXI_M_ACLK_FREQ_MHZ" -parent ${General}
  set AXI_M_ACLK_FREQ_MHZ [ipgui::add_param $IPINST -parent ${General} -name AXI_M_ACLK_FREQ_MHZ ]

}


#########################################################
### RSB related procs
##########################################################
#~ proc make_params_auto { IpView paramList } {
   #~ foreach param $paramList {
      #~ set paramhandle [ipgui::get_paramspec $param -of $IpView]
      #~ set dtext [get_property display_name $paramhandle]
      #~ #changing the display text
      #~ set_property display_name "$dtext (Auto)" $paramhandle
      #~ #disabling the parameter
      #~ #set_property visible false $paramhandle
      #~ #locking the parameter enablement, so that no drc enables it
      #~ set_property locked true $paramhandle
   #~ }
#~ }

#~ proc init_xpg_bd { IpView } {
   #~ set params_to_mask "AXI_M_ACLK_FREQ_MHZ"
   #~ make_params_auto $IpView $params_to_mask
#~ }
#########################################################




#########################################################
### PARAM_VALUEs
#########################################################


proc update_PARAM_VALUE.VIDEO_GROUP { PARAM_VALUE.VIDEO_GROUP } {
  # Procedure called to update VIDEO_GROUP when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.VIDEO_GROUP { PARAM_VALUE.VIDEO_GROUP } {
  # Procedure called to validate VIDEO_GROUP
  set vid_grp [get_property value ${PARAM_VALUE.VIDEO_GROUP}] 
  if {($vid_grp < 1) || ($vid_grp > 2)} {
    set_property errmsg "Video Group ID must be 1 or 2. See the manual for supported Video Group / Video Mode combinations." ${PARAM_VALUE.VIDEO_GROUP} 
    return false
  }
  return true
}


proc update_PARAM_VALUE.VIDEO_MODE { PARAM_VALUE.VIDEO_MODE } {
  # Procedure called to update VIDEO_MODE when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.VIDEO_MODE { PARAM_VALUE.VIDEO_MODE PARAM_VALUE.VIDEO_GROUP } {
  # Procedure called to validate VIDEO_MODE
  set vid_grp [get_property value ${PARAM_VALUE.VIDEO_GROUP}] 
  set vid_mode [get_property value ${PARAM_VALUE.VIDEO_MODE}] 
  
  if { (    ( ($vid_grp == 1) && ( ($vid_mode ==  4) || ($vid_mode == 32) || ($vid_mode == 33) || ($vid_mode == 34) ) ) 
         || ( ($vid_grp == 2) && ( ($vid_mode ==  4) || ($vid_mode ==  8) || ($vid_mode == 10) || ($vid_mode == 16) || ($vid_mode == 35) ) ) 
       ) } {
    return true
  }
  set_property errmsg "Invalid Video Group / Video Mode combination. See the manual for supported combinations." ${PARAM_VALUE.VIDEO_MODE} 
  return false
}


proc update_PARAM_VALUE.COLOR_MODE { PARAM_VALUE.COLOR_MODE } {
  # Procedure called to update COLOR_MODE when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.COLOR_MODE { PARAM_VALUE.COLOR_MODE } {
  # Procedure called to validate COLOR_MODE
  set col_mode [get_property value ${PARAM_VALUE.COLOR_MODE}] 
  
  if {($col_mode < 0) || ($col_mode > 1)} {
    set_property errmsg "Color Mode must be 0 (grayscale) or 1 (color)." ${PARAM_VALUE.COLOR_MODE} 
    return false
  }
  return true
}


proc update_PARAM_VALUE.VGA_OUTPUT_ENABLE { PARAM_VALUE.VGA_OUTPUT_ENABLE } {
  # Procedure called to update VGA_OUTPUT_ENABLE when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.VGA_OUTPUT_ENABLE { PARAM_VALUE.VGA_OUTPUT_ENABLE } {
  # Procedure called to validate VGA_OUTPUT_ENABLE
  return true
}


proc update_PARAM_VALUE.VGA_COLOR_WIDTH { PARAM_VALUE.VGA_COLOR_WIDTH } {
  # Procedure called to update VGA_COLOR_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.VGA_COLOR_WIDTH { PARAM_VALUE.VGA_COLOR_WIDTH } {
  # Procedure called to validate VGA_COLOR_WIDTH
  return true
}


proc update_PARAM_VALUE.VGA_TFT_OUTPUT_ENABLE { PARAM_VALUE.VGA_TFT_OUTPUT_ENABLE } {
  # Procedure called to update VGA_TFT_OUTPUT_ENABLE when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.VGA_TFT_OUTPUT_ENABLE { PARAM_VALUE.VGA_TFT_OUTPUT_ENABLE } {
  # Procedure called to validate VGA_TFT_OUTPUT_ENABLE
  return true
}


proc update_PARAM_VALUE.HDMI_OUTPUT_ENABLE { PARAM_VALUE.HDMI_OUTPUT_ENABLE } {
  # Procedure called to update HDMI_OUTPUT_ENABLE when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.HDMI_OUTPUT_ENABLE { PARAM_VALUE.HDMI_OUTPUT_ENABLE } {
  # Procedure called to validate HDMI_OUTPUT_ENABLE
  return true
}


proc update_PARAM_VALUE.CH7301C_OUTPUT_ENABLE { PARAM_VALUE.CH7301C_OUTPUT_ENABLE } {
  # Procedure called to update CH7301C_OUTPUT_ENABLE when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.CH7301C_OUTPUT_ENABLE { PARAM_VALUE.CH7301C_OUTPUT_ENABLE } {
  # Procedure called to validate CH7301C_OUTPUT_ENABLE
  return true
}



#proc validate_PARAM_VALUE.AXI_M_ACLK_FREQ_MHZ { PARAM_VALUE.AXI_M_ACLK_FREQ_MHZ } {
#  # Procedure called to validate AXI_M_ACLK_FREQ_MHZ
#  set axi_clk [get_property value ${PARAM_VALUE.AXI_M_ACLK_FREQ_MHZ}] 
#  set axi_clk_mhz [expr {$axi_clk*1000000} ]
#  if {$axi_clk_mhz = 100000000} {
#    set_property errmsg "AXI clock frequency must be 100 MHz" ${PARAM_VALUE.AXI_M_ACLK_FREQ_MHZ} 
#    return false
#  }
#  return true
#}


proc update_PARAM_VALUE.C_ADDR_PIPE_DEPTH { PARAM_VALUE.C_ADDR_PIPE_DEPTH } {
  # Procedure called to update C_ADDR_PIPE_DEPTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_ADDR_PIPE_DEPTH { PARAM_VALUE.C_ADDR_PIPE_DEPTH } {
  # Procedure called to validate C_ADDR_PIPE_DEPTH
  return true
}

proc update_PARAM_VALUE.C_LENGTH_WIDTH { PARAM_VALUE.C_LENGTH_WIDTH } {
  # Procedure called to update C_LENGTH_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_LENGTH_WIDTH { PARAM_VALUE.C_LENGTH_WIDTH } {
  # Procedure called to validate C_LENGTH_WIDTH
  return true
}

proc update_PARAM_VALUE.C_MAX_BURST_LEN { PARAM_VALUE.C_MAX_BURST_LEN } {
  # Procedure called to update C_MAX_BURST_LEN when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_MAX_BURST_LEN { PARAM_VALUE.C_MAX_BURST_LEN } {
  # Procedure called to validate C_MAX_BURST_LEN
  return true
}

proc update_PARAM_VALUE.C_M_AXI_ADDR_WIDTH { PARAM_VALUE.C_M_AXI_ADDR_WIDTH } {
  # Procedure called to update C_M_AXI_ADDR_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_ADDR_WIDTH { PARAM_VALUE.C_M_AXI_ADDR_WIDTH } {
  # Procedure called to validate C_M_AXI_ADDR_WIDTH
  return true
}

proc update_PARAM_VALUE.C_M_AXI_DATA_WIDTH { PARAM_VALUE.C_M_AXI_DATA_WIDTH } {
  # Procedure called to update C_M_AXI_DATA_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_M_AXI_DATA_WIDTH { PARAM_VALUE.C_M_AXI_DATA_WIDTH } {
  # Procedure called to validate C_M_AXI_DATA_WIDTH
  return true
}

proc update_PARAM_VALUE.C_NATIVE_DATA_WIDTH { PARAM_VALUE.C_NATIVE_DATA_WIDTH } {
  # Procedure called to update C_NATIVE_DATA_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_NATIVE_DATA_WIDTH { PARAM_VALUE.C_NATIVE_DATA_WIDTH } {
  # Procedure called to validate C_NATIVE_DATA_WIDTH
  return true
}

proc update_PARAM_VALUE.C_S_AXI_ADDR_WIDTH { PARAM_VALUE.C_S_AXI_ADDR_WIDTH } {
  # Procedure called to update C_S_AXI_ADDR_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_S_AXI_ADDR_WIDTH { PARAM_VALUE.C_S_AXI_ADDR_WIDTH } {
  # Procedure called to validate C_S_AXI_ADDR_WIDTH
  return true
}

proc update_PARAM_VALUE.C_S_AXI_DATA_WIDTH { PARAM_VALUE.C_S_AXI_DATA_WIDTH } {
  # Procedure called to update C_S_AXI_DATA_WIDTH when any of the dependent parameters in the arguments change
}

proc validate_PARAM_VALUE.C_S_AXI_DATA_WIDTH { PARAM_VALUE.C_S_AXI_DATA_WIDTH } {
  # Procedure called to validate C_S_AXI_DATA_WIDTH
  return true
}




#########################################################
### MODELPARAM_VALUEs
#########################################################


proc update_MODELPARAM_VALUE.VIDEO_GROUP { MODELPARAM_VALUE.VIDEO_GROUP PARAM_VALUE.VIDEO_GROUP } {
  # Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
  set_property value [get_property value ${PARAM_VALUE.VIDEO_GROUP}] ${MODELPARAM_VALUE.VIDEO_GROUP}
}

proc update_MODELPARAM_VALUE.VIDEO_MODE { MODELPARAM_VALUE.VIDEO_MODE PARAM_VALUE.VIDEO_MODE } {
  # Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
  set_property value [get_property value ${PARAM_VALUE.VIDEO_MODE}] ${MODELPARAM_VALUE.VIDEO_MODE}
}

proc update_MODELPARAM_VALUE.COLOR_MODE { MODELPARAM_VALUE.COLOR_MODE PARAM_VALUE.COLOR_MODE } {
  # Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
  set_property value [get_property value ${PARAM_VALUE.COLOR_MODE}] ${MODELPARAM_VALUE.COLOR_MODE}
}

proc update_MODELPARAM_VALUE.VGA_OUTPUT_ENABLE { MODELPARAM_VALUE.VGA_OUTPUT_ENABLE PARAM_VALUE.VGA_OUTPUT_ENABLE } {
  # Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
  set_property value [get_property value ${PARAM_VALUE.VGA_OUTPUT_ENABLE}] ${MODELPARAM_VALUE.VGA_OUTPUT_ENABLE}
}

proc update_MODELPARAM_VALUE.VGA_COLOR_WIDTH { MODELPARAM_VALUE.VGA_COLOR_WIDTH PARAM_VALUE.VGA_COLOR_WIDTH } {
  # Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
  set_property value [get_property value ${PARAM_VALUE.VGA_COLOR_WIDTH}] ${MODELPARAM_VALUE.VGA_COLOR_WIDTH}
}

proc update_MODELPARAM_VALUE.VGA_TFT_OUTPUT_ENABLE { MODELPARAM_VALUE.VGA_TFT_OUTPUT_ENABLE PARAM_VALUE.VGA_TFT_OUTPUT_ENABLE } {
  # Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
  set_property value [get_property value ${PARAM_VALUE.VGA_TFT_OUTPUT_ENABLE}] ${MODELPARAM_VALUE.VGA_TFT_OUTPUT_ENABLE}
}

proc update_MODELPARAM_VALUE.HDMI_OUTPUT_ENABLE { MODELPARAM_VALUE.HDMI_OUTPUT_ENABLE PARAM_VALUE.HDMI_OUTPUT_ENABLE } {
  # Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
  set_property value [get_property value ${PARAM_VALUE.HDMI_OUTPUT_ENABLE}] ${MODELPARAM_VALUE.HDMI_OUTPUT_ENABLE}
}

proc update_MODELPARAM_VALUE.CH7301C_OUTPUT_ENABLE { MODELPARAM_VALUE.CH7301C_OUTPUT_ENABLE PARAM_VALUE.CH7301C_OUTPUT_ENABLE } {
  # Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
  set_property value [get_property value ${PARAM_VALUE.CH7301C_OUTPUT_ENABLE}] ${MODELPARAM_VALUE.CH7301C_OUTPUT_ENABLE}
}




# Map AXI_M_ACLK_FREQ_MHZ to C_M_AXI_ACLK_FREQ_HZ
proc update_MODELPARAM_VALUE.C_M_AXI_ACLK_FREQ_HZ {MODELPARAM_VALUE.C_M_AXI_ACLK_FREQ_HZ PARAM_VALUE.AXI_M_ACLK_FREQ_MHZ} {
  set axi_clk [get_property value ${PARAM_VALUE.AXI_M_ACLK_FREQ_MHZ}]
  set val_clk_Mhz [expr {int($axi_clk*1000000)} ]
  #puts "VEARS <vears_v1_0.tcl>: C_M_AXI_ACLK_FREQ_HZ is $val_clk_Mhz";
  set_property value $val_clk_Mhz ${MODELPARAM_VALUE.C_M_AXI_ACLK_FREQ_HZ}
}

#proc update_MODELPARAM_VALUE.C_M_AXI_ACLK_FREQ_HZ {MODELPARAM_VALUE.C_M_AXI_ACLK_FREQ_HZ PARAM_VALUE.C_M_AXI_ACLK_FREQ_HZ} {
#  # Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
#  set_property value [get_property value ${PARAM_VALUE.C_M_AXI_ACLK_FREQ_HZ}] ${MODELPARAM_VALUE.C_M_AXI_ACLK_FREQ_HZ}
#}

proc update_MODELPARAM_VALUE.C_M_AXI_ADDR_WIDTH { MODELPARAM_VALUE.C_M_AXI_ADDR_WIDTH PARAM_VALUE.C_M_AXI_ADDR_WIDTH } {
  # Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
  set_property value [get_property value ${PARAM_VALUE.C_M_AXI_ADDR_WIDTH}] ${MODELPARAM_VALUE.C_M_AXI_ADDR_WIDTH}
}

proc update_MODELPARAM_VALUE.C_M_AXI_DATA_WIDTH { MODELPARAM_VALUE.C_M_AXI_DATA_WIDTH PARAM_VALUE.C_M_AXI_DATA_WIDTH } {
  # Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
  set_property value [get_property value ${PARAM_VALUE.C_M_AXI_DATA_WIDTH}] ${MODELPARAM_VALUE.C_M_AXI_DATA_WIDTH}
}

proc update_MODELPARAM_VALUE.C_MAX_BURST_LEN { MODELPARAM_VALUE.C_MAX_BURST_LEN PARAM_VALUE.C_MAX_BURST_LEN } {
  # Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
  set_property value [get_property value ${PARAM_VALUE.C_MAX_BURST_LEN}] ${MODELPARAM_VALUE.C_MAX_BURST_LEN}
}

proc update_MODELPARAM_VALUE.C_NATIVE_DATA_WIDTH { MODELPARAM_VALUE.C_NATIVE_DATA_WIDTH PARAM_VALUE.C_NATIVE_DATA_WIDTH } {
  # Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
  set_property value [get_property value ${PARAM_VALUE.C_NATIVE_DATA_WIDTH}] ${MODELPARAM_VALUE.C_NATIVE_DATA_WIDTH}
}

proc update_MODELPARAM_VALUE.C_LENGTH_WIDTH { MODELPARAM_VALUE.C_LENGTH_WIDTH PARAM_VALUE.C_LENGTH_WIDTH } {
  # Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
  set_property value [get_property value ${PARAM_VALUE.C_LENGTH_WIDTH}] ${MODELPARAM_VALUE.C_LENGTH_WIDTH}
}

proc update_MODELPARAM_VALUE.C_ADDR_PIPE_DEPTH { MODELPARAM_VALUE.C_ADDR_PIPE_DEPTH PARAM_VALUE.C_ADDR_PIPE_DEPTH } {
  # Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
  set_property value [get_property value ${PARAM_VALUE.C_ADDR_PIPE_DEPTH}] ${MODELPARAM_VALUE.C_ADDR_PIPE_DEPTH}
}

# Map AXI_S_ACLK_FREQ_MHZ to C_S_AXI_ACLK_FREQ_HZ
#proc update_MODELPARAM_VALUE.C_S_AXI_ACLK_FREQ_HZ {MODELPARAM_VALUE.C_S_AXI_ACLK_FREQ_HZ PARAM_VALUE.AXI_S_ACLK_FREQ_MHZ} {
#  set axi_clk [get_property value ${PARAM_VALUE.AXI_S_ACLK_FREQ_MHZ}]
#  set val_clk_Mhz [expr {int($axi_clk*1000000)} ]
#  #puts "clock value is $val_clk_Mhz";
#  set_property value $val_clk_Mhz ${MODELPARAM_VALUE.C_S_AXI_ACLK_FREQ_HZ}
#}

#proc update_MODELPARAM_VALUE.C_S_AXI_ACLK_FREQ_HZ {MODELPARAM_VALUE.C_S_AXI_ACLK_FREQ_HZ PARAM_VALUE.C_S_AXI_ACLK_FREQ_HZ} {
#  # Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
#  set_property value [get_property value ${PARAM_VALUE.C_S_AXI_ACLK_FREQ_HZ}] ${MODELPARAM_VALUE.C_S_AXI_ACLK_FREQ_HZ}
#}

proc update_MODELPARAM_VALUE.C_S_AXI_DATA_WIDTH { MODELPARAM_VALUE.C_S_AXI_DATA_WIDTH PARAM_VALUE.C_S_AXI_DATA_WIDTH } {
  # Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
  set_property value [get_property value ${PARAM_VALUE.C_S_AXI_DATA_WIDTH}] ${MODELPARAM_VALUE.C_S_AXI_DATA_WIDTH}
}

proc update_MODELPARAM_VALUE.C_S_AXI_ADDR_WIDTH { MODELPARAM_VALUE.C_S_AXI_ADDR_WIDTH PARAM_VALUE.C_S_AXI_ADDR_WIDTH } {
  # Procedure called to set VHDL generic/Verilog parameter value(s) based on TCL parameter value
  set_property value [get_property value ${PARAM_VALUE.C_S_AXI_ADDR_WIDTH}] ${MODELPARAM_VALUE.C_S_AXI_ADDR_WIDTH}
}
