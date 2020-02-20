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
-- Copyright (C) 2010 Andreas Becher
----------------------------------------------------------------------------------
-- File:           embedded_augmenter_font.h
--
-- Company:        University of Applied Sciences, Augsburg, Germany
--
-- Author:         Andreas Becher
-- Date:           24/01/2010
--
-- Modified:       * 2010 by Andreas Becher
--
-- Description:    Provides fonts.
--------------------------------------------------------------------------------*/

// Glyph converted from Font: Bitstream Vera Sans Size: 18
// Converter: Font Converter written by A.Becher

#ifndef EMBEDDED_AUGMENTER_FONT_H_INCLUDED
#define EMBEDDED_AUGMENTER_FONT_H_INCLUDED
struct glyphs{
int c_width;
int c_height;
unsigned int chars[95][34];
};



extern struct glyphs std_glyph;
extern struct glyphs tit_glyph;

/*****************************/
// Glyph converted from Font: Verdana
// Converter: Font Converterwritten by A.Becher

//#define F_WIDTH 31					//Zeichenbreite
//#define F_HEIGHT 28					//Zeichenhoehe

//extern unsigned int tglyphs[95][F_HEIGHT];
/*struct tglyphs{
int c_width;
int c_height;
unsigned int chars[95][28];
};

extern struct tglyphs tit_glyph;
*/

#endif //EMBEDDED_AUGMENTER_FONT_H_INCLUDED
