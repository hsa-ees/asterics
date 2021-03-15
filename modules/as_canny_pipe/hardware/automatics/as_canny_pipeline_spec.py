# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_canny_pipeline_spec.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Python module used by as_automatics used to build the generators internal model
of the ASTERICS hardware module as_canny_pipeline.
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
# @file as_canny_pipeline_spec.py
# @author Philip Manke
# @brief Specifics for as_canny_pipeline used by as_automatics
# -----------------------------------------------------------------------------

from as_automatics_module import AsModule


def get_module_instance(module_dir: str) -> AsModule:

    module = AsModule()
    toplevel_file = "hardware/hdl/vhdl/as_canny_pipeline.vhd"
    module.files = []
    module.dependencies = [
        "as_regmgr",
        "as_generic_filter_module",
        "as_pipeline_flush",
        "as_edge_threshold",
        "as_edge_nms",
        "as_cordic_direction",
        "as_gradient_weight",
        "as_edge_list",
        "as_feature_counter",
        "helpers",
        "as_2d_conv_filter_internal",
        "as_pipeline_row",
        "as_window_pipeline_helper",
    ]
    module.show_in_browser = True
    module.dev_status = AsModule.DevStatus.BETA
    module.module_type = AsModule.ModuleTypes.HARDWARE_SW_CTRL
    module.module_category = "Image Processing Pipeline"

    # as_automatics now automatically parses the toplevel file and discovers
    # ports, generics, existing interfaces and register interfaces
    module.discover_module(module_dir + "/" + toplevel_file)

    return module
