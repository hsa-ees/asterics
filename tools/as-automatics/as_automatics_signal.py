# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_automatics_signal.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Implements the classes 'GenericSignal' and 'GlueSignal' for as_automatics.
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
# @file as_automatics_signal.py
# @ingroup automatics_intrep
# @author Philip Manke
# @brief Implements classes 'GenericSignal' and 'GlueSignal' for as_automatics.
# -----------------------------------------------------------------------------

import copy

from as_automatics_exceptions import AsConnectionError
from as_automatics_port import Port
from as_automatics_connection_helper import get_parent_module

import as_automatics_helpers as as_help
import as_automatics_logging as as_log

LOG = as_log.get_log()


## @ingroup automatics_intrep
class GenericSignal(Port):
    """! @brief Variation of the as_automatics_port::Port class,
    representing a VHDL signal.
    Has additional attributes and may have multiple incoming data sources.
    The 'direction' and 'connected' attribute are ignored for this class.
    Models a generic VHDL signal in an architecture."""

    def __init__(
        self,
        name: str = "",
        code_name: str = "",
        port_type: str = "signal",
        data_type: str = "std_logic",
        optional: bool = False,
        data_width=Port.DataWidth(1, None, None),
    ):
        super().__init__(
            name, code_name, "inout", port_type, data_type, optional, data_width
        )
        self.incoming = []
        self.is_signal = True
        self.vector_map_incoming = dict()
        self.vector_map_outgoing = dict()
        self.vector_assignment_tasks = []

    def get_direction_normalized(self):
        """! @brief Signals don't have a direction, returns 'inout'."""
        return "inout"

    def set_connected(self, value: bool = True):
        """! @brief Set the 'connected' attribute"""
        self.connected = False

    ##
    # @addtogroup automatics_cds
    # @{

    def connect(self, target):
        """! @brief Connect this Port to another Port, Interface or AsModule."""
        try:
            self.parent.__connect__(self, target)
        except AttributeError:
            raise AsConnectionError(
                self,
                (
                    "GenericSignal '{}' not associated to an AsModuleGroup!"
                    " - in '{}'"
                ).format(self.code_name, self.parent.name),
            )

    def assign_from_this_vector(self, target, from_bit_index: int):
        """! @brief Assign a Signal or Port from part of this vector Signal.
        Use for partial assignment from this (vector) signal
        to other signals. For complete assignments (entire vector)
        use the 'connect' method!"""
        self.__vector_assignment__(target, from_bit_index, "out")

    def define_vector_assignment(self, source_list):
        """! @brief Define the assignment of this vector Signal from a list of sources.
        Assign the value of this vector from list of sources.
        @note NOT compatible with the method 'assign_to_this_vector'.
        Use either exclusively to assign to a vector signal."""
        self.vector_assignment_tasks.extend(list(source_list))

    ## @ingroup automatics_connection
    def __process_vector_assignment_tasks__(self):
        bit_counter = 0
        for port in self.vector_assignment_tasks:
            self.assign_to_this_vector(port, bit_counter)
            bit_counter += port.data_width.get_bit_width()

    def assign_to_this_vector(self, source, from_bit_index: int):
        """! @brief Assign a Signal or Port to part of this vector Signal.
        Use for partial assignment to this (vector) signal
        to other signals. For complete assignments (entire vector)
        use the 'connect' method of the source signal!"""
        self.__vector_assignment__(source, from_bit_index, "in")

    ## @}

    ## @ingroup automatics_connection
    def __vector_assignment__(self, other, from_bit_index: int, direction: str):
        if "vector" not in self.data_type:
            raise AsConnectionError(
                self,
                (
                    "Cannot partially assign to/from signal '{}'"
                    " with data type '{}'."
                ).format(self, self.data_type),
            )
        # Removing an assignment
        if other is None:
            if direction == "in":
                vector_map = self.vector_map_incoming
                con_list = self.incoming
            else:
                vector_map = self.vector_map_outgoing
                con_list = self.outgoing
            # Get the connecting signal
            try:
                other = self.vector_map_incoming[from_bit_index]
            except KeyError:
                return False
            # Remove the references in the vector map and connection list
            con_list.remove(other)
            vector_map.pop(from_bit_index)
            return True

        if other.data_type not in (
            "std_logic",
            "std_logic_vector",
            "bit",
            "bit_vector",
            "std_ulogic",
            "std_ulogic_vector",
        ):
            raise AsConnectionError(
                self,
                (
                    "Cannot partially assign {} with data type '{}' "
                    "to/from signal '{}'."
                ).format(other, other.data_type, self),
            )
        omod = get_parent_module(other)
        if (not isinstance(other, GenericSignal)) and (
            omod.modlevel > get_parent_module(self).modlevel
        ):
            if other.glue_signal:
                other = other.glue_signal
            else:
                signame = omod.name + "_" + other.code_name + "_signal"
                sig = omod.parent.get_signal(signame)
                if sig is None:
                    sig = omod.parent.define_signal(
                        signame, other.data_type, other.data_width
                    )
                sig.generics = copy.copy(other.generics)
                omod.chain.__connect__(sig, other, top=omod.parent)
                other = sig

        # Make the connection
        if direction == "in":
            other.outgoing.append(self)
            self.incoming.append(other)
            self.vector_map_incoming[from_bit_index] = other
            # Add a glue signal if not present
            if not isinstance(other, GenericSignal):
                if other.glue_signal is None:
                    other.glue_signal = GlueSignal.generate_glue_signal(
                        other, other, self
                    )
        else:
            other.incoming.append(self)
            self.outgoing.append(other)
            self.vector_map_outgoing[from_bit_index] = other

    # Overwriting Port.make_external()
    ## @ingroup automatics_connection
    def make_external(self, external_port_name: str = "") -> bool:
        if self.parent is not None:
            if not external_port_name:
                portname = self.code_name + "_sig_ext"
            else:
                portname = external_port_name
            port_dir = "out"
            module = self.parent
            ext_port = module.get_port(portname, suppress_error=True)
            if ext_port is not None:
                if (
                    ext_port.direction != port_dir
                    or ext_port.incoming is not None
                ):
                    LOG.error(
                        (
                            "Externalizing signal '%s': Port with name '%s' "
                            "already exists in module '%s'! Define another "
                            "port name to resolve this conflict."
                        ),
                        self.code_name,
                        portname,
                        module.name,
                    )
                    raise AsConnectionError(
                        self,
                        "Port with name '{}' already exists.".format(portname),
                        "While making signal '{}' external".format(
                            self.code_name
                        ),
                    )
            if ext_port is None:
                ext_port = module.define_port(
                    name=portname,
                    code_name=portname,
                    direction=port_dir,
                    data_type=self.data_type,
                    data_width=self.data_width,
                )
            ext_port.incoming = self
            self.outgoing.append(ext_port)
            return True
        LOG.error(
            (
                "Could not externalize signal '%s': "
                "Signal is not associated to any module!"
            ),
            self.code_name,
        )
        return False

    def __check_vector_assignments__(self):
        """! @brief Checks the plausibility of the vector assignments.
        If assignments are overlapping or out of bounds, an AsConnectionError
        is raised."""
        if not self.data_width.is_resolved():
            raise AsConnectionError(
                self,
                (
                    "Cannot partially assign to/from signal '{}' "
                    "with unresolved data width '{}' (generics present)!"
                ).format(self, self.data_width),
            )
        bitwidth = self.data_width.get_bit_width()
        for vector_map in (self.vector_map_incoming, self.vector_map_outgoing):
            assignment_map = set()
            # Check plausibility of vector assignment (out of bounds, overlap, etc.)
            for assignment_id in vector_map:
                # Is bit position out of bounds?
                if assignment_id > bitwidth:
                    raise AsConnectionError(
                        self,
                        (
                            "Vector assignment to/from signal '{}' at "
                            "bit index {} is out of bounds for signal type: {}"
                        ).format(
                            self,
                            assignment_id,
                            as_help.get_printable_datatype(self),
                        ),
                    )
                # Get source port/signal
                signal = vector_map[assignment_id]
                # Is its data width resolved?
                if not signal.data_width.is_resolved():
                    raise AsConnectionError(
                        signal,
                        (
                            "Cannot assign {} to/from vector signal {}. "
                            "Data width '{}' is unresolved!"
                        ).format(
                            signal, self, as_help.get_printable_datatype(signal)
                        ),
                    )

                # Get bit width and a tuple with all bit positions to assign to
                signal_bit_width = signal.data_width.get_bit_width()
                new_map = tuple(
                    range(assignment_id, assignment_id + signal_bit_width)
                )
                # Does the new assignment overlap with previous assignments?
                if assignment_map.intersection_update(new_map):
                    raise AsConnectionError(
                        signal,
                        (
                            "Vector assignment to/from signal '{}' from '{}' "
                            "overlaps with previous assignments! List: {}"
                        ).format(self, signal, vector_map),
                    )


