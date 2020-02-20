/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
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
--! @file  as_support.h
--! @brief Software support module for ASTERICS systems.
--------------------------------------------------------------------------------*/


#include "as_support.h"


/***************************** Basic declarations ******************************/


/***** Endianess *****/
uint64_t as_swap64 (uint64_t x) {
  return (x >> 56) | ((x & 0x00ff000000000000) >> 40) | ((x & 0x0000ff0000000000) >> 24) | ((x & 0x000000ff00000000) >> 8) | ((x & 0x00000000ff000000) << 8) | ((x & 0x0000000000ff0000) << 24) | ((x & 0x000000000000ff00) << 40) | (x << 56);
}

uint32_t as_swap32 (uint32_t x) {
  return (x >> 24) | ((x & 0x00ff0000) >> 8) | ((x & 0x0000ff00) << 8) | (x << 24);
}


uint16_t as_swap16 (uint16_t x) {
  return (x << 8) | (x >> 8);
}



/***************************** Logging *****************************************/


#if AS_HAVE_PRINTF


static const char *log_head, *log_file;
static int log_line;


void as_log_para (const char *_log_head, const char* _log_file, int _log_line) {
  const char *p;
  int n;

  p = _log_file + strlen (_log_file);
  for (n = 2; p > _log_file && n > 0; p--) if (p[-1] == '/') n--;

  log_head = _log_head;
  log_file = p;
  log_line = _log_line;
}


void as_log_printf (const char *format, ...) {
  char buf [1024];
  va_list ap;

  if (log_head[0] == 'D' && !envDebug) return;   // do not output debug messages

  va_start (ap, format);
  vsnprintf (buf, sizeof (buf) - 1, format, ap);
  fprintf (stderr, "%s:%i: %s: %s\n", log_file, log_line, log_head, buf);
}


#endif /* AS_HAVE_PRINTF */





/***************************** Register Get/Set functions **********************/



#if AS_OS_LINUX_KERNEL

long as_regio_ioctl(struct file *f, unsigned int ioctl_num, unsigned long ioctl_param);

void as_reg_write (uint32_t *addr, uint32_t val) {
    as_ioctl_params_t as_regio_from_kernel_params;
    as_regio_from_kernel_params.cmd = (uint32_t)AS_IOCTL_CMD_WRITE;
    as_regio_from_kernel_params.address = addr;
    as_regio_from_kernel_params.value = val;
    as_regio_ioctl(NULL, CALLED_FROM_KERNEL, (unsigned long)&as_regio_from_kernel_params);
}
uint32_t as_reg_read (uint32_t *addr) {
    as_ioctl_params_t as_regio_from_kernel_params;
    as_regio_from_kernel_params.cmd = (uint32_t)AS_IOCTL_CMD_READ;
    as_regio_from_kernel_params.address = addr;
    as_regio_from_kernel_params.value = 0;
    return as_regio_ioctl(NULL, CALLED_FROM_KERNEL, (unsigned long)&as_regio_from_kernel_params);
}

#endif

#if AS_OS_POSIX
void as_reg_write (uint32_t *addr, uint32_t val){
    as_ioctl_params_t as_regio_from_user_params;
    as_regio_from_user_params.cmd = (uint32_t)AS_IOCTL_CMD_WRITE;
    as_regio_from_user_params.address = addr;
    as_regio_from_user_params.value = val;
    ioctl(as_regio_fd, CALLED_FROM_USER, &as_regio_from_user_params);
}
uint32_t as_reg_read (uint32_t *addr){
    as_ioctl_params_t as_regio_from_user_params;
    as_regio_from_user_params.cmd = (uint32_t)AS_IOCTL_CMD_READ;
    as_regio_from_user_params.address = addr;
    as_regio_from_user_params.value = 0;
    return ioctl(as_regio_fd, CALLED_FROM_USER, &as_regio_from_user_params);  
}
#endif /* AS_OS_POSIX */



void as_reg_write_masked (uint32_t *addr, uint32_t mask, uint32_t val) {
  as_reg_write (addr, (as_reg_read (addr) & ~mask) | (val & mask));
}


