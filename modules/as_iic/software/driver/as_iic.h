/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  Copyright (C) Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Module:         as_iic
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Author:         Philip Manke
--
-- Modified:       2017-08-30 Philip Manke
--                 2019-07-22 Philip Manke; Updated IO Register offsets (new HW)
--
-- Description:    Driver (header file) for the as_iic module.
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
 * @file  as_iic.h
 * @brief Driver (header file) for the as_iic module.
 *
 * \defgroup as_iic Module as_iic
 * 
 */


#ifndef AS_IIC_H
#define AS_IIC_H

#include "as_support.h"

/******************* Misc ************************/

//! Uncomment this to enable the function as_iic_err_to_str()
//#define AS_IIC_DEBUG 1
//! The driver will wait ten times longer for the hardware before 
//! returning with an error.
//#define AS_IIC_USE_VERY_LONG_TIMEOUT 1

//! The driver needs to know the FPGAs system clock frequency to set the
//! SCL-DIV register correctly. Should be defined somewhere system-wide
//! in the future
#define AS_SYSTEM_CLOCK_HZ 100000000


/******************* I/O Registers ************************/

#define AS_IIC_DATA_RX_OFFSET 0
#define AS_IIC_STATUSCONTROL_OFFSET 0
#define AS_IIC_DATA_TX_OFFSET 1
#define AS_IIC_SCL_DIV_OFFSET 1

/******************* Bits *********************************/

// Control Bits
//! Start a transaction.
#define AS_IIC_TSTART (1 << 0)
//! End the current transaction.
#define AS_IIC_TEND (1 << 1)

//! Read/Write bit. Controls what the next transaction will be.
//! '0' := Continue with a write transaction;
//! '1' := Continue with a read transaction.
#define AS_IIC_RW (1 << 2)
//! Immediatly reset the hardware to the initial state 
//! (should be in "ready" state after a single clock cycle)
#define AS_IIC_RESET (1 << 3)
//! Signal the hardware that the data registers are in a valid state.
//! Needed when the "waiting_sw" (AS_IIC_WAITING) bit is '1'.
#define AS_IIC_DATA_READY (1 << 4)
//! Bit to modify the acknowledge behaviour. 
//! '0' := Regular acknowledge behaviour.
//! '1' := Causes the master to send an acknowledge after a write 
//! transaction.
#define AS_IIC_ACK_MODIFIER (1 << 5)

// Status Bits
//! The hardware is in the "ready" state.
#define AS_IIC_READY (1 << 0)
//! The data registers are in a valid state. IO is permitted.
#define AS_IIC_IO_READY (1 << 1)
//! The hardware is currently writing data onto the iic bus.
#define AS_IIC_BUS_ACTIVE (1 << 2)
//! The hardware has received an acknowledgement from the slave.
#define AS_IIC_ACK_RECEIVED (1 << 3)
//! The slave has slowed the current transaction at some point.
#define AS_IIC_STALLED (1 << 4)
//! The hardware is currently waiting for the software to confirm that 
//! the data registers are in a valid state to continue the current 
//! transaction.
#define AS_IIC_WAITING (1 << 5)

// Combined Bits
//! Control bit combination. Continue with a write transaction.
#define AS_IIC_CONT_WRITE AS_IIC_TSTART | AS_IIC_DATA_READY
//! Control bit combination. Continue with a read transaction.
#define AS_IIC_CONT_READ  AS_IIC_TSTART | AS_IIC_RW | AS_IIC_DATA_READY
//! Control bit combination. Stop the current transaction.
#define AS_IIC_STOP_TRANS AS_IIC_TEND | AS_IIC_DATA_READY

