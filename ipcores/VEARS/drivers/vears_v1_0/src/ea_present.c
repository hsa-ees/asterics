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
-- Copyright (C) 2018-2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- File:           ea_present.c
--
-- Company:        University of Applied Sciences, Augsburg, Germany
--
-- Author:         Michael Schaeferling, Gundolf Kiefer
-- Date:           24/08/2018
--
-- Modified:       * 25/08/2018 by Gundolf Kiefer
--
-- Description:
--------------------------------------------------------------------------------*/


#include "embedded_augmenter_lib.h"

#include <xil_cache.h>


ea_bool ea_present()
{
// Proper way to do this:
//   1) use a single buffer:
//       - each change is directly applied to the frame buffer
//       - finally, d-cache is flushed
//
//   2) use double buffering, with each frame needing to be completely re-drawn #
//       (may be computationally exhaustive):
//       - draw to new (empty) buffer
//       - flush d-cache and switch buffers in hardware
//
// NOTE [GK]: In the current implementation, any 'vears_*()' function that sets
//     a buffer or draws something to the overlay performs a cache flush. This
//     makes '*_present()' superfluous.
//     This simplifies the interface, and the flushing effort is not too high.

  // we just use a single buffer right now:
	Xil_DCacheFlush();
	return ea_true;
}
