
/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework.
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Module:         as_canny_pipe
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Author:         Philip Manke
--
-- Modified:
--
-- Description:    Driver (header file) for the canny reference systems canny pipeline.
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
 * @file  as_canny_pipe.h
 * @brief Driver (header file) for the canny reference systems canny pipeline.
 *
 * @addtogroup asterics_modules
 * @{
 *   @defgroup as_canny as_canny: Canny Edge Filter Implementation
 * @}
 * as_canny is a Canny edge filter implementation using the 2D Window Pipeline 
 * architecture generated using Automatics.
 */

#ifndef AS_WINDOW_PIPELINE_COMMON_H
#define AS_WINDOW_PIPELINE_COMMON_H

#include "as_support.h"
#include "as_window_pipeline_common.h"

/// @addtogroup as_canny
/// @{

// Register offsets
#define AS_CANNY_PIPE_THRESHOLD_REG_OFFSET 2
#define AS_CANNY_PIPE_FEATURE_COUNT_REG_OFFSET 4

// Debug selection values
#define AS_CANNY_PIPE_DEBUG_SELECT_ORIG   0x00
#define AS_CANNY_PIPE_DEBUG_SELECT_GAUSS  0x08
#define AS_CANNY_PIPE_DEBUG_SELECT_SOBELX 0x02
#define AS_CANNY_PIPE_DEBUG_SELECT_SOBELY 0x12
#define AS_CANNY_PIPE_DEBUG_SELECT_WEIGHT 0x01
#define AS_CANNY_PIPE_DEBUG_SELECT_NMS    0x21
#define AS_CANNY_PIPE_DEBUG_SELECT_CORDIC 0x05
#define AS_CANNY_PIPE_DEBUG_SELECT_EDGE   0x45


#define AS_CANNY_PIPE_FEATURE_VALUE_WIDTH 11
#define AS_CANNY_PIPE_FEATURE_XCOORD_WIDTH 10
#define AS_CANNY_PIPE_FEATURE_YCOORD_WIDTH 10

#define AS_CANNY_PIPE_FEATURE_MASK_VALUE (0xFFFFFFFF >> (32 - AS_CANNY_PIPE_FEATURE_VALUE_WIDTH))
#define AS_CANNY_PIPE_FEATURE_MASK_XCOORD (0xFFFFFFFF >> (32 - AS_CANNY_PIPE_FEATURE_XCOORD_WIDTH))
#define AS_CANNY_PIPE_FEATURE_MASK_YCOORD (0xFFFFFFFF >> (32 - AS_CANNY_PIPE_FEATURE_YCOORD_WIDTH))

typedef struct canny_feature_struct {
  uint16_t xcoordinate;
  uint16_t ycoordinate;
  uint16_t value;
} canny_feature;

/**
 * Reset the canny pipeline
 * @param base_addr  Address of the canny pipeline to reset
 */
void as_canny_pipe_reset(uint32_t* base_addr);

/**
 * Flush the canny pipeline returning all valid data values buffered
 * @param base_addr  Address of the canny pipeline to flush
 */
void as_canny_pipe_flush(uint32_t* base_addr);


/**
 * Return whether the canny pipeline is ready for operation
 * @param base_addr  Address of the canny pipeline to query
 */
uint32_t as_canny_pipe_is_ready(uint32_t* base_addr);

/**
 * Return the entire state register of the canny pipeline
 * @param base_addr  Address of the canny pipeline to query
 */
uint32_t as_canny_pipe_get_state_reg(uint32_t* base_addr);

/**
 * Return the entire control register of the canny pipeline
 * @param base_addr  Address of the canny pipeline to query
 */
uint32_t as_canny_pipe_get_control_reg(uint32_t* base_addr);

/**
 * Set the Canny thresholds for the canny pipeline
 * @param base_addr  Address of the canny pipeline to access
 * @param high       8 bit high canny threshold 
 * @param low        8 bit low canny threshold
 */
void as_canny_pipe_set_thresholds(uint32_t* base_addr, uint8_t high, uint8_t low);

/**
 * Return the number of canny features found in the last image processed
 * @param base_addr  Address of the canny pipeline to query
 */
uint32_t as_canny_pipe_get_feature_count(uint32_t* base_addr);

/**
 * Decode a raw canny feature returned by the hardware from main memory
 * @param feature_memory Pointer to the memory area where the features to be decoded are located
 * @param feature_number Index number of the feature to be decoded
 * @param feature        Pointer to the canny feature struct where the results are to be stored
 */
void as_canny_pipe_decode_feature(uint32_t* feature_memory, uint32_t feature_number, canny_feature* feature);

/// @} // addtogroup


#endif
