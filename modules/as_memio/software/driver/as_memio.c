/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework.
--  Copyright (C) Hochschule Augsburg, University of Applied Sciences, All rights
--  reserved
----------------------------------------------------------------------------------
-- File:           as_memio.c
-- Module:         as_memio
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Author:         Julian Sarcher, Alexander Zoellner
--
-- Modified:
--
-- Description:    Driver (source file) for as_memio streaming interface with
--                 as_memreader and as_memwriter hardware modules.
----------------------------------------------------------------------------------
--! @file
--! @brief Driver (source file) for as_memio streaming interface.
--------------------------------------------------------------------------------*/
#include "as_memio.h"

#if AS_OS_LINUX_KERNEL
    #include <asm/cacheflush.h>
    #include <asm/outercache.h>
#endif /* AS_OS_LINUX_KERNEL */

/**
 *
 * Structure for internal buffer handling and managing
 * HW/SW communication.
 *
 * @param baseaddr             Base address of the involved HW
 *                              module.
 * @param buffer                Pointer to the start address of the
 *                              as_memio buffer for data exchange
 *                              between HW and SW.
 * @param buffer_size           Size of the as_memio buffer in
 *                              byte.
 * @param cur_hw_addr           The first address on which the
 *                              HW module has not performed an
 *                              action yet.
 * @param transfer_size         Ensures a minimum amount of data to be 
 *                              transfered by memwriter hw module to 
 *                              prevent data loss due to too short data
 *                              transmissions. Parameter is ignored for 
 *                              memreader hw module since it is not relevant.
 * @param cur_sw_addr           The first address the SW will
 *                              perform an action on next.
 * @param cur_hw_start_addr     The start address of the current
 *                              HW module operation.
 * @param cur_hw_blocksize      The number of byte 
 *                              the HW module is performing an
 *                              action on starting from
 *                              cur_hw_start_addr.
 *
 */
typedef struct as_memio_buffer_handler_s {
    uint32_t  buffer_size;
    uint8_t * cur_hw_addr;
    uint8_t * cur_sw_addr;
    uint8_t * cur_hw_start_addr;
    uint32_t  cur_hw_blocksize;
    uint32_t  transfer_size;
    uint8_t * buffer_baseaddr_phys;
    uint8_t * buffer_baseaddr_virt;
}as_memio_buffer_handler_t;

typedef struct as_memio_hw_settings_s {
    uint32_t * baseaddr;
    uint32_t   wordsize;
    uint32_t   burst_length;
    AS_BOOL    read_not_write;
    AS_BOOL    manage_cache;
}as_memio_hw_settings_t;


typedef struct as_memio_file_s {
    as_memio_hw_settings_t memio_hw_settings;
    as_memio_buffer_handler_t memio_buffer_handler;
}as_memio_file_t;


void as_memio_module_setup(as_memio_hw_settings_t* hw_settings) {
    if ((*hw_settings).baseaddr != NULL) {
        /* HW module supports only 1 section for as_memio configuration */
        as_reader_writer_set_section_count((*hw_settings).baseaddr, 1);
        /* There is no section offset since there is only one section */
        as_reader_writer_set_section_offset((*hw_settings).baseaddr, 0);
        /* Set maximum possible burst length of HW module */
        as_reader_writer_set_max_burst_length((*hw_settings).baseaddr, (*hw_settings).burst_length);

        /* Bring HW module to defined state */
        as_reader_writer_reset((*hw_settings).baseaddr);
        
        /* Enable the memwriter module to receive data */
        if((*hw_settings).read_not_write == AS_TRUE) {
            as_writer_set_enable((*hw_settings).baseaddr);
        }
    }
}

void as_memio_config_init(as_memio_config_t * memio_config) {

    /* Set default values for using as_memwriter with as_memio */
    (*memio_config).as_reader_writer_buffer_size = AS_MEMIO_DEFAULT_FIFO_BUFFER_SIZE;       /* as_memio buffer_size in words */
    (*memio_config).as_reader_writer_transfer_size = AS_MEMIO_DEFAULT_HW_TRANSFER_SIZE;     /* minimum data to transfer on single read request */
    (*memio_config).as_reader_writer_max_burst_length = AS_MEMIO_DEFAULT_MAX_BURST_LENGTH;  /* max_burst_length in Bytes */
    (*memio_config).as_reader_writer_interface_width = AS_MEMIO_DEFAULT_INTERFACE_WIDTH;
    (*memio_config).manage_cache = AS_MEMIO_DEFAULT_MANAGE_CACHE;
}


