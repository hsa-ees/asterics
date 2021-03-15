/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework.
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- Module:         as_picam
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Author:         Thomas Izycki
--
-- Modified:       
--
-- Description:    Driver (source file) for as_picam module
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
 * @file  as_picam.c
 * @brief Driver (source file) for as_picam module.
 */


#include "as_picam.h"

/* The PS I2C is used to configure the raspberry pi camera */
#include "xparameters.h"
#include "xiicps.h"

#define IIC_MULTIPLEXER_ADDR	0x70
#define CAMERA_V1_3_IIC_ADDR	0x36
#define CAMERA_V2_1_IIC_ADDR 	0x10
#define IIC_SCLK_RATE 			100000

#define CS_CMMN_CHIP_ID_H	   	0x300A
#define CS_CMMN_CHIP_ID_L		0x300B

#define TABLE_END		0xffff

/* atomar register element */
struct sensor_cmd {
	 unsigned short reg;
	 unsigned char	val;
};

/* Instance of the IIC Device */
XIicPs instanceIIC;

void write_iic_register(XIicPs *instancePtr, u8 chipAddr, u16 regAddr, u8 regVal) {
	u8 writeData[3];
	int status;

	writeData[0] = regAddr >> 8;
	writeData[1] = regAddr & 0xFF;
	writeData[2] = regVal;
	status = XIicPs_MasterSendPolled(instancePtr, writeData, 3, chipAddr);

	/* Wait until bus is idle to start another transfer */
	while (XIicPs_BusIsBusy(instancePtr)) {
        /* NOP */
    }
}

int read_iic_register(XIicPs *instancePtr, u8 chipAddr, u16 regAddr) {
	u8 writeData[2];
	u8 readData;

	writeData[0] = regAddr >> 8;
	writeData[1] = regAddr & 0xFF;
	XIicPs_MasterSendPolled(instancePtr, writeData, 2, chipAddr);
	XIicPs_MasterRecvPolled(instancePtr, &readData, 1, chipAddr);

    /* Wait until bus is idle */
	while (XIicPs_BusIsBusy(instancePtr)) {
        /* NOP */
    }

	return readData;
}

/* The register values (along with some comments) for the initialization functions are taken from
 * TE0726 Zynqberry Demo (1-3) - https://wiki.trenz-electronic.de/display/PD/TE0726+Zynqberry+Demo1
 * in file zynqberrydemo1/os/petalinux/project-spec/meta-user/recipes-apps/rpicam/files/sensor_config.h
 */
