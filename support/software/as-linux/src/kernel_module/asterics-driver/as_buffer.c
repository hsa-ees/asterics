#include "as_support.h"
#include "as_buffer.h"
// TODO: Required only for update_state function
#include "as_reader_writer.h"
#include "as_cache.h"

/** @file as_buffer.c
 *  @brief Buffer implementation file
 * 
 * 
 */

#if AS_OS_LINUX_KERNEL
extern struct device *asterics_device;
#include <linux/dma-mapping.h>
#include <linux/dma-direction.h>
#include "trace_events_asterics.h"
#endif

#if !AS_OS_POSIX
/** Object containing managing the lifetime and configuration of the buffers */
typedef struct as_buffer_manager_ctx_s {
  as_buffer_obj_t buffers[16];
  size_t available_buffers;
} as_buffer_manager_ctx_t;

/** Singleton manager inside driver as of now */
as_buffer_manager_ctx_t as_buffer_manager_ctx = {.available_buffers = 16};

/** Creates a new buffer object
 * @param[in] config contains the requested configuration 
 * @return pointer to new object
 * @note No memory was allocated when null-pointer returned*/
as_buffer_obj_t *as_buffer_obj_create(as_buffer_config_t *config) {
  int i;
  as_buffer_obj_t *object = NULL;
  for (i = 0; i < as_buffer_manager_ctx.available_buffers; i++) {
    if (as_buffer_manager_ctx.buffers[i].state == AS_BUFFER_STATE_UNALLOCATED) {
      object = &as_buffer_manager_ctx.buffers[i];
      object->buffer_size = config->size;
      object->buffer_baseaddr_virt = as_malloc(object->buffer_size);
      if (object->buffer_baseaddr_virt == NULL)
        break; // Return with no object

      AS_INFO("Allocated buffer at baseaddr: %p\n", object->buffer_baseaddr_virt);
#if AS_OS_LINUX_KERNEL
      object->buffer_baseaddr_phys = virt_to_phys((volatile void *)object->buffer_baseaddr_virt);
#else
      object->buffer_baseaddr_phys = object->buffer_baseaddr_virt;
#endif
      object->state = AS_BUFFER_STATE_INACTIVE;
      break;
    }
  }
  return object;
}

/** Destroys a buffer object
 * @param[in] object to be destroyed */
void as_buffer_obj_destroy(as_buffer_obj_t *object) {
  if (object->buffer_baseaddr_virt) {
    as_free(object->buffer_baseaddr_virt);
    object->state = AS_BUFFER_STATE_UNALLOCATED;
  } else
    AS_WARNING("Tried to free null pointer %p\n", object);

  return;
}

/** Used in kernel space to create a handle from the internal object
 * @param[in] object
 * @return Implementation agnostic handle */
as_buffer_obj_handle_t as_buffer_obj_ptr_to_handle(as_buffer_obj_t *object) {
  int i;
  as_buffer_obj_handle_t handle = AS_BUFFER_OBJ_INVALID;
  for (i = 0; i < as_buffer_manager_ctx.available_buffers; i++) {
    if (&as_buffer_manager_ctx.buffers[i] == object) {
      handle = i;
    }
  }
  return handle;
}

/** Used in kernel space to find the internal object from a handle
 * @param[in] handle to be converted
 * @return Internal reference to buffer object */
as_buffer_obj_t *as_buffer_obj_handle_to_ptr(as_buffer_obj_handle_t handle) {
  int i;
  i = min(handle, as_buffer_manager_ctx.available_buffers - 1);
  if (i < 0) {
    return NULL;
  }

  return &as_buffer_manager_ctx.buffers[i];
}

// Internal functionality

/** Initialize buffer queue */
void as_buffer_queue_init(as_buffer_obj_queue_t *queue, size_t count) {
  int i;
  queue->count = count;
  for (i = 0; i < queue->count; i++) {
    queue->elements[i] = NULL;
  }
}

/** Find inactive buffer in array of buffer object pointers */
as_buffer_obj_t *as_buffer_find_inactive_buffer(as_buffer_obj_t **buf,
                                                size_t count) {
  as_buffer_obj_t *ptr = NULL;
  int i;
  for (i = 0; i < count; i++) {
    if (buf[i]->state == AS_BUFFER_STATE_INACTIVE) {
      ptr = buf[i];
      break;
    }
  }

  return ptr;
}

