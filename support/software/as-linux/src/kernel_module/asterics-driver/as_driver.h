/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework and the VEARS core. 
--  Copyright (C) Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- File:           as_driver.h
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Author:         Alexander Zoellner
--
-- Modified:       
--
-- Description:    Header file of linux device driver for ASTERICS
--                 ASTERICS linux device driver for performing general register IO 
--                 and memory data transfers.
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

#ifndef _AS_DRIVER_
#define _AS_DRIVER_

#include <linux/cdev.h>

/* Maximum number of supported devices (first one is reserved for the control device) */
#define MAX_DEVICES 100

/* 
 * Set the interval of the polling timer in jiffies. The actual resulting time in ms 
 * depends on the settings for HZ in param.h of the corresponding platform's architecture.
 * For most embedded platform HZ is set to 100, which results in a 10 ms granularity.
 */
#define TIMER_INTERVAL 1


/* Mmap control structure */
typedef struct mmap_info {
    void *data;                  /* Physical concurrent memory for mapping to user space */
    uint32_t size;               /* Size of physical memory for mmap */
    int page_allocation_order;   /* The number of pages to allocate (2^x) */
}mmap_info_t;

/* Structure containing device information */
struct device_data_t {
  
    /* General information */
    struct cdev cdev;               /* Device struct */
    uint8_t flags;                  /* Supported direction flags (O_RDWR, O_RONLY, O_WRONLY) */
    atomic_t busy;                  /* Device currently in use */
    void* fops;                     /* Corresponding file operations (memio, mmap, ...); Currently only used to identify regio and interrupt handling */
    struct as_mutex_s * access_lock; /* Secure critical part of functions, where multiple calls could lead to race conditions */
    
    /* HW memory modules (currently memreader, -writer) */
    uint32_t * hw_module_addr;      /* Phys. address of hardware module (as_memreader, -writer, ...) */
    uint32_t interface_width;       /* Inferface width to memory */
    
    /* Interrupts */
    AS_BOOL register_intr;          /* Device is going to sleep and is ready to process interrupts */
    wait_queue_head_t wait;         /* Wait queue for blocking calls */
    uint8_t wake_up_cond;           /* Used to wake up blocking processes and prevents premature wake ups */
    
    /* Devices with memory region (currently as_regio, as_i2c) */
    char* req_mem_region_name;      /* Memory region name (as_regio, as_i2c, ...) */
    uint32_t * baseaddress_virt;    /* Virtual address of memory region */
    uint32_t offset;                /* Offset between phys. and virt. memory region addresses */
    uint32_t address_range_size;    /* Size of the mapped region (also used for mmap address range) */
    
    /* mmap specific information */
    mmap_info_t * mmap;             /* Mmap control structure which contains the size and start address of the allocated memory. */
    
    /* memio specific information */
    AS_BOOL memio_active;                 /* Memio device is open (used by interrupt handler) */
    struct as_memio_file_s * memio_file;  /* Memio control structure (Part of the as_memio module driver) */
    AS_BOOL manage_cache;                 /* Set to "AS_TRUE" if the driver has to handle cache coherency itself */
};




#endif /** _AS_DRIVER_ */