static struct sensor_cmd ov5647_sensor_common_10bit[] = {
	 { 0x3034, 0x1A },	// 10 bit mode
//  { 0x3034, 0x10 },	// 8 bit mode
	 { 0x503D, 0x00 },	// Test Pattern
	 { 0x3035, 0x21 },	// CLK DIV
	 { 0x3036, 0x46 },	// PLL MULT
	 { 0x303c, 0x11 },	// PLLS CP
	 { 0x3106, 0xf5 },	// PLL DIV
	 { 0x3821, 0x07 },	// TIMING TC
	 { 0x3820, 0x41 },	// TIMING TC
	 { 0x3827, 0xec },
	 { 0x370c, 0x0f },
	 { 0x3612, 0x59 },
	 { 0x3503, 0x00 }, // AEC/AGC
	 { 0x5000, 0x89 }, // Lens Correction
	 { 0x5001, 0x01 }, // AWB
	 { 0x5002, 0x41 }, // AWB GAIN, OPT, WIN
	 { 0x5003, 0x0A }, // BIN
	 { 0x5a00, 0x08 },
	 { 0x3000, 0x00 },
	 { 0x3001, 0x00 },
	 { 0x3002, 0x00 },
	 { 0x3016, 0x08 },
	 { 0x3017, 0xe0 },
	 { 0x3018, 0x44 },
	 { 0x301c, 0xf8 },
	 { 0x301d, 0xf0 },
	 { 0x3a18, 0x00 },
	 { 0x3a19, 0xf8 },
	 { 0x3c01, 0x80 }, // 50/60HZ Detection
	 { 0x3b07, 0x0c },
	 { 0x380c, 0x07 },
	 { 0x380d, 0x68 },
	 { 0x380e, 0x03 },
	 { 0x380f, 0xd8 },
	 { 0x3814, 0x31 },
	 { 0x3815, 0x31 },
	 { 0x3708, 0x64 },
	 { 0x3709, 0x52 },
	 { 0x3630, 0x2e },
	 { 0x3632, 0xe2 },
	 { 0x3633, 0x23 },
	 { 0x3634, 0x44 },
	 { 0x3636, 0x06 },
	 { 0x3620, 0x65 },  // V BINNING
	 { 0x3621, 0xe1 },  // H BINNING
	 { 0x3600, 0x37 },
	 { 0x3704, 0xa0 },
	 { 0x3703, 0x5a },
	 { 0x3715, 0x78 },
	 { 0x3717, 0x01 },
	 { 0x3731, 0x02 },
	 { 0x370b, 0x60 },
	 { 0x3705, 0x1a },
	 { 0x3f05, 0x02 },
	 { 0x3f06, 0x10 },
	 { 0x3f01, 0x0a },
	 { 0x3a08, 0x01 },
	 { 0x3a09, 0x27 },
	 { 0x3a0a, 0x00 },
	 { 0x3a0b, 0xf6 },
	 { 0x3a0d, 0x04 },
	 { 0x3a0e, 0x03 },
	 { 0x3a0f, 0x58 },
	 { 0x3a10, 0x50 },
	 { 0x3a1b, 0x58 },
	 { 0x3a1e, 0x50 },
	 { 0x3a11, 0x60 },
	 { 0x3a1f, 0x28 },
	 { 0x4001, 0x02 },
	 { 0x4004, 0x02 },
	 { 0x4000, 0x09 },
	 { 0x4837, 0x24 },
	 { 0x4050, 0x6e },
	 { 0x4051, 0x8f },
	 { TABLE_END, 0x00 },
};

/* 1280 x 720 @ 30 fps */
	 /*
	  * MIPI Link	: 291.667 Mbps
	  * Pixel clock : 58.333 MHz
	  * Timing zone : 1896 x 984
	  * FPS			: 31.3
	  */
static struct sensor_cmd ov5647_sensor_1280_720_30[] = {
  { 0x3035, 0x21 },	// *
  { 0x3036, 0x46 },	// * PLL multiplier
  { 0x303c, 0x11 },	// * PLL div
  { 0x3821, 0x07 },	// * Timing
  { 0x3820, 0x41 },	// * Timing
  { 0x3612, 0x59 },	// ?
  { 0x3618, 0x00 },	// ?
  { 0x380c, 0x07 },	// * Horisontal size [12:8] 1896
  { 0x380d, 0x68 },	// * Horisontal size [7:0]
  { 0x380e, 0x03 },	// * total vertical size [9:8]  984
  { 0x380f, 0xd8 },	// * total vertical size [7:0]
  { 0x3814, 0x31 },	// * timing x inc
  { 0x3815, 0x31 },	// * timing y inc
  { 0x3708, 0x64 },	//
  { 0x3709, 0x52 },	//
  { 0x3808, 0x05 },	//  out horisontal [11:8]	1280
  { 0x3809, 0x00 },	//  out horisontal [7:0]
  { 0x380a, 0x02 },	//  out vertical [11:8]	  720
  { 0x380b, 0xd0 },	//  out vertical [7:0]
  { 0x3800, 0x00 },	//  + X start [11:8]
  { 0x3801, 0x00 },	//  + X start [7:0] /* 18 */
  { 0x3802, 0x00 },	//  + Y start [11:8]
  { 0x3803, 0x08 },	//  + Y start [7:0] /* 0e */
  { 0x3804, 0x0a },	//  + X end [11:8]
  { 0x3805, 0x3b },	//  + X end [7:0]  /* 27 */
  { 0x3806, 0x07 },	//  + Y end [11:8]
  { 0x3807, 0x9b },	//  + Y end [7:0] /* 95 */
  { 0x3a08, 0x01 },	//
  { 0x3a09, 0x27 },	//
  { 0x3a0a, 0x00 },	//
  { 0x3a0b, 0xf6 },	//
  { 0x3a0d, 0x04 },	//
  { 0x3a0e, 0x03 },	//
  { 0x4004, 0x02 },	//
  { 0x4837, 0x24 },	// * PCLK period