uint32_t as_reg_read_masked (uint32_t *addr, uint32_t mask) {
  return as_reg_read (addr) & mask;
}



/***************************** OS Wrappers: Common *****************************/


/********** Tasklets **********/


/* Tasklets are managed in a static array, so that no heap is required.
 * If we are sure to have a heap, this may be changed to a chained list
 * in order to get rid of the 'MAX_TASKLETS' limit.
 */


#define MAX_TASKLETS 32



struct as_tasklet_s {
  as_tasklet_f *func;
  void *data;
};


static struct as_tasklet_s tasklets[MAX_TASKLETS];
static int tasklets_top = 0;


struct as_tasklet_s *as_tasklet_new (as_tasklet_f *func, void *data) {
  struct as_tasklet_s *tasklet;

  ASSERT (tasklets_top < MAX_TASKLETS);
  tasklet = &(tasklets[tasklets_top++]);
  tasklet->func = func;
  tasklet->data = data;
  return tasklet;
}


void as_tasklet_del (struct as_tasklet_s *tasklet) {
  int n;

  n = tasklet - tasklets;
  ASSERT (n >= 0 && n < tasklets_top);
  if (n < tasklets_top - 1) tasklets[n] = tasklets[tasklets_top-1];
  tasklets_top--;
}





/***************************** OS Wrappers: Single processing ******************/


#if !AS_WITH_MULTIPROCESSING



/********** Tasklets **********/


void as_yield () {
  int n;

#if SERIALIZE_TASKLETS
  as_mutex_lock (&tasklet_m);
#endif
  for (n = 0; n < tasklets_top; n++)
    tasklets[n].func (tasklets[n].data);
#if SERIALIZE_TASKLETS
  as_mutex_unlock (&tasklet_m);
#endif /* SERIALIZE_TASKLETS */
}



/********** as_sleep ***********/


#define AS_ITER_NANOSECS 100
  /* average/minimum number of nanoseconds of one delay loop iteration;
   * to be adjusted for present processor */


void as_sleep (int nanoseconds) {
  /* FIXME: This should be replaced or complemented by a version that uses a timer.
   *        A timer interface would have to be added to the support interface.
   */
  static volatile int i;

  i = 0;
  while (nanoseconds > 0) {
    i += AS_ITER_NANOSECS;
    nanoseconds -= AS_ITER_NANOSECS;
    if (i >= 1000000) {     /* one 'as_yield' call approx. every millisecond */
      as_yield ();
      i -= 1000000;
    }
  }
}



/********* Init/Done *********/
#if AS_OS_POSIX

void as_support_init(void) {
  
    //Open as_control driver...
    as_control_fd = open("/dev/as_control", O_RDWR);
    if (as_control_fd == 0) {
        perror("fopen()");
        printf("Cannot open /dev/as_control.\n");
        exit(1);
    }

    /* Open as_regio_global device */
    as_regio_fd = open("/dev/as_regio_global", O_RDWR);
    if (as_regio_fd == 0) {
        perror("fopen()");
        printf("Cannot open /dev/as_regio_global.\n");
        exit(1);
    }
}

void as_support_done(void) {
    close(as_control_fd);
    close(as_regio_fd);
}

#else


void as_support_init () {
}


void as_support_done () {
}

#endif /* AS_OS_POSIX */

#endif /* !AS_WITH_MULTIPROCESSING */



/***************************** OS Wrappers: POSIX ******************************/


#if AS_WITH_MULTIPROCESSING && AS_OS_POSIX && !AS_OS_LINUX_KERNEL

#define SERIALIZE_TASKLETS 1            /* if set, tasklets do not need to be synchronized with the main thread */
#define TASKLETS_SLEEP_TIME 100000000   /* number of nanoseconds between tasklet iterations */


static struct as_thread_s tasklet_thread;
static volatile int tasklets_thread_quit;
#if SERIALIZE_TASKLETS
static struct as_mutex_s tasklet_m;
#endif


#include <pthread.h>
#include <time.h>       /* for 'nanosleep' */



/********** Tasklets **********/


void as_yield () {
#if SERIALIZE_TASKLETS
  as_mutex_lock (&tasklet_m);
  as_mutex_unlock (&tasklet_m);
#endif
}


