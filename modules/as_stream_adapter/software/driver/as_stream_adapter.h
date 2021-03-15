/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Module:         as_stream_adapter
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Author:         Michael Schaeferling
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
 * @file  as_stream_adapter.h
 * @brief Driver (header file) for as_stream_adapter module.
 * 
 * \addtogroup asterics_modules
 * @{
 * \defgroup as_stream_adapter as_stream_adapter: As Stream Bit Width Adapter
 * @}
 * This module can be used to adapt the bit width of an as_stream's data signal. 
 * 
 */


#ifndef AS_STREAM_ADAPTER_H
#define AS_STREAM_ADAPTER_H


#include "as_support.h"


/******************* I/O Registers ************************/

// Internal register definitions
#define AS_STREAM_ADAPTER_STATUS_REG_OFFSET 0
#define AS_STREAM_ADAPTER_CONTROL_REG_OFFSET 1
#define AS_STREAM_ADAPTER_STROBE_IN_REG_OFFSET 2
#define AS_STREAM_ADAPTER_STROBE_OUT_REG_OFFSET 3

// Bit offsets
#define AS_STREAM_ADAPTER_STATUS_FULL_OFFSET 0
#define AS_STREAM_ADAPTER_STATUS_EMPTY_OFFSET 1
#define AS_STREAM_ADAPTER_STATUS_COUNTERS_ENABLED_OFFSET 7
#define AS_STREAM_ADAPTER_STATUS_BUFFER_SIZE_OFFSET 8
#define AS_STREAM_ADAPTER_CONTROL_RESET_OFFSET 0
#define AS_STREAM_ADAPTER_CONTROL_COUNTER_RESET_OFFSET 1


#define AS_STREAM_ADAPTER_BUFFER_SIZE_BITWIDTH 24




/** \addtogroup as_stream_adapter
 *  @{
 */

/******************* Driver functions **********************/

/**
 * Reset the as_stream_adapter hardware component.
 * Clears the internal buffer.
 * @param base_addr  The base address of the hardware module
 */
void as_stream_adapter_reset(uint32_t* base_addr);

/**
 * Reset the strobe counters of the component, if enabled.
 * Use 'as_stream_adapter_is_strobe_counting_enabled' 
 * to check if the counters are enabled.
 * @param base_addr  The base address of the hardware module
 */
void as_stream_adapter_strobe_counters_reset(uint32_t* base_addr);

/**
 * Check if the buffer of the hardware component is full.
 * While the buffer is full, previous modules are stalled.
 * @param base_addr  The base address of the hardware module
 * @return AS_TRUE if it is full, AS_FALSE otherwise.
 */
AS_BOOL as_stream_adapter_is_buffer_full(uint32_t* base_addr);

/**
 * Check if the buffer of the hardware component is empty.
 * Important: This function is NOT the opposite of 'as_stream_adapter_is_buffer_full'.
 * While the buffer is empty, no more strobes are generated until more data is received.
 * @param base_addr  The base address of the hardware module
 * @return AS_TRUE if it is empty, AS_FALSE otherwise.
 */
AS_BOOL as_stream_adapter_is_buffer_empty(uint32_t* base_addr);

/**
 * Check if the strobe counter hardware is enabled.
 * To enable the counters, the generic 'GENERATE_STROBE_COUNTERS' of the 
 * hardware module must be set to true in VHDL code or using Automatics.
 * @param base_addr  The base address of the hardware module
 * @return AS_TRUE if it is enabled, AS_FALSE otherwise.
 */
AS_BOOL as_stream_adapter_is_strobe_counting_enabled(uint32_t* base_addr);

/**
 * Provides the automatically configured buffer size for verification.
 * Buffer size is computed as the least common multiple of the input and output data bit width.
 * @param base_addr  The base address of the hardware module
 * @return the buffer size as a uint32_t.
 */
uint32_t as_stream_adapter_get_buffer_size(uint32_t* base_addr);

/**
 * Provides the number of strobes received since the last counter reset.
 * @param base_addr  The base address of the hardware module
 * @return the strobe_in count as a uint32_t.
 */
uint32_t as_stream_adapter_get_strobe_in_count(uint32_t* base_addr);

/**
 * Provides the number of strobes generated since the last counter reset.
 * @param base_addr  The base address of the hardware module
 * @return the strobe_out count as a uint32_t.
 */
uint32_t as_stream_adapter_get_strobe_out_count(uint32_t* base_addr);



/** @}*/

#endif /** AS_STREAM_ADAPTER_H */
