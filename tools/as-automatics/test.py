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
    chain.connect(splitter0.get_interface("0"), sync.get_interface("1", "in"))
    chain.connect(splitter1.get_interface("0"), sync.get_interface("0", "in"))
    chain.connect(sync.get_interface("0", "out"), diff.get_interface("0", "in"))
    chain.connect(sync.get_interface("1", "out"), diff.get_interface("1", "in"))
    chain.connect(diff, collect2)
    chain.connect(collect2, writer2)


def define_stream_sync_test(chain):

    # image difference (delta t) demo:
    #                 /-> invert ->\            /-> collect1 -> wrtier1 -> RAM
    # HW  -> camera -+----------> stream_sync =+--> collect0 -> writer0 -> RAM

    # Camera
    camera = chain.add_module("as_sensor_ov7670", "camera0")
    camera.port_rule_add("VCOMPLETE_OUT", "sink_missing", "fallback_port(vsync_in)")

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
    chain.connect(
        splitter.get_interface("as_stream_0"), sync.get_interface("as_stream_0")
    )

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

    camera.get_port("VCOMPLETE_OUT").add_rule("sink_missing", "fallback_port(vsync_in)")

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


def define_diff(chain):
    # Camera
    camera = chain.add_module("as_sensor_ov7670_xpm")
    # Splitter
    splitter = chain.add_module("as_stream_splitter")
    # Reader
    reader = chain.add_module("as_memreader", "reader")
    # Disperse
    disperse = chain.add_module("as_disperse")
    # Stream Sync
    sync = chain.add_module("as_stream_sync")
    sync.set_generic_value("BUFF_DEPTH", 1024)
    # Pixel Diff
    diff = chain.add_module("as_pixel_diff")
    # Collect modules
    collect0 = chain.add_module("as_collect", "collect0")
    # collect0.set_generic_value("COLLECT_COUNT", 16)
    collect1 = chain.add_module("as_collect", "collect1")
    # collect1.set_generic_value("COLLECT_COUNT", 16)
    # Writer 0
    writer0 = chain.add_module("as_memwriter", "writer0")
    writer0.set_generic("MEMORY_DATA_WIDTH", 32)
    writer0.set_generic("DIN_WIDTH", 32)
    # Writer 1
    writer1 = chain.add_module("as_memwriter", "writer1")
    writer1.set_generic("MEMORY_DATA_WIDTH", 32)
    writer1.set_generic("DIN_WIDTH", 32)

    # -------- Module connections ---------------------------
    chain.connect(camera, splitter)

    # original image path:
    chain.connect(splitter.get("0"), collect1)
    chain.connect(collect1, writer1)

    # previous image read path:
    chain.connect(reader, disperse)

    # sync image pixels, diff and write back the result:
    chain.connect(disperse, sync.get("0", "in"))
    chain.connect(splitter.get("1"), sync.get("1", "in"))
    chain.connect(sync.get("0", "out"), diff.get("0", "in"))
    chain.connect(sync.get("1", "out"), diff.get("1", "in"))
    chain.connect(diff, collect0)
    chain.connect(collect0, writer0)

    # Auto-instantiate modules
    chain.auto_instantiate()

    # Get AXI Master interfaces for reader & writer modules and configure them
    axi_master_r = chain.get_module("reader_AXI_Master")
    axi_master_r.set_generic_value("C_M_AXI_DATA_WIDTH", 32)
    axi_master_r.set_generic_value("C_NATIVE_DATA_WIDTH", 32)

    axi_master_w0 = chain.get_module("writer0_AXI_Master")
    axi_master_w0.set_generic_value("C_M_AXI_DATA_WIDTH", 32)
    axi_master_w0.set_generic_value("C_NATIVE_DATA_WIDTH", 32)

    axi_master_w1 = chain.get_module("writer1_AXI_Master")
    axi_master_w1.set_generic_value("C_M_AXI_DATA_WIDTH", 32)
    axi_master_w1.set_generic_value("C_NATIVE_DATA_WIDTH", 32)


