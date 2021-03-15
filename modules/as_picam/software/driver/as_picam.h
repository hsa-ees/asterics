/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework.
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Module:         as_picam
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Author:         Thomas Izycki
--
-- Modified:       
--
-- Description:    Driver (header file) for as_picam module
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
 * @file  as_picam.h
 * @brief Driver (header file) for as_picam module.
 *
 * \addtogroup asterics_modules
 * @{
 * \defgroup as_picam as_picam: Raspberry Pi Camera Adapter
 * @}
 *
 * This module interfaces the VIDEO_IN Module from Trenz-Electronic GmbH and
 * an attached raspberry pi camera v1.3 (sensors ov5647) or v2.1 (sensor imx219).
 *
 * It configures the sensor with the help of the PS IIC module and receives the
 * image stream from the VIDEO_IN module via AXI stream.
 *
 * The modules output data format is as follows:
 *   - 1280x720 pixels
 *   - 8 bit gray-scale
 *
 * To allow frame based image operations, The 'as_picam'
 * module can be operated in two modes:
 *   - Single shot mode ('run_once'): the module waits for a new frame
 *     to come in and outputs data for only this single frame.
 *   - Continuous mode ('run'): the module outputs data for all frames
 *     until the module is stopped ('stop').
 */


#ifndef AS_PICAM_H
#define AS_PICAM_H


#include "as_support.h"

/* uncomment for debug output */
//#define DEBUG_PRINT


/******************* I/O Registers ************************/

/* Internal register definitions */
#define AS_PICAM_STATE_CONTROL_REG_OFFSET	0

/* Bit offsets */
#define AS_PICAM_FRAME_DONE_BIT_OFFSET   0
#define AS_PICAM_RESET_BIT_OFFSET       16
#define AS_PICAM_DATAENABLE_BIT_OFFSET  17
#define AS_PICAM_ENABLEONCE_BIT_OFFSET  18
/* Bit masks */
#define AS_PICAM_FRAME_DONE_MASK        (1<<AS_PICAM_FRAME_DONE_BIT_OFFSET)
#define AS_PICAM_RESET_MASK             (1<<AS_PICAM_RESET_BIT_OFFSET)
#define AS_PICAM_DATAENABLE_MASK        (1<<AS_PICAM_DATAENABLE_BIT_OFFSET)
#define AS_PICAM_ENABLEONCE_MASK        (1<<AS_PICAM_ENABLEONCE_BIT_OFFSET)

/** \addtogroup as_picam
 *  @{
 */

/******************* Driver functions **********************/

/**
 * Initialize the pi camera (via IIC).
 *
 * @param iic_device_id         Device ID of the corresponding IIC
 *                              module (see also xparameters.h)
 */
int as_picam_init(uint16_t iic_device_id);

/**
 * Set the module to free running mode until the corresponding
 * as_picam_stop(..) function is called.
 *
 * @param base_addr             Address of the corresponding hardware
 *                              module (see also as_hardware.h)
 */
void as_picam_run(uint32_t* base_addr);

/**
 * Stop the module to send image data after the recent incoming frame
 * is completed.
 *
 * @param base_addr             Address of the corresponding hardware
 *                              module (see also as_hardware.h)
 */
void as_picam_stop(uint32_t* base_addr);

/**
 * Instruct the corresponding module to send image data of only one frame.
 *
 * @param base_addr             Address of the corresponding hardware
 *                              module (see also as_hardware.h)
 */
void as_picam_run_once(uint32_t* base_addr);

/**
 * Get information towards frame transmission status (module output).
 *
 * @param base_addr             Address of the corresponding hardware
 *                              module (see also as_hardware.h)
 *
 * @return                      The return value shows if a frame is 
 *                              completely transmitted on the modules
 *                              output side.
 */
AS_BOOL as_picam_frame_is_transmitted(uint32_t* base_addr);


/** @}*/

#endif /** AS_PICAM_H */
