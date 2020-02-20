/*--------------------------------------------------------------------------------
-- This file is part of V.E.A.R.S.
--
-- V.E.A.R.S. is free software: you can redistribute it and/or modify
-- it under the terms of the GNU Lesser General Public License as published by
-- the Free Software Foundation, either version 3 of the License, or
-- (at your option) any later version.
--
-- V.E.A.R.S. is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
-- GNU Lesser General Public License for more details.
--
-- You should have received a copy of the GNU Lesser General Public License
-- along with V.E.A.R.S. If not, see <http://www.gnu.org/licenses/lgpl.txt>.
--
-- Copyright (C) 2010-2019 Hochschule Augsburg, University of Applied Sciences
--                         and Stefan Durner
----------------------------------------------------------------------------------
-- File:           ch7301c_init.c
--
-- Company:        University of Applied Sciences, Augsburg, Germany
--
-- Author:         Michael Schaeferling, Stefan Durner
-- Date:           06/11/2010
--
-- Modified:       * 25/04/2014 by Michael Schaeferling
--                 * 12/09/2019 by Michael Schaeferling
--
-- Description:    Driver (source file) for the VEARS IP core.
--                 This file contains functions to configure a Chrontel CH7301C
--                 device to properly output video data provided by VEARS.
--------------------------------------------------------------------------------*/


#include "ch7301c_init.h"

#include <stdint.h>
#include <stdio.h>

#include <xparameters.h>
#include <xil_printf.h>


#ifdef XPAR_CH7301C_IIC_BASEADDR
#include "xiic_l.h"
#endif


/************************** Function Definitions ***************************/
// Configuration for Chrontel Video Device for RGB-Mode

#define DECODER_ADDRESS 0x76          // IIC-ADDRESS for Chrontel device
#define DECODER_COMP_CONFIG_CNT 6     // Count of values to write to Chrontel device


struct VideoModule {                  // Struct with adresses and values to send with IIC
  uint8_t addr;                       // Also includes the default values of the device,
  uint8_t config_val;                 // which are just used for Debug-Information
  uint8_t default_val;
};


void config_decoder_ch7301()
{
#ifdef XPAR_CH7301_IIC_BASEADDR

  struct VideoModule decoder[] = // Configuration as shown in Chrontel Datasheet
  {
    { 0x1C, 0x01, 0x00 },    // |R|R|R|R|R|MCP|R|XCM|                            XCLK_invert[2] and XCLKx2[0]
    { 0x1D, 0x47, 0x48 },    // |R|R|R|R|XCMD3|XCMD2|XCMD1|XCMD0|                Input Clock delay
    //{ 0x1F, 0x80, 0x80 },  // |R|DES|R|VSP|HSP|IDF2|IDF1|IDF0|                 MUX-Mode of RGB-Inputdata
    { 0x21, 0x09, 0x00 },    // |R|R|R|R|SYNC|DACG1|DACG0|DACBP|                 HS/VS-enable[3] and RGB-Bypass[0]
    //{ 0x23, 0x00, 0x00 },  // |R|R|R|R|R|HPDD|R|R|                             Hardware Hot Plug Detection
    //values below for <65MHz:
    { 0x33, 0x08, 0xE4 },    // |DVID2|DVID1|DVID0|DVII|TPPSD1|TPPSD0|R|TPCP0|   DVI PLL Charge Pump
    //{ 0x34, 0x16, 0x16 },  // |R|R|TPFFD1|TPFFD0|TPFBD3|TPFBD2|TPFBD1|TPFBD0|  DVI PLL Divider
    //{ 0x35, 0x30, 0x30 },  // |R|R|R|R|R|R|R|R|                                DVI PLL Suply
    { 0x36, 0x60, 0x00 },    // |TPLPF3|TPLPF2|TPLPF1|TPLPF1|TPLPF0|R|R|R|       DVI PLL FILTER
    //
    //{ 0x48, 0x18, 0x18 },  // |R|R|R|ResetIB|ResetDB|R|TSTP1|TSTP0|            Input or ...
    //{ 0x48, 0x19, 0x18 },  // |R|R|R|ResetIB|ResetDB|R|TSTP1|TSTP0|            ... Testpattern
    { 0x49, 0xC0, 0x01 }     // |DVIP|DVIL|R|R|DACPD2|DACPD1|DACPD0|FPD|         Powermanagement: unset FullPowerDown[0] and enable all other hardware
    //{ 0x56, 0x00, 0x00 }   // |R|R|TMSYO|R|R|R|R|T_RGB|                        Set Sync Polarity
  };



  uint8_t send_cnt, i;
  uint8_t send_data[2] = {0};
  uint8_t success = 1;
  send_cnt = 2;

  for( i = 0; i < DECODER_COMP_CONFIG_CNT; i++ )     // do all struct values
  {
    send_data[0] = decoder[i].addr;                  // Address to send
    send_data[1] = decoder[i].config_val;            // Value to send
    send_cnt = XIic_Send(XPAR_DVI_IIC_BASEADDR, DECODER_ADDRESS, send_data, 2, XIIC_STOP); // IIC-Sendroutine
    xil_printf(" %d\n\r",send_cnt);
    if( send_cnt != 2 )
    {
      success = 0;               // No success if not all two bytes have been sent
      break;
    }
  }

#else
  xil_printf("Cannot configure Chrontel CH7301 device, no CH7301_IIC module found in SoC.\n\r");

#endif
}