// Modifier Bits
//! No modifiers. Default IIC behaviour.
#define AS_IIC_MOD_NONE 0
//! Bit 0 of the "modifier" parameter. Causes the master to send an 
//! acknowledge after sending the slave address.
#define AS_IIC_MOD_MASTER_ACK (1 << 0)
//! Bit 1 of the "modifier" parameter. Causes the software to skip
//! checks for the slave acknowledge. Needed when the master sent an 
//! acknowledge. 
#define AS_IIC_MOD_IGNORE_ACKNOWLEDGE (1 << 1)
//! Bit 2 of the "modifier" parameter. Only used by 
//! "as_iic_start_transaction". The function will only send the address.
#define AS_IIC_MOD_ONLY_ADDRESS (1 << 2)

// Read and write defines

//! Used in "as_iic_start_transaction". Starts a read transaction.
#define AS_IIC_READ 1
//! Used in "as_iic_start_transaction". Starts a write transaction.
#define AS_IIC_WRITE 0

/******************* Masks ********************************/

#define AS_IIC_TX_DATA_MASK 0x00FFFFFF
#define AS_IIC_SCL_DIV_MASK 0xFF000000
#define AS_IIC_CTRL_MASK 0x3F
#define AS_IIC_RX_DATA_MASK 0x0000FF00
#define AS_IIC_STATUS_MASK 0x0000003F
#define AS_IIC_CTRL_READ_MASK 0x003F0000

/******************* Error Codes **************************/

//! No error
#define AS_IIC_OK 0x0				
//! The ready bit is not set
#define AS_IIC_ERR_HW_NOT_READY 0x1	
//! The hardware took too long to set the io_ready bit
#define AS_IIC_ERR_HW_TO_IOREADY 0x2	
//! The hardware took too long to set the waiting_sw bit 
//! while writing the address
#define AS_IIC_ERR_HW_TO_SENDADR 0x3	
//! The hardware took too long to set the waiting_sw bit 
//! while writing a data byte
#define AS_IIC_ERR_HW_TO_WRITE_DATA 0x4
//! The hardware took too long to set the waiting_sw bit 
//! while receiving a data byte
#define AS_IIC_ERR_HW_TO_RECV_DATA 0x5
//! The hardware took too long to set the waiting_sw bit 
//! during a transaction
#define AS_IIC_ERR_HW_TO_GENERAL 0xA
//! The hardware did not receive an acknowledgement after 
//! sending a slave address
#define AS_IIC_ERR_ADR_NACK 0x6
//! The hardware did not receive an acknowledgement after 
//! sending a data byte
#define AS_IIC_ERR_DATA_NACK 0x7
//! The hardware did not receive an acknowledgement after 
//! sending a register address
#define AS_IIC_ERR_REG_NACK 0x8
//! The hardware did not receive an acknowledgement after a transmission
#define AS_IIC_ERR_NACK 0xB
//! The hardware reports that IO is not permitted, although it should be
#define AS_IIC_ERR_IO_NOT_READY 0x9
//! The entered frequency is not supported by as_iic.
#define AS_IIC_ERR_FREQ_INVALID 0xC
//! The bus frequency has not been set yet!
#define AS_ERR_NOT_INITIALIZED 0xD

/******************* Timeouts for busy waiting functions **************/

#define AS_IIC_TIMEOUT_BASE 1000 // timeout base 1 us

#ifdef AS_IIC_USE_VERY_LONG_TIMEOUT
	#define AS_IIC_LONG_TIMEOUT 1000 // very long timeout 1 ms
#else
	#define AS_IIC_LONG_TIMEOUT 100 // long timeout 100 us
#endif

#ifdef AS_IIC_USE_VERY_LONG_TIMEOUT
	#define AS_IIC_SHORT_TIMEOUT 100 // longer short timeout 100 us
#else
	#define AS_IIC_SHORT_TIMEOUT 10 // short timeout 10 us
#endif

/******************* Driver state variables ***************************/

//! This flag is set when the function as_iic_init is called.
//! It is reset when the function as_iic_reset is called.
static AS_BOOL as_iic_initialized_flag;

/******************* Debug related ************************/
 
#ifdef AS_IIC_DEBUG
	const char* as_iic_err_to_str(uint8_t error_number);
#endif

/******************* Driver functions *********************/

/** \addtogroup as_iic
 *  @{
 */

