# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2020 Hochschule Augsburg, University of Applied Sciences
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
# @file asterics-gen.py
# @author Philip Manke, Michael Schäferling
# @brief Chain description script to generate the as_refdesign_canny ASTERICS IP-core
# -----------------------------------------------------------------------------

# Import Automatics
import asterics

# Import sys for argument handling
import sys

# Get a new processing chain object
chain = asterics.new_chain()

############### ↓ Canny System description ↓ ###############

# _ Add streaming modules
# Camera
cam0 = chain.add_module("as_sensor_ov7670", "cam0")
# Set Camera's IIC master
cam0.add_iic_master("XILINX_PL_IIC")
# Feature memory writer
writer0 = chain.add_module("as_memwriter", "writer0")
collect_orig = chain.add_module("as_collect", "collect_orig")
writer_orig = chain.add_module("as_memwriter", "writer_orig")

# _ Configure streaming modules

# Feature memory writer
writer0.set_generic_value("MEMORY_DATA_WIDTH", 32)
writer0.set_generic_value("DIN_WIDTH", 32)
writer0.set_generic_value("SUPPORT_DATA_UNIT_COMPLETE", "True")
writer0.set_generic_value("UNIT_COUNTER_WITDH", 8)

# Original image memory writer
writer_orig.set_generic_value("MEMORY_DATA_WIDTH", 32)
writer_orig.set_generic_value("DIN_WIDTH", 32)


# _ Setup 2D Window Pipeline
pipe = asterics.new_2d_window_pipeline(
    image_width=640, name="as_canny_pipeline", force_synchronous_pipeline=True
)
pipe.add_software_driver_file("asterics/canny_pipeline/as_canny_pipe.c")
pipe.add_software_driver_file("asterics/canny_pipeline/as_canny_pipe.h")

pipe.set_generic_value("MINIMUM_BRAM_SIZE", 500)
pipe.set_main_buffer_optimization_strategy(pipe.optimize_all_same_length)
pipe.set_reshape_long_buffers_optimization(True)
pipe.set_similar_length_optimization(True)

# _ Add filter modules

# @q Gauss filter 5x5
fgauss0 = pipe.add_module("as_2d_conv_filter_internal", "fgauss0")
fgauss0.set_generic_value("KERNEL_SIZE", 5)
fgauss0.set_generic_value("KERNEL_TYPE", '"gauss"')

# @q Sobel X filter 3x3
fsobelx = pipe.add_module("as_2d_conv_filter_internal", "fsobelx")
fsobelx.set_generic_value("KERNEL_SIZE", 3)
fsobelx.set_generic_value("KERNEL_TYPE", '"sobel_x"')
fsobelx.set_generic_value("OUTPUT_SIGNED", "true")
fsobelx.set_generic_value("DOUT_WIDTH", 9)

# @q Sobel Y filter 3x3
fsobely = pipe.add_module("as_2d_conv_filter_internal", "fsobely")
fsobely.set_generic_value("KERNEL_SIZE", 3)
fsobely.set_generic_value("KERNEL_TYPE", '"sobel_y"')
fsobely.set_generic_value("OUTPUT_SIGNED", "true")
fsobely.set_generic_value("DOUT_WIDTH", 9)

# @q Gradient weight module
fedgeweight = pipe.add_module("as_gradient_weight", "edge_weight")
fedgeweight.set_generic_value("DIN_WIDTH", 9)

# @q Cordic direction pipeline
fcordic = pipe.add_module("as_cordic_direction", "cordic")
fcordic.set_generic_value("CORDIC_STEP_COUNT", 9)
fcordic.set_generic_value("DIN_WIDTH", 9)
fcordic.set_generic_value("ANGLE_WIDTH", 10)

# @q Non-maximum suppression filter 3x3
fnms = pipe.add_module("as_edge_nms", "nms")

