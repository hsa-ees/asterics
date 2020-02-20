/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  Copyright (C) Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Module:         as_crop
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Julian Sarcher
--
-- Modified:       
--
-- Description:    Driver (header file) for as_crop module
--                 to set needed parameters.
----------------------------------------------------------------------------------
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
--------------------------------------------------------------------------------*/

/** 
 * @file  as_crop.h
 * @brief Driver (header file) for as_crop module.
 *
 * \defgroup as_crop Module as_crop
 * 
 */


#ifndef AS_CROP_H
#define AS_CROP_H


#include "as_support.h"


/******************* I/O Registers ************************/

/* Internal register definitions */
#define AS_CROP_PARM0_REG_OFFSET            0
#define AS_CROP_PARM1_REG_OFFSET            1


/** \addtogroup as_crop
 *  @{
 */

/******************* Driver functions **********************/

int as_crop_init(uint32_t* base_addr, uint32_t x1, uint32_t y1, uint32_t x2, uint32_t y2);


/** @}*/

#endif /** AS_CROP_H */