  { 0x5001, 0x01 },	// AWB on
  { 0x5002, 0x41 },	// AWB on

  { TABLE_END,  0x00 },	//
};

static struct sensor_cmd imx219_720p_regs[] = { //720: 1280*720@30fps
	{0x30EB, 0x05},
	{0x30EB, 0x0C},
	{0x300A, 0xFF},
	{0x300B, 0xFF},
	{0x30EB, 0x05},
	{0x30EB, 0x09},

	{0x0114, 0x01},	// CSI_LANE_MODE = 2-lane
	{0x0128, 0x00},	// DPHY_CTRL = auto mode

	{0x012A, 0x13},	// EXCLK_FREQ[15:8]
	{0x012B, 0x34},	// EXCLK_FREQ[7:0] = 4916 MHz

	{0x0160, 0x04},	// FRM_LENGTH_A[15:8]
	{0x0161, 0x60},	// FRM_LENGTH_A[7:0] = 1120
	{0x0162, 0x0D},	// LINE_LENGTH_A[15:8]
	{0x0163, 0x78},	// LINE_LENGTH_A[7:0] = 3448
	{0x0164, 0x01},	// XADD_STA_A[11:8]
	{0x0165, 0x58},	// XADD_STA_A[7:0] = X top left = 344
	{0x0166, 0x0B},	// XADD_END_A[11:8]
	{0x0167, 0x77},	// XADD_END_A[7:0] = X bottom right = 2935
	{0x0168, 0x01},	// YADD_STA_A[11:8]
	{0x0169, 0xF0},	// YADD_STA_A[7:0] = Y top left = 496
	{0x016A, 0x07},	// YADD_END_A[11:8]
	{0x016B, 0xAF},	// YADD_END_A[7:0] = Y bottom right = 1967
	{0x016C, 0x05},	// x_output_size[11:8]
	{0x016D, 0x10},	// x_output_size[7:0] = 1296
	{0x016E, 0x02},	// y_output_size[11:8]
	{0x016F, 0xE0}, // y_output_size[7:0] = 736
	{0x0170, 0x01},	// X_ODD_INC_A
	{0x0171, 0x01},	// Y_ODD_INC_A
	{0x0174, 0x01},	// BINNING_MODE_H_A = x2-binning
	{0x0175, 0x01},	// BINNING_MODE_V_A = x2-binning
//    {0x0174, 0x00}, // BINNING_MODE_H_A = no-binning
//    {0x0175, 0x00}, // BINNING_MODE_V_A = no-binning
	{0x0176, 0x01},	// BINNING_CAL_MODE_H_A
	{0x0177, 0x01},	// BINNING_CAL_MODE_V_A
	{0x018C, 0x0A},	// CSI_DATA_FORMAT_A[15:8]
	{0x018D, 0x0A},	// CSI_DATA_FORMAT_A[7:0]
	{0x0301, 0x05},
	{0x0303, 0x01},
	{0x0304, 0x02},
	{0x0305, 0x02},
    {0x0309, 0x0A}, // OPPXCK_DIV
	{0x030B, 0x01}, // OPSYCK_DIV

	{0x0306, 0x00},	// PLL_VT_MPY[10:8]
	//{0x0307, 0x2E},	// PLL_VT_MPY[7:0] = 46
    {0x0307, 0x17}, // PLL_VT_MPY[7:0] = 23
    //{0x0307, 0x0F}, // PLL_VT_MPY[7:0] = 15

	{0x030C, 0x00},	// PLL_OP_MPY[10:8]
	//{0x030D, 0x5C}, // PLL_OP_MPY[7:0] = 92
    {0x030D, 0x2E}, // PLL_OP_MPY[7:0] = 46
    //{0x030D, 0x1E}, // PLL_OP_MPY[7:0] = 30

