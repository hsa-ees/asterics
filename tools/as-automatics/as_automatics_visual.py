# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_automatics_visual.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Implements various visualization methods for as_automatics.
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
#
# --------------------- DOXYGEN -----------------------------------------------
##
# @file as_automatics_visual.py
# @author Philip Manke
# @brief Implements various visualization methods for as_automatics.
# -----------------------------------------------------------------------------


import copy
import importlib

from as_automatics_2d_pipeline import As2DWindowPipeline
from as_automatics_window_module import AsWindowModule, AsWindowInterface
from as_automatics_2d_infrastructure import AsLayer
from as_automatics_module import AsModule
from as_automatics_interface import Interface
from as_automatics_port import Port
from as_automatics_proc_chain import AsProcessingChain
import as_automatics_logging as as_log

LOG = as_log.get_log()

# Check if Graphviz is installed before importing,
# we don't want all of Automatics to fail if not installed!
graphviz_available = bool(importlib.util.find_spec("graphviz"))
if graphviz_available:
    import graphviz as gv
else:
    LOG.warning(
        (
            "Could not find python graphviz package on your system."
            " Visualization features will be unavailable."
        )
    )


class Graph:
    """Automatic's own graph class. Keeps track of nodes added to the graph.
    Sadly no nice interface for checking for added nodes exists in graphviz
    (not that I'm aware of, anyways).
    The default behaviour of the graphviz API is to automatically add nodes 
    that don't exist when adding edges - we don't want this here!"""

    def __init__(self, graph):
        self.graph = graph
        self.nodes = []
        self.default_form = {"style": "filled", "fillcolor": "white"}

    def add_node(self, name: str, label: str = "", form: dict = None):
        self.nodes.append(name)
        if form is None:
            form = self.default_form
        self.graph.node(name, label, **form)

    def has_node(self, name: str):
        return name in self.nodes

    def add_edge(self, tail: str, head: str, label: str = "") -> bool:
        # Only draw the edge if both nodes exist
        if not (self.has_node(tail) and self.has_node(head)):
            return False
        # => Else
        self.graph.edge(tail, head, label)
        return True

    def write_svg(self, out_file: str):
        # Render and write the graph in SVG format
        self.graph.format = "svg"
        self.graph.render(out_file, cleanup=True)


