/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  Copyright (C) Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Author:         Gundolf Kiefer, Michael Schaeferling
--
-- Description:    Software support module for ASTERICS systems containing:
--                 - Basic declarations
--                 - Generic register access encapsulating FPGA vendor specific IO operations
--                 - OS wrapper functions
----------------------------------------------------------------------------------
--  This program is free software; you can redistribute it and/or
--  modify it under the terms of the GNU Lesser General Public
--  License as published by the Free Software Foundation; either
--  version 3 of the License, or (at your option) any later version.
--  
--  This program is distributed in the hope that it will be useful,
--  but WITHOUT ANY WARRANTY; without even the implied warranty of
--  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
--  Lesser General Public License for more details.
--  
--  You should have received a copy of the GNU Lesser General Public License
--  along with this program; if not, see <http://www.gnu.org/licenses/>
--  or write to the Free Software Foundation, Inc.,
--  51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
----------------------------------------------------------------------------------
--! @file
--! @brief Software support module for ASTERICS systems.
--------------------------------------------------------------------------------*/

#ifndef _AS_SUPPORT_
#define _AS_SUPPORT_


#include "as_config.h"



/* C Libraries */
#if !AS_OS_LINUX_KERNEL
    #include <stdint.h>
    #include <stdlib.h>     /* presently for 'NULL' only */
    #include <stdio.h>
    #include <fcntl.h>
    #include <string.h>
    #include <unistd.h>
#endif

#if AS_OS_POSIX
    #include <sys/ioctl.h>
#endif

#if AS_OS_LINUX_KERNEL
    #include <linux/types.h>
    #include <linux/slab.h>
    #include <asm/uaccess.h>
    #include <linux/fcntl.h>
    #include <linux/ioctl.h>
#endif

#if (AS_OS_LINUX_KERNEL || AS_OS_POSIX)
    #include "as_linux_kernel_if.h"
#endif

/* Xilinx Libraries */
#if AS_BSP_XILINX
    #include "xil_cache.h"
#endif


/* NOTE: For portability reasons, module drivers must not include any system header files
 * themselves and should only use definitions from those external libraries listed above. */



/***************************** Basic declarations ******************************/


#define AS_BOOL char
#define AS_TRUE 1
#define AS_FALSE 0



/***** Endianess *****/

/* Helpers */
uint64_t as_swap64 (uint64_t x);   /* reverse byte order of a 32-bit word (helper) */
uint32_t as_swap32 (uint32_t x);   /* reverse byte order of a 32-bit word (helper) */
uint16_t as_swap16 (uint16_t x);   /* reverse byte order of a 16-bit word (helper) */



/* Hardware vs. software... */
#if AS_BIG_ENDIAN_HW == AS_BIG_ENDIAN_SW

static inline uint32_t as_reg_to_uint32 (uint32_t x) { return x; }
static inline int32_t as_reg_to_int32 (int32_t x) { return x; }
static inline uint16_t as_reg_to_uint16 (uint16_t x) { return x; }
static inline int16_t as_reg_to_int16 (int16_t x) { return x; }

static inline uint32_t as_reg_from_uint32 (uint32_t x) { return x; }
static inline int32_t as_reg_from_int32 (int32_t x) { return x; }
static inline uint16_t as_reg_from_uint16 (uint16_t x) { return x; }
static inline int16_t as_reg_from_int16 (int16_t x) { return x; }

#else

static inline uint32_t as_reg_to_uint32 (uint32_t x) { return as_swap32 (x); }
static inline int32_t as_reg_to_int32 (int32_t x) { return (int32_t) as_swap32 ((uint32_t) x); }
static inline uint16_t as_reg_to_uint16 (uint16_t x) { return as_swap16 (x); }
static inline int16_t as_reg_to_int16 (int16_t x) { return (int16_t) as_swap16 ((uint16_t) x); }

static inline uint32_t as_reg_from_uint32 (uint32_t x) { return as_swap32 (x); }
static inline int32_t as_reg_from_int32 (int32_t x) { return (int32_t) as_swap32 ((uint32_t) x); }
static inline uint16_t as_reg_from_uint16 (uint16_t x) { return as_swap16 (x); }
static inline int16_t as_reg_from_int16 (int16_t x) { return (int16_t) as_swap16 ((uint16_t) x); }

