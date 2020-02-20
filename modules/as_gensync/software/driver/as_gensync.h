/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  Copyright (C) Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Module:         as_gensync
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Alexander Zoellner
--
-- Modified:       
--
-- Description:    Driver (header file) for as_sync module
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
 * @file  as_gensync.h
 * @brief Driver (header file) for as_gensync module.
 *
 * \defgroup as_gensync Module as_gensync
 * 
 */


#ifndef AS_GENSYNC_H
#define AS_GENSYNC_H


#include "as_support.h"


/* Line length of 640 pixel */
#define AS_GENSYNC_DEFAULT_XRES                 640
/* Frame size for a 640*480 pixel resolution */
#define AS_GENSYNC_DEFAULT_FRAME_SIZE           307200


/******************* I/O Registers ************************/

// Internal register definitions
#define AS_GENSYNC_STATE_CONTROL_REG_OFFSET         0
#define AS_GENSYNC_X_RESOLUTION_CONFIG_REG_OFFSET   1
#define AS_GENSYNC_FRAME_SIZE_CONFIG_REG_OFFSET     2

/* Bit offsets */
#define AS_GENSYNC_STATE_CONTROL_REG_ENABLE_BIT_OFFSET  16

/* Bit masks */
#define AS_GENSYNC_STATE_CONTROL_REG_ENABLE_MASK        (1<<AS_GENSYNC_STATE_CONTROL_REG_ENABLE_BIT_OFFSET)


/** \addtogroup as_gensync
 *  @{
 */

/******************* Driver functions **********************/

/* Register Write Functions */
void as_gensync_set_x_res(uint32_t* base_addr, uint32_t value);
void as_gensync_set_frame_size(uint32_t* base_addr, uint32_t value);

void as_gensync_init(uint32_t* base_addr);

/* Control Register Write Functions */
void as_gensync_enable(uint32_t* base_addr);
void as_gensync_disable(uint32_t* base_addr);


/** @}*/

#endif /** AS_GENSYNC_H */