def system_graph(
    chain: AsProcessingChain,
    out_file: str,
    show_ports: bool,
    show_auto_inst: bool,
    show_unconnected: bool,
    show_toplevels: bool,
    *,
    return_graph: bool = False
):
    # Instanciate graphviz graph
    gv_graph = gv.Digraph(name="AsModule Graph")
    # Small custom management class. Keeps track of added nodes
    graph = Graph(gv_graph)

    # External inputs and outputs, plus node names
    ext_in_name = "External Inputs"
    ext_out_name = "External Outputs"
    ext_in_added = False
    ext_out_added = False
    ext_form = {"shape": "diamond", "style": "bold"}

    # Gather modules
    all_modules = copy.copy(chain.modules)
    all_modules.extend(chain.module_groups)
    all_modules.append(chain.top)

    # Add one node for each module
    for module in all_modules:
        # If auto-instantiated modules should be shown, add all modules
        if (module not in chain.auto_instantiated) or show_auto_inst:
            if not show_toplevels and module in (chain.top, chain.as_main):
                continue
            label = module.name
            # If unconnected ports should be shown:
            if show_unconnected:
                # Add all unconnected ports to the module node label
                uncon = module.get_unconnected_ports()
                uncon = [port.name for port in uncon]
                label += ":\n" + "\n".join(uncon)
            graph.add_node(module.name, label)

    # Interfaces to skip:
    # For each interface from A to B, a connection from B to A exists.
    # If we already added A to B or B to A, we skip the connection in the
    # reverse direction.
    skip_inters = []

    # Draw connections (edges) for each interface of each module
    for module in all_modules:
        for inter in module.interfaces:
            # Skip interfaces we already added the connection for
            if inter in skip_inters and module is not chain.top:
                continue

            inter_label = "{}\n{}".format(inter.name, inter.type)
            # Add a port list to the interface label
            if show_ports:
                inter_label += ":\n"
                inter_label += "\n".join([port.name for port in inter.ports])
            # For interfaces from or to external (on toplevel)
            if show_toplevels and inter.to_external and (inter.parent is chain.top):
                if inter.direction == "in":
                    if not ext_in_added:  # Add an external node, if necessary
                        graph.add_node(ext_in_name, ext_in_name, ext_form)
                    tail = ext_in_name
                    head = inter.parent.name
                else:
                    if not ext_out_added:  # Add an external node, if necessary
                        graph.add_node(ext_out_name, ext_out_name, ext_form)
                    tail = inter.parent.name
                    head = ext_out_name
                # Draw the edge
                graph.add_edge(tail, inter.parent.name, inter_label)
            else:
                # Source module name
                tail_module = inter.parent
                tail = tail_module.name

                # Get a port of the source interface
                p0 = inter.ports[0]
                # Get the port it's connected to
                # (we can't rely on interface connections)
                target = (
                    p0.incoming
                    if p0.get_direction_normalized() == "in"
                    else p0.outgoing[0]
                    if p0.outgoing
                    else None
                )
                # Count the ports tried
                count = 1
                # If no connection exists for this port, try until we get one
                while target is None:
                    p0 = inter.ports[count]
                    target = (
                        p0.incoming
                        if p0.get_direction_normalized() == "in"
                        else p0.outgoing[0]
                        if p0.outgoing
                        else None
                    )
                    count += 1
                    # Stop at the last port
                    if count == len(inter.ports):
                        break
                    # Skip single port targets
                    if isinstance(target, Port) and target.port_type == "single":
                        target = None
                # Still no connection? Skip this interface
                if target is None:
                    continue

                # Get the interface of the target port,
                head_inter = target.parent
                # the interface' parent module
                head_module = head_inter.parent

                if not show_auto_inst:
                    # If the tail module was auto-instantiated to the toplevel,
                    # substitute tail with as_main
                    if (head_module is chain.top) and (
                        tail_module in chain.auto_instantiated
                    ):
                        tail = chain.as_main.name
                    # Same treatment the other way around
                    elif (tail_module is chain.top) and (
                        head_module in chain.auto_instantiated
                    ):
                        head_module = chain.as_main

                # and the interface's parent module's name
                head = head_module.name

                # Since the edge we'll draw covers the target interface,
                # we don't need to handle it (we'd draw the connection twice!).
                if not head_inter.to_external:
                    skip_inters.append(head_inter)
                # Interface direction infers edge (arrow) direction
                if inter.direction == "in":
                    graph.add_edge(head, tail, inter_label)
                else:
                    graph.add_edge(tail, head, inter_label)
    if return_graph:
        return graph.graph
    else:
        # Render and write graph file
        graph.write_svg(out_file)