// raw register access ~~~~~~~~~~~~~~~~

/**
 * Read and return the contents of the "status and control" register,
 * without alterations.
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @return 							Contents of the "status and control"
 * 											register.
 */
uint32_t as_iic_get_status(uint32_t* base_addr);

/**
 * Read and return the contents of the "data receive" register,
 * without alterations.
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @return 							Contents of the "data receive" register.
 */
uint32_t as_iic_get_data_rx(uint32_t* base_addr);

/**
 * Read and return the contents of the "data transmit and scl div" 
 * register, without alterations.
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @return 							Contents of the "data transmit and scl 
 * 											div" register.
 */
uint32_t as_iic_get_data_tx(uint32_t* base_addr);

// write access to registers ~~~~~~~~~~~~~~~~

/**
 * Overwrite the contents of (only) the control part of the "status and 
 * control" register.
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @param control				The byte combination to set the control
 * 											register to.
 */
void as_iic_set_control(uint32_t* base_addr, uint8_t control);


/**
 * Overwrite the contents of the entire data register.
 * This includes the bus frequency and the data tx part. 
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @param data 					The data to write into the register.
 */
void as_iic_set_data_register(uint32_t* base_addr, uint32_t data);

/**
 * Overwrite the contents of (only) the "data transmit" part of the 
 * "data transmit and scl div" register.
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @param byte					Pointer to the byte to set the "data
 * 											transmit" byte to.
 */
void as_iic_set_data_tx(uint32_t* base_addr, uint8_t* byte);

/**
 * Overwrite the contents of (only) the "scl div" part of the "data 
 * transmit and scl div" register.
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @param div						Value to set "scl div" part of the 
 * 											register to (max 24 bit). 
 */
void as_iic_set_scl_div(uint32_t* base_addr, uint32_t div);

// read access to registers ~~~~~~~~~~~~~~~~

/**
 * Read the contents of the "data receive" register and return only the
 * read byte.
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @return							The "read byte" part of the "data 
 * 											receive" register.
 */
uint8_t as_iic_get_rx_byte(uint32_t* base_addr);

/**
 * Read the contents of the "status and control" register and return only
 * the status bits (6 bits).
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @return							The current status bits as a byte.
 */
uint8_t as_iic_get_status_reg(uint32_t* base_addr);

/**
 * Read the contents of the "status and control" register and return only
 * the control bits (5 bits).
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @return							The current control bits as a byte.
 */
uint8_t as_iic_get_control_reg(uint32_t* base_addr);

// check status bits ~~~~~~~~~~~~~~~~

/**
 * Read the contents of the "status and control" register and assert
 * whether the "iic_ready" bit is set or not.
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @return							If the "iic_ready" bit is set as an
 * 											AS_BOOL. 
 */
AS_BOOL as_iic_is_ready(uint32_t* base_addr);

/**
 * Read the contents of the "status and control" register and assert
 * whether the "io_ready" bit is set or not.
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @return							If the "io_ready" bit is set as an
 * 											AS_BOOL. 
 */
AS_BOOL as_iic_is_io_ready(uint32_t* base_addr);

/**
 * Read the contents of the "status and control" register and assert
 * whether the "bus_active" bit is set or not.
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @return							If the "bus_active" bit is set as an
 * 											AS_BOOL. 
 */
AS_BOOL as_iic_is_active(uint32_t* base_addr);

/**
 * Read the contents of the "status and control" register and assert
 * whether the "ack_recieved" bit is set or not.
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @return							If the "ack_recieved" bit is set as an
 * 											AS_BOOL. 
 */
AS_BOOL as_iic_ack_received(uint32_t* base_addr);

/**
 * Read the contents of the "status and control" register and assert
 * whether the "stalled" bit is set or not.
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @return							If the "stalled" bit is set as an
 * 											AS_BOOL. 
 */
AS_BOOL as_iic_is_stalled(uint32_t* base_addr);

