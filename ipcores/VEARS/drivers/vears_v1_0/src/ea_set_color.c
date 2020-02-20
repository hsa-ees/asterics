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
-- File:           ea_set_color.c
--
-- Company:        University of Applied Sciences, Augsburg, Germany
--
-- Author:         Tobias Engelhard
-- Date:           29/10/2009
--
-- Modified:       * 22/12/2009 by Andreas Becher
--                 * 24/01/2010 by Tobias Engelhard
--                 * 04/06/2019 by Michael Schaeferling
--                 * 12/09/2019 by Michael Schaeferling
--
-- Description:    Writes a colour value into the CLUT.
--------------------------------------------------------------------------------*/


#include "embedded_augmenter_lib.h"
#include "embedded_augmenter_helpers.h"

#include "vears.h"


ea_bool ea_set_color(uint32_t R_in, uint32_t G_in, uint32_t B_in , uint32_t color_idx)
{
  uint32_t color_val;

  color_idx--;

  // check if red channel is in range
  if (R_in > 255)
  {
    return ea_false;
  }
  // check if green channel is in range
  if (G_in > 255)
  {
    return ea_false;
  }
  // check if blue channel is in range
  if (B_in > 255)
  {
    return ea_false;
  }

  // check if index is in range
  if (color_idx >= (1 << COLOR_DEPTH)-1)
  {
    return ea_false;
  }

  color_val = (R_in << 16) + (G_in << 8) + B_in;

  vears_overlay_set_color (VEARS_BASEADDR, color_idx, color_val);

  return ea_true;
}
