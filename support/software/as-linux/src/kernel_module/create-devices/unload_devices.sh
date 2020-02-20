#!/bin/sh

#/*--------------------------------------------------------------------------------
#--  This file is part of the ASTERICS Framework and the VEARS core. 
#--  Copyright (C) Hochschule Augsburg, University of Applied Sciences
#----------------------------------------------------------------------------------
#-- File:           unload_devices.sh
#--
#-- Company:        University of Applied Sciences, Augsburg, Germany
#-- Author:         Alexander Zoellner   
#--
#-- Description:    Script for deleting devices and their nodes on the file system for
#--                 the ASTERICS device driver
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

# Delete the acutal devices (expects executable of create-devices)
./create-devices -d

#TODO: Get the device names dynamically from somewhere

# Remove device nodes
rm -f /dev/as_control
rm -f /dev/as_regio_global
rm -f /dev/as_memreader_0_64
rm -f /dev/as_memreader_1_64
rm -f /dev/as_memreader_2_64
rm -f /dev/as_memwriter_0_64
rm -f /dev/as_memwriter_1_64
rm -f /dev/as_memwriter_2_64
rm -f /dev/as_mmap_conf_data
rm -f /dev/as_mmap_feat_data
rm -f /dev/as_mmap_out_data
rm -f /dev/as_mmap_image_data

exit 0
