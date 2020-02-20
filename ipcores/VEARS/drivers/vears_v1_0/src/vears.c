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
-- File:           vears.c
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
-- Description:    Driver (source file) for the VEARS IP core.
--                 This driver contains API functions.
--------------------------------------------------------------------------------*/


#include "vears.h"

#include <xil_io.h>
#include <xil_cache.h>

#include <stdlib.h>

#include "embedded_augmenter_lib.h"





static vears_overlay_t *curOverlay = NULL, *internalOverlay = NULL;


#define ASSERT(COND) { if (!(COND)) { xil_printf ("ERROR in %s:%i: Assertion failed", __FILE__, __LINE__); abort (); } }

uint8_t vears_initialized = 0;

uint32_t vears_frame_width = 0;
uint32_t vears_frame_height = 0;






/************************ Helpers ********************************************/


static inline void flush_cache_for_image () {
  Xil_DCacheFlush ();
}


static inline void flush_cache_for_overlay () {

  // TBD: Test if the first line is sufficient.

  //~ Xil_DCacheFlushRange (ea_get_overlay_hardware_address (), sizeof (vears_overlay_t));
  Xil_DCacheFlush ();
}




/************************ Module Driver **************************************/


// Standard colors for overlay-picture after init
#define STD_COLOR_1	0xFF0000 //red
#define STD_COLOR_2	0x00FF00 //green
#define STD_COLOR_3	0x0000FF //blue


// Stored control register contents...
static uint32_t ctrlReg = 0;


int8_t vears_init(uint32_t vears_iobase, uint8_t *image_base) {
  uint32_t frame_width, frame_height;

  vears_reset (vears_iobase);

  if (!vears_get_resolution(vears_iobase, &frame_width, &frame_height)){
    vears_initialized = 0;
    return -1;
  } else {
    vears_frame_width = frame_width;
    vears_frame_height = frame_height;
    vears_initialized = 1;
  }

  if (!image_base) {
    return -1;
  } else {
    vears_image_show(vears_iobase, image_base);
    vears_enable (vears_iobase);
  }

  ea_init ();
  flush_cache_for_image ();

  return 0;
}


void vears_reset (uint32_t vears_iobase){
  Xil_Out32 (vears_iobase + VEARS_REG_CONTROL, 0);
  Xil_Out32 (vears_iobase + VEARS_REG_CONTROL, VEARS_CONTROL_REG_RESET_MASK);
  Xil_Out32 (vears_iobase + VEARS_REG_CONTROL, 0);
  ctrlReg = 0;
}


void vears_enable (uint32_t vears_iobase){
  if (vears_initialized){
    ctrlReg |= VEARS_CONTROL_REG_ENABLE_MASK;
    Xil_Out32 (vears_iobase + VEARS_REG_CONTROL, ctrlReg);
  }
}


void vears_disable (uint32_t vears_iobase){
  ctrlReg &= ~VEARS_CONTROL_REG_ENABLE_MASK;
  Xil_Out32 (vears_iobase + VEARS_REG_CONTROL, ctrlReg);
}


void vears_overlay_on (uint32_t vears_iobase){

  // Switch to (and create) internal overlay if non is set ...
  if (!curOverlay) {
    if (!internalOverlay) {
      internalOverlay = malloc (vears_frame_width * vears_frame_height / 4);
      ASSERT (internalOverlay != NULL);
      vears_overlay_drawto (internalOverlay);
      vears_overlay_clear ();
    }
    vears_overlay_show (vears_iobase, internalOverlay);
    vears_overlay_drawto (internalOverlay);
  }

  // Switch on the overlay...
  ctrlReg |= VEARS_CONTROL_REG_OVERLAY_ENABLE_MASK;
  Xil_Out32 (vears_iobase + VEARS_REG_CONTROL, ctrlReg);

  // Reset color map...
  vears_overlay_set_color(vears_iobase, 1, STD_COLOR_1);
  vears_overlay_set_color(vears_iobase, 2, STD_COLOR_2);
  vears_overlay_set_color(vears_iobase, 3, STD_COLOR_3);
}


void vears_overlay_off (uint32_t vears_iobase){
  ctrlReg &= ~VEARS_CONTROL_REG_OVERLAY_ENABLE_MASK;
  Xil_Out32 (vears_iobase + VEARS_REG_CONTROL, ctrlReg);
}


void vears_overlay_set_color (uint32_t vears_iobase, int col_idx, uint32_t color){
  if (col_idx == 1)
    //VEARS_write_reg_color0(vears_iobase, 0, color);
    Xil_Out32(vears_iobase + VEARS_REG_COLOR_1, color);

  else if (col_idx == 2)
    //VEARS_write_reg_color1(vears_iobase, 0, color);
    Xil_Out32(vears_iobase + VEARS_REG_COLOR_2, color);

  else if (col_idx == 3)
    //VEARS_write_reg_color2(vears_iobase, 0, color);
    Xil_Out32(vears_iobase + VEARS_REG_COLOR_3, color);
}


void vears_image_show (uint32_t vears_iobase, uint8_t *image_base){
  //VEARS_write_reg_pic_base_addr(vears_iobase, 0, image_base);
  Xil_Out32(vears_iobase + VEARS_REG_IMAGE_BASE, (uint32_t) image_base);
  flush_cache_for_image ();
}


void vears_overlay_show (uint32_t vears_iobase, vears_overlay_t *overlay){
  //VEARS_write_reg_ovl_base_addr(vears_iobase, 0, overlay);
  Xil_Out32(vears_iobase + VEARS_REG_OVERLAY_BASE, (uint32_t) overlay);
}


