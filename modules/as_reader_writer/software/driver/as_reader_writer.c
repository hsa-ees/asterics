/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework.
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Module:         as_reader_writer
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Alexander Zoellner
--
-- Modified:       
--
-- Description:    Implements software drivers for using the
--                 as_reader_writer modules.
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
 * @file  as_reader_writer.c
 * @brief Driver (source file) for as_reader_writer module.
 */

#include "as_reader_writer.h"

/* Module Init Function */

void as_reader_writer_init(as_hardware_address_t base_addr, as_reader_writer_config_t *config) {
  if (config != NULL) {
    as_reader_writer_set_section_offset(base_addr, (*config).section_offset);
    as_reader_writer_set_section_addr(base_addr, (*config).first_section_addr);
    as_reader_writer_set_section_size(base_addr, (*config).section_size);
    as_reader_writer_set_section_count(base_addr, (*config).section_count);
    as_reader_writer_set_max_burst_length(base_addr, (*config).max_burst_length);
  }
  /* Write Default Values to Registers */
  else {
    as_reader_writer_set_section_offset(base_addr, (uint32_t)AS_READER_WRITER_DEFAULT_SECTION_OFFSET);
    as_reader_writer_set_section_size(base_addr, (uint32_t)AS_READER_WRITER_DEFAULT_SECTION_SIZE);
    as_reader_writer_set_section_count(base_addr, (uint32_t)AS_READER_WRITER_DEFAULT_SECTION_COUNT);
    as_reader_writer_set_max_burst_length(base_addr, (uint32_t)AS_READER_WRITER_DEFAULT_MAX_BURST_LENGTH);
  }
  /* Reset */
  as_reader_writer_reset(base_addr);
}

/* Register Read Functions */

as_hardware_address_t as_reader_writer_get_cur_hw_addr(as_hardware_address_t base_addr) {
  return (as_hardware_address_t)as_reg_read(as_module_reg(base_addr, AS_READER_WRITER_REG_CUR_HW_ADDR_OFFSET));
}

/* Memwriter only */
as_hardware_address_t as_writer_get_last_data_unit_complete_addr(as_hardware_address_t base_addr) {
  return (as_hardware_address_t)as_reg_read(as_module_reg(base_addr, AS_WRITER_REG_LAST_DATA_UNIT_COMPLETE_ADDR_OFFSET));
}

uint32_t as_writer_get_cur_unit_count(as_hardware_address_t base_addr) {
  return as_reg_read(as_module_reg(base_addr, AS_WRITER_REG_CURRENT_UNIT_COUNT));
}

/* Register Write Functions */

void as_reader_writer_set_section_addr(as_hardware_address_t base_addr, as_hardware_address_t value) {
  as_reg_write(as_module_reg(base_addr, AS_READER_WRITER_REG_SECTION_ADDR_OFFSET), (uint32_t)value);
}

void as_reader_writer_set_section_offset(as_hardware_address_t base_addr, uint32_t value) {
  as_reg_write(as_module_reg(base_addr, AS_READER_WRITER_REG_SECTION_OFFSET_OFFSET), value);
}

void as_reader_writer_set_section_size(as_hardware_address_t base_addr, uint32_t value) {
  as_reg_write(as_module_reg(base_addr, AS_READER_WRITER_REG_SECTION_SIZE_OFFSET), value);
}
void as_reader_writer_set_section_count(as_hardware_address_t base_addr, uint32_t value) {
  as_reg_write(as_module_reg(base_addr, AS_READER_WRITER_REG_SECTION_COUNT_OFFSET), value);
}

void as_reader_writer_set_max_burst_length(as_hardware_address_t base_addr, uint32_t value) {
  as_reg_write(as_module_reg(base_addr, AS_READER_WRITER_REG_MAX_BURST_LENGTH_OFFSET), value);
}

/* State Register Read Functions */

AS_BOOL as_reader_writer_is_done(as_hardware_address_t base_addr) {
  return as_reg_read_masked(as_module_reg(base_addr, AS_READER_WRITER_STATE_CONTROL_REG_OFFSET), AS_READER_WRITER_DONE_MASK) ? AS_TRUE : AS_FALSE;
}