#endif /* AS_BIG_ENDIAN_HW == AS_BIG_ENDIAN_SW */



/* Software vs. outside world ('Net': files, network)... */
#if !AS_BIG_ENDIAN_SW  /* TBD: Make decision on endianess in the 'as_net' format */

static inline uint32_t as_net_to_uint32 (uint32_t x) { return x; }
static inline int32_t as_net_to_int32 (int32_t x) { return x; }
static inline uint16_t as_net_to_uint16 (uint16_t x) { return x; }
static inline int16_t as_net_to_int16 (int16_t x) { return x; }

static inline uint32_t as_net_from_uint32 (uint32_t x) { return x; }
static inline int32_t as_net_from_int32 (int32_t x) { return x; }
static inline uint16_t as_net_from_uint16 (uint16_t x) { return x; }
static inline int16_t as_net_from_int16 (int16_t x) { return x; }

#else

static inline uint32_t as_net_to_uint32 (uint32_t x) { return as_swap32 (x); }
static inline int32_t as_net_to_int32 (int32_t x) { return (int32_t) as_swap32 ((uint32_t) x); }
static inline uint16_t as_net_to_uint16 (uint16_t x) { return as_swap16 (x); }
static inline int16_t as_net_to_int16 (int16_t x) { return (int16_t) as_swap16 ((uint16_t) x); }

static inline uint32_t as_net_from_uint32 (uint32_t x) { return as_swap32 (x); }
static inline int32_t as_net_from_int32 (int32_t x) { return (int32_t) as_swap32 ((uint32_t) x); }
static inline uint16_t as_net_from_uint16 (uint16_t x) { return as_swap16 (x); }
static inline int16_t as_net_from_int16 (int16_t x) { return (int16_t) as_swap16 ((uint16_t) x); }

#endif /* !AS_BIG_ENDIAN_SW */



 

/***** Safe heap operations *****/

#if AS_HAVE_HEAP

#define SETP(P, X) { if (P) free (P); P = (X); }
#define FREEP(P) SETP(P, NULL)
#define MALLOC(T, N) (T*) malloc (sizeof (T) * (N))
#define REALLOC(T, P, N) (T*) realloc (P, sizeof (T) * (N))

#endif /* AS_HAVE_HEAP */





/***** Module init/done *****/
#if AS_OS_POSIX
    int as_control_fd;
    int as_iic_fd;
    int as_regio_fd;
#endif /* AS_OS_POSIX */

void as_support_init (void);      /* must be called by application on startup */
void as_support_done (void);      /* must be called by application when shutting down */





/***************************** Logging *****************************************/

#if AS_HAVE_PRINTF
void as_log_para (const char *_log_head, const char*_log_file, int _log_line);    /* Helper; use the following macros instead */
void as_log_printf (const char *format, ...);    /* Helper; use the following macros instead */
#else
static inline void as_log_para (const char *_log_head, const char*_log_file, int _log_line) {}
static inline void as_log_printf (const char *format, ...) {}
#endif /* AS_HAVE_PRINTF */


#if AS_WITH_DEBUG
#define DEBUG(MSG) { as_log_para ("DEBUG", __FILE__, __LINE__); as_log_printf (MSG); }
#define DEBUGF(FMT) { as_log_para ("DEBUG", __FILE__, __LINE__); as_log_printf FMT; }
#else
#define DEBUG(MSG) {}
#define DEBUGF(FMT) {}
#endif /* AS_WITH_DEBUG */

#if AS_OS_LINUX_KERNEL

#define INFO(MSG) {}
#define INFOF(FMT) {}

#define WARNING(MSG) {}
#define WARNINGF(FMT) {}

#define ERROR(MSG) {}
#define ERRORF(FMT) {}

#define ASSERT(COND) {}
#define ASSERTM(COND,MSG) {}

#else

#define INFO(MSG) { as_log_para ("INFO", __FILE__, __LINE__); as_log_printf (MSG); }
#define INFOF(FMT) { as_log_para ("INFO", __FILE__, __LINE__); as_log_printf FMT; }

#define WARNING(MSG) { as_log_para ("WARNING", __FILE__, __LINE__); as_log_printf (MSG); }
#define WARNINGF(FMT) { as_log_para ("WARNING", __FILE__, __LINE__); as_log_printf FMT; }