/**
 * Read the contents of the "status and control" register and assert
 * whether the "waiting_sw" bit is set or not.
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @return							If the "waiting_sw" bit is set as an
 * 											AS_BOOL. 
 */
AS_BOOL as_iic_is_waiting(uint32_t* base_addr);

/**
 * Read the contents of the "status and control" register and assert
 * whether the "readwrite" bit is set or not.
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @return							If the "readwrite" bit is set as an
 * 											AS_BOOL. 
 */
AS_BOOL as_iic_is_readwrite(uint32_t* base_addr);

/**
 * Assert whether the "initialized" flag is set or not.
 * 
 * @return							If the "readwrite" bit is set as an
 * 											AS_BOOL. 
 */
AS_BOOL as_iic_is_initialized(void);


// set control bits ~~~~~~~~~~~~~~~~~~~~~

/**
 * Read the contents of the "status and control" register and set the
 * "transmit_start" bit to '1' without affecting the other bits.
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 */
void as_iic_set_transmit_start(uint32_t* base_addr);

/**
 * Read the contents of the "status and control" register and change the
 * "read_write" bit without affecting the other bits.
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @param value					Whether to set the bit to '0' (write) or
 * 											'1' (read).
 */
void as_iic_set_readwrite(uint32_t* base_addr, uint8_t value);

/**
 * Read the contents of the "status and control" register and set the
 * "transmit_stop" bit to '1' without affecting the other bits.
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 */
void as_iic_set_transmit_stop(uint32_t* base_addr);

/**
 * Sets the "initialized" flag to value.
 * 
 * @param value					Whether to set the bit to '0' (write) or
 * 											'1' (read).
 */
void as_iic_set_initialized(uint8_t value);


/**
 * Set the "reset" bit of the "status and control" register to '1'.
 * This only resets the internal hardware state machines.
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 */
void as_iic_reset_hw_state(uint32_t* base_addr);

/**
 * Complete reset for the module as_iic.
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 */
void as_iic_reset(uint32_t* base_addr);

/**
 * Read the contents of the "status and control" register and set 
 * "data_ready" bit to '1' without affecting the other bits.
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 */
void as_iic_set_data_ready(uint32_t* base_addr);

// busy waiting ftw ~~~~~~~~~~~~~~~~

/**
 * Continuously check the "iic_ready" bit until it is set or 
 * "timeout_ns" has passed. 
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @param timeout_ns		How long in ns before this function will
 * 											stop waiting.
 * @return							"AS_FALSE" if the timeout is reached, 
 * 											otherwise "AS_TRUE".
 */
AS_BOOL as_iic_busy_wait_for_hwready(uint32_t* base_addr, 
																			uint32_t timeout_ns);

/**
 * Continuously check the "waiting_sw" bit until it is set or 
 * "timeout_ns" has passed. 
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @param timeout_ns		How long in ns before this function will
 * 											stop waiting.
 * @return							"AS_FALSE" if the timeout is reached, 
 * 											otherwise "AS_TRUE".
 */
AS_BOOL as_iic_busy_wait_for_wait(uint32_t* base_addr, 
																		uint32_t timeout_ns);

/**
 * Continuously check the "io_ready" bit until it is set or 
 * "timeout_ns" has passed. 
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @param timeout_ns		How long in ns before this function will
 * 											stop waiting.
 * @return							"AS_FALSE" if the timeout is reached, 
 * 											otherwise "AS_TRUE".
 */
AS_BOOL as_iic_busy_wait_for_ioready(uint32_t* base_addr, 
																			uint32_t timeout_ns);

// helper functions ~~~~~~~~~~~~~~~~

/**
 * Start a transaction and optionally send or receive the first byte.
 * Send the Start Bit and send the slave address.
 * Then check or send an acknowledge and send or receive the first byte.
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @param slave_addr		Pointer to the slave address byte.
 * @param data					Pointer to the data byte to send.
 * @param readwrite			Whether to continue with a read (1) or 
 * 											write (0) transaction after the address.
 * @param modifier			A byte to modify the transaction. Check 
 * 											the modifier defines for an explanation.
 * @return 							Byte containing a status code, 0 if OK.
 */
