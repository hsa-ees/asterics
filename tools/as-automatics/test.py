#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct  1 14:43:29 2018

Testscript for as_automatics during development.

@author: phil

Description:
    Just start the current generator test function(-s).
"""
import copy
import time

import asterics

import as_automatics_visual as as_visual
# ~~~~ TESTING ~~~~


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
    chain.connect(splitter0.get_interface("as_stream_1"), collect1)
    chain.connect(collect1, writer1)

    # reader -> disperse -> splitter1 (read from delay image, previous frame)
    chain.connect(reader, disperse)
    chain.connect(disperse, splitter1)

    # splitter1 (0) -> inverter -> collect0 -> writer0 (test for delay image)
    chain.connect(splitter1.get_interface("as_stream_1"), inverter)
    chain.connect(inverter, collect0)
    chain.connect(collect0, writer0)

    # splitter0 (1) -> sync => diff -> collect2 -> writer2 (diff image)
    # splitter1 (1) --->/
    chain.connect(splitter0.get_interface("as_stream_0"),
                  sync.get_interface("as_stream_1", "in"))
    chain.connect(splitter1.get_interface("as_stream_0"),
                  sync.get_interface("as_stream_0", "in"))
    chain.connect(sync.get_interface("as_stream_0", "out"),
                  diff.get_interface("as_stream_0", "in"))
    chain.connect(sync.get_interface("as_stream_1", "out"),
                  diff.get_interface("as_stream_1", "in"))
    chain.connect(diff, collect2)
    chain.connect(collect2, writer2)


def define_stream_sync_test(chain):

    # image difference (delta t) demo:
    #                 /-> invert ->\            /-> collect1 -> wrtier1 -> RAM
    # HW  -> camera -+----------> stream_sync =+--> collect0 -> writer0 -> RAM

    # Camera
    camera = chain.add_module("as_sensor_ov7670", "camera0")
    camera.port_rule_add("VCOMPLETE_OUT",
                         "sink_missing", "fallback_port(vsync_in)")

    # Splitter
    splitter = chain.add_module("as_stream_splitter", "split0")

    inverter = chain.add_module("as_invert", "invert0")

    # Stream Sync
    sync = chain.add_module("as_stream_sync", "sync0")

    # Collect modules
    collect0 = chain.add_module("as_collect", "collect0")
    collect1 = chain.add_module("as_collect", "collect1")

    # Writer 0
    writer0 = chain.add_module("as_memwriter", "writer0")
    writer0.set_generic("MEMORY_DATA_WIDTH", 32)
    writer0.set_generic("DIN_WIDTH", 32)
    writer0.make_port_external("flush_in")
    writer0.set_port_fixed_value("interrupt_out", "open")
    writer0.set_port_fixed_value("data_unit_complete_in", "'0'")

    # Writer 1
    writer1 = chain.add_module("as_memwriter", "writer1")
    writer1.set_generic("MEMORY_DATA_WIDTH", 32)
    writer1.set_generic("DIN_WIDTH", 32)
    writer1.make_port_external("flush_in")
    writer1.set_port_fixed_value("interrupt_out", "open")
    writer1.set_port_fixed_value("data_unit_complete_in", "'0'")

    # -------- Module connections ---------------------------
    chain.connect(camera, splitter)
    chain.connect(splitter.get_interface("as_stream_0"),
                  sync.get_interface("as_stream_0"))

    chain.connect(splitter.get_interface("as_stream_1"), inverter)
    chain.connect(inverter, sync.get_interface("as_stream_1"))
    chain.connect(sync.get_interface("as_stream_0", "out"), collect0)
    chain.connect(sync.get_interface("as_stream_1", "out"), collect1)

    chain.connect(collect1, writer1)
    chain.connect(collect0, writer0)


def define_canny_eas(chain):
    # ---------------- Module instantiations ----------------
    camera = chain.add_module("as_sensor_ov7670", "camera0")
    splitter = chain.add_module("as_stream_splitter", "splitter0")
    collect0 = chain.add_module("as_collect", "collect0")
    writer0 = chain.add_module("as_memwriter", "writer0")
    collect1 = chain.add_module("as_collect", "collect1")
    writer1 = chain.add_module("as_memwriter", "writer1")
    canny_eas = chain.add_module("as_edge_and_scale_640", "canny_eas")

    # -------- Module configurations --------
    collect0.set_generic("DOUT_ORDER_ASCENDING", "False")
    collect0.set_generic_value("DIN_WIDTH", 8)
    collect0.set_generic_value("COLLECT_COUNT", 4)

    collect1.set_generic("DOUT_ORDER_ASCENDING", "False")

    camera.get_port("VCOMPLETE_OUT").add_rule("sink_missing",
                                              "fallback_port(vsync_in)")

    writer0.set_generic("MEMORY_DATA_WIDTH", 32)
    writer0.set_generic("DIN_WIDTH", 32)
    writer0.get_port("interrupt_out").set_value("open")
    writer0.get_port("data_unit_complete_in").set_value("'0'")
    writer0.get_port("flush_in").make_external()

    writer1.set_generic("MEMORY_DATA_WIDTH", 32)
    writer1.set_generic("DIN_WIDTH", 32)
    writer1.get_port("flush_in").make_external()
    writer1.get_port("interrupt_out").set_value("open")
    writer1.get_port("data_unit_complete_in").set_value("'0'")

    splitter.get_port("xres_in").set_value('X"280"')
    splitter.get_port("yres_in").set_value('X"1E0"')

    # -------- Module connections ---------------------------
    # HW -> camera -> splitter -+-> canny_eas -> collect0 -> writer0 -> DRAM
    #                           \--------------> collect1 -> writer1 -> DRAM

    chain.connect(camera, splitter)
    chain.connect(splitter.get_interface("as_stream_1"), canny_eas)
    chain.connect(canny_eas.get_interface("debug_as_stream"), collect0)
    chain.connect(canny_eas.get_port("scaled_vsync_out"), collect0)
    chain.connect(canny_eas.get_port("scaled_hsync_out"), collect0)

    chain.connect(collect0, writer0)

    chain.connect(splitter.get_interface("as_stream_0"), collect1)
    chain.connect(collect1, writer1)


#### CANNY SYSTEM ###########################################
def define_canny(chain):

    # Canny demo system structure:
    # HW -> camera -> splitter ------------------------> collect0 -> writer0 -> DRAM
    #                         \-> canny -> pixel_conv -> collect1 -> writer1 -> DRAM

    #########################################################
    #  CAMERA
    #########################################################
    camera = chain.add_module("as_sensor_ov7670", "camera0")

    #########################################################
    #  STREAM SPLITTER
    #########################################################
    splitter = chain.add_module("as_stream_splitter", "splitter0")

    # Configure Ports
    splitter.set_port_fixed_value("xres_in", 'X"280"')
    splitter.set_port_fixed_value("yres_in", 'X"1E0"')

    # Connect: camera -> splitter
    chain.connect(camera, splitter)

    #########################################################
    #  COLLECT 0 (orignal image)
    #########################################################
    collect0 = chain.add_module("as_collect", "collect0")

    # Connect: myfilter (original image) -> collect0
    chain.connect(splitter.get_interface("as_stream_1"), collect0)

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
    #  CANNY
    #########################################################
    canny = chain.add_module("as_canny", "canny0")

    # Configure Generics
    canny.set_generic_value("gen_debug", "False")

    # Connect: splitter -> canny
    chain.connect(splitter.get_interface("as_stream_0"), canny)

    #########################################################
    #  PIXEL CONVERTER (1 Bit -> 8 Bit)
    #########################################################
    pixel_conv = chain.add_module("as_pixel_conv", "expansion0")

    # Configure Generics
    pixel_conv.set_generic_value("DATA_WIDTH_IN", 1)
    pixel_conv.set_generic_value("DATA_WIDTH_OUT", 8)

    # Connect: canny -> pixel_conv
    chain.connect(canny, pixel_conv)

    #########################################################
    #  COLLECT 1 (filtered image)
    #########################################################
    collect1 = chain.add_module("as_collect", "collect1")

    # Connect: inverter -> collect1
    chain.connect(pixel_conv, collect1)

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


def define_threshold_system(chain):
    
    # topology:
    # CAM -> sensor -> collect_4to1 -> reorder -> disperse_1to4 -> threshold ->
    #       -> collect_2to1 (0) -> collect_2to1 (1) -> reorder -> writer -> RAM 

    camera = chain.add_module("as_sensor_ov7670", "camera")
    coll41 = chain.add_module("as_collect_4to1")
    reord1 = chain.add_module("as_reorder")
    reord2 = chain.add_module("as_reorder")
    thresh = chain.add_module("as_threshold")
    disp = chain.add_module("as_disperse_1to4")
    coll2_0 = chain.add_module("as_collect_2to1")

    coll2_1 = chain.add_module("as_collect_2to1")
    coll2_1.set_generic_value("DIN_WIDTH", 16)
    coll2_1.set_generic_value("DOUT_WIDTH", 32)
    
    writer = chain.add_module("as_memwriter")
    writer.set_generic_value("MEMORY_DATA_WIDTH", 32)
    writer.set_generic_value("DIN_WIDTH", 32)

    chain.connect(camera, coll41)
    chain.connect(coll41, reord1)
    chain.connect(reord1, disp)
    chain.connect(disp, thresh)
    chain.connect(thresh, coll2_0)
    chain.connect(coll2_0, coll2_1)
    chain.connect(coll2_1, reord2)
    chain.connect(reord2, writer)



def run_test():
    comptime = time.time()
    asterics.set_loglevel("info", "info")
    chain = asterics.new_chain()

    thistime = time.time() - comptime
    print("Init: {}".format(thistime))
    comptime = time.time()

    #auto.add_module_repository("./unit-test-resources/", "user")
    asterics.add_module_repository("./tools/as-automatics/demo_user_modules/", "user")

    thistime = time.time() - comptime
    print("Add subfolder: {}".format(thistime))
    comptime = time.time()

    #define_diff_image(chain)
    define_threshold_system(chain)

    thistime = time.time() - comptime
    print("Chain definition: {}".format(thistime))
    comptime = time.time()

    if not chain.write_system("astertest/", use_symlinks=True, module_driver_dirs=False, force=True):
        return False

    chain.top.list_module(2)
    thistime = time.time() - comptime
    print("Build chain: {}".format(thistime))
    #comptime = time.time()
    all_modules = copy.copy(chain.modules)
    all_modules.extend(chain.module_groups)

    as_visual.generate_module_graph(all_modules, "module_graph")

    chain.list_address_space()
    print("Done")


if __name__ == "__main__":

    comptime = time.time()
    run_test()
    print("Testtime: {}".format(time.time() - comptime))
