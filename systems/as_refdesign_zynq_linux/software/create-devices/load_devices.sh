#!/bin/sh

#/*--------------------------------------------------------------------------------
#--  This file is part of the ASTERICS Framework and the VEARS core. 
#--  Copyright (C) Hochschule Augsburg, University of Applied Sciences
#----------------------------------------------------------------------------------
#-- File:           load_devices.sh
#--
#-- Company:        University of Applied Sciences, Augsburg, Germany
#-- Author:         Alexander Zoellner
#--
#-- Description:    Script for creating device nodes on file system for the ASTERICS
#--                 device driver
#--                 
#----------------------------------------------------------------------------------
#--  This program is free software: you can redistribute it and/or modify
#--  it under the terms of the GNU Lesser General Public License as published by
#--  the Free Software Foundation, either version 3 of the License, or
#--  (at your option) any later version.
#--
#--  This program is distributed in the hope that it will be useful,
#--  but WITHOUT ANY WARRANTY; without even the implied warranty of
#--  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#--  GNU Lesser General Public License for more details.
#--
#--  You should have received a copy of the GNU Lesser General Public License
#--  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#---------------------------------------------------------------------------------*/

module="as_driver"

# In case the script has a way to obtain a list of devices, it may be useful to 
# create an "asterics" group and assign the devices to it with the appropriate 
# permissions (since some parts may require root permissions)
group="asterics"
mode="664"



# Get major number
major=`cat /proc/devices | awk "\\$2==\"$module\" {print \\$1}"`

# Control device is always posses the first minor number
mknod /dev/as_control c $major 0

# TODO: Get the device names dynamically from somewhere

# Create device nodes
# IMPORTANT: Minor number starts with "1". Minor numbers are assigned in ascending order, in 
# the same way as the devices are created (i.e. usually in the same order as specified in as_hardware.c)

mknod /dev/as_regio_global c $major 1
mknod /dev/as_memreader_0_64 c $major 2
mknod /dev/as_memreader_1_64 c $major 3
mknod /dev/as_memreader_2_64 c $major 4
mknod /dev/as_memwriter_0_64 c $major 5
mknod /dev/as_memwriter_1_64 c $major 6
mknod /dev/as_memwriter_2_64 c $major 7
mknod /dev/as_mmap_conf_data c $major 8
mknod /dev/as_mmap_feat_data c $major 9
mknod /dev/as_mmap_out_data c $major 10
mknod /dev/as_mmap_image_data c $major 11

# Create the actual devices (expects executable of create-devices)
./create-devices -c