int8_t vears_get_resolution (uint32_t vears_iobase, uint32_t *screen_width, uint32_t *screen_height){
  // read status register
  uint32_t reg_status = Xil_In32(vears_iobase + VEARS_REG_STATUS);
  uint8_t video_group = (uint8_t)(reg_status);
  uint8_t video_mode  = (uint8_t)(reg_status>>8);

  if ( ( video_group != 0 ) && ( video_mode != 0 ) ) {
    *screen_width = video_settings_group_mode_array[video_group-1][video_mode-1].H_Tdisp;
    *screen_height = video_settings_group_mode_array[video_group-1][video_mode-1].V_Tdisp;
    return 1;
  } else {
    *screen_width = 0;
    *screen_height = 0;
    return -1;
  }
}


int8_t vears_is_color (uint32_t vears_iobase){
  // read status register
  uint32_t reg_status = Xil_In32(vears_iobase + VEARS_REG_STATUS);
  uint8_t is_color = (uint8_t)((reg_status >> 16) & 0x1);
  return is_color;
}


void vears_interrupt_frame_enable (uint32_t vears_iobase){
  ctrlReg |= VEARS_CONTROL_REG_INTR_FRAME_EN_MASK;
  Xil_Out32 (vears_iobase + VEARS_REG_CONTROL, ctrlReg);
}

void vears_interrupt_frame_disable (uint32_t vears_iobase){
  ctrlReg &= ~VEARS_CONTROL_REG_INTR_FRAME_EN_MASK;
  Xil_Out32 (vears_iobase + VEARS_REG_CONTROL, ctrlReg);
}


void vears_interrupt_line_enable (uint32_t vears_iobase){
  ctrlReg |= VEARS_CONTROL_REG_INTR_LINE_EN_MASK;
  Xil_Out32 (vears_iobase + VEARS_REG_CONTROL, ctrlReg);
}

void vears_interrupt_line_disable (uint32_t vears_iobase){
  ctrlReg &= ~VEARS_CONTROL_REG_INTR_LINE_EN_MASK;
  Xil_Out32 (vears_iobase + VEARS_REG_CONTROL, ctrlReg);
}


/************************ Overlay functions ***********************************/


void vears_overlay_drawto (vears_overlay_t *overlay) {
  ea_set_overlay_software_address ((uint32_t*) overlay);
}


void vears_overlay_clear () {
  ea_erase ();
  flush_cache_for_overlay ();
}


void vears_set_clipping (uint32_t x0, uint32_t y0, uint32_t x1, uint32_t y1) {

  // Sanitize parameters (the EA lib fails completely if out of range)...
  //if (x0 < 0) x0 = 0;
  if (x1 > vears_frame_width - 1) x1 = vears_frame_width - 1;
  //if (y0 < 0) y0 = 0;
  if (y1 > vears_frame_height - 1) y1 = vears_frame_height - 1;

  // Go ahead...
  ea_set_clipped_area (x0, y0, x1, y1);
}


void vears_draw_pixel (uint32_t x, uint32_t y, uint32_t color) {
  ea_draw_point (x, y, color);
  flush_cache_for_overlay ();
}


void vears_draw_line (uint32_t x0, uint32_t y0, uint32_t x1, uint32_t y1, uint32_t color) {
  ea_draw_line (x0, y0, x1, y1, color);
  flush_cache_for_overlay ();
}


void vears_draw_circle (uint32_t x, uint32_t y, uint32_t r, uint32_t color) {
  ea_draw_circle (x, y, r, color);
  flush_cache_for_overlay ();
}


void vears_draw_filled_circle (uint32_t x, uint32_t y, uint32_t r, uint32_t color) {
  ea_draw_filled_circle (x, y, r, color);
  flush_cache_for_overlay ();
}


void vears_draw_rectangle (uint32_t x0, uint32_t y0, uint32_t x1, uint32_t y1, uint32_t color) {
  ea_draw_rectangle (x0, y0, x1, y1, color);
  flush_cache_for_overlay ();
}


void vears_draw_filled_rectangle (uint32_t x0, uint32_t y0, uint32_t x1, uint32_t y1, uint32_t color) {
  ea_draw_filled_rectangle (x0, y0, x1, y1, color);
  flush_cache_for_overlay ();
}


void vears_draw_string (uint32_t x, uint32_t y, uint32_t color, const char *str, enum vears_font_e font, int32_t charSpace) {
  ea_draw_string ((uint8_t*) str, strlen (str), x, y, color, font == fnt_tit ? &tit_glyph : &std_glyph, charSpace);
  flush_cache_for_overlay ();
}


int vears_string_get_width (const char *str, enum vears_font_e font, int32_t charSpace) {
  struct glyphs *fnt = font == fnt_tit ? &tit_glyph : &std_glyph;
  int len = strlen (str);
  return len * fnt->c_width + (len-1) * charSpace;
}


int vears_string_get_height (enum vears_font_e font) {
  struct glyphs *fnt = font == fnt_tit ? &tit_glyph : &std_glyph;
  return fnt->c_height;
}


void vears_draw_icon (uint32_t x, uint32_t y, uint32_t color, const char *icon, uint32_t w, uint32_t h) {
  const char *p;
  char c;
  uint32_t dx, dy;

  p = icon;
  for (dy = 0; dy < h; dy++) {
    for (dx = 0; dx < w; dx++) {
      switch ( (c = (*p++)) ) {
        case ' ':
        case '.':
          break;
        case '+':
          ea_draw_point (x + dx, y + dy, (1 << COLOR_DEPTH) - 1);
          break;
        case '0':
        case '1':
        case '2':
          ea_draw_point (x + dx, y + dy, c - '0');
          break;
        default:
          ea_draw_point (x + dx, y + dy, color);
      }
    }
  }
  flush_cache_for_overlay ();
}