AS_BOOL as_reader_writer_is_busy(as_hardware_address_t base_addr) {
  return as_reg_read_masked(as_module_reg(base_addr, AS_READER_WRITER_STATE_CONTROL_REG_OFFSET), AS_READER_WRITER_BUSY_MASK) ? AS_TRUE : AS_FALSE;
}

AS_BOOL as_reader_writer_is_pending_go(as_hardware_address_t base_addr) {
  return as_reg_read_masked(as_module_reg(base_addr, AS_READER_WRITER_STATE_CONTROL_REG_OFFSET), AS_READER_WRITER_PENDING_GO_MASK) ? AS_TRUE : AS_FALSE;
}

/* Memwriter only */
AS_BOOL as_writer_is_sync_error(as_hardware_address_t base_addr) {
  return as_reg_read_masked(as_module_reg(base_addr, AS_READER_WRITER_STATE_CONTROL_REG_OFFSET), AS_READER_WRITER_SYNC_ERROR_MASK) ? AS_TRUE : AS_FALSE;
}

AS_BOOL as_writer_is_flushable_data(as_hardware_address_t base_addr) {
  return as_reg_read_masked(as_module_reg(base_addr, AS_READER_WRITER_STATE_CONTROL_REG_OFFSET), AS_WRITER_FLUSHABLE_DATA_MASK) ? AS_TRUE : AS_FALSE;
}

AS_BOOL as_writer_is_set_enable(as_hardware_address_t base_addr) {
  return as_reg_read_masked(as_module_reg(base_addr, AS_READER_WRITER_STATE_CONTROL_REG_OFFSET), AS_WRITER_SET_ENABLE_MASK) ? AS_TRUE : AS_FALSE;
}

/* Control Register Write Functions */

void as_reader_writer_reset(as_hardware_address_t base_addr) {
  as_reg_write_masked(as_module_reg(base_addr, AS_READER_WRITER_STATE_CONTROL_REG_OFFSET), AS_READER_WRITER_RESET_MASK, 0xffffffff);
}

void as_reader_writer_set_go(as_hardware_address_t base_addr) {
  as_reg_write_masked(as_module_reg(base_addr, AS_READER_WRITER_STATE_CONTROL_REG_OFFSET), AS_READER_WRITER_GO_MASK, 0xffffffff);
}

/* Memwriter only */
void as_writer_set_enable(as_hardware_address_t base_addr) {
  as_reg_write_masked(as_module_reg(base_addr, AS_READER_WRITER_STATE_CONTROL_REG_OFFSET), AS_WRITER_ENABLE_MASK, 0xffffffff);
}

void as_writer_set_disable(as_hardware_address_t base_addr) {
  as_reg_write_masked(as_module_reg(base_addr, AS_READER_WRITER_STATE_CONTROL_REG_OFFSET), AS_WRITER_DISABLE_MASK, 0xffffffff);
}

void as_writer_set_enable_on_data_unit_complete(as_hardware_address_t base_addr) {
  as_reg_write_masked(as_module_reg(base_addr, AS_READER_WRITER_STATE_CONTROL_REG_OFFSET), AS_WRITER_ENABLE_ON_DATA_UNIT_COMPLETE_MASK, 0xffffffff);
}

void as_writer_set_single_shot(as_hardware_address_t base_addr) {
  as_reg_write_masked(as_module_reg(base_addr, AS_READER_WRITER_STATE_CONTROL_REG_OFFSET), AS_WRITER_SINGLE_SHOT_MASK, 0xffffffff);
}

void as_writer_set_disable_on_no_go(as_hardware_address_t base_addr) {
  as_reg_write_masked(as_module_reg(base_addr, AS_READER_WRITER_STATE_CONTROL_REG_OFFSET), AS_WRITER_DISABLE_ON_NO_GO_MASK, 0xffffffff);
}

void as_writer_set_flush(as_hardware_address_t base_addr) {
  as_reg_write_masked(as_module_reg(base_addr, AS_READER_WRITER_STATE_CONTROL_REG_OFFSET), AS_WRITER_FLUSH_DATA_MASK, 0xffffffff);
}
