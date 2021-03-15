
/*------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework.
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
--------------------------------------------------------------------------------
-- File:           asterics.h
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Author:         ASTERICS Automatics
--
-- Description:    Driver (header file) for the ASTERICS IP core.
--                 This header file
--                  a) incorporates drivers of implemented ASTERICS modules and
--                  b) defines register mapping for low level hardware access.
--------------------------------------------------------------------------------
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
------------------------------------------------------------------------------*/

/**
 * @file  asterics.h
 * @brief Incorporating drivers for ASTERICS IP core modules and register mapping definition.
 *
 * \defgroup asterics_mod ASTERICS modules
 *
 */

#ifndef ASTERICS_H
#define ASTERICS_H

#ifdef __cplusplus
extern "C"
{
#endif

#include "as_support.h"


/************************** Integrated Modules ***************************/

#include "as_reader_writer.h" 
#include "as_reader_writer.h" 


/************************** ASTERICS IP-Core Base Address ***************************/
#define ASTERICS_BASEADDR 0X43C10000

#define AS_REGISTERS_PER_MODULE 16

/************************** Module Register Mapping ***************************/

#define AS_MODULE_BASEREG_READER0 0
#define AS_MODULE_BASEREG_AS_INVERT_0 1
#define AS_MODULE_BASEREG_WRITER0 2


/************************** Module Address Mapping ***************************/

#define AS_MODULE_BASEADDR_READER0 ((ASTERICS_BASEADDR + (AS_MODULE_BASEREG_READER0 * 4 * AS_REGISTERS_PER_MODULE)))
#define AS_MODULE_BASEADDR_AS_INVERT_0 ((ASTERICS_BASEADDR + (AS_MODULE_BASEREG_AS_INVERT_0 * 4 * AS_REGISTERS_PER_MODULE)))
#define AS_MODULE_BASEADDR_WRITER0 ((ASTERICS_BASEADDR + (AS_MODULE_BASEREG_WRITER0 * 4 * AS_REGISTERS_PER_MODULE)))



/************************** Module Defines and Additions ***************************/



#ifdef __cplusplus
}
#endif

#endif /** ASTERICS_H */
