/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework.
--  Copyright (C) Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Module:         as_sensor_ov7670
--
-- Company:        Efficient Embedded Systems Group at University of Applied Sciences, Augsburg, Germany
-- Author:         Michael Schaeferling
--
-- Modified:       Philip Manke: Add support for as_iic IIC hardware
--
-- Description:    Driver (source file) for as_sensor_ov7670 module
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
 * @file  as_sensor_ov7670.c
 * @brief Driver (source file) for as_sensor_ov7670 module.
 */


#include "as_sensor_ov7670.h"
#include <unistd.h>  // for usleep()


/* Xilinx specific headers, needed for IIC device address and communication: */
#include "xparameters.h"


#ifndef USING_AS_IIC
#include "xiic_l.h"
#ifndef XPAR_AS_SENSOR_OV7670_0_IIC_0_BASEADDR
 #error "This module needs an IIC module for sensor configuration."
#else
 /* use OV7670_IIC for IIC device base address in the driver: */
 #define OV7670_IIC XPAR_AS_SENSOR_OV7670_0_IIC_0_BASEADDR
#endif
#else
 #include "as_iic.h"
 // Modify if necessary
 #define OV7670_IIC AS_MODULE_BASEADDR_AS_IIC_0
#endif




/* This is the IIC bus address of the sensor: */
#define OV7670_IIC_SLV_ADDR 0x42

/* Register definitions in OV7670 sensor module:
   -- Identification: Manufacturer-- */
#define MIDH_REG        0x1C
#define MIDH_REG_VAL    0x7F
#define MIDL_REG        0x1D
#define MIDL_REG_VAL    0xA2
/* -- Identification: Product-- */
#define PID_REG         0x0A
#define PID_REG_VAL     0x76
#define VER_REG         0x73
#define VER_REG_VAL     0xA2

/* -- Output drive capability and soft sleep -- */
#define COM2_REG 0x09

/* -- Exposure --
   AGC is set in COM8[0] */
#define AEC_REG 0x13
#define AEC_EN_BIT 0
/* Exposure is a 16 bit value, splitted and stored in following registers:
   [15:10] in AECHH(0x07)[5:0]
   [ 9: 2] in  AECH(0x10)[7:0]
   [ 1: 0] in  COM1(0x04)[1:0] */
#define EXP_REG_AECHH   0x07
#define EXP_REG_AECH    0x10
#define EXP_REG_COM1    0x04
/* -- Gain -- */
#define GAIN_REG 0x00
/* AGC is set in COM8[2] */
#define AGC_REG 0x13
#define AGC_EN_BIT 2


/* These extra settings cause image artifacts, making it look "compressed" */
/* #define OV7670_USE_EXTRA_CONFIG */

/* Default Contrast values. When calling the 'Init' function, the sensor will be put to these values: */
#define OV7670_INIT_CONTRAST_CONTROL 85
#define OV7670_INIT_CONTRAST_CENTER  255


/* IIC function declarations (internal use only): */
uint32_t ov7670_iic_reg_set(uint8_t iic_adr, uint8_t reg_adr, uint8_t value);
uint32_t ov7670_iic_reg_get(uint8_t iic_adr, uint8_t reg_adr, uint8_t *value);
/* Simplified usage of IIC write: */
#define IIC_SETREG(r,v) ov7670_iic_reg_set(OV7670_IIC_SLV_ADDR, (r),(v));


/* Internal values of exposure and gain: */
uint32_t ov7670_exposure = 0;
uint8_t  ov7670_gain = 0;


void as_sensor_ov7670_resolution_set(uint32_t* base_addr){
    as_reg_write( as_module_reg(base_addr, AS_SENSOR_OV7670_PARM0_REG_OFFSET), (OV7670_SENSOR_WIDTH << 16) | OV7670_SENSOR_HEIGHT );
}