#define ERROR(MSG) { as_log_para ("ERROR", __FILE__, __LINE__); as_log_printf (MSG); exit (3); }
#define ERRORF(FMT) { as_log_para ("ERROR", __FILE__, __LINE__); as_log_printf FMT; exit (3); }

#define ASSERT(COND) { if (!(COND)) { as_log_para ("ERROR", __FILE__, __LINE__); as_log_printf ("Assertion failed"); abort (); } }
#define ASSERTM(COND,MSG) { if (!(COND)) { as_log_para ("ERROR", __FILE__, __LINE__); as_log_printf ("Assertion failed: %s", MSG); abort (); } }


#endif /* !AS_OS_LINUX_KERNEL */


/***************************** Register Get/Set functions **********************/

/* Note: Compared to the previous design ('asterics_support.h' from system 'as_zedboard_minimal',
 *       this file makes the following simplification, which need to be taken care of in
 *       generated 'as_hardware.h' files and module driver headers:
 *       1. Module base addresses are absolute. (-> Add 'ASTERICS_BASEADDR' to each module base in 'as_asterics.h')
 *       2. All addresses are of type 'uint32_t *'
 *          => All ASTERICS registers have 32 bits.
 *          => register IDs inside modules are in units of 32-bit words.
 *
 */


/********* No operating system present **********/
#if AS_OS_NONE

/********* Vendor driver: Dummy ********/

#if AS_BSP_DUMMY
static inline void as_reg_write (uint32_t *addr, uint32_t val) {}    /* TBD: Print to console? */
static inline uint32_t as_reg_read (uint32_t *addr) { return 0; }    /* TBD: Print something to console? */
static inline void as_dcache_invalidate() {}
static inline void as_dcache_invalidate_range(uint32_t *addr, uint32_t len) {}
static inline void as_dcache_flush() {}
static inline void as_dcache_flush_range(uint32_t *addr, uint32_t len) {}

#endif /* AS_BSP_DUMMY */



/********* Vendor driver: Xilinx ********/

#if AS_BSP_XILINX

#include "xil_types.h"      // TBD: Do we need all of these includes?
#include "xstatus.h"
#include "xil_io.h"

/* TBD: Insert assertions to check whether the CPU type and properties
 *   match those defined in 'as_config.h'.
 */

/**
 *
 * Write 32 bit value to an ASTERICS module register.
 *
 * @param   addr is the absolute address of the ASTERICS register.
 * @param   val is the value to be written.
 *
 */
static inline void as_reg_write (uint32_t *addr, uint32_t val) { Xil_Out32 ((uint32_t) addr, as_reg_from_uint32 (val)); }

/**
 *
 * Read 32 bit value from an ASTERICS module register.
 *
 * @param   addr is the absolute address of the ASTERICS register.
 *
 * @return  The data read from a specific register.
 *
 */
static inline uint32_t as_reg_read (uint32_t *addr) { return as_reg_to_uint32 (Xil_In32 ((uint32_t) addr)); }

/**
 * 
 * Invalidate data cache to force main memory access.
 *
 */
static inline void as_dcache_invalidate() { Xil_DCacheInvalidate(); }

/**
 * 
 * Invalidate only target memory area to force main memory access and leave 
 * others parts untouched.
 * 
 * @param   addr is the absolute memory address where invalidation starts.
 * @param   len is the number of bytes (!) to be invalidated.
 *
 */
static inline void as_dcache_invalidate_range(uint32_t *addr, uint32_t len) { Xil_DCacheInvalidateRange((uint32_t)addr, len); }

/**
 *
 * Flushes the data cache which causes memory write-back and invalidation 
 * of the data cache.
 *
 */
static inline void as_dcache_flush() { Xil_DCacheFlush(); }

/**
 * 
 * Flushes only target memory area which causes memory write-back and 
 * invalidation of target area starting from addr.
 * 
 * @param   addr is the absolute memory address on which a write-back and
 *          invalidation operation is performed.
 * @param   len specifies the number of following bytes of addr to be 
 *          written back to memory and to be invalidated in the data cache.
 */
static inline void as_dcache_flush_range(uint32_t *addr, uint32_t len) { Xil_DCacheFlushRange((uint32_t)addr, len); }

#endif /* AS_BSP_XILINX */



/********* Vendor driver: Altera (TBD) ********/

#if AS_BSP_ALTERA

