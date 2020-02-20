/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework and the VEARS core. 
--  Copyright (C) Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- File:           as_driver.c
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Author:         Alexander Zoellner
--
-- Modified:       
--
-- Description:    Source file of linux device driver for ASTERICS
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

/* Asterics header files */
#include "as_support.h"
#include "as_reader_writer.h"
#include "as_memio.h"

#include "as_driver.h"

#include <linux/fs.h>           /* file operations */
#include <linux/module.h>       /* module (de)initialization */
#include <linux/device.h>       /* device creation, memory regions, etc. */
#include <linux/mm.h>           /* mmap */

#include <asm/io.h>             /* ioread, -write */

/* Module information */

MODULE_AUTHOR("Alexander Zoellner");
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("ASTERICS driver");
MODULE_SUPPORTED_DEVICE("none");


/* Global Variables */

static struct timer_list interrupt_timer;             /* Timer for waking up sleeping io devices */
AS_BOOL timer_shutdown;                               /* Signal that timer is going to shutdown to prevent re-registering timer */

static dev_t first;                                 /* Global variable for the first device number */
static struct class *cl;                            /* Global variable for the device class */
static unsigned int initialized_devices = 0;        /* Number of devices currently in use */
static struct file_operations as_regio_fops;        /* Forward declaration */
static struct file_operations as_i2c_fops;          /* Forward declaration */
static struct file_operations as_memio_fops;        /* Forward declaration */
struct file_operations as_mmap_fops;                /* Forward declaration; Not static because file operations are overwritten */

/* Set pointers of device to NULL and disable interrupt handling for memio */
void set_device_defaults(unsigned int index);

/* Array containing the asterics devices */
static struct device_data_t device_data [MAX_DEVICES];

/* Work item for the shared work queue to be scheduled by the interrupt handler */
static struct work_struct timer_wq;
/* The task to be executed by the work queue */
void data_transfer_update_task(unsigned long arg);

/* Calculate the exponent to the base of 2 for a given number ( used for obtaining the order for __get_free_pages() )*/
int log2_ceil(unsigned long long size)
{
  static const unsigned long long t[6] = {
    0xFFFFFFFF00000000ull,
    0x00000000FFFF0000ull,
    0x000000000000FF00ull,
    0x00000000000000F0ull,
    0x000000000000000Cull,
    0x0000000000000002ull
  };

  int order = (((size & (size - 1)) == 0) ? 0 : 1);
  int j = 32;
  int i;

  for (i = 0; i < 6; i++) {
    int k = (((size & t[i]) == 0) ? 0 : j);
    order += k;
    size >>= k;
    j >>= 1;
  }

  return order;
}

/* This function is used to set the default parameters for the currently initialized device */
void set_device_defaults(unsigned int index) {
    device_data[index].req_mem_region_name = NULL;
    device_data[index].mmap = NULL;
    device_data[index].memio_file = NULL;
    atomic_set(&device_data[index].busy,1);
    device_data[index].register_intr = AS_FALSE;
    device_data[index].memio_active = AS_FALSE;
}

/******************* Ctrl device **************************************/