/* The register values (along with some comments) for this initialization function are taken from the Linux driver "ov7670.c". */
void ov7670_set_registers_vga_gray(){
    IIC_SETREG(0x11, 0x01) /* OV: clock scale */
    IIC_SETREG(0x3a, 0x04) /* OV */
    IIC_SETREG(0x12, 0x00) /* VGA */
    IIC_SETREG(0x8C, 0x00)
    IIC_SETREG(0x17, 0x13) /* HSTART */
    IIC_SETREG(0x18, 0x01) /* HSTOP */
    IIC_SETREG(0x32, 0xb6) /* HREF */
    IIC_SETREG(0x19, 0x02) /* VSTART */
    IIC_SETREG(0x1A, 0x7a) /* VSTOP */
    IIC_SETREG(0x03, 0x0a) /* VREF */
    IIC_SETREG(0x0C, 0x00) /* COM13 */
    IIC_SETREG(0x3E, 0x00) /* COM14 */
    IIC_SETREG(0x70, 0x3a) /* MISTERY SCALLING NUMBER */
    IIC_SETREG(0x71, 0x35)
    IIC_SETREG(0x72, 0x11)
    IIC_SETREG(0x73, 0xf0)
    IIC_SETREG(0xa2, 0x02)
    IIC_SETREG(0x15, 0x00) /* END OF MISTERY SCALLING NUMBER */
    IIC_SETREG(0x7a, 0x20) /* GAMMA CURVES VALUES */
    IIC_SETREG(0x7b, 0x10)
    IIC_SETREG(0x7c, 0x1e)
    IIC_SETREG(0x7d, 0x35)
    IIC_SETREG(0x7e, 0x5a)
    IIC_SETREG(0x7f, 0x69)
    IIC_SETREG(0x80, 0x76)
    IIC_SETREG(0x81, 0x80)
    IIC_SETREG(0x82, 0x88)
    IIC_SETREG(0x83, 0x8f)
    IIC_SETREG(0x84, 0x96)
    IIC_SETREG(0x85, 0xa3)
    IIC_SETREG(0x86, 0xaf)
    IIC_SETREG(0x87, 0xc4)
    IIC_SETREG(0x88, 0xd7)
    IIC_SETREG(0x89, 0xe8) /* END OF GAMMA CURVES VALUES */
    IIC_SETREG(0x13, 0x8f) /* & IIC_SETREG(0x80" OR X"40" OR X"20")), (COM8) */
    IIC_SETREG(0x00, 0x00) /* GAIN */
    IIC_SETREG(0x10, 0x00) /* AECH */
    IIC_SETREG(0x0D, 0x40) /* COM4 */
    IIC_SETREG(0x14, 0x18) /* COM9 */
    IIC_SETREG(0xa5, 0x05) /* BD50MAX */
    IIC_SETREG(0xab, 0x07) /* BD60MAX */
    IIC_SETREG(0x24, 0x95) /* AEW */
    IIC_SETREG(0x25, 0x33) /* AEB */
    IIC_SETREG(0x26, 0xe3) /* VPT */
    IIC_SETREG(0x9f, 0x78) /* HAECC1 */
    IIC_SETREG(0xA0, 0x68) /* HAECC2 */
    IIC_SETREG(0xa1, 0x03) /* MAGIC NUMBER */
    IIC_SETREG(0xA6, 0xd8) /* HAECC3 */
    IIC_SETREG(0xA7, 0xd8) /* HAECC4 */
    IIC_SETREG(0xA8, 0xf0) /* HAECC5 */
    IIC_SETREG(0xA9, 0x90) /* HAECC6 */
    IIC_SETREG(0xAA, 0x94) /* HAECC7 */
    IIC_SETREG(0x13, 0xe5) /* & IIC_SETREG(0x80" OR X"40" OR X"20" OR X"04"OR X"01")), (COM8) */
    IIC_SETREG(0x0E, 0x61) /* COM5 */
    IIC_SETREG(0x0F, 0x4b) /* COM6 */
    IIC_SETREG(0x16, 0x02)
    IIC_SETREG(0x1E, 0x07) /* MVFP */
    IIC_SETREG(0x21, 0x02)
    IIC_SETREG(0x22, 0x91)
    IIC_SETREG(0x29, 0x07)
    IIC_SETREG(0x33, 0x0b)
    IIC_SETREG(0x35, 0x0b)
    IIC_SETREG(0x37, 0x1d)
    IIC_SETREG(0x38, 0x71)
    IIC_SETREG(0x39, 0x2a)
    IIC_SETREG(0x3C, 0x78) /* COM12 */
    IIC_SETREG(0x4d, 0x40)
    IIC_SETREG(0x4e, 0x20)
    IIC_SETREG(0x69, 0x00) /* GFIX */
    IIC_SETREG(0x6b, 0x4a)
    IIC_SETREG(0x74, 0x10)
    IIC_SETREG(0x8d, 0x4f)
    IIC_SETREG(0x8e, 0x00)
    IIC_SETREG(0x8f, 0x00)
    IIC_SETREG(0x90, 0x00)
    IIC_SETREG(0x91, 0x00)
    IIC_SETREG(0x96, 0x00)
    IIC_SETREG(0x9a, 0x00)
    IIC_SETREG(0xb0, 0x84)
    IIC_SETREG(0xb1, 0x0c)
    IIC_SETREG(0xb2, 0x0e)
    IIC_SETREG(0xb3, 0x82)
    IIC_SETREG(0xb8, 0x0a)
    IIC_SETREG(0x43, 0x0a) /* MAGIC NUMBERS */
    IIC_SETREG(0x44, 0xf0)
    IIC_SETREG(0x45, 0x34)
    IIC_SETREG(0x46, 0x58)
    IIC_SETREG(0x47, 0x28)
    IIC_SETREG(0x48, 0x3a)
    IIC_SETREG(0x59, 0x88)
    IIC_SETREG(0x5a, 0x88)
    IIC_SETREG(0x5b, 0x44)
    IIC_SETREG(0x5c, 0x67)
    IIC_SETREG(0x5d, 0x49)
    IIC_SETREG(0x5e, 0x0e)
    IIC_SETREG(0x6c, 0x0a)
    IIC_SETREG(0x6d, 0x55)
    IIC_SETREG(0x6e, 0x11)
    IIC_SETREG(0x6f, 0x9E) /* 9E FOR ADVANCE AWB */
    IIC_SETREG(0x6a, 0x40)
    IIC_SETREG(0x01, 0x40) /* REG BLUE */
    IIC_SETREG(0x02, 0x60) /* REG_RED */
    /* IIC_SETREG(0x13" & IIC_SETREG(0x80" OR X"40" OR X"20" OR X"04" OR X"01" OR X"02")), */ /* COM8 AWB AGC AEC */
    IIC_SETREG(0x13, 0xe5) /*& IIC_SETREG(0x80" OR X"40" OR X"20" OR X"04" OR X"01")), */ /* COM8 AGC AEC */
    /*IIC_SETREG(0x13" & IIC_SETREG(0x80" OR X"40" OR X"20" OR X"04")), */ /* COM8 AGC */
    /*IIC_SETREG(0x13" & IIC_SETREG(0x80" OR X"40" OR X"20" )), */ /* COM8 */
    /*IIC_SETREG(0x13" & IIC_SETREG(0x80" OR X"40" OR X"20" OR X"01" )), */ /* COM8 AEC IIC_SETREG(BEST CONFIG FOR LINE DETECTION) */

    /* The following settings cause image artifacts, making it look "compressed" */
#ifdef OV7670_USE_EXTRA_CONFIG
    IIC_SETREG(0x4f, 0x80) /* "matrix coefficient 1" */
    IIC_SETREG(0x50, 0x80) /* "matrix coefficient 2" */
    IIC_SETREG(0x51, 0x00) /* vb */
    IIC_SETREG(0x52, 0x22) /* "matrix coefficient 4" */
    IIC_SETREG(0x53, 0x5e) /* "matrix coefficient 5" */
    IIC_SETREG(0x54, 0x80) /* "matrix coefficient 6" */
    IIC_SETREG(0x58, 0x9e)

    IIC_SETREG(0x41, 0x08) /* COM16 */
    IIC_SETREG(0x3F, 0x00) /* EDGE */

    IIC_SETREG(0x75, 0x05)
    IIC_SETREG(0x76, 0xe1)
    IIC_SETREG(0x4c, 0x00)
    IIC_SETREG(0x77, 0x01)

    /*IIC_SETREG(0x3D" & IIC_SETREG(0x80"OR X"40" OR X"03")),*/ /* COM13 */
    IIC_SETREG(0x3D, 0xC0) /* & IIC_SETREG(0x80"OR X"40")), */
    IIC_SETREG(0xc9, 0x60)
    IIC_SETREG(0x41, 0x38) /* COM16 */
    IIC_SETREG(0x56, 0x40)
    IIC_SETREG(0x34, 0x11)
    IIC_SETREG(0x3B, 0x12) /* & IIC_SETREG(0x02"OR X"10")), (COM11) */

    IIC_SETREG(0xa4, 0x88)
    IIC_SETREG(0x96, 0x00)
    IIC_SETREG(0x97, 0x30)
    IIC_SETREG(0x98, 0x20)
    IIC_SETREG(0x99, 0x30)
    IIC_SETREG(0x9a, 0x84)
    IIC_SETREG(0x9b, 0x29)
    IIC_SETREG(0x9c, 0x03)
    IIC_SETREG(0x9d, 0x4c)
    IIC_SETREG(0x9e, 0x3f)
    IIC_SETREG(0x78, 0x04)
    /* Extra-weird stuff.  Some sort of multiplexor register */
    IIC_SETREG(0x79, 0x01)
    IIC_SETREG(0xc8, 0xf0)
    IIC_SETREG(0x79, 0x0f)
    IIC_SETREG(0xc8, 0x00)
    IIC_SETREG(0x79, 0x10)
    IIC_SETREG(0xc8, 0x7e)
    IIC_SETREG(0x79, 0x0a)
    IIC_SETREG(0xc8, 0x80)
    IIC_SETREG(0x79, 0x0b)
    IIC_SETREG(0xc8, 0x01)
    IIC_SETREG(0x79, 0x0c)
    IIC_SETREG(0xc8, 0x0f)
    IIC_SETREG(0x79, 0x0d)
    IIC_SETREG(0xc8, 0x20)
    IIC_SETREG(0x79, 0x09)
    IIC_SETREG(0xc8, 0x80)
    IIC_SETREG(0x79, 0x02)
    IIC_SETREG(0xc8, 0xc0)
    IIC_SETREG(0x79, 0x03)
    IIC_SETREG(0xc8, 0x40)
    IIC_SETREG(0x79, 0x05)
    IIC_SETREG(0xc8, 0x30)
    IIC_SETREG(0x79, 0x26)
    IIC_SETREG(0x04, 0x00) /* COM1 */
    IIC_SETREG(0x40, 0xC0) /* COM15 */
    IIC_SETREG(0xff, 0xff)
#endif
}


