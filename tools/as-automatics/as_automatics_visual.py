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
# @ingroup automatics_generate
# @author Philip Manke
# @brief Implements various visualization methods for as_automatics.
# -----------------------------------------------------------------------------


import copy
import importlib

from as_automatics_2d_pipeline import As2DWindowPipeline
from as_automatics_module import AsModule
from as_automatics_interface import Interface
from as_automatics_port import Port
from as_automatics_signal import GenericSignal
from as_automatics_proc_chain import AsProcessingChain
from as_automatics_connection_helper import get_parent_module
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


##
# @addtogroup automatics_generate
# @{


class Graph:
    """! @brief Automatic's own graph class - keeps track of nodes added to the graph.
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
    show_line_buffers: bool,
    *,
    return_graph: bool = False
):
    """! @brief Implemenation of the SVG graph drawing function.
    For more information, check
    as_automatics_proc_chain::AsProcessingChain::write_system_graph()."""
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
    all_modules = [
        mod
        for mod in all_modules
        if not isinstance(mod.parent, As2DWindowPipeline)
    ]
    all_modules.append(chain.as_main)
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
                # All ports of toplevel are unconnected; don't print
                if module is not chain.top:
                    # Add all unconnected ports to the module node label
                    uncon = module.get_unconnected_ports()
                    uncon = [port.code_name for port in uncon]
                    if uncon:
                        label += "\n\nUnconnected ports:\n" + "\n".join(uncon)
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
                inter_label += "\n".join(
                    [port.code_name for port in inter.ports]
                )
            # For interfaces from or to external (on toplevel)
            if (
                show_toplevels
                and inter.to_external
                and (inter.parent is chain.top)
            ):
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
                # If target is a mock GlueSignal (no parent)
                if target is not None:
                    if target.parent is None:
                        target = None
                    if "signal" in target.port_type:
                        target = None
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
                    # If target is a mock GlueSignal (no parent)
                    if target is not None:
                        if target.parent is None:
                            target = None
                        if "signal" in target.port_type:
                            target = None  # Stop at the last port
                    if count == len(inter.ports):
                        break
                    # Skip single port targets
                    if (
                        isinstance(target, Port)
                        and target.port_type == "single"
                    ):
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

    # Add any 2D Window pipelines to the graph
    for pipe in chain.pipelines:
        add_2dpipe_subgraph(pipe, graph, show_line_buffers=show_line_buffers)

    if return_graph:
        return graph.graph
    else:
        # Render and write graph file
        graph.write_svg(out_file)


def add_2dpipe_subgraph(
    pipe: As2DWindowPipeline,
    ggraph: Graph,
    show_line_buffers: bool,
):
    def get_target_mods(target, targets=[]) -> list:
        mods = []
        targets.append(target)
        if isinstance(target, GenericSignal):
            for sig in target.outgoing:
                if sig in targets:
                    return []
                mods.extend(get_target_mods(sig, targets))
        else:
            mods.append(get_parent_module(target))
        return list(set(mods))

    mod_form = {"style": "filled, bold", "color": "blue", "fillcolor": "white"}
    buf_form = {"shape": "box", "style": "filled", "fillcolor": "white"}
    with ggraph.graph.subgraph(name="cluster_" + pipe.name) as subg:
        graph = Graph(subg)
        graph.graph.attr(
            style="filled, rounded",
            fillcolor="lightgrey",
            label="2D Window Pipeline: {}".format(pipe.name),
        )
        # Exclude flushing module
        added_mods = [pipe.pipe_manager]
        for buff in pipe.buffer_rows:
            added_mods.append(buff.module)
            if not show_line_buffers:
                continue
            name = buff.name
            label = "Module '{}'\ndelay: {}\nlength: {}".format(
                name, buff.input_delay, buff.length
            )

            graph.add_node(name=name, label=label, form=buf_form)

        # Generate nodes
        for mod in pipe.modules:
            if mod in added_mods:
                continue
            name = mod.name
            label = "Module '{}'\nOutput delay: {}".format(name, mod.delay)
            # Add the module node
            graph.add_node(name=name, label=label, form=mod_form)

        # Generate edges
        for mod in pipe.modules:
            source = mod.name
            for port in mod.get_full_port_list():
                if port.get_direction_normalized() == "in":
                    continue
                for target in port.outgoing:
                    if target.code_name == "pipeline_stream_in":
                        continue
                    target_mods = get_target_mods(target)
                    for target_mod in target_mods:
                        if target_mod is pipe:
                            continue
                        graph.add_edge(
                            source,
                            target_mod.name,
                            port.code_name + " ->\n" + target.code_name,
                        )
    ggraph.nodes.extend(graph.nodes)
    for in_stream in pipe.input_streams:
        tail = get_parent_module(in_stream.stream).name
        if isinstance(in_stream.stream, Interface):
            label = "{} ->\n{}\n({})".format(
                in_stream.stream.name,
                in_stream.target.name,
                in_stream.stream.type,
            )
        else:
            label = in_stream.stream.code_name
        for target in in_stream.signal.outgoing:
            if isinstance(target, GenericSignal):
                continue
            head = get_parent_module(target).name
            ggraph.add_edge(tail, head, label)
    for out_stream in pipe.output_streams:

        tail = get_parent_module(out_stream.source).name
        head = out_stream.target_stream.parent.name
        label = "{} ->\n{}\n({})".format(
            out_stream.source.name,
            out_stream.stream.name,
            out_stream.stream.type,
        )
        ggraph.add_edge(tail, head, label)


def write_graph_svg(graph, out_file: str):
    graph.format = "svg"
    graph.render(out_file, cleanup=True)


## @}
