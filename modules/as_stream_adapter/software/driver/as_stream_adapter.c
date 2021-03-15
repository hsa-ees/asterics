/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Module:         as_stream_adapter
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Author:         Michael Schaeferling
--
-- Modified:       
--
-- Description:    Driver (source file) for as_stream_adapter module
--                 to set needed parameters.
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
--------------------------------------------------------------------------------*/

/** 
 * @file  as_stream_adapter.c
 * @brief Driver (source file) for as_stream_adapter module.
 */

#include "as_stream_adapter.h"

void as_stream_adapter_reset(uint32_t* base_addr){
    as_reg_write(
        base_addr + AS_STREAM_ADAPTER_CONTROL_REG_OFFSET,
        (1 << AS_STREAM_ADAPTER_CONTROL_RESET_OFFSET)
    );
    as_reg_write(base_addr + AS_STREAM_ADAPTER_CONTROL_REG_OFFSET, 0);
}

void as_stream_adapter_strobe_counters_reset(uint32_t* base_addr){
    as_reg_write(
        base_addr + AS_STREAM_ADAPTER_CONTROL_REG_OFFSET,
        (1 << AS_STREAM_ADAPTER_CONTROL_COUNTER_RESET_OFFSET)
    );
    as_reg_write(base_addr + AS_STREAM_ADAPTER_CONTROL_REG_OFFSET, 0);
}



AS_BOOL as_stream_adapter_is_buffer_full(uint32_t* base_addr){
    return (as_reg_read(base_addr + AS_STREAM_ADAPTER_STATUS_REG_OFFSET)
            & (1 << AS_STREAM_ADAPTER_STATUS_FULL_OFFSET)
        ) ? AS_TRUE : AS_FALSE;
}

AS_BOOL as_stream_adapter_is_buffer_empty(uint32_t* base_addr){
    return (as_reg_read(base_addr + AS_STREAM_ADAPTER_STATUS_REG_OFFSET)
            & (1 << AS_STREAM_ADAPTER_STATUS_EMPTY_OFFSET)
        ) ? AS_TRUE : AS_FALSE;
}

AS_BOOL as_stream_adapter_is_strobe_counting_enabled(uint32_t* base_addr){
    return (as_reg_read(base_addr + AS_STREAM_ADAPTER_STATUS_REG_OFFSET)
            & (1 << AS_STREAM_ADAPTER_STATUS_COUNTERS_ENABLED_OFFSET)
        ) ? AS_TRUE : AS_FALSE;
}

uint32_t as_stream_adapter_get_buffer_size(uint32_t* base_addr){
    return (uint32_t) (
        as_reg_read(base_addr + AS_STREAM_ADAPTER_STATUS_REG_OFFSET) 
        >> (32 - AS_STREAM_ADAPTER_BUFFER_SIZE_BITWIDTH)
    );
}

uint32_t as_stream_adapter_get_strobe_in_count(uint32_t* base_addr){
    return (uint32_t) as_reg_read(base_addr + AS_STREAM_ADAPTER_STROBE_IN_REG_OFFSET);
}

uint32_t as_stream_adapter_get_strobe_out_count(uint32_t* base_addr){
    return (uint32_t) as_reg_read(base_addr + AS_STREAM_ADAPTER_STROBE_OUT_REG_OFFSET);
}
