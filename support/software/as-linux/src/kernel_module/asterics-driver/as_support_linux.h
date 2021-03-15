#pragma once
#include "as_linux_kernel_if.h"

/********* Linux kernel module utility ********/

#if AS_OS_LINUX_KERNEL

void fill_as_regio_params(uint32_t cmd, uint32_t address, uint32_t value, as_ioctl_params_t *structure);
void as_reg_write(as_hardware_address_t addr, uint32_t val);
uint32_t as_reg_read(as_hardware_address_t addr);

#endif /* AS_OS_LINUX_KERNEL */

#if AS_OS_POSIX

void fill_as_regio_params(uint32_t cmd, uint32_t address, uint32_t value, as_ioctl_params_t *structure);
void as_reg_write(as_hardware_address_t addr, uint32_t val);
uint32_t as_reg_read(as_hardware_address_t addr);

static inline void as_dcache_invalidate_range(as_hardware_address_t addr, uint32_t len) {}
static inline void as_dcache_flush(void) {}
static inline void as_dcache_flush_range(as_hardware_address_t addr, uint32_t len) {}

#endif /* AS_OS_POSIX */
