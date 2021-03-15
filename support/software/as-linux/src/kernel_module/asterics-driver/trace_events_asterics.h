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
--! @file       trace_events_asterics.h
--! @brief      Contains definitions for trace points as well as formatting.
--------------------------------------------------------------------------------*/

#undef TRACE_SYSTEM
#define TRACE_SYSTEM asterics

#include "as_support.h"
#include <linux/tracepoint.h>
TRACE_EVENT(asterics_start_transfer, 
        TP_PROTO(as_hardware_address_t buffer_base_addr, as_hardware_address_t buffer_end_addr),
        TP_ARGS(buffer_base_addr, buffer_end_addr),
        TP_STRUCT__entry(
          __field(	as_hardware_address_t,	buffer_base_addr			)
          __field(	as_hardware_address_t,	buffer_end_addr			)
        ),
        TP_fast_assign(
          __entry->buffer_base_addr = buffer_base_addr;
          __entry->buffer_end_addr = buffer_end_addr;
        ),
        TP_printk("\nBuffer Addr: \t\t%x\nCurrent Addr: \t\t%x", __entry->buffer_base_addr, __entry->buffer_end_addr)
        );

TRACE_EVENT(asterics_finished_transfer, 
        TP_PROTO(as_hardware_address_t buffer_base_addr, as_hardware_address_t buffer_end_addr),
        TP_ARGS(buffer_base_addr, buffer_end_addr),
        TP_STRUCT__entry(
          __field(	as_hardware_address_t,	buffer_base_addr			)
          __field(	as_hardware_address_t,	buffer_end_addr			)
        ),
        TP_fast_assign(
          __entry->buffer_base_addr = buffer_base_addr;
          __entry->buffer_end_addr = buffer_end_addr;
        ),
        TP_printk("\nBuffer Addr: \t\t%x\nCurrent Addr: \t\t%x", __entry->buffer_base_addr, __entry->buffer_end_addr)
        );

TRACE_EVENT(asterics_enqueued, 
        TP_PROTO(as_buffer_obj_t *buffer_obj),
        TP_ARGS(buffer_obj),
        TP_STRUCT__entry(
          __field_struct(	as_buffer_obj_t,	buffer_obj			)
        ),
        TP_fast_assign(
          __entry->buffer_obj = *buffer_obj;
        ),
        TP_printk("\nBuffer Addr: \t\t%x\nState: \t\t%x", __entry->buffer_obj.buffer_baseaddr_phys, __entry->buffer_obj.state)
        );

TRACE_EVENT(asterics_dequeued, 
        TP_PROTO(as_buffer_obj_t *buffer_obj),
        TP_ARGS(buffer_obj),
        TP_STRUCT__entry(
          __field_struct(	as_buffer_obj_t,	buffer_obj			)
        ),
        TP_fast_assign(
          __entry->buffer_obj = *buffer_obj;
        ),
        TP_printk("\nBuffer Addr: \t\t%x\nState: \t\t%x", __entry->buffer_obj.buffer_baseaddr_phys, __entry->buffer_obj.state)
        );

#undef TRACE_INCLUDE_PATH
#undef TRACE_INCLUDE_FILE
#define TRACE_INCLUDE_PATH .
#define TRACE_INCLUDE_FILE trace_events_asterics
#include <trace/define_trace.h>
