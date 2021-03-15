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
--! @file       as_cache.h
--! @brief      Functions declarations for (un-)mapping memory areas for DMA use.
--------------------------------------------------------------------------------*/

#ifndef AS_CACHE_H
#define AS_CACHE_H
#include "as_support.h"
#include "as_buffer.h"

#if AS_OS_LINUX_KERNEL
#include <linux/types.h>
typedef dma_addr_t as_dma_address_t;
#else
typedef as_hardware_address_t as_dma_address_t;
#endif

/**
 * @brief Unmap DMA address at end of transfer 
 * @param dma_addr Handle of DMA Address to be unmapped
 * @param bytes Size of area to be unmapped
 * @param direction Direction which has been used during mapping
 * @param cpu_sync Whether changes should be synced with CPU-cache
 * 
 * Unmaps a DMA address previously mapped using as_map_single.
 * On bare metal system if cpu_sync is false, does nothing.
 * On Linux this currently makes sure that the page is being unmapped.
 * 
 * If cpu_sync is set and direction is AS_BUFFER_DIR_FROM_DEVICE,
 * the CPU-cache will be invalidated.
*/
void as_unmap_single(as_dma_address_t dma_addr, size_t bytes, as_buffer_dir_t direction, AS_BOOL cpu_sync);
/**
 * @brief Map virtual kernel address for DMA
 * @param addr Pointer to memory address to be prepare for DMA
 * @param bytes Size of area to be unmapped
 * @param direction Direction which has been used during mapping
 * @param cpu_sync Whether changes should be synced with CPU-cache
 * @return DMA address handle
 * 
 * Maps a virtual kernel address for DMA.
 * On bare metal system if cpu_sync is false, does nothing.
 * On Linux this currently makes sure that the page is being mapped.
 * 
 * If cpu_sync is set and direction is AS_BUFFER_DIR_TO_DEVICE,
 * the CPU-cache will be flushed, ensuring that data on addr
 * will be visible by other devices on the bus.
*/
as_dma_address_t as_map_single(as_kernel_address_t addr, size_t bytes, as_buffer_dir_t direction, AS_BOOL cpu_sync);
#endif
