/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Module:         as_iic
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Author:         Philip Manke
--
-- Modified:       2017-08-30 Philip Manke
--
-- Description:    Driver (source file) for the as_iic module.
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
 * @file  as_iic.c
 * @brief Driver (source file) for as_iic module.
 */
 
 
#include "as_iic.h"

/***** Debug things *****/

#ifdef AS_IIC_DEBUG
const char* as_iic_err_to_str(uint8_t error_number){
	switch(error_number){
		case 0x0: return "OK";
		case 0x1: return "Hardware not ready!";
		case 0x2: return "Timeout: IO not ready!";
		case 0x3: return "Timeout: Send address";
		case 0x4: return "Timeout: Send data";
		case 0x5: return "Timeout: Receive data";
		case 0x6: return "NACK after address!";
		case 0x7: return "NACK after data!";
		case 0x8: return "NACK after register!";
		case 0x9: return "IO not ready after read!";
		case 0xA: return "Timeout - general transmission";
		case 0xB: return "No acknowledgement from slave";
		case 0xC: return "Invalid frequency. 10kHz - 1MHz is supported!";
		case 0xD: return "The hardware is uninitialized! Call as_iic_init first!";
		default : return "Unkown error number!";
	}
}
#endif

/***** Get raw register contents *****/

uint32_t as_iic_get_status(uint32_t* base_addr){
	return as_reg_read(base_addr + AS_IIC_STATUSCONTROL_OFFSET);
}

uint32_t as_iic_get_data_rx(uint32_t* base_addr){
	return as_reg_read(base_addr + AS_IIC_DATA_RX_OFFSET);
}

uint32_t as_iic_get_data_tx(uint32_t* base_addr){
	return as_reg_read(base_addr + AS_IIC_DATA_TX_OFFSET);
}

/***** Set register values *****/

void as_iic_set_control(uint32_t* base_addr, uint8_t control){
	as_reg_write(base_addr + AS_IIC_STATUSCONTROL_OFFSET, 
								(uint32_t) ((control & AS_IIC_CTRL_MASK) << 16));
}

void as_iic_set_data_register(uint32_t* base_addr, uint32_t data){
	as_reg_write(base_addr + AS_IIC_DATA_TX_OFFSET, data);
}

void as_iic_set_data_tx(uint32_t* base_addr, uint8_t* byte){
	as_reg_write(base_addr + AS_IIC_DATA_TX_OFFSET, (uint32_t) (*byte << 24) |
			(as_reg_read(base_addr + AS_IIC_DATA_TX_OFFSET) & AS_IIC_TX_DATA_MASK));
}

void as_iic_set_scl_div(uint32_t* base_addr, uint32_t div){
	as_reg_write(base_addr + AS_IIC_DATA_TX_OFFSET, (uint32_t) (div & AS_IIC_TX_DATA_MASK) |
			(as_reg_read(base_addr + AS_IIC_DATA_TX_OFFSET) & AS_IIC_SCL_DIV_MASK));
}

/***** Get register values *****/

uint8_t as_iic_get_rx_byte(uint32_t* base_addr){
	return (uint8_t) (as_reg_read(base_addr + AS_IIC_DATA_RX_OFFSET) >> 8);
}

uint8_t as_iic_get_status_reg(uint32_t* base_addr){
	return (uint8_t) (as_reg_read(base_addr + AS_IIC_STATUSCONTROL_OFFSET) 
											& AS_IIC_STATUS_MASK);
}

uint8_t as_iic_get_control_reg(uint32_t* base_addr){
	return (uint8_t) ((as_reg_read(base_addr + AS_IIC_STATUSCONTROL_OFFSET) 
											& AS_IIC_CTRL_READ_MASK) >> 16);
}

/***** Check as_iic status bits *****/

AS_BOOL as_iic_is_ready(uint32_t* base_addr){
	return ((as_iic_get_status_reg(base_addr) & AS_IIC_READY) > 0) ? AS_TRUE : AS_FALSE;
}

