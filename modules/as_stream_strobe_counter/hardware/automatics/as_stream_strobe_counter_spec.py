# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2021 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_stream_strobe_counter_spec.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Python module used by Automatics used to build the generators internal model
of the ASTERICS hardware module as_stream_strobe_counter.
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
# @file as_stream_strobe_counter_spec.py
# @author Philip Manke
# @brief Specifics for as_stream_strobe_counter used by Automatics
# -----------------------------------------------------------------------------

from as_automatics_module import AsModule


def get_module_instance(module_dir: str) -> AsModule:

    module = AsModule()
    toplevel_file = "hardware/hdl/vhdl/as_stream_strobe_counter.vhd"
    module.files = []
    module.dependencies = []

    module.show_in_browser = True
    module.dev_status = AsModule.DevStatus.BETA
    module.module_type = AsModule.ModuleTypes.HARDWARE_SW_CTRL
    module.module_category = "Debugging Modules"

    # Automatics now automatically parses the toplevel file and discovers
    # ports, generics, existing interfaces and register interfaces
    module.discover_module(module_dir + "/" + toplevel_file)

    return module