static int as_sensor_ov7670_identify(){
    uint8_t midl, midh = 0;

#ifdef DEBUG_PRINT
    xil_printf("Getting Sensor ID. \n\r");
#endif
    ov7670_iic_reg_get(OV7670_IIC_SLV_ADDR, MIDH_REG, &midh);
    ov7670_iic_reg_get(OV7670_IIC_SLV_ADDR, MIDL_REG, &midl);

    if ((midh == MIDH_REG_VAL) && (midl == MIDL_REG_VAL)){
#ifdef DEBUG_PRINT
        xil_printf("Sensor ID ok: ");
        xil_printf("MIDH=[0x%02X] MDIL=[0x%02X] \n\r",midh, midl);
#endif
        return 1;
    }
    else{
#ifdef DEBUG_PRINT
        xil_printf("Sensor ID fail: ");
        xil_printf("MIDH=[0x%02X] MDIL=[0x%02X] \n\r",midh, midl);
#endif
        return 0;
    }
}


uint8_t as_sensor_ov7670_init(uint32_t* base_addr)
{
    IIC_SETREG(COM2_REG, 0x00) /* Set Video Output Strength to 1x (lowest possible value to avoid crosstalk) */

    // Check for sensor ID:
    if (!as_sensor_ov7670_identify()) return 0;

    as_sensor_ov7670_resolution_set(base_addr);
    as_sensor_ov7670_reset(base_addr);

    /* Perform a reset to the sensors core: */
    IIC_SETREG(0x12, 0x80) /* COM7   SCCB Register Reset */
    /* wait some time after reset: */
    usleep(10000);


    IIC_SETREG(COM2_REG, 0x00) /* Set Video Output Strength to 1x (lowest possible value to avoid crosstalk) */

    /* Set default iic register values for grayscale at VGA resolution: */
    ov7670_set_registers_vga_gray();

    /* Set 25fps for 50HZ light environment (0x66=25fps; 0x0=30fps): */
    IIC_SETREG(0x92, 0x66)

    /* Set Contrast: */
    IIC_SETREG(0x56, OV7670_INIT_CONTRAST_CONTROL)
    IIC_SETREG(0x57, OV7670_INIT_CONTRAST_CENTER)

    /* Set Exposure and Gain to auto: */
    as_sensor_ov7670_exposure_auto(1);
    as_sensor_ov7670_gain_auto(1);

    return 1;
}

