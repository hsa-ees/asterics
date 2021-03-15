/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework.
--  Copyright (C) Hochschule Augsburg, University of Applied Sciences, All rights
--  reserved
----------------------------------------------------------------------------------
-- File:           as_memio.c
-- Module:         as_memio
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Author:         Julian Sarcher, Alexander Zoellner, Patrick Zacharias
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

#include "as_cache.h"
#if AS_OS_LINUX_KERNEL
#include <asm/cacheflush.h>
#include <asm/outercache.h>
#include "trace_events_asterics.h"
extern struct device *asterics_device;
#endif /* AS_OS_LINUX_KERNEL */

void as_memio_module_setup(as_memio_hw_settings_t *hw_settings) {
  if ((*hw_settings).baseaddr != 0) {
    /* HW module supports only 1 section for as_memio configuration */
    as_reader_writer_set_section_count((*hw_settings).baseaddr, 1);
    /* There is no section offset since there is only one section */
    as_reader_writer_set_section_offset((*hw_settings).baseaddr, 0);
    /* Set maximum possible burst length of HW module */
    as_reader_writer_set_max_burst_length((*hw_settings).baseaddr, (*hw_settings).burst_length);

    /* Bring HW module to defined state */
    as_reader_writer_reset((*hw_settings).baseaddr);

    /* Enable the memwriter module to receive data */
    if ((*hw_settings).read_not_write == AS_TRUE) {
      as_writer_set_enable((*hw_settings).baseaddr);
    }
  }
}

void as_memio_config_init(as_memio_config_t *memio_config) {
  /* Set default values for using as_memwriter with as_memio */
  (*memio_config).as_reader_writer_buffer_size = AS_MEMIO_DEFAULT_FIFO_BUFFER_SIZE;      /* as_memio buffer_size in words */
  (*memio_config).as_reader_writer_transfer_size = AS_MEMIO_DEFAULT_HW_TRANSFER_SIZE;    /* minimum data to transfer on single read request */
  (*memio_config).as_reader_writer_max_burst_length = AS_MEMIO_DEFAULT_MAX_BURST_LENGTH; /* max_burst_length in Bytes */
  (*memio_config).as_reader_writer_interface_width = AS_MEMIO_DEFAULT_INTERFACE_WIDTH;
  (*memio_config).manage_cache = AS_MEMIO_DEFAULT_MANAGE_CACHE;
}

static void print_memio_config(as_memio_config_t *memio_config) {
  AS_INFO("MEMIO_CONFIG at %p:\n", memio_config);
  AS_INFO("as_reader_writer_buffer_size: %x\n", memio_config->as_reader_writer_buffer_size);
  AS_INFO("as_reader_writer_interface_width: %x\n", memio_config->as_reader_writer_interface_width);
  AS_INFO("as_reader_writer_max_burst_length: %x\n", memio_config->as_reader_writer_max_burst_length);
  AS_INFO("as_reader_writer_transfer_size: %x\n", memio_config->as_reader_writer_transfer_size);
  AS_INFO("manage_cache: %x\n", memio_config->manage_cache);
  AS_INFO("read_not_write: %x\n", memio_config->read_not_write);
}

static void print_buffer_handler(as_memio_buffer_handler_t *buffer_handle) {
  AS_INFO("as_memio_buffer_handler_t at %p:\n", buffer_handle);
  // AS_INFO("buffer_baseaddr_phys: %x\n", buffer_handler->buffer_baseaddr_phys);
  // AS_INFO("buffer_baseaddr_virt: %x\n", buffer_handler->buffer_baseaddr_virt);
  // AS_INFO("buffer_size: %x\n", buffer_handler->buffer_size);
  // AS_INFO("cur_hw_addr: %x\n", buffer_handler->cur_hw_addr);
  // AS_INFO("cur_hw_blocksize: %x\n", buffer_handler->cur_hw_blocksize);
  // AS_INFO("cur_hw_start_addr: %x\n", buffer_handler->cur_hw_start_addr);
  // AS_INFO("cur_sw_addr: %x\n", buffer_handler->cur_sw_addr);
  // AS_INFO("dma_addr: %x\n", buffer_handler->dma_addr);
  // AS_INFO("transfer_size: %x\n", buffer_handler->transfer_size);
}

static void print_hw_settings(as_memio_hw_settings_t *settings) {
  AS_INFO("as_memio_hw_settings_t at %p:\n", settings);
  AS_INFO("baseaddr: %x\n", settings->baseaddr);
  AS_INFO("burst_length: %x\n", settings->burst_length);
  AS_INFO("manage_cache: %x\n", settings->manage_cache);
  AS_INFO("read_not_write: %x\n", settings->read_not_write);
  AS_INFO("wordsize: %x\n", settings->wordsize);
}