def define_threshold_system(chain):

    # topology:
    # CAM -> sensor -> collect_4to1 -> reorder -> disperse_1to4 -> threshold ->
    #       -> collect_2to1 (0) -> collect_2to1 (1) -> reorder -> writer -> RAM

    camera = chain.add_module("as_sensor_ov7670", "camera")
    thresh = chain.add_module("as_threshold", "thres")
    coll = chain.add_module("as_collect", "collect")
    writer = chain.add_module("as_memwriter", "writer0")

    writer.set_generic_value("MEMORY_DATA_WIDTH", 32)
    writer.set_generic_value("DIN_WIDTH", 32)
    writer.get("stall_in").overwrite_rule("sink_missing", "set_value('0')")

    chain.connect(camera, thresh)
    chain.connect(thresh, coll)
    chain.connect(coll, writer)


def define_nitra(chain):

    # System structure:
    # CAM -> as_sensor ----> as_nitra -> as_collect -> as_memwriter -> RAM
    # RAM -> as_memreader -->/ ← Config data

    # --------- Camera ---------
    camera = chain.add_module("as_sensor_ov7670")

    # --------- Reader ---------
    reader = chain.add_module("as_memreader", "nitra_config")

    # Configure generics
    reader.set_generic_value("MEMORY_DATA_WIDTH", 32)
    reader.set_generic_value("MEM_ADDRESS_BIT_WIDTH", 32)
    reader.set_generic_value("DOUT_WIDTH", 32)
    reader.set_generic_value("BURST_LENGTH_BIT_WIDTH", 10)

    # Disable as_regmgr for as_memreader slv_registers
    reader.get("in", if_type="slv_reg_interface").instantiate_no_module()

    # --------- NITRA ---------
    nitra = chain.add_module("as_nitra", "nitra")

    # Configure generics
    nitra.set_generic_value("IMAGE_WIDTH", 480)
    nitra.set_generic_value("IMAGE_HEIGHT", 640)

    # Nitra input is camera
    camera.connect(nitra.get("in", if_type="as_stream"))
    # Disable regmgr for reader slv_register interface
    nitra.get("reader_out").instantiate_no_module()
    # Connect as_memreader register interface to nitra
    nitra.get("reader_out").connect(reader)
    # Nitra configuration input is as_memreader as_stream output
    nitra.get("reader").connect(reader.get("out"))

    # --------- Collect ---------
    collect = chain.add_module("as_collect")

    nitra.get("out", if_type="as_stream").connect(collect)

    # --------- Writer ---------
    writer = chain.add_module("as_memwriter")
    writer.set_generic_value("MEMORY_DATA_WIDTH", 32)
    writer.set_generic_value("DIN_WIDTH", 32)

    collect.connect(writer)


def define_myfilter(chain):
    camera = chain.add_module("as_sensor_ov7670")
    camera.add_iic_master("XILINX_PL_IIC")
    splitter = chain.add_module("as_stream_splitter")
    myfilter = chain.add_module("as_myfilter")
    collect0 = chain.add_module("as_collect")
    writer0 = chain.add_module("as_memwriter")
    writer0.set_generic("MEMORY_DATA_WIDTH", 32)
    writer0.set_generic("DIN_WIDTH", 32)
    collect1 = chain.add_module("as_collect")
    writer1 = chain.add_module("as_memwriter")
    writer1.set_generic("MEMORY_DATA_WIDTH", 32)
    writer1.set_generic("DIN_WIDTH", 32)

    camera.connect(splitter)
    splitter.get("1").connect(myfilter)
    myfilter.connect(collect1)
    collect1.connect(writer1)
    splitter.get("0").connect(collect0)
    collect0.connect(writer0)


