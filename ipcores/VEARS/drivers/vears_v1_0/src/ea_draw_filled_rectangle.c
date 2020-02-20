/*--------------------------------------------------------------------------------
-- This file is part of V.E.A.R.S.
--
-- V.E.A.R.S. is free software: you can redistribute it and/or modify
-- it under the terms of the GNU Lesser General Public License as published by
-- the Free Software Foundation, either version 3 of the License, or
-- (at your option) any later version.
--
-- V.E.A.R.S. is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
-- GNU Lesser General Public License for more details.
--
-- You should have received a copy of the GNU Lesser General Public License
-- along with V.E.A.R.S. If not, see <http://www.gnu.org/licenses/lgpl.txt>.
--
-- Copyright (C) 2010-2019 Andreas Becher, Tobias Engelhard,
--                         Christian Hilgers, Moritz Lessmann and
--                         Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- File:           ea_draw_filled_rectangle.c
--
-- Company:        University of Applied Sciences, Augsburg, Germany
--
-- Author:         Moritz Lessmann
-- Date:           10/11/2009
--
-- Modified:       * 10/11/2009 by Moritz Lessmann
--                 * 13/11/2009 by Andreas Becher
--                 * 23/11/2009 by Tobias Engelhard
--                 * 06/01/2010 by Moritz Lessmann
--                 * 24/01/2010 by Tobias Engelhard
--                 * 04/06/2019 by Michael Schaeferling
--                 * 12/09/2019 by Michael Schaeferling
--
-- Description:    Draws a filled rectangle.
--------------------------------------------------------------------------------*/


#include "embedded_augmenter_lib.h"
#include "embedded_augmenter_helpers.h"

ea_bool ea_draw_filled_rectangle (uint32_t x_left, uint32_t y_low, uint32_t x_right, uint32_t y_high, uint32_t color)
{
  ea_bool returnvalue = ea_true;
  uint32_t y_recent = y_high;

  if (x_left > x_right) {                   //swap x_values if necessary
    x_left ^= x_right;
    x_right ^= x_left;
    x_left ^= x_right;
  }

  if (y_low > y_high) {                      //swap y_values if necessary
    y_low ^= y_high;
    y_high ^= y_low;
    y_low ^= y_high;
  }

  while (1) {
    if (ea_draw_quick_line_h (x_left, x_right,  y_recent,  color) == ea_false) {
      returnvalue = ea_false;
    }
    if (y_recent == y_low) break;
    y_recent--;
  }
  
  return returnvalue;
}
