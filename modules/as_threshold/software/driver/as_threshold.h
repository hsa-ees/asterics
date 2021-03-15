/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Module:         as_threshold
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Michael Schaeferling
--
-- Modified:       
--
-- Description:    Driver (header file) for as_threshold module
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
 * @file  as_threshold.h
 * @brief Driver (header file) for as_threshold module.
 * \addtogroup asterics_modules
 * @{
 * \defgroup as_threshold as_threshold: Two-Value Thresholding
 * @}
 * This module thresholds image data by taking two threshold values into account. 
 * 
 * The lower threshold t1 and the upper threshold t2 separate the occuring image data values into 3 ranges:
 *   - a) below lower threshold t1: [a] := [image_data < t1]
 *   - b) between lower threshold t1 and upper threshold t2: [b] := [t1 >= image_data <= t2]
 *   - c) above upper threshold t2: [c] := [image_data > t2]
 * 
 * For each range [a], [b] and [c], it can be specified whether original image data or a fixed, user determined value is to be output.
 * 
 */
 

#ifndef AS_THRESHOLD_H
#define AS_THRESHOLD_H


#include "as_support.h"


/******************* I/O Registers ************************/

/* Internal register definitions */
#define AS_THRESHOLD_PARAMETER_1_REG_OFFSET 0
#define AS_THRESHOLD_PARAMETER_2_REG_OFFSET 1

/* Bit offsets */
#define AS_THRESHOLD_ENABLE_A_VALUE_BIT_OFFSET  28
#define AS_THRESHOLD_ENABLE_B_VALUE_BIT_OFFSET  29
#define AS_THRESHOLD_ENABLE_C_VALUE_BIT_OFFSET  30
/* Bit masks */
#define AS_THRESHOLD_ENABLE_A_VALUE_BIT_MASK         (1<<AS_THRESHOLD_ENABLE_A_VALUE_BIT_OFFSET)
#define AS_THRESHOLD_ENABLE_B_VALUE_BIT_MASK         (1<<AS_THRESHOLD_ENABLE_B_VALUE_BIT_OFFSET)
#define AS_THRESHOLD_ENABLE_C_VALUE_BIT_MASK         (1<<AS_THRESHOLD_ENABLE_C_VALUE_BIT_OFFSET)


/** \addtogroup as_threshold
 *  @{
 */

/******************* Driver functions **********************/

/**
 * Get the t1 value set in the module.
 * 
 * @param base_addr             Address of the corresponding hardware 
 *                              module (see also as_hardware.h)
 * @return                      The return value is the t1 value set in
 *                              the module.
 */
uint32_t as_threshold_get_t1(uint32_t* base_addr);


/**
 * Set the t1 value.
 * 
 * @param base_addr             Address of the corresponding hardware 
 *                              module (see also as_hardware.h)
 * @param value                 The t1 value to be set.
 */
void as_threshold_set_t1(uint32_t* base_addr, uint32_t value);


/**
 * Get the t2 value set in the module.
 * 
 * @param base_addr             Address of the corresponding hardware 
 *                              module (see also as_hardware.h)
 * @return                      The return value is the t2 value set in
 *                              the module.
 */
uint32_t as_threshold_get_t2(uint32_t* base_addr);


/**
 * Set the t2 value.
 * 
 * @param base_addr             Address of the corresponding hardware 
 *                              module (see also as_hardware.h)
 * @param value                 The t2 value to be set.
 */
void as_threshold_set_t2(uint32_t* base_addr, uint32_t value);


/**
 * Enable/disable data replacement (fixed value) for image data range [a] (image_data < t1).
 * 
 * @param base_addr             Address of the corresponding hardware 
 *                              module (see also as_hardware.h)
 * @param enable                Enable ('AS_TRUE') to replace image data
 *                              in range [a] with a fixed value (use 
 *                              appropriate driver function to set this 
 *                              value). 
 *                              Disable ('AS_FALSE') to pass original 
 *                              image data in range [a]. 
 */
void as_threshold_enable_a_value(uint32_t* base_addr, AS_BOOL enable);


/**
 * Enable/disable data replacement (fixed value) for image data range [b] (t1 >= image_data <= t2).
 * 
 * @param base_addr             Address of the corresponding hardware 
 *                              module (see also as_hardware.h)
 * @param enable                Enable ('AS_TRUE') to replace image data
 *                              in range [b] with a fixed value (use 
 *                              appropriate driver function to set this 
 *                              value). 
 *                              Disable ('AS_FALSE') to pass original 
 *                              image data in range [b]. 
 */
void as_threshold_enable_b_value(uint32_t* base_addr, AS_BOOL enable);


/**
 * Enable/disable data replacement (fixed value) for image data range [c] (image_data > t2).
 * 
 * @param base_addr             Address of the corresponding hardware 
 *                              module (see also as_hardware.h)
 * @param enable                Enable ('AS_TRUE') to replace image data
 *                              in range [c] with a fixed value (use 
 *                              appropriate driver function to set this 
 *                              value). 
 *                              Disable ('AS_FALSE') to pass original 
 *                              image data in range [c]. 
 */
void as_threshold_enable_c_value(uint32_t* base_addr, AS_BOOL enable);


/**
 * Set the fixed value for image data range [a] (image_data < t1).
 * 
 * @param base_addr             Address of the corresponding hardware 
 *                              module (see also as_hardware.h)
 * @param value                 Fix value for image data range [a]. 
 */
void as_threshold_set_a_value(uint32_t* base_addr, uint32_t value);


/**
 * Set the fixed value for image data range [b] (t1 >= image_data <= t2).
 * 
 * @param base_addr             Address of the corresponding hardware 
 *                              module (see also as_hardware.h)
 * @param value                 Fix value for image data range [b]. 
 */
void as_threshold_set_b_value(uint32_t* base_addr, uint32_t value);


/**
 * Set the fixed value for image data range [c] (image_data > t2).
 * 
 * @param base_addr             Address of the corresponding hardware 
 *                              module (see also as_hardware.h)
 * @param value                 Fix value for image data range [c]. 
 */
void as_threshold_set_c_value(uint32_t* base_addr, uint32_t value);


/** @}*/

#endif /** AS_THRESHOLD_H */