/*
 * See annotation in as_memio.h
 */
as_memio_file_t * as_memio_open(uint32_t* as_reader_writer_baseaddr, as_memio_config_t* memio_config, uint8_t flags)   {

    as_memio_config_t memio_config_init;
    as_memio_file_t * fd = NULL;
    
    if(memio_config == NULL) {
        as_memio_config_init(&memio_config_init);
    }
    else {
        memio_config_init = *memio_config;
    }
    
    /* Create new structure for as_memio operations */
    fd = (as_memio_file_t*)as_malloc(sizeof(as_memio_file_t));
    if(fd == NULL) {
        return NULL;
    }
    

    /* Allocate memory for as_memio buffer */
    (*fd).memio_buffer_handler.buffer_baseaddr_virt = as_malloc((uint32_t)(memio_config_init).as_reader_writer_buffer_size*sizeof(uint8_t));
    if((*fd).memio_buffer_handler.buffer_baseaddr_virt == NULL) {
        as_free(fd);
        return NULL;
    }
    /* Set buffer size for internal data operation */
    (*fd).memio_buffer_handler.buffer_size = (memio_config_init).as_reader_writer_buffer_size;
    /* Set transfer size to prevent configuring to small sizes for data operations */
    (*fd).memio_buffer_handler.transfer_size = (memio_config_init).as_reader_writer_transfer_size;
    /* Set amount of data (in words) for first HW operation */
    (*fd).memio_buffer_handler.cur_hw_blocksize = 0;
#if AS_OS_LINUX_KERNEL
    (*fd).memio_buffer_handler.buffer_baseaddr_phys = (uint8_t*)virt_to_phys((volatile void *)(*fd).memio_buffer_handler.buffer_baseaddr_virt);
#else /* AS_OS_NONE */
    (*fd).memio_buffer_handler.buffer_baseaddr_phys = (*fd).memio_buffer_handler.buffer_baseaddr_virt;
#endif    
    /* Set operating HW address to as_memio buffer start address (Will be set by HW later on) */
    (*fd).memio_buffer_handler.cur_hw_addr = (*fd).memio_buffer_handler.buffer_baseaddr_virt;
    /* Set as_memio buffer operating pointer to as_memio buffer start address */
    (*fd).memio_buffer_handler.cur_sw_addr = (*fd).memio_buffer_handler.buffer_baseaddr_virt;
    /* Set HW address for first write operation (HW perspective) */
    (*fd).memio_buffer_handler.cur_hw_start_addr = (*fd).memio_buffer_handler.buffer_baseaddr_virt;
  

    /* Memio config assignments */
    /* Set address of associated hardware module */
    (*fd).memio_hw_settings.baseaddr = as_reader_writer_baseaddr;
    /* Set burst length for hardware module */
    (*fd).memio_hw_settings.burst_length = (memio_config_init).as_reader_writer_max_burst_length;
    /* Set word size of associated hardware module */
    (*fd).memio_hw_settings.wordsize = (memio_config_init).as_reader_writer_interface_width/8;
    /* Initialize as_memio for read operations if at least one of the following flags were provided */
    if( (flags&O_ACCMODE) == O_RDONLY) {
        (*fd).memio_hw_settings.read_not_write = AS_TRUE;
    }
    /* Initialize as_memio for write operations if at least one of the following flags were provided */
    else if( (flags&O_ACCMODE) == O_WRONLY) {
        (*fd).memio_hw_settings.read_not_write = AS_FALSE;
    }
    else {
        as_free((*fd).memio_buffer_handler.buffer_baseaddr_virt);
        as_free(fd);
        return NULL;
    }
    (*fd).memio_hw_settings.manage_cache = (memio_config_init).manage_cache;

    /* Setup hardware modules for as_memio usage */
    as_memio_module_setup(&((*fd).memio_hw_settings));

    /* Return the as_memio structure to caller for as_memio operations */
    return fd;
}

