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
-- File:           ea_draw_line.c
--
-- Company:        University of Applied Sciences, Augsburg, Germany
--
-- Author:         Christian Hilgers
-- Date:           08/11/2009
--
-- Modified:       * 01/01/2010 by Christian Hilgers
--                 * 24/01/2010 by Tobias Engelhard
--                 * 04/06/2019 by Michael Schaeferling
--                 * 12/09/2019 by Michael Schaeferling
--
-- Description:    Draws a line from one point to the other.
--------------------------------------------------------------------------------*/


#include "embedded_augmenter_lib.h"
#include "embedded_augmenter_helpers.h"

/*************************************************************************
sgn
Called by ea_draw_line
Function: returns sign (-1,0,1)
Important: -
************************************************************************/

int8_t sgn (int32_t X)
{
  if (X > 0) {
    return 1;
  }
  else if (X < 0)
  {
    return -1;
  }
  return 0;
}

/*************************************************************************
abs
Called by ea_draw_line
Function: returns value without sign
Important: -
************************************************************************/

uint32_t abs (int32_t X)
{
  if (X >= 0) {
    return X;
  }
  else {
    X = -X;
    return X;
  }
}


ea_bool ea_draw_line (uint32_t x_start, uint32_t y_start, uint32_t x_end, uint32_t y_end, uint32_t color)
{
  uint32_t i = 0;

  uint32_t dX = x_end - x_start;
  uint32_t dY = y_end - y_start;

  uint32_t x_recent = 0;
  uint32_t y_recent = 0;

  //step size (parallel)
  uint32_t step_parX = 0;
  uint32_t step_parY = 0;

  //step size (diagonal)
  uint32_t step_diagX = sgn(dX);
  uint32_t step_diagY = sgn(dY);

  //values for correcting the error term
  uint32_t step_error_neg = 0;
  uint32_t step_error_pos = 0;

  //error term
  int32_t error = 0;

  ea_bool returnvalue = ea_true;


  //calling the quick_line_vertical - function if necessary
  if (x_start == x_end)
  {
    //swap values if necessary
    if (y_start > y_end)
    {
      y_start ^= y_end;
      y_end ^= y_start;
      y_start ^= y_end;
    }

    if (ea_draw_quick_line_v(x_start, y_start, y_end, color) == ea_true)
      return ea_true;
    else return ea_false;
  }

  //calling the quick_line_horizontal - function if necessary
  if (y_start == y_end)
  {
    //swap values if necessary
    if (x_start > x_end)
    {
      x_start ^= x_end;
      x_end ^= x_start;
      x_start ^= x_end;
    }

    if (ea_draw_quick_line_h(x_start, x_end, y_end, color) == ea_true)
      return ea_true;
    else return ea_false;
  }

  //starting point to the left of clipped area?
  if (x_start < X_LEFT)
  {
    y_start += (dY*(X_LEFT - x_start))/dX;
    x_start = X_LEFT;

    returnvalue = ea_false;
  }

  //starting point to the right of clipped area?
  if (x_start > X_RIGHT)
  {
    y_start += (dY*(x_start - X_RIGHT))/dX;
    x_start = X_RIGHT;

    returnvalue = ea_false;
  }

  //starting point above clipped area?
  if (y_start < Y_HIGH)
  {
    x_start += (dX*(Y_HIGH - y_start))/dY;
    y_start = Y_HIGH;

    returnvalue = ea_false;
  }

  //starting point below clipped area?
  if (y_start > Y_LOW)
  {
    x_start += (dX*(y_start - Y_LOW))/dY;
    y_start = Y_LOW;

    returnvalue = ea_false;
  }

  // -1 < gradient < 1
  if (abs(dX) > abs(dY))
  {
    //set step size (parallel)
    step_parX = sgn(dX);
    step_parY = 0;

    //set values for correcting the error term
    step_error_neg = abs(dY);
    step_error_pos = abs(dX);
  }

  // gradient <= -1 or gradient >= 1
  else
  {
    //set step size (parallel)
    step_parX=0;
    step_parY=sgn(dY);

    //set values for correcting the error term
    step_error_neg =abs(dX);
    step_error_pos =abs(dY);
  }

  //initialize the error term
  error = step_error_pos / 2;

  //set starting point
  x_recent = x_start;
  y_recent = y_start;

  //draw starting point
  ea_draw_point(x_start, y_start, color);

  for(i = 1; i <= step_error_pos; i++)
  {
    //correcting error term
    error -= step_error_neg;

    if(error < 0)
    {
      //correcting error term
      error += step_error_pos;

      //one step diagonal
      x_recent += step_diagX;
      y_recent += step_diagY;
    }
    else
    {
      //one step parallel
      x_recent += step_parX;
      y_recent += step_parY;
    }

    //draw point
    if (ea_draw_point(x_recent, y_recent, color) == ea_false)
      return ea_false;
  }
  return returnvalue;
}