#error "Altera BSPs not yet implemented"

#endif /* AS_BSP_ALTERA */

#endif /* AS_OS_NONE */


/********* Linux kernel module utility ********/

#if AS_OS_LINUX_KERNEL

void fill_as_regio_params (uint32_t cmd, uint32_t address, uint32_t value, as_ioctl_params_t * structure);
void as_reg_write (uint32_t *addr, uint32_t val);
uint32_t as_reg_read (uint32_t *addr);

#endif /* AS_OS_LINUX_KERNEL */

#if AS_OS_POSIX

void fill_as_regio_params (uint32_t cmd, uint32_t address, uint32_t value, as_ioctl_params_t * structure);
void as_reg_write (uint32_t *addr, uint32_t val);
uint32_t as_reg_read (uint32_t *addr);

static inline void as_dcache_invalidate_range(uint32_t *addr, uint32_t len) {}
static inline void as_dcache_flush(void) {}
static inline void as_dcache_flush_range(uint32_t *addr, uint32_t len) {}

#endif /* AS_OS_POSIX */



/********* Useful helpers ********/

/**
 * Compute the absolute register address for a module and register offset.
 *
 * @param module_addr is the base address of the module.
 * @param reg_id is the number of the register in the address.
 *
 * @return absolute address that can be passed to 'as_reg_read' or 'as_reg_write'.
 */
static inline uint32_t *as_module_reg (uint32_t *module_addr, int reg_id) { return &module_addr[reg_id]; }

/**
 * Write to register with mask.
 */
void as_reg_write_masked (uint32_t *addr, uint32_t mask, uint32_t val);

/**
 * Read from register with mask.
 */
uint32_t as_reg_read_masked (uint32_t *addr, uint32_t mask);




/***************************** OS Wrappers *************************************/

/* In order to write OS-independent code, that may alternatively also execute
 * without any OS at all, the following functionality is required:
 *
 * 1. A portable mechanism to run small recurring tasks in the background ("tasklets"),
 *    particularly for bare metall cases without thread support.
 *
 * 2. Synchronisation primitives, particularly for the OS case, where concurrent
 *    threads are available.
 *
 * 3. Support for virtual memory address translation.
 */


/********** Tasklets and 'as_yield' **********/

/* Tasklets are small tasks that need to be executed regularly (e.g. checking for new
 * data in a buffer and eventually copying it out of the way).
 *
 * Callers (applications, module drivers) should regularly call 'as_yield', e.g. inside
 * waiting loops, to make sure that the tasklets are executed.
 *
 * Tasklets are typically executed if 'as_yield' is called. Depending on the OS, they
 * may also be performed in a background thread. Hence, they must be synchronized
 * correctly with the foreground thread if 'AS_WITH_MULTIPROCESSING' is
 * set. In the POSIX backend, the switch 'SERIALIZE_TASKLETS' decides whether tasklets
 * are synchronized with the main thread internally.
 */

typedef void as_tasklet_f (void *);

/**
 * Define new tasklet. From now, the function 'func' is invoked regularly, and
 * 'data' is passed as its argument.
 *
 * @return handle to the tasklet object, which must be passed to 'as_taskletDel ()' later.
 */
struct as_tasklet_s *as_tasklet_new (as_tasklet_f *func, void *data);

/**
 * Stop and delete a previously defined tasklet.
 */
void as_tasklet_del (struct as_tasklet_s *tasklet);

/**
 * as_yield: This function should be called regularly to let background tasklets
 *   do their work.
 */
void as_yield (void);



/********** as_sleep ***********/


/**
 * Sleep for a number of nanoseconds.
 */
void as_sleep (int nanoseconds);


/********** as_thread **********/


typedef void *as_thread_func_f (void *);


#if AS_WITH_MULTIPROCESSING


/**
 * Start a new background thread.
 *
 * @return Handle to the thread
 */
struct as_thread_s *as_thread_start (as_thread_func_f *func, void *data);

/**
 * Join a background thread. The object referenced by 'thread' is deleted,
 * the pointer must not be used afterwards.
 */
void *as_thread_join (struct as_thread_s *thread);


#else

/* Dummy implementation for single-processing systems... */
static inline struct as_thread_s *as_thread_start (as_thread_func_f *func, void *data) { return NULL; }
static inline void *as_thread_join (struct as_thread_s *thread) { return NULL; }

