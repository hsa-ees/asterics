import asterics

asterics.set_loglevel(console="DEBUG")
asterics.quiet()
asterics.add_module_repository("./demo_user_modules/")

chain = asterics.new_chain()
pipe = asterics.new_2d_window_pipeline(640, 480)

# Pixel based modules
camera = chain.add_module("as_sensor_ov7670", "camera")
collect0 = chain.add_module("as_collect", "collect")
writer0 = chain.add_module("as_memwriter", "writer")

# Configure modules
collect0.set_generic_value("DIN_WIDTH", 4)
collect0.set_generic_value("COLLECT_COUNT", 8)
writer0.set_generic_value("MEMORY_DATA_WIDTH", 32)
writer0.set_generic_value("DIN_WIDTH", 32)

# Pipeline Data Layers
grey = pipe.add_layer("grey", 8, baselayer=True)
gauss = pipe.add_layer("gauss", 8)
cordic = pipe.add_layer("cordic", 4)
edge_x = pipe.add_layer("edge_x", 1)
edge_y = pipe.add_layer("edge_y", 1)

# Filter modules
fgauss = pipe.add_module("as_2dpipe_gauss", "gauss_filter")
fcordic = pipe.add_module("as_2dpipe_cordic", "cordic_filter")
fsobelx = pipe.add_module("as_2dpipe_sobel", "sobel_x")
fsobely = pipe.add_module("as_2dpipe_sobel", "sobel_y")

#########################
# Pipeline architecture #
#########################

#                                  /-> fsobel_y -> edge_y -> fcordic -> cordic -> collect1 -> writer1
# camera -> grey -> fgauss -> gauss -> fsobel_x -> edge_x ->/
#

# Pipeline inputs
grey.connect(camera.get("out"))

# Gauss filter
fgauss.connect("input", grey)
gauss.connect(fgauss.get("blurred"))

# Sobel filters
fsobelx.connect("in_grey", gauss)
fsobely.connect("in_grey", gauss)
fsobelx.connect("edge", edge_x)
fsobely.connect("edge", edge_y)

# Cordic filter
fcordic.connect("direction_x", edge_x)
fcordic.connect("direction_y", edge_y)
fcordic.connect("cordic", cordic)

# Pipeline outputs
cordic.connect(collect0.get("in"))

# Connect writers
collect0.connect(writer0)

# TODO: [CHECK]
#       interface names from vhdl:
#       interface name (no prefix/suffix): direction
#       interface name (multiple interfaces of different types without pre-/suffix): interface type + direction
#       interface name (prefix and/or suffix): prefix and suffix
# [WIP] add to manual


# TODO: [WIP]
#       visualisierung: Layer und filter am Beispiel Canny
#       Unterschied klar machen: Physikalische/Logische positionen/Referencen
#       Logische und Physische Sicht darstellen, Bild mit verknüpfungen zu Automatics methoden & objekten

# ↓ [!WIP!] ↓

pipe.__run_user_connect_calls__()
chain.write_asterics_core("astertest2d/", force=True)

print("Building done.\nGenerating graph...")
# as_vis.generate_2dpipe_graph(pipe, "./pipe_graph.svg")
asterics.write_system_graph(pipe, "asterics_2dwindow_graph", show_auto_inst=False)
print("Done")
# aft = pipe.add_module("as_filter_template")
# aft.list_module(3)

# aft.window_interfaces[0].print_interface(1)

# TODO:
# [CHECK] - modul.connect("interface_name" or object?, layer object (oder string), position)
#             evtl spezielidentifier für generischeres
#         - BRAM optimisation algorithms
#         - BRAM Hardware specifiers (module sizes, port widths, port count, ...)
# [NEXT]  - VHDL Code gen (look at old generator again)
#         - Pipeline footprint calculator
#         - "Randbehandlung" Ausschneiden, Spiegelung?, Torus?
#         - Module für Automatics anpassen


# Attributes:
# module.offset           : number of strobes (pixels into input of pipeline) before this module gets pixel (0,0)
# module.user_phys_offset : module.offset as set by user (may not be implementable!)
# module.delay            : number of strobes before this module outputs the input pixel
# layer.delay             : number of strobes before this layers pixel (0,0) contains input pixel (0,0)
# connect(offset)         : relative pixel offset for this connect operation. This tells Automatics:
#                           Move this layer in-/output ahead by (x,y) pixels, relative to the last out-/input
# inter.references        : pixel offsets (in strobes) relative to the offset of this interface's module
# layer.input_ref         : AsConnectionRef with the reference equal to layer.delay
# layer.output_refs       : list of all outputs of layer. references are the number of strobes
#                           until this in-/output contains pixel (0,0)