AS_BOOL as_iic_is_io_ready(uint32_t* base_addr){
	return ((as_iic_get_status_reg(base_addr) & AS_IIC_IO_READY) > 0) ? AS_TRUE : AS_FALSE;
}

AS_BOOL as_iic_is_active(uint32_t* base_addr){
	return ((as_iic_get_status_reg(base_addr) & AS_IIC_BUS_ACTIVE) > 0) ? AS_TRUE : AS_FALSE;
}

AS_BOOL as_iic_ack_received(uint32_t* base_addr){
	return ((as_iic_get_status_reg(base_addr) & AS_IIC_ACK_RECEIVED) > 0) ? AS_TRUE : AS_FALSE;
}

AS_BOOL as_iic_is_stalled(uint32_t* base_addr){
	return ((as_iic_get_status_reg(base_addr) & AS_IIC_STALLED) > 0) ? AS_TRUE : AS_FALSE;
}

AS_BOOL as_iic_is_waiting(uint32_t* base_addr){
	return ((as_iic_get_status_reg(base_addr) & AS_IIC_WAITING) > 0) ? AS_TRUE : AS_FALSE;
}

AS_BOOL as_iic_is_readwrite(uint32_t* base_addr){
	return ((as_iic_get_control_reg(base_addr) & AS_IIC_RW) > 0) ? AS_TRUE : AS_FALSE;
}

AS_BOOL as_iic_is_initialized(void){
	return as_iic_initialized_flag ? AS_TRUE : AS_FALSE;
}


/***** Set as_iic control bits *****/

void as_iic_set_transmit_start(uint32_t* base_addr){
	as_iic_set_control(base_addr, (as_iic_get_control_reg(base_addr) 	
																& (~AS_IIC_TSTART)) | AS_IIC_TSTART);
}

void as_iic_set_readwrite(uint32_t* base_addr, uint8_t value){
	if(value){
		as_iic_set_control(base_addr, (as_iic_get_control_reg(base_addr) & (~AS_IIC_RW)) | AS_IIC_RW);
	} else {
		as_iic_set_control(base_addr, as_iic_get_control_reg(base_addr) & (~AS_IIC_RW));
	}
}

void as_iic_set_transmit_stop(uint32_t* base_addr){
	as_iic_set_control(base_addr, (as_iic_get_control_reg(base_addr) 
																& (~AS_IIC_TEND)) | AS_IIC_TEND);
}

void as_iic_set_data_ready(uint32_t* base_addr){
	as_iic_set_control(base_addr, (as_iic_get_control_reg(base_addr) 
																& (~AS_IIC_DATA_READY)) | AS_IIC_DATA_READY);
}

void as_iic_set_ack_mod(uint32_t* base_addr){
	as_iic_set_control(base_addr, (as_iic_get_control_reg(base_addr) 
																& (~AS_IIC_ACK_MODIFIER)) | AS_IIC_ACK_MODIFIER);
}

void as_iic_set_initialized(uint8_t value){

	as_iic_initialized_flag = value;
}

void as_iic_reset_hw_state(uint32_t* base_addr){
	as_iic_set_control(base_addr, AS_IIC_RESET);
}

void as_iic_reset(uint32_t* base_addr){
	as_iic_set_initialized(0);
	as_iic_set_data_register(base_addr, 0);
	as_iic_reset_hw_state(base_addr);
}

/***** as_iic helper functions *****/

AS_BOOL as_iic_busy_wait_for_hwready(uint32_t* base_addr, uint32_t timeout_ns){
    uint32_t counter;
    for(counter = 0; counter < timeout_ns; counter += 100){
		if(as_iic_is_ready(base_addr)){
			return AS_TRUE;
		} else {
			as_sleep(100);
		}
	}
	return AS_FALSE;
}

AS_BOOL as_iic_busy_wait_for_wait(uint32_t* base_addr, uint32_t timeout_ns){
    uint32_t counter;
    for(counter = 0; counter < timeout_ns; counter += 100){
		if(as_iic_is_waiting(base_addr)){
			return AS_TRUE;
		} else {
			as_sleep(100);
		}
	}
	return AS_FALSE;
}

