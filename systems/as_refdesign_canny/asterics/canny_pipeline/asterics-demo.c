/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework.
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Author:         Michael Schäferling <michael.schaeferling@hs-augsburg.de>
--                 Gundolf Kiefer <gundolf.kiefer@hs-augsburg.de>
--                 Philip Manke <philip.manke@hs-augsburg.de>
--
-- Description:    Demo application for the ASTERICS Framework.
--                 To be used alongside the as_refdesign_canny_with_debug demo.
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
#include "xgpio.h"
#include "xparameters.h"

// libc...
#include <assert.h>
#include <stdio.h>

// ASTERICS...
#include "asterics.h"

// VEARS...
#include <vears.h>

#define FRAME_WIDTH 640
#define FRAME_HEIGHT 480
#define FRAME_SIZE (FRAME_WIDTH * FRAME_HEIGHT)

int main() {
  uint32_t *features;
  uint8_t *orig;
  XGpio gpio_btns, gpio_sws, gpio_leds;

  // Init platform (must be done first) ...
  init_platform();

  printf("Hello from ASTERICS!\n");

  // Init GPIOs ...
  XGpio_Initialize(&gpio_btns, XPAR_AXI_GPIO_0_DEVICE_ID);
  XGpio_SetDataDirection(&gpio_btns, 1, 0xFFFFFFFF);

  XGpio_Initialize(&gpio_sws, XPAR_AXI_GPIO_1_DEVICE_ID);
  XGpio_SetDataDirection(&gpio_sws, 1, 0xFFFFFFFF);

  XGpio_Initialize(&gpio_leds, XPAR_AXI_GPIO_2_DEVICE_ID);
  XGpio_SetDataDirection(&gpio_leds, 1, 0x0);

  as_reader_writer_reset(AS_MODULE_BASEADDR_WRITER0);
  as_reader_writer_reset(AS_MODULE_BASEADDR_WRITER_ORIG);

  // Allocate memory region for image data storage ...
  features = calloc(FRAME_SIZE, sizeof(uint32_t));
  orig = malloc(FRAME_SIZE * sizeof(uint8_t));

  AS_ASSERT(features != NULL);
  AS_ASSERT(orig != NULL);

  // Init VEARS ...
  XGpio_DiscreteWrite(&gpio_leds, 1, 0x01); // Set LED0: Starting VEARS
  vears_init(VEARS_BASEADDR, orig);
  vears_overlay_on(VEARS_BASEADDR);

  // Init ASTERICS ...
  // Set LED1: VEARS started, starting ASTERICS
  XGpio_DiscreteWrite(&gpio_leds, 1, 0x03);
  printf("ASTERICS:\n");
  printf(" * initializing modules:\n");

  //   1) Sensor_OV7670...
  printf("   - as_sensor_ov7670\n");
  as_sensor_ov7670_init(AS_MODULE_BASEADDR_CAM0, OV7670_XILINX_PL_IIC,
                        XPAR_AS_SENSOR_OV7670_0_IIC_0_BASEADDR);

  //   2) MemWriter #0 ...
  printf("   - as_reader_writer #0 (writer canny features)\n");
  as_reader_writer_init(AS_MODULE_BASEADDR_WRITER0, NULL);
  as_reader_writer_set_section_addr(AS_MODULE_BASEADDR_WRITER0,
                                    (uint32_t *)features);
  as_reader_writer_set_section_size(AS_MODULE_BASEADDR_WRITER0,
                                    FRAME_SIZE * sizeof(uint32_t));
  //   3) MemWriter #1
  printf("   - as_reader_writer #1 (writer orig image)\n");
  as_reader_writer_init(AS_MODULE_BASEADDR_WRITER_ORIG, NULL);
  as_reader_writer_set_section_addr(AS_MODULE_BASEADDR_WRITER_ORIG,
                                    (uint32_t *)orig);
  as_reader_writer_set_section_size(AS_MODULE_BASEADDR_WRITER_ORIG,
                                    FRAME_SIZE * sizeof(uint8_t));

  printf("   - as_canny\n");
  as_canny_pipe_reset(AS_MODULE_BASEADDR_AS_CANNY_PIPELINE);
  as_canny_pipe_set_thresholds(AS_MODULE_BASEADDR_AS_CANNY_PIPELINE, 0x08,
                               0x04);

  // Set LED2: ASTERICS started, starting main loop
  XGpio_DiscreteWrite(&gpio_leds, 1, 0x07);

  vears_image_show(VEARS_BASEADDR, orig);

  uint8_t switches = 0;
  uint8_t buttons = 0;
  uint8_t old_buttons;
  uint8_t old_switches;
  uint8_t count;
  uint8_t canny_thres_low;
  uint8_t canny_thres_high;
  uint8_t canny_feature_visualization;
  uint32_t feature_count;
  uint32_t fcount;
  uint32_t crt_unit_count =
      (uint32_t)as_writer_get_cur_unit_count(AS_MODULE_BASEADDR_WRITER0);
  canny_feature feature;
  uint32_t *feature_start;

  const uint8_t c_sw0 = 0x01;
  const uint8_t c_sw1 = 0x02;
  const uint8_t c_sw2 = 0x04;
  const uint8_t c_btn0 = 0x01;
  const uint8_t c_btn1 = 0x02;
  const uint8_t c_btn2 = 0x04;

  while (AS_TRUE) {
    old_switches = switches;
    old_buttons = buttons;
    switches = XGpio_DiscreteRead(&gpio_sws, 1);
    buttons = XGpio_DiscreteRead(&gpio_btns, 1);
    // button state change
    if (buttons != old_buttons) {
      if (buttons & c_btn0) {
        printf("Canny threshold set to [%x].\n\r",
               (canny_thres_low + (canny_thres_high << 8)));
        as_canny_pipe_set_thresholds(AS_MODULE_BASEADDR_AS_CANNY_PIPELINE,
                                     canny_thres_low, canny_thres_high);
      }
      canny_feature_visualization = (buttons & c_btn1);
      if (buttons & c_btn2) {
        vears_overlay_clear();
      }
    }
    // switch state change
    if (switches != old_switches) {
      if (switches & c_sw0) {
        vears_image_show(VEARS_BASEADDR, features);
      } else {
        vears_image_show(VEARS_BASEADDR, orig);
      }
      // Canny threshold select
      if ((switches & c_sw1) && (switches & c_sw2)) {
        canny_thres_low = 0x04;
        canny_thres_high = 0x08;
      } else {
        if (switches & c_sw2) {
          canny_thres_low = 0x08;
          canny_thres_high = 0x10;
        } else {
          if (switches & c_sw1) {
            canny_thres_low = 0x10;
            canny_thres_high = 0x20;
          } else {
            canny_thres_low = 0x20;
            canny_thres_high = 0x40;
          }
        }
      }
    }

    // Prepare MemWriter modules ...
    as_writer_set_enable(AS_MODULE_BASEADDR_WRITER0);
    as_reader_writer_set_go(AS_MODULE_BASEADDR_WRITER0);
    as_writer_set_enable(AS_MODULE_BASEADDR_WRITER_ORIG);
    as_reader_writer_set_go(AS_MODULE_BASEADDR_WRITER_ORIG);

    crt_unit_count =
        (uint32_t)as_writer_get_cur_unit_count(AS_MODULE_BASEADDR_WRITER0);
    feature_start =
        as_writer_get_last_data_unit_complete_addr(AS_MODULE_BASEADDR_WRITER0);

    // Trigger the camera and wait for the frame to be send...
    as_sensor_ov7670_run_once(AS_MODULE_BASEADDR_CAM0);
    while (!as_sensor_ov7670_frame_is_transmitted(AS_MODULE_BASEADDR_CAM0)) {
      ;
    }

    // Wait for pipeline to finish flushing
    as_canny_pipe_flush(AS_MODULE_BASEADDR_AS_CANNY_PIPELINE);
    count = 0;
    while (!(as_canny_pipe_is_ready(AS_MODULE_BASEADDR_AS_CANNY_PIPELINE))) {
      count++;
      if (count == 250) {
        printf("Timeout waiting for canny pipeline flush!\n\r");
        break;
      }
    }

    // Wait for MemWriter1 to write the original image to RAM ...
    count = 0;
    while (!as_reader_writer_is_done(AS_MODULE_BASEADDR_WRITER_ORIG)) {
      count++;
      as_sleep(500000);
      if (count == 250) {
        printf("Timeout waiting for the orig image writer!\n\r");
        break;
      }
    }
    as_writer_set_disable(AS_MODULE_BASEADDR_WRITER_ORIG);

    // Wait for MemWriter0 to write the canny features to RAM ...
    count = 0;
    while (crt_unit_count ==
           (uint32_t)as_writer_get_cur_unit_count(AS_MODULE_BASEADDR_WRITER0)) {
      count++;
      as_sleep(500000);
      if (count == 250) {
        printf("Timeout waiting for the canny feature writer!\n\r");
        break;
      }
    }
    as_writer_set_disable(AS_MODULE_BASEADDR_WRITER0);
    // Canny feature visualization mode
    if (canny_feature_visualization) {
      vears_overlay_clear();
      // Get the feature count
      feature_count =
          as_canny_pipe_get_feature_count(AS_MODULE_BASEADDR_AS_CANNY_PIPELINE);

      printf("Got %d features!\n\r", feature_count);
      // For all features
      for (fcount = 0; fcount < feature_count && fcount < FRAME_SIZE;
           fcount++) {
        // Decode the feature
        as_canny_pipe_decode_feature(feature_start, fcount, &feature);
        // Valid value guard
        if (feature.xcoordinate < FRAME_WIDTH &&
            feature.ycoordinate < FRAME_HEIGHT) {
          // Draw the feature at its coordinates
          vears_draw_pixel((uint32_t)feature.xcoordinate,
                           (uint32_t)feature.ycoordinate, 1);
        }
      }
    }

  } // main loop

  // We never get here!
  // However, it is good practice to clean up in the end.
  free(features);
  free(orig);
  cleanup_platform();
}
