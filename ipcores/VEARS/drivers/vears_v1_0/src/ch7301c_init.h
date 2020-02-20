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
--                         and Stefan Durner
----------------------------------------------------------------------------------
-- File:           ch7301c_init.h
--
-- Company:        University of Applied Sciences, Augsburg, Germany
--
-- Author:         Michael Schaeferling, Stefan Durner
-- Date:           06/11/2010
--
-- Modified:       * 12/09/2019 by Michael Schaeferling
--
-- Description:    Driver (header file) for the VEARS IP core.
--                 This file contains functions to configure a Chrontel CH7301C
--                 device to properly output video data provided by VEARS.
--------------------------------------------------------------------------------*/


#ifndef CH7301C_INIT_H
#define CH7301C_INIT_H


#ifdef __cplusplus
extern "C"
{
#endif

void config_decoder_ch7301();

#ifdef __cplusplus
}
#endif

#endif //CH7301C_INIT_H