void as_memio_hw_write_update(as_memio_file_t* fd) {

    uint8_t * next_hw_start_addr;
    uint32_t next_hw_blocksize;
    uint8_t * temp_addr;

    /* check if next go can already be accepted by hardware */
    if (as_reader_writer_is_pending_go((*fd).memio_hw_settings.baseaddr) == AS_FALSE) {
    /* Set next start address to end of last data transmission */
        next_hw_start_addr = (*fd).memio_buffer_handler.cur_hw_start_addr + (*fd).memio_buffer_handler.cur_hw_blocksize;
        /*
         * Set start address to as_memio buffer start address if next start address points
         * to end of buffer.
         */
        if((next_hw_start_addr == ((*fd).memio_buffer_handler.buffer_baseaddr_virt + (*fd).memio_buffer_handler.buffer_size))) {
            next_hw_start_addr = (*fd).memio_buffer_handler.buffer_baseaddr_virt;
        }
        /* as_memio buffer is considered empty if HW and SW addresses are equal */
        if(next_hw_start_addr != (*fd).memio_buffer_handler.cur_sw_addr) {
            /* If HW pointer is ahead read the remaining as_memio buffer */
            if(next_hw_start_addr > (*fd).memio_buffer_handler.cur_sw_addr)  {
                next_hw_blocksize = ((uint32_t)(*fd).memio_buffer_handler.buffer_baseaddr_virt + (*fd).memio_buffer_handler.buffer_size) -
                        (uint32_t)next_hw_start_addr;
            }
            /* Otherwise read only up to SW pointer */
            else {
                next_hw_blocksize = (uint32_t)(*fd).memio_buffer_handler.cur_sw_addr - (uint32_t)next_hw_start_addr;
            }
            
            /* Update HW address and blocksize for next read request (of HW) */
            (*fd).memio_buffer_handler.cur_hw_blocksize = next_hw_blocksize;
            (*fd).memio_buffer_handler.cur_hw_start_addr = next_hw_start_addr;

            /*
             * Setup next read request if blocksize is not 0. Otherwise skip setup and try again on next
             * call of this function.
             */
            if((*fd).memio_buffer_handler.cur_hw_blocksize != 0) {
                /* Set start address for next write operation */
#if AS_OS_LINUX_KERNEL
                as_reader_writer_set_section_addr((*fd).memio_hw_settings.baseaddr, (uint32_t*)virt_to_phys((volatile void*)(*fd).memio_buffer_handler.cur_hw_start_addr));
#else /* AS_OS_NONE */
                as_reader_writer_set_section_addr((*fd).memio_hw_settings.baseaddr, (uint32_t*)(*fd).memio_buffer_handler.cur_hw_start_addr);
#endif
                /* Set blocksize in byte! (Required by HW module) */
                as_reader_writer_set_section_size((*fd).memio_hw_settings.baseaddr, (*fd).memio_buffer_handler.cur_hw_blocksize);
                /* Start as_memreader */
                as_reader_writer_set_go((*fd).memio_hw_settings.baseaddr); 
            }
        }
    }

    /* Get current operating address of HW module to update HW address of as_memio */
    temp_addr = (uint8_t*)as_reader_writer_get_cur_hw_addr((*fd).memio_hw_settings.baseaddr);
    if(temp_addr == 0) {
        temp_addr = (*fd).memio_buffer_handler.buffer_baseaddr_phys;
    }
    (*fd).memio_buffer_handler.cur_hw_addr = (uint8_t*)((uint32_t)(*fd).memio_buffer_handler.buffer_baseaddr_virt + 
                                              ((uint32_t)temp_addr) - (uint32_t)(*fd).memio_buffer_handler.buffer_baseaddr_phys);

    /*
     * Set HW address (as_memio) to buffer start address if no go signal has been set yet (default HW register value
     * is 0x0 after reset) or if HW pointer is out of buffer scope.
     */
    if(((*fd).memio_buffer_handler.cur_hw_addr == 0) || ((*fd).memio_buffer_handler.cur_hw_addr >=
            ((*fd).memio_buffer_handler.buffer_baseaddr_virt + (*fd).memio_buffer_handler.buffer_size)))
    {
        (*fd).memio_buffer_handler.cur_hw_addr = (*fd).memio_buffer_handler.buffer_baseaddr_virt;
    }
}

