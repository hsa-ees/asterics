# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_sensor_ov7670_spec.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Python module used by as_automatics used to build the generators internal model
of the ASTERICS hardware module as_sensor_ov7670.
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
# @file as_sensor_ov7670_spec.py
# @author Philip Manke
# @brief Specifics for as_sensor_ov7670 used by as_automatics
# -----------------------------------------------------------------------------

from as_automatics_module import AsModule

# Import and retrieve an instance of the Automatics Python logging module
import as_automatics_logging as as_log

LOG = as_log.get_log()


def get_module_instance(module_dir: str) -> AsModule:

    module = AsModule()
    toplevel_file = "hardware/hdl/vhdl/as_sensor_ov7670.vhd"

    module.files = []
    module.dependencies = ["as_regmgr"]

    module.show_in_browser = True
    module.dev_status = AsModule.DevStatus.STABLE
    module.module_type = AsModule.ModuleTypes.HARDWARE_SW_CTRL
    module.module_category = "External IO"

    # as_automatics now automatically parses the toplevel file and discovers
    # ports, generics, existing interfaces and register interfaces
    module.discover_module(module_dir + "/" + toplevel_file)

    module.iic_masters = []
    module.iic_masters_available = ("XILINX_PL_IIC", "XILINX_PS_IIC", "AS_IIC")

    # Special function definitions for as_sensor_ov7670 module:
    def add_iic_master(self, iic_type: str):
        self.iic_masters.append(iic_type)
        LOG.info("Added IIC master '%s' to '%s'", iic_type, self.name)

    def set_iic_masters(self, iic_types: list):
        self.iic_masters = iic_types

    def list_iic_masters(self):
        print("IIC masters available for '{}':".format(self.name))
        for iic in self.iic_masters_available:
            print(" - '{}'".format(iic))
        print("")

    def overwrite_sw_additions(self) -> list:
        additions = []
        for master in self.iic_masters:
            additions.append("#define AS_USING_{}".format(master.upper()))
        return additions

    # Assign functions to module instance
    # The call to "__get__(module)" is necessary and "binds" the method
    # the instance AsModule instance "module" that was created here!
    # Syntax:
    # module.<function_name (user script)> = <function to add>.__get__(module)
    module.set_iic_masters = set_iic_masters.__get__(module)
    module.add_iic_master = add_iic_master.__get__(module)
    module.list_iic_masters = list_iic_masters.__get__(module)
    module.get_software_additions = overwrite_sw_additions.__get__(module)

    return module