/*
 * See annotation in as_memio.h
 */
as_memio_file_t *as_memio_open(as_hardware_address_t as_reader_writer_baseaddr, as_memio_config_t *memio_config, uint8_t flags) {
  as_memio_config_t memio_config_init;
  as_memio_file_t *fd = NULL;
  // Hardcode 1280*960 for now
  as_buffer_config_t config;
  config.size = 0x12c000;
  config.type = AS_BUFFER_KERN_MEM;

  if (memio_config == NULL) {
    as_memio_config_init(&memio_config_init);
  } else {
    memio_config_init = *memio_config;
  }

  print_memio_config(&memio_config_init);

  /* Create new structure for as_memio operations */
  fd = (as_memio_file_t *)as_malloc(sizeof(as_memio_file_t));
  if (fd == NULL) {
    return NULL;
  }


  fd->memio_buffer_handler.available_buffers = 0;

  /* Allocate memory for as_memio buffer */
  fd->memio_buffer_handler.buffers[0] = as_buffer_obj_create(&config);
  if (fd->memio_buffer_handler.buffers[0] == NULL) {
    AS_ERROR("Failed to allocate buffer 1\n");
    as_free(fd);
    return NULL;
  }
  fd->memio_buffer_handler.buffers[1] = as_buffer_obj_create(&config);
  if (fd->memio_buffer_handler.buffers[1] == NULL) {
    AS_ERROR("Failed to allocate buffer 2\n");
    as_buffer_obj_destroy(fd->memio_buffer_handler.buffers[0]);
    as_free(fd);
    return NULL;
  }
  fd->memio_buffer_handler.available_buffers = 2;
  as_buffer_queue_init(&fd->memio_buffer_handler.queue, 2);

  /* Memio config assignments */
  /* Set address of associated hardware module */
  fd->memio_hw_settings.baseaddr = as_reader_writer_baseaddr;
  /* Set burst length for hardware module */
  fd->memio_hw_settings.burst_length = (memio_config_init).as_reader_writer_max_burst_length;
  /* Set word size of associated hardware module */
  fd->memio_hw_settings.wordsize = (memio_config_init).as_reader_writer_interface_width / 8;
  /* Initialize as_memio for read operations if at least one of the following flags were provided */
  if ((flags & O_ACCMODE) == O_RDONLY) {
    fd->memio_hw_settings.read_not_write = AS_TRUE;
  }
  /* Initialize as_memio for write operations if at least one of the following flags were provided */
  else if ((flags & O_ACCMODE) == O_WRONLY) {
    fd->memio_hw_settings.read_not_write = AS_FALSE;
  } else {
    as_buffer_obj_destroy(fd->memio_buffer_handler.buffers[0]);
    as_buffer_obj_destroy(fd->memio_buffer_handler.buffers[1]);
    as_free(fd);
    return NULL;
  }
  fd->memio_hw_settings.manage_cache = (memio_config_init).manage_cache;

  print_buffer_handler(&fd->memio_buffer_handler);
  print_hw_settings(&fd->memio_hw_settings);
  /* Setup hardware modules for as_memio usage */
  as_memio_module_setup(&(fd->memio_hw_settings));

  /* Return the as_memio structure to caller for as_memio operations */
  return fd;
}

