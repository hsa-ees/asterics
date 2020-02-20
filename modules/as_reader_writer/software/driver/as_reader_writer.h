/***********************************************************************
 *  This file is part of the ASTERICS Framework.
 *  Copyright (C) Hochschule Augsburg, University of Applied Sciences
 *  All rights reserved
 ***********************************************************************
 * File:           as_reader_writer.h
 *
 * Company:        University of Applied Sciences, Augsburg, Germany
 *                 Efficient Embedded Systems Group
 *                 http://ees.hs-augsburg.de
 *
 * Author:         Alexander Zoellner
 *
 * Description:    Implements software drivers for using the
 *                 as_reader_writer module.
 *
 * *********************************************************************
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program.  If not, see <http://www.gnu.org/licenses/>.
 **********************************************************************/

/**
 * @file  as_reader_writer.h
 * @brief Driver (header file) for as_reader_writer module.
 *
 * \addtogroup asterics_mod
 * @{
 *   \defgroup as_reader_writer Reader/Writer
 * @}
 *
 * Operation of the 'as_reader_writer' hardware module
 * -----------------------------------------------
 *
 * Purpose of the 'as_reader_writer' module is efficiently transfer data
 * streams ('as_stream') to main memory using bus master access and
 * burst transfers. Data chunks are referred to as "sections" and are
 * defined by their base address and size.
 *
 * To support the efficient transfer of rectangular sub-images or memory
 * layouts with padding at the end of lines, multiple repeated sections
 * with a constant offset (= difference between the start addresses
 * of two consecutive sections) may be defined for one base address.
 * This feature is only available if the hardware has been synthesized
 * with the generic ENABLE_MULTI_SECTIONS set to 'true'.
 *
 * To support seamless writing to multiple buffers without frequent
 * software polling (for example, when using double buffering or FIFOs),
 * the base address can be rewritten and the 'go' flag be set already
 * during a running transfer. The previous base address is latched
 * internally, and the module hardware automatically continues with the
 * next setup as soon as the previous section set has been completely
 * written.
 *
 * The progress of the writing process can be determined by querying the
 * current write address.
 */


#ifndef AS_READER_WRITER_H
#define AS_READER_WRITER_H

#include "as_support.h"



/******************* Default values ************************/


/* Set section size to "0" to remind the user to set the correct size */
#define AS_READER_WRITER_DEFAULT_SECTION_SIZE                   0
/* (See hardware bus specification for supported maximum) */
#define AS_READER_WRITER_DEFAULT_MAX_BURST_LENGTH               256
/* (i.e. use only one section for a single frame) */
#define AS_READER_WRITER_DEFAULT_SECTION_COUNT                  1
/* (No offset needed since only one section is used) */
#define AS_READER_WRITER_DEFAULT_SECTION_OFFSET                 0



/******************* I/O Registers ************************/


/* Internal register definitions */
#define AS_READER_WRITER_STATE_CONTROL_REG_OFFSET               0
#define AS_READER_WRITER_REG_SECTION_ADDR_OFFSET                1
#define AS_READER_WRITER_REG_SECTION_OFFSET_OFFSET              2
#define AS_READER_WRITER_REG_SECTION_SIZE_OFFSET                3
#define AS_READER_WRITER_REG_SECTION_COUNT_OFFSET               4
#define AS_READER_WRITER_REG_MAX_BURST_LENGTH_OFFSET            5
#define AS_READER_WRITER_REG_CUR_HW_ADDR_OFFSET                 6
/* Memwriter only */
#define AS_WRITER_REG_LAST_DATA_UNIT_COMPLETE_ADDR_OFFSET       7
#define AS_WRITER_REG_CURRENT_UNIT_COUNT                        8


/* Status bit offsets */
#define AS_READER_WRITER_DONE_BIT_OFFSET                        0
#define AS_READER_WRITER_BUSY_BIT_OFFSET                        1
#define AS_READER_WRITER_SYNC_ERROR_BIT_OFFSET                  3
#define AS_READER_WRITER_PENDING_GO_BIT_OFFSET                  5
/* Memwriter only */
#define AS_WRITER_FLUSHABLE_DATA_BIT_OFFSET                     4
#define AS_WRITER_SET_ENABLE_BIT_OFFSET                         6