AS_BOOL as_iic_busy_wait_for_ioready(uint32_t* base_addr, uint32_t timeout_ns){
    uint32_t counter;
    for(counter = 0; counter < timeout_ns; counter += 100){
		if(as_iic_is_io_ready(base_addr)){
			return AS_TRUE;
		} else {
			as_sleep(100);
		}
	}
	return AS_FALSE;
}

uint8_t as_iic_init(uint32_t* base_addr, uint32_t iic_bus_freq){
	
	as_iic_reset(base_addr);
	
	// check if a valid frequency is entered
	// note that valid is not always possible. This depends on the hardware implementation
	if(iic_bus_freq < 10000 || iic_bus_freq > 1000000){
		return AS_IIC_ERR_FREQ_INVALID;
	}

	// wait for the hardware to set the iic_ready bit
	if(as_iic_busy_wait_for_hwready(base_addr, AS_IIC_TIMEOUT_BASE * AS_IIC_SHORT_TIMEOUT) == AS_FALSE){
		// if it takes too long, return with an error
		return AS_IIC_ERR_HW_NOT_READY;
	}
	// calculates and sets the contents of the scl-div register.
	// SCL_DIV = (System Freq / 4 * Desired IIC Bus Freq) - 2.
	as_iic_set_scl_div(base_addr, (uint32_t) ((AS_SYSTEM_CLOCK_HZ / (4 * iic_bus_freq)) - 2));
	
	// set the initialized bit.
	as_iic_set_initialized(1);
	
	return AS_IIC_OK;
}

/***** as_iic transaction parts *****/

uint8_t as_iic_start_transaction(uint32_t* base_addr, uint8_t* slave_addr, 
																	uint8_t* data, uint8_t readwrite, uint8_t modifier){
	
	// if the bus frequency hasn't been set yet, return an error
	if(as_iic_is_initialized() != AS_TRUE){
		return AS_ERR_NOT_INITIALIZED;
	}	

	// wait for the hardware to set the iic_ready bit
	if(as_iic_busy_wait_for_hwready(base_addr, AS_IIC_TIMEOUT_BASE * AS_IIC_SHORT_TIMEOUT) == AS_FALSE){
		// if it takes too long, set the reset bit
		as_iic_reset_hw_state(base_addr);
		if(as_iic_is_ready(base_addr) == AS_FALSE){
			// if it's still not ready, return an error. Something's seriously wrong.
			return AS_IIC_ERR_HW_NOT_READY;
		}
	}
	
	// make sure the address is in the correct form:
	if(readwrite){ 			   // read address:
		(*slave_addr) |= 0x01; // add one to the address, if it isn't already there.
	}
	 else {				   // write address:
		(*slave_addr) &= 0xFE; // force a 0 for the last bit, if it isn't already there.
	}
	
	// the hardware is ready. Copy the slave address to the tx data register
	as_iic_set_data_tx(base_addr, slave_addr);
	
	// start the transaction
	as_iic_set_control(base_addr, AS_IIC_TSTART);
	
	// wait for the hardware to send the address. If it takes too long, reset and return an error.
	if(as_iic_busy_wait_for_wait(base_addr, AS_IIC_TIMEOUT_BASE * AS_IIC_LONG_TIMEOUT) == AS_FALSE){
		as_iic_reset_hw_state(base_addr); 
		return AS_IIC_ERR_HW_TO_SENDADR;
	}
	// do we only need to send the address?
	if(modifier & AS_IIC_MOD_ONLY_ADDRESS){
		// yes -> stop the transaction.
		as_iic_stop_write_transaction(base_addr);
	} else { // no -> check what transaction is next:
		if(readwrite){ // read ...
			if(modifier & AS_IIC_MOD_MASTER_ACK){ // ... with master acknowledge.
				as_iic_set_control(base_addr, AS_IIC_CONT_READ | AS_IIC_ACK_MODIFIER);
			} else { // ... without master acknowledge.
				as_iic_set_control(base_addr, AS_IIC_CONT_READ);
			}
		} else { // write ...
			// (set the byte to write)
			as_iic_set_data_tx(base_addr, data);
			
			if(modifier & AS_IIC_MOD_MASTER_ACK){ // ... with master acknowledge.
				as_iic_set_control(base_addr, AS_IIC_CONT_WRITE | AS_IIC_ACK_MODIFIER);
			} else { // ... without master acknowledge.
				as_iic_set_control(base_addr, AS_IIC_CONT_WRITE);
			}
		}
	
		// wait for the hardware to send/receive the next byte. 
		// If it takes too long, reset and return an error.
		if(as_iic_busy_wait_for_wait(base_addr, AS_IIC_TIMEOUT_BASE * AS_IIC_LONG_TIMEOUT) == AS_FALSE){
			as_iic_reset_hw_state(base_addr); 
			return AS_IIC_ERR_HW_TO_SENDADR;
		}
		// check if the slave acknowledged the address. 
		// If not, stop the transaction and return an error.
		if(as_iic_ack_received(base_addr) == AS_FALSE 
				&& !(modifier & (AS_IIC_MOD_MASTER_ACK | AS_IIC_MOD_IGNORE_ACKNOWLEDGE))){
			as_iic_set_control(base_addr, AS_IIC_STOP_TRANS); 
			return AS_IIC_ERR_ADR_NACK;
		}
	}
	// everything seems to have worked. Great!
	return AS_IIC_OK;
}

