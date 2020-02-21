# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_automatics_2d_infrastructure.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Module containing helper and infrastructure classes (WindowRef, AsLayer,
 AsWindowSection, ...) for the 2D Window Pipeline of ASTERICS.
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
# @file as_automatics_2d_infrastructure.py
# @author Philip Manke
# @brief Helper module for the 2D Window Pipeline of ASTERICS.
# -----------------------------------------------------------------------------


from collections import namedtuple
from typing import Sequence
from copy import copy, deepcopy

from as_automatics_port import Port
from as_automatics_helpers import is_data_width_resolved
from as_automatics_exceptions import AsConnectionError

import as_automatics_logging as as_log

LOG = as_log.get_log()


class WindowRef:
    columns = 0
    rows = 0
    init = False

    def __init__(self, col: int, row: int):
        self.row = row
        self.col = col
        if self.init:
            self.refnum = self.row * self.columns + self.col
        else:
            self.refnum = None

    def __str__(self):
        return "({}, {})".format(self.col, self.row)

    def __repr__(self):
        return str(self.refnum)

    def coords(self) -> tuple:
        return (self.col, self.row)

    def update(self, ref):
        if isinstance(ref, WindowRef):
            self.refnum = ref.refnum
        elif isinstance(ref, int):
            self.refnum = ref
        else:
            raise TypeError(
                "WindowRef.update() doesn't accept type {}!".format(type(ref))
            )
        self.__update__()

    def __update__(self):
        """Compute this refs correct attribute values, for when one of the 
        representations needs to be updated.
        Usually updates the column and row numbers.
        Can also be used to compute the refnum after setting the classes
        columns and rows attributes."""
        if self.refnum is None and self.col is not None and self.row is not None:
            self.refnum = self.columns * self.row + self.col
        else:
            self.row = int(self.refnum / self.columns)
            if self.row > self.rows:
                raise AttributeError("Reference '{}' out of bounds!".format(repr(self)))
            self.col = self.refnum % self.columns

    def __eq__(self, other):
        if isinstance(other, int):
            return self.refnum == other
        if isinstance(other, WindowRef):
            if self.refnum is None:
                return self.col == other.col and self.row == other.row
            return self.refnum == other.refnum
        self.__comp_type_error__(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __gt__(self, other):
        if isinstance(other, WindowRef):
            return self.refnum > other.refnum
        if isinstance(other, int):
            return self.refnum > other
        self.__comp_type_error__(other)

    def __lt__(self, other):
        if self.__eq__(other):
            return False
        return not self.__gt__(other)

    def __ge__(self, other):
        if self.__eq__(other):
            return True
        return self.__gt__(other)

    def __le__(self, other):
        if self.__eq__(other):
            return True
        return self.__lt__(other)

    def __sub__(self, other: int):
        if isinstance(other, WindowRef):
            other = other.refnum
        elif not isinstance(other, int):
            self.__math_type_error__(other)
        out = copy(self)
        out.refnum -= other
        out.__update__()
        return out

    def __add__(self, other: int):
        if isinstance(other, WindowRef):
            other = other.refnum
        elif not isinstance(other, int):
            self.__math_type_error__(other)
        out = copy(self)
        out.refnum += other
        out.__update__()
        return out

    def get_ref(self):
        return self

    @classmethod
    def set_windowsize(cls, columns: int, rows: int):
        cls.columns = columns
        cls.rows = rows
        cls.init = True

    @classmethod
    def get_ref_from_refnum(cls, refnum: int):
        out = WindowRef(0, 0)
        out.update(refnum)
        return out

    @staticmethod
    def __comp_type_error__(other):
        raise TypeError(
            "Comparison of WindowRef with '{}' not allowed!".format(type(other))
        )

    @staticmethod
    def __math_type_error__(other):
        raise TypeError(
            "Arithmatic of WindowRef with '{}' not allowed!".format(type(other))
        )


class WindowDef:
    def __init__(self, from_x, to_x, from_y, to_y):
        self.from_x = from_x
        self.to_x = to_x
        self.from_y = from_y
        self.to_y = to_y
        self.start_ref = WindowRef(self.from_x, self.from_y)
        self.end_ref = WindowRef(self.to_x, self.to_y)

    def __str__(self):
        return "{} to {}".format(str(self.start_ref), str(self.end_ref))

    def __repr__(self):
        return "{} to {}".format(repr(self.start_ref), repr(self.end_ref))


class AsConnectionRef(WindowRef):
    def __init__(self, ref: WindowRef, port: Port):
        super().__init__(ref.col, ref.row)
        self.port = port

    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        if isinstance(other, AsConnectionRef):
            return self.port is other.port
        return True

    def __str__(self):
        return "{} {} {}".format(
            super().__str__(),
            ("->" if self.port.direction == "in" else "<-"),
            self.port.code_name,
        )

    def __repr__(self):
        return "{} {} {}".format(self.refnum, self.port.direction, self.port.code_name)

    def __add__(self, other):
        return AsConnectionRef(super().__add__(other), self.port)

    def __sub__(self, other):
        return AsConnectionRef(super().__sub__(other), self.port)

    def get_ref(self) -> WindowRef:
        return WindowRef(self.col, self.row)


class AsLayerRef(WindowRef):
    def __init__(self, col: int, row: int, layer):
        super().__init__(col=col, row=row)
        self.layer = layer

    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        if isinstance(other, AsLayerRef):
            return self.layer is other.layer
        return True

    def __str__(self) -> str:
        return "{} of {}".format(super().__str__(), self.layer.name)

    def __add__(self, other):
        return AsLayerRef(*super().__add__(other).coords(), self.layer)

    def __sub__(self, other):
        return AsLayerRef(*super().__sub__(other).coords(), self.layer)

    def get_ref(self) -> WindowRef:
        return WindowRef(self.col, self.row)


class AsLayer:
    """Class representing a data layer of the 2DWindowPipeline.
    The pipeline is made up of two dimensional AsLayers stacked on top
    of each other. Each layer must have exactly one data input and may have
    one or more data outputs to AsWindowModules.
    Parameters:
        name: Name of the AsLayer. Referenced in the Auto-Tag of AsWindowModules
        data_width: Width of the data transported in the layer as bits
        parent_pipeline: Reference to the associated As2DWindowPipeline object
    """

    def __init__(self, name: str, data_width: int, parent_pipeline):
        self.modules = []
        self.parent = parent_pipeline
        self.interfaces = []
        self.data_width = data_width
        self.start_ref = None
        self.end_ref = None
        self.sections = []
        self.output_refs = []
        self.input = None
        self.name = name
        self.base_layer = False
        self.delay = WindowRef(0, 0)

    def __repr__(self) -> str:
        return self.name

    def __gt__(self, other):
        if not isinstance(other, AsLayer):
            raise TypeError(
                "Comparison between AsLayer and {} unsupported!".format(type(other))
            )
        return self.offset < other.offset

    def connect(self, interface, offset: tuple = None):
        self.parent.connect(interface, self, offset)

    def add_section(self, section) -> bool:
        if any((True for sec in self.sections if sec in section)):
            LOG.debug(
                (
                    "Tried adding section '%s' to layer '%s'. Section alread"
                    "y present or overlapping!"
                ),
                str(section),
                self.name,
            )
            return False
        self.sections.append(section)
        return True

    def is_valid_ref(self, ref: WindowRef, direction: str) -> bool:
        if any((self.input is None, self.start_ref is None, self.end_ref is None)):
            LOG.debug("'is_valid_ref()' returned False: Layer not initialized!")
            return False
        if direction == "in":
            # Port is data sink -> layer outputs data
            # => ref must be after layer input
            if (self.input <= ref) and (ref <= self.end_ref):
                return True
        elif direction == "out":
            # Port is data source -> layer is data sink
            # => ref must be after layer.start_ref
            if (ref > self.start_ref) and (ref <= self.end_ref):
                return True
        return False

    def remove_section(self, section) -> bool:
        try:
            self.sections.remove(section)
        except ValueError as err:
            LOG.debug(
                "Couldn't remove '%s' from '%s': '%s'",
                repr(section),
                self.name,
                str(err),
            )
            return False
        return True

    def is_input(self, ref: WindowRef = None, refnum: int = 0):
        if ref is None:
            ref = WindowRef.get_ref_from_refnum(refnum)
        return self.input == ref

    def is_output(self, ref: WindowRef = None, refnum: int = 0):
        if ref is None:
            ref = WindowRef.get_ref_from_refnum(refnum)
        return ref in self.output_refs

    def set_offset(self, offset: WindowRef):
        if offset < 0 or offset > self.parent.get_last_ref():
            LOG.error("Offset for layer '%s' out of bounds!", self.name)
            raise ValueError("Reference out of bounds: %s", str(offset))
        self.offset = offset

    def set_input(self, input_ref: AsConnectionRef):
        """Set the data input reference for this layer.
        Each layer's input reference should be @ (0,0), with the layer.offset
        signifying the layer's offset from the base layer."""
        port = input_ref.port
        # Check data widths if the port's data width is already fixed
        if is_data_width_resolved(port.data_width):
            port_data_width = Port.data_width_to_string(port.data_width)
            if self.data_width != port_data_width:
                LOG.error(
                    ("Incompatiple layer input detected! '%s'(%s) -> " "'%s'(%s)"),
                    port.code_name,
                    port_data_width,
                    self.name,
                    self.data_width,
                )
                raise AsConnectionError("Layer and input port data widths differ!")
        if (
            (input_ref.row < self.parent.rows)
            and (input_ref.col < self.parent.columns)
            and (input_ref.row >= 0 and input_ref.col >= 0)
        ):
            self.input = input_ref
            LOG.debug("Set input for layer '%s' to %s.", self.name, str(input_ref))
        else:
            LOG.error("Input '%s' is out of bounds!", str(input_ref))

    def add_outputs(self, iterable: Sequence[AsConnectionRef]) -> list:
        """Add multiple data outputs to this layer"""
        out = []
        for item in iterable:
            out.append(self.add_output(item))
        return out

    def add_output(
        self, output_ref: AsConnectionRef, ignore_offset: bool = False
    ) -> AsLayerRef:
        """Add a data output to this layer. The layer's offset parameter is
        automatically applied, unless the parameter 'ignore_offset' is set to
        True."""
        if ignore_offset:
            to_add = output_ref
        else:
            to_add = output_ref + self.offset
        found = next((ref for ref in self.output_refs if ref == to_add), None)
        if found:
            LOG.debug(
                "Did not add output at '%s', already in layer '%s'!",
                str(to_add),
                self.name,
            )
        else:
            if (to_add.row < self.parent.rows) and (to_add.col < self.parent.columns):
                self.output_refs.append(to_add)
                LOG.debug(
                    "Added filter output %s to layer '%s'.", str(to_add), self.name
                )
            else:
                raise AttributeError("Out of bounds!")
        return AsLayerRef(to_add.col, to_add.row, self)

    def set_bounds(self, ref_from: WindowRef, ref_to: WindowRef):
        # Sanity check: Make sure the references are inside the window
        if (ref_from.col >= self.parent.columns) or (ref_to.col >= self.parent.columns):
            # TODO: Error handling
            raise AttributeError("Out of bounds!")
        if ref_from.row >= self.parent.rows or ref_to.row >= self.parent.rows:
            # TODO: Error handling
            raise AttributeError("Out of bounds!")

        start = ref_from.row * self.parent.columns + ref_from.col
        end = ref_to.row * self.parent.columns + ref_to.col
        if (end - start) <= 0:
            # TODO: Error handling
            raise AttributeError("Out of bounds!")

        self.start_ref = ref_from
        self.end_ref = ref_to


class AsWindowSection:
    """Class representing a section of ASTERICS 2DWindowPipeline.
    Contains the start and end references of the section, which data layers it
    spans, the implementation strategy, ..."""

    BRAM = "bram"
    FF = "flipflops"

    def __init__(self, layer_ref, data_width: int):
        self.parent = layer_ref
        self.impl_type = self.FF
        self.start_ref = None
        self.end_ref = None
        self.data_width = data_width
        self.layers = {layer_ref}
        self.bram_id = None

    def set_bounds(self, ref_from: WindowRef, ref_to: WindowRef):
        self.start_ref = ref_from
        self.end_ref = ref_to

    def width(self) -> int:
        """Return the width of this section's start and end references"""
        return self.end_ref.refnum - self.start_ref.refnum

    def __str__(self) -> str:
        return "{} -> {} | {}".format(self.start_ref, self.end_ref, self.impl_type)

    def __repr__(self) -> str:
        return "{} -> {}".format(repr(self.start_ref), repr(self.end_ref))

    def __contains__(self, other):
        """Overloading of the 'in' operator. Does this section fully contain
        another section?"""
        # Does this section contain all layers of the other layer?
        if not all((layer in other.layers for layer in self.layers)):
            return False
        # Do the start and end references of the other layer
        # fall within this section's references?
        if (other.start_ref >= self.start_ref) and (other.end_ref <= self.start_ref):
            return True
        return False

    def overlaps(self, other) -> bool:
        """Determine if this section overlaps another section
        as a boolean function."""
        # Do the sections share any layers? No? -> No overlap?
        if not any((layer in self.layers for layer in other.layers)):
            return False
        # Yes? -> Do the start and end references overlap?
        if (other.end_ref > self.start_ref) and (other.start_ref < self.end_ref):
            return True
        return False

    def __eq__(self, other):
        if self.start_ref != other.start_ref:
            return False
        if self.end_ref != other.end_ref:
            return False
        if self.data_width != other.data_width:
            return False
        if self.layers == other.layers:
            return True
        return False

    def get_overlap(self, sec):
        """Determine and return a section object of
        the overlap between this section and the provided section object.
        Returns None if there is no overlap."""
        # Is there any overlap?
        if sec.end_ref < self.start_ref or self.end_ref < sec.start_ref:
            return None
        # Output will be a copy of this section object
        out = copy(self)
        # Update the start or endpoint if necessary
        if sec.start_ref > out.start_ref:
            out.start_ref = sec.start_ref
        if sec.end_ref < out.end_ref:
            out.end_ref = sec.end_ref
        # Copy the layers set. IMPORTANT, we need a separate set per section!
        out.layers = copy(self.layers)
        # Add the layers of the provided section
        out.layers.add(sec.parent)
        out.data_width += sec.data_width
        return out

    def split(self, split_at: WindowRef):
        """Splits this section into multiple sections.
        Split either at a single point, resulting with two sections
        (start -> split_at - 1, split_at -> end)."""
        # Create the second part of the section
        # it will be split into as a copy of itself
        new_sec = copy(self)
        # Move the endpoint of the section to the point before the split point
        self.end_ref = split_at - 1
        # The new section starts at the split point
        # (it's end reference) can stay as the endpoint of the original section
        new_sec.start_ref = split_at
        # Add the new section to all layers it spans
        for layer in self.layers:
            layer.sections.append(new_sec)
        return new_sec

    def size(self) -> int:
        """Return the size of the section in bits."""
        return self.data_width * self.width()