static long as_control_ioctl(struct file *f, unsigned int ioctl_num, unsigned long ioctl_param) {
  
    as_ctrl_params_t as_ctrl_params;
    int device_index;
    uint32_t addr;
    int ret_val = 0;

    as_mutex_lock(device_data[0].access_lock);

    if (ioctl_num != CALLED_FROM_KERNEL) {
        if (copy_from_user(&as_ctrl_params, (void *)ioctl_param, sizeof(as_ctrl_params_t)) != 0) {
            printk(KERN_ALERT "error: copy_from_user in as_control_ioctl\n");
            return ret_val = -1;
            goto control_exit;
        }
    }else {
        as_ctrl_params.cmd = (*(as_ctrl_params_t*)ioctl_param).cmd;
        strcpy(as_ctrl_params.dev_name, (*(as_ctrl_params_t*)ioctl_param).dev_name);
        as_ctrl_params.dev_type = (*(as_ctrl_params_t*)ioctl_param).dev_type;
        as_ctrl_params.dev_address = (*(as_ctrl_params_t*)ioctl_param).dev_address;
        as_ctrl_params.address_range_size = (*(as_ctrl_params_t*)ioctl_param).address_range_size;
        as_ctrl_params.interface_width = (*(as_ctrl_params_t*)ioctl_param).interface_width;
        as_ctrl_params.flags = (*(as_ctrl_params_t*)ioctl_param).flags;
        as_ctrl_params.manage_cache = (*(as_ctrl_params_t*)ioctl_param).manage_cache;
    }
   
    switch (as_ctrl_params.cmd) {
        case CMD_CREATE_DEVICE:
            if (initialized_devices >= MAX_DEVICES) {
                printk(KERN_ALERT "error: Maximum number of devices reached. Device not created.\n");
                ret_val = -EUSERS;
                goto control_exit;
            } 
            
            /* Set pointer to NULL and variables to 0 */
            set_device_defaults(initialized_devices);
            
            switch (as_ctrl_params.dev_type) {
            /* link file operations with device type... */
                case DEV_TYPE_REGIO:
                    printk(KERN_INFO "info: Creating DEV_TYPE_REGIO\n");
                    device_data[initialized_devices].fops = &as_regio_fops;
                    device_data[initialized_devices].req_mem_region_name = "as_regio";
                    break;
                case DEV_TYPE_I2C:
                    printk(KERN_INFO "info: Creating DEV_TYPE_I2C\n");              
                    device_data[initialized_devices].fops = &as_i2c_fops;
                    device_data[initialized_devices].req_mem_region_name = "as_iic";
                    break;          
                case DEV_TYPE_MEMIO:
                    printk(KERN_INFO "info: Creating DEV_TYPE_MEMIO\n");
                    device_data[initialized_devices].fops = &as_memio_fops;
                    break;
                case DEV_TYPE_MMAP:
                    printk(KERN_INFO "info: Creating DEV_TYPE_MMAP\n");
                    device_data[initialized_devices].fops = &as_mmap_fops;
                    break;
                default:
                    ret_val = -EINVAL;
                    goto control_exit;
            }   
            
            /* Adopt device flags for open */
            device_data[initialized_devices].flags = as_ctrl_params.flags;
            /* Adopt bit width of the memory interface */
            device_data[initialized_devices].interface_width = as_ctrl_params.interface_width;
            /* Adopt cache management */
            device_data[initialized_devices].manage_cache = as_ctrl_params.manage_cache;
            
            /* create device */
            device_data[initialized_devices].address_range_size = as_ctrl_params.address_range_size;
            cdev_init(&device_data[initialized_devices].cdev, device_data[initialized_devices].fops);   /* cdev_init has no return value */
            /* Devices with no region name (memio, mmap) */
            if (device_data[initialized_devices].req_mem_region_name == NULL) {
                device_data[initialized_devices].hw_module_addr = as_ctrl_params.dev_address;
                if(as_ctrl_params.dev_type == DEV_TYPE_MMAP) {
                    device_data[initialized_devices].mmap = as_malloc(sizeof(mmap_info_t));
                    if(!device_data[initialized_devices].mmap) {
                        ret_val = -ENOMEM;
                        goto control_exit;
                    }
                    device_data[initialized_devices].mmap->size = as_ctrl_params.address_range_size;
                    (*device_data[initialized_devices].mmap).page_allocation_order = log2_ceil(as_ctrl_params.address_range_size) - log2_ceil(PAGE_SIZE);
//                    (*device_data[initialized_devices].mmap).data = (void*)__get_free_pages(GFP_KERNEL, ((*device_data[initialized_devices].mmap).page_allocation_order));
                    device_data[initialized_devices].mmap->data = as_malloc(as_ctrl_params.address_range_size);
                    if(!(*device_data[initialized_devices].mmap).data) {
                        as_free(device_data[initialized_devices].mmap);
                        ret_val = -ENOMEM;
                        goto control_exit;
                    }
                    /* Setup wait queue for sleeping */
                    init_waitqueue_head (&device_data[initialized_devices].wait);
                    /* Set condition variable to 0 (is set to 1 by interrupt routine) */
                    device_data[device_index].wake_up_cond = 0;
                }
            }
            /* Device which needs a named memory region (iic, regio_global) */
            else { 
                if (NULL == (request_mem_region((resource_size_t)as_ctrl_params.dev_address, as_ctrl_params.address_range_size, \
                    device_data[initialized_devices].req_mem_region_name))) {
                    printk( KERN_ALERT "error: Kernel function request_mem_region failed. Device not created.\n");
                    device_destroy (cl, MKDEV(MAJOR(first), MINOR(first) + initialized_devices));
                    ret_val = -1;
                    goto control_exit;
                }
                if (NULL == (device_data[initialized_devices].baseaddress_virt = \
                    ioremap ((resource_size_t)as_ctrl_params.dev_address, as_ctrl_params.address_range_size))) {
                    printk( KERN_ALERT "error: Kernel function ioremap failed. Device not created.\n");
                    release_mem_region((resource_size_t)as_ctrl_params.dev_address, as_ctrl_params.address_range_size);
                    device_destroy (cl, MKDEV(MAJOR(first), MINOR(first) + initialized_devices));
                    ret_val = -1;
                    goto control_exit;
                }       
                device_data[initialized_devices].offset = (uint32_t)device_data[initialized_devices].baseaddress_virt - \
                (uint32_t)as_ctrl_params.dev_address;
            }
      
            if (cdev_add(&device_data[initialized_devices].cdev, MKDEV(MAJOR(first), MINOR(first) + initialized_devices), 1) == -1){
                printk( KERN_ALERT "error: Kernel function cdev_add failed. Device not created.\n");
                /* TBD: differenciate between memiodevice and regdevice */
                iounmap(as_ctrl_params.dev_address);
                release_mem_region((resource_size_t)as_ctrl_params.dev_address, as_ctrl_params.address_range_size);
                device_destroy (cl, MKDEV(MAJOR(first), MINOR(first) + initialized_devices));
                ret_val = -1;
                goto control_exit;
            }
            device_data[initialized_devices].access_lock = as_mutex_new ();
            printk(KERN_INFO "info: Device %s created sucessfully at address 0x%x with range: 0x%x \n", \
            as_ctrl_params.dev_name, (unsigned int)as_ctrl_params.dev_address, as_ctrl_params.address_range_size);
            initialized_devices++;
            break;
        case CMD_REMOVE_DEVICE:
            /* Remove every device except the control device (which is required for creating new devices) */
            for ( device_index = 1; device_index < initialized_devices; device_index++) { 
                cdev_del(&device_data[device_index].cdev);
                addr = (uint32_t)device_data[device_index].baseaddress_virt - (uint32_t)device_data[device_index].offset;
                if (device_data[device_index].req_mem_region_name != NULL) {
                    iounmap((volatile void*)addr);
                    release_mem_region((resource_size_t)addr, device_data[device_index].address_range_size);
                }
                if(device_data[device_index].mmap != NULL) {
                    as_free((*device_data[device_index].mmap).data);
//                    free_pages((unsigned long)(*device_data[device_index].mmap).data, ((*device_data[initialized_devices].mmap).page_allocation_order));
                    as_free(device_data[device_index].mmap);
                }
                as_mutex_del(device_data[device_index].access_lock);
                device_destroy (cl, MKDEV(MAJOR(first), MINOR(first) + device_index));
            } 
            initialized_devices = 1;
            break;
        default:
            printk(KERN_WARNING "warning: Undefined parameter in as_control_ioctl\n");
            break;
    } 
    
    printk(KERN_INFO "info: Initialized devices: %i\n", initialized_devices);

control_exit: 

    as_mutex_unlock(device_data[0].access_lock);
    return ret_val;
    /*
    To obtain the major or minor parts of a dev_t, use:
    MAJOR(dev_t dev);
    MINOR(dev_t dev);
    If, instead, you have the major and minor numbers and need to turn them into a dev_t, use:
    MKDEV(int major, int minor);
    device_create(cl, NULL, MKDEV(MAJOR(first), MINOR(first) + device_index), NULL, "mynull%d", device_index);
    */
}


