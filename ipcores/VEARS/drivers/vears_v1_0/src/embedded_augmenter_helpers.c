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
-- Copyright (C) 2010-2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- File:           embedded_augmenter_font.h
--
-- Company:        University of Applied Sciences, Augsburg, Germany
--
-- Author:         Michael Schaeferling
-- Date:           2010
--
-- Modified:       * 04/06/2019 by Michael Schaeferling
--                 * 12/09/2019 by Michael Schaeferling
--
-- Description:    Provides fonts.
--------------------------------------------------------------------------------*/

#include "embedded_augmenter_helpers.h"

uint32_t X_LEFT;   // left  border of the overlay
uint32_t Y_HIGH;   // upper border of the overlay
uint32_t X_RIGHT;  // right border of the overlay
uint32_t Y_LOW;    // lower border of the overlay


uint32_t* hardware_overlay_address;  // pointer to hardware processing overlay
uint32_t* overlay_table;
uint32_t* mask;
