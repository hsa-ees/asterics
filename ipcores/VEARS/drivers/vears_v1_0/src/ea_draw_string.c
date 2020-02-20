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
-- File:           ea_draw_string.c
--
-- Company:        University of Applied Sciences, Augsburg, Germany
--
-- Author:         Tobias Engelhard
-- Date:           29/10/2009
--
-- Modified:       * 23/11/2009 by Tobias Engelhard
--                 * 11/12/2009 by Tobias Engelhard
--                 * 21/12/2009 by Andreas Becher
--                 * 22/12/2009 by Andreas Becher
--                 * 23/12/2009 by Tobias Engelhard
--                 * 24/01/2010 by Tobias Engelhard
--                 * 04/06/2019 by Michael Schaeferling
--                 * 12/09/2019 by Michael Schaeferling
--
-- Description:    Writes a text into the overlay.
--------------------------------------------------------------------------------*/


#include "embedded_augmenter_lib.h"
#include "embedded_augmenter_helpers.h"
#include "embedded_augmenter_font.h"

ea_bool ea_draw_string(uint8_t* target, uint32_t length, uint32_t point_X, uint32_t point_Y, uint32_t color,struct glyphs *ascii, int32_t charWidthMod)
{
  ea_bool returnval = ea_true;
  uint32_t char_pos = 0;
  uint32_t temp=0;
  uint32_t y = 0;
  uint32_t shift = 24;
  uint32_t *char_line = (uint32_t*) ascii + 2;

  shift = 32 - ascii->c_width;
  point_Y -= ascii->c_height;

  if (point_X < X_LEFT || point_X > X_RIGHT)
    return ea_false;

  if ( point_Y > Y_LOW || point_Y < Y_HIGH)
    return ea_false;

  for (char_pos = 0 ; char_pos< length;char_pos++) // Loop over Charcount
  {
    for (y=0; y < (uint32_t) ascii->c_height;y++) // Loop every Line on Char
    {
      //temp = ascii->chars[target[char_pos]-32][y]; //aus der Tabelle auslesen

      temp = (uint32_t) *(char_line + (target[char_pos] -32) * ascii->c_height  + y);
      temp = temp << shift;// evtl verschieben
      returnval &= ea_draw_int( point_X,point_Y+y,temp,color);
    }
    point_X += ascii->c_width + charWidthMod; //n?chster buchstabe
  }
  return returnval;
}

ea_bool ea_draw_int(uint32_t x, uint32_t y, uint32_t muster, uint32_t color)
{
  ea_bool returnval= ea_true;
  uint32_t temp=0;
  uint32_t int_cnt = 0;
  uint32_t color_cnt = 0;
  uint32_t value = 0;
  uint32_t rest = 0;
  uint32_t rpos =x+y*WIDTH; //real position
  uint32_t pos = rpos/ ( PIXEL_PER_INT); //table pos
  uint32_t shift = (rpos%(PIXEL_PER_INT));
  uint32_t xl_off = shift * COLOR_DEPTH;
  uint32_t xr_off = BUS_WIDTH;

  if ( y > Y_LOW || y < Y_HIGH) return ea_false;  //Check Y-Direction
  if ( x > X_RIGHT) return ea_false; //Check X_RIGHT-Direction nichts mehr zu tun
  if ( x < X_LEFT )                           //Check X_LEFT-Direction
  {
      xl_off = (X_LEFT -x)*COLOR_DEPTH;
      if (xl_off > BUS_WIDTH)
          return ea_false; //nichts mehr zu tun
      returnval = ea_false;
  }

  rest = muster & ((1<<shift)-1); // get rest
  rest = ((rest <<(PIXEL_PER_INT))>> shift); //bring rest to right position
  muster >>=shift; //shift muster

  for (int_cnt = 0 ; int_cnt <= COLOR_DEPTH ; int_cnt++)
  {
      temp = 0; //zuruecksetzen fuer neues Pixel
      if (muster == 0) return returnval; //Cancel if nothing to do
      for (color_cnt = xl_off; color_cnt <  xr_off ;color_cnt+= COLOR_DEPTH) // 0 - 1 bei 2 bit
      {

          #if COLOR_DEPTH == 2
          temp |= (0x80000000  & (muster<< (color_cnt / 2))) >> (color_cnt);
          temp |= (0x80000000  & (muster<< (color_cnt / 2))) >> (color_cnt | 1);
          #else

          for ( bit_cnt = 0 ; bit_cnt < COLOR_DEPTH ; bit_cnt ++)
              temp |= (0x80000000  & (muster<< (color_cnt / COLOR_DEPTH))) >> (color_cnt | bit_cnt);
          #endif
      }
      value = overlay_table[pos + int_cnt] & ~temp; //Read existing Overlay
      overlay_table[pos + int_cnt] = value | (temp & mask[color]); //Write muster

      muster <<= (PIXEL_PER_INT);
      muster |=rest;
      rest=0;
      xl_off = 0; //zur�ckstellen damit der rest gedruckt werden kann
  }


  return returnval;
}





/*
ea_bool ea_draw_string(char* target, int length, int point_X, int point_Y, int color,struct glyphs *ascii)
{

	uint32_t i = 0;															//control variable for input string
	uint32_t ii = 0;														//control variable for glyph's height

	uint32_t j = 0;															//control variable for glyph's width
	uint32_t place = 0;														//variable for place of glyph in glyph-database
	uint32_t temp1 = 0;														//temporary variable for line in glyph's height
	uint32_t temp2 = 0;														//temporary variable for outmasked bit
	uint32_t shift = 1 << ascii->c_width;											//variable for outmasking bits

	uint32_t temp_point_X = point_X;										//variable for x coordinate of base-point of the glyph
	uint32_t temp_point_Y = point_Y;										//variable for y coordinate of base-point of the glyph

	char temp_letter = ' ';														//temporary variable for character in input string
	char temp_array[ (ascii->c_height)][ ascii->c_width];											//temporary array for handover to ea_draw_icon

	ea_bool status = ea_true;															//status for return value
	ea_bool s_flag = ea_true;															//status flag

	if (length <= 0) {															//check if transfered string-lengh <= 0:
		return ea_false;															//cancel
	}

	if (color < 0 || color > (1 << COLOR_DEPTH) - 1) {							//Check if colour is in range
		color = 1;																//set colour to first colour
	}

	for (i = 0; i < length; i++) {												//run through string
		temp_letter = *(target + i);											//set temp_letter to target[i]
		place = (int)(temp_letter - 32);										//compute place of temp_letter in the glyph-database

		for (ii = 0; ii < ascii->c_height; ii++) {										//run through glyph in y direction
			temp1 = (int) ascii->chars[place][ii];									//set temp to ii'th line in glyph[place]

			for (j = 0; j < ascii->c_width; j++) {										//run through glyph's width
				temp2 = temp1 & shift;											//mask all bits out execpt that bit on place F_WIDTH
				if (temp2 == 0) {												//check if temp2 is 0
					temp_array[ii][j] = '.';									//write in temp_array background
				}
				else {															//else
					temp_array[ii][j] = 'a';									//write in temp_array colour
				}
				temp1 = temp1 << 1;												//shift temp1 one left
			}
		}

		s_flag = ea_draw_icon(*temp_array, ascii->c_width, ascii->c_height, temp_point_X, temp_point_Y, color);
																				//write glyph in overlay
		temp_point_X += ascii->c_width + 3;											//set base-point of next letter to temp_point_X + F_WIDTH + 1

		if (s_flag == ea_false) {													//check if ea_draw_icon was not successful
			status = ea_false;														//overwrite status
		}
	}
	return status;																//return status
}
*/

