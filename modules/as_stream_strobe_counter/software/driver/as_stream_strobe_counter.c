/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework.
--  (C) 2021 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Module:         as_stream_strobe_counter
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Author:         Philip Manke
--
-- Modified:
--
-- Description:    Driver (source file) for as_stream_strobe_counter module
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
 * @file  as_stream_strobe_counter.c
 * @brief Driver (source file) for as_stream_strobe_counter module.
 */

#include "as_stream_strobe_counter.h"

void as_stream_strobe_counter_reset(uint32_t *base_addr) {
  as_reg_write(base_addr + AS_STREAM_STROBE_COUNTER_CONTROL_REG_OFFSET,
               1 << AS_STREAM_STROBE_COUNTER_CONTROL_RESET_OFFSET);
  as_reg_write(base_addr + AS_STREAM_STROBE_COUNTER_CONTROL_REG_OFFSET, 0x0);
}

void as_stream_strobe_counter_strobe_enable(uint32_t *base_addr) {
  as_reg_write(base_addr + AS_STREAM_STROBE_COUNTER_CONTROL_REG_OFFSET,
               1 << AS_STREAM_STROBE_COUNTER_CONTROL_ENABLE_OFFSET);
}

void as_stream_strobe_counter_strobe_disable(uint32_t *base_addr) {
  as_reg_write(base_addr + AS_STREAM_STROBE_COUNTER_CONTROL_REG_OFFSET, 0x0);
};

uint32_t as_stream_strobe_counter_get_count_value(uint32_t *base_addr) {
  return as_reg_read(base_addr + AS_STREAM_STROBE_COUNTER_STATUS_REG_OFFSET);
}