/* Control bit offsets */
#define AS_READER_WRITER_RESET_BIT_OFFSET                       16
#define AS_READER_WRITER_GO_BIT_OFFSET                          17
/* Memwriter only */
#define AS_WRITER_ENABLE_BIT_OFFSET                             18
#define AS_WRITER_DISABLE_BIT_OFFSET                            19
#define AS_WRITER_ENABLE_ON_DATA_UNIT_COMPLETE_BIT_OFFSET       20
#define AS_WRITER_SINGLE_SHOT_BIT_OFFSET                        21
#define AS_WRITER_DISABLE_ON_NO_GO_BIT_OFFSET                   22
#define AS_WRITER_FLUSH_DATA_BIT_OFFSET                         23


/* Status bit masks */
#define AS_READER_WRITER_DONE_MASK              (1<<AS_READER_WRITER_DONE_BIT_OFFSET)
#define AS_READER_WRITER_BUSY_MASK              (1<<AS_READER_WRITER_BUSY_BIT_OFFSET)
#define AS_READER_WRITER_SYNC_ERROR_MASK        (1<<AS_READER_WRITER_SYNC_ERROR_BIT_OFFSET)
#define AS_READER_WRITER_PENDING_GO_MASK        (1<<AS_READER_WRITER_PENDING_GO_BIT_OFFSET)
/* Memwriter only */
#define AS_WRITER_FLUSHABLE_DATA_MASK           (1<<AS_WRITER_FLUSHABLE_DATA_BIT_OFFSET)
#define AS_WRITER_SET_ENABLE_MASK               (1<<AS_WRITER_SET_ENABLE_BIT_OFFSET)


/* Control bit masks */
#define AS_READER_WRITER_RESET_MASK                         (1<<AS_READER_WRITER_RESET_BIT_OFFSET)
#define AS_READER_WRITER_GO_MASK                            (1<<AS_READER_WRITER_GO_BIT_OFFSET)
/* Memwriter only */
#define AS_WRITER_ENABLE_MASK                               (1<<AS_WRITER_ENABLE_BIT_OFFSET)
#define AS_WRITER_DISABLE_MASK                              (1<<AS_WRITER_DISABLE_BIT_OFFSET)
#define AS_WRITER_ENABLE_ON_DATA_UNIT_COMPLETE_MASK         (1<<AS_WRITER_ENABLE_ON_DATA_UNIT_COMPLETE_BIT_OFFSET)
#define AS_WRITER_SINGLE_SHOT_MASK                          (1<<AS_WRITER_SINGLE_SHOT_BIT_OFFSET)
#define AS_WRITER_DISABLE_ON_NO_GO_MASK                     (1<<AS_WRITER_DISABLE_ON_NO_GO_BIT_OFFSET)
#define AS_WRITER_FLUSH_DATA_MASK                           (1<<AS_WRITER_FLUSH_DATA_BIT_OFFSET)


/** \addtogroup as_reader_writer
 *  @{
 */


/******************* Driver functions **********************/


/**
 * @brief Contains all necessary variables for
 * as_reader_writer configuration.
 *
 * These variables may be assigned
 * by the user for calling as_reader_writer_init afterwards for a
 * more comfortable configuration instead of calling each function
 * individually.
 */
typedef struct as_reader_writer_config_s {
    uint32_t section_size;
    uint32_t* first_section_addr;
    uint32_t max_burst_length;
    uint32_t section_count;
    uint32_t section_offset;
}as_reader_writer_config_t;


/* Configuration functions */
/**
 * @brief Initializes the hardware module with values provided
 * by config.
 *
 * If config is a NULL pointer, default values will be set
 * for section_size, max_burst_length, section_count and section_offset.
 * The parameter first_section_addr has to be set separately by calling
 * as_reader_writer_set_section_addr.
 * After setting parameters the hardware module will be set to a
 * defined state by calling as_memreader_reset internally.
 *
 * @param base_addr             Address of the corresponding hardware
 *                              module (see also as_hardware.h)
 * @param config                Structure which contains parameters
 *                              for hardware module configuration. Set
 *                              NULL pointer if default values are to
 *                              be set.
 */
void as_reader_writer_init(uint32_t* base_addr, as_reader_writer_config_t * config);

/**
 * @brief Returns the next address on which the hardware will
 * perform a write operation.
 *
 * @param base_addr             Address of the corresponding hardware
 *                              module (see also as_hardware.h)
 *
 * @return                      Address on which hardware will perform
 *                              the next read operation
 */
uint32_t* as_reader_writer_get_cur_hw_addr(uint32_t* base_addr);

/**
 * @brief Sets the start address of the first section to the
 * given value.
 *
 * @param base_addr             Address of the corresponding hardware
 *                              module (see also as_hardware.h)
 * @param value                 Specifies the start address of the first
 *                              section
 */
void as_reader_writer_set_section_addr(uint32_t* base_addr, uint32_t* value);

