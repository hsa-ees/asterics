/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Module:         as_invert
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Author:         Michael Schaeferling
--
-- Modified:       
--
-- Description:    Driver (source file) for as_invert module
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
 * @file  as_invert.c
 * @brief Driver (source file) for as_invert module.
 */
 
 
#include "as_invert.h"


void as_invert_enable(uint32_t* base_addr, AS_BOOL enable)
{
	if (enable == AS_FALSE)
		as_reg_write_masked( as_module_reg(base_addr, AS_INVERT_STATE_CONTROL_REG_OFFSET), AS_INVERT_STATE_CONTROL_REG_ENABLE_MASK, 0x0);
	else
		as_reg_write_masked( as_module_reg(base_addr, AS_INVERT_STATE_CONTROL_REG_OFFSET), AS_INVERT_STATE_CONTROL_REG_ENABLE_MASK, 0xffffffff);
}