/******************* Register IO (regio) ******************************/


long as_regio_ioctl(struct file *filp, unsigned int ioctl_num, unsigned long ioctl_param) {
    uint32_t val;
    uint32_t regio_offset = 0;
    as_ioctl_params_t as_regio_params;
    int device_index = 0;
    
    /* Choose the appropriate method for accessing the fields of the ioctl_param structure */
    if (ioctl_num != CALLED_FROM_KERNEL) {
        if (copy_from_user(&as_regio_params, (void *)ioctl_param, sizeof(as_regio_params)) != 0){
            printk(KERN_ALERT "error: copy_from_user in as_regio_ioctl\n");
            return -1;
        }
    }
    else {
        as_regio_params.cmd = (*(as_ioctl_params_t*)ioctl_param).cmd;
        as_regio_params.address = (*(as_ioctl_params_t*)ioctl_param).address;
        as_regio_params.value = (*(as_ioctl_params_t*)ioctl_param).value;
    }
    
    for (device_index = 0; device_index < initialized_devices; device_index++) {
    /* Find out which module was called, this version allows only one global regio device containing the entire ASTERICS address space */
    /* since as_reg_read and as_reg_write function calls do not deliver a file pointer */
        if (device_data[device_index].fops == &as_regio_fops){
            /* Then determine offset */
            regio_offset = device_data[device_index].offset;
            break;
        }   
    }
    
    switch (as_regio_params.cmd) {
        case AS_IOCTL_CMD_READ:
            val = ioread32 ((const volatile void*)((uint32_t)as_regio_params.address + regio_offset));
            return val;
            break;  
        case AS_IOCTL_CMD_WRITE:
            iowrite32 (as_regio_params.value, (volatile void *)((uint32_t)as_regio_params.address + regio_offset)); 
            break;
        default:
            printk(KERN_WARNING "warning: undefined parameter in as_regio_ioctl\n");
            break;  
    }
    return 0;
}



/****************************** memio *********************************/

/*
 * Transfers data between hardware and software using the memio module 
 * provided by the ASTERICS framework.
 * A single memio device is either associated with a as_memreader (write)
 * or as_memwriter (read) and therefore supports only one direction at 
 * a time. 
 */

/* 
 * Updates the internal ringbuffer of the memio device, may be called by 
 * the user but is usually not necessary, since the interrupt handler 
 * calls "as_memio_hw_update" regularly for all open devices.
 */
