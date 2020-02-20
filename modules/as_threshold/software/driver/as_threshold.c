/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Module:         as_threshold
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Michael Schaeferling
--
-- Modified:       
--
-- Description:    Driver (source file) for as_threshold module
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
 * @file  as_threshold.c
 * @brief Driver (source file) for as_threshold module.
 */


#include "as_threshold.h"


uint32_t as_threshold_get_t1(uint32_t* base_addr){
    uint32_t regval;
    regval = as_reg_read( as_module_reg(base_addr, AS_THRESHOLD_PARAMETER_1_REG_OFFSET));
    regval &= 0xfff;
    return regval;
}

void as_threshold_set_t1(uint32_t* base_addr, uint32_t value){
    uint32_t regval;
    regval = as_reg_read( as_module_reg(base_addr, AS_THRESHOLD_PARAMETER_1_REG_OFFSET));
    regval &= 0xfffff000; /* clear old t1 value */
    regval = regval | (value & 0x00000fff); /* set new t1 value */
    as_reg_write( as_module_reg(base_addr, AS_THRESHOLD_PARAMETER_1_REG_OFFSET), regval);
}


uint32_t as_threshold_get_t2(uint32_t* base_addr){
    uint32_t regval;
    regval = as_reg_read( as_module_reg(base_addr, AS_THRESHOLD_PARAMETER_1_REG_OFFSET));
    regval = (regval >> 12) & 0x00000fff;
    return regval;
}

void as_threshold_set_t2(uint32_t* base_addr, uint32_t value){
    uint32_t regval;
    regval = as_reg_read( as_module_reg(base_addr, AS_THRESHOLD_PARAMETER_1_REG_OFFSET));
    regval &= 0xff000fff; /* clear old t2 value */
    regval = regval | ((value << 12) & 0x00fff000); /* set new t2 value */
    as_reg_write( as_module_reg(base_addr, AS_THRESHOLD_PARAMETER_1_REG_OFFSET), regval);
}


void as_threshold_enable_a_value(uint32_t* base_addr, AS_BOOL enable){
    uint32_t regval;
    regval = as_reg_read( as_module_reg(base_addr, AS_THRESHOLD_PARAMETER_1_REG_OFFSET));
    if (enable == AS_FALSE) {
        regval &= ~AS_THRESHOLD_ENABLE_A_VALUE_BIT_MASK; /* clear a_enable */
    } else {
        regval |= AS_THRESHOLD_ENABLE_A_VALUE_BIT_MASK; /* set a_enable */
    }
    as_reg_write( as_module_reg(base_addr, AS_THRESHOLD_PARAMETER_1_REG_OFFSET), regval);
}

void as_threshold_enable_b_value(uint32_t* base_addr, AS_BOOL enable){
    uint32_t regval;
    regval = as_reg_read( as_module_reg(base_addr, AS_THRESHOLD_PARAMETER_1_REG_OFFSET));
    if (enable == AS_FALSE) {
        regval &= ~AS_THRESHOLD_ENABLE_B_VALUE_BIT_MASK; /* clear b_enable */
    } else {
        regval |= AS_THRESHOLD_ENABLE_B_VALUE_BIT_MASK; /* set b_enable */
    }
    as_reg_write( as_module_reg(base_addr, AS_THRESHOLD_PARAMETER_1_REG_OFFSET), regval);
}

void as_threshold_enable_c_value(uint32_t* base_addr, AS_BOOL enable){
    uint32_t regval;
    regval = as_reg_read( as_module_reg(base_addr, AS_THRESHOLD_PARAMETER_1_REG_OFFSET));
    if (enable == AS_FALSE) {
        regval &= ~AS_THRESHOLD_ENABLE_C_VALUE_BIT_MASK; /* clear c_enable */
    } else {
        regval |= AS_THRESHOLD_ENABLE_C_VALUE_BIT_MASK; /* set c_enable */
    }
    as_reg_write( as_module_reg(base_addr, AS_THRESHOLD_PARAMETER_1_REG_OFFSET), regval);
}


void as_threshold_set_a_value(uint32_t* base_addr, uint32_t value){
    uint32_t regval;
    regval = as_reg_read( as_module_reg(base_addr, AS_THRESHOLD_PARAMETER_2_REG_OFFSET));
    regval &= 0xfffff000; /* clear old a value */
    regval = regval | (value & 0x00000fff); /* set new a value */
    as_reg_write( as_module_reg(base_addr, AS_THRESHOLD_PARAMETER_2_REG_OFFSET), regval);
}

void as_threshold_set_b_value(uint32_t* base_addr, uint32_t value){
    uint32_t regval;
    regval = as_reg_read( as_module_reg(base_addr, AS_THRESHOLD_PARAMETER_2_REG_OFFSET));
    regval &= 0xff000fff; /* clear old b value */
    regval = regval | ((value<<12) & 0x00fff000); /* set new b value */
    as_reg_write( as_module_reg(base_addr, AS_THRESHOLD_PARAMETER_2_REG_OFFSET), regval);
}

void as_threshold_set_c_value(uint32_t* base_addr, uint32_t value){
    uint32_t regval;
    /* upper 4 bits of c are within reg 1 */
    regval = as_reg_read( as_module_reg(base_addr, AS_THRESHOLD_PARAMETER_1_REG_OFFSET));
    regval &= 0xf0ffffff; /* clear old c_upper value */
    regval = regval | ((value<<16) & 0x0f000000); /* set new c_upper value */
    as_reg_write( as_module_reg(base_addr, AS_THRESHOLD_PARAMETER_1_REG_OFFSET), regval);
    /* lower 8 bits of c are within reg 2 */
    regval = as_reg_read( as_module_reg(base_addr, AS_THRESHOLD_PARAMETER_2_REG_OFFSET));
    regval &= 0x00ffffff; /* clear old c_lower value */
    regval = regval | ((value<<24) & 0xff000000); /* set new c_lower value */
    as_reg_write( as_module_reg(base_addr, AS_THRESHOLD_PARAMETER_2_REG_OFFSET), regval);
}