#endif /* AS_WITH_MULTIPROCESSING */



/********** as_mutex **********/


#if AS_WITH_MULTIPROCESSING


/**
 * Create a new mutex object.
 */
struct as_mutex_s *as_mutex_new ();

/**
 * Delete a mutex object.
 */
void as_mutex_del (struct as_mutex_s *mutex);

/**
 * Lock a mutex.
 */
void as_mutex_lock (struct as_mutex_s *mutex);

/**
 * Try to lock a mutex without blocking.
 *
 * @return AS_TRUE, iff the mutex could be locked.
 */
AS_BOOL as_mutex_trylock (struct as_mutex_s *mutex);

/**
 * Unlock a mutex.
 */
void as_mutex_unlock (struct as_mutex_s *mutex);


#else

/* Dummy implementation for single-processing systems... */
static inline struct as_mutex_s *as_mutex_new (void) { return NULL; }
static inline void as_mutex_del (struct as_mutex_s *mutex) {}
static inline void as_mutex_lock (struct as_mutex_s *mutex) {}
static inline AS_BOOL as_mutex_trylock (struct as_mutex_s *mutex) { return AS_TRUE; }
static inline void as_mutex_unlock (struct as_mutex_s *mutex) {}

#endif /* AS_WITH_MULTIPROCESSING */





/********** as_cond **********/


#if AS_WITH_MULTIPROCESSING


/**
 * Create a new condition variable.
 */
struct as_cond_s *as_cond_new ();

/**
 * Delete a condition variable.
 */
void as_cond_del (struct as_cond_s *cond);

/**
 * Wait on a condition variable. The mutex must be locked before and
 * is unlocked atomically for the time waiting (see the PThreads manual
 * for details). Spurious wakeups (without a prior call to 'as_condSignal'
 * or 'as_condBroadcast') may happen.
 */
void as_cond_wait (struct as_cond_s *cond, struct as_mutex_s *mutex);

/**
 * Wakeup a one thread waiting on a condition variable.
 */
void as_cond_signal (struct as_cond_s *cond);

/**
 * Wakeup all threads waiting on a condition variable.
 */
void as_cond_broadcast (struct as_cond_s *cond);


#else

/* Dummy implementation for single-processing systems... */
static inline struct as_cond_s *as_cond_new (void) { return NULL; }
static inline void as_cond_del (struct as_cond_s *cond) {}
static inline void as_cond_wait (struct as_cond_s *cond, struct as_mutex_s *mutex) { as_yield (); }
static inline void as_cond_signal (struct as_cond_s *cond) {}
static inline void as_cond_broadcast (struct as_cond_s *cond) {}

#endif /* AS_WITH_MULTIPROCESSING */


/* Note: The waiting on an I/O event (for example in 'as_memio' in blocking mode)
 *       can (and should) be implemented in a portable way using a condition variable:
 *       The waiting function repeatedly calls 'as_cond_wait', the respective tasklet
 *       in turn calls 'as_cond_signal' if new work is available.
 *
 *       On single-processing systems, this will end up in a busy loop repeatedly
 *       executing 'as_yield ()'. On multi-processing system, the waiting thread will
 *       block properly.
 */
 



/********** Virtual memory **********/

/* Abstraction for virtual address space translation is still to be done.
 * The present approach is:
 *
 * 1. I/O registers: The addresses are always virtual, and no translation is
 *           necessary. Possibly, the addresses refer to an I/O address space
 *           seperate from memory. This does not matter, if the 'as_reg_read'
 *           and 'as_reg_write' functions are defined accordingly.
 *
 * 2. Modules with a bus master port: This probably only affects 'as_memreader',
 *           'as_memwriter', and 'as_memio'. Amoung those, 'as_memio' may
 *           need address translation functionality from here. All the
 *           others can be specified to use physical addresses.
 */
 
#if AS_OS_LINUX_KERNEL

static inline void* as_malloc(uint32_t size) { return kmalloc(size, GFP_KERNEL); }
static inline void as_free(const void* objp) { kfree(objp); };

#else

static inline void* as_malloc(uint32_t size) { return malloc(size); }
static inline void as_free (void* objp) { free(objp); }

#endif /* AS_OS_LINUX_KERNEL */

#endif /** _AS_SUPPORT_ */

