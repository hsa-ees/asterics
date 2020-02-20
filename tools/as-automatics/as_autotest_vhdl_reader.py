# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# Copyright (C) Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_autotest_vhdl_reader.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Module implementing unit tests for the as_automatics
module as_vhdl_reader.py
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
# @file as_autotest_vhdl_reader.py
# @author Philip Manke
# @brief Unit tests for as_vhdl_reader
# -----------------------------------------------------------------------------

import unittest as ut
import as_automatics_logging as as_log
from as_automatics_vhdl_reader import VHDLReader
from as_automatics_port import Port

LOG = as_log.get_log()


class TestVHDLReader(ut.TestCase):

    def setUp(self):
        # Set mut (Module Under Test)
        self.mut = VHDLReader("./unit-test-resources/vhdl_reader_testfile.vhd")

    def test_get_entity_name(self):
        LOG.debug("*UNITTEST* <running test_get_entity_name>")
        # Check that the entity name was identified correctly
        self.assertEqual(self.mut.get_entity_name(), "as_filter_permissive")

    def test_get_constants(self):
        LOG.debug("*UNITTEST* <running test_get_constants>")
        # Get constants
        constants = self.mut.get_constant_list()
        # Checks for constants. Only checking the constant formatted like the
        # slave register configuration tables.
        # Check the value, name, number of found constants and the data type
        self.assertEqual(constants[0].value,
                         ('("11","10","10","10","10","10","01","01","01","02",'
                          '"10","03","10","04","20","50","02","10","00","30",'
                          '"60","02","01","02","11","01","10","01","30","02",'
                          '"04","05","01","30","55","20","04","01","10","02",'
                          '"42","55","21","22","11","23","44","01","11","20",'
                          '"30","01","01","02","03","10","24","86","88","10",'
                          '"22","24","10","42")'))
        self.assertEqual(constants[0].code_name, "wonderful_constant_name")
        self.assertEqual(len(constants), 2)
        self.assertEqual(constants[0].data_type,
                         "slv_reg_config_table(0 to max_regs_per_module - 1)")

    def test_get_ports(self):
        LOG.debug("*UNITTEST* <running test_get_ports>")
        # Get the port list
        ports = self.mut.get_port_list()
        # Checks for the found ports:
        # Check the number of ports, name, direction, data type and data width
        self.assertEqual(len(ports), 7)
        self.assertEqual([port.code_name for port in ports],
                         ["clk", "reset", "ready", "mem_out_data", "wideport",
                          "invwideport", "expdatatest"])
        self.assertEqual([port.direction for port in ports],
                         ["in", "inout", "out", "out", "out", "in", "out"])
        self.assertEqual([port.data_type for port in ports],
                         ["std_logic", "std_logic", "std_logic",
                          "std_logic_vector", "bitvector", "vector",
                          "anothervector"])
        sdwtemp = Port.DataWidth(1, None, None)
        self.assertEqual([port.data_width for port in ports],
                         [sdwtemp, sdwtemp, sdwtemp,
                          Port.DataWidth("MEMORY_DATA_WIDTH - 1", "downto", 0),
                          Port.DataWidth(1023, "downto", 0),
                          Port.DataWidth(0, "to",
                                         "24 * 11 - 9 + MAX_REGS_PER_MODULE"),
                          Port.DataWidth(65535, "downto", 0)])

    def test_get_generics(self):
        LOG.debug("*UNITTEST* <running test_get_generics>")
        # Get the generic list
        generics = self.mut.get_generic_list()
        # Checks for found generics:
        # Check for number of generics, name, data type and default value
        self.assertEqual(len(generics), 4)
        self.assertEqual([gen.code_name for gen in generics],
                         ["MAX_REGS_PER_MODULE", "IMAGENERIC", "ANOTHERONE",
                          "LASTONE"])
        self.assertEqual([gen.data_type for gen in generics],
                         ["data_type", "string", "expression",
                          "intrusionattempt"])
        self.assertEqual([gen.default_value for gen in generics],
                         ["genericvalue", '"andthisismyvalue"', 63,
                          "eval(\"__import__(\'os\').listdir(\'/etc/\')\")"])

    def tearDown(self):
        self.mut = None


if __name__ == '__main__':
    LOG = as_log.init_log()
    LOG.disabled = True
    ut.main(exit=False)
