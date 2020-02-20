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
-- File:           ea_draw_point.c
--
-- Company:        University of Applied Sciences, Augsburg, Germany
--
-- Author:         Tobias Engelhard
-- Date:           29/10/2009
--
-- Modified:       * 02/11/2009 by Andreas Becher
--                 * 09/11/2009 by Andreas Becher
--                 * 24/01/2010 by Tobias Engelhard
--                 * 04/06/2019 by Michael Schaeferling
--                 * 12/09/2019 by Michael Schaeferling
--
-- Description:    Draws a point into the overlay.
--------------------------------------------------------------------------------*/


#include "embedded_augmenter_lib.h"
#include "embedded_augmenter_helpers.h"

ea_bool ea_draw_point(uint32_t X, uint32_t Y, uint32_t farbe)
{

  uint32_t position = Y * WIDTH + X;        //Absolute Position of the Pixel to draw
  uint32_t table_position = 0;              //Variable to hold the position of the Pixel in the Overlaytable
  uint32_t offset = 0;                      //Offset in the Overlaytableposition
  uint32_t temp = (1 << COLOR_DEPTH) - 1;   //Mask for Colordepht

  if (X_LEFT  > X || X > X_RIGHT) {         //Check if Pixel is in clipped Area, Horizontal
    return ea_false;
  }

  if (Y_HIGH > Y || Y > Y_LOW) {            //Check if Pixel is in clipped Area, Vertical
    return ea_false;
  }

  if (farbe > (1 << COLOR_DEPTH) - 1) {     //Check if Color is a available value
    return ea_false;
  }

  table_position = position / (BUS_WIDTH / COLOR_DEPTH);        //Calcs the absolute Position of the ColorTable
  offset = position % (BUS_WIDTH / COLOR_DEPTH);  //Calcs the Position in the ColorTableposition


  temp = temp << (((BUS_WIDTH / COLOR_DEPTH) - 1 - offset) * COLOR_DEPTH );  //Shifts the mask to its desired position

  temp = ~temp;                            //negates the mask

  temp = temp & overlay_table[table_position];            //saves the actual Pixels found in the ColorTable and masks the desired out

  overlay_table[table_position] = temp | (farbe << (((BUS_WIDTH/COLOR_DEPTH) - 1 - offset) * COLOR_DEPTH));  //writes the Pixel with its ColorValue and the actual Pixels in the ColorTable

  return ea_true;
}
