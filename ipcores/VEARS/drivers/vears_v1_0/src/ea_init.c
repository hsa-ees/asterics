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
-- File:           ea_init.c
--
-- Company:        University of Applied Sciences, Augsburg, Germany
--
-- Author:         Tobias Engelhard
-- Date:           29/10/2009
--
-- Modified:       * 02/11/2009 by Andreas Becher
--                 * 24/01/2010 by Tobias Engelhard
--                 * 22/07/2011 by Ulrich Hornung (fixed endless loop when using COLOR_DEPTH >= 8)
--                 * 04/06/2019 by Michael Schaeferling
--                 * 12/09/2019 by Michael Schaeferling
--
-- Description:    Overwrites the CLUT with transparent overlay.
--------------------------------------------------------------------------------*/


#include "embedded_augmenter_lib.h"
#include "embedded_augmenter_helpers.h"

#include "stdlib.h"

ea_bool ea_init(void)
{
  uint32_t i  = 0;
  uint32_t ii = 0;

  for (i = 1; i <= (1 << COLOR_DEPTH) - 1; i++) // Color Table to 0
  {
    ea_set_color(0, 0, 0, i);
  }

  ea_set_clipped_area(0, HEIGHT - 1, WIDTH - 1, 0); // Set clipped area to screen size

  mask = (uint32_t*) malloc((1 << COLOR_DEPTH) * sizeof (uint32_t));

  for (i=0; i < ((1<<COLOR_DEPTH));i++)
  {
    mask[i]=0;
    for (ii=0; ii< (PIXEL_PER_INT);ii++)
      mask[i] |= i << (ii*COLOR_DEPTH);
  }

  return ea_true;
}