void as_memio_hw_write_update(as_memio_file_t *fd) {
  as_buffer_obj_t *buf = NULL;

  //AS_INFO("Call to hw write update\n");
  /* check if next go can already be accepted by hardware */
  if (as_reader_writer_is_pending_go(fd->memio_hw_settings.baseaddr) == AS_FALSE) {
    buf = as_buffer_find_waiting_buffer(fd->memio_buffer_handler.buffers, fd->memio_buffer_handler.available_buffers);
    if (buf != NULL) {
      buf->dma_addr = as_map_single(buf->buffer_baseaddr_virt, buf->buffer_size, AS_BUFFER_DIR_TO_DEV, fd->memio_hw_settings.manage_cache);
      /* Set start address for next write operation */
  #if AS_OS_LINUX_KERNEL
      AS_INFO("Set MEMREADER at %x to address %x, with size: %x", fd->memio_hw_settings.baseaddr,
              (unsigned int)virt_to_phys((volatile void *)buf->buffer_baseaddr_virt), buf->transfer_size);
      //AS_INFO("Buffer is %p\n", buf);
      as_reader_writer_set_section_addr(fd->memio_hw_settings.baseaddr, virt_to_phys((volatile void *)buf->buffer_baseaddr_virt));
  #else /* AS_OS_NONE */
      as_reader_writer_set_section_addr(fd->memio_hw_settings.baseaddr, fd->memio_buffer_handler.cur_hw_start_addr);
  #endif
      /* Set blocksize in byte! (Required by HW module) */
      as_reader_writer_set_section_size(fd->memio_hw_settings.baseaddr, buf->transfer_size);
      /* Start as_memreader */
      as_reader_writer_set_go(fd->memio_hw_settings.baseaddr);
      buf->state = AS_BUFFER_STATE_OWN_DEVICE;
      as_buffer_enqueue(&fd->memio_buffer_handler.queue, buf);
    }
  }

  // Check if there is a buffer that is ready to be transferred back to CPU
  buf = as_buffer_inspect(&fd->memio_buffer_handler.queue);
  //AS_INFO("Buffer %p\n", buf);
  if (buf != NULL && buf->state == AS_BUFFER_STATE_OWN_DEVICE) {
    as_hardware_address_t start = (as_hardware_address_t)buf->buffer_baseaddr_phys;
    as_hardware_address_t end = (as_hardware_address_t)buf->buffer_baseaddr_phys + buf->transfer_size;

    /* Get current operating address of HW module to update HW address of as_memio */
    as_hardware_address_t temp_addr = as_reader_writer_get_cur_hw_addr(fd->memio_hw_settings.baseaddr);
    if (temp_addr == 0) {
      temp_addr = fd->memio_buffer_handler.buffers[0]->buffer_baseaddr_phys;
    }

    // If outside of bounds or not busy, transfer is finished
    if (temp_addr >= start && temp_addr < end && as_reader_writer_is_busy(fd->memio_hw_settings.baseaddr)) {
      AS_INFO("Incomplete write\n");
    } else {
      AS_INFO("Buffer write complete (address is outside of buffer): %x\n", temp_addr);
      AS_INFO("Unmap buffers at: %x, %p\n", buf->dma_addr, buf->buffer_baseaddr_virt);
      as_unmap_single(buf->dma_addr, buf->buffer_size, AS_BUFFER_DIR_TO_DEV, fd->memio_hw_settings.manage_cache);
      buf->dma_addr = 0;
      buf->state = AS_BUFFER_STATE_OWN_CPU;
    }
  }
}

/** Transfer buffers to hardware if applicable
 *  @details If the hardware is able to receive a new buffer transfer request,
 *      this function looks for waiting buffers and if found transfers ownership
 *      to the hardware. 
 *  @param fd contains information about the current buffers for transfer
 */
