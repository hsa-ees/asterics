#pragma once

/** @file as_buffer.h
 *  @brief Header filer containing structure definitions for use of ASTERICS buffer objects
 * @addtogroup as_driver
 * @{
 *   @defgroup as_buffer
 *   @{
 */

// Typedefs
typedef struct as_buffer_obj_s as_buffer_obj_t;
/** Index used to retrieve buffer object in a safe way */
typedef uint32_t as_buffer_obj_handle_t;

/** This enum defines where the user wishes the buffer
 * to reside */
typedef enum as_buffer_type_e {
  /** Buffer resides purely in Kernel memory */
  AS_BUFFER_KERN_MEM,
  /** Buffer resides in user memory and needs to be copied */
  AS_BUFFER_USER_MEM
} as_buffer_type_t;

typedef enum as_buffer_dir_e {
  // CPU Write
  AS_BUFFER_DIR_TO_DEV,
  // CPU Read
  AS_BUFFER_DIR_FROM_DEV
} as_buffer_dir_t;

/** Buffer configuration struct */
typedef struct as_buffer_config_s {
  /** Virtual address provided when buffer in user memory */
  as_virtual_address_t address;
  /** Size of the buffer to be created */
  size_t size;
  /** Location of buffer */
  as_buffer_type_t type;
} as_buffer_config_t;

#if !AS_OS_POSIX
/** Queue used to handle transfers of buffers */
typedef struct as_buffer_obj_queue_s {
  /** Reference to elements on queue */
  as_buffer_obj_t *elements[2];
  /** Maximum storage capacity of queue */
  size_t count;
} as_buffer_obj_queue_t;

/** Identifies the current state this buffer (object) is in */
typedef enum as_buffer_state_e {
  /** Buffer is not allocated */
  AS_BUFFER_STATE_UNALLOCATED,

  /** Buffer is not currently in use by any hardware */
  AS_BUFFER_STATE_INACTIVE,
  /** Buffer is configured by software and waiting for action */
  AS_BUFFER_STATE_WAITING,
  /** Buffer is currently in use by ASTERICS */
  AS_BUFFER_STATE_OWN_DEVICE,
  /** Buffer is currently in use by CPU */
  AS_BUFFER_STATE_OWN_CPU,
} as_buffer_state_t;

/** Internal struct that keeps track of various states of the buffer */
typedef struct as_buffer_obj_s {
  /** Physical address to be used by ASTERICS */
  as_hardware_address_t buffer_baseaddr_phys;
  /** Virtual address to be used by CPU */
  as_kernel_address_t buffer_baseaddr_virt;
  /** Virtual user address used only for tracking */
  as_virtual_address_const_t buffer_baseaddr_user;
  /** Buffer size of currently managed buffer */
  uint32_t buffer_size;
  /** Actual amount of bytes to transfer/transferred (depending on state) */
  uint32_t transfer_size;
  /** Where ASTERICS currently is as a virtual address */
  uint8_t *cur_hw_addr;
  /** Where CPU is in Kernel Virtual Address Space */
  uint8_t *cur_sw_addr;
  // This is obsoleted as no partial reads will happen
  // uint8_t * cur_hw_start_addr;
  // cur_hw_blocksize as well
  as_buffer_state_t state;
  /** Direction of transfer */
  as_buffer_dir_t direction;
#if AS_OS_LINUX_KERNEL
  /** Handle to be used when (un-)mapping device for DMA */
  dma_addr_t dma_addr;
#endif
} as_buffer_obj_t;
#endif

// Defines
/** Invalid buffer object handle, returned on error */
#define AS_BUFFER_OBJ_INVALID (as_buffer_obj_handle_t)(-1)

// Functions

/** @name Buffer object lifetime 
 *  @{*/
#if AS_OS_POSIX
as_buffer_obj_handle_t as_buffer_obj_create(as_buffer_config_t *config);
void as_buffer_obj_destroy(as_buffer_obj_handle_t object);

static inline AS_BOOL as_buffer_obj_is_valid(as_buffer_obj_handle_t object) {
  return (object < 0) ? AS_FALSE : AS_TRUE;
}
#else
as_buffer_obj_t *as_buffer_obj_create(as_buffer_config_t *config);
void as_buffer_obj_destroy(as_buffer_obj_t *object);
/** @}*/

/** @name Safety operations
 *  @{*/
static inline AS_BOOL as_buffer_obj_is_valid(as_buffer_obj_t *object) {
  return (object == 0) ? AS_FALSE : AS_TRUE;
}

as_buffer_obj_handle_t as_buffer_obj_ptr_to_handle(as_buffer_obj_t *object);
as_buffer_obj_t *as_buffer_obj_handle_to_ptr(as_buffer_obj_handle_t handle);
/** @}*/

/** @name Buffer Queue operations
 *  @{*/
void as_buffer_queue_init(as_buffer_obj_queue_t *queue, size_t count);
as_buffer_obj_t *as_buffer_find_inactive_buffer(as_buffer_obj_t **buf,
                                                size_t count);
as_buffer_obj_t *as_buffer_find_waiting_buffer(as_buffer_obj_t **buf,
                                               size_t count);
AS_BOOL as_buffer_enqueue(as_buffer_obj_queue_t *queue, as_buffer_obj_t *buf);
as_buffer_obj_t *as_buffer_dequeue(as_buffer_obj_queue_t *queue);
as_buffer_obj_t *as_buffer_inspect(as_buffer_obj_queue_t *queue);

void as_buffer_update_state(as_buffer_obj_t *buf, as_hardware_address_t module_address, AS_BOOL supports_data_unit, AS_BOOL manage_cache);
void as_buffer_print_all(as_buffer_obj_queue_t *queue);
#endif
/** @}*/
/** @} defgroup */
/** @} addtogroup */ 