uint8_t as_iic_stop_read_transaction(uint32_t* base_addr, uint8_t* read_data){

	// get the received data byte
	*read_data = as_iic_get_rx_byte(base_addr);

	// stop the transaction.
	as_iic_set_control(base_addr, AS_IIC_STOP_TRANS);
	
	// wait for the hardware to enter the "ready" state again
	if(as_iic_busy_wait_for_hwready(base_addr, AS_IIC_TIMEOUT_BASE * AS_IIC_SHORT_TIMEOUT) == AS_FALSE){
		as_iic_reset_hw_state(base_addr); 
		return AS_IIC_ERR_HW_TO_GENERAL;
	}

	// wait for a bit. When stringing transaction together 
  // the slave needs some time between transactions
	as_sleep(50000);
	
	return AS_IIC_OK;
}

uint8_t as_iic_stop_write_transaction(uint32_t* base_addr){
	
	// stop the transaction.
	as_iic_set_control(base_addr, AS_IIC_STOP_TRANS);
	
	// wait for the hardware to enter the "ready" state again
	if(as_iic_busy_wait_for_hwready(base_addr, AS_IIC_TIMEOUT_BASE * AS_IIC_SHORT_TIMEOUT) == AS_FALSE){
		as_iic_reset_hw_state(base_addr); 
		return AS_IIC_ERR_HW_TO_GENERAL;
	}
	
	// check if the slave acknowledged the data. If not, return an error.
	if(as_iic_ack_received(base_addr) == AS_FALSE){
		return AS_IIC_ERR_DATA_NACK;
	}
	
	// wait for a bit. When stringing transaction together 
  // the slave needs some time between transactions
	as_sleep(50000);

	return AS_IIC_OK;
}

uint8_t as_iic_write_transaction(uint32_t* base_addr, uint8_t* byte, uint8_t modifier){
	
	// check whether the previous transaction was read or write.
	AS_BOOL prev_rw = as_iic_is_readwrite(base_addr);

	// copy the next byte into the tx data register.
	as_iic_set_data_tx(base_addr, byte);
	
	if(!(modifier & AS_IIC_MOD_IGNORE_ACKNOWLEDGE) && !prev_rw){
		// check if the slave acknowledged the last byte. 
		// If not, stop the transaction and return an error.
		if(as_iic_ack_received(base_addr) == AS_FALSE){
			as_iic_set_control(base_addr, AS_IIC_STOP_TRANS); 
			return AS_IIC_ERR_DATA_NACK;
		}
	}
	// start the next transaction ... 
	if(modifier & AS_IIC_MOD_MASTER_ACK){ // ... with master acknowledge.
		as_iic_set_control(base_addr, AS_IIC_CONT_WRITE | AS_IIC_ACK_MODIFIER);
	} else { // ... without master acknowledge.
		as_iic_set_control(base_addr, AS_IIC_CONT_WRITE);
	}
	
	// wait for the hardware to send the byte. If it takes too long, reset and return an error.
	if(as_iic_busy_wait_for_wait(base_addr, AS_IIC_TIMEOUT_BASE * AS_IIC_LONG_TIMEOUT) == AS_FALSE){
		as_iic_reset_hw_state(base_addr); 
		return AS_IIC_ERR_HW_TO_GENERAL;
	}
	return AS_IIC_OK;
}