	{0x455E, 0x00},
	{0x471E, 0x4B},
	{0x4767, 0x0F},
	{0x4750, 0x14},
	{0x4540, 0x00},
	{0x47B4, 0x14},
	{0x4713, 0x30},
	{0x478B, 0x10},
	{0x478F, 0x10},
	{0x4793, 0x10},
	{0x4797, 0x0E},
	{0x479B, 0x0E},
	//{0x0601, 0x02}, // Test pattern = Color bar
    {0x0601, 0x00}, // Test pattern = Normal work
	{0x0620, 0x00},	// TP_WINDOW_X_OFFSET[11:8]
    {0x0621, 0x00}, // TP_WINDOW_X_OFFSET[7:0]
    {0x0621, 0x00}, // TP_WINDOW_Y_OFFSET[11:8]
    {0x0623, 0x00}, // TP_WINDOW_Y_OFFSET[7:0]
    {0x0624, 0x05}, // TP_WINDOW_WIDTH[11:8]
    {0x0625, 0x00}, // TP_WINDOW_WIDTH[7:0] = 1280
    {0x0626, 0x02}, // TP_WINDOW_HEIGHT[11:8]
    {0x0627, 0xD0}, // TP_WINDOW_HEIGHT[7:0] = 720
    {0x0100, 0x01}, /* mode select streaming on */
    {TABLE_END, 0x00}
};

void write_config_picam_iic(XIicPs *instancePtr, u8 chip_addr, struct sensor_cmd *set) {
	int i;
	for (i = 0; set[i].reg != TABLE_END; i++)
	{
		write_iic_register(instancePtr, chip_addr, set[i].reg, set[i].val);
	}
}

int init_iic(uint16_t device_id) {
	int status;
	int Index;
	XIicPs_Config *Config;
	XIicPs *instancePtr = &instanceIIC;

	/* Initialize the IIC driver so that it's ready to use
	 * Look up the configuration in the config table,
	 * then initialize it.
	 */
	Config = XIicPs_LookupConfig(device_id);
	if (NULL == Config)
	{
		return XST_FAILURE;
	}

	status = XIicPs_CfgInitialize(instancePtr, Config, Config->BaseAddress);
	if (status != XST_SUCCESS)
	{
		return XST_FAILURE;
	}

	/* Perform a self-test to ensure that the hardware was built correctly. */
	status = XIicPs_SelfTest(instancePtr);
	if (status != XST_SUCCESS)
	{
		return XST_FAILURE;
	}

	/* Set the IIC serial clock rate. */
	XIicPs_SetSClk(instancePtr, IIC_SCLK_RATE);

    return status;
}

int configure_picam_v2_iic(XIicPs *instancePtr) {
    int status;
	u8 writeData[1];
    u8 readData[1];
	u16 modelID;

    /* Set the I2C Multiplexer to the channel required for addressing the picam */
	writeData[0] = 0x07;
	status = XIicPs_MasterSendPolled(instancePtr, writeData, 1, IIC_MULTIPLEXER_ADDR);
	if (status != XST_SUCCESS)
	{
		return XST_FAILURE;
	}

	/* Wait until bus is idle to start another transfer. */
	while (XIicPs_BusIsBusy(instancePtr))
	{
		/* NOP */
	}

    write_config_picam_iic(instancePtr, CAMERA_V2_1_IIC_ADDR, imx219_720p_regs);

	return XST_SUCCESS;
}

int configure_picam_v1_iic(XIicPs *instancePtr) {
	int status;
	u8 writeData[1];
    u8 readData[2];

	/* Set the I2C Multiplexer to the channel required for addressing the picam */
	writeData[0] = 0x07;
	status = XIicPs_MasterSendPolled(instancePtr, writeData, 1, IIC_MULTIPLEXER_ADDR);
	if (status != XST_SUCCESS)
	{
		return XST_FAILURE;
	}

	/* Wait until bus is idle to start another transfer. */
	while (XIicPs_BusIsBusy(instancePtr))
	{
		/* NOP */
	}

	write_iic_register(instancePtr, CAMERA_V1_3_IIC_ADDR, 0x0100, 0x00);	// Disable
	write_iic_register(instancePtr, CAMERA_V1_3_IIC_ADDR, 0x0103, 0x01);	// Reset
	for(int i=1000; i != 0; i--) {
		/* wait for camera to reset */
	}
	write_iic_register(instancePtr, CAMERA_V1_3_IIC_ADDR, 0x0103, 0x01);	// Reset
	for(int i=1000000; i != 0; i--) {
		/* wait for camera to reset again but longer */
	}
	// Load common configuration
	write_config_picam_iic(instancePtr, CAMERA_V1_3_IIC_ADDR,ov5647_sensor_common_10bit);
	// load specific configuration
	write_config_picam_iic(instancePtr, CAMERA_V1_3_IIC_ADDR,ov5647_sensor_1280_720_30);
	write_iic_register(instancePtr, CAMERA_V1_3_IIC_ADDR, 0x0100, 0x01);	// Reset

	return XST_SUCCESS;
}

