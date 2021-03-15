/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  Copyright (C) Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Author:         Michael Schaeferling
--
-- Description:    
----------------------------------------------------------------------------------
--  This program is free software: you can redistribute it and/or modify
--  it under the terms of the GNU General Public License as published by
--  the Free Software Foundation, either version 3 of the License, or
--  (at your option) any later version.
--
--  This program is distributed in the hope that it will be useful,
--  but WITHOUT ANY WARRANTY; without even the implied warranty of
--  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
--  GNU General Public License for more details.
--
--  You should have received a copy of the GNU General Public License
--  along with this program.  If not, see <http://www.gnu.org/licenses/>.
----------------------------------------------------------------------------------
--! @file
--! @brief Hardware support module for ASTERICS systems.
--------------------------------------------------------------------------------*/

#ifndef AS_HARDWARE_H
#define AS_HARDWARE_H

#include "as_support.h"

/** Version of the matching ASTERICS hardware configuration */
//extern const char *build_hw_Version;
/** Date of building this file */
//extern const char *build_hw_date;

/****************************** ASTERICS IP-Core ********************************/
/* Base address of the ASTERICS IP-Core (first configuration register) */
#define ASTERICS_BASEADDR 0X43C10000

#define AS_REGISTERS_PER_MODULE 16

/* Address offset to be added to ASTERICS_BASEADDR to define accessible address 
 *  range of the IP-Core 
 */
#define ASTERICS_ADDRESS_MASK 0x10000

/********************** Global ASTERICS Processing Mapping **********************/

/** Index of register which is used to control the ASTERICS hardware chain */
#define AS_GLOBAL_PROCESSING_BASEREG           0

/*************************** Module Register Mapping ****************************/
/* 
 * List the first register index of all hardware modules of a specific ASTERICS 
 * chain to be accessed by software here.
 */
/* Uncomment for Reader/Writer Demo
 * #define AS_MODULE_BASEREG_AS_MEMREADER_0 0
 * #define AS_MODULE_BASEREG_AS_MEMWRITER_0 1
 */
/* Uncomment for OV7670 Demo */
/*
#define AS_MODULE_BASEREG_AS_MEMWRITER_0 0
#define AS_MODULE_BASEREG_INVERTER 1
#define AS_MODULE_BASEREG_IMAGE_SENSOR 2
*/

/************************** Module Address Mapping ***************************/
/* Uncomment for Reader/Writer Demo
 * #define AS_MODULE_BASEADDR_AS_MEMREADER_0 ((uint32_t*)(ASTERICS_BASEADDR + (AS_MODULE_BASEREG_AS_MEMREADER_0 * 4 * AS_REGISTERS_PER_MODULE)))
 * #define AS_MODULE_BASEADDR_AS_MEMWRITER_0 ((uint32_t*)(ASTERICS_BASEADDR + (AS_MODULE_BASEREG_AS_MEMWRITER_0 * 4 * AS_REGISTERS_PER_MODULE)))
 */
/* Uncomment for OV7670 Demo */
/*
#define AS_MODULE_BASEADDR_AS_MEMWRITER_0 ((uint32_t*)(ASTERICS_BASEADDR + (AS_MODULE_BASEREG_AS_MEMWRITER_0 * 4 * AS_REGISTERS_PER_MODULE)))
#define AS_MODULE_BASEADDR_INVERTER ((uint32_t*)(ASTERICS_BASEADDR + (AS_MODULE_BASEREG_INVERTER * 4 * AS_REGISTERS_PER_MODULE)))
#define AS_MODULE_BASEADDR_IMAGE_SENSOR ((uint32_t*)(ASTERICS_BASEADDR + (AS_MODULE_BASEREG_IMAGE_SENSOR * 4 * AS_REGISTERS_PER_MODULE)))
*/

/************************** Module Address Calculation **************************/
/** Convert register index to address */
// #define AS_ADDR(ADDR) (uint64_t*)(ASTERICS_BASEADDR + (ADDR * 4))

/******************************* Device Information *****************************/

/* 
 * The following struct and functions are only available for the user space of 
 * an operating system for creating ASTERICS devices using the ASTERICS device
 * driver. 
 */

#if AS_OS_POSIX

/**
 *
 * Structure: as_device_t
 * 
 * This structure contains the required information to create ASTERICS devices 
 * using the ioctl of the ASTERICS device driver from user space. 
 *
 * @param dev_type             Type of the type which is to be created
 * @param dev_name             The desired name of the device to be created
 * @param flags                Supported direction flags of the device (i.e. O_RDWR, O_RDONLY, ...)
 * @param interface_width      The interface width of the hardware module, if the module is connected
 *                             to a memory bus (width in bit)
 * @param dev_addr             The base address of the hardware module or start address of a mapped
 *                             memory region (for as_regio device) which is used by the device
 *                             (Set to zero for mmap since it is not bound to a single hardware module)  
 * @param addr_range           The address to be added to dev_addr for mapping a memory region
 *                             (i.e. as_regio, as_i2c) or the the size of allocated physical memory (for as_mmap)
 *                             Not used for as_memio devices.
 * @param manage_cache         Set to "true" if the driver has to manage cache coherency of the device, "false" 
 *                             otherwise (e.g. if connected to ACP). Currently, only relevant for as_memio devices.
 *
 */
typedef struct {
    AS_DEV_TYPE dev_type;
    char * dev_name;
    uint8_t flags;
    uint8_t interface_width;
    as_hardware_address_t dev_addr;
    uint32_t addr_range;
    AS_BOOL manage_cache;
    AS_BOOL support_data_unit;
}as_device_t;


/**
 *  
 * Function: get_devices
 *
 * This function returns a pointer to a list of ASTERICS devices to be 
 * created using the ioctl of the ASTERICS device driver.
 * 
 * @return                      Address of the first device
 * 
 */
as_device_t *get_devices();


/**
 *  
 * Function: get_num_devices
 *
 * This function returns the number of available devices of the device 
 * list obtained by get_devices()
 * 
 * @return                      Number of devices of the device list
 * 
 */
uint32_t get_num_devices();

    
#endif /* AS_OS_POSIX */

#endif /** AS_HARDWARE_H */