void as_sensor_ov7670_reset(uint32_t* base_addr){
    /* Soft-Reset (as_sensor_ov7670 module in ASTERICS chain): */
    as_reg_write_masked( as_module_reg(base_addr, AS_SENSOR_OV7670_STATE_CONTROL_REG_OFFSET), AS_SENSOR_OV7670_RESET_MASK, 0xffffffff);

    /* Reset to external OV7670 sensor: */
    as_reg_write_masked( as_module_reg(base_addr, AS_SENSOR_OV7670_STATE_CONTROL_REG_OFFSET), AS_SENSOR_OV7670_EXT_RESET_MASK, 0xffffffff);
    usleep(10000);
    as_reg_write_masked( as_module_reg(base_addr, AS_SENSOR_OV7670_STATE_CONTROL_REG_OFFSET), AS_SENSOR_OV7670_EXT_RESET_MASK, 0x0);
    usleep(10000);
}


void as_sensor_ov7670_run(uint32_t* base_addr){
    as_reg_write_masked( as_module_reg(base_addr, AS_SENSOR_OV7670_STATE_CONTROL_REG_OFFSET), AS_SENSOR_OV7670_ENABLEONCE_MASK, 0x0);
    as_reg_write_masked( as_module_reg(base_addr, AS_SENSOR_OV7670_STATE_CONTROL_REG_OFFSET), AS_SENSOR_OV7670_DATAENABLE_MASK, 0xffffffff);
}