long driver_as_memio_ioctl(struct file *filp, unsigned int ioctl_num, unsigned long ioctl_param) {

    struct device_data_t * dev = filp->private_data;
    if(dev != NULL) {
        if(((*dev).memio_active)) {    /* Check if memio device is open */
            as_memio_hw_update((*dev).memio_file);
        }
        else { /* Permission denied since device is not open */
            return -EPERM;
        }
    }
    else { /* Device does not exist or is no memio device */
        return -ENODEV;
    }
    return 0;
}


/* Determine the module to be opened and call as_memio_open_and_config function to setup the data stream. */

static int driver_as_memio_open( struct inode *device_file, struct file *filp ) {
    int device_index = 0;
    as_memio_config_t memio_config;
    
    for (device_index = 0; device_index < initialized_devices; device_index++){
        /* Find out which module was called */
        if (device_data[device_index].cdev.dev == filp->f_inode->i_rdev) {
            break;
        }   
    }
    
    /* 
     * Test if device is already open (Only allow one open instance).
     * Busy is set to "1" upon creating the device. The following function returns "1" if the variable is "0"
     * after decrementing it.
     * The same "busy" flag is also used if the associated memory module is to be used for mmap!
     */
    if(!atomic_dec_and_test(&device_data[device_index].busy)) {
        atomic_inc(&device_data[device_index].busy);
        return -EBUSY;
    }
    
    /* Check if provided flags match the corresponding ones used for device creation */
    if ((device_data[device_index].flags & (O_RDONLY | O_WRONLY)) == (filp->f_flags & (O_RDONLY | O_WRONLY))) {
        /* Use memio default values (see as_memio for more details) */
        memio_config.as_reader_writer_buffer_size = AS_MEMIO_DEFAULT_FIFO_BUFFER_SIZE;
        memio_config.as_reader_writer_transfer_size = AS_MEMIO_DEFAULT_HW_TRANSFER_SIZE;
        memio_config.as_reader_writer_max_burst_length = AS_MEMIO_DEFAULT_MAX_BURST_LENGTH;
        /* Use interface bit width provided by device tree */
        memio_config.as_reader_writer_interface_width = device_data[device_index].interface_width;
        memio_config.manage_cache = device_data[device_index].manage_cache;
        /* Initialize memio */
        device_data[device_index].memio_file = as_memio_open( device_data[device_index].hw_module_addr, &memio_config, device_data[device_index].flags);
        if(device_data[device_index].memio_file == NULL) {
            atomic_inc(&device_data[device_index].busy);
            return -ENOMEM;
        }
    }
    else {
        printk(KERN_ALERT "Error on memio open: Given flags do not match the device\n");
        atomic_inc(&device_data[device_index].busy);
        return -EINVAL;  
    }
    
    /* Check if O_NONBLOCK flag is absent */
    if(!(filp->f_flags & O_NONBLOCK)) {
        /* Setup wait queue for sleeping */
        init_waitqueue_head (&device_data[device_index].wait);
        /* Set condition variable to 0 (is set to 1 by interrupt routine) */
        device_data[device_index].wake_up_cond = 0;
    }
    /* Store device data into private area of file pointer to avoid having to search for the device again */
    filp->private_data = &(device_data[device_index]);
    /* Tell interrupt routine that the device may now be served */
    device_data[device_index].memio_active = AS_TRUE;
  
    return 0;
  
}


/* Determine the module to be closed and call the as_memio_close function for cleanup */

static int driver_as_memio_close( struct inode *device_file, struct file *filp ) {
  
    struct device_data_t * dev = filp->private_data;
    
    /* Tell interrupt routine that this device is shutting down */
    (*dev).memio_active = AS_FALSE;
    /* Disable interrupt requests */
    (*dev).register_intr = AS_FALSE;
    /* Close memio instance */
    as_memio_close((*dev).memio_file);
    /* Set device to non-busy */
    atomic_inc(&(*dev).busy);

    return 0;
}



/*
 * Performs data transfers from hardware to software by utilizing 
 * the as_memwriter module.
 * Calls may be blocking or nonblocking by using the O_NONBLOCK 
 * flag upon "open".
 * In case the following function blocks the process, it is woken 
 * up by the interrupt handler (currently timer-based).
 * Otherwise, "as_memio_hw_update" is called on a regular basis 
 * by the interrupt handler.
 */