int as_picam_init(uint16_t iic_device_id) {
	int status;
	u8 writeData[1];
    u8 readData[2];
	u16 modelID;

	XIicPs *instancePtr = &instanceIIC;

    /* Init the I2C module */
    init_iic(iic_device_id);

    /* Set the I2C Multiplexer to the channel required for addressing the picam */
	writeData[0] = 0x07;
	status = XIicPs_MasterSendPolled(instancePtr, writeData, 1, IIC_MULTIPLEXER_ADDR);
	if (status != XST_SUCCESS)
	{
		return XST_FAILURE;
	}

	/* Wait until bus is idle to start another transfer. */
	while (XIicPs_BusIsBusy(instancePtr))
	{
		/* NOP */
	}

	/* Check for version 2.19 camera */
	readData[0] = read_iic_register(instancePtr, CAMERA_V2_1_IIC_ADDR, 0x0000);
	if (status != XST_SUCCESS)
	{
		return XST_FAILURE;
	}
	modelID = readData[0] << 8;

	readData[0] = read_iic_register(instancePtr, CAMERA_V2_1_IIC_ADDR, 0x0001);
	if (status != XST_SUCCESS)
	{
		return XST_FAILURE;
	}
	modelID |= readData[0];

	if(modelID == 0x0219) {
#ifdef DEBUG_PRINT
		xil_printf("Raspberry Pi camera v2.19 found.\n\r");
#endif
		status = configure_picam_v2_iic(instancePtr);
    	if (status != XST_SUCCESS)
		{
			return XST_FAILURE;
		}
		return XST_SUCCESS;
	}

	/* Check for version 1.3 camera */
	readData[0] = read_iic_register(instancePtr, CAMERA_V1_3_IIC_ADDR, CS_CMMN_CHIP_ID_H);
	if (status != XST_SUCCESS)
	{
		return XST_FAILURE;
	}

	readData[1] = read_iic_register(instancePtr, CAMERA_V1_3_IIC_ADDR, CS_CMMN_CHIP_ID_L);
	if (status != XST_SUCCESS)
	{
		return XST_FAILURE;
	}

	if (!((readData[0] != 0x56) || (readData[1] != 0x47))) {
#ifdef DEBUG_PRINT
		xil_printf("Raspberry Pi camera v1.3 found.\n\r");
#endif
		status = configure_picam_v1_iic(instancePtr);
		if (status != XST_SUCCESS)
		{
			return XST_FAILURE;
		}
		return XST_SUCCESS;
	}

	return XST_FAILURE;
}

void as_picam_run(uint32_t* base_addr){
    as_reg_write_masked( as_module_reg(base_addr, AS_PICAM_STATE_CONTROL_REG_OFFSET), AS_PICAM_ENABLEONCE_MASK, 0x0);
    as_reg_write_masked( as_module_reg(base_addr, AS_PICAM_STATE_CONTROL_REG_OFFSET), AS_PICAM_DATAENABLE_MASK, 0xffffffff);
}

void as_picam_stop(uint32_t* base_addr){
    as_reg_write_masked( as_module_reg(base_addr, AS_PICAM_STATE_CONTROL_REG_OFFSET), AS_PICAM_DATAENABLE_MASK, 0x0);
}

void as_picam_run_once(uint32_t* base_addr){
    as_reg_write_masked( as_module_reg(base_addr, AS_PICAM_STATE_CONTROL_REG_OFFSET), AS_PICAM_ENABLEONCE_MASK, 0xffffffff);
    as_reg_write_masked( as_module_reg(base_addr, AS_PICAM_STATE_CONTROL_REG_OFFSET), AS_PICAM_DATAENABLE_MASK, 0xffffffff);
}

AS_BOOL as_picam_frame_is_transmitted(uint32_t* base_addr){
    return as_reg_read_masked( as_module_reg( base_addr, AS_PICAM_STATE_CONTROL_REG_OFFSET), AS_PICAM_FRAME_DONE_MASK) ? AS_TRUE : AS_FALSE;
}
