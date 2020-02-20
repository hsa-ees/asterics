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
-- File:           ea_draw_filled_circle.c
--
-- Company:        University of Applied Sciences, Augsburg, Germany
--
-- Author:         Christian Hilgers
-- Date:           08/11/2009
--
-- Modified:       * 02/01/2010 by Christian Hilgers
--                 * 04/06/2019 by Michael Schaeferling
--                 * 12/09/2019 by Michael Schaeferling
--
-- Description:    Draws a filled circle.
--------------------------------------------------------------------------------*/


#include "embedded_augmenter_lib.h"
#include "embedded_augmenter_helpers.h"

ea_bool ea_draw_filled_circle (uint32_t x0, uint32_t y0, uint32_t radius, uint32_t color)
{
  int32_t x_recent = radius;
  int32_t y_recent = 0;
  int32_t error = radius;
  int32_t dx = 0;
  int32_t dy = 0;

  ea_bool new_value = ea_false;                        //flag ea_true if x_recent changed
  ea_bool returnvalue = ea_true;

  if (ea_draw_quick_line_h(x0 - radius, x0 + radius, y0, color) == ea_false) {  //draw horizontal center line
    returnvalue = ea_false;
  }

  while (y_recent < x_recent)
  {
    dy = y_recent * 2 + 1;                      //calculate error step
    y_recent++;
    error -= dy;                          //correcting error term

    if (error < 0)
    {
       dx = 1 - x_recent * 2;                    //calculate error step
       x_recent--;
       error -= dx;                          //correcting error term
       new_value = ea_true;                      //set flag (x_recent changed)
    }


    if (ea_draw_quick_line_h(x0 - x_recent, x0 + x_recent, y0 + y_recent, color) == ea_false) {  //draw first slice (positive direction)
      returnvalue = ea_false;
    }
    if (ea_draw_quick_line_h(x0 - x_recent, x0 + x_recent, y0 - y_recent, color) == ea_false) {  //draw first slice (negative direction)
      returnvalue = ea_false;
    }
    if (new_value == ea_true)                      //if x_recent changed
    {
      if (ea_draw_quick_line_h(x0 - y_recent, x0 + y_recent, y0 + x_recent, color) == ea_false) {  //draw second slice (positive direction)
        returnvalue = ea_false;
      }
      if (ea_draw_quick_line_h(x0 - y_recent, x0 + y_recent, y0 - x_recent, color) == ea_false) {  //draw second slice (negative direction)
        returnvalue = ea_false;
      }
      new_value = ea_false;                      //correct flag
    }
  }
  return returnvalue;
}
