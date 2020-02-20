/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework. 
--  Copyright (C) Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Author:         Michael Schäferling <michael.schaeferling@hs-augsburg.de>
--                 Gundolf Kiefer <gundolf.kiefer@hs-augsburg.de>
--
-- Description:    Demo application for the ASTERICS Framework.
--                 To be used alongside the as_refdesign_zynq image differencing demo.
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
----------------------------------------------------------------------------------
--! @file  asterics-demo.c
--! @brief Demo application for the ASTERICS Framework.
--------------------------------------------------------------------------------*/


/*
 * This application configures UART 16550 to baud rate 9600.
 * PS7 UART (Zynq) is not initialized by this application, since
 * bootrom/bsp configures it to baud rate 115200
 *
 * ------------------------------------------------
 * | UART TYPE   BAUD RATE                        |
 * ------------------------------------------------
 *   uartns550   9600
 *   uartlite    Configurable only in HW design
 *   ps7_uart    115200 (configured by bootrom/bsp)
 */

// Platform / BSP...
#include "platform.h"
#include "xparameters.h"
#include "xgpio.h"

// libc...
#include <stdio.h>
#include <assert.h>

// ASTERICS...
#include "asterics.h"

// VEARS...
#include <vears.h>


#define FRAME_WIDTH 640
#define FRAME_HEIGHT 480
#define FRAME_SIZE (FRAME_WIDTH*FRAME_HEIGHT)


int main() {
  uint8_t *delay_buf;
  uint8_t *diff_image;
  XGpio gpio_btns, gpio_sws, gpio_leds;

  // Init platform (must be done first) ...
  init_platform();

  printf("Hello from ASTERICS!\n");

  // Init GPIOs ...
  XGpio_Initialize (&gpio_btns, XPAR_AXI_GPIO_0_DEVICE_ID);
  XGpio_SetDataDirection (&gpio_btns, 1, 0xFFFFFFFF);

  XGpio_Initialize (&gpio_sws, XPAR_AXI_GPIO_1_DEVICE_ID);
  XGpio_SetDataDirection (&gpio_sws, 1, 0xFFFFFFFF);

  XGpio_Initialize (&gpio_leds, XPAR_AXI_GPIO_2_DEVICE_ID);
  XGpio_SetDataDirection (&gpio_leds, 1, 0x0);

  as_reader_writer_reset(AS_MODULE_BASEADDR_WRITER0);
  as_reader_writer_reset(AS_MODULE_BASEADDR_WRITER1);
  as_reader_writer_reset(AS_MODULE_BASEADDR_AS_MEMREADER_0);

  // Allocate memory region for image data storage ...
  delay_buf = malloc (FRAME_SIZE);   // 8 Bit per Pixel -> 300kB
  diff_image = malloc (FRAME_SIZE);   // 8 Bit per Pixel -> 300kB

  ASSERT (delay_buf != NULL);
  ASSERT (diff_image != NULL);

  // Init VEARS ...
  XGpio_DiscreteWrite (&gpio_leds, 1, 0x01);    // Set LED0: Starting VEARS
  printf("VEARS: img=0x%08x (@%luK)\n", (uint32_t) diff_image, ((uint32_t) diff_image) / 1024);
  vears_init (VEARS_BASEADDR, delay_buf);
  vears_overlay_on (VEARS_BASEADDR);  /* We may move this down to hide the drawing process */

  // Init ASTERICS ...
  XGpio_DiscreteWrite (&gpio_leds, 1, 0x03);    // Set LED1: VEARS started, starting ASTERICS
  printf ("ASTERICS:\n");
  printf (" * initializing modules:\n");

  //   1) Sensor_OV7670...
  printf ("   - as_sensor_ov7670\n");
  as_sensor_ov7670_init (AS_MODULE_BASEADDR_AS_SENSOR_OV7670_0);

  //   2) MemWriter #0 ...
  printf ("   - as_reader_writer #0 (writer0)\n");
  as_reader_writer_init (AS_MODULE_BASEADDR_WRITER0, NULL);
  as_reader_writer_set_section_addr (AS_MODULE_BASEADDR_WRITER0, (uint32_t *) diff_image);
  as_reader_writer_set_section_size (AS_MODULE_BASEADDR_WRITER0, FRAME_SIZE * sizeof (uint8_t));

  //   3) MemWriter #1 ...
  printf ("   - as_reader_writer #1 (writer1)\n");
  as_reader_writer_init (AS_MODULE_BASEADDR_WRITER1, NULL);
  as_reader_writer_set_section_addr (AS_MODULE_BASEADDR_WRITER1, (uint32_t *) delay_buf);
  as_reader_writer_set_section_size (AS_MODULE_BASEADDR_WRITER1, FRAME_SIZE * sizeof (uint8_t));

  //   4) MemReader #0 ...
  printf ("   - as_reader_writer #3 (reader0)\n");
  as_reader_writer_init (AS_MODULE_BASEADDR_AS_MEMREADER_0, NULL);
  as_reader_writer_set_section_addr (AS_MODULE_BASEADDR_AS_MEMREADER_0, (uint32_t *) delay_buf);
  as_reader_writer_set_section_size (AS_MODULE_BASEADDR_AS_MEMREADER_0, FRAME_SIZE * sizeof (uint8_t));


  XGpio_DiscreteWrite (&gpio_leds, 1, 0x07);    // Set LED2: ASTERICS started, starting main loop


  vears_image_show (VEARS_BASEADDR, delay_buf);
  // Main loop...
  printf ("Entering main loop.\n");
  uint8_t switches = 0;
  uint8_t old_switches;
  uint8_t sw_0;

  while (AS_TRUE) {
	old_switches = switches;
	switches = XGpio_DiscreteRead (&gpio_sws, 1);

	if(switches != old_switches){
		sw_0 = switches & (1 << 0);
		
		if (sw_0) {
			vears_image_show(VEARS_BASEADDR, diff_image);
			printf("Showing image differences.\n");
		}
		else{
			vears_image_show(VEARS_BASEADDR, delay_buf);
			printf("Showing delay (original) image.\n");
		}
	}

    // Prepare MemWriter modules ...
    as_writer_set_enable (AS_MODULE_BASEADDR_WRITER0);
    as_reader_writer_set_go (AS_MODULE_BASEADDR_WRITER0);
    as_writer_set_enable (AS_MODULE_BASEADDR_WRITER1);
    as_reader_writer_set_go (AS_MODULE_BASEADDR_WRITER1);

    // Trigger MemReader
    as_reader_writer_set_go(AS_MODULE_BASEADDR_AS_MEMREADER_0);

    // Trigger the camera ...
    as_sensor_ov7670_run_once (AS_MODULE_BASEADDR_AS_SENSOR_OV7670_0);

    // Wait for chain MemReader to read the image from RAM ...
    while (!as_reader_writer_is_done (AS_MODULE_BASEADDR_AS_MEMREADER_0)) {}

    // Wait for chain MemWriter to write the image to RAM ...
    while (!as_reader_writer_is_done (AS_MODULE_BASEADDR_WRITER1)) {}
    as_writer_set_disable (AS_MODULE_BASEADDR_WRITER1);

    // Wait for chain MemWriter to write the image to RAM ...
    while (!as_reader_writer_is_done (AS_MODULE_BASEADDR_WRITER0)) {}
    as_writer_set_disable (AS_MODULE_BASEADDR_WRITER0);

  } // main loop

  // We never get here!
  //   However, it is good practice to clean up in the end.
  free(diff_image);
  free(delay_buf);

  cleanup_platform();
}