void as_memio_hw_read_update(as_memio_file_t* fd) {

    uint8_t * next_hw_start_addr;
    uint32_t next_hw_blocksize;
    uint8_t * temp_addr;

    /* Check if a new go signal can already be set */
    if (as_reader_writer_is_pending_go((*fd).memio_hw_settings.baseaddr) == AS_FALSE) {
        /* Set next start address to end of last data transmission */
        next_hw_start_addr = ((*fd).memio_buffer_handler.cur_hw_start_addr + (*fd).memio_buffer_handler.cur_hw_blocksize);
        /*
         * Set the start address to as_memio buffer start address if next start address points
         * to end of buffer.
         */
        if((next_hw_start_addr == ((*fd).memio_buffer_handler.buffer_baseaddr_virt + (*fd).memio_buffer_handler.buffer_size))) {
            next_hw_start_addr = (*fd).memio_buffer_handler.buffer_baseaddr_virt;
        }
        /* Calculate the number of available bytes for HW configuration and keep safety distance to SW pointer.*/
        if(next_hw_start_addr < (*fd).memio_buffer_handler.cur_sw_addr) {
            next_hw_blocksize = (*fd).memio_buffer_handler.cur_sw_addr - next_hw_start_addr - (*fd).memio_hw_settings.wordsize;
        }
        /*
         * HW module cannot perform address jumps. Thus, only a continuous memory area can
         * be written. Any write operation must not exceed the buffer limit and the HW
         * pointer has to point to a valid buffer address. Therefore check if the SW
         * pointer is at the start address of the buffer and a safety distance has to
         * be kept.
         */
        else if((*fd).memio_buffer_handler.cur_sw_addr == (*fd).memio_buffer_handler.buffer_baseaddr_virt) {
            next_hw_blocksize = (*fd).memio_buffer_handler.buffer_baseaddr_virt + (*fd).memio_buffer_handler.buffer_size -
                    next_hw_start_addr - (*fd).memio_hw_settings.wordsize;
        }
        /* Let HW write until end of as_memio buffer in all other cases */
        else {
            next_hw_blocksize = (*fd).memio_buffer_handler.buffer_baseaddr_virt + (*fd).memio_buffer_handler.buffer_size -
                    next_hw_start_addr;
        }

        /* Ensure block size being a multiple of transfer size to prevent data loss due to too short hw write requests */
        next_hw_blocksize = (next_hw_blocksize - (next_hw_blocksize%(*fd).memio_buffer_handler.transfer_size));
        /* Update HW address and blocksize for next write request (of HW) */
        (*fd).memio_buffer_handler.cur_hw_blocksize = next_hw_blocksize;
        (*fd).memio_buffer_handler.cur_hw_start_addr = next_hw_start_addr;

        /*
         * Setup next write request if blocksize is not 0. Otherwise skip setup and try again on next
         * call of this function.
         */
        if((*fd).memio_buffer_handler.cur_hw_blocksize != 0) {
            /* Invalidate Cache in order to clear outdated data and set start address for next read operation */
#if AS_OS_LINUX_KERNEL
            if((*fd).memio_hw_settings.manage_cache) {
                outer_inv_range(virt_to_phys((volatile void*)(*fd).memio_buffer_handler.buffer_baseaddr_virt), 
                                virt_to_phys((volatile void*)(*fd).memio_buffer_handler.buffer_baseaddr_virt + (*fd).memio_buffer_handler.buffer_size));
            }
            as_reader_writer_set_section_addr((*fd).memio_hw_settings.baseaddr,(uint32_t*)virt_to_phys((volatile void*)(*fd).memio_buffer_handler.cur_hw_start_addr));
#else /* AS_OS_NONE */
            if((*fd).memio_hw_settings.manage_cache) {
                as_dcache_invalidate_range(((volatile void*)(*fd).memio_buffer_handler.cur_hw_start_addr), (*fd).memio_buffer_handler.cur_hw_blocksize);
            }
            as_reader_writer_set_section_addr((*fd).memio_hw_settings.baseaddr,(uint32_t*)(*fd).memio_buffer_handler.cur_hw_start_addr);
#endif
            /* Set blocksize in byte! (Required by HW module) */
            as_reader_writer_set_section_size((*fd).memio_hw_settings.baseaddr, (*fd).memio_buffer_handler.cur_hw_blocksize);
            /* Start as_memwriter */
            as_reader_writer_set_go((*fd).memio_hw_settings.baseaddr);
        }
    }

    /* Update HW address */
    temp_addr = (uint8_t*)as_reader_writer_get_cur_hw_addr((*fd).memio_hw_settings.baseaddr);
    if(temp_addr == 0) {
        temp_addr = (*fd).memio_buffer_handler.buffer_baseaddr_phys;
    }
    (*fd).memio_buffer_handler.cur_hw_addr = (uint8_t*)((uint32_t)(*fd).memio_buffer_handler.buffer_baseaddr_virt + 
                                              ((uint32_t)temp_addr) - (uint32_t)(*fd).memio_buffer_handler.buffer_baseaddr_phys);

    /*
     * Set HW address (as_memio) to buffer start address if no go signal has been set yet (default HW register value
     * is 0x0 after reset) or if HW pointer is out of buffer scope.
     */
    if(((*fd).memio_buffer_handler.cur_hw_addr == 0) || ((*fd).memio_buffer_handler.cur_hw_addr ==
                ((*fd).memio_buffer_handler.buffer_baseaddr_virt + (*fd).memio_buffer_handler.buffer_size)))
    {
        (*fd).memio_buffer_handler.cur_hw_addr = (*fd).memio_buffer_handler.buffer_baseaddr_virt;
    }
}

