/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Module:         as_gensync
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Alexander Zoellner
--
-- Modified:       
--
-- Description:    Driver (source file) for as_sync module
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
 * @file  as_gensync.c
 * @brief Driver (source file) for as_gensync module.
 */


#include "as_gensync.h"

/* Set line resolution*/
void as_gensync_set_x_res(uint32_t* base_addr, uint32_t value) {
    as_reg_write( as_module_reg( base_addr,AS_GENSYNC_X_RESOLUTION_CONFIG_REG_OFFSET), value);
}

/* Set frame size */
void as_gensync_set_frame_size(uint32_t* base_addr, uint32_t value) {
    as_reg_write( as_module_reg( base_addr,AS_GENSYNC_FRAME_SIZE_CONFIG_REG_OFFSET), value);
}

void as_gensync_init(uint32_t* base_addr) {
    as_gensync_set_x_res(base_addr, AS_GENSYNC_DEFAULT_XRES);
    as_gensync_set_frame_size(base_addr, AS_GENSYNC_DEFAULT_FRAME_SIZE);
}

void as_gensync_enable(uint32_t* base_addr) {
    as_reg_write_masked( as_module_reg( base_addr, AS_GENSYNC_STATE_CONTROL_REG_OFFSET), AS_GENSYNC_STATE_CONTROL_REG_ENABLE_MASK, 0xffffffff);
}

void as_gensync_disable(uint32_t* base_addr) {
    as_reg_write_masked( as_module_reg( base_addr, AS_GENSYNC_STATE_CONTROL_REG_OFFSET), AS_GENSYNC_STATE_CONTROL_REG_ENABLE_MASK, 0x00000000);
}