def define_uht_ew(chain):
    camera = chain.add_module("as_sensor_ov7670")
    splitter_cam = chain.add_module("as_stream_splitter", "splitter_cam")

    camera.connect(splitter_cam)

    collect_cam = chain.add_module("as_collect", "collect_cam")
    writer_cam = chain.add_module("as_memwriter", "writer_cam")

    collect_cam.set_generic_value("COLLECT_COUNT", 8)

    splitter_cam.get("0", "out").connect(collect_cam)
    collect_cam.connect(writer_cam)

    edge = chain.add_module("as_feature")
    collect_dbg = chain.add_module("as_collect", "collect_dbg")
    writer_dbg = chain.add_module("as_memwriter", "writer_dbg")
    collect_scaled = chain.add_module("as_collect", "collect_scaled")
    writer_scaled = chain.add_module("as_memwriter", "writer_scaled")

    collect_scaled.set_generic_value("DIN_WIDTH", 32)
    collect_scaled.set_generic_value("COLLECT_COUNT", 2)
    collect_dbg.set_generic_value("COLLECT_COUNT", 8)
    edge.set_generic_value("GEN_X_RES", 640)
    edge.set_generic_value("GEN_Y_RES", 480)

    splitter_cam.get("1", "out").connect(edge)

    edge.get("debug").connect(collect_dbg)
    collect_dbg.connect(writer_dbg)
    edge.get("scaled").connect(collect_scaled)
    collect_scaled.connect(writer_scaled)

    uht = chain.add_module("as_uht")
    reader_conf = chain.add_module("as_memreader", "reader_conf")
    collect_uht = chain.add_module("as_collect", "collect_uht")
    writer_uht = chain.add_module("as_memwriter", "writer_uht")

    collect_uht.set_generic_value("DIN_WIDTH", 32)
    collect_uht.set_generic_value("COLLECT_COUNT", 2)

    uht.set_generic_value("GEN_DIN_WIDTH", 32)
    uht.set_generic_value("GEN_RAM_BIT_WIDTH", 16)

    edge.get("feature").connect(uht.get("in", if_type="as_stream"))
    reader_conf.connect(uht.get("conf"))
    uht.get("out").connect(collect_uht)
    collect_uht.connect(writer_uht)

    chain.auto_instantiate()
    master_w_cam = chain.get_module("writer_cam_AXI_Master")
    master_w_dbg = chain.get_module("writer_dbg_AXI_Master")
    master_w_scaled = chain.get_module("writer_scaled_AXI_Master")
    master_w_uht = chain.get_module("writer_uht_AXI_Master")

    master_w_cam.set_generic_value("C_M_AXI_DATA_WIDTH", 64)
    master_w_cam.set_generic_value("C_NATIVE_DATA_WIDTH", 64)
    master_w_dbg.set_generic_value("C_M_AXI_DATA_WIDTH", 64)
    master_w_dbg.set_generic_value("C_NATIVE_DATA_WIDTH", 64)
    master_w_scaled.set_generic_value("C_M_AXI_DATA_WIDTH", 64)
    master_w_scaled.set_generic_value("C_NATIVE_DATA_WIDTH", 64)
    master_w_uht.set_generic_value("C_M_AXI_DATA_WIDTH", 64)
    master_w_uht.set_generic_value("C_NATIVE_DATA_WIDTH", 64)