/**
 * @brief Sets the offset in bytes between the start addresses of
 * two subsequent sections.
 *
 * @note This value will take no effect
 * if the hardware generic "ENABLE_MULTI_SECTIONS" is set to "false".
 *
 * @param base_addr             Address of the corresponding hardware
 *                              module (see also as_hardware.h).
 * @param value                 Specifies the offset between two subsequent
 *                              sections in bytes.
 */
void as_reader_writer_set_section_offset(uint32_t* base_addr, uint32_t value);

/**
 * @brief Sets the size of a single section in bytes.
 *
 * @param base_addr             Address of the corresponding hardware
 *                              module (see also as_hardware.h).
 * @param value                 Specifies the number of bytes of a single
 *                              section. Only integer multiples of
 *                              BYTES_PER_WORD are valid.
 */
void as_reader_writer_set_section_size(uint32_t* base_addr, uint32_t value);

/**
 * @brief Sets the number of sections.
 *
 * @param base_addr             Address of the corresponding hardware
 *                              module (see also as_hardware.h).
 * @param value                 Specifies the number sections whereas
 *                              only values greater 0 are valid.
 */
void as_reader_writer_set_section_count(uint32_t* base_addr, uint32_t value);

/**
 * @brief Sets the maximum possible burst length to be performed
 * by the hardware module.
 *
 * Only the configured burst length will be performed, if possible.
 * In all other cases the hardware module will fall back
 * to (slower) single beat operations.
 *
 * @param base_addr             Address of the corresponding hardware
 *                              module (see also as_hardware.h).
 * @param value                 Specifies the maximum possible burst length.
 *                              Only values ranging from BYTES_PER_WORD*2
 *                              to MAX_PLATFORM_BURST_LENGTH (generic)
 *                              are considered valid. Furthermore, values
 *                              in between have to be an integer multiple
 *                              of BYTES_PER_WORD.
 */
void as_reader_writer_set_max_burst_length(uint32_t* base_addr, uint32_t value);


/* Memwriter only */
/**
 * @brief Returns the first address after the last successfully
 * written unit.
 *
 * Addresses smaller than the returned one contain data of the unit.
 *
 * @param base_addr             Address of the corresponding hardware
 *                              module (see also as_hardware.h)
 *
 * @return                      First address after last completed section
 *
 */
uint32_t* as_writer_get_last_data_unit_complete_addr(uint32_t* base_addr);

/**
 * @brief Returns the number of received units by the reader_writer.
 *
 * @param base_addr             Address of the corresponding hardware
 *                              module (see also as_hardware.h)
 *
 * @return                      Number of received units by the reader_writer
 *
 */
 uint32_t* as_writer_get_cur_unit_count(uint32_t* base_addr);



/* Status functions */
/**
 * @brief Checks if module is ready for operation.
 *
 * This function checks the corresponding hardware status bit if the
 * hardware module is ready for operation or has finished its current
 * operation. In this case the function will return 'AS_TRUE' and
 * 'AS_FALSE' otherwise.
 *
 * @param                       Address of the corresponding hardware
 *                              module (see also as_hardware.h).
 *
 * @return                      Returns 'AS_TRUE' if hardware module is
 *                              ready for operation and 'AS_FALSE' otherwise.
 */
AS_BOOL as_reader_writer_is_done(uint32_t* base_addr);

/**
 * @brief Checks if module is busy.
 *
 * This function checks the corresponding hardware status bit if the
 * hardware module is currently performing an operation. In this
 * case the function will return 'AS_TRUE' and 'AS_FALSE' otherwise.
 *
 * @param                       Address of the corresponding hardware
 *                              module (see also as_hardware.h).
 *
 * @return                      Returns 'AS_TRUE' if hardware module is
 *                              occupied with operation and 'AS_FALSE'
 *                              otherwise.
 */
AS_BOOL as_reader_writer_is_busy(uint32_t* base_addr);


/**
 * @brief Checks if another operation is queued.
 *
 * This function checks the corresponding hardware status bit if the
 * hardware module already received an additional "go" signal during its
 * operation to initialize the next operation right after finishing the
 * current one.
 *
 * @param                       Address of the corresponding hardware
 *                              module (see also as_hardware.h).
 *
 * @return                      Returns 'AS_TRUE' if the next "go" signal
 *                              has been set already and 'AS_FALSE' otherwise.
 */
AS_BOOL as_reader_writer_is_pending_go(uint32_t* base_addr);


