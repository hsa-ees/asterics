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
-- File:           embedded_augmenter_helpers.h
--
-- Company:        University of Applied Sciences, Augsburg, Germany
--
-- Author:         Tobias Engelhard
-- Date:           29/10/2009
--
-- Modified:       * 10/11/2009 by Tobias Engelhard
--                 * 17/11/2009 by Tobias Engelhard
--                 * 18/01/2010 by Tobias Engelhard
--                 * 24/01/2010 by Tobias Engelhard
--                 * 22/07/2011 by Ulrich Hornung (fixed problematic #define true 0 and #define false -1)
--                 * 16/11/2013 by Michael Schaeferling
--                 * 04/06/2019 by Michael Schaeferling
--                 * 12/09/2019 by Michael Schaeferling
--
-- Description:    Internal header for helper functions.
--------------------------------------------------------------------------------*/


#ifndef EA_LIB_HELPER
#define EA_LIB_HELPER EA_LIB_HELPER

#include <stdint.h>


#ifndef EA_BOOL_DEFINED
#define EA_BOOL_DEFINED
typedef uint8_t ea_bool;
#define ea_false 0
#define ea_true 1
#endif


// Clipped area:
extern uint32_t X_LEFT;  //Left Border of the overlay
extern uint32_t Y_HIGH;  //Upper Border of the overlay
extern uint32_t X_RIGHT; //Right Border of the overlay
extern uint32_t Y_LOW;   //Lower Border of the overlay

extern uint32_t* hardware_overlay_address;  // pointer to hardware processing overlay
extern uint32_t* overlay_table;  // pointer to software writing overlay
extern uint32_t* mask;

ea_bool ea_draw_quick_line_h (uint32_t, uint32_t, uint32_t, uint32_t);

/*************************************************************************
Function:
Draws quickly a horizontal line from one point to the other

Meaning of the transfer-values:
Coordinates of the two points (X1, int; X2, int; Y, int) and the colour (int)

Meaning of the return-value:
Did the Function perform well?
*************************************************************************/

ea_bool ea_draw_quick_line_v (uint32_t, uint32_t, uint32_t, uint32_t);

/*************************************************************************
Function:
Draws quickly a vertical line from one point to the other

Meaning of the transfer-values:
Coordinates of the two points (X, int; Y1, int; Y2, int) and the colour (int)

Meaning of the return-value:
Did the Function perform well?
*************************************************************************/


uint32_t get_mask(uint32_t,uint32_t,uint32_t);

/*************************************************************************
Function:
return a Mask with a color between highest Pixel and lowest Pixel

Meaning of the transfer-values:
hp (int) = highest Pixel
lp (int) = lowest Pixel and the colour (int)

Meaning of the return-value:
mask
*************************************************************************/

ea_bool ea_draw_int(uint32_t x, uint32_t y, uint32_t muster , uint32_t color);


#endif