def define_simple_camera(chain):
    cam = chain.add_module("as_sensor_ov7670")
    cam.add_iic_master("XILINX_PL_IIC")
    invert = chain.add_module("as_invert")
    collect = chain.add_module("as_collect")
    writer = chain.add_module("as_memwriter")
    writer.set_generic("MEMORY_DATA_WIDTH", 32)
    writer.set_generic("DIN_WIDTH", 32)
    writer.make_port_external("interrupt_out")
    cam.connect(invert)
    invert.connect(collect)
    collect.connect(writer)

    chain.auto_instantiate()

    axi_master = chain.get_module("as_memwriter_0_AXI_Master")
    axi_master.set_port_fixed_value("m_axi_awcache", "open")
    axi_master.set_port_fixed_value("m_axi_arcache", "open")

    chain.top.define_port(
        "master_memwriter_0_m_axi_awcache",
        data_type="std_logic_vector",
        data_width=(3, "downto", 0),
        direction="out",
        fixed_value='"1111"',
    )
    chain.top.define_port(
        "master_memwriter_0_m_axi_arcache",
        data_type="std_logic_vector",
        data_width=(3, "downto", 0),
        direction="out",
        fixed_value='"1111"',
    )
    # axi_slave = chain.get_module("as_main_AXI_Slave")

    # chain.top.define_port("awcache", direction="out")
    # chain.top.port_set_value("awcache", "'1'")
    # chain.top.define_port("flush_in")
    # chain.top.define_signal("flush_internal")
    # chain.top.signal_connect("flush_internal", chain.top.get_port("flush_in"))
    # chain.top.define_port("my_clk", direction="out")
    # chain.top.port_connect("my_clk", axi_slave.get_port("s_axi_aclk"))
    # pass
    # chain.auto_instantiate()
    # chain.auto_connect()
    # print(chain.top.get_signal("master_memwriter_0_m_axi_awcache"))
    # axi_master = chain.get_module("as_memwriter_0_AXI_Master")
    # axi_master.set_port_fixed_value("m_axi_awcache", '"1111"')
    # chain.top.set_port_fixed_value("master_memwriter_0_m_axi_awcache", '"1111"')
    # print(writer.get("flush_in"))
    # collect.get_port("hsync_out").connect(writer.get("flush_in"))


def define_single_2dwpmod(chain):
    cam = chain.add_module("as_sensor_ov7670")
    cam.add_iic_master("XILINX_PL_IIC")
    gauss = chain.add_module("as_gauss")
    collect = chain.add_module("as_collect")
    writer = chain.add_module("as_memwriter")
    writer.set_generic("MEMORY_DATA_WIDTH", 32)
    writer.set_generic("DIN_WIDTH", 32)
    cam.connect(gauss)
    gauss.connect(collect)
    collect.connect(writer)


def define_test(chain):
    asterics.add_module_repository("demo_user_modules/")
    filter2 = chain.add_module("as_myfilter_2")
    filter2.get("foo", "in").print_interface(2)
    filter2.get("foo", "out").print_interface(2)
    filter2.get("bar", "in").print_interface(2)
    filter2.get("bar", "out").print_interface(2)


def run_test():
    asterics.quiet()
    comptime = time.time()
    # asterics.set_loglevel("info", "info")
    chain = asterics.new_chain()

    thistime = time.time() - comptime
    print("Init: {}".format(thistime))
    comptime = time.time()
    asterics.set_loglevel("info")

    asterics.add_module_repository(
        "/home/phil/EES/asterics-nonfree/modules/", "nonfree"
    )
    # asterics.add_module_repository("demo_user_modules/", "demo")

    thistime = time.time() - comptime
    print("Add subfolder: {}".format(thistime))
    comptime = time.time()

    # define_diff_image(chain)
    # define_threshold_system(chain)
    # define_myfilter(chain)
    # define_diff(chain)
    # define_nitra(chain)
    # define_uht_ew(chain)
    define_simple_camera(chain)
    # define_single_2dwpmod(chain)
    # define_test(chain)

    thistime = time.time() - comptime
    print("Chain definition: {}".format(thistime))
    comptime = time.time()

    success = chain.write_asterics_core("astertest/", use_symlinks=True, force=True)
    # success = chain.write_ip_core_xilinx("astertest/", use_symlinks=True, force=True)
    if success:
        # asterics.vears("astertest/IPs/", force=True)

        thistime = time.time() - comptime
        print("Build chain: {}".format(thistime))
        comptime = time.time()

        chain.list_address_space()
        asterics.write_system_graph(
            chain,
            show_toplevels=False,
            show_auto_inst=False,
            show_ports=False,
            show_unconnected=False,
        )

        thistime = time.time() - comptime
        print("Print graph and regs: {}".format(thistime))
        print("Done")
    else:
        print("Failed")


if __name__ == "__main__":
    comptime = time.time()
    asterics.print_version()
    # asterics.requires_version("0.2.003")
    # asterics.requires_at_least_version("0.3.000")
    run_test()
    print("Testtime: {}".format(time.time() - comptime))