## @ingroup automatics_intrep
class GlueSignal(GenericSignal):
    """! @brief Variation of as_automatics_port::Port representing a glue signal.
    Inherits as_automatics_signal::GenericSignal.
    Has additional attributes and may have multiple incoming data sources.
    The 'direction' and 'connected' attribute are ignored for this class.
    Used only to connect a port to a VHDL component in a port map."""

    def __init__(
        self,
        name: str = "",
        code_name: str = "",
        port_type: str = "glue_signal",
        data_type: str = "std_logic",
        optional: bool = False,
        data_width=Port.DataWidth(1, None, None),
    ):
        super().__init__(
            name, code_name, port_type, data_type, optional, data_width
        )

    @classmethod
    def generate_glue_signal(
        cls, port: Port, con_from: Port, con_to: Port
    ) -> Port:
        """! @brief Generates and returns a GlueSignal port for the given port.
        First checks a few things using the provided ports (con_to, con_from),
        to determine if a glue signal is required."""
        from_parent = get_parent_module(con_from)
        to_parent = get_parent_module(con_to)
        from_mdlvl = getattr(from_parent, "modlevel", 0)
        to_mdlvl = getattr(to_parent, "modlevel", 0)
        if from_mdlvl + 1 == to_mdlvl:
            return cls.generate_glue_signal(con_to, con_to, con_from)
        if from_mdlvl == to_mdlvl + 1:
            try:
                con_sig = to_parent.get_signal(con_to.code_name)
            except AttributeError:
                con_sig = None
            if con_sig is None:
                con_sig = con_to
            return con_sig

        if from_mdlvl != to_mdlvl:
            return None
        # If the connection source is already a signal
        if isinstance(con_from, GenericSignal):
            return con_from

        # For ports: Format and generate the glue signal name
        if con_from.port_type == "interface":
            signame = "{}_{}{}".format(
                get_parent_module(port).name,
                port.parent.name_prefix,
                port.code_name,
            )
        else:
            signame = "{}_{}".format(
                get_parent_module(port).name, port.code_name
            )
        # Create the glue signal object
        signal = cls(
            name=signame, data_width=port.data_width, data_type=port.data_type
        )
        # Add delay value (for 2D Window Pipeline systems) to glue signal
        try:
            setattr(signal, "delay", con_from.delay)
        except AttributeError:
            pass
        signal.assign_to(get_parent_module(port))
        signal.incoming = con_from
        signal.outgoing.append(con_to)
        return signal
