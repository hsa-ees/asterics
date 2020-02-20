# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_autotest_module.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Module implementing unit tests for the as_automatics
module as_automatics_module.py
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
# @file as_autotest_module.py
# @author Philip Manke
# @brief Unit tests for as_automatics_module
# -----------------------------------------------------------------------------

import unittest as ut
from as_automatics_module import AsModule
from as_automatics_port import Port
from as_automatics_generic import Generic
from as_automatics_constant import Constant
from as_automatics_interface import Interface
from as_automatics_register import SlaveRegisterInterface
import as_automatics_templates as as_templates
import as_automatics_logging as as_log

LOG = as_log.get_log()


class TestAsModule(ut.TestCase):

    def setUp(self):
        as_templates.add_templates()
        self.mut = AsModule("Testmodule")
        test_if = Interface("as-stream")
        test_if.template = as_templates.AsStream()
        test_if.ports.extend([Port("strobe"), Port("hsync"),
                              Port("stall", direction="out")])
        self.mut.interfaces = [test_if]

        test_regif = SlaveRegisterInterface()
        test_regif.ports.extend(
            [Port("slv_status_reg",
                  data_width=Port.DataWidth(a="MAX_REGS_PER_MODULE - 1",
                                            sep="downto",
                                            b=0))])
        self.mut.register_ifs.append(test_regif)

        self.mut.generics.append(Generic("DATA_WIDTH"))

    def test_add_standard_port(self):
        LOG.debug("*UNITTEST* <running test_add_standard_port>")
        fut = self.mut.add_standard_port

        # Make sure the module rejects non-Port objects
        self.assertFalse(fut(Generic("clk")))
        # Check if the module rejects ports not in the list of standard ports
        self.assertFalse(fut(Port("noclk")))
        # Check if the module checks the port direction correctly
        self.assertFalse(fut(Port("clk", direction="inout")))
        # Make sure the module hasn't added any of these ports above
        self.assertFalse(self.mut.standard_ports)  # Empty lists are == False
        # Make sure the module accepts valid standard ports
        # First check if the standard port list is empty
        self.assertFalse(bool(self.mut.standard_ports))
        # Now attempt to add a valid standard port (the first template)
        self.assertTrue(fut(self.mut.standard_port_templates[0]))
        # Now check if the standard port list is no longer empty
        self.assertTrue(bool(self.mut.standard_ports))

    def test_add_generic(self):
        LOG.debug("*UNITTEST* <running test_add_generic>")
        fut = self.mut.add_generic

        # Make sure the module rejects non-Generic objects
        self.assertFalse(fut(Port("strobe")))
        # Make sure the module rejects duplicate generics
        self.assertFalse(fut(Generic("DATA_WIDTH")))
        self.assertEqual(sum([1 for gen in self.mut.generics
                              if gen.name == "DATA_WIDTH"]), 1)
        # Check that the module accepts valid generics
        self.assertTrue(fut(Generic("REG_WIDTH")))
        self.assertIn("REG_WIDTH", [gen.name for gen in self.mut.generics])

    def test_new_interface_from_template(self):
        LOG.debug("*UNITTEST* <running test_new_interface_from_template>")
        fut = self.mut.__new_interface_from_template__

        # Prepare parameters for the Function Under Test
        if_template = as_templates.AsStream()
        n_port = Port("w_strobe_in_i0")
        t_port = if_template.get_ports("strobe")[0]

        # Run the function under test
        new_if = fut(if_template, t_port, n_port)
        # Check if: the returned interface is an Interface object, with correct
        # direction, template, parent and with n_port added
        self.assertIsNotNone(new_if)
        self.assertIsInstance(new_if, Interface)
        self.assertEqual(new_if.direction, "in")
        self.assertIs(new_if.template, if_template)
        self.assertIs(new_if.parent, self.mut)
        self.assertIn(n_port, new_if.ports)

        # Same test, just now the direction of the first port is reversed
        # This should result in the new interfaces direction being reversed
        # and the ports direction being "re-reversed"
        n_port = Port("w_strobe_in_i0", direction="out")
        new_if = fut(if_template, t_port, n_port)
        self.assertIsNotNone(new_if)
        self.assertIsInstance(new_if, Interface)
        self.assertEqual(new_if.direction, "out")
        self.assertIs(new_if.template, if_template)
        self.assertIn(n_port, new_if.ports)
        self.assertIs(new_if.parent, self.mut)
        self.assertEqual(new_if.ports[0].direction, "in")

    def test_fit_port_to_new_interface(self):
        LOG.debug("*UNITTEST* <running test_fit_port_to_new_interface>")
        fut = self.mut.__fit_port_to_new_interface__

        # Check if the module rejects a port that's in no template
        self.assertFalse(fut(Port("nothing")))
        self.assertFalse(len(self.mut.interfaces) > 1)

        self.assertTrue(fut(Port("data_error")))
        self.assertEqual(len(self.mut.interfaces), 2)
        self.assertNotIn("data",
                         [port.name for port in self.mut.interfaces[1].ports])
        self.assertIn("data_error",
                      [port.name for port in self.mut.interfaces[1].ports])

    def test_fit_port_to_existing_interface(self):
        LOG.debug("*UNITTEST* <running test_fit_port_to_existing_interface>")
        fut = self.mut.__fit_port_to_existing_interface__

        # Check if the module rejects a port already present in the existing
        # interface
        self.assertFalse(fut(Port("strobe")))
        self.assertEqual(sum([1 for port in self.mut.interfaces[0].ports
                              if port.name == "strobe"]), 1)
        # Check if the module rejects a port that doesn't match any interface
        self.assertFalse(fut(Port("notvalid")))
        self.assertNotIn("notvalid",
                         [port.name for port in self.mut.interfaces[0].ports])
        # Check if the module accepts a valid port
        self.assertTrue(fut(Port("data_error")))
        self.assertIn("data_error",
                      [port.name for port in self.mut.interfaces[0].ports])

    def test_fit_port(self):
        LOG.debug("*UNITTEST* <running test_fit_port>")
        fut = self.mut.__fit_port__

        # Check that the module assigns a non-matching port to itself
        self.assertFalse(fut(Port("nomatch")))
        self.assertIn("nomatch", [port.name for port in self.mut.ports])

        # Check that the module adds an interface for a port that matches a
        # template
        self.assertTrue(fut(Port("strobe")))
        self.assertEqual(len(self.mut.interfaces), 2)

        # Both existing interfaces are missing the "data" port.
        self.assertTrue(fut(Port("data", data_type="std_logic_vector")))
        self.assertTrue(fut(Port("data", data_type="std_logic_vector")))
        # As a result, both interfaces now have both mandatory ports (complete)
        self.assertTrue(all([inter.is_complete() for inter
                             in self.mut.interfaces]))

        self.assertTrue(fut(Port("clk")))
        self.assertIn("clk", [port.name for port in self.mut.standard_ports])

    def test_assign_generic(self):
        LOG.debug("*UNITTEST* <running test_assign_generic>")
        fut = self.mut.__assign_generic__

        # Prepare test module
        asstream_0 = self.mut.interfaces[0]
        asstream_0.ports.append(
            Port("data", data_width=Port.DataWidth(a="DATA_WIDTH - 1",
                                                   sep="downto", b=0)))
        asstream_1 = Interface("as-stream_inv",
                               template=as_templates.AsStream())
        asstream_1.ports.append(
            Port(
                "data",
                data_width=Port.DataWidth(
                    a="INV_WIDTH - 1",
                    sep="downto",
                    b=0)))
        self.mut.interfaces.append(asstream_1)
        t_regif = SlaveRegisterInterface()
        t_regif.ports.append(
            Port("slv_ctrl_reg",
                 data_width=Port.DataWidth(a="MAX_REGS_PER_MODULE - 1",
                                           sep="downto", b=0)))
        t_regif.ports.append(
            Port("slv_reg_modify",
                 data_width=Port.DataWidth(a="MAX_REGS_PER_MODULE - 1",
                                           sep="downto", b=0)))
        self.mut.register_ifs.append(t_regif)

        # Test case 0: Generic that doesn't match any interface
        # Should only be assigned to the module itself
        gen_0 = Generic("NOMATCH")
        fut(gen_0)
        self.assertNotIn(gen_0.name, [gen.name for gen in t_regif.generics])
        self.assertNotIn(gen_0.name, [gen.name for gen in asstream_0.generics])
        self.assertIn(gen_0.name, [gen.name for gen in self.mut.generics])

        # Test case 1: Generic that matches an interface
        # Should be assigned to the module and the matching interface
        gen_1 = Generic("DATA_WIDTH")
        fut(gen_1)
        self.assertNotIn(gen_1.name, [gen.name for gen in t_regif.generics])
        self.assertIn(gen_1.name, [gen.name for gen in asstream_0.generics])
        self.assertNotIn(gen_1.name, [gen.name for gen in asstream_1.generics])
        self.assertIn(gen_1.name, [gen.name for gen in self.mut.generics])

        # Test case 2: Generic that matches a register interface
        # Should be assigned to the module and the register interface
        gen_2 = Generic("MAX_REGS_PER_MODULE")
        fut(gen_2)
        self.assertIn(gen_2.name, [gen.name for gen in t_regif.generics])
        self.assertNotIn(gen_2.name, [gen.name for gen in asstream_0.generics])
        self.assertIn(gen_2.name, [gen.name for gen in self.mut.generics])

    def test_assign_interfaces(self):
        LOG.debug("*UNITTEST* <running test_assign_interfaces>")
        fut = self.mut.__assign_interfaces__

        # Prepare test AsModule (assign_interfaces uses the "entity_XYZ" lists)
        # These additional ports should be sorted into the existing AsStream
        # interface. Plus an additional AsStream with the "data" and "strobe"
        # ports instanciated below
        # The "data_error" port should generate another interface with
        # the direction "out". Since no other ports match that AsStream
        # direction, the interface should be removed during "assign_interfaces"
        # The port should be added to the module itself, as a single/lone port
        self.mut.entity_ports = [
            Port(
                "data", data_type="std_logic_vector"), Port(
                "data_error", direction="out"), Port(
                "data", data_type="std_logic_vector", data_width=Port.DataWidth(
                    a="DWIDTH - 1", sep="downto", b=0)), Port("strobe")]
        self.mut.entity_generics = [Generic("DWIDTH"), Generic("NOMATCH"),
                                    Generic("MAX_REGS_PER_MODULE")]

        fut()
        self.assertEqual(len(self.mut.interfaces), 2)
        inter0 = self.mut.interfaces[0]
        inter1 = self.mut.interfaces[1]

        # Check that the module assigned a Generic that matches no interface
        # only to the module itself
        self.assertIn("NOMATCH", [gen.name for gen in self.mut.generics])
        # Check that the module assigned the matching Generic only to the
        # interface that contains a port that has the Generic's name in the
        # ports datawidth definition (Port.data_width)
        self.assertIn("DWIDTH", [gen.name for gen in inter1.generics])
        self.assertNotIn("DWIDTH", [gen.name for gen in inter0.generics])
        # Make sure the Generic is still also assigned to the module itself
        self.assertIn("DWIDTH", [gen.name for gen in self.mut.generics])
        # Check that the Generic matching the datawidth definition was assigned
        # to the (only) register interface
        self.assertIn("MAX_REGS_PER_MODULE",
                      [gen.name for gen in self.mut.register_ifs[0].generics])
        # Make sure the port not matching with any interfaces is assigned to
        # the module itself
        self.assertIn("data_error", [port.name for port in self.mut.ports])
        # Make sure both AsStreams are complete (have both "data" and "strobe")
        self.assertIn("data", [port.name for port in inter0.ports])
        self.assertIn("data", [port.name for port in inter1.ports])
        self.assertIn("strobe", [port.name for port in inter0.ports])
        self.assertIn("strobe", [port.name for port in inter1.ports])
        # Make sure only the two expected interfaces were created
        self.assertEqual(len(self.mut.interfaces), 2)
        # Make sure that the existing register interface is still there
        self.assertEqual(len(self.mut.register_ifs), 1)
        # Make sure the pre-existing port "hsync" is still there
        self.assertIn("hsync", [port.name for port in inter0.ports])

    def test_assign_register_interfaces(self):
        LOG.debug("*UNITTEST* <running test_assign_register_interface>")
        fut = self.mut.__assign_register_interfaces__

        # Prepare the test with new ports generics and constants to work with
        # The module should recognize two full register interfaces with the
        # existing ports and those instanciated below.
        # The port "slv_reg_modify_supp" should end up assigned to the module
        self.mut.entity_ports = \
            [Port("slv_reg_modify", data_type="std_logic_vector",
                  direction="out"),
             Port("slv_ctrl_reg", data_type="slv_reg_data"),
             Port("slv_reg_modify_sup", data_type="std_logic_vector",
                  direction="out"),
             Port("slv_ctrl_reg", data_type="slv_reg_data"),
             Port("slv_reg_config_sup", data_type="slv_reg_config_table",
                  direction="out"),
             Port("slv_reg_config", data_type="slv_reg_config_table",
                  direction="out"),
             Port("slv_reg_modify_supp", data_type="std_logic_vector",
                  direction="out"),
             Port("slv_ctrl_reg_sup", data_type="slv_reg_data"),
             Port("slv_status_reg_sup", data_type="slv_reg_data",
                  direction="out")]
        # The constants should be assigned to the correct register interface.
        self.mut.entity_constants = \
            [Constant("slave_register_configuration"),
             Constant("slave_register_configuration_sup")]

        fut()
        # Check if the correct number of register interfaces was created
        self.assertEqual(len(self.mut.register_ifs), 2)
        regif0 = self.mut.register_ifs[0]
        regif1 = self.mut.register_ifs[1]

        # Check if all ports for the register interfaces were assigned right
        self.assertIn("slv_reg_modify",
                      [port.code_name for port in regif0.ports])
        self.assertIn("slv_reg_modify_sup",
                      [port.code_name for port in regif1.ports])
        self.assertIn("slv_reg_config",
                      [port.code_name for port in regif0.ports])
        self.assertIn("slv_reg_config_sup",
                      [port.code_name for port in regif1.ports])
        self.assertIn("slv_ctrl_reg",
                      [port.code_name for port in regif0.ports])
        self.assertIn("slv_ctrl_reg_sup",
                      [port.code_name for port in regif1.ports])
        self.assertIn("slv_status_reg",
                      [port.code_name for port in regif0.ports])
        self.assertIn("slv_status_reg_sup",
                      [port.code_name for port in regif1.ports])
        # Check that the port "slv_reg_modify_supp" was added back to the
        # modules "entity_ports" list (it's register interface is incomplete)
        # Also check for the duplicate port "slv_ctrl_reg"
        self.assertIn("slv_reg_modify_supp",
                      [port.code_name for port in self.mut.entity_ports])
        self.assertIn("slv_ctrl_reg",
                      [port.code_name for port in self.mut.entity_ports])
        # Check that the module has had no other ports assigned to entity_ports
        self.assertEqual(len(self.mut.entity_ports), 2)
        # Check if the suffix for regif1 was set correctly
        self.assertEqual("_sup", regif1.name_suffix)
        # Check if the constants were assigned correctly (matching the suffix)
        self.assertEqual("slave_register_configuration",
                         regif0.config.code_name)
        self.assertEqual("slave_register_configuration_sup",
                         regif1.config.code_name)

    def tearDown(self):
        self.mut = None
        AsModule.interface_templates = []


if __name__ == '__main__':
    LOG = as_log.init_log()
    LOG.disabled = True
    ut.main(exit=False)
