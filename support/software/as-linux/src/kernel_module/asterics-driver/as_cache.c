/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework and the VEARS core.
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Author:         Patrick Zacharias
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
--! @file       as_cache.c
--! @brief      Functions definitions for (un-)mapping memory areas for DMA use.
--------------------------------------------------------------------------------*/

#include "as_cache.h"

#if AS_OS_LINUX_KERNEL
extern struct device *asterics_device;
#include <linux/dma-direction.h>
#include <linux/dma-mapping.h>
void as_unmap_single(as_dma_address_t dma_addr, size_t bytes, as_buffer_dir_t direction, AS_BOOL cpu_sync) {
  unsigned long attr = cpu_sync ? 0 : DMA_ATTR_SKIP_CPU_SYNC;
  if (direction == AS_BUFFER_DIR_FROM_DEV)
    dma_unmap_single_attrs(asterics_device, dma_addr, bytes, DMA_FROM_DEVICE, attr);
  else
    dma_unmap_single_attrs(asterics_device, dma_addr, bytes, DMA_TO_DEVICE, attr);
}
as_dma_address_t as_map_single(as_kernel_address_t addr, size_t bytes, as_buffer_dir_t direction, AS_BOOL cpu_sync) {
  as_dma_address_t ret;
  unsigned long attr = cpu_sync ? 0 : DMA_ATTR_SKIP_CPU_SYNC;
  if (direction == AS_BUFFER_DIR_FROM_DEV)
    ret = dma_map_single_attrs(asterics_device, addr, bytes, DMA_FROM_DEVICE, attr);
  else
    ret = dma_map_single_attrs(asterics_device, addr, bytes, DMA_TO_DEVICE, attr);
  return ret;
}
#else
void as_unmap_single(as_dma_address_t dma_addr, size_t bytes, as_buffer_dir_t direction, AS_BOOL cpu_sync) {
  as_hardware_address_t addr = (as_hardware_address_t)dma_addr;
  if ((direction == AS_BUFFER_DIR_FROM_DEV) && cpu_sync)
    as_dcache_invalidate_range(addr, bytes);
  return addr;
}
as_dma_address_t as_map_single(as_kernel_address_t addr, size_t bytes, as_buffer_dir_t direction, AS_BOOL cpu_sync) {
  if ((direction == AS_BUFFER_DIR_TO_DEV) && cpu_sync)
    as_dcache_flush_range((as_hardware_address_t)addr, bytes);
  return (as_dma_address_t)addr;
}
#endif