void as_memio_hw_update(as_memio_file_t* fd) {
    if ((*fd).memio_hw_settings.read_not_write == AS_TRUE) {
        as_memio_hw_read_update(fd);
    }
    else {/* read_not_write is AS_FALSE */
        as_memio_hw_write_update(fd);
    }
}

uint32_t as_memio_read(as_memio_file_t* fd, void* buffer, uint32_t count) {

    /* Temporary variables used for copying data */
    uint32_t bytes_to_read = 0;
    uint32_t bytes_available = 0;
    uint32_t bytes_to_copy = 0;
    uint32_t not_copied = 0;
    uint8_t *dst = NULL;
    uint8_t *src = NULL;
#if AS_OS_NONE
    uint32_t n = 0;
#endif

    /* Configure HW if possible and update HW address */
    as_memio_hw_read_update(fd);

    /* Calculate the number of bytes currently available in as_memio buffer */
    if((*fd).memio_buffer_handler.cur_sw_addr != (*fd).memio_buffer_handler.cur_hw_addr) {
        bytes_available = ((uint32_t)(*fd).memio_buffer_handler.cur_hw_addr - (uint32_t)(*fd).memio_buffer_handler.cur_sw_addr +
                          (*fd).memio_buffer_handler.buffer_size) % (*fd).memio_buffer_handler.buffer_size;
    }
    /* as_memio buffer is considered empty if HW and SW address are equal */
    else    {
        bytes_available = 0;
    }

    /* Choose the smaller number of bytes */
    bytes_to_read = (bytes_available > count) ? count : bytes_available;
    

    /* Copy buffer (from user) and SW address to temporary variables for copy process */
    src = (uint8_t*)(*fd).memio_buffer_handler.cur_sw_addr;
    dst = (uint8_t*)buffer;
    
    /*
     * If the number of words fit into the remaining as_memio buffer no further overhead is needed, copy everything
     * until done.
     */
    if(((*fd).memio_buffer_handler.cur_sw_addr + bytes_to_read) <= ((*fd).memio_buffer_handler.buffer_baseaddr_virt + (*fd).memio_buffer_handler.buffer_size)) {
        bytes_to_copy = bytes_to_read;
#if AS_OS_LINUX_KERNEL
        not_copied = copy_to_user((void*)dst, (const void*)src, bytes_to_copy);
        src = src + (bytes_to_copy - not_copied);
#else /* AS_OS_NONE */

        /* Copy all bytes from memio buffer to user buffer */
        for(n = bytes_to_copy; n > 0; n--) {
            *dst++ = *src++;
        }
#endif
    }
    
    /* Otherwise split data copy operation to remaining as_memio buffer and continue at the beginning of the buffer */
    else {
        bytes_to_copy = ((*fd).memio_buffer_handler.buffer_baseaddr_virt + (*fd).memio_buffer_handler.buffer_size - (*fd).memio_buffer_handler.cur_sw_addr);
#if AS_OS_LINUX_KERNEL
        not_copied = copy_to_user(dst, src, bytes_to_copy);
        src = src + (bytes_to_copy - not_copied);
        dst = dst + (bytes_to_copy - not_copied);
#else /* AS_OS_NONE */
        for(n = bytes_to_copy; n > 0; n--) {
            *dst++ = *src++;
        }
#endif

        bytes_to_copy = (bytes_to_read - ((*fd).memio_buffer_handler.buffer_baseaddr_virt + (*fd).memio_buffer_handler.buffer_size - (*fd).memio_buffer_handler.cur_sw_addr));
        if(not_copied) {
            not_copied = bytes_to_copy + not_copied;
        }
       
#if AS_OS_LINUX_KERNEL
        /* Only try to copy remaining bytes from the buffer if the previous copy was successful */
        if(!not_copied) {
            src = (uint8_t*)(*fd).memio_buffer_handler.buffer_baseaddr_virt;
            not_copied = copy_to_user(dst, src, bytes_to_copy);
            src = src + (bytes_to_copy - not_copied);
        }
#else /* AS_OS_NONE */
        src = (uint8_t*)(*fd).memio_buffer_handler.buffer_baseaddr_virt;
        for(n = bytes_to_copy; n > 0; n--) {
            *dst++ = *src++;
        }
#endif
    }

    /* Update SW address by copying temporary variable back to SW address */
    (*fd).memio_buffer_handler.cur_sw_addr = (src >= ((*fd).memio_buffer_handler.buffer_baseaddr_virt + 
                                              (*fd).memio_buffer_handler.buffer_size)) ? (*fd).memio_buffer_handler.buffer_baseaddr_virt : src;

    /* Return the number of bytes which were copied */
    return bytes_to_read - not_copied;
}

