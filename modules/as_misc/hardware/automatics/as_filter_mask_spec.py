# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# Copyright (C) Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_filter_mask_spec.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author: Philip Manke

Description:
Python module used by as_automatics used to build the generators internal model
of the ASTERICS hardware support library 'filter_mask'.
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
# @file as_filter_mask_spec.py
# @author Philip Manke
# @brief Specifics for support library 'filter_mask' used by as_automatics
# -----------------------------------------------------------------------------

from as_automatics_module import AsModule


def get_module_instance(module_dir: str) -> AsModule:
    module = AsModule("as_filter_mask")

    #                "hardware/hdl/vhdl/pkg/as_sim_ram_pkg.vhd",
    #toplevel_file = "hardware/hdl/vhdl/pkg/filter_mask.vhd"
    module.files = ["hardware/hdl/vhdl/pkg/as_filter_mask_pkg.vhd"]
    module.dependencies = []
    
    # As this is not a typical Automatics module (no VHDL entity)
    # we manually set the necessary attributes,
    # so Automatics can work with it normally
    module.module_dir = module_dir
    module.repository_name = "default"
    module.name = "as_filter_mask"
    module.entity_name = "as_filter_mask"
    module.generics = []
    module.standard_ports = []
    module.ports = []
    module.interfaces = []

    # Automatic module discovery would run into errors (no entity in 'filter_mask')
    # as_automatics now automatically parses the toplevel file and discovers
    # ports, generics, existing interfaces and register interfaces
    #module.discover_module("{mdir}/{toplevel}"
    #                       .format(mdir=module_dir, toplevel=toplevel_file))


    return module
