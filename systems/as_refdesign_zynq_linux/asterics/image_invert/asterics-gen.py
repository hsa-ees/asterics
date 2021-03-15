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

# Reader 0
#reader = chain.add_module("as_sensor_ov7670")
#reader.add_iic_master("XILINX_PL_IIC")
reader = chain.add_module("as_memreader", "reader0")
reader.make_port_external("interrupt_out")
#reader.set_generic_value("DOUT_WIDTH", 32)
reader.set_generic_value("SUPPORT_INTERRUPTS", "true")
reader.set_generic_value("SUPPORT_DONE_IRQ_SOURCE", "true")

# Splitter
splitter = chain.add_module("as_invert")
#splitter.set_generic_value("DATA_WIDTH", 32)

# Disperse
disperse = chain.add_module("as_disperse")

# Collect modules
collect = chain.add_module("as_collect", "collect0")

# Writer 0
writer = chain.add_module("as_memwriter", "writer0")
writer.set_generic_value("MEMORY_DATA_WIDTH", 32)
writer.set_generic_value("DIN_WIDTH", 32)
writer.set_generic_value("SUPPORT_INTERRUPTS", "true")
writer.set_generic_value("SUPPORT_DONE_IRQ_SOURCE", "true")
writer.set_generic_value("SUPPORT_DATA_UNIT_COMPLETE", "true")

writer.make_port_external("interrupt_out")

# -------- Module connections ---------------------------

chain.connect(reader,
                disperse)

chain.connect(disperse,
                splitter)

# original image path:
chain.connect(splitter,
                collect)
chain.connect(collect,
                writer)

chain.auto_instantiate()

# Writer0 cache fix
axi_master_0 = chain.get_module("writer0_AXI_Master")
axi_master_0.set_generic_value("CACHING_OVERWRITE", "true")

# Reader0 cache fix
axi_master_r0 = chain.get_module("reader0_AXI_Master")
axi_master_r0.set_generic_value("CACHING_OVERWRITE", "true")

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
#if success:
#    asterics.write_system_graph(chain, "asterics_system_graph")

# Report
if success:
    print("Automatics completed successfully!")
else:
    print("Automatics encountered errors:")
    asterics.list_errors()

