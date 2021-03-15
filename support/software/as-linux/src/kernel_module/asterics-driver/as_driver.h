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
--! @file       as_driver.c
--! @brief      ASTERICS linux device driver for performing general register IO
--              and memory data transfers.
--------------------------------------------------------------------------------*/

/**
 * @file  as_driver.h
 * @brief Linux kernel driver header file
 *
 * @defgroup as_driver Linux kernel driver
 * @{
 * @details The linux kernel driver provides access to ASTERICS hardware
 * through POSIX system-calls. It creates and configures devices to be able
 * to read and write from user-space.
 */

#ifndef _AS_DRIVER_
#define _AS_DRIVER_

#include <linux/cdev.h>

#include "as_support.h"
#include "as_support_linux.h"

/** Maximum number of supported devices (first one is reserved for the control
 * device) */
#define MAX_DEVICES 100

/**
 * Set the interval of the polling timer in jiffies. The actual resulting time
 * in ms depends on the settings for HZ in param.h of the corresponding
 * platform's architecture. For most embedded platform HZ is set to 100, which
 * results in a 10 ms granularity.
 */
#define TIMER_INTERVAL 1

/** Mmap control structure */
typedef struct mmap_info {
  /** Physical concurrent memory for mapping to user space */
  //void *data;
  as_buffer_obj_t *buffer;
  /** Size of physical memory for mmap */
  uint32_t size;
  /** The number of pages to allocate (2^x) (unused) */
  int page_allocation_order;
} mmap_info_t;

/** Structure containing device information */
struct device_data_t {
  /** @name General information */
  ///@{
  /** Device struct */
  struct cdev cdev;
  /** Supported direction flags (O_RDWR, O_RONLY, O_WRONLY) */
  uint8_t flags;
  /** Device currently in use */
  atomic_t busy;
  /** Corresponding file operations (memio, mmap, ...);
   *  @note Currently only used to identify regio and interrupt handling */
  void *fops;
  /** Secure critical part of functions, where multiple calls could lead to race
   * conditions */
  struct as_mutex_s *access_lock;
  ///@}

  /** @name HW memory modules
   *  @note Currently memreader/writer */
  ///@{
  /** Phys. address of hardware module (as_memreader, -writer, ...) */
  as_hardware_address_t hw_module_addr;
  /** Inferface width to memory */
  uint32_t interface_width;
  ///@}

  /** @name Interrupts */
  ///@{
  /** Device is going to sleep and is ready to process interrupts */
  AS_BOOL register_intr;
  /** Wait queue for blocking calls */
  wait_queue_head_t wait;
  /** Used to wake up blocking processes and prevents premature wake ups */
  uint8_t wake_up_cond;
  ///@}

  /** @name Devices with memory region
   *  @note Currently as_regio, as_i2c */
  ///@{
  /** Memory region name (as_regio, as_i2c, ...) */
  char *req_mem_region_name;
  /** Virtual address of memory region */
  as_kernel_address_t baseaddress_virt;
  /** virt. - phys. memory address */
  ptrdiff_t offset;
  /** Size of the mapped region (also used for mmap address range) */
  uint32_t address_range_size;
  ///@}

  /** @name mmap specific information */
  ///@{
  /** Mmap control structure which contains the size and start address of the
   * allocated memory. */
  mmap_info_t *mmap;
  ///@}

  /** @name memio specific information */
  ///@{
  /** Memio device is open (used by interrupt handler) */
  AS_BOOL memio_active;
  /** Memio control structure (Part of the as_memio module driver) */
  struct as_memio_file_s *memio_file;
  /** Set to "AS_TRUE" if the driver has to handle cache coherency itself */
  AS_BOOL manage_cache;
  /** Set to "AS_TRUE" if the device is configured with SUPPORT_DATA_UNIT_COMPLETE enabled */
  AS_BOOL support_data_unit;
  ///@}
};
#endif /** _AS_DRIVER_ */
       ///@}