uint8_t as_iic_start_transaction(uint32_t* base_addr, 
																	uint8_t* slave_addr, 
																	uint8_t* data, uint8_t readwrite, 
																	uint8_t modifier);

/**
 * Stop a current write transaction, check the acknowledge 
 * and send the stop bit.
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @return 							Byte containing a status code, 0 if OK.
 */
uint8_t as_iic_stop_write_transaction(uint32_t* base_addr);

/**
 * Stop a current read transaction, copy the received byte to 
 * "read_data" and send the stop bit.
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @param read_data			Pointer to a byte variable to copy the 
 * 											byte the slave send to.
 * @return 							Byte containing a status code, 0 if OK.
 */
uint8_t as_iic_stop_read_transaction(uint32_t* base_addr, 
																			uint8_t* read_data);

/**
 * Write a byte to the iic bus. Check the slave acknowledge, copy "byte"
 * to the hardware register and let the hardware continue to write this 
 * byte to the iic bus.
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @param byte					Pointer to a byte to write send.	
 * @param modifier			A byte to modify the transaction. Check 
 * 											the modifier defines for an explanation.
 * @return 							Byte containing a status code, 0 if OK.
 */
uint8_t as_iic_write_transaction(uint32_t* base_addr, uint8_t* byte, 
																	uint8_t modifier);

/**
 * Read another byte from the slave. Copy the last received byte to 
 * "read_data" and let the slave continue writing.
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @param read_data			Pointer to a byte variable to copy the 
 * 											byte the slave send to.
 * @param modifier			A byte to modify the transaction. Check 
 * 											the modifier defines for an explanation.
 * @return 							Byte containing a status code, 0 if OK.
 */
uint8_t as_iic_read_transaction(uint32_t* base_addr, uint8_t* read_data, 
																	uint8_t modifier);

// high level functions ~~~~~~~~~~~~~~~~~~~~~

/**
 * Set the iic bus serial clock frequency.
 * The actual bus frequency is an approximation of the given value,
 * usually a few percent lower than given.
 * The hardware immediatly reacts to this change.
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @param iic_bus_freq	The desired scl frequency in Hz.
 */
uint8_t as_iic_init(uint32_t* base_addr, uint32_t iic_bus_freq);

/**
 * Execute a read transaction for a single byte. Writes the slave 
 * (read) address and receives the byte the slave sends. 
 * Automatically converts the slave write address to the read address, 
 * if the write address is given. 
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @param slave_addr		The address of the slave on the bus to talk to.
 * @param read_data			Pointer to a byte variable to copy the 
 * 											byte the slave send to.
 * @return 							Byte containing a status code, 0 if OK.
 */
uint8_t as_iic_get_byte(uint32_t* base_addr, uint8_t slave_addr, 
													uint8_t* read_data);

/**
 * Execute a read transaction for a single byte. Writes the slave 
 * (read) address and receives the byte the slave sends. 
 * Automatically converts the slave write address to the read address, 
 * if the write address is given. 
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @param slave_addr		The address of the slave on the bus to talk to.
 * @param read_data			Pointer to a byte variable to copy the 
 * 											byte the slave send to.
 * @param modifier			Modifier byte. Allows for advanced operations.
 * @return 							Byte containing a status code, 0 if OK.
 */
uint8_t as_iic_get_byte_mod(uint32_t* base_addr, uint8_t slave_addr, 
															uint8_t* read_data, uint8_t modifier);



/**
 * Execute a write transaction for a single byte. Writes the slave 
 * address and the given data byte to the slave.
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @param slave_addr		The address of the slave on the bus to talk to.
 * @param byte					Pointer to the byte to write to the bus.
 * @return 							Byte containing a status code, 0 if OK.
 */
uint8_t as_iic_write_byte(uint32_t* base_addr, uint8_t slave_addr, 
														uint8_t* byte);

