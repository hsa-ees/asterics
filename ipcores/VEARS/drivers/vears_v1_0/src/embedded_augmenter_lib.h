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
-- File:           embedded_augmenter_lib.h
--
-- Company:        University of Applied Sciences, Augsburg, Germany
--
-- Author:         Tobias Engelhard
-- Date:           14/10/2009
--
-- Modified:       * 29/10/2009 by Tobias Engelhard
--                 * 02/11/2009 by Andreas Becher
--                 * 10/11/2009 by Tobias Engelhard
--                 * 11/11/2009 by Moritz Lessmann
--                 * 13/11/2009 by Andreas Becher
--                 * 17/01/2010 by Tobias Engelhard
--                 * 24/01/2010 by Tobias Engelhard
--                 * 22/07/2011 by Ulrich Hornung (fixed problematic #define true 0 and #define false -1)
--                 * 16/11/2013 by Michael Schaeferling
--                 * 04/06/2019 by Michael Schaeferling
--                 * 12/09/2019 by Michael Schaeferling
--
-- Description:    User header of the Overlay.
--------------------------------------------------------------------------------*/


#ifndef EA_LIB                              //protection from multiple inclusion
#define EA_LIB EA_LIB

#include <stdint.h>

#include "embedded_augmenter_font.h"

extern uint32_t vears_frame_width;
extern uint32_t vears_frame_height;

#define WIDTH vears_frame_width
#define HEIGHT vears_frame_height


#define BUS_WIDTH 32                          //Number of Bits in datatype integer

#ifdef __linux__
// set color with to 8 bit on PC system -> this is easier to convert into image  data to show with opencv
#define COLOR_DEPTH 8                          //Colour depth of the overlay
#else
#define COLOR_DEPTH 2                          //Colour depth of the overlay
#endif

#define PIXEL_PER_INT (BUS_WIDTH / COLOR_DEPTH)




#ifdef __cplusplus
extern "C" {
#endif

#ifndef EA_BOOL_DEFINED
#define EA_BOOL_DEFINED
typedef unsigned char ea_bool;
#define ea_false 0
#define ea_true 1
#endif

ea_bool ea_set_overlay_hardware_address(uint32_t *);

/*************************************************************************
Function:
Sets the address where the overlayhardware should read

Meaning of the transfer-values:
Address

Meaning of the return-value:
Did the Function perform well?
*************************************************************************/

uint32_t* ea_get_overlay_hardware_address (void);

/*************************************************************************
Function:
Gets the address where the overlayhardware should write to

Meaning of the transfer-values:

Meaning of the return-value:
The Address as unsigned integer where the overlayhardware writes to
*************************************************************************/

ea_bool ea_set_overlay_software_address (uint32_t *);

/*************************************************************************
Function:
Sets the address where the lib should write to

Meaning of the transfer-values:
Address

Meaning of the return-value:
Did the Function perform well?
*************************************************************************/

uint32_t* ea_get_overlay_software_address (void);

/*************************************************************************
Function:
Gets the address where the lib should write to

Meaning of the transfer-values:

Meaning of the return-value:
The Address as unsigned integer where the lib writes to
*************************************************************************/

ea_bool ea_init (void);

/*************************************************************************
Function:
Initialize the Overlay with 0 = Backgroundcolor = VGA

Meaning of the transfer-values:

Meaning of the return-value:
Did the Function perform well?
*************************************************************************/


ea_bool ea_set_color (uint32_t, uint32_t, uint32_t, uint32_t);

/*************************************************************************
Function:
Sets A Color on the CLUT

Meaning of the transfer-values:
Colour Values R (int), G (int), B (int) and index (int)
Color as Color Values Red, Green and Blue with each has 4Bit (0-15).
Int, Index which the Color should select with.

Meaning of the return-value:
Did the Function perform well?
*************************************************************************/

ea_bool ea_erase (void);

/*************************************************************************
Function:
Erasing the drawn overlay

Meaning of the transfer-values:
no transfer-values

Meaning of the return-value:
Did the Function perform well?
*************************************************************************/

ea_bool ea_set_clipped_area (uint32_t, uint32_t, uint32_t, uint32_t);

/*************************************************************************
Function:
Sets the protected area of the overlay outside the in the defineded rectangle (if it's in the "monitor area")

Meaning of the transfer-values:
Lower left corner point (X_LEFT, int; Y_LOW, int) and upper right corner point (X_RIGHT, int; Y_HIGH, int)

Meaning of the return-value:
Did the Function perform well?
*************************************************************************/

ea_bool ea_draw_point (uint32_t, uint32_t, uint32_t);

/*************************************************************************
Function:
Draws one point on the overlay

Meaning of the transfer-values:
Coordinates of the point (X, int; Y, int) and the colour (int)

Meaning of the return-value:
Did the Function perform well?
*************************************************************************/

ea_bool ea_draw_line (uint32_t, uint32_t, uint32_t, uint32_t, uint32_t);

/*************************************************************************
Function:
Draws a line from one point to the other

Meaning of the transfer-values:
Coordinates of the two points (X1, int; Y1, int; X2, int; Y2, int) and the colour (int)

Meaning of the return-value:
Did the Function perform well?
*************************************************************************/

ea_bool ea_draw_circle (uint32_t, uint32_t, uint32_t, uint32_t);

/*************************************************************************
Function:
Draws an unfilled circle

Meaning of the transfer-values:
Center of the circle (X, int; Y, int), radius (int) and colour (int)

Meaning of the return-value:
Did the Function perform well?
*************************************************************************/

ea_bool ea_draw_filled_circle (uint32_t, uint32_t, uint32_t, uint32_t);

/*************************************************************************
Function:
Draws a filled circle

Meaning of the transfer-values:
Center of the circle (X, int; Y, int), radius (int) and colour (int)

Meaning of the return-value:
Did the Function perform well?
*************************************************************************/

ea_bool ea_draw_rectangle (uint32_t, uint32_t, uint32_t, uint32_t, uint32_t);

/*************************************************************************
Function:
Draws an unfilled rectangle

Meaning of the transfer-values:
Lower left corner point (X, int; Y, int), upper right corner point (X, int; Y, int) and colour (int)

Meaning of the return-value:
Did the Function perform well?
*************************************************************************/

ea_bool ea_draw_filled_rectangle (uint32_t, uint32_t, uint32_t, uint32_t, uint32_t);

/*************************************************************************
Function:
Draws a filled rectangle

Meaning of the transfer-values:
lower left corner point (X, int; Y, int), upper right corner point (X, int; Y, int) and colour (int)

Meaning of the return-value:
Did the Function perform well?
*************************************************************************/

ea_bool ea_draw_icon (uint8_t*, int32_t, int32_t, uint32_t, uint32_t, uint32_t);

/*************************************************************************
Function:
Draws an icon which is defined in a two dimensional char array

Meaning of the transfer-values:
A char-array (char*), its dimensions (int, int) and the startpoint (lower left) (X, int; Y, int)
In the char-array have '_' and 'a' - 'o' the meaning of no overlay and 'a' colour '1', 'b' colour '2' and so on
other chars will be ignored respectively filled with no overlay.

EDIT: Ulrich Hornung:
charWidthMod: optional space between characters (negative values also possible)

Meaning of the return-value:
Did the Function perform well?
*************************************************************************/

ea_bool ea_draw_string (uint8_t*, uint32_t, uint32_t, uint32_t, uint32_t,struct glyphs*, int32_t charWidthMod);

/*************************************************************************
Function:
Prints an string

Meaning of the transfer-values:
The string (char*), length (int), start point (lower left) (X, int; Y, int) colour (int) and pointer to Charset

Meaning of the return-value:
Did the Function perform well?
*************************************************************************/

#ifdef USE_FAST_COPY_PASTE
ea_bool ea_copy (uint32_t, uint32_t, uint32_t*, uint32_t, uint32_t, ea_bool);
#else
ea_bool ea_copy (uint32_t, uint32_t, uint8_t*, uint32_t, uint32_t, ea_bool);
#endif

/*************************************************************************
Function:
Copies an area of the overlay into a char array. The char array can be drawn into the overlay
with ea_draw_icon

Meaning of the transfer-values:
Lower left corner (X, int; Y, int), the char-array (char*), its dimensions (int, int)
and a flag for overwriting the overlay in the pasting area with no overlay (ea_bool, true)
or ignore the overlay (ea_bool, false)

Meaning of the return-value:
Did the Function perform well?
*************************************************************************/

ea_bool ea_present();



#ifdef __cplusplus
}
#endif

#endif

