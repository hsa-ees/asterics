# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# Copyright (C) Hochschule Augsburg, University of Applied Sciences
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

from typing import Sequence
import copy

import graphviz as gv

from as_automatics_module import AsModule
from as_automatics_interface import Interface
from as_automatics_port import Port
import as_automatics_logging as as_log

LOG = as_log.get_log()


def generate_module_graph(all_modules: Sequence[AsModule], out_file: str):

    graph = gv.Digraph(name="AsModule Graph")
    # TODO: Add graph node representing "External"

    # Generate nodes
    for mod in all_modules:
        name = mod.name
        # Add all unconnected ports to the node label
        # Skip toplevel, as it only has unconnencted ports
        if mod.name != "asterics":
            uncon_ports = mod.get_unconnected_ports()

            uncon = "Unconnected:"
            for port in uncon_ports:
                uncon = "{}\n{}".format(uncon, port.code_name)
            if not uncon_ports:
                uncon = ""
        # Add the module node
        graph.node(name=name, label="{}\n{}".format(name, uncon))

    # Generate edges
    for mod in all_modules:
        # Skip toplevel (would only generate unconnected ports)
        if mod.name == "asterics":
            continue

        # Gather all objects that we want to draw as edges
        edges = copy.copy(mod.ports)
        edges.extend(mod.standard_ports)
        edges.extend(mod.interfaces)

        # For all edges
        for edge in edges:
            # For interfaces
            if isinstance(edge, Interface):
                # Use the unique name to label the edge
                label = edge.unique_name + ":"
                # Followed by a list of all ports of the interface
                for port in edge.ports:
                    label = "{}\n{}".format(label, port.code_name)
            # For ports, the glue signal, if present
            elif edge.glue_signal:
                label = edge.glue_signal.name
            elif edge.code_name:  # else, the code_name.
                label = edge.code_name
            else:  # For modules, use the user-set module name
                label = edge.name

            # Determine edge direction: in
            if edge.direction == "in":
                if edge.incoming:
                    if isinstance(edge.incoming, list):
                        target = AsModule.get_parent_module(
                            edge.incoming[-1]).name
                    else:
                        target = AsModule.get_parent_module(edge.incoming).name
                else:
                    target = "__uncon__"

            else:  # edge direction: out
                if edge.outgoing:
                    if isinstance(edge.outgoing[0], str):
                        target = "__uncon__"
                    else:
                        target = AsModule.get_parent_module(edge.outgoing[0])
                        target = getattr(target, "name", target)
                else:
                    target = "__uncon__"
            # If not marked as "__uncon__", add the edge to the graph
            if target != "__uncon__":
                graph.edge(mod.name, target, label)
    graph.format = "svg"
    graph.render(out_file, cleanup=True)