# @q Edge threshold filter
fthreshold = pipe.add_module("as_edge_threshold", "thresh")
fthreshold.set_generic_value("THRESHOLD_WIDTH", 8)

# @q Edge feature list module
ffeature = pipe.add_module("as_edge_list", "feat")
ffeature.set_generic_value("X_COORDINATE_WIDTH", 10)
ffeature.set_generic_value("Y_COORDINATE_WIDTH", 10)
ffeature.set_generic_value("DIN_WIDTH", 11)

# @q Edge feature counter module
ffeatcount = pipe.add_module("as_feature_counter", "featcount")


# _ Pipeline connections

# @q Connect canny threshold registers
# Add registers for canny edge thresholds:
pipe.assign_register_to_port(2, fthreshold.get_port("thr_low_in"), 0)
pipe.assign_register_to_port(2, fthreshold.get_port("thr_high_in"), 8)


# @q Connect into pipeline
cam0.connect(fgauss0)

# @q Connect gauss to sobel x and sobel y
fgauss0.get_port("data_out").connect(fsobelx)
fgauss0.get_port("data_out").connect(fsobely)

# @q Connect sobels to gradient weight
fsobelx.get_port("data_out").connect(fedgeweight.get_port("data1_in"))
fsobely.get_port("data_out").connect(fedgeweight.get_port("data2_in"))

# @q Connect sobels to cordic
fsobelx.get_port("data_out").connect(fcordic.get_port("data_x_in"))
fsobely.get_port("data_out").connect(fcordic.get_port("data_y_in"))

# @q Connect NMS
fedgeweight.get_port("data_out").connect(fnms.get("window_weight_in"))
fcordic.get_port("data_out_reduced").connect(fnms.get_port("data_dir_in"))

# @q Connect edge threshold
fnms.get_port("data_out").connect(fthreshold.get_port("nms_in"))
fthreshold.get_port("data_out").connect(fthreshold.get("first_row_is_edge"))

# @q Connect edge feature list
fthreshold.get_port("data_out").connect(ffeature.get_port("is_edge_in"))
fcordic.get_port("data_out_full").connect(ffeature.get_port("edge_data_in"))
cam0.get_port("hsync_out").connect(ffeature.get_port("hsync_in"))
cam0.get_port("vsync_out").connect(ffeature.get_port("vsync_in"))

# @q Connect feature counter module
ffeatcount.set_port_fixed_value("trigger_in", "strobe_out_feat_fixed_value")
pipe.connect(pipe.flush_done, ffeatcount.get_port("frame_done"))
pipe.assign_port_to_register(4, ffeatcount.get_port("count_out"), 0)

# @q Connect feature data to writer 0
ffeature.get("out").connect(writer0.get("in"))


# Connect streaming modules

cam0.connect(collect_orig)
collect_orig.connect(writer_orig)

############### ↑ Canny System description ↑ ###############

############### Automatics outputs ##############################

if len(sys.argv) < 3:
    print(
        (
            "Not enough parameters!\n"
            "Usage:\nasterics-gen.py build-target output-folder\n"
            "Valid build-targets: 'vivado', 'core'"
        )
    )
    sys.exit()

# Build chain: Generate output products
# Write the outputs for the ASTERICS core

# Stores wether Automatics completed without errors or not
success = False

if sys.argv[1] == "vivado":
    success = chain.write_ip_core_xilinx(
        sys.argv[2] + "/ASTERICS", use_symlinks=True, force=True
    )
    if success:
        # Create link to the VEARS IP-Core
        success = asterics.vears(sys.argv[2], use_symlinks=True, force=True)
elif sys.argv[1] == "core":
    success = chain.write_asterics_core(sys.argv[2], use_symlinks=True)
else:
    sys.exit("Not a valid build target!")
# On success, generate a system graph using dot
if success:
    chain.write_system_graph("asterics_system_graph")

# Report
if success:
    print("Automatics completed successfully!")
else:
    print("Automatics encountered error(s):")
    asterics.list_errors()