/* Memwriter only */
/**
 * @brief Checks if module has dropped data.
 *
 * This function checks the corresponding hardware status bit if the
 * hardware module received additional STROBE signals after STALL was
 * set.
 *
 * @param                       Address of the corresponding hardware
 *                              module (see also as_hardware.h).
 *
 * @return                      Returns 'AS_TRUE' if an error was detected
 *                              and 'AS_FALSE' otherwise.
 */
AS_BOOL as_writer_is_sync_error(uint32_t* base_addr);

/**
 * @brief Checks if there is buffered data.
 *
 * This function checks if there is currently data in the fifo buffer of
 * the reader_writer which may be flushed.
 *
 * @param                       Address of the corresponding hardware
 *                              module (see also as_hardware.h).
 *
 * @return                      Returns 'AS_TRUE' if there is flushable
 *                              data and 'AS_FALSE' otherwise.
 */
AS_BOOL as_writer_is_flushable_data(uint32_t* base_addr);

/**
 * @brief Checks if the module accepts data.
 *
 * This function checks whether the "enable" bit is set or if it has been
 * reset by hardware due to "disable_on_no_go" took effect.
 *
 * @param                       Address of the corresponding hardware
 *                              module (see also as_hardware.h).
 *
 * @return                      Returns 'AS_TRUE' if the "enable" signal
 *                              is set and 'AS_FALSE' otherwise.
 */
AS_BOOL as_writer_is_set_enable(uint32_t* base_addr);




/* Control functions */
/**
 * @brief Resets the hardware module.
 *
 * This function resets the hardware module. All currently performed
 * operations will be terminated.
 *
 * @param                       Address of the corresponding hardware
 *                              module (see also as_hardware.h).
 */
void as_reader_writer_reset(uint32_t* base_addr);

/**
 * @brief Starts operation of hardware module.
 *
 * This function enables the hardware module to perform a read operation
 * according to prior configuration. IF the hardware module is currently
 * in operation then the "pending go" bit will be set to have the next
 * operation be performed right after finishing the current one (thus
 * minimizing downtime). This function may only be called after performing
 * all required configurations of this module.
 *
 * @param                       Address of the corresponding hardware
 *                              module (see also as_hardware.h).
 */
void as_reader_writer_set_go(uint32_t* base_addr);


/* Memwriter only */
/**
 * @brief Enable module input port.
 *
 * This function enables the hardware module to receive data at its input
 * port for writing data to memory.
 *
 * @param                       Address of the corresponding hardware
 *                              module (see also as_hardware.h).
 */
void as_writer_set_enable(uint32_t* base_addr);

/**
 * @brief Disable module input port.
 *
 * This function disables the hardware module to receive data at its input
 * port for writing data to memory.
 *
 * @param                       Address of the corresponding hardware
 *                              module (see also as_hardware.h).
 */
void as_writer_set_disable(uint32_t* base_addr);

/**
 * @brief Enable module input port on data unit complete.
 *
 * This function synchronizes every section start of the reader_writer on the
 * "data_unit_complete" signal of the connected hardware module. All data
 * will be discarded until a high value at the "data_unit_complete" hardware
 * port is received. This allows the reader_writer to be activated with a
 * continuously running hardware processing chain.
 *
 * @param                       Address of the corresponding hardware
 *                              module (see also as_hardware.h).
 */
void as_writer_set_enable_on_data_unit_complete(uint32_t* base_addr);

/**
 * @brief Transfer single data unit to memory.
 *
 * This function requests the reader_writer to only write a single data unit
 * to memory. After all data has been written to memory, the reader_writer is
 * reset, which results in all previously set control bits to be cleared.
 * After the reset, the reader_writer may receive a new configuration and "go" signal.
 *
 * @param                       Address of the corresponding hardware
 *                              module (see also as_hardware.h).
 */
void as_writer_set_single_shot(uint32_t* base_addr);

/**
 * @brief Disable module if no operation is queued.
 *
 * This function disables the module if no additional "go" signal has been
 * set (i.e. no "pending_go") during the current operation of the reader_writer.
 * The hardware will set the "enable" bit "0" upon disabling the reader_writer.
 *
 * @param                       Address of the corresponding hardware
 *                              module (see also as_hardware.h).
 */
void as_writer_set_disable_on_no_go(uint32_t* base_addr);

/**
 * @brief Flush data to memory.
 *
 * This function requests to write all currently stored data in the fifo
 * buffer of the reader_writer to memory.
 *
 * @param                       Address of the corresponding hardware
 *                              module (see also as_hardware.h).
 */
void as_writer_set_flush(uint32_t* base_addr);


/** @}*/

#endif /** AS_READER_WRITER_H */
