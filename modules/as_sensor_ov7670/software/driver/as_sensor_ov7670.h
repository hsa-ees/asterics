/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework.
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Module:         as_sensor_ov7670
--
-- Company:        Efficient Embedded Systems Group at University of Applied
Sciences, Augsburg, Germany
-- Author:         Michael Schaeferling
--
-- Modified:       Philip Manke: Add support for as_iic IIC hardware
--
-- Description:    Driver (header file) for as_sensor_ov7670 module
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
 * @file  as_sensor_ov7670.h
 * @brief Driver (header file) for as_sensor_ov7670 module.
 *
 * \addtogroup asterics_modules
 * @{
 *   \defgroup as_sensor_ov7670 as_sensor_ov7670: OV7670 Camera Adapter
 * @}
 *
 * This module interfaces an attached OV7670 image sensor.
 * It configures the sensor with the help of an additionally needed
 * IIC module and receives the image data stream from the sensor.
 *
 * The modules output data format is as follows:
 *   - 640x480 pixels
 *   - 8 bit gray-scale
 *
 * Note: The OV7670 image sensor does not have a trigger input pin, thus it
 * continuously sends an image data stream.
 *
 * To allow frame based image operations, The 'as_sensor_ov7670'
 * module can be operated in two modes:
 *   - Single shot mode ('run_once'): the module waits for a new frame
 *     to come in and outputs data for only this single frame.
 *   - Continuous mode ('run'): the module outputs data for all frames
 *     until the module is stopped ('stop').
 *
 */

#ifndef AS_SENSOR_OV7670_H
#define AS_SENSOR_OV7670_H

#include "asterics.h"

#include <unistd.h> // for usleep()

#if (defined AS_USING_XILINX_PL_IIC) && (AS_OS_POSIX == 0)
#include "xiic_l.h"
/* Xilinx specific headers, needed for IIC device address and communication: */
#include "xparameters.h"
#endif

#ifdef AS_USING_XILINX_PS_IIC
// TODO
#endif

/**
 This driver supports configuring the OV7670 Camera via multiple different
 IIC master modules. Multiple cameras may be connected and configured using
 this driver. Set the any of the following defines to select IIC types for
 the pool of available hardware modules before compiling the ASTERICS library:
 #define AS_USING_AS_IIC
 #define AS_USING_XILINX_PL_IIC
 #define AS_USING_XILINX_PS_IIC // TO BE IMPLEMENTED
*/
/* uncomment for debug output */
//#define DEBUG_PRINT

/* Native resolution of the sensor: */
#define OV7670_SENSOR_WIDTH 640
#define OV7670_SENSOR_HEIGHT 480

/******************* I/O Registers ************************/

/* Internal register definitions */
#define AS_SENSOR_OV7670_STATE_CONTROL_REG_OFFSET 0
#define AS_SENSOR_OV7670_PARM0_REG_OFFSET 1

/* Bit offsets */
#define AS_SENSOR_OV7670_FRAME_DONE_BIT_OFFSET 0
#define AS_SENSOR_OV7670_RESET_BIT_OFFSET 16
#define AS_SENSOR_OV7670_DATAENABLE_BIT_OFFSET 17
#define AS_SENSOR_OV7670_ENABLEONCE_BIT_OFFSET 18
#define AS_SENSOR_OV7670_EXT_RESET_BIT_OFFSET 19
/* Bit masks */
#define AS_SENSOR_OV7670_FRAME_DONE_MASK                                       \
  (1 << AS_SENSOR_OV7670_FRAME_DONE_BIT_OFFSET)
#define AS_SENSOR_OV7670_RESET_MASK (1 << AS_SENSOR_OV7670_RESET_BIT_OFFSET)
#define AS_SENSOR_OV7670_DATAENABLE_MASK                                       \
  (1 << AS_SENSOR_OV7670_DATAENABLE_BIT_OFFSET)
#define AS_SENSOR_OV7670_ENABLEONCE_MASK                                       \
  (1 << AS_SENSOR_OV7670_ENABLEONCE_BIT_OFFSET)