/**
 * Execute a write transaction for a single byte. Writes the slave 
 * address and the given data byte to the slave.
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @param slave_addr		The address of the slave on the bus to talk to.
 * @param byte					Pointer to the byte to write to the bus.
 * @param modifier			Modifier byte. Allows for advanced operations.
 * @return 							Byte containing a status code, 0 if OK.
 */													
uint8_t as_iic_write_byte_mod(uint32_t* base_addr, uint8_t slave_addr, 
																uint8_t* byte, uint8_t modifier);

/**
 * Execute a read transaction for multiple bytes. Writes the slave 
 * (read) address and let's the slave send the desired data bytes.
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @param slave_addr		The address of the slave on the bus to talk to.
 * @param byte_count		Number of bytes to receive (16bit uint).
 * @param read_data			Pointer to a byte array the received 
 * 											bytes are stored to.
 * @return 							Byte containing a status code, 0 if OK.
 */
uint8_t as_iic_get_bytes(uint32_t* base_addr, uint8_t slave_addr, 
													uint16_t byte_count, uint8_t* read_data);

/**
 * Execute a read transaction for multiple bytes. Writes the slave 
 * (read) address, the starting register and let's the slave send the 
 * desired data bytes.
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @param slave_addr		The address of the slave on the bus to talk to.
 * @param reg						The address of the register from which 
 * 											the slave should start reading. 
 * @param byte_count		Number of bytes to receive (16bit uint).
 * @param read_data			Pointer to a byte array the received 
 * 											bytes are stored to.
 * @return 							Byte containing a status code, 0 if OK.
 */
uint8_t as_iic_read_regs(uint32_t* base_addr, uint8_t slave_addr, 
													uint8_t* reg, uint16_t byte_count, 
													uint8_t* read_data);

/**
 * Execute a write transaction with multiple bytes. Writes the slave 
 * address and the given data bytes to the slave.
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @param slave_addr		The address of the slave on the bus to talk to.
 * @param byte_count		Number of bytes to send (16bit uint).
 * @param bytes					Pointer to the byte array conaining the 
 * 											bytes to write to the bus.
 * @return 							Byte containing a status code, 0 if OK.
 */
uint8_t as_iic_write_bytes(uint32_t* base_addr, uint8_t slave_addr, 
														uint16_t byte_count, uint8_t* bytes);

/**
 * Execute a write and a read transaction to fetch the content of a 
 * single register.
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @param slave_addr		The address of the slave on the bus to talk to.
 * @param reg						The register address the slave should 
 * 											return the contents of. 
 * @param read_data			Pointer to a byte array the received 
 * 											bytes are stored to.
 * @return 							Byte containing a status code, 0 if OK.
 */
uint8_t as_iic_read_reg(uint32_t* base_addr, uint8_t slave_addr, 
													uint8_t* reg, uint8_t* read_data);

/**
 * Execute a write transaction for two bytes, the register address and 
 * it's content.
 * This function simply calls the function "as_iic_write_bytes".
 * 
 * @param base_addr    	Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @param slave_addr		The address of the slave on the bus to talk to.
 * @param reg       		Pointer to the register address.
 * @param data					Pointer to the byte that will be written
 * 											into to the register.
 * @return 							Byte containing a status code, 0 if OK.
 */
uint8_t as_iic_write_reg(uint32_t* base_addr, uint8_t slave_addr, 
													uint8_t* reg, uint8_t* data);


/**
 * Execute a special write transaction for one byte, sending an 
 * acknowledgement after sending the slave address.
 * 
 * @param base_addr     Address of the corresponding as_iic 
 * 											hardware module (see also as_hardware.h)
 * @param slave_addr		The address of the slave on the bus to talk to.
 * @param pointer				Pointer to the byte to send to the 
 * 											slave.
 * @return 							Byte containing a status code, 0 if OK.
 */
uint8_t as_iic_set_regpointer(uint32_t* base_addr, uint8_t slave_addr, 
																uint8_t* pointer);

/** @}*/

#endif /** AS_IIC_H */
