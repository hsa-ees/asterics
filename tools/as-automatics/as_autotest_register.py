# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# Copyright (C) Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_autotest_register.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Module implementing unit tests for the as_automatics
module as_automatics_register.py
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
# @file as_autotest_register.py
# @author Philip Manke
# @brief Unit tests for as_automatics_register
# -----------------------------------------------------------------------------

import unittest as ut
from as_automatics_register import *
from as_automatics_port import Port
from as_automatics_constant import Constant
import as_automatics_logging as as_log

LOG = as_log.get_log()


class TestSlvRegIf(ut.TestCase):

    def setUp(self):
        self.regif = SlaveRegisterInterface()
        testports = [Port(name="slv_status_reg", data_type="slv_reg_data",
                          direction="out"),
                     Port(name="slv_reg_modify", data_type="std_logic_vector",
                          direction="out"),
                     Port(name="slv_reg_config",
                          data_type="slv_reg_config_table",
                          direction="out")]
        self.regif.ports = testports
        self.regif.config = \
            Constant(name="slave_register_configuration",
                     value='("11","11","01","01","01","10","10","00");')

    def test_is_complete(self):
        LOG.debug("*UNITTEST* <running test_is_complete>")
        # setUp() adds all required ports except for one, this should fail
        self.assertFalse(self.regif.is_complete())
        # Manually (not using add_port()) add the missing port
        tport = REGIF_PORTS[1]
        self.regif.ports.append(
            Port(
                name=tport.name,
                direction=tport.direction,
                data_type=tport.data_type))
        # Now the regif should report itself as complete
        self.assertTrue(self.regif.is_complete())

    def test_remove_port(self):
        LOG.debug("*UNITTEST* <running test_remove_port>")
        # Count the number of ports already present
        port_count = len(self.regif.ports)
        # Remove a valid port
        self.assertTrue(self.regif.remove_port("slv_status_reg"))
        # This specific port should now be missing from the list of ports
        self.assertNotIn("slv_status_reg",
                         [port.name for port in self.regif.ports])
        # The number of ports should now be one fewer
        self.assertEqual(port_count - 1, len(self.regif.ports))
        # Remove another port, this time the last one in the list
        self.assertTrue(self.regif.remove_port("slv_reg_config"))
        self.assertNotIn("slv_reg_config",
                         [port.name for port in self.regif.ports])
        self.assertEqual(port_count - 2, len(self.regif.ports))
        # Try to remove a port that is already missing, this should fail
        self.assertFalse(self.regif.remove_port("slv_reg_config"))

    def test_add_port_wo_pre_suffix(self):
        LOG.debug("*UNITTEST* <running test_add_port_wo_pre_suffix>")
        # Test without pre-/suffixes
        testport_p = Port(name="slv_ctrl_reg", data_type="slv_reg_data")
        testport_n = Port(name="slv_reg_config", direction="out",
                          data_type="slv_reg_config_table")
        #  self.regif.list_ports()
        self.assertTrue(self.regif.add_port(testport_p))
        self.assertFalse(self.regif.add_port(testport_p))
        self.assertFalse(self.regif.add_port(testport_n))

    def test_add_port_w_pre_suffix(self):
        LOG.debug("*UNITTEST* <running test_add_port_w_pre_suffix>")
        # Test with suffixes

        # Start with fresh regif for this test
        self.regif = SlaveRegisterInterface()
        testport_p = Port(code_name="right_slv_ctrl_reg_42",
                          name="slv_ctrl_reg", data_type="slv_reg_data")
        testport_n = Port(name="slv_reg_config", direction="out",
                          data_type="slv_reg_config_table")

        # Add a port with suffix and prefix. This should work regardless
        self.assertTrue(self.regif.add_port(testport_p))
        testport_p = Port(code_name="right_slv_reg_modify_42",
                          name="slv_reg_modify", data_type="std_logic_vector",
                          direction="out")
        # Add another port using the same fixes. This should work
        self.assertTrue(self.regif.add_port(testport_p))
        # Try to add a port without fixes.
        self.assertFalse(self.regif.add_port(testport_n))
        testport_n = Port(code_name="42_slv_reg_config_right",
                          name="slv_reg_config", direction="out",
                          data_type="slv_reg_config_table")
        # Another negative test using the wrong fixes
        self.assertFalse(self.regif.add_port(testport_n))

    def test_set_config_constant(self):
        LOG.debug("*UNITTEST* <running test_set_config_constant>")
        testconfig = \
            Constant(name="slave_register_configuration",
                     value='("11","11","01","01","01","10","10","00");')
        # setUp() already adds a config constant, this should fail
        self.assertFalse(self.regif.set_config_constant(testconfig))
        # Remove the present config and check if that worked
        self.regif.clear_config_const()
        self.assertIsNone(self.regif.config, "clear_config_const failed!")
        # Try to add a Port object as the config. This should raise a TypeError
        testport = Port(name="slave_register_configuration")
        with self.assertRaises(TypeError):
            self.regif.set_config_constant(testport)
        # Try to add a config with an invalid suffix
        testconfig.code_name = "slave_register_configuration_42"
        self.assertFalse(self.regif.set_config_constant(testconfig))
        # Try to add a valid config constant
        testconfig.code_name = "slave_register_configuration"
        self.assertTrue(self.regif.set_config_constant(testconfig))

    def test_decode_slvreg_table(self):
        LOG.debug("*UNITTEST* <running test_decode_slvreg_table>")
        # Prepare a config constant with too many definitions
        testconfig_h = Constant(name="slave_register_configuration",
                                value=('("11","11","01","01","01","10",'
                                       '"10","00","00","00");'))
        result_h = ["HW <=> SW", "HW <=> SW", "HW -> SW", "HW -> SW",
                    "HW -> SW", "HW <- SW", "HW <- SW", "None", "None", "None"]
        # And one with too few
        testconfig_l = Constant(name="slave_register_configuration",
                                value='("11","11","01","01","01","10");')
        result_l = ["HW <=> SW", "HW <=> SW", "HW -> SW", "HW -> SW",
                    "HW -> SW", "HW <- SW"]
        # One with the correct number of definitions including an invalid value
        testconfig_i = Constant(name="slave_register_configuration",
                                value=('("11","11","21","01",'
                                       '"01","10","00","00");'))
        # Another one that uses the "(others => X)" syntax
        testconfig_o = Constant(name="slave_register_configuration",
                                value='("11","11","01",(others => "10");')
        result_o = ["HW <=> SW", "HW <=> SW", "HW -> SW", "HW <- SW"]
        # Another one now with an invalid value in the others-clause
        testconfig_oi = Constant(name="slave_register_configuration",
                                 value='("11","11","01",(others => "12");')
        # Run the decoding (indirectly) for the setUp config and compare
        # to the expected result: (2, 3, 2)
        self.assertEqual(self.regif.get_register_numbers(), (2, 3, 2))
        # Set a different config
        self.regif.clear_config_const()
        self.regif.config = testconfig_h
        # Directly call the decode function.
        # Using a config with ten registers, check if all are recognized:
        self.assertTrue(self.regif.__decode_slvreg_table__())
        self.assertEqual(self.regif.reg_count, 7)
        self.assertEqual(self.regif.register_table, result_h)
        # Same test, now using the config with fewer definitions
        self.regif.clear_config_const()
        self.regif.config = testconfig_l
        self.assertTrue(self.regif.__decode_slvreg_table__())
        self.assertEqual(self.regif.reg_count, 6)
        self.assertEqual(self.regif.register_table, result_l)
        # Same test, now using the config with an invalid value
        self.regif.clear_config_const()
        self.regif.config = testconfig_i
        self.assertFalse(self.regif.__decode_slvreg_table__())
        # Now using the config with the others-clause
        self.regif.clear_config_const()
        self.regif.config = testconfig_o
        # This should work and return a result
        self.assertEqual(self.regif.get_register_numbers(), (2, 1, 1))
        self.assertEqual(self.regif.register_table, result_o)
        # Now using the config with an invalid value in the others-clause
        self.regif.clear_config_const()
        self.regif.config = testconfig_oi
        self.assertFalse(self.regif.__decode_slvreg_table__())

    def tearDown(self):
        self.regif = None


if __name__ == '__main__':
    LOG = as_log.init_log()
    LOG.disabled = True
    ut.main(exit=False)