static ssize_t driver_as_memio_read ( struct file *filp, char __user * buffer, size_t count, loff_t *offp) {
  
    int32_t error = 0;
    uint32_t bytes_copied = 0;
    uint32_t time_out_counter = 0;
    struct device_data_t * dev = filp->private_data;

    /* Lock to prevent multiple reads at once */
    as_mutex_lock((*dev).access_lock);

    /* Check if read is supported by this device, i.e. it refers to a as_memwriter */
    if(!filp->f_flags & O_RDONLY) {
        printk(KERN_ALERT "Error on memio read: Not supported for this device (uses as_memwriter)\n");
        /* Set appropriate error */
        error = -EBADF;
        goto read_out;
    }
    
    /* Read as many data as currently possible from memio buffer and return immediately */
    if(filp->f_flags & O_NONBLOCK) {
        bytes_copied = as_memio_read((*dev).memio_file, buffer, count);
        goto read_out;
    }
        
read_retry:
    time_out_counter++;
    
    /* Read all data from memio buffer, sleep if necessary */
    (*dev).wake_up_cond = 0;
    bytes_copied += as_memio_read((*dev).memio_file, buffer+bytes_copied, count-bytes_copied);
    /* Sleep if there is still data remaining */
    if(bytes_copied!=count) {
        /* Tell interrupt routine that this device is going to sleep */
        (*dev).register_intr = AS_TRUE;
        /* Wait for interrupt */ 
        wait_event_interruptible((*dev).wait, ((*dev).wake_up_cond));
        /* No wake-up has to be performed by interrupt routine */
        (*dev).register_intr = AS_FALSE;
        /* Check if all data has been transfered */
        if(time_out_counter < 100) {
          goto read_retry;
        }
        else {
            printk(KERN_ALERT "timeout\n");
        }
    }
    
read_out:

    as_mutex_unlock((*dev).access_lock);
    
    /* Check if an error occured, otherwise return the transferred number of bytes */
    return (error!=0) ? error : bytes_copied;

}


/*
 * Performs data transfers from software to hardware by utilizing 
 * the as_memreader module.
 * Calls may be blocking or nonblocking by using the O_NONBLOCK 
 * flag upon "open".
 * In case the following function blocks the process, it is woken 
 * up by the interrupt handler (currently timer-based).
 * Otherwise, "as_memio_hw_update" is called on a regular basis 
 * by the interrupt handler.
 */
static ssize_t driver_as_memio_write ( struct file *filp, const char __user * buffer, size_t count, loff_t * offp) {
  
    int32_t error = 0;
    uint32_t bytes_copied = 0;
    uint32_t time_out_counter = 0;
    struct device_data_t * dev = filp->private_data;

    /* Lock to prevent multiple writes at once */
    as_mutex_lock((*dev).access_lock);

    /* Check if write is supported by this device, i.e. it refers to a as_memreader */
    if(!filp->f_flags & O_WRONLY) {
        printk(KERN_ALERT "Error on memio read: Not supported for this device (uses as_memreader)\n");
        /* Set appropriate error */
        error = -EBADF;
        goto write_out;
    }

    /* Write as many data as currently possible to memio buffer and return immediately */
    if(filp->f_flags & O_NONBLOCK) {
        bytes_copied = (ssize_t)as_memio_write((*dev).memio_file, buffer, count);
        goto write_out;
    }
    
write_retry:

    time_out_counter++;
    
    /* Write all data to memio buffer, sleep if necessary */
    (*dev).wake_up_cond = 0;
    bytes_copied += as_memio_write((*dev).memio_file, buffer+bytes_copied, count-bytes_copied);
    /* Sleep if there is still data remaining */
    if(bytes_copied!=count) {
        /* Tell interrupt routine that this device is going to sleep */
        (*dev).register_intr = AS_TRUE; 
        /* Wait for interrupt */ 
        wait_event_interruptible((*dev).wait, ((*dev).wake_up_cond)); 
        /* No wake-up has to be performed by interrupt routine */
        (*dev).register_intr = AS_FALSE; 
        /* Check if all data has been transfered */
        if(time_out_counter < 100) {
          goto write_retry;
        }
        else {
            printk(KERN_ALERT "timeout\n");
        }
    }
    
write_out:

    as_mutex_unlock((*dev).access_lock);
    
    /* Check if an error occured, otherwise return the transferred number of bytes */
    return (error!=0) ? error : bytes_copied;

}


/****************************** i2c ***********************************/

/* Uses a hardware register for data transfers. */

static long as_i2c_ioctl(struct file *f, uint32_t ioctl_num, unsigned long ioctl_param) {
    uint32_t val;
    uint32_t *LocalAddr;
    uint32_t iic_offset = 0;
    
    as_ioctl_params_t as_iic_params;
    
    int device_index;
    if (copy_from_user(&as_iic_params, (void *)ioctl_param, sizeof(as_ioctl_params_t)) != 0) {
        printk(KERN_ALERT "error: copy_from_user in as_i2c_ioctl\n");
        return -1;
    }
    
    for (device_index = 0; device_index < initialized_devices; device_index++){
        /* Find out which module was called */
        if (device_data[device_index].cdev.dev == f->f_inode->i_rdev){
            /* Determine offset */
            iic_offset = device_data[device_index].offset;
            break;
        }   
    }
    switch (as_iic_params.cmd)
    {
      case AS_IOCTL_CMD_READ:
          val = ioread32 (as_iic_params.address + iic_offset);
          return val;
          break;  
      case AS_IOCTL_CMD_WRITE:
          LocalAddr = (as_iic_params.address + iic_offset);
          iowrite32 (as_iic_params.value, LocalAddr); 
          break;
      default:
          printk(KERN_WARNING "warning: undefined parameter in as_i2c_ioctl\n");
          break;  
    }
    return 0;
}


