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
-- Description:    Driver (source file) for as_crop module
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
 * @file  as_crop.c
 * @brief Driver (source file) for as_crop module.
 */


#include "as_crop.h"


int as_crop_init(uint32_t* base_addr, uint32_t x1, uint32_t y1, uint32_t x2, uint32_t y2)
{
    uint32_t x1i = x1-1;
    uint32_t y1i = y1-1;
    uint32_t x2i = x2-1;
    uint32_t y2i = y2-1;

    if ((x1i > x2i) || (y1i > y2i)){
        return -1;
    } else {
        as_reg_write(as_module_reg(base_addr, AS_CROP_PARM0_REG_OFFSET), (x1i << 16) | y1i);
        as_reg_write(as_module_reg(base_addr, AS_CROP_PARM1_REG_OFFSET), (x2i << 16) | y2i);
        return 0;
    }
}

