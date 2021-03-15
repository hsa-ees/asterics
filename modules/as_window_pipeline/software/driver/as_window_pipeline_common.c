/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework.
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Module:         as_window_pipeline_common
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Author:         Philip Manke
--
-- Modified:
--
-- Description:    Common driver (source file) for as_window_pipeline modules.
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
 * @file  as_window_pipeline_common.c
 * @brief Common driver (source file) for as_window_pipeline modules.
 */

#include "as_window_pipeline_common.h"

void as_window_pipe_reset(uint32_t* base_addr){
  as_reg_write(base_addr + AS_WINDOW_PIPELINE_COMMON_CONTROL_REG_OFFSET, 0x1);
}

void as_window_pipe_flush(uint32_t* base_addr){
  as_reg_write(base_addr + AS_WINDOW_PIPELINE_COMMON_CONTROL_REG_OFFSET, 0x2);
}

uint8_t is_as_window_pipe_ready(uint32_t* base_addr){
  return (uint8_t) (as_reg_read(base_addr + AS_WINDOW_PIPELINE_COMMON_STATUS_REG_OFFSET) & 0x1);
}

uint32_t as_window_pipe_get_state_reg(uint32_t* base_addr){
  return as_reg_read(base_addr + AS_WINDOW_PIPELINE_COMMON_STATUS_REG_OFFSET);
}

uint32_t as_window_pipe_get_control_reg(uint32_t* base_addr){
  return as_reg_read(base_addr + AS_WINDOW_PIPELINE_COMMON_CONTROL_REG_OFFSET);
}
