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
-- File:           ea_set_clipped_area.c
--
-- Company:        University of Applied Sciences, Augsburg, Germany
--
-- Author:         Tobias Engelhard
-- Date:           10/11/2009
--
-- Modified:       * 03/12/2009 by Andreas Becher
--                 * 24/01/2010 by Tobias Engelhard
--                 * 04/06/2019 by Michael Schaeferling
--                 * 12/09/2019 by Michael Schaeferling
--
-- Description:    Sets the clipped area of the overlay.
--------------------------------------------------------------------------------*/


#include "embedded_augmenter_lib.h"
#include "embedded_augmenter_helpers.h"

ea_bool ea_set_clipped_area (uint32_t x_left, uint32_t y_low, uint32_t x_right, uint32_t y_high)
{
  if (x_left > WIDTH || x_right > WIDTH) {
    return ea_false;
  }
  
  if (y_high > HEIGHT || y_low > HEIGHT) {
    return ea_false;
  }
  
  if (x_left > x_right || y_high > y_low) {
    return ea_false;
  }

  X_LEFT = x_left;
  Y_HIGH = y_high;
  X_RIGHT = x_right;
  Y_LOW = y_low;

  return ea_true;
}
