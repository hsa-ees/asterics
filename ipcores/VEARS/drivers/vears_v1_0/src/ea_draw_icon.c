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
-- File:           ea_draw_icon.c
--
-- Company:        University of Applied Sciences, Augsburg, Germany
--
-- Author:         Tobias Engelhard
-- Date:           29/10/2009
--
-- Modified:       * 09/11/2009 by Tobias Engelhard
--                 * 11/11/2009 by Andreas Becher
--                 * 18/11/2009 by Andreas Becher
--                 * 23/11/2009 by Tobias Engelhard
--                 * 11/12/2009 by Tobias Engelhard
--                 * 20/12/2009 by Tobias Engelhard
--                 * 24/01/2010 by Tobias Engelhard
--                 * 11/02/2010 by Andreas Becher
--                 * 04/06/2019 by Michael Schaeferling
--                 * 12/09/2019 by Michael Schaeferling
--
-- Description:    Draws an icon which is defined in a two dimensional char array.
--------------------------------------------------------------------------------*/


#include "embedded_augmenter_lib.h"
#include "embedded_augmenter_helpers.h"

ea_bool ea_draw_icon(uint8_t *target, int32_t target_x, int32_t target_y, uint32_t point_X, uint32_t point_Y , uint32_t colour)
{
  int32_t i = 0;                          //control variable for y direction
  int32_t ii = 0;                        //control variable for x direction
  uint32_t c_nr = 0;                        //internal colour number
  uint32_t temp_x = 0;                      //temporary variable for x coordinate
  uint32_t temp_y = 0;                      //temporary variable for y coordinate

  uint8_t temp = '_';                          //temporary variable for content of target array

  ea_bool s_flag = ea_true;                          //status flag
  ea_bool status = ea_true;                          //status return value
  ea_bool c_flag = ea_true;                          //colour flag

  if (target_x <= 0 || target_y <= 0 || point_X > WIDTH || point_Y > HEIGHT)
  {
      return ea_false;
  }

  if (colour >= 1 && colour <= (1 << COLOR_DEPTH) - 1)          //Check if colour is in range
  {
      c_nr = colour;                          //set colour variable
      c_flag = ea_true;                          //set colour flag
  }
  else                                  //else
  {
      c_flag = ea_false;                          //set colour flag
  }

  for (i = 0; i < target_y; i++)                    //run through target array in Y direction
  {
    for (ii = 0; ii < target_x; ii++)                  //run through target array in X direction
    {

      temp_x = point_X + ii;                    //jump to position in X direction
      temp_y = point_Y - target_y + i;              //jump to position in Y direction
      temp = *(target + ii + i * target_x);            //set temp to target[x][y]

      if (temp == '_')                        //if target[x][y] = _
      {
        s_flag = ea_draw_point(temp_x, temp_y, 0);        //overwrite with no overlay
        if (s_flag == ea_false)
        {
          status = ea_false;
        }
        else
        {
          status = status;
        }
      }
      else if ((int)(temp - 96) < 0 || (int)(temp - 96) > (1 << COLOR_DEPTH) - 1)    //if target[x][y] is not [a, o]
      {
        ;                            //ignore
      }
      else if (c_flag == ea_true)                    //if status flag is ea_true
      {
        s_flag = ea_draw_point(temp_x, temp_y, c_nr);      //set status flag
        if (s_flag == ea_false)                    //if status flag is ea_false
        {
          status = ea_false;                    //set status return value
        }
        else
        {
          status = status;                  //else: do no alter status return value
        }
      }
      else if (c_flag == ea_false)                    //if flag is ea_false
      {
        c_nr = (int)(temp - 96);                //calculate the right colour value
        s_flag = ea_draw_point(temp_x, temp_y, c_nr);      //write pixel with calculated value and set status flag
        if (s_flag == ea_false)                    //if status flag is ea_false
        {
          status = ea_false;                    //set status return value
        }
        else
        {
          status = status;                  //else: do not alter status return value
        }
      }
    }
  }
  return status;                            //return status
}