/** Find waiting buffer in array of buffer object pointers */
as_buffer_obj_t *as_buffer_find_waiting_buffer(as_buffer_obj_t **buf,
                                               size_t count) {
  as_buffer_obj_t *ptr = NULL;
  int i;
  for (i = 0; i < count; i++) {
    if (buf[i]->state == AS_BUFFER_STATE_WAITING) {
      ptr = buf[i];
      break;
    }
  }

  return ptr;
}

/** Find inactive buffer in array of buffer object pointers 
 * @todo Currently unused
*/
as_buffer_obj_t *as_buffer_find_buffer_in_range(as_buffer_obj_t **buf,
                                                size_t count, 
                                                as_hardware_address_t start, as_hardware_address_t end) {
  as_buffer_obj_t *ptr = NULL;
  int i;
  for (i = 0; i < count; i++) {
    if (buf[i]->buffer_baseaddr_phys >= start &&
        buf[i]->buffer_baseaddr_phys + buf[i]->buffer_size <= end) {
      ptr = buf[i];
      break;
    }
  }

  return ptr;
}

/** Add element to tail of queue */
AS_BOOL as_buffer_enqueue(as_buffer_obj_queue_t *queue, as_buffer_obj_t *buf) {
  AS_BOOL found = AS_FALSE;
  int i = 0;

  for (i = 0; i < queue->count; i++) {
    if (queue->elements[i] == NULL) {
      queue->elements[i] = buf;
      found = AS_TRUE;
      break;
    }
  }
  trace_asterics_enqueued(buf);
  return found;
}

/** Remove first element from queue */
as_buffer_obj_t *as_buffer_dequeue(as_buffer_obj_queue_t *queue) {
  int i;
  as_buffer_obj_t *buf = queue->elements[0];

  if (buf == NULL) {
    AS_ERROR("No element to dequeue\n");
  }

  // Move all elements down
  for (i = 1; i < queue->count; i++) {
    queue->elements[i - 1] = queue->elements[i];
  }

  queue->elements[queue->count - 1] = NULL;

  trace_asterics_dequeued(buf);
  return buf;
}

/** Inspect first element on queue */
as_buffer_obj_t *as_buffer_inspect(as_buffer_obj_queue_t *queue) {
  return queue->elements[0];
}

/** Checks if buffer is in an active transfer */
void as_buffer_update_state(as_buffer_obj_t *buf, as_hardware_address_t module_address, AS_BOOL supports_data_unit, AS_BOOL manage_cache) {
  as_hardware_address_t start = (as_hardware_address_t)buf->buffer_baseaddr_phys;
  as_hardware_address_t end = (as_hardware_address_t)buf->buffer_baseaddr_phys + buf->transfer_size;

  /* Get current operating address of HW module to update HW address of as_memio */
  as_hardware_address_t temp_addr = as_reader_writer_get_cur_hw_addr(module_address);
  if (temp_addr == 0) {
    temp_addr = buf->buffer_baseaddr_phys;
  }

  // If outside of bounds or not busy, transfer is finished
  if (temp_addr >= start && temp_addr <= end && as_reader_writer_is_busy(module_address)) {
    // AS_INFO("Incomplete read\n");
  } else {
    AS_INFO("Buffer complete (address is outside of buffer): %x\n", temp_addr);
    AS_INFO("Unmap buffers at: %x, %p\n", buf->dma_addr, buf->buffer_baseaddr_virt);
    as_unmap_single(buf->dma_addr, buf->buffer_size, buf->direction, manage_cache);
    if ((buf->direction == AS_BUFFER_DIR_FROM_DEV) && supports_data_unit) {
      buf->transfer_size = start - (as_hardware_address_t)as_writer_get_last_data_unit_complete_addr(module_address);
    }
    buf->dma_addr = 0;
    buf->state = AS_BUFFER_STATE_OWN_CPU;
  }
}

void as_buffer_print(as_buffer_obj_t *buf) {
  AS_INFO("Phys addr: %x\n", buf->buffer_baseaddr_phys);
  AS_INFO("State: %x\n", buf->state);
  AS_INFO("Transfer size: %x\n", buf->transfer_size);
}

/** Prints all buffers and their content */
void as_buffer_print_all(as_buffer_obj_queue_t *queue) {
  int i = 0;

  for (i = 0; i < queue->count; i++) {
    if (queue->elements[i] == NULL) {
      AS_INFO("Element %d empty", i);
    } else {
      as_buffer_print(queue->elements[i]);
    }
  }
  return;
}
#endif