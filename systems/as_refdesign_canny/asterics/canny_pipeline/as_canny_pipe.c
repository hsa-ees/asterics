/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework.
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Module:         as_canny_pipe
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Author:         Philip Manke
--
-- Modified:
--
-- Description:    Driver (source file) for the canny reference systems canny pipeline.
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
 * @file  as_canny_pipe.c
 * @brief Driver (source file) for the canny reference systems canny pipeline.
 */

 #include "as_canny_pipe.h"

void as_canny_pipe_reset(uint32_t* base_addr){
  as_window_pipe_reset(base_addr);
}

void as_canny_pipe_flush(uint32_t* base_addr){
  as_window_pipe_flush(base_addr);
}

uint32_t as_canny_pipe_is_ready(uint32_t* base_addr){
  return is_as_window_pipe_ready(base_addr);
}

uint32_t as_canny_pipe_get_state_reg(uint32_t* base_addr){
  return as_window_pipe_get_state_reg(base_addr);
}

uint32_t as_canny_pipe_get_control_reg(uint32_t* base_addr){
  return as_window_pipe_get_control_reg(base_addr);
}

void as_canny_pipe_set_thresholds(uint32_t* base_addr, uint8_t high, uint8_t low){
  as_reg_write(base_addr + AS_CANNY_PIPE_THRESHOLD_REG_OFFSET, (high << 8) | low);
}

uint32_t as_canny_pipe_get_feature_count(uint32_t* base_addr){
  return (uint32_t) as_reg_read(base_addr + AS_CANNY_PIPE_FEATURE_COUNT_REG_OFFSET);
}

void as_canny_pipe_decode_feature(uint32_t* feature_memory, uint32_t feature_number, canny_feature* feature){
  uint32_t val = feature_memory[feature_number];
  feature->value = (uint16_t) (val & AS_CANNY_PIPE_FEATURE_MASK_VALUE);
  val = val >> AS_CANNY_PIPE_FEATURE_VALUE_WIDTH;
  feature->xcoordinate = (uint16_t) (val & AS_CANNY_PIPE_FEATURE_MASK_XCOORD);
  val = val >> AS_CANNY_PIPE_FEATURE_XCOORD_WIDTH;
  feature->ycoordinate = (uint16_t) (val & AS_CANNY_PIPE_FEATURE_MASK_YCOORD);
}