void as_sensor_ov7670_stop(uint32_t* base_addr){
    as_reg_write_masked( as_module_reg(base_addr, AS_SENSOR_OV7670_STATE_CONTROL_REG_OFFSET), AS_SENSOR_OV7670_DATAENABLE_MASK, 0x0);
}


void as_sensor_ov7670_run_once(uint32_t* base_addr){
    as_reg_write_masked( as_module_reg(base_addr, AS_SENSOR_OV7670_STATE_CONTROL_REG_OFFSET), AS_SENSOR_OV7670_ENABLEONCE_MASK, 0xffffffff);
    as_reg_write_masked( as_module_reg(base_addr, AS_SENSOR_OV7670_STATE_CONTROL_REG_OFFSET), AS_SENSOR_OV7670_DATAENABLE_MASK, 0xffffffff);
}

AS_BOOL as_sensor_ov7670_frame_is_transmitted(uint32_t* base_addr){
    return as_reg_read_masked( as_module_reg( base_addr, AS_SENSOR_OV7670_STATE_CONTROL_REG_OFFSET), AS_SENSOR_OV7670_FRAME_DONE_MASK) ? AS_TRUE : AS_FALSE;
}


void as_sensor_ov7670_exposure_auto(AS_BOOL enable){
    uint8_t val;
    ov7670_iic_reg_get(OV7670_IIC_SLV_ADDR, AEC_REG, &val);

    if (enable == AS_TRUE)
        val |= 1 << AEC_EN_BIT;
    else
        val &= ~(1 << AEC_EN_BIT);

    ov7670_iic_reg_set(OV7670_IIC_SLV_ADDR, AEC_REG, val);
}


void as_sensor_ov7670_exposure_set(uint32_t exposure)
{
    uint8_t val;

    exposure &= 0x0000ffff;

    val = (uint8_t)(exposure & 0x03);
    ov7670_iic_reg_set(OV7670_IIC_SLV_ADDR, EXP_REG_COM1, val);

    val = (uint8_t)(exposure >> 2);
    ov7670_iic_reg_set(OV7670_IIC_SLV_ADDR, EXP_REG_AECH, val);

    val = (uint8_t)((exposure >> 10) & 0x3F);
    ov7670_iic_reg_set(OV7670_IIC_SLV_ADDR, EXP_REG_AECHH, val);

    ov7670_exposure = exposure;
}


