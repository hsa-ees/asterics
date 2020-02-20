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
-- Copyright (C) 2015 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- File:           vears_baseaddr.h
--
-- Company:        University of Applied Sciences, Augsburg, Germany
--
-- Author:         Michael Schaeferling
-- Date:           2015
--
-- Modified:
--
-- Description:    Define the Base-Address of the IP core (as this is
--                 broken in Vivado 2015.4, this can't be done with
--                 xparameters.h).
--------------------------------------------------------------------------------*/


#ifndef VEARS_BASEADDR_H
#define VEARS_BASEADDR_H

#define VEARS_BASEADDR ((uint32_t) 0x43c00000)

#endif // VEARS_BASEADDR_H
