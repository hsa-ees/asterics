/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework.
--  Copyright (C) Hochschule Augsburg, University of Applied Sciences, All rights
--  reserved
----------------------------------------------------------------------------------
-- File:           as_memio.h
-- Module:         as_memio
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Author:         Julian Sarcher, Alexander Zoellner
--
-- Modified:
--
-- Description:    Driver (header file) for as_memio streaming interface with
--                 as_memreader and as_memwriter hardware modules.
----------------------------------------------------------------------------------
--! @file
--! @brief Driver (header file) for as_memio streaming interface.
--------------------------------------------------------------------------------*/


#ifndef _AS_MEMIO_H_
#define _AS_MEMIO_H_

#include "as_support.h"
#include "as_reader_writer.h"

/* Word size of hardware (32- or 64-bit architecture) */
#define AS_MEMIO_DEFAULT_INTERFACE_WIDTH    32U
/* Default maximum burst (in byte!) access on bus (see hardware specification for details) */
#define AS_MEMIO_DEFAULT_MAX_BURST_LENGTH   256U
/* Default buffer size (in byte!) which is needed to prevent data loss on hw side between consecutive read() calls */
#define AS_MEMIO_DEFAULT_HW_TRANSFER_SIZE   256U * 64U
/* Default as_memio buffer size (in byte!) for HW/SW data transfers; CAUTION: Has to be a multiple of AS_MEMIO_DEFAULT_HW_TRANSFER_SIZE*/
#define AS_MEMIO_DEFAULT_FIFO_BUFFER_SIZE   AS_MEMIO_DEFAULT_HW_TRANSFER_SIZE * 32U//256U

#define AS_MEMIO_DEFAULT_MANAGE_CACHE       AS_TRUE



/**
 *
 * Structure: as_memio_config_t
 *
 * @param as_reader_writer_buffer_size          Configures the size of the Ring Buffer in bytes for 
 *                                              intermediately storing data.
 *                                              Increasing the size allows to transfer more data for a 
 *                                              single memory module configuration.
 *                                              The size has to be a multiple of the bus interface width
 *                                              of the memory module.
 * @param as_reader_writer_transfer_size        The minimum section size to be used when a as_memwriter
 *                                              module is utilized. This prevents overflows at the FIFO
 *                                              Buffer of the hardware module.
 *                                              The size is configured in bytes and has to be a multiple
 *                                              of the bus interface width of the as_memwriter module.
 *                                              Currently, this parameter takes no effect when a 
 *                                              as_memreader is associated with the as_memio module.
 * @param as_reader_writer_max_burst_length     Configures the burst length of the memory module in bytes.
 * @param as_reader_writer_interface_width      Configures the bus interface width in bit for the memory
 *                                              module.
 * @param manage_cache                          Set to "true" if the module driver has to handle cache coherency.
 *                                              Otherwise, it is assumed that the HW platform manages coherency 
 *                                              automatically (e.g. the ACP port of ZYNQ).
 * @param read_not_write                        Set to "true" if a as_memwriter is used and "false" otherwise.
 *
 */
typedef struct as_memio_config_s {
    uint32_t as_reader_writer_buffer_size;
    uint32_t as_reader_writer_transfer_size;
    uint32_t as_reader_writer_max_burst_length;
    uint32_t as_reader_writer_interface_width;
    AS_BOOL manage_cache;
    AS_BOOL read_not_write;
}as_memio_config_t;



/**
 *
 * Function: as_memio_init
 *
 * Future implementation - Perform driver initialization for a list of HW modules.
 *
 * @param uint32_t          Number of HW modules
 * @param uint32_t**        List of HW module base addresses
 *
 */
void as_memio_init(uint32_t, uint32_t**);


/**
 *
 * Function: as_memio_done
 *
 * Future implementation - Perform driver deinitialization for a list of HW modules.
 *
 * @param uint32_t          Number of HW modules
 * @param uint32_t**        List of HW module base addresses
 *
 */
void as_memio_done(uint32_t, uint32_t**);


/**
 *
 * Function: as_memio_config_init
 *
 * This function sets default values for as_memio buffer size and maximum burst length for
 * using either a as_memreader or a as_memwriter with as_memio. 
 *
 * @param as_memio_config               Pointer to an as_memio_config structure to set 
 *                                      default values.
 *
 */