/***************************** mmap *******************************/

/*
 * Maps a physically concurrent memory area (acquired by control device)
 * to virtual address space of the user (driver_as_mmap).
 * Transfers data between user application and hardware without copying 
 * the data (as_mmap_ioctl).
 * It uses one of the memory modules of the existing memio devices for 
 * transferring data.
 */

static int driver_as_mmap(struct file *filp, struct vm_area_struct *vma) {

    unsigned long pfn;
    int i;
    int ret_val = 0;

    for (i = 0; i < initialized_devices; i++) {
        /* Find out which module was called */
        if (device_data[i].cdev.dev == filp->f_inode->i_rdev) {
            break;
        }   
    }

    /* Lock to prevent mapping the same area twice */
    as_mutex_lock(device_data[i].access_lock);
    
    /* Check if requested memory region is within the scope of the physical memory */
    if((vma->vm_end - vma->vm_start) > (*device_data[i].mmap).size) {
        ret_val = -ENOMEM;
        goto mmap_exit;
    }

    /* Get the page frame number for remapping the physical memory to virtual */
    pfn = virt_to_phys((void *)(*device_data[i].mmap).data)>>PAGE_SHIFT;
    
  
    /* The actual remapping */
    if(remap_pfn_range(vma, vma->vm_start, pfn, vma->vm_end - vma->vm_start, vma->vm_page_prot)) {
        ret_val = -EAGAIN;
        goto mmap_exit;
    }
        
    filp->private_data = vma;

mmap_exit:  
  
    as_mutex_unlock(device_data[i].access_lock);    

    return ret_val;

}


/* Performs the actual data transfer between software and hardware. */

static long as_mmap_ioctl(struct file *filp, uint32_t ioctl_num, unsigned long ioctl_param) {
    bool memory_mod_found;
    int as_mmap_index, hw_module_index;
    as_ioctl_params_t as_mmap_params;
    uint32_t address_offset;
    int ret_val = 0;
    struct vm_area_struct *vma = filp->private_data;
    uint32_t time_out_counter = 0;

    /* Search as_mmap module */
    for (as_mmap_index = 0; as_mmap_index < initialized_devices; as_mmap_index++) {
        /* Find out which module was called */
        if (device_data[as_mmap_index].cdev.dev == filp->f_inode->i_rdev) {
            break;
        }   
    }

    as_mutex_lock(device_data[as_mmap_index].access_lock);
    
    if (copy_from_user(&as_mmap_params, (void *)ioctl_param, sizeof(as_ioctl_params_t)) != 0) {
        printk(KERN_ALERT "error: copy_from_user in as_mmap_ioctl\n");
        ret_val = -EAGAIN;
        goto mmap_ioctl_out;
    }

    if(vma == NULL) {
        printk(KERN_ALERT "Error: Memory has not been mapped. Call to mmap required!\n");
        ret_val = -EINVAL;
        goto mmap_ioctl_out;
    }
    
    /* Determine the offset within the allocated memory area for the data transfer*/
    address_offset = (uint32_t)as_mmap_params.user_addr_start;
    
    if((as_mmap_params.value + address_offset) > (*device_data[as_mmap_index].mmap).size) {
        printk(KERN_ALERT "error: requested size is out of scope\n");
        ret_val = -EINVAL;
        goto mmap_ioctl_out;
    }

    memory_mod_found = AS_FALSE;
    
    /* Search hardware module */
    for (hw_module_index = 0; hw_module_index < initialized_devices; hw_module_index++) {
        /* Find out which module was called */
        if (device_data[hw_module_index].hw_module_addr == as_mmap_params.address) {
            memory_mod_found = AS_TRUE;
            break;
        }   
    }

    /* The corresponding memory module is not guaranteed to exist */
    if(!memory_mod_found) {
        ret_val = -ENODEV;
        goto mmap_ioctl_out;
    }


    /* Test if hardware device is already in use by memio */
    if(!atomic_dec_and_test(&device_data[hw_module_index].busy)) {
        atomic_inc(&device_data[hw_module_index].busy);
        ret_val = -EBUSY;
        goto mmap_ioctl_out;
    }
    
    if(as_mmap_params.value % (device_data[hw_module_index].interface_width/8)) {
        printk(KERN_ALERT "error: requested size has to be a multiple of %i bytes\n", (device_data[hw_module_index].interface_width/8));
        atomic_inc(&device_data[hw_module_index].busy);
        ret_val = -EINVAL;
        goto mmap_ioctl_out;
    }
    
    /* Use defaults for burst length */
    as_reader_writer_init(device_data[hw_module_index].hw_module_addr, NULL);
    as_reader_writer_set_section_size(device_data[hw_module_index].hw_module_addr, as_mmap_params.value);
    as_reader_writer_set_section_addr(device_data[hw_module_index].hw_module_addr, (uint32_t*)(virt_to_phys((volatile void *)(*device_data[as_mmap_index].mmap).data + address_offset)));
    if(as_mmap_params.cmd == AS_IOCTL_CMD_READ) {
        as_writer_set_enable(device_data[hw_module_index].hw_module_addr);
        as_writer_set_disable_on_no_go(device_data[hw_module_index].hw_module_addr);
    }
    as_reader_writer_set_go(device_data[hw_module_index].hw_module_addr);

  while(!as_reader_writer_is_busy(device_data[hw_module_index].hw_module_addr));

mmap_ioctl_retry:
    time_out_counter++;

    device_data[as_mmap_index].wake_up_cond = 0;
    /* Check if hardware module has finished its data transfer, sleep if necessary */
    if(!as_reader_writer_is_done(device_data[hw_module_index].hw_module_addr)) {
        /* Tell interrupt routine that this device is going to sleep */
        device_data[as_mmap_index].register_intr = AS_TRUE; 
        /* Wait for interrupt */ 
        wait_event_interruptible(device_data[as_mmap_index].wait, (device_data[as_mmap_index].wake_up_cond)); 
        /* No wake-up has to be performed by interrupt routine */
        device_data[as_mmap_index].register_intr = AS_FALSE; 
        /* Check if all data has been transfered */
        if(time_out_counter < 100) {
          goto mmap_ioctl_retry;
        }
        else {
            printk(KERN_ALERT "timeout\n");
        }
    }

    /* Only release memory module if all data has been transfered */
    atomic_inc(&device_data[hw_module_index].busy);
    
mmap_ioctl_out:

    as_mutex_unlock(device_data[as_mmap_index].access_lock);
    return ret_val;

}

