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
-- File:           ea_draw_quick_line_v.c
--
-- Company:        University of Applied Sciences, Augsburg, Germany
--
-- Author:         Christian Hilgers
-- Date:           12/12/2009
--
-- Modified:       * 12/12/2009 by Christian Hilgers
--                 * 24/01/2010 by Tobias Engelhard
--                 * 04/06/2019 by Michael Schaeferling
--                 * 12/09/2019 by Michael Schaeferling
--
-- Description:    Draws quickly a vertical line.
--------------------------------------------------------------------------------*/


#include "embedded_augmenter_lib.h"
#include "embedded_augmenter_helpers.h"

ea_bool ea_draw_quick_line_v(uint32_t x, uint32_t y_start, uint32_t y_end, uint32_t farbe)
{

  uint32_t position = y_start * WIDTH + x;  //Pixelposition
  uint32_t table_position = 0;
  uint32_t offset = 0;
  uint32_t temp = (1 << COLOR_DEPTH) - 1;  //Bitmaske für Farbtiefe
  uint32_t safe = 0;
  uint32_t i = 0;

  table_position = position / (BUS_WIDTH / COLOR_DEPTH);  //Position umgerechnet auf die Pointeradresse
  offset = position - (table_position * (BUS_WIDTH / COLOR_DEPTH));  //Position innerhalb des Speicherblocks
  temp = temp << (((BUS_WIDTH / COLOR_DEPTH) - 1 - offset) * COLOR_DEPTH );  //Maske in Position schieben
  temp = ~temp;  //negieren für und
  safe = temp;

  for (i = 0; i <= (uint32_t) (y_end - y_start); i++)
  {
    temp = temp & overlay_table[table_position];  //Aktuelle werte im Speicherblock zwischenspeichern
    overlay_table[table_position] = temp + (farbe << (((BUS_WIDTH / COLOR_DEPTH) - 1 - offset) * COLOR_DEPTH));  //Aktuellen Farbwert in Position bringen und in den Speicherblock schreiben

    table_position += WIDTH / (BUS_WIDTH/COLOR_DEPTH);
    temp = safe;
  }

  return ea_true;
}
