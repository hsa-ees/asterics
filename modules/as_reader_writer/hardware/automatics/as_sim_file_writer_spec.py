# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_memwriter_spec.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Python module used by as_automatics used to build the generators internal model
of the ASTERICS hardware module as_memwriter.
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
# @file as_memwriter_spec.py
# @author Philip Manke
# @brief Specifics for as_memwriter used by as_automatics
# -----------------------------------------------------------------------------

from as_automatics_module import AsModule
from as_automatics_interface import Interface
from as_automatics_port import Port


class SimWriterRegisterInterface(Interface):

    INTERFACE_TYPE_NAME = "sim_writer_register_interface"

    def __init__(self):
        super().__init__(self.INTERFACE_TYPE_NAME)
        self.add_port(
            Port(
                "control",
                direction="in",
                data_type="std_logic_vector",
                data_width=(15, "downto", 0),
            )
        )
        self.add_port(
            Port(
                "control_reset",
                direction="out",
                data_type="std_logic_vector",
                data_width=(15, "downto", 0),
            )
        )
        self.add_port(
            Port(
                "state",
                direction="out",
                data_type="std_logic_vector",
                data_width=(15, "downto", 0),
            )
        )
        self.add_port(
            Port(
                "force_done",
            )
        )
        self.add_port(
            Port(
                "reg_section_addr",
                direction="in",
                data_type="std_logic_vector",
                data_width=(31, "downto", 0),
            )
        )
        self.add_port(
            Port(
                "reg_section_offset",
                direction="in",
                data_type="std_logic_vector",
                data_width=(31, "downto", 0),
            )
        )
        self.add_port(
            Port(
                "reg_section_size",
                direction="in",
                data_type="std_logic_vector",
                data_width=(31, "downto", 0),
            )
        )
        self.add_port(
            Port(
                "reg_section_count",
                direction="in",
                data_type="std_logic_vector",
                data_width=(31, "downto", 0),
            )
        )
        self.add_port(
            Port(
                "reg_max_burst_length",
                direction="in",
                data_type="std_logic_vector",
                data_width=(31, "downto", 0),
            )
        )
        self.add_port(
            Port(
                "reg_current_hw_addr",
                direction="out",
                data_type="std_logic_vector",
                data_width=(31, "downto", 0),
            )
        )

        self.to_external = True


def get_module_instance(module_dir: str) -> AsModule:

    module = AsModule()

    module.add_local_interface_template(SimWriterRegisterInterface())

    toplevel_file = "hardware/hdl/vhdl/sim/as_sim_file_writer.vhd"
    module.files = []
    module.dependencies = ["as_sim_ram_pkg", "helpers"]
    module.show_in_browser = True
    module.dev_status = AsModule.DevStatus.STABLE
    module.module_type = AsModule.ModuleTypes.HARDWARE_SOFTWARE
    module.module_category = "Simulation Resources"

    # as_automatics now automatically parses the toplevel file and discovers
    # ports, generics, existing interfaces and register interfaces
    module.discover_module(module_dir + "/" + toplevel_file)

    module.driver_files = [
        "hardware/hdl/vhdl/sim/write_byte.h",
        "hardware/hdl/vhdl/sim/write_byte.c",
    ]

    return module