uint8_t as_iic_read_transaction(uint32_t* base_addr, uint8_t* read_data, uint8_t modifier){

	// check whether the previous transaction was read or write.
	AS_BOOL prev_rw = as_iic_is_readwrite(base_addr);

	// read the byte from the rx data register.
	*read_data = as_iic_get_rx_byte(base_addr);
	
	// if the previous transaction was a write transaction and acknowledges are not ignored ...
	if(!(modifier & AS_IIC_MOD_IGNORE_ACKNOWLEDGE) && !prev_rw){ 
		// ... check if the slave acknowledged the last byte. 
		// If not, stop the transaction and return an error.
		if(as_iic_ack_received(base_addr) == AS_FALSE){
			as_iic_set_control(base_addr, AS_IIC_STOP_TRANS); 
			return AS_IIC_ERR_DATA_NACK;
		}
	}
	
	// Continue with the read transaction
	as_iic_set_control(base_addr, AS_IIC_CONT_READ);
	
	// wait for the hardware to receive the byte. If it takes too long, reset and return an error.
	if(as_iic_busy_wait_for_wait(base_addr, AS_IIC_TIMEOUT_BASE * AS_IIC_LONG_TIMEOUT) == AS_FALSE){
		as_iic_reset_hw_state(base_addr); 
		return AS_IIC_ERR_HW_TO_GENERAL;
	}
	return AS_IIC_OK;
}

/********** Complete transactions **********/

/***** Simple one-byte transactions *****/ 

uint8_t as_iic_get_byte(uint32_t* base_addr, uint8_t slave_addr, uint8_t* read_data){
	return as_iic_get_byte_mod(base_addr, slave_addr, read_data, AS_IIC_MOD_NONE);
}

uint8_t as_iic_write_byte(uint32_t* base_addr, uint8_t slave_addr, uint8_t* byte){
	return as_iic_write_byte_mod(base_addr, slave_addr, byte, AS_IIC_MOD_NONE);
}

uint8_t as_iic_get_byte_mod(uint32_t* base_addr, uint8_t slave_addr, uint8_t* read_data, uint8_t modifier){
	uint8_t report;
	// start a read transaction (send the address) and let the slave send the byte.
	report = as_iic_start_transaction(base_addr, &slave_addr, 0, AS_IIC_READ, modifier);
	if(report != AS_IIC_OK) return report;
	// finish the read transaction and receive the single byte.
	return as_iic_stop_read_transaction(base_addr, read_data);
}

uint8_t as_iic_write_byte_mod(uint32_t* base_addr, uint8_t slave_addr, uint8_t* byte, uint8_t modifier){
	uint8_t report;
	// start a write transaction (send the address) and write the byte.
	report = as_iic_start_transaction(base_addr, &slave_addr, byte, AS_IIC_WRITE, modifier);
	if(report != AS_IIC_OK) return report;
	// finish the transaction.
	return as_iic_stop_write_transaction(base_addr);
}

/***** Simple multi-byte transactions *****/

