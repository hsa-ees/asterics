# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_pipeline_row_spec.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author: Philip Manke

Description:
Python module used by as_automatics used to build the generators internal model
of the ASTERICS hardware support library 'as_pipeline_row'.
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
# @file as_pipeline_row_spec.py
# @author Philip Manke
# @brief Specifics for support component 'as_pipeline_row' used by as_automatics
# -----------------------------------------------------------------------------

from as_automatics_2d_window_module import AsWindowModule


def get_module_instance(module_dir: str) -> AsWindowModule:
    module = AsWindowModule()

    toplevel_file = "hardware/hdl/vhdl/pipeline/as_pipeline_row.vhd"
    module.files = [
        "hardware/hdl/vhdl/pipeline/as_line_buffer.vhd",
        "hardware/hdl/vhdl/pipeline/as_shift_line.vhd",
        "hardware/hdl/vhdl/pipeline/as_fifo.vhd",
    ]
    module.dependencies = ["as_generic_filter", "DUAL_BRAM_READ_FIRST"]

    module.show_in_browser = False
    module.dev_status = AsWindowModule.DevStatus.BETA
    module.module_type = AsWindowModule.ModuleTypes.HARDWARE
    module.module_category = "Internal Submodules"

    # as_automatics now automatically parses the toplevel file and discovers
    # ports, generics, existing interfaces and register interfaces
    module.discover_module(module_dir + "/" + toplevel_file)

    return module