uint32_t as_sensor_ov7670_exposure_get()
{
    uint8_t val;
    uint32_t val_full = 0;

    ov7670_iic_reg_get(OV7670_IIC_SLV_ADDR, EXP_REG_COM1, &val);
    val_full |= val & 0x03;

    ov7670_iic_reg_get(OV7670_IIC_SLV_ADDR, EXP_REG_AECH, &val);
    val_full |= val << 2;

    ov7670_iic_reg_get(OV7670_IIC_SLV_ADDR, EXP_REG_AECHH, &val);
    val_full |= (val & 0x3F) << 10;

    ov7670_exposure = val_full;
    return val_full;
}


void as_sensor_ov7670_gain_auto(AS_BOOL enable){
    uint8_t val;
    ov7670_iic_reg_get(OV7670_IIC_SLV_ADDR, AGC_REG, &val);

    if (enable == AS_TRUE)
        val |= 1 << AGC_EN_BIT;
    else
        val &= ~(1 << AGC_EN_BIT);

    ov7670_iic_reg_set(OV7670_IIC_SLV_ADDR, AGC_REG, val);
}


void as_sensor_ov7670_gain_set(uint8_t gain)
{
    if ((gain > 0)||(gain < 255)){
        ov7670_iic_reg_set(OV7670_IIC_SLV_ADDR, GAIN_REG, gain);
        ov7670_gain = gain;
    }
}


uint8_t as_sensor_ov7670_gain_get()
{
    #define GAIN_REG 0x00

    uint8_t val;
    ov7670_iic_reg_get(OV7670_IIC_SLV_ADDR, GAIN_REG, &val);
    ov7670_gain = val;
    return val;
}


/* ov7670_iic_reg_set and ov7670_iic_reg_get make use of specific Xilinx IIC ipcore functions;
 * change these if you want to use them with another IIC API */
uint32_t ov7670_iic_reg_set(uint8_t iic_adr, uint8_t reg_adr, uint8_t value)
{
    /* Note: OV7670 IIC interface is quite slow... give it some time between sequential accesses. */

    int send;


    uint8_t data[2] = {0};
    data[0] = reg_adr;
    data[1] = value;
#ifdef DEBUG_PRINT
    xil_printf("Set: Send to [0x%02X]: [0x%02X] <- [0x%02X] \n\r", iic_adr, reg_adr, value);
#endif
#ifdef USING_AS_IIC 
    send = as_iic_write_reg(OV7670_IIC, iic_adr, &reg_adr, &value);
    xil_printf("Got from as_iic: %x\n", send);
#else
    send = XIic_Send(OV7670_IIC, iic_adr>>1, data, 2, XIIC_STOP);
#endif
    usleep(100);

    return send;
}


uint32_t ov7670_iic_reg_get(uint8_t iic_adr, uint8_t reg_adr, uint8_t *value)
{
    /* Note: OV7670 IIC interface is quite slow... give it some time between sequential accesses. */

    uint32_t send;

#ifdef DEBUG_PRINT
    xil_printf("Get: Send to [0x%02X]: [0x%02X] \n\r", iic_adr, *value);
#endif
#ifdef USING_AS_IIC
    send = as_iic_read_reg(OV7670_IIC, iic_adr, &reg_adr, value);
    xil_printf("Got from as_iic: %x\n", send);
    
#else
    iic_adr = iic_adr >> 1;

    uint8_t data = reg_adr;
    send = XIic_Send(OV7670_IIC, iic_adr, &data, 1, XIIC_STOP);

    usleep(100);

    send = XIic_Recv(OV7670_IIC, iic_adr, &data, 1, XIIC_STOP);
    *value = data;
#endif
#ifdef DEBUG_PRINT
    xil_printf("Get: Got from [0x%02X]: [0x%02X] \n\r", iic_adr, *value);
#endif

    usleep(100);

    return send;
}