/******************************* Timer ********************************/

/*
 *  Checks if any memio or mmap processes are currently sleeping due to 
 *  waiting for data transfers to finish. Wakes up any sleeping process.
 *  For open memio devices which are currently not sleeping, it calls
 *  hw_update to check if data can be transferred.
 *  Especially importand for write requests, since data may be transferred 
 *  to the buffer but the as_memreader has not yet programmed due to 
 *  buffer wrap around (request has to be splitted into 2 sections, since
 *  the memreader can only read physically concurrent addresses!)
 */

void data_transfer_update_task(unsigned long arg) {
    int device_index;
    
    /* Loop all devices and synchronize data buffers for memio */
    for (device_index = 0; device_index < initialized_devices; device_index++) {
        if (device_data[device_index].fops == &as_memio_fops) {   /* Check for memio device */
            if((device_data[device_index].memio_active)) {    /* Check if memio device is open; mainly required for hw update */
                if(device_data[device_index].register_intr) {         /* Check if interrupts can be served; only call wake up when process is actually sleeping */
                    device_data[device_index].wake_up_cond = 1;       /* Set the wake-up condition */
                    wake_up_interruptible(&device_data[device_index].wait);   /* Wake up blocking device */
                }
                else {
                    as_memio_hw_update(device_data[device_index].memio_file); /* Call memio update to flush data from buffers to hardware/memory */
                }
            }
        }
        else if(device_data[device_index].fops == &as_mmap_fops) {  /* Check for mmap device */
            if(device_data[device_index].register_intr) {         /* Check if interrupts can be served; only call wake up when process is actually sleeping */
                device_data[device_index].wake_up_cond = 1;       /* Set the wake-up condition */
                wake_up_interruptible(&device_data[device_index].wait);   /* Wake up blocking device */
            }
        }
    }
}


/* Interrupt handler for the timer. */

void timer_callback(unsigned long data) {
    
    /* Trigger to run work queue which handles waking up sleeping processes */
    schedule_work(&timer_wq);
    
    /* Check if timer is going to shutdown due to unloading module */
    if(!timer_shutdown) {
      /* Run timer again */
      add_timer(&interrupt_timer);
    }
}


/*************************** HW Interrupts ****************************/

/* 
 * TBD: 
 * - Add interrupt handler(s) here!
 * - Probably better to use a single interrupt handler and use the same 
 *   one for all interrupt lines (point to the same handler for "request_irq"
 *   calls)
 * - Perhaps use the same work item and only schedule "data_transfer_update_task"
 */


/***************************** Top-Level ******************************/

/*
 * File operation structs for all device types of the driver.
 */

/* as_mmap file operations */
struct file_operations as_mmap_fops = 
{
    .owner = THIS_MODULE, 
    .mmap  = driver_as_mmap,
    .unlocked_ioctl = as_mmap_ioctl,
};

  
/* as_control file operations */
static struct file_operations as_control_fops =
{
    .owner = THIS_MODULE,
    .unlocked_ioctl = as_control_ioctl,
};


