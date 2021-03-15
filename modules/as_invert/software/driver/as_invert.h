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
-- Description:    Driver (header file) for as_invert module
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
 * @file  as_invert.h
 * @brief Driver (header file) for as_invert module.
 *
 * @addtogroup asterics_modules
 * @{
 * \defgroup as_invert as_invert: Pixel Value Inverter
 * @}
 *
 * This module can be used to invert (logical 'not') the image data stream.
 *
 */

#ifndef AS_INVERT_H
#define AS_INVERT_H

#include "as_support.h"

/******************* I/O Registers ************************/

/* Internal register definitions */
#define AS_INVERT_STATE_CONTROL_REG_OFFSET 0

/* Bit offsets */
#define AS_INVERT_STATE_CONTROL_REG_ENABLE_BIT_OFFSET 17
/* Bit masks */
#define AS_INVERT_STATE_CONTROL_REG_ENABLE_MASK (1 << AS_INVERT_STATE_CONTROL_REG_ENABLE_BIT_OFFSET)

/** \addtogroup as_invert
 *  @{
 */

/******************* Driver functions **********************/

/**
 * Enable/disable inversion (logical 'not') of the image data stream.
 *
 * @param base_addr             Address of the corresponding hardware
 *                              module (see also as_hardware.h)
 * @param enable                Enable ('AS_TRUE') or disable ('AS_FALSE')
 *                              the inversion of the image data stream.
 */
void as_invert_enable(as_hardware_address_t base_addr, AS_BOOL enable);

/** @}*/

#endif /** AS_INVERT_H */
