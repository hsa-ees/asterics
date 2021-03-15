/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework.
--  (C) 2021 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Module:         as_stream_adapter
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Author:         Philip Manke
--
-- Modified:
--
-- Description:    Driver (header file) for as_stream_adapter module
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
 * @file  as_stream_strobe_counter.h
 * @brief Driver (header file) for as_stream_strobe_counter module.
 *
 * \addtogroup asterics_modules
 * @{
 * \defgroup as_stream_strobe_counter as_stream_strobe_counter: As Stream Debug
 * Module
 * @}
 * This module counts the number of strobe signals send through an AsStream
 * interface.
 *
 */

#ifndef AS_STREAM_STROBE_COUNTER_H
#define AS_STREAM_STROBE_COUNTER_H

#include "as_support.h"

/******************* I/O Registers ************************/

// Internal register definitions
#define AS_STREAM_STROBE_COUNTER_STATUS_REG_OFFSET 0
#define AS_STREAM_STROBE_COUNTER_CONTROL_REG_OFFSET 1

// Bit offsets
#define AS_STREAM_STROBE_COUNTER_CONTROL_RESET_OFFSET 0
#define AS_STREAM_STROBE_COUNTER_CONTROL_ENABLE_OFFSET 1

/** \addtogroup as_stream_strobe_counter
 *  @{
 */

/******************* Driver functions **********************/

/**
 * @ brief Reset the strobe counter to zero.
 * @param base_addr  The base address of the hardware module
 */
void as_stream_strobe_counter_reset(uint32_t *base_addr);

/**
 * @brief Enable counting of the strobe signal.
 * @param base_addr  The base address of the hardware module
 */
void as_stream_strobe_counter_strobe_enable(uint32_t *base_addr);

/**
 * @brief Disable counting of the strobe signal.
 * @param base_addr  The base address of the hardware module
 */
void as_stream_strobe_counter_strobe_disable(uint32_t *base_addr);

/**
 * @brief Retrieve the current strobe counter value.
 * @param base_addr  The base address of the hardware module
 * @return The current counter value.
 */
uint32_t as_stream_strobe_counter_get_count_value(uint32_t *base_addr);

/** @}*/

#endif /** AS_STREAM_STROBE_COUNTER_H */
