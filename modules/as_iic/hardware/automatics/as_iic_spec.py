# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_iic_spec.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Python module used by as_automatics used to build the generators internal model
of the ASTERICS hardware module as_iic.
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
# @file as_iic_spec.py
# @author Philip Manke
# @brief Specifics for as_iic used by as_automatics
# -----------------------------------------------------------------------------


from as_automatics_module import AsModule
from as_automatics_interface import Interface
from as_automatics_port import Port


class IIC_Interface(Interface):
    def __init__(self):
       super().__init__("iic_interface")
       self.add_port(Port("scl_in", direction="in"))
       self.add_port(Port("scl_out", direction="out"))
       self.add_port(Port("scl_out_enable", direction="out"))
       self.add_port(Port("sda_in", direction="in"))
       self.add_port(Port("sda_out", direction="out"))
       self.add_port(Port("sda_out_enable", direction="out"))
       self.to_external = True


def get_module_instance(module_dir: str) -> AsModule:

    module = AsModule()
    toplevel_file = "hardware/hdl/vhdl/as_iic.vhd"
    module.files = []
    module.dependencies = ["helpers", "as_regmgr"]

    module.add_local_interface_template(IIC_Interface())

    # as_automatics now automatically parses the toplevel file and discovers
    # ports, generics, existing interfaces and register interfaces
    module.discover_module("{mdir}/{toplevel}"
                           .format(mdir=module_dir, toplevel=toplevel_file))

    return module
