/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework.
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Module:         as_window_pipeline_common
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Author:         Philip Manke
--
-- Modified:
--
-- Description:    Generic driver (header file) for window pipeline modules.
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
 * @file  as_window_pipeline_common.h
 * @brief Generic driver (header file) for window pipeline modules.
 * \addtogroup asterics_modules
 * @{
 *   \defgroup as_window_pipeline_common as_window_pipeline_common: 2D Window Pipeline Generic Driver
 * @}
 *
 * This driver implements functionality available with all 2D Window Pipelines
 * generated by Automatics and is always included with such systems.
 * Additional functionality implemented in hardware must be implemented in software
 * by the developers as needed.
 */

#ifndef AS_WINDOW_PIPELINE_COMMON_H
#define AS_WINDOW_PIPELINE_COMMON_H

#include "as_support.h"

/** \addtogroup as_window_pipeline_common
 *  @{
 */
 
#define AS_WINDOW_PIPELINE_COMMON_STATUS_REG_OFFSET 1
#define AS_WINDOW_PIPELINE_COMMON_CONTROL_REG_OFFSET 0

/**
 * Reset the pipeline, clearing controller state.
 * Does not clear image data from buffers.
 * @param base_addr  The base address of the hardware module
 */
void as_window_pipe_reset(uint32_t* base_addr);

/**
 * Flush the pipeline. 
 * Invalid flush-data is inserted at the pipeline's input 
 * until all buffers are empty of valid data.
 * @param base_addr  The base address of the hardware module
 */
void as_window_pipe_flush(uint32_t* base_addr);

/**
 * Check if the pipeline is in a ready state (All buffers empty).
 * @param base_addr  The base address of the hardware module
 * @return AS_TRUE if pipeline is ready, else AS_FALSE
 */
uint8_t is_as_window_pipe_ready(uint32_t* base_addr);


/**
 * Read the contents of the pipeline's state register.
 * @param base_addr  The base address of the hardware module
 * @return Data stored in the state register (uint32)
 */
uint32_t as_window_pipe_get_state_reg(uint32_t* base_addr);

/**
 * Read the contents of the pipeline's control register.
 * @param base_addr  The base address of the hardware module
 * @return Data stored in the control register (uint32)
 */
uint32_t as_window_pipe_get_control_reg(uint32_t* base_addr);

/** @}*/

#endif /*AS_WINDOW_PIPELINE_COMMON_H*/