void as_memio_config_init(as_memio_config_t * memio_config);


/**
 *
 * Function: as_memio_open
 *
 * This function allocates memory for each HW module ringbuffer and initializes the as_memio 
 * infrastructure for ringbuffer management. Depending on settings of "memio_config" and 
 * "flags" the setup for the corresponding hardware module is performed. 
 * If a NULL-pointer is provided for "memio_config", the default values are used. The "flag"
 * paramter determines whether a as_memreader or as_memwriter is associated.
 * Supported flags are O_RDONLY (as_memwriter) and O_WRONLY (as_memreader). If the former is 
 * used, only calls to "read" are allowed with the "write" interface becoming unavailable and 
 * vice versa for O_WRONLY.
 * The function returns a pointer to the opaque as_memio_file_s structure which can be used for
 * performing further actions on the as_memio module.
 *
 * @param config                            This structure is used to setup the ringbuffer(s) 
 *                                          and hardware modules (see "as_memio_config_init")
 * @param flags                             This variable is used to determine the mode 
 *                                          in which to use the ASTERICS streaming interface. 
 *                                          Depending on this variable either the "as_memreader" 
 *                                          or "as_memwriter" hardware module is used for the 
 *                                          streaming interface.
 *
 * @return                                  The function returns a pointer to the configured
 *                                          structure which can be used for further calls.
 *
 */
struct as_memio_file_s * as_memio_open(uint32_t* as_reader_writer_baseaddr, as_memio_config_t* memio_config, uint8_t flags);


/**
 * Function: as_memio_close
 *
 * This function de-initializes the ASTERICS streaming interface and releases all acquired
 * memory for setting up its infrastructure (i.e. ringbuffer, configuration structures).
 *
 * @param fd                            The pointer to the as_memio structure
 * 
 */
void as_memio_close(struct as_memio_file_s* fd);


/**
 *
 * Function: as_memio_write
 *
 * The purpose of this function is to transfer data from the user software 
 * to the ringbuffer which is used by the as_memreader hardware module. 
 * This function may copy less data from "buffer" than requested by "count" 
 * if the Ring Buffer has not enough empty entries.
 *
 * @param fd                            Pointer to the opaque as_memio structure.
 * @param buffer                        The container which holds data meant 
 *                                      for transferring to hardware.
 * @param count                         Specifies the amount of data requested 
 *                                      by the caller of this function in byte.
 *                                      This value has to be a multiple of the 
 *                                      configured bus interface width of the 
 *                                      as_memreader.
 *
 * @return                              This function returns the number of bytes 
 *                                      which were actually copied from "buffer".
 *
 */
uint32_t as_memio_write(struct as_memio_file_s* fd, const void * buffer, uint32_t count);


/**
 *
 * Function: as_memio_read
 *
 * The purpose of this function is to request data from the as_memwriter
 * hardware module and copies the requested amount but not more than
 * the currently available amount of data into "buffer". This function
 * returns the number of bytes which were actually transfered.
 *
 * @param fd                            Pointer to the opaque as_memio structure.
 * @param buffer                        Pointer to the buffer for copying the 
 *                                      data from hardware to.
 * @param count                         Request a desired amount of data from 
 *                                      the hardware module in byte. This value 
 *                                      has to be a multiple of the configured 
 *                                      bus interface width of the as_memwriter.
 *
 * @return                              The function returns the number of bytes 
 *                                      which were actually transfered to "buffer".
 *
 */
uint32_t as_memio_read(struct as_memio_file_s* fd, void* buffer, uint32_t count);


/**
 *
 * Function: as_memio_hw_read_update
 *
 * This function calls "as_memio_hw_read_update" and "as_memio_hw_write_update" 
 * depending on ASTERICS streaming interface configuration. The user has to 
 * make sure to call this function periodically to ensure that no data gets 
 * "stuck" within the Ring Buffer.
 *
 * @param fd                            Pointer to the opaque as_memio structure.
 */
void as_memio_hw_update(struct as_memio_file_s* fd);


#endif
