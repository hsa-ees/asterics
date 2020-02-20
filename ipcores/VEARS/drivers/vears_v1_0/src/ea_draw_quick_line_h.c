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
-- File:           ea_draw_quick_line_h.c
--
-- Company:        University of Applied Sciences, Augsburg, Germany
--
-- Author:         Christian Hilgers and Moritz Lessmann
-- Date:           01/12/2009
--
-- Modified:       * 16/12/2009 by Christian Hilgers and Moritz Lessmann
--                 * 24/01/2010 by Tobias Engelhard
--                 * 10/02/2010 by Andreas Becher
--                 * 04/06/2019 by Michael Schaeferling
--                 * 12/09/2019 by Michael Schaeferling
--
-- Description:    Draws quickly a horizontal line.
--------------------------------------------------------------------------------*/


#include "embedded_augmenter_lib.h"
#include "embedded_augmenter_helpers.h"

uint32_t get_mask(uint32_t hp, uint32_t lp, uint32_t color)
{
  uint32_t value=0;
  if (color != 0)
  {
    hp = (PIXEL_PER_INT)-1-(hp-lp);
    value = mask[color];
    value >>= (hp*COLOR_DEPTH);
    value <<= (lp*COLOR_DEPTH);
  } 
  else {
    value = 0;
  }
  
  return value;
}

ea_bool ea_draw_quick_line_h(uint32_t x_start, uint32_t x_end, uint32_t y, uint32_t color)
{
  uint32_t mask_val = 0;

  uint32_t position_start = 0;
  uint32_t position_end = 0;
  uint32_t table_position_start = 0;
  uint32_t table_position_end = 0;
  uint32_t temp = 0;
  uint32_t max_pos = BUS_WIDTH/COLOR_DEPTH-1;

  int i = 0;

  ea_bool returnvalue = ea_true;
  //Abfragen fuer sichtbaren Bereich

  if (X_LEFT  > x_start)
  {
      x_start = X_LEFT;
      returnvalue = ea_false;
  }

  if (X_RIGHT  < x_end)
  {
      x_end = X_RIGHT;
      returnvalue = ea_false;
  }

  if (X_RIGHT  < x_start || X_LEFT > x_end)
  {
      return ea_false;
  }

  if (Y_HIGH > y || y > Y_LOW)
  {
      return ea_false;
  }

  if (color > (1 << COLOR_DEPTH)-1)
  {
      return ea_false;
  }

  position_start = y * WIDTH + x_start;  //Pixelnummer Start
  position_end = y * WIDTH + x_end;  //Pixelnummer End
  table_position_start = position_start / (BUS_WIDTH / COLOR_DEPTH);  //Position umgerechnet auf die Pointeradresse
  table_position_end = position_end / (BUS_WIDTH / COLOR_DEPTH);  //Position umgerechnet auf die Pointeradresse

  position_start %= (BUS_WIDTH / COLOR_DEPTH);
  position_start = (BUS_WIDTH / COLOR_DEPTH)-position_start-1;
  position_end %= (BUS_WIDTH / COLOR_DEPTH);
  position_end = (BUS_WIDTH / COLOR_DEPTH)-position_end-1;

  if (table_position_end != table_position_start)
  {
    //left
    if (position_start < max_pos)
    {
      mask_val = get_mask(position_start,0,(1<<COLOR_DEPTH)-1);
      temp = overlay_table[table_position_start] & ~mask_val;
      overlay_table[table_position_start] = temp | get_mask(position_start,0,color);
      table_position_start++;
    }

    //right
    if ( position_end > 0)
    {
      mask_val = get_mask(max_pos,position_end,(1<<COLOR_DEPTH)-1);
      temp = overlay_table[table_position_end] & ~mask_val;
      overlay_table[table_position_end] = temp | get_mask(max_pos,position_end,color);
      table_position_end--;
    }

    //between
    if (table_position_end-table_position_start+1>0)
    {
      temp = get_mask(max_pos,0,color);
      for (i=0; i <= (int) (table_position_end - table_position_start); i++)  //Registerschleife
        overlay_table[table_position_start + i] = temp;  //Farbwerte in Position bringen und in den Speicherblock schreiben
    }
  }

  else
  {
    mask_val = get_mask(position_start,position_end,(1<<COLOR_DEPTH)-1);
    temp = overlay_table[table_position_start] & ~mask_val;
    overlay_table[table_position_start] = temp | get_mask(position_start,position_end,color);
  }

  return returnvalue;
}
