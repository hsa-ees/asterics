/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework and the VEARS core.
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Author:         Alexander Zoellner
--                 Patrick Zacharias
--
----------------------------------------------------------------------------------
--  This program is free software: you can redistribute it and/or modify
--  it under the terms of the GNU Lesser General Public License as published by
--  the Free Software Foundation, either version 3 of the License, or
--  (at your option) any later version.
--
--  This program is distributed in the hope that it will be useful,
--  but WITHOUT ANY WARRANTY; without even the implied warranty of
--  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
--  GNU Lesser General Public License for more details.
--
--  You should have received a copy of the GNU Lesser General Public License
--  along with this program.  If not, see <http://www.gnu.org/licenses/>.
----------------------------------------------------------------------------------
--! @file       as_linux_kernel_if.h
--! @brief      Common definitions for the ASTERICS kernel module and
--              the Linux backend in 'as_support' to allow them interact
--              with each other.
--------------------------------------------------------------------------------*/

#ifndef AS_LINUX_KERNEL_IF_H
#define AS_LINUX_KERNEL_IF_H

#include "as_buffer.h"
/*
 * Tells the ASTERICS device driver whether the "copy_from_user" has to be used
 * for accessing the "arg" parameter for the unlocked_ioctl file operation.
 * "CALLED_FROM_KERNEL" is only used for the control and regio device.
 */
#define CALLED_FROM_USER 400
#define CALLED_FROM_KERNEL 500

/********************* Declarations for control device ***********************/

typedef struct {
  char name[20];                 /* Device name used for printing feedback if device creation was successful */
  int type;                      /* One of the AS_DEV_TYPE */
  as_hardware_address_t address; /* Hardware address of the memory module for DEV_TYPE_MEMIO, start address for DEV_TYPE_REGIO and DEV_TYPE_I2C */
  uint32_t address_range_size;   /* Number of bytes to be mapped for DEV_TYPE_REGIO and DEV_TYPE_I2C. Number of bytes to allocate for DEV_TYPE_MMAP */
  uint32_t interface_width;      /* Bit width of the bus interface of the memory module for the DEV_TYPE_MEMIO device */
  uint8_t flags;                 /* O_RDWR, O_RDONLY or O_WRONLY; DEV_TYPE_MEMIO requires O_RDONLY for as_memwriter and O_WRONLY for as_memreader */
  char manage_cache;             /* If "AS_TRUE", the device driver has to handle cache coherency for the device (currently: as_memio only) */
  char support_data_unit;        /* If "AS_TRUE", the device is capable of providing the end address of the last transferred unit */
} device_info_t;

typedef union {
  // User -> Kernel
  as_buffer_config_t config;
  // Kernel -> User
  as_buffer_obj_handle_t object;
} buffer_info_t;

/*
 * Structure used for the control device of the ASTERICS device driver.
 * Use "CMD_CREATE_DEVICE" for creating a new device of "dev_type" or
 * "CMD_REMOVE_DEVICE" for deleting ALL devices except for the control
 * device.
 */
typedef struct {
  int cmd; /* CMD_CREATE_DEVICE or CMD_REMOVE_DEVICE */
  union {
    device_info_t device;
    buffer_info_t buffer;
  };

} as_ctrl_params_t;

/* Create a new device of type AS_DEV_TYPE */
#define CMD_CREATE_DEVICE 100
/* Remove ALL devices except the control device */
#define CMD_REMOVE_DEVICE 200

#define CMD_CREATE_BUFFER 300
#define CMD_DESTROY_BUFFER 400
#define CMD_ADD_BUFFER 500
#define CMD_REMOVE_BUFFER 600

/* Device types available to the ASTERICS device driver to be used for control device. */
typedef enum { DEV_TYPE_MMAP, DEV_TYPE_MEMIO, DEV_TYPE_REGIO, DEV_TYPE_I2C } AS_DEV_TYPE;

/**************** Declarations for ioctl of the "AS_DEV_TYPE" ****************/

/*
 * Structure used for ioctl/unlocked_ioctl file operation of devices of the type AS_DEV_TYPE.
 */
typedef struct {
  uint32_t cmd;                         /* AS_IOCTL_CMD_READ (from hardware) or AS_IOCTL_CMD_WRITE (to hardware) */
  as_hardware_address_t address;        /* Address of the hardware access for DEV_TYPE_REGIO and DEV_TYPE_I2C. Memory module address for DEV_TYPE_MMAP. */
  uint32_t value;                       /* Value to write for DEV_TYPE_REGIO and DEV_TYPE_I2C. Amount of data to transfer for DEV_TYPE_MMAP. */
  as_virtual_address_t user_addr_start; /* Start address in the mapped virtual address space of the user for DEV_TYPE_MMAP */
} as_ioctl_params_t;

/* Read data provided by hardware */
#define AS_IOCTL_CMD_READ 100
/* Write data to hardware */
#define AS_IOCTL_CMD_WRITE 200

#define AS_IOCTL_CMD_MMAP_WAIT  400

#endif /* AS_LINUX_KERNEL_IF_H */
