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
-- Copyright (C) 2011-2019 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- File:           vears.h
--
-- Company:        University of Applied Sciences, Augsburg, Germany
--
-- Author:         Andreas Becher, Michael Schaeferling, Gundolf Kiefer
-- Date:           05/06/2011
--
-- Modified:       * 24/08/2018 by Gundolf Kiefer
--                 * 04/06/2019 by Michael Schaeferling
--                 * 08/07/2019 by Michael Schaeferling
--
-- Description:    Driver (header file) for the VEARS IP core.
--                 This driver contains API functions.
--------------------------------------------------------------------------------*/


/**
 * @file  vears.h
 * @brief VEARS API for hardware configuration.
 */

#ifndef VEARS_H
#define VEARS_H

#include "vears_baseaddr.h"

#include <stdint.h>




/** @defgroup vears VEARS software driver and library.
 * @{
 */





/************************ I/O Registers **************************************/


/** @defgroup vears_slaveregs VEARS I/O Registers
 *  @{
 */


#define VEARS_WORD_BYTES 4


/* Internal register definitions */
#define VEARS_REG_CONTROL      0 * VEARS_WORD_BYTES
#define VEARS_REG_STATUS       1 * VEARS_WORD_BYTES
#define VEARS_REG_IMAGE_BASE   2 * VEARS_WORD_BYTES
#define VEARS_REG_OVERLAY_BASE 3 * VEARS_WORD_BYTES
#define VEARS_REG_COLOR_1      4 * VEARS_WORD_BYTES
#define VEARS_REG_COLOR_2      5 * VEARS_WORD_BYTES
#define VEARS_REG_COLOR_3      6 * VEARS_WORD_BYTES


/* Bit offsets */
#define VEARS_CONTROL_REG_RESET_BIT           0
#define VEARS_CONTROL_REG_ENABLE_BIT          1
#define VEARS_CONTROL_REG_OVERLAY_ENABLE_BIT  2
#define VEARS_CONTROL_REG_INTR_FRAME_EN_BIT   6
#define VEARS_CONTROL_REG_INTR_LINE_EN_BIT    7


/* Bit masks */
#define VEARS_CONTROL_REG_RESET_MASK          (1<<VEARS_CONTROL_REG_RESET_BIT)
#define VEARS_CONTROL_REG_ENABLE_MASK         (1<<VEARS_CONTROL_REG_ENABLE_BIT)
#define VEARS_CONTROL_REG_OVERLAY_ENABLE_MASK (1<<VEARS_CONTROL_REG_OVERLAY_ENABLE_BIT)
#define VEARS_CONTROL_REG_INTR_FRAME_EN_MASK  (1<<VEARS_CONTROL_REG_INTR_FRAME_EN_BIT)
#define VEARS_CONTROL_REG_INTR_LINE_EN_MASK   (1<<VEARS_CONTROL_REG_INTR_LINE_EN_BIT)

/** @} */



/** @defgroup vears_videomodes VEARS Video Modes
 *  @{
 */

typedef struct {
  uint8_t vid_group_id;
  uint8_t vid_mode_id;
  float Pixel_Clock;
  uint32_t H_Tpw;
  uint32_t H_Tbp;
  uint32_t H_Tdisp;
  uint32_t H_Tfp;
  uint8_t H_SP;
  uint32_t V_Tpw;
  uint32_t V_Tbp;
  uint32_t V_Tdisp;
  uint32_t V_Tfp;
  uint8_t V_SP;
} video_settings_t;

static const video_settings_t video_settings_group_mode_array[2][35] = {
  /* Video Group ID 1 (CEA) */
  /* Mode 4: 1280x720 @ 60Hz/45kHz (@74.250MHz PixClk) */
  [0][3]  = { 0x01, 0x04, 74.250, 40, 220, 1280, 110, 1, 5, 20, 720, 5, 1 },
  /* Mode 32: 1920x1080 @ 24Hz/26.8kHz (@74.250MHz PixClk) */
  [0][31] = { 0x01, 0x20, 74.250, 44, 148, 1920, 638, 1, 5, 36, 1080, 4, 1 },
  /* Mode 33: 1920x1080 @ 25Hz/27.9kHz (@74.250MHz PixClk) */
  [0][32] = { 0x01, 0x21, 74.250, 44, 148, 1920, 528, 1, 5, 36, 1080, 4, 1 },
  /* Mode 34: 1920x1080 @ 30Hz/33.5kHz (@74.250MHz PixClk) */
  [0][33] = { 0x01, 0x22, 74.250, 44, 148, 1920, 88,  1, 5, 36, 1080, 4, 1 },
  
  /* Video Group ID 2 (DMT) */
  /* Mode 4: 640x480   @ 60Hz/31.5kHz (@25.175MHz PixClk) / Industry Standard */
  [1][3]  = { 0x02, 0x04, 25.175, 96, 48 , 640 , 16, 0, 2, 33, 480 , 10, 0 },
  /* Mode 8: 800x600   @ 56Hz/35.2kHz (@36MHz PixClk)     / VESA#900601 */
  [1][7]  = { 0x02, 0x08, 36.0 , 72 , 128, 800 , 24, 1, 2, 22, 600 , 1 , 1 },
  /* Mode 10: 800x600   @ 72Hz/48.1kHz (@50MHz PixClk)     / VESA#900603A */
  [1][9]  = { 0x02, 0x0A, 50.0 , 120, 64 , 800 , 56, 1, 6, 23, 600 , 37, 1 },
  /* Mode 16: 1024x768  @ 60Hz/48.4kHz (@65MHz PixClk)     / VESA#901101A */
  [1][15] = { 0x02, 0x10, 65.0 , 136, 160, 1024, 24, 0, 6, 29, 768 , 3 , 0 },
  /* Mode 35: 1280x1024 @ 60Hz/64kHz   (@108MHz PixClk)    / VESA#VDMTREV */
  [1][34] = { 0x02, 0x23, 108.0, 112, 248, 1280, 48, 1, 3, 38, 1024, 1 , 1 }
};

