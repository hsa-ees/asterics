# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# Copyright (C) Hochschule Augsburg, University of Applied Sciences
#
# Author: Philip Manke <philip.manke@hs-augsburg.de> 2019-07-09
#
# --------------------- LICENSE -----------------------------------------------
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
# --------------------- DOXYGEN -----------------------------------------------
##
# @file user_script.py
# @author Philip Manke
# @brief Template user script for running the ASTERICS generator Automatics.
# -----------------------------------------------------------------------------

# Import Automatics
import asterics


# Optional: Include user modules from folder(s)
# Automatics expects the passed folder to contain folders for each module,
# structured like the module folders of included modules
#asterics.add_module_repository("path/to/user/module/folder",
#                               <optional> "repository_name")

# Create a new processing chain
chain = asterics.new_chain()

# --------- Example chain description start ---------

# as_invert demo system structure:
# HW -> camera -> inverter -> collect -> writer -> DRAM

#########################################################
#  CAMERA
#########################################################
camera = chain.add_module("as_sensor_ov7670", "camera0")

#########################################################
#  INVERTER
#########################################################
inverter = chain.add_module("as_invert")

# Connect: camera -> inverter
chain.connect(camera, inverter)

#########################################################
#  COLLECT module
#########################################################
collect = chain.add_module("as_collect")

# Connect: inverter -> collect
chain.connect(inverter, collect)

#########################################################
#  MEMWRITER
#########################################################
writer = chain.add_module("as_memwriter")

# Configure generics
writer.set_generic_value("MEMORY_DATA_WIDTH", 32)
writer.set_generic_value("DIN_WIDTH", 32)

# Connect: collect -> writer
chain.connect(collect, writer)

# --------- Chain description end ---------


# Generate output products
# !! Set output directory here !!
chain.write_ip_core_xilinx("output/directory/")
# Optional parameters: 
#   use_symlinks : link to source files instead of copying them (default: True)
#   force : delete contents of output directory if not empty (False)
#   module_driver_dirs : sort ASTERICS module driver files in subfolders (False)

# Build functions:
# write_core(path, use_symlinks, force, module_driver_dirs)
#    simple folder structure, output HW and SW sources only
# write_hw(path, use_symlinks, force)
#    output only HW sources
# write_sw(path, use_symlinks, force, module_driver_dirs)
#    output only SW sources
# write_system(path, use_symlinks, force, module_driver_dirs, add_vears)
#    output all sources into a system template folder structure.
#    package IP core and link/copy the VEARS core into the system
#    Additional parameter: add_vears : Copy/Link the VEARS core (default: True)
#                             VEARS enables video output via VGA, DVI or HDMI


# Done!
print("Process complete!")