#define AS_SENSOR_OV7670_EXT_RESET_MASK                                        \
  (1 << AS_SENSOR_OV7670_EXT_RESET_BIT_OFFSET)

// Constant definitions for different IIC types:
enum ov7670_iic_types {
  OV7670_AS_IIC,
  OV7670_XILINX_PL_IIC,
  OV7670_XILINX_PS_IIC
};

/** \addtogroup as_sensor_ov7670
 *  @{
 */

/******************* Driver functions **********************/

/**
 * Initialize the hardware module (FPGA logic) as well as
 * the attached OV7670 sensor module (via IIC).
 *
 * @param base_addr             Address of the corresponding hardware
 *                              module (see also as_hardware.h)
 */
uint8_t as_sensor_ov7670_init(uint32_t *base_addr, uint8_t iic_type,
                              uint32_t *iic_base_addr);

/**
 * Reset the hardware module (FPGA logic) as well as the attached
 * OV7670 sensor module (reset pin and IIC registers).
 *
 * @param base_addr             Address of the corresponding hardware
 *                              module (see also as_hardware.h)
 */
void as_sensor_ov7670_reset(uint32_t *base_addr);

/**
 * Set the module to free running mode until the corresponding
 * as_sensor_ov7670_stop(..) function is called.
 *
 * @param base_addr             Address of the corresponding hardware
 *                              module (see also as_hardware.h)
 */
void as_sensor_ov7670_run(uint32_t *base_addr);

/**
 * Stop the module to send image data after the recent incoming frame
 * is completed.
 *
 * @param base_addr             Address of the corresponding hardware
 *                              module (see also as_hardware.h)
 */
void as_sensor_ov7670_stop(uint32_t *base_addr);

/**
 * Instruct the corresponding module to send image data of only one frame.
 *
 * @param base_addr             Address of the corresponding hardware
 *                              module (see also as_hardware.h)
 */
void as_sensor_ov7670_run_once(uint32_t *base_addr);

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
AS_BOOL as_sensor_ov7670_frame_is_transmitted(uint32_t *base_addr);

/**
 * Set the attached OV7670 sensor modules gain-adjustment to
 * 'auto' or 'manual' (via IIC).
 *
 * @param enable                Enable ('AS_TRUE') or disable ('AS_FALSE')
 *                              the auto-gain feature.
 *                              When auto-gain is not used, an
 *                              appropriate gain value must be set using
 *                              the corresponding function.
 */
void as_sensor_ov7670_gain_auto(uint32_t *base_addr, AS_BOOL enable);

/**
 * Set the gain value for the OV7670 sensor module.
 *
 * @return                      The return value is the gain value
 *                              of the module.
 */
void as_sensor_ov7670_gain_set(uint32_t *base_addr, uint8_t gain);

/**
 * Get the gain value set in the module.
 *
 * @return                      The return value is the gain value set
 *                              in the module.
 */
uint8_t as_sensor_ov7670_gain_get(uint32_t *base_addr);

/**
 * Set the attached OV7670 sensor modules exposure-adjustment to
 * 'auto' or 'manual' (via IIC) .
 *
 * @param enable                Enable ('AS_TRUE') or disable ('AS_FALSE')
 *                              the auto-exposure feature.
 *                              When auto-exposure is not used, an
 *                              appropriate exposure value must be
 *                              set using the corresponding function.
 */
void as_sensor_ov7670_exposure_auto(uint32_t *base_addr, AS_BOOL enable);

/**
 * Set the exposure value for the OV7670 sensor module.
 *
 * @return                      The return value is the exposure value
 *                              of the module.
 */
void as_sensor_ov7670_exposure_set(uint32_t *base_addr, uint32_t exposure);

/**
 * Get the exposure value set in the module.
 *
 * @return                      The return value is the exposure value
 *                              of the module.
 */
uint32_t as_sensor_ov7670_exposure_get(uint32_t *base_addr);

/** @}*/

#endif /** AS_SENSOR_OV7670_H */