uint32_t as_memio_write(as_memio_file_t* fd, const void * buffer, uint32_t count) {

    /* Temporary variables used for copying data */
    uint32_t bytes_to_write = 0;
    uint32_t bytes_available = 0;
    uint32_t bytes_to_copy = 0;
    uint32_t not_copied = 0;
    uint8_t *dst = NULL;
    uint8_t *src = NULL;
#if AS_OS_NONE
    uint32_t n = 0;
#endif
    
#if AS_OS_LINUX_KERNEL
    // TBD: print warning concerning requested amount of data
#else /* AS_OS_NONE */
    // TBD: print warning concerning requested amount of data
#endif

    /* Get the number of available bytes while keeping safety distance to HW pointer */
    bytes_available = ((*fd).memio_buffer_handler.cur_hw_addr - ((*fd).memio_buffer_handler.cur_sw_addr + (*fd).memio_hw_settings.wordsize) +
                       (*fd).memio_buffer_handler.buffer_size) % (*fd).memio_buffer_handler.buffer_size;

    /* Choose the smaller number of words for copying to buffer */
    bytes_to_write = (bytes_available > count) ? count : bytes_available;
    
    /* copy buffer (from user) and SW address to temporary variables for copy process */
    src = (uint8_t*)buffer;
    dst = (uint8_t*)(*fd).memio_buffer_handler.cur_sw_addr;

    /*
     * If the number of words fit into the remaining as_memio buffer no further overhead is needed, copy everything
     * until done.
     */
    if(((*fd).memio_buffer_handler.cur_sw_addr + bytes_to_write) <= ((*fd).memio_buffer_handler.buffer_baseaddr_virt + (*fd).memio_buffer_handler.buffer_size)) {
        bytes_to_copy = bytes_to_write;
#if AS_OS_LINUX_KERNEL
        not_copied = copy_from_user((void*)dst, (const void*)src, bytes_to_copy);
        dst = dst + (bytes_to_copy - not_copied);
#else /* AS_OS_NONE */
        for(n = bytes_to_copy; n > 0; n--) {
            *dst++ = *src++;
        }
#endif
    }
    
    /* Otherwise split data copy operation to remaining as_memio buffer and continue at the beginning of the buffer */
    else {
        bytes_to_copy = ((uint32_t)(*fd).memio_buffer_handler.buffer_baseaddr_virt + (*fd).memio_buffer_handler.buffer_size - (uint32_t)(*fd).memio_buffer_handler.cur_sw_addr);
    
#if AS_OS_LINUX_KERNEL
        not_copied = copy_from_user(dst, src, bytes_to_copy);
        dst = dst + (bytes_to_copy - not_copied);
        src = src + (bytes_to_copy - not_copied);
#else /* AS_OS_NONE */
        for(n = bytes_to_copy; n > 0; n--) {
            *dst++ = *src++;
        }
#endif
        
        bytes_to_copy = (bytes_to_write - ((uint32_t)(*fd).memio_buffer_handler.buffer_baseaddr_virt + (*fd).memio_buffer_handler.buffer_size - (uint32_t)(*fd).memio_buffer_handler.cur_sw_addr));
        if(not_copied) {
            not_copied = bytes_to_copy + not_copied;
        }
        
#if AS_OS_LINUX_KERNEL
        /* Only try to copy remaining bytes from the buffer if the previous copy was successful */
        if(!not_copied) {
            dst = (uint8_t*)(*fd).memio_buffer_handler.buffer_baseaddr_virt;
            not_copied = copy_from_user(dst, src, bytes_to_copy);
            dst = dst + (bytes_to_copy - not_copied);
        }
#else /* AS_OS_NONE */
        dst = (uint8_t*)(*fd).memio_buffer_handler.buffer_baseaddr_virt;
        for(n = bytes_to_copy; n > 0; n--) {
            *dst++ = *src++;
        }
#endif
    }
    
    /*
     * Force write-back of copied data from user space to ensure HW module having valid data (if
     * HW module does not perform cache coherent memory access).
     */
    if((*fd).memio_hw_settings.manage_cache) {
#if AS_OS_LINUX_KERNEL
        /* Flush L1 Cache content into L2 */
        __cpuc_flush_dcache_area((void*)(*fd).memio_buffer_handler.buffer_baseaddr_virt, (*fd).memio_buffer_handler.buffer_size);
        /* Flush L2 Cache to memory */
        outer_flush_range(virt_to_phys((*fd).memio_buffer_handler.buffer_baseaddr_virt), virt_to_phys((*fd).memio_buffer_handler.buffer_baseaddr_virt + (*fd).memio_buffer_handler.buffer_size));
#else /* AS_OS_NONE */
        as_dcache_flush_range(((volatile void*)(*fd).memio_buffer_handler.cur_hw_start_addr), (*fd).memio_buffer_handler.cur_hw_blocksize);
#endif
    }

    /* Update SW address by copying temporary variable back to SW address */
    (*fd).memio_buffer_handler.cur_sw_addr = (dst >= ((*fd).memio_buffer_handler.buffer_baseaddr_virt + 
                                              (*fd).memio_buffer_handler.buffer_size)) ? (*fd).memio_buffer_handler.buffer_baseaddr_virt : dst;

    /* Configure HW if possible and update HW address */
    as_memio_hw_write_update(fd);

    /* Return the number of bytes which were copied */
    return bytes_to_write - not_copied;
}

void as_memio_close(as_memio_file_t* fd) {
    if(fd != NULL) {
        if((*fd).memio_hw_settings.baseaddr !=NULL) {
            as_reader_writer_reset((*fd).memio_hw_settings.baseaddr);
            as_free((*fd).memio_buffer_handler.buffer_baseaddr_virt );
        }
        as_free(fd);
    }
}

