# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
demo_script.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Demo user script with three different demonstration systems, buildable from
included ASTERICS modules.
"""
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
# -----------------------------------------------------------------------------

import time
import sys
import asterics


#### INVERT SYSTEM ##########################################
def define_invert(chain):

    # as_invert demo system structure:
    # HW -> camera -> inverter -> collect -> writer -> DRAM

    #########################################################
    #  CAMERA
    #########################################################
    camera = chain.add_module("as_sensor_ov7670", "camera0")

    #########################################################
    #  INVERTER
    #########################################################
    inverter = chain.add_module("as_invert", "invert0")

    # Connect: camera -> inverter
    chain.connect(camera, inverter)

    #########################################################
    #  COLLECT module
    #########################################################
    collect = chain.add_module("as_collect", "collect0")

    # Connect: inverter -> collect
    chain.connect(inverter, collect)

    #########################################################
    #  MEMWRITER
    #########################################################

    writer = chain.add_module("as_memwriter", "writer0")

    # Configure generics
    writer.set_generic_value("MEMORY_DATA_WIDTH", 32)
    writer.set_generic_value("DIN_WIDTH", 32)

    # Connect: collect -> writer
    chain.connect(collect, writer)

#############################################################

#### MYFILTER SYSTEM ########################################


def define_myfilter(chain):

    # Myfilter demo system topology:
    #                         ↓ Passthrough of original image
    # HW -> camera -> myfilter --------------> collect0 -> writer0 -> DRAM
    #                        \-> [inverter] -> collect1 -> writer1 -> DRAM
    #                         ↑ Filtered image

    #########################################################
    #  CAMERA
    #########################################################
    camera = chain.add_module("as_sensor_ov7670", "camera0")

    #########################################################
    #  MYFILTER
    #########################################################
    myfilter = chain.add_module("as_myfilter", "myfilter0")

    # Connect: camera -> myfilter
    chain.connect(camera, myfilter)
    #########################################################
    #  COLLECT 0 (orignal image)
    #########################################################
    collect0 = chain.add_module("as_collect", "collect0")

    # Connect: myfilter (original image) -> collect0
    chain.connect(myfilter.get_interface("0"), collect0)
    #########################################################
    #  MEMWRITER 0 (original image)
    #########################################################
    writer0 = chain.add_module("as_memwriter", "writer0")

    # Configure Generics
    writer0.set_generic_value("MEMORY_DATA_WIDTH", 32)
    writer0.set_generic_value("DIN_WIDTH", 32)

    # Connect: collect0 -> writer0
    chain.connect(collect0, writer0)

    #########################################################
    #  To insert: INVERTER
    #########################################################

    # Connect: myfilter (filtered image) -> inverter

    #########################################################
    #  COLLECT 1 (filtered image)
    #########################################################
    collect1 = chain.add_module("as_collect", "collect1")

    # Connect: myfilter (filtered image) -> collect1
    chain.connect(myfilter.get_interface("1"), collect1)

    #########################################################
    #  MEMWRITER 1 (filtered image)
    #########################################################
    writer1 = chain.add_module("as_memwriter", "writer1")

    # Configure Generics
    writer1.set_generic_value("MEMORY_DATA_WIDTH", 32)
    writer1.set_generic_value("DIN_WIDTH", 32)

    # Connect: collect1 -> writer1
    chain.connect(collect1, writer1)

#############################################################


#### IMAGE DIFFERENCE SYSTEM ################################
def define_diff_image(chain):

    # image difference (delta t) demo:
    #                     /-----------------------------> collect1 -> writer1 -> RAM
    # HW  -> camera -----+-> stream_sync => pixel_diff -> collect0 -> writer0 -> RAM
    # RAM -> reader -> disperse -+->/
    #                            \-> invert -> collect2 -> writer2 -> RAM
    # stream sync and pixel diff have two inputs; stream sync has two outputs

    # Camera
    camera = chain.add_module("as_sensor_ov7670", "camera0")

    # Splitters
    splitter0 = chain.add_module("as_stream_splitter", "split0")
    splitter1 = chain.add_module("as_stream_splitter", "split1")

    # Reader
    reader = chain.add_module("as_memreader", "reader0")

    # Disperse
    disperse = chain.add_module("as_disperse", "disperse0")

    # Stream Sync
    sync = chain.add_module("as_stream_sync", "sync0")
    sync.set_generic_value("BUFF_DEPTH", 1024)

    # Pixel Diff
    diff = chain.add_module("as_pixel_diff", "diff0")

    # Collect modules
    collect0 = chain.add_module("as_collect", "collect0")
    collect1 = chain.add_module("as_collect", "collect1")
    collect2 = chain.add_module("as_collect", "collect2")

    # Writer 0
    writer0 = chain.add_module("as_memwriter", "writer0")
    writer0.set_generic("MEMORY_DATA_WIDTH", 32)
    writer0.set_generic("DIN_WIDTH", 32)

    # Writer 1
    writer1 = chain.add_module("as_memwriter", "writer1")
    writer1.set_generic("MEMORY_DATA_WIDTH", 32)
    writer1.set_generic("DIN_WIDTH", 32)

    # Writer 2
    writer2 = chain.add_module("as_memwriter", "writer2")
    writer2.set_generic("MEMORY_DATA_WIDTH", 32)
    writer2.set_generic("DIN_WIDTH", 32)

    # Inverter
    inverter = chain.add_module("as_invert", "invert0")

    # -------- Module connections ---------------------------
    # camera -> splitter0
    chain.connect(camera, splitter0)

    # splitter0 (0) -> collect1 -> writer1 (delay image)
    chain.connect(splitter0.get_interface("1"), collect1)
    chain.connect(collect1, writer1)

    # reader -> disperse -> splitter1 (read from delay image, previous frame)
    chain.connect(reader, disperse)
    chain.connect(disperse, splitter1)

    # splitter1 (0) -> inverter -> collect0 -> writer0 (test for delay image)
    chain.connect(splitter1.get_interface("1"), inverter)
    chain.connect(inverter, collect0)
    chain.connect(collect0, writer0)

    # splitter0 (1) -> sync => diff -> collect2 -> writer2 (diff image)
    # splitter1 (1) --->/
    chain.connect(splitter0.get_interface("0"),
                  sync.get_interface("1", "in"))
    chain.connect(splitter1.get_interface("0"),
                  sync.get_interface("0", "in"))
    chain.connect(sync.get_interface("0", "out"),
                  diff.get_interface("0", "in"))
    chain.connect(sync.get_interface("1", "out"),
                  diff.get_interface("1", "in"))
    chain.connect(diff, collect2)
    chain.connect(collect2, writer2)

#############################################################

def define_iic_test(chain):
    camera = chain.add_module("as_sensor_ov7670", "camera")
    collect = chain.add_module("as_collect")
    iic = chain.add_module("as_iic")
    writer = chain.add_module("as_memwriter", "writer0")
    writer.set_generic_value("MEMORY_DATA_WIDTH", 32)
    writer.set_generic_value("DIN_WIDTH", 32)

    chain.connect(camera, collect)
    chain.connect(collect, writer)


# Build function
def build(demo_system):
    # Automatics instance and initialization
    chain = asterics.new_chain()

    # Include user modules
    asterics.add_module_repository("{}/demo_user_modules/"
            .format(sys.argv[0].rsplit("/", maxsplit=1)[0]), "user")

    # Define system
    demo_system(chain)
    
    # Build system
    chain.write_system("astertest/", use_symlinks=False, force=True)

    asterics.write_system_graph(chain)


if __name__ == "__main__":
    runtime = time.time()

    # Choose system configuration (only one at a time)
    build(define_invert)
    # build(define_myfilter)
    # build(define_iic_test)
    # build(define_diff_image)

    print("Automatics finished in {:.2f}s!".format(time.time() - runtime))
