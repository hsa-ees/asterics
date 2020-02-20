proc init { cellpath otherInfo } {
    #set clk_pin_handle [get_bd_pins $cellpath/m_axi_aclk]
    #set_property CONFIG.FREQ_HZ 100000000 $clk_pin_handle
    set cell [get_bd_cells $cellpath]
    set paramList "AXI_M_ACLK_FREQ_MHZ"
    bd::mark_propagate_only $cell $paramList
}


#~ proc post_config_ip {cellpath otherInfo } {
  
#~ }


proc propagate {cellpath otherInfo } {
    set cell_handle [get_bd_cells $cellpath]
    set intf_handle [get_bd_intf_pins $cellpath/m_axi_aclk]
    set clk_pin_handle [get_bd_pins $cellpath/m_axi_aclk]
    set freq_Hz [get_property CONFIG.FREQ_HZ $clk_pin_handle]
    if { $freq_Hz == "" } {
      set_property MSG.ERROR "VEARS: cannot get AXI master clock frequency" $cell_handle
    } else {
      set freq_Hz_int [expr int($freq_Hz)] 
      set freq_MHz [expr {$freq_Hz_int/1000000.0}];
      set_property CONFIG.AXI_M_ACLK_FREQ_MHZ $freq_MHz $cell_handle
      #puts "VEARS <bd.tcl>: AXI_M_ACLK_FREQ_MHZ is $freq_MHz";
    }
}