static void *posix_thread_routine (void *data) {
  struct timespec ts;
  int n;

  ts.tv_sec = 0;
  ts.tv_nsec = TASKLETS_SLEEP_TIME;
  while (!tasklets_thread_quit) {
#if SERIALIZE_TASKLETS
    as_mutex_lock (&tasklet_m);
#endif
    for (n = 0; n < tasklets_top; n++)
      tasklets[n].func (tasklets[n].data);
#if SERIALIZE_TASKLETS
    as_mutex_unlock (&tasklet_m);
#endif
    nanosleep (&ts, NULL);    /* We do not care about a potential pre-mature wakeup due to a signal. */
  }
}



/********** as_sleep ***********/


void as_sleep (int nanoseconds) {
  struct timespec ts, rem;

  ts.tv_sec = nanoseconds / 1000000000;
  ts.tv_nsec = nanoseconds % 1000000000;
  while (nanosleep (&ts, &rem) < 0) ts = rem;
    /* Notes: 1. This loop may in total last longer than 'nanoseconds' (see nanosleep(2) ).
     *        2. The loop should probably do some more sanity checks.
     */
}



/********** as_thread **********/


struct as_thread_s {
  pthread_t pthread;
};


struct as_thread_s *as_thread_start (as_thread_func_f *func, void *data) {
  struct as_thread_s *thread;

  thread = MALLOC (struct as_thread_s, 1);
  ASSERT (pthread_create (&thread->pthread, NULL, func, data) == 0);
  return thread;
}


void *as_thread_join (struct as_thread_s *thread) {
  void *ret;
  
  ASSERT (pthread_join (thread->pthread, &ret) == 0);
  free (thread);
  return ret;
}



/********** as_mutex **********/


struct as_mutex_s {
  pthread_mutex_t pmutex;
};


struct as_mutex_s *as_mutex_new () {
  struct as_mutex_s *mutex;

  mutex = MALLOC (struct as_mutex_s, 1);
  pthread_mutex_init (&mutex->pmutex, NULL);
  return mutex;
}


void as_mutex_del (struct as_mutex_s *mutex) {
  pthread_mutex_destroy (&mutex->pmutex);
  free (mutex);
}


void as_mutex_lock (struct as_mutex_s *mutex) {
  pthread_mutex_lock (&mutex->pmutex);
}


AS_BOOL as_mutex_trylock (struct as_mutex_s *mutex) {
  return pthread_mutex_trylock (&mutex->pmutex) == 0;
}


void as_mutex_unlock (struct as_mutex_s *mutex) {
  pthread_mutex_unlock (&mutex->pmutex);
}



/********** as_cond **********/


struct as_cond_s {
  pthread_cond_t pcond;
};


struct as_cond_s *as_cond_new () {
  struct as_cond_s *cond;

  cond = MALLOC (struct as_cond_s, 1);
  pthread_cond_init (&cond->pcond, NULL);
  return cond;  
}


void as_cond_del (struct as_cond_s *cond) {
  pthread_cond_destroy (&cond->pcond);
  free (cond);
}


void as_cond_wait (struct as_cond_s *cond, struct as_mutex_s *mutex) {
  pthread_cond_wait (&cond->pcond, &mutex->pmutex);
}


void as_cond_signal (struct as_cond_s *cond) {
  pthread_cond_signal (&cond->pcond);
}


void as_cond_broadcast (struct as_cond_s *cond) {
  pthread_cond_broadcast (&cond->pcond);
}



/********* Init/Done *********/


void as_support_init () {
  tasklets_thread_quit = AS_FALSE;
#if SERIALIZE_TASKLETS
  as_mutex_lock (&tasklet_m);
#endif
  as_thread_start (posix_thread_routine, NULL);
}


void as_support_done () {
  tasklets_thread_quit = AS_TRUE;
#if SERIALIZE_TASKLETS
  as_mutex_unlock (&tasklet_m);
#endif
  as_thread_join (&tasklet_thread);
}



#endif /* AS_WITH_MULTIPROCESSING && AS_OS_POSIX && AS_OS_LINUX_KERNEL == 0*/