void as_memio_hw_read_update(as_memio_file_t *fd) {
  as_buffer_obj_t *buf = NULL;

  /* Check if a new go signal can already be set */
  if (as_reader_writer_is_pending_go(fd->memio_hw_settings.baseaddr) == AS_FALSE) {
    buf = as_buffer_find_waiting_buffer(fd->memio_buffer_handler.buffers, fd->memio_buffer_handler.available_buffers);
    if (buf != NULL) {
      if (buf->buffer_size < buf->transfer_size) {
        //AS_ERROR("Tried to transfer more bytes than available\n");
        buf->transfer_size = buf->buffer_size;
      }
      AS_INFO("Set MEMWRITER at %x to address %x, with size: %x", fd->memio_hw_settings.baseaddr,
             (unsigned int)virt_to_phys((volatile void *)buf->buffer_baseaddr_virt), buf->buffer_size);
#if AS_OS_LINUX_KERNEL
      trace_asterics_start_transfer(buf->buffer_baseaddr_phys, as_reader_writer_get_cur_hw_addr(fd->memio_hw_settings.baseaddr));
      buf->dma_addr = as_map_single(buf->buffer_baseaddr_virt, buf->buffer_size, AS_BUFFER_DIR_FROM_DEV, fd->memio_hw_settings.manage_cache);
      as_reader_writer_set_section_addr(fd->memio_hw_settings.baseaddr, virt_to_phys((volatile void *)buf->buffer_baseaddr_virt));
#else /* AS_OS_NONE */
      if (fd->memio_hw_settings.manage_cache) {
        as_dcache_invalidate_range(((volatile void *)fd->memio_buffer_handler.cur_hw_start_addr), buf->transfer_size);
      }
      as_reader_writer_set_section_addr(fd->memio_hw_settings.baseaddr, fd->memio_buffer_handler.cur_hw_start_addr);
#endif
      /* Set blocksize in byte! (Required by HW module) */
      as_reader_writer_set_section_size(fd->memio_hw_settings.baseaddr, buf->transfer_size);
      /* Start as_memwriter */
      as_reader_writer_set_go(fd->memio_hw_settings.baseaddr);
      buf->state = AS_BUFFER_STATE_OWN_DEVICE;
      AS_BOOL success = as_buffer_enqueue(&fd->memio_buffer_handler.queue, buf);
      if (success == AS_FALSE) {
        AS_ERROR("Unable to add more transfers to queue\n");
      }
    }
  }

  // Check if there is a buffer that is ready to be transferred back to CPU
  buf = as_buffer_inspect(&fd->memio_buffer_handler.queue);
  if (buf != NULL && buf->state == AS_BUFFER_STATE_OWN_DEVICE) {
    as_hardware_address_t start = (as_hardware_address_t)buf->buffer_baseaddr_phys;
    as_hardware_address_t end = (as_hardware_address_t)buf->buffer_baseaddr_phys + buf->transfer_size;

    /* Get current operating address of HW module to update HW address of as_memio */
    as_hardware_address_t temp_addr = as_reader_writer_get_cur_hw_addr(fd->memio_hw_settings.baseaddr);
    if (temp_addr == 0) {
      temp_addr = fd->memio_buffer_handler.buffers[0]->buffer_baseaddr_phys;
    }

    // If outside of bounds or not busy, transfer is finished
    if (temp_addr >= start && temp_addr < end && as_reader_writer_is_busy(fd->memio_hw_settings.baseaddr)) {
      // AS_INFO("Incomplete read\n");
    } else {
      AS_INFO("Buffer complete (address is outside of buffer): %x for %x\n", temp_addr, buf->buffer_baseaddr_phys);
      AS_INFO("Unmap buffers at: %x, %p\n", buf->dma_addr, buf->buffer_baseaddr_virt);
      trace_asterics_finished_transfer(buf->buffer_baseaddr_phys, temp_addr);
      as_unmap_single(buf->dma_addr, buf->buffer_size, AS_BUFFER_DIR_FROM_DEV, fd->memio_hw_settings.manage_cache);
      buf->dma_addr = 0;
      buf->state = AS_BUFFER_STATE_OWN_CPU;
    }
  }
}

void as_memio_hw_update(as_memio_file_t *fd) {
  if (fd->memio_hw_settings.read_not_write == AS_TRUE) {
    as_memio_hw_read_update(fd);
  } else { /* read_not_write is AS_FALSE */
    as_memio_hw_write_update(fd);
  }
}

/** Copies bytes from a kernel virtual address to a user virtual address
 * @todo Don't copy byte by byte in bare-metal
 * @todo Add void typed for addresses so they can be used with const keyword */
static int as_copy_to_user(as_virtual_address_t dst, as_kernel_address_t src, unsigned long bytes_to_copy) {
  uint32_t not_copied = 0;
#if AS_OS_NONE
  uint32_t n = 0;
#endif

#if AS_OS_LINUX_KERNEL
  not_copied = copy_to_user((void *)dst, (const void *)src, bytes_to_copy);
  // AS_INFO("Not copied: %x\n", not_copied);
#else /* AS_OS_NONE */
  /* Copy all bytes from memio buffer to user buffer */
  for (n = bytes_to_copy; n > 0; n--) {
    *(uint8_t *)dst++ = *(uint8_t *)src++;
  }
#endif
  return bytes_to_copy - not_copied;
}

/** Copies bytes from a user virtual address to a kernel virtual address
 * @todo Don't copy byte by byte in bare-metal */
static int as_copy_from_user(as_kernel_address_t dst, as_virtual_address_const_t src, unsigned long bytes_to_copy) {
  uint32_t not_copied = 0;
#if AS_OS_NONE
  uint32_t n = 0;
#endif

#if AS_OS_LINUX_KERNEL
  not_copied = copy_from_user((void *)dst, (const void *)src, bytes_to_copy);
  // AS_INFO("Not copied: %x\n", not_copied);
#else /* AS_OS_NONE */
  /* Copy all bytes from memio buffer to user buffer */
  for (n = bytes_to_copy; n > 0; n--) {
    *(uint8_t *)dst++ = *(uint8_t *)src++;
  }
#endif
  return bytes_to_copy - not_copied;
}

