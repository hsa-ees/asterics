# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
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
# @author Philip Manke, Michael Schäferling
# @brief Template user script for running the ASTERICS generator Automatics.
# -----------------------------------------------------------------------------

# Import Automatics
import asterics

# Import Sys for argument handling
import sys

# Get a new processing chain object
chain = asterics.new_chain()

############### ↓ Difference System description ↓ ###############

# Image difference demo system structure:
# CAM -> as_sensor -+-----------------------> collect0 -> writer0 -> RAM
#                   \-------> sync => diff -> collect1 -> writer1 -> RAM
# RAM -> reader -> disperse ->/ 
#        as_iic ---------------------------------------------------> CAM

# Camera
camera = chain.add_module("as_sensor_ov7670")
camera.add_iic_master("XILINX_PL_IIC")

# Splitter
splitter = chain.add_module("as_stream_splitter")

# Reader
reader = chain.add_module("as_memreader")

# Disperse
disperse = chain.add_module("as_disperse")

# Stream Sync
sync = chain.add_module("as_stream_sync")
sync.set_generic_value("BUFF_DEPTH", 1024)

# Pixel Diff
diff = chain.add_module("as_pixel_diff")

# Collect modules
collect0 = chain.add_module("as_collect", "collect0")
collect1 = chain.add_module("as_collect", "collect1")

# Writer 0
writer0 = chain.add_module("as_memwriter", "writer0")
writer0.set_generic_value("MEMORY_DATA_WIDTH", 32)
writer0.set_generic_value("DIN_WIDTH", 32)

# Writer 1
writer1 = chain.add_module("as_memwriter", "writer1")
writer1.set_generic_value("MEMORY_DATA_WIDTH", 32)
writer1.set_generic_value("DIN_WIDTH", 32)

# -------- Module connections ---------------------------

chain.connect(camera,
                splitter)
                
# original image path:
chain.connect(splitter.get("0"),
                collect1)
chain.connect(collect1,
                writer1)

# previous image read path:
chain.connect(reader,
                disperse)
                
# sync image pixels, diff and write back the result:
chain.connect(disperse,
                  sync.get("0", "in"))
chain.connect(splitter.get("1"),
                  sync.get("1", "in"))
chain.connect(sync.get("0", "out"),
              diff.get("0", "in"))
chain.connect(sync.get("1", "out"),
              diff.get("1", "in"))
chain.connect(diff, 
                collect0)
chain.connect(collect0, 
                writer0)


############### ↑ Difference System description ↑ ###############

############### Automatics outputs ##############################

if len(sys.argv) < 3:
    print(("Not enough parameters!\n"
           "Usage:\nasterics-gen.py build-target output-folder\n"
           "Valid build-targets: 'vivado', 'core'"))
    sys.exit()

# Build chain: Generate output products
# Write the outputs for the ASTERICS core

# Stores wether Automatics completed without errors or not
success = False

if sys.argv[1] == "vivado":
    success = chain.write_ip_core_xilinx(sys.argv[2] + "/ASTERICS",
                                         use_symlinks=True, force=True)
    if success:
        # Create link to the VEARS IP-Core
        success = asterics.vears(sys.argv[2], use_symlinks=True, force=True)
elif sys.argv[1] == "core":
    success = chain.write_asterics_core(sys.argv[2], use_symlinks=True)
else:
    sys.exit("Not a valid build target!")
# On success, generate a system graph using dot
if success:
    asterics.write_system_graph(chain, "asterics_system_graph")

# Report
if success:
    print("Automatics completed successfully!")
else:
    print("Automatics encountered errors:")
    asterics.list_errors()

