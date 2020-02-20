# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# Copyright (C) Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_automatics_interface.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Implements the class 'Interface' for as_automatics.
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
# @file as_automatics_interface.py
# @author Philip Manke
# @brief Implements the class 'Interface' for as_automatics.
# -----------------------------------------------------------------------------
import copy
from typing import Sequence

from as_automatics_port import Port
from as_automatics_generic import Generic
import as_automatics_helpers as as_help
import as_automatics_logging as as_log

LOG = as_log.get_log()


class Interface():
    """Describes a hardware interface consisting of VHDL ports and generics."""

    def __init__(self, name: str, template: object = None):
        self.ports = []  # List of this interface's Ports
        self.generics = []  # List of this interface's Generics
        self.name = name  # The interface "type" (as_stream, AXI_Master, ...)
        self.parent = None
        self.template = None
        self.direction = "in"  # Data direction (flips all Port's direction)
        self.name_prefix = ""  # Prefix to the '.name'
        self.name_suffix = ""  # Suffix to the '.name'
        self.unique_name = ""  # System-wide unique name
        self.connected = False  # Is the interface connected to another if?
        self.to_external = False  # This interface should be made external
        # AsModule to instantiate in toplevel.
        # Used to automatically instantiate management components
        # (ie AXI Master for memory access)
        self.instantiate_in_top = None
        self.in_entity = True  # Include in VHDL entity?
        self.incoming = []  # Incoming connections (data -> self)
        self.outgoing = []  # Outgoing connections (self -> data)

        # If a template is passed, make sure it's actually an Interface object
        if template is not None:
            if isinstance(template, Interface):
                self.template = template
            else:
                LOG.error("Template passed to %s is not an Interface object!",
                          name)

    def __str__(self) -> str:
        """Return the 'full name' of this interface (not the unique name)"""
        return self.name_prefix + self.name + self.name_suffix

    def duplicate(self):
        """Generate a copy of this interface object and reset a few parameters
        to default values. Returns a 'cleaned' version of this object to use."""

        # First, create a low-level copy of this interface
        out = copy.copy(self)
        # Reset connection data
        out.incoming = []
        out.outgoing = []

        # Copy all ports
        out.ports = []
        for port in self.ports:
            out.ports.append(port.duplicate())

        # and Generics
        out.generics = []
        for gen in self.generics:
            out.generics.append(copy.copy(gen))

        # Reset connection state, parent, connect_to
        out.connected = False
        out.parent = None
        connect_to = getattr(self, "connect_to", None)
        if connect_to:
            setattr(out, "connect_to", connect_to)

        # Reset connection data and state of all ports
        for port in out.ports:
            port.glue_signal = None
            port.connected = False
            port.incoming = None
            port.outgoing = []
            port.assign_to(out)

        return out

    def add_port(self, port_obj: Port) -> bool:
        """Add a port to this interface instance. Performs some checks on
           whether the handed port object may be added to this interface:
           Duplicate ports aren't allowed. If the interface has a template,
           the port must be part of it and have the matching direction."""
        # Make sure we got a port object
        if not isinstance(port_obj, Port):
            LOG.error("'add_port' was passed the non-Port object '%s'.",
                      repr(port_obj))
            return False

        # Check if a port with the same name is already assigned
        if self.has_port(port_obj.name):
            LOG.debug("Port '%s' already present in interface '%s'",
                      port_obj.name, str(self))
            return False

        # Checks for when a template is set
        if self.template is not None:
            # Check if this port is in the template
            tport = self.template.get_port(port_obj.name, suppress_error=True)
            add = bool(tport)
            if not add:
                LOG.debug("Port '%s' not found in template '%s'",
                          port_obj.name, str(self.template))
                return False

            if tport.data_type != port_obj.data_type:
                LOG.debug("Data type mismatch for port '%s'.", port_obj.name)
                return False
            # Also make sure the port direction matches
            add = tport.direction == port_obj.direction
            if self.direction == "out":
                # If this interface's direction is out,
                # reverse the port direction (and set add = !add)
                add = not add
                if add:
                    port_obj.direction = tport.direction
            if not add:
                LOG.debug("Port direction mismatch!")
                return False
            port_obj.optional = tport.optional
            port_obj.set_ruleset(list(tport.ruleset))

        # If the checks passed, add this port
        LOG.debug("Add port '%s' to interface '%s'.",
                  port_obj.code_name, str(self))
        port_obj.assign_to(self)
        port_obj.port_type = "interface"
        self.ports.append(port_obj)
        return True

    def make_external(self):
        """For use in the user script / interactive mode: Make this interface
        external, exposing it to the outside of the IP-Core."""
        self.to_external = True

    def instantiate_module(self, entity_name: str):
        """For use in the user script / interactive mode: Automatically add the
        module 'entity_name' to toplevel and connect this interface to it."""
        self.instantiate_in_top = entity_name
        self.to_external = True

    def get_ports(self, port_name: str, *,
                  suppress_error: bool = False) -> Sequence[Port]:
        """Search for and return any Ports matching 'port_name'
        using the port.name attribute"""
        found = [port for port in self.ports if port.name == port_name]
        if not found and not suppress_error:
            LOG.error("Could not find a port '%s' in interface '%s'!",
                      port_name, str(self))
            raise NameError("No port {} found in {}!".format(port_name, self))
        return found

    def get_port(
            self,
            port_name: str,
            *,
            suppress_error: bool = False) -> Port:
        """Search for and return the first Port matching 'port_name'
        using the port.name attribute"""
        found = next((port for port in self.ports if port.name == port_name),
                     None)
        if not found and not suppress_error:
            LOG.error("Could not find a port '%s' in interface '%s'!",
                      port_name, str(self))
            raise NameError("No port {} found in {}!".format(port_name, self))
        return found

    def get_port_by_code_name(self, port_name: str, *,
                              suppress_error: bool = False) -> Port:
        """Search for and return the first Port matching 'port_name'
        using the port.code_name attribute"""
        found = next((port for port in self.ports
                      if port.code_name == port_name), None)
        if not found and not suppress_error:
            LOG.error("Could not find a port '%s' in interface '%s'!",
                      port_name, str(self))
            raise NameError("No port {} found in {}!".format(port_name, self))
        return found

    def has_port(self, port_name: str) -> bool:
        """Return 'True' if this interface has a Port matching 'port_name'
        in its port.name attribute"""
        return port_name in [port.name for port in self.ports]

    def template_has_port(self, port_name: str) -> bool:
        """Return 'True' if this interface's template has a Port matching
        'port_name' in its port.name attribute"""
        if self.template is not None:
            return self.template.has_port(port_name)
        return False

    def get_generics(self, generic_name: str) -> Sequence[Generic]:
        """Return all Generics matching 'generic_name'
        in their generic.name attribute"""
        return [gen for gen in self.generics if gen.name == generic_name]

    def has_generic(self, generic_name: str) -> bool:
        """Return 'True' if this interface has a Generic matching
        'generic_name' in its generic.name attribute"""
        return generic_name in [gen.name for gen in self.generics]

    def template_has_generic(self, generic_name: str) -> bool:
        """Return 'True' if this interface's template has a Generic matching
        'generic_name' in its generic.name attribute"""
        if self.template is not None:
            return self.template.has_generic(generic_name)
        return False

    def get_port_name_list(self) -> Sequence[str]:
        """Return a list of the port.name attribute of all present Ports"""
        return [port.name for port in self.ports]

    def is_connect_complete(self) -> bool:
        """Returns True if all ports of this interface are connected."""
        for port in self.ports:
            if not port.connected:
                return False
        return True

    def set_connected(self, value: bool = True):
        """Set the 'connected' attribute"""
        self.connected = value

    def set_connected_all(self, value: bool = True):
        """Set the 'connected' attribute for this interface and all Ports"""
        self.connected = value
        for port in self.ports:
            port.connected = value

    def set_prefix_suffix(self, new_prefix, new_suffix, update : bool = True):
        """Modify the prefix and suffix for all Ports.
        Does NOT store the new prefix and suffix in the respective attributes"""
        for port in self.ports:
            port.code_name = "{}{}{}".format(new_prefix, port.name, new_suffix)
        if update:
            self.name_prefix = new_prefix
            self.name_suffix = new_suffix

    def fit_and_add_port(self, port_obj: Port) -> bool:
        """Use if only the code_name of the port is available.
           Finds the longest matching name fragment of the code_name with the
           names of the ports of this interfaces template. This is used to set
           the ports name (port.name). Also compares the pre- and suffixes
           of the interface and port to add"""
        # Make sure we got a port object
        if not isinstance(port_obj, Port):
            LOG.error("'fit_and_add_port' got the non-Port object '%s'.",
                      repr(port_obj))
            return False

        # This method can only work if the template is set
        if self.template is None:
            LOG.error(("'fit_and_add_port' called for port '%s' while "
                       "interface '%s' had no template assigned!"),
                      port_obj.code_name, str(self))
            return False

        # Check if the port is defined in this interfaces template
        matchlist = [tport.name for tport in self.template.ports
                     if tport.name in port_obj.code_name]
        if not matchlist:
            LOG.debug("Port '%s' not found in template.", port_obj.code_name)
            return False

        # Find the longest matching template port -> set the ports name to that
        matchlist.sort(key=lambda name: len(name), reverse=True)
        port_obj.name = matchlist[0]

        # Pre-/Suffix check
        this_prefix, this_suffix = \
            as_help.get_prefix_suffix(port_obj.name,
                                      port_obj.code_name,
                                      Port.directions)
        first_port = not self.ports
        if not first_port:
            # If this is not the first port, the pre-/suffix need to match
            if ((this_suffix != self.name_suffix) or
                    (this_prefix != self.name_prefix)):
                LOG.debug("Port '%s' didn't fit, prefix/suffix mismatch!",
                          port_obj.code_name)
                return False
        else:
            # If this is the first port, use its pre-/suffix for this regif
            self.name_prefix = this_prefix
            self.name_suffix = this_suffix

        LOG.debug("Trying to add '%s' to interface '%s'", port_obj.code_name,
                  str(self))
        # Try adding the port
        if not self.add_port(port_obj):
            return False

        return True

    def remove_port(self, port_name: str) -> bool:
        """Remove port(s) from this interface instance by name 'port_name'."""
        to_remove = self.get_ports(port_name, suppress_error=True)
        if not to_remove:
            LOG.error(("Couldn't remove '%s' from interface '%s'; no matching "
                       "ports found"), port_name, str(self))
            return False

        if len(to_remove) > 1:
            # This shouldn't happen, unless a duplicate port was added
            # by directly manipulating the ports list (interface.ports)
            LOG.warning(("Found multiple ports to remove: %s - "
                         "removing all!"), str(to_remove))
        else:
            LOG.debug("Removing port '%s' from interface '%s'",
                      port_name, str(self))
        for rem_port in to_remove:
            self.ports.remove(rem_port)
        return True

    def add_generic(self, generic_obj: Generic) -> bool:
        """Add a generic to this interface instance."""
        # Check if the passed object is a generic object
        if not isinstance(generic_obj, Generic):
            LOG.error("Couldn't add generic, not a generic (VHDL) object!")
            return False
        # Only add the generic if it's not already added
        if self.has_generic(generic_obj.name):
            LOG.debug("Interface '%s' already has a generic '%s'", str(self),
                      generic_obj.name)
            return False
        # Add the generic
        generic_obj.assign_to(self)
        self.generics.append(generic_obj)
        return True

    def remove_generic(self, generic_name: str) -> bool:
        """Remove a generic from this
           interface instance by name ('generic_name')."""
        to_remove = [gen for gen in self.generics if gen.name == generic_name]
        if not to_remove:
            LOG.error(("Couldn't remove '%s' from interface '%s', generic "
                       "not found"), generic_name, str(self))
            return False

        if len(to_remove) > 1:
            # This shouldn't happen, 'add_generic' prohibits copies of
            # generics, the generics-list could be modified directly though
            LOG.warning(("Found multiple generics to remove: %s - "
                         "removing all!"), str(to_remove))
        else:
            LOG.debug("Removing generic '%s' from interface '%s'",
                      generic_name, str(self))
        for rem_gen in to_remove:
            self.generics.remove(rem_gen)
        return True

    def get_port_direction_normalized(self, port_name: str) -> str:
        """Return the direction of a port as it is defined in the VHDL file."""
        found = self.get_port(port_name, suppress_error=True)
        if found is None:
            LOG.error("Couldn't find port '%s' in interface '%s'", port_name,
                      str(self))
            return ""
        if self.direction == "in":
            return found.direction
        return "out" if found.direction == "in" else "in"

    def print_interface(self, verbose: bool = False):
        """Print the interface configuration, listing all ports and generics.
           Prints only the mandatory ports if 'verbose' is set to 'False'."""
        print(self.name_prefix + self.name + self.name_suffix +
              ": Interface with direction '{}'".format(self.direction))
        if verbose:
            print("Source module: {}"
                  .format(str(as_help.get_source_module(self))))
            if self.generics:
                print("Generics:")
                self.list_generics()
            print("Ports:")
            self.list_ports()
        else:
            print("Mandatory ports:")
            for port in self.ports:
                if not port.optional:
                    print(str(port))

    def list_ports(self):
        """Print a list of ports associated with this interface instance."""
        for port in self.ports:
            print(str(port))

    def list_generics(self):
        """Print a list of generics associated with this interface instance."""
        for gen in self.generics:
            print(str(gen))

    def assign_to(self, parent: object):
        """Assigns this instance as part of/linked to 'parent'"""
        self.parent = parent

    def clear(self):
        """Removes all ports and generics from this interface instance.
           Also removes the parent (set by assign_to())
           and this instances interface template."""
        self.ports = []
        self.generics = []
        self.parent = None
        self.template = None

    def is_complete(self) -> bool:
        """Checks if this instance currently 'has' all the mandatory ports,
           as defined by the interface template."""
        LOG.debug("Starting consistency check for interface '%s'", self.name)
        # For all ports of this interface's template
        present_portnames = [port.name for port in self.ports]
        for mtport in [tport for tport in
                       self.template.ports if not tport.optional]:
            # LOG.debug("Checking for port '%s'", mtport.name)
            # Make sure all !mandatory! (optional == False) ports are present
            if mtport.name not in present_portnames:
                LOG.debug("Port '%s' isn't present! Removing interface.",
                          mtport.name)
                return False
        LOG.debug("Interface has all mandatory ports.")
        return True

    def get_unconnected_ports(self) -> Sequence[Port]:
        """Return a list of this interface's ports that are not connected to
        another port (attribute port.connected == False)."""
        return [port for port in self.ports if not port.connected]