uint8_t as_iic_get_bytes(uint32_t* base_addr, uint8_t slave_addr, 
													uint16_t byte_count, uint8_t* read_data){
	uint8_t report = 0;
	uint16_t count = 0;
	byte_count--;
	// start a read transaction (send the address).
	report = as_iic_start_transaction(base_addr, &slave_addr, 0, AS_IIC_READ, AS_IIC_MOD_NONE);
	if(report != AS_IIC_OK) return report;
	// for every data byte:
	for(;count < byte_count; count++){
		// let the slave write the data byte to the bus.
		report = as_iic_read_transaction(base_addr, &(read_data[count]), AS_IIC_MOD_NONE);
		if(report != AS_IIC_OK) return report;
	}
	// finish the transaction and receive the last byte.
	return as_iic_stop_read_transaction(base_addr, &(read_data[byte_count]));
}

uint8_t as_iic_write_bytes(uint32_t* base_addr, uint8_t slave_addr, 
														uint16_t byte_count, uint8_t* bytes){
	uint8_t report = 0;
	uint16_t count = 1;
	// start a write transaction (send the address) and send the first data byte.
	report = as_iic_start_transaction(base_addr, &slave_addr, &(bytes[0]),
																			AS_IIC_WRITE, AS_IIC_MOD_NONE);
	if(report != AS_IIC_OK) return report;
	
	// for every data byte:
	for(;count < byte_count; count++){
		// write the data byte to the bus.
		report = as_iic_write_transaction(base_addr, &(bytes[count]), AS_IIC_MOD_NONE);
		if(report != AS_IIC_OK) return report;
	}
	// finish the transaction.
	return as_iic_stop_write_transaction(base_addr);
}

/***** Register transactions for a single register *****/

uint8_t as_iic_read_reg(uint32_t* base_addr, uint8_t slave_addr, 
													uint8_t* reg, uint8_t* read_data){
	uint8_t report = 0;
	// write the register address to the slave.
	report = as_iic_write_byte(base_addr, slave_addr, reg);
	if(report != AS_IIC_OK) return report;
	// wait a bit, so the slave has enough time to recognize the next transaction.
	as_sleep(50000);
	// have the slave send the byte of the register address.
	return as_iic_get_byte(base_addr, slave_addr, read_data);
}

uint8_t as_iic_write_reg(uint32_t* base_addr, uint8_t slave_addr, 
													uint8_t* reg, uint8_t* data){
	uint8_t reg_and_data[2] = {*reg, *data};
	// wrapper for the "write_bytes" function. 
	// Write two bytes, register address and register content.
	return as_iic_write_bytes(base_addr, slave_addr, 2, &(reg_and_data[0]));
}

/***** Register transactions for multiple registers *****/

uint8_t as_iic_read_regs(uint32_t* base_addr, uint8_t slave_addr, 
													uint8_t* reg, uint16_t byte_count, uint8_t* read_data){
	uint8_t report = 0;
	uint16_t count = 0;
	byte_count--;
	// send the starting register to the slave.
	as_iic_write_byte(base_addr, slave_addr, reg);
	// wait a bit, so the slave has enough time to recognize the next transaction.
	as_sleep(50000);
	// start a read transaction (send the address).
	report = as_iic_start_transaction(base_addr, &slave_addr, 0, AS_IIC_READ, AS_IIC_MOD_NONE);
	if(report != AS_IIC_OK) return report;
	// for every data byte:
	for(;count < byte_count; count++){
		// let the slave write the data byte to the bus.
		report = as_iic_read_transaction(base_addr, &(read_data[count]), AS_IIC_MOD_NONE);
		if(report != AS_IIC_OK) return report;
	}
	// finish the transaction and receive the last byte.
	return as_iic_stop_read_transaction(base_addr, &(read_data[byte_count]));
}

/***** Special IIC transactions *****/

uint8_t as_iic_set_regpointer(uint32_t* base_addr, uint8_t slave_addr, uint8_t* pointer){
	uint8_t report = 0;
	report = as_iic_start_transaction(base_addr, &slave_addr, pointer, 
																		AS_IIC_WRITE, AS_IIC_MOD_MASTER_ACK);
	if(report != AS_IIC_OK) return report;
	return as_iic_stop_write_transaction(base_addr);
}