ssize_t as_memio_read(as_memio_file_t *fd, void *buffer, uint32_t count) {
  /* Temporary variables used for copying data */
  uint8_t *dst = NULL;
  uint8_t *src = NULL;
#if AS_OS_NONE
  uint32_t n = 0;
#endif
  uint32_t copied = 0;
  // Is a buffer already waiting for it's transfer?
  AS_BOOL alreadyOnQueue = AS_FALSE;

  if (as_writer_is_sync_error(fd->memio_hw_settings.baseaddr)) {
    AS_ERROR("Tried to use MemWriter after sync error occured\n");
    return -ENODEV;
  }

  // AS_INFO("read: %x bytes\n", count);
  as_buffer_obj_t *buf = as_buffer_inspect(&fd->memio_buffer_handler.queue);
  if (buf != NULL) {
    if (buf->buffer_baseaddr_user == buffer) {
      alreadyOnQueue = AS_TRUE;
    }
  }

  // If this transfer isn't yet on queue, add it
  if (alreadyOnQueue == AS_FALSE && count > 0) {
    as_buffer_obj_t *wait_buf = as_buffer_find_inactive_buffer(fd->memio_buffer_handler.buffers, fd->memio_buffer_handler.available_buffers);
    if (wait_buf != NULL) {
      wait_buf->buffer_baseaddr_user = buffer;
      wait_buf->transfer_size = count;
      wait_buf->state = AS_BUFFER_STATE_WAITING;
    } else {
      return -EAGAIN;
    }
  }

  /* Start transfer and track progress */
  as_memio_hw_read_update(fd);

  /* Check if a completed object is on queue */
  buf = as_buffer_inspect(&fd->memio_buffer_handler.queue);

  if (buf != NULL) {
    if (buf->state == AS_BUFFER_STATE_OWN_CPU) {
      as_buffer_dequeue(&fd->memio_buffer_handler.queue);

      /* Copy buffer (from user) and SW address to temporary variables for copy
       * process */
      src = (uint8_t *)buf->buffer_baseaddr_virt;
      dst = (uint8_t *)buffer;

      copied = as_copy_to_user(dst, src, buf->transfer_size);
      AS_INFO("copied: %x\n", copied);
      buf->state = AS_BUFFER_STATE_INACTIVE;
    } else {
      return -EAGAIN;
    }
  }

  return copied;
}

ssize_t as_memio_write(as_memio_file_t *fd, const void *buffer, uint32_t count) {
  uint32_t copied = 0;
  AS_BOOL alreadyOnQueue = AS_FALSE;
  as_buffer_obj_t *buf = as_buffer_inspect(&fd->memio_buffer_handler.queue);
  if (buf != NULL) {
    if (buf->buffer_baseaddr_user == buffer) {
      alreadyOnQueue = AS_TRUE;
    }
  }

  if (alreadyOnQueue == AS_FALSE && count > 0) {
    as_buffer_obj_t *wait_buf = as_buffer_find_inactive_buffer(fd->memio_buffer_handler.buffers, fd->memio_buffer_handler.available_buffers);
    if (wait_buf == NULL) {
      AS_ERROR("Failed to find inactive buffer\n");
      return -EAGAIN;
    }

    wait_buf->buffer_baseaddr_user = buffer;

    // Copy as many bytes as possible
    if (wait_buf->buffer_size < count) {
        count = wait_buf->buffer_size;
    }
    wait_buf->transfer_size = as_copy_from_user(wait_buf->buffer_baseaddr_virt, buffer, count);
    if (wait_buf->transfer_size != 0) {
      wait_buf->state = AS_BUFFER_STATE_WAITING;
    }
  }

  // Initiate transfer and update state
  as_memio_hw_write_update(fd);

  /* Check if a completed object is on queue */
  buf = as_buffer_inspect(&fd->memio_buffer_handler.queue);

  if (buf != NULL) {
    if (buf->state == AS_BUFFER_STATE_OWN_CPU) {
      // Writing is done, dequeue object
      as_buffer_dequeue(&fd->memio_buffer_handler.queue);

      // AS_INFO("copied (write): %x\n", buf->transfer_size);
      copied = buf->transfer_size;
      buf->state = AS_BUFFER_STATE_INACTIVE;
    }
  }

  return copied;
}

void as_memio_close(as_memio_file_t *fd) {
  if (fd != NULL) {
    if (fd->memio_hw_settings.baseaddr != 0) {
      as_reader_writer_reset(fd->memio_hw_settings.baseaddr);
      as_buffer_obj_destroy(fd->memio_buffer_handler.buffers[0]);
      as_buffer_obj_destroy(fd->memio_buffer_handler.buffers[1]);
    }
    as_free(fd);
  }
}