/* as_regio file operations */
static struct file_operations as_regio_fops =
{
    .owner = THIS_MODULE,
    .unlocked_ioctl = as_regio_ioctl,
};


/* as_memio file operations */
static struct file_operations as_memio_fops =
{
    .owner = THIS_MODULE,
    .read = driver_as_memio_read,
    .write = driver_as_memio_write,
    .unlocked_ioctl = driver_as_memio_ioctl, 
    .open = driver_as_memio_open,
    .release = driver_as_memio_close,
};


/* as_i2c file operations */
static struct file_operations as_i2c_fops =
{
    .owner = THIS_MODULE,
    .unlocked_ioctl = as_i2c_ioctl,
};



/**************************** Constructor *****************************/

/*
 * Initialization of the driver is done here. Requests a major number 
 * from the kernel and a range of minor numbers (MAX_DEVICES).
 * No device node on the file system is created, since the user may 
 * want to choose the location.
 */

static int __init mod_init(void) {
    /* Get a range of minor numbers (starting with 0) to work with */
    if (alloc_chrdev_region(&first, 0, MAX_DEVICES, "as_driver") < 0)
    {
        printk(KERN_ALERT "error: kernel function alloc_chrdev_region failed. Device not created.\n");
        return -1;
    }
    /* Create device class for the devices */
    if ((cl = class_create(THIS_MODULE, "as_driver")) == NULL) {
        printk(KERN_ALERT "error: kernel function class_create failed. Device not created.\n");
        unregister_chrdev_region(first, MAX_DEVICES);
        return -1;
    }

    /* Index is zero as this is the first device */
    initialized_devices = 0;

    /* Set defaults for control device; Init pointers to NULL */
    set_device_defaults(initialized_devices);

    device_data[initialized_devices].fops = &as_control_fops;
    cdev_init(&device_data[initialized_devices].cdev, device_data[0].fops);
    if (cdev_add(&device_data[initialized_devices].cdev, first, 1) == -1) {
        printk(KERN_ALERT "error: kernel function cdev_add failed. Device not created.\n");
        device_destroy(cl, MKDEV(MAJOR(first), MINOR(first)));
        class_destroy(cl);
        unregister_chrdev_region(first, MAX_DEVICES);
        return -1;
    }
    /* Initialize the mutex */
    device_data[initialized_devices].access_lock = as_mutex_new ();
    initialized_devices++;

    timer_shutdown = AS_FALSE;
    
    /* Setup work queue for handling code after interrupts */
    INIT_WORK(&timer_wq, (void (*)(struct work_struct *)) data_transfer_update_task);
    
    /* Setup basic timer for interrupt blocking support and buffer synchronization */
    setup_timer(&interrupt_timer, timer_callback, 0);
    mod_timer(&interrupt_timer, jiffies + TIMER_INTERVAL);
    
    printk(KERN_INFO "info: initalized devices %i\n", initialized_devices);
    printk(KERN_INFO "info: module initialized correctly.\n");
    return 0;
}
 

/***************************** Destructor *****************************/

/* 
 * Deinitializes the driver and releases all acquired resources back to the 
 * kernel, including major and minor numbers.
 */

static void __exit mod_exit(void) {
    /* Remove other devices */
    int device_index;
    uint32_t addr;

    /* Signal timer to stop running */
    timer_shutdown = AS_TRUE;

    /* Delete timer */
    del_timer_sync(&interrupt_timer);

    /* Delete all devices except the control device */
    for ( device_index = 1; device_index < initialized_devices; device_index++) { 
        cdev_del(&device_data[device_index].cdev);
        addr = (uint32_t)device_data[device_index].baseaddress_virt - (uint32_t)device_data[device_index].offset;
        if (device_data[device_index].req_mem_region_name != NULL) {
            iounmap((volatile void*)addr);
            release_mem_region((resource_size_t)addr, device_data[device_index].address_range_size);
        }
        if(device_data[device_index].mmap != NULL) {
            as_free((*device_data[device_index].mmap).data);
//            free_pages((unsigned long)(*device_data[device_index].mmap).data, ((*device_data[device_index].mmap).page_allocation_order));
            as_free(device_data[device_index].mmap);
        }
        as_mutex_del(device_data[device_index].access_lock);
        device_destroy (cl, MKDEV(MAJOR(first), MINOR(first) + device_index));
    } 

    /* Remove control device */
    as_mutex_del(device_data[0].access_lock);
    cdev_del(&device_data[0].cdev);
    device_destroy (cl, MKDEV(MAJOR(first), MINOR(first)));     
    class_destroy(cl);
    unregister_chrdev_region(first, MAX_DEVICES);
    initialized_devices = 0;
    printk(KERN_INFO "info: driver unregistered\n");

}


module_init(mod_init);
module_exit(mod_exit);
