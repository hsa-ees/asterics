/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  Copyright (C) Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Author:         Alexander Zoellner
--
-- Description:    List of ASTERICS devices to be created in OS user space.
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
--! @brief Hardware support module for ASTERICS device creation in OS user space.
--------------------------------------------------------------------------------*/

#include "asterics.h"
#include "as_hardware.h"

//const char *build_hw_Version = "";
//const char *build_hw_date = "";

#if AS_OS_POSIX

#include "as_linux_kernel_if.h"

/* List of ASTERICS devices for the ASTERICS device driver */
as_device_t as_device_list[]={
    {.dev_type = DEV_TYPE_REGIO,
     .dev_name = "as_regio_global",
     .flags = O_RDWR,
     .interface_width = 32,
     .dev_addr = ASTERICS_BASEADDR,
     .addr_range = ASTERICS_ADDRESS_MASK,
     .manage_cache = AS_TRUE
    },
    {.dev_type = DEV_TYPE_MEMIO,
     .dev_name = "as_memreader_0_128",
     .flags = O_WRONLY,
     .interface_width = 64,
     .dev_addr = AS_MODULE_BASEADDR_READER0,
     .addr_range = 0x0,
     .manage_cache = AS_TRUE
    },
    {.dev_type = DEV_TYPE_MEMIO,
     .dev_name = "as_memwriter_0_128",
     .flags = O_RDONLY,
     .interface_width = 64,
     .dev_addr = AS_MODULE_BASEADDR_WRITER0,
     .addr_range = 0x0,
     .manage_cache = AS_TRUE
    },
    {.dev_type = DEV_TYPE_MMAP,
     .dev_name = "as_mmap_0_in_data",
     .flags = O_RDWR,
     .interface_width = 32,
     .dev_addr = AS_MODULE_BASEADDR_READER0,
     .addr_range = 0x400000,
     .manage_cache = AS_TRUE
    },
    {.dev_type = DEV_TYPE_MMAP,
     .dev_name = "as_mmap_0_out_data",
     .flags = O_RDONLY,
     .interface_width = 32,
     .dev_addr = AS_MODULE_BASEADDR_WRITER0,
     .addr_range = 0x400000,
     .manage_cache = AS_TRUE
    },
    {.dev_type = DEV_TYPE_MMAP,
     .dev_name = "as_mmap_1_in_data",
     .flags = O_RDWR,
     .interface_width = 32,
     .dev_addr = 0,
     .addr_range = 0x400000,
     .manage_cache = AS_TRUE
    },
    {.dev_type = DEV_TYPE_MMAP,
     .dev_name = "as_mmap_1_out_data",
     .flags = O_RDWR,
     .interface_width = 32,
     .dev_addr = 0,
     .addr_range = 0x400000,
     .manage_cache = AS_TRUE
    }
};

as_device_t *get_devices() {
    return as_device_list;
}

uint32_t get_num_devices() {
    return (sizeof(as_device_list)/sizeof(as_device_t));
}

#endif /* AS_OS_POSIX */

/*
as_device_t as_device_list[]={
    {.dev_type = DEV_TYPE_REGIO,
     .dev_name = "as_regio_global",
     .flags = O_RDWR,
     .interface_width = 32,
     .dev_addr = (uint32_t*)ASTERICS_BASEADDR,
     .addr_range = ASTERICS_ADDRESS_MASK,
     .manage_cache = AS_FALSE
    },
    {.dev_type = DEV_TYPE_MEMIO,
     .dev_name = "as_memwriter_0_128",
     .flags = O_RDONLY,
     .interface_width = 128,
     .dev_addr = (uint32_t*)AS_MODULE_BASEADDR_AS_MEMWRITER_0,
     .addr_range = 0x0,
     .manage_cache = AS_FALSE
    },
    {.dev_type = DEV_TYPE_MEMIO,
     .dev_name = "as_memreader_0_128",
     .flags = O_WRONLY,
     .interface_width = 128,
     .dev_addr = (uint32_t*)AS_MODULE_BASEADDR_AS_MEMREADER_0,
     .addr_range = 0x0,
     .manage_cache = AS_FALSE
    },
    {.dev_type = DEV_TYPE_MMAP,
     .dev_name = "as_mmap_in_data",
     .flags = O_RDWR,
     .interface_width = 64,
     .dev_addr = 0,
     .addr_range = 0x400000,
     .manage_cache = AS_FALSE
    },
    {.dev_type = DEV_TYPE_MMAP,
     .dev_name = "as_mmap_out_data",
     .flags = O_RDWR,
     .interface_width = 64,
     .dev_addr = 0,
     .addr_range = 0x400000,
     .manage_cache = AS_FALSE
    }
};
 */

/*
as_device_t as_device_list[]={
    {.dev_type = DEV_TYPE_REGIO,
     .dev_name = "as_regio_global",
     .flags = O_RDWR,
     .interface_width = 32,
     .dev_addr = (uint32_t*)ASTERICS_BASEADDR,
     .addr_range = ASTERICS_ADDRESS_MASK,
     .manage_cache = AS_FALSE
    },
    {.dev_type = DEV_TYPE_MEMIO,
     .dev_name = "as_memwriter_0_32",
     .flags = O_RDONLY,
     .interface_width = 32,
     .dev_addr = (uint32_t*)AS_ADDR(AS_MODULE_BASEREG_MEMWRITER_0),
     .addr_range = 0x0,
     .manage_cache = AS_TRUE
    },
    {.dev_type = DEV_TYPE_MEMIO,
     .dev_name = "as_memwriter_1_32",
     .flags = O_RDONLY,
     .interface_width = 32,
     .dev_addr = (uint32_t*)AS_ADDR(AS_MODULE_BASEREG_MEMWRITER_1),
     .addr_range = 0x0,
     .manage_cache = AS_TRUE
    },
    {.dev_type = DEV_TYPE_MEMIO,
     .dev_name = "as_memwriter_2_64",
     .flags = O_RDONLY,
     .interface_width = 64,
     .dev_addr = (uint32_t*)AS_ADDR(AS_MODULE_BASEREG_MEMWRITER_2),
     .addr_range = 0x0,
     .manage_cache = AS_FALSE
    },
    {.dev_type = DEV_TYPE_MEMIO,
     .dev_name = "as_memreader_0_64",
     .flags = O_WRONLY,
     .interface_width = 64,
     .dev_addr = (uint32_t*)AS_ADDR(AS_MODULE_BASEREG_MEMREADER_0),
     .addr_range = 0x0,
     .manage_cache = AS_FALSE
    },
    {.dev_type = DEV_TYPE_MMAP,
     .dev_name = "as_mmap_in_data",
     .flags = O_RDWR,
     .interface_width = 64,
     .dev_addr = 0,
     .addr_range = 0x400000,
     .manage_cache = AS_FALSE
    },
    {.dev_type = DEV_TYPE_MMAP,
     .dev_name = "as_mmap_out_data",
     .flags = O_RDWR,
     .interface_width = 64,
     .dev_addr = 0,
     .addr_range = 0x400000,
     .manage_cache = AS_FALSE
    }
};
*/