/** @} */




/************************ Driver functions ***********************************/


/** @defgroup vears_driver VEARS hardware driver
 *  @{
 */


typedef uint8_t vears_overlay_t[];


/**
 * @brief Initialize and reset the VEARS module.
 *
 * Must be executed before doing anything else with VEARS!
 *
 * Unless 'image_base' is 'NULL', the core will be enabled as well.
 *
 * @param vears_iobase        I/O address of the VEARS module
 * @param image_base          Base address of the (main) image data
 * @return int                0 on success, -1 on failure
 */
int8_t vears_init (uint32_t vears_iobase, uint8_t *image_base);


/**
 * @brief Reset the VEARS module.
 *
 * @param vears_iobase        I/O address of the VEARS module
 */
void vears_reset (uint32_t vears_iobase);


/**
 * @brief Enable the VEARS module, if it was previously disabled.
 *
 * @param vears_iobase        I/O address of the VEARS module
 */
void vears_enable (uint32_t vears_iobase);


/**
 * @brief Disable the VEARS module.
 *
 * @param vears_iobase        I/O address of the VEARS module
 */
void vears_disable (uint32_t vears_iobase);


/**
 * @brief Enable the VEARS modules overlay operation.
 *
 * @param vears_iobase        I/O address of the VEARS module
 */
void vears_overlay_on (uint32_t vears_iobase);


/**
 * @brief Disable the VEARS modules overlay operation.
 *
 * @param vears_iobase        I/O address of the VEARS module
 */
void vears_overlay_off (uint32_t vears_iobase);


/**
 * @brief Set entry of the overlay color map.
 *
 * @param vears_iobase        I/O address of the VEARS module
 * @param col_idx             Color index (1..3)
 * @param color               Color in 0xrrggbb format
 *
 * If no color is set, the default colors are:
 * - 1: red
 * - 2: green
 * - 3: blue
 *
 * **Note:** This call has no effect if the VEARS module is not enabled.
 */
void vears_overlay_set_color (uint32_t vears_iobase, int col_idx, uint32_t color);


/**
 * @brief Set the main image data base address.
 *
 * @param vears_iobase        I/O address of the VEARS module
 * @param image_base          Memory address of the image data
 */
void vears_image_show (uint32_t vears_iobase, uint8_t *image_base);


/**
 * @brief Set the overlay base address.
 *
 * Setting a custom overlay allows to use multiple buffers for fast animations
 * or to render with double buffering.
 *
 * @param vears_iobase        I/O address of the VEARS module
 * @param overlay             Memory address of the overlay data
 */
void vears_overlay_show (uint32_t vears_iobase, vears_overlay_t *overlay);


/**
 * @brief Get the VEARS modules screen resolution.
 *
 * @param vears_iobase        I/O address of the VEARS module
 * @param screen_width        Reference to screen_width
 * @param screen_height       Reference to screen_height
 * @return int                0 on success, -1 on failure
 */
int8_t vears_get_resolution (uint32_t vears_iobase, uint32_t *screen_width, uint32_t *screen_height);


/**
 * @brief Get the VEARS modules color mode.
 *
 * @param vears_iobase        I/O address of the VEARS module
 * @return int                0 for grayscale mode (no color), 1 for color mode
 */
int8_t vears_is_color (uint32_t vears_iobase);


/**
* @brief Enable the VEARS modules frame interrupt output.
 *
 * @param vears_iobase        I/O address of the VEARS module
 */
void vears_interrupt_frame_enable (uint32_t vears_iobase);