def add_2dpipe_subgraph(pipe: As2DWindowPipeline, graph):
    tgraph = graph
    with tgraph.subgraph(name="cluster_pipe2d") as subg:
        graph = subg
        graph.attr(
            style="filled, rounded", fillcolor="lightgrey", label="2D Window Pipeline"
        )
        # Generate nodes
        for mod in pipe.window_modules:
            name = mod.name
            label = "Module '{}'\noffset{}".format(name, mod.offset)
            # Add the module node
            graph.node(
                name=name,
                label=label,
                style="filled, bold",
                color="blue",
                fillcolor="white",
            )

        for layer in pipe.layers:
            label = "Layer '{}'\noffset{}".format(layer.name, layer.offset)
            graph.node(
                name=layer.name,
                label=label,
                shape="box",
                style="filled",
                fillcolor="white",
            )

        def make_window_edge(graph, layer, refs, end: bool = False):
            out = "Window '{}':\n".format(refs[0].port.name)
            count = 0
            leave_count = 1 if end else 2
            while len(refs) > leave_count:
                out += str(refs.pop(0).get_ref()) + ", "
                count += 1
                if count == 3:
                    count = 0
                    out += "\n"
            crt_ref = refs.pop(0)
            out += str(crt_ref.get_ref())
            graph.edge(layer.name, crt_ref.port.parent.parent.name, out)

        def make_edge(graph, layer, refs, tgraph):
            crt_ref = refs.pop(0)
            # Add edges to going outside the pipeline to the top graph
            if isinstance(crt_ref.port.parent.parent, AsWindowModule):
                graph.edge(
                    layer.name, crt_ref.port.parent.parent.name, str(crt_ref.get_ref())
                )
            else:
                tgraph.edge(
                    layer.name, crt_ref.port.parent.parent.name, str(crt_ref.get_ref())
                )

        # Generate edges
        for layer in pipe.layers:
            refs = []
            to_mod = layer.input.port.parent.parent
            # Add edges going into the pipeline to the top graph
            if isinstance(to_mod, AsWindowModule):
                graph.edge(to_mod.name, layer.name, str(layer.offset.get_ref()))
            else:
                tgraph.edge(to_mod.name, layer.name, str(layer.offset.get_ref()))
            for ref in layer.output_refs:
                if not refs:
                    refs.append(ref)
                else:
                    refs.append(ref)
                    if refs[0].port is not ref.port and len(refs) == 2:
                        make_edge(graph, layer, refs, tgraph)
                    elif refs[0].port is not ref.port and len(refs) > 2:
                        make_window_edge(graph, layer, refs)
            if len(refs) > 1:
                make_window_edge(graph, layer, refs, end=True)
            else:
                make_edge(graph, layer, refs, tgraph)


def write_graph_svg(graph, out_file: str):
    graph.format = "svg"
    graph.render(out_file, cleanup=True)


def generate_2dpipe_graph(pipe: As2DWindowPipeline, out_file: str):

    graph = gv.Digraph(name="AsModule Graph")
    # TODO: Add graph node representing "External"

    # Generate nodes
    for mod in pipe.window_modules:
        name = mod.name
        label = "Module '{}'\noffset{}".format(name, mod.offset)
        # Add the module node
        graph.node(name=name, label=label)

    for layer in pipe.layers:
        label = "Layer '{}'\noffset{}".format(layer.name, layer.offset)
        graph.node(name=layer.name, label=label)

    def make_window_edge(graph, layer, refs, end: bool = False):
        out = "Window '{}':\n".format(refs[0].port.name)
        count = 0
        leave_count = 1 if end else 2
        while len(refs) > leave_count:
            out += str(refs.pop(0).get_ref()) + ", "
            count += 1
            if count == 3:
                count = 0
                out += "\n"
        crt_ref = refs.pop(0)
        out += str(crt_ref.get_ref())
        graph.edge(layer.name, crt_ref.port.parent.parent.name, out)

    def make_edge(graph, layer, refs):
        crt_ref = refs.pop(0)
        graph.edge(layer.name, crt_ref.port.parent.parent.name, str(crt_ref.get_ref()))

    # Generate edges
    for layer in pipe.layers:
        refs = []
        graph.edge(
            layer.input.port.parent.parent.name, layer.name, str(layer.offset.get_ref())
        )
        for ref in layer.output_refs:
            if not refs:
                refs.append(ref)
            else:
                refs.append(ref)
                if refs[0].port is not ref.port and len(refs) == 2:
                    make_edge(graph, layer, refs)
                elif refs[0].port is not ref.port and len(refs) > 2:
                    make_window_edge(graph, layer, refs)
        if len(refs) > 1:
            make_window_edge(graph, layer, refs, end=True)
        else:
            make_edge(graph, layer, refs)

    graph.format = "svg"
    graph.render(out_file, cleanup=True)
