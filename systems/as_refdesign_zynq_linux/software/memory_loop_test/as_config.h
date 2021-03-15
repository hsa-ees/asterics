/*--------------------------------------------------------------------
-- This file is part of the ASTERICS Framework.
-- Copyright (C) Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------
-- File:     as_config.h
--
-- Company:  Efficient Embedded Systems Group
--           University of Applied Sciences, Augsburg, Germany
--           http://ees.hs-augsburg.de
--
-- Author:   Alexander Zoellner
--           Michael Schaeferling <michael.schaeferling@hs-augsburg.de>
-- Date:     
-- Modified: 
--
-- Description:
-- Configuration file for the ASTERICS Support Library
--
----------------------------------------------------------------------
--  This program is free software; you can redistribute it and/or
--  modify it under the terms of the GNU Lesser General Public
--  License as published by the Free Software Foundation; either
--  version 3 of the License, or (at your option) any later version.
--  
--  This program is distributed in the hope that it will be useful,
--  but WITHOUT ANY WARRANTY; without even the implied warranty of
--  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
--  Lesser General Public License for more details.
--  
--  You should have received a copy of the GNU Lesser General Public License
--  along with this program; if not, see <http://www.gnu.org/licenses/>
--  or write to the Free Software Foundation, Inc.,
--  51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
--------------------------------------------------------------------*/

#ifndef _AS_CONFIG_
#define _AS_CONFIG_

extern const char *buildVersion;
extern const char *buildDate;

#define AS_WITH_DEBUG 0

#define AS_BIG_ENDIAN_HW 0
#define AS_BIG_ENDIAN_SW 0
#define AS_BSP_DUMMY 0
#define AS_BSP_XILINX 0
#define AS_BSP_ALTERA 0
#define AS_WITH_MULTIPROCESSING 0
#define AS_OS_NONE 0
#define AS_OS_POSIX 1
#define AS_OS_LINUX_KERNEL 0
#define AS_OS_WINDOWS 0
#define AS_OS_WINDOWS_KERNEL 0
#define AS_HAVE_HEAP 0
#define AS_HAVE_PRINTF 0

#endif
