# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_autotest_interface.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Module implementing unit tests for the as_automatics
module as_automatics_interface.py
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
# @file as_autotest_interface.py
# @author Philip Manke
# @brief Unit tests for as_automatics_interface
# -----------------------------------------------------------------------------

import unittest as ut
from as_automatics_port import Port
from as_automatics_generic import Generic
from as_automatics_interface import Interface
from as_automatics_templates import AsStream
import as_automatics_logging as as_log

LOG = as_log.get_log()


class TestInterface(ut.TestCase):

    asstream_template = AsStream()

    def setUp(self):
        self.tif = Interface("as_stream")
        self.tif.template = self.asstream_template
        self.tif.ports.append(Port("strobe"))

    def test_add_port_w_template_1(self):
        LOG.debug("*UNITTEST* <running test_add_port_w_template_1>")
        # Set fut (Function Under Test)
        fut = self.tif.add_port
        # Tests with template (port is in template and direction checks)
        # Check if the interface rejects the port "notastrobe" as it isn't part
        # of the template interface "as_stream"
        self.assertFalse(fut(Port("notastrobe")))
        self.assertNotIn("notastrobe", [port.name for port in self.tif.ports])
        # Check if the interface rejects the port hsync, even though it is part
        # of the template interface since it's in the wrong direction
        self.assertFalse(fut(Port("hsync", direction="out")))
        self.assertNotIn("hsync", [port.name for port in self.tif.ports])
        # Check if the interface accepts a valid port in the
        # right direction that is part of the template
        self.assertTrue(fut(Port("vsync")))
        self.assertIn("vsync", [port.name for port in self.tif.ports])
        # Second positive test, to check using a port with a direction of "out"
        self.assertTrue(fut(Port("stall", direction="out")))
        self.assertIn("stall", [port.name for port in self.tif.ports])

    def test_add_port_w_template_2(self):
        LOG.debug("*UNITTEST* <running test_add_port_w_template_2>")
        fut = self.tif.add_port
        self.tif.direction = "out"

        # These tests are almost identical with the tests in
        # "test_add_port_w_template_1" only with the interface in dir. "out"
        # Check if the interface rejects the port "notastrobe" as it isn't part
        # of the template interface "as_stream"
        self.assertFalse(fut(Port("notastrobe")))
        self.assertNotIn("notastrobe", [port.name for port in self.tif.ports])
        # Check if the interface rejects the port hsync, even though it is part
        # of the template interface since it's in the wrong direction
        self.assertFalse(fut(Port("hsync")))
        # Make sure neither or the ports were added to the interface
        self.assertNotIn("hsync", [port.name for port in self.tif.ports])
        # Positive test: Check if the interface accepts a valid port in the
        # right direction that is part of the template
        self.assertTrue(fut(Port("vsync", direction="out")))
        # Make sure the port was actually added:
        self.assertIn("vsync", [port.name for port in self.tif.ports])
        # Second positive test, to check using a port with a direction of "in"
        self.assertTrue(fut(Port("stall")))
        self.assertIn("stall", [port.name for port in self.tif.ports])

    def test_add_port_wo_template(self):
        LOG.debug("*UNITTEST* <running test_add_port_wo_template>")
        # Tests without template. Only checks if port is already present
        fut = self.tif.add_port
        self.tif.template = None  # Remove the template
        # Check if the interface rejects an already present port
        self.assertFalse(fut(Port("strobe")))
        # Make sure the "strobe" port is still there
        self.assertIn("strobe", [port.name for port in self.tif.ports])
        # Check if the interface accepts any other port ...
        self.assertTrue(fut(Port("itsarandomportname")))
        self.assertIn("itsarandomportname",
                      [port.name for port in self.tif.ports])
        # But should still reject any other object
        self.assertFalse(fut(Generic("totallyavalidport")))
        self.assertNotIn("totallyavalidport",
                         [port.name for port in self.tif.ports])

    def test_fit_and_add_port(self):
        LOG.debug("*UNITTEST* <running test_fit_and_add_port>")
        fut = self.tif.fit_and_add_port

        # Check if the interface correctly matches the port "data_error" and
        # adds it. Make sure it doesn't match with the template port "data"
        self.assertTrue(fut(Port("data_error")))
        self.assertIn("data_error", [port.name for port in self.tif.ports])
        # Check if the interface rejects the port using a wrong prefix
        self.assertFalse(fut(Port("error_data")))
        self.assertNotIn("error_data", [port.name for port in self.tif.ports])
        # Same check, but for suffix
        self.assertFalse(fut(Port("data_invalid")))
        self.assertNotIn("data_invalid",
                         [port.name for port in self.tif.ports])
        # Check if the interface rejects objects that aren't ports
        self.assertFalse(fut(Generic("hsync")))
        self.assertNotIn("hsync", [port.name for port in self.tif.ports])

        # Set blank interface
        self.tif = Interface("as-stream")
        fut = self.tif.fit_and_add_port

        # Calling fit_and_add_port should always fail if no template is set...
        self.assertFalse(fut(Port("strobe")))

        self.tif.template = self.asstream_template

        # Add a port with suffix and prefix
        # These should be extracted and used by the interface
        self.assertTrue(fut(Port("right_n1_data_error_lane_2")))
        self.assertIn("data_error", [port.name for port in self.tif.ports])

        # Check if the pre- and suffix were extracted
        self.assertEqual(self.tif.name_prefix, "right_n1_")
        self.assertEqual(self.tif.name_suffix, "_lane_2")

        # Make sure the pre- and suffix checks work
        self.assertFalse(fut(Port("right_n2_strobe_lane_2")))
        self.assertNotIn("strobe", [port.name for port in self.tif.ports])
        self.assertFalse(fut(Port("right_n1_data_lame_2")))
        self.assertNotIn("data", [port.name for port in self.tif.ports])

        # Make sure a port with the correct fixes is added
        self.assertTrue(fut(Port("right_n1_strobe_lane_2")))
        self.assertIn("strobe", [port.name for port in self.tif.ports])

    def test_is_complete(self):
        LOG.debug("*UNITTEST* <running test_is_complete>")
        fut = self.tif.is_complete
        # The interface provided by setUp is incomplete. is_complete -> False
        self.assertFalse(fut())
        self.tif.ports.append(Port("data_error"))
        # After adding a port similar to the missing "data" port, it should
        # still report itself as incomplete
        self.assertFalse(fut())
        self.tif.ports.append(Port("data"))
        # Now the interface should be complete
        self.assertTrue(fut())
        self.tif.ports = [Port("data")]
        # After "removing" all ports except for the "data" port, the interface
        # should once again report itself as incomplete
        self.assertFalse(fut())

    def test_add_generic(self):
        LOG.debug("*UNITTEST* <running test_add_generic>")
        fut = self.tif.add_generic

        # Check if the interface accepts a new generic
        self.assertTrue(fut(Generic("AGENERIC")))
        self.assertIn("AGENERIC", [gen.name for gen in self.tif.generics])

        # Check if the interface rejects an object, that's not a Generic
        self.assertFalse(fut(Port("NOTAGENERIC")))
        self.assertNotIn("NOTAGENERIC",
                         [gen.name for gen in self.tif.generics])

        # Make sure the interface rejects a duplicate generic
        self.assertFalse(fut(Generic("AGENERIC")))

    def test_remove_generic(self):
        LOG.debug("*UNITTEST* <running test_remove_generic>")
        fut = self.tif.remove_generic
        self.tif.generics.extend([Generic("AGENERIC"), Generic("AGENERIC"),
                                  Generic("ANOTHERONE"), Generic("LASTONE")])

        # Make sure the method can remove an existing generic
        self.assertTrue(fut("ANOTHERONE"))
        self.assertNotIn("ANOTHERONE", [gen.name for gen in self.tif.generics])
        # Make sure False is returned if the requested generic doesn't exist
        self.assertFalse(fut("NOTAGENERIC"))
        # Make sure the interface removes all duplicates, if there are some
        self.assertTrue(fut("AGENERIC"))
        self.assertNotIn("AGENERIC", [gen.name for gen in self.tif.generics])
        # Now there should only be one generic left
        self.assertEqual(self.tif.generics[0].name, "LASTONE")

    def test_get_port_direction_normalized(self):
        fut = self.tif.get_port_direction_normalized
        self.tif.ports.extend([Port("data", direction="out")])

        # This method should return the direction of ports as specified in VHDL
        self.assertEqual(fut("strobe"), "in")
        self.assertEqual(fut("data"), "out")

        # Interfaces with direction "out" have the port directions "flipped"
        self.tif.direction = "out"
        # This method has to "unflip" them
        self.assertEqual(fut("strobe"), "out")
        self.assertEqual(fut("data"), "in")
        # It should return an empty string for ports that don't exist
        self.assertEqual(fut("notpresent"), "")

    def tearDown(self):
        self.tif = None


if __name__ == '__main__':
    LOG = as_log.init_log()
    LOG.disabled = True
    ut.main(exit=False)
