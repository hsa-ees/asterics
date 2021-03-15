/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework and the VEARS core.
--  (C) 2020 Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Author:         Patrick Zacharias
--
----------------------------------------------------------------------------------
--  This program is free software: you can redistribute it and/or modify
--  it under the terms of the GNU Lesser General Public License as published by
--  the Free Software Foundation, either version 3 of the License, or
--  (at your option) any later version.
--
--  This program is distributed in the hope that it will be useful,
--  but WITHOUT ANY WARRANTY; without even the implied warranty of
--  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
--  GNU Lesser General Public License for more details.
--
--  You should have received a copy of the GNU Lesser General Public License
--  along with this program.  If not, see <http://www.gnu.org/licenses/>.
----------------------------------------------------------------------------------
--! @file       as_i2c_driver.c
--! @brief      Functions declarations for I2C part of linux driver.
--------------------------------------------------------------------------------*/

#pragma once 

#include <linux/i2c.h>
#include <linux/clk.h>
#include <linux/platform_device.h>
#include "as_iic.h"

struct asterics_i2c {
  struct i2c_adapter adapter;
  struct clk *clk;
};

int as_driver_i2c_probe(struct platform_device *pdev);
int as_driver_i2c_remove(struct platform_device *pdev);