/**
 * @brief Disable the VEARS modules frame interrupt output.
 *
 * @param vears_iobase        I/O address of the VEARS module
 */
void vears_interrupt_frame_disable (uint32_t vears_iobase);


/**
* @brief Enable the VEARS modules line interrupt output.
 *
 * @param vears_iobase        I/O address of the VEARS module
 */
void vears_interrupt_line_enable (uint32_t vears_iobase);

/**
* @brief Disable the VEARS modules line interrupt output.
 *
 * @param vears_iobase        I/O address of the VEARS module
 */
void vears_interrupt_line_disable (uint32_t vears_iobase);


/** @}*/  /* @defgroup vears_driver */





/************************ Overlay functions ***********************************/


/** @defgroup vears_overlay VEARS overlay drawing functions.
 *  @{
 */


/** @brief Set the current target overlay for subsequent drawing.
 *
 * Setting a custom overlay allows to use multiple buffers for fast animations
 * or to render with double buffering. This function allows to draw to a background
 * buffer while another buffer is still shown.
 */
void vears_overlay_drawto (vears_overlay_t *overlay);


/** @brief Clear the current draw overlay.
 */
void vears_overlay_clear ();
//~ ea_bool ea_erase (void);


/** @brief Set clipping rectangle.
 * (x0, y0) is the upper-left and (x1, y1) is the lower-right corner of the clipping
 * area, respectively. In subsequent drawing operations, only those pixels inside
 * the clipping rectangle are modified.
 */
void vears_set_clipping (uint32_t x0, uint32_t y0, uint32_t x1, uint32_t y1);


/** @brief Draw a single pixel.
 * 'color' is an index to the color table (0, 1, 2). A value of 3 means "transparent".
 */
void vears_draw_pixel (uint32_t x, uint32_t y, uint32_t color);


/** @brief Draw a line from (x0, y0) to (x1, y1).
 */
void vears_draw_line (uint32_t x0, uint32_t y0, uint32_t x1, uint32_t y1, uint32_t color);


/** @brief Draw a circle of radius r around (x, y).
 */
void vears_draw_circle (uint32_t x, uint32_t y, uint32_t r, uint32_t color);


/** @brief Draw a filled circle of radius r around (x, y).
 */
void vears_draw_filled_circle (uint32_t x, uint32_t y, uint32_t r, uint32_t color);


/** @brief Draw a rectangle.
 * (x0, y0) is the upper-left, (x1, y1) is the lower-right corner, respectively.
 */
void vears_draw_rectangle (uint32_t x0, uint32_t y0, uint32_t x1, uint32_t y1, uint32_t color);


/** @brief Draw a filled rectangle.
 * (x0, y0) is the upper-left, (x1, y1) is the lower-right corner, respectively.
 */
void vears_draw_filled_rectangle (uint32_t x0, uint32_t y0, uint32_t x1, uint32_t y1, uint32_t color);


/** @brief Font identifier for vears_draw_string(). */
enum vears_font_e {
  fnt_std = 0,  /**< Standard font */
  fnt_tit       /**< Title font */
};


/** @brief Draw a text string.
 * @param x is the target position's x coordinate (upper left corner).
 * @param y is the target position's y coordinate (lower right corner).
 * @param color is the color.
 * @param str is the string.
 * @param font is the selected font.
 * @param charSpace is extra space in pixels between characters (use 0 if unsure; may also be <0 for narrow text).
 */
void vears_draw_string (uint32_t x, uint32_t y, uint32_t color, const char *str, enum vears_font_e font, int32_t charSpace);


/** @brief Get the width of a text string in pixels.
 */
int vears_string_get_width (const char *str, enum vears_font_e font, int32_t charSpace);


/** @brief Get the height of a text string in pixels.
 */
int vears_string_get_height (enum vears_font_e font);


/** @brief Draw an icon (sprite) which is defined in a two dimensional char array (experimental!).
 *
 * @param x is the target position's x coordinate.
 * @param y is the target position's y coordinate.
 * @param color is the color of pixels marked with '*'.
 * @param icon is the definition of the icon. This is a character array with 'w' * 'h' characters,
 *   where 'h' subsequent characters define a row of the sprite. The characters are interpreted as
 *   follows:
 *
 *   - ' ' or '.': Background (pixel is left unchanged)
 *   - '+':        Transparent (pixel is set to transparency)
 *   - '0'...'2':  Mapped color (pixel is set to color #0, #1, or #2, respectively)
 *   - '*' or any other character: Pixel is set to 'color'
 *
 * @param w is the width of the icon.
 * @param h is the height of the icon.
 */
void vears_draw_icon (uint32_t x, uint32_t y, uint32_t color, const char *icon, uint32_t w, uint32_t h);



/** @}*/  /* @defgroup vears_overlay */







/**  * @}  */  /* @defgroup vears */


#endif /** VEARS_H */
