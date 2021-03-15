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
--! @brief      Functions definitions for I2C part of linux driver.
--------------------------------------------------------------------------------*/

#include "as_i2c_driver.h"

// Main transfer function
static int asterics_i2c_master_xfer(struct i2c_adapter *adap, struct i2c_msg *msgs, int num) { return -1; }

// Reports features supported by this bus
static u32 asterics_i2c_functionality(struct i2c_adapter *adap) { return I2C_FUNC_I2C; }

static const struct i2c_algorithm asterics_i2c_algo = {
    .master_xfer = asterics_i2c_master_xfer,
    .functionality = asterics_i2c_functionality,
};

int as_driver_i2c_probe(struct platform_device *pdev) {
  int ret = 0;
  struct asterics_i2c *priv_data = NULL;

  // Create driver data and set it for this platform device, lifetime managed by kernel
  priv_data = devm_kzalloc(&pdev->dev, sizeof(*priv_data), GFP_KERNEL);
  if (!priv_data)
    return -ENOMEM;

  platform_set_drvdata(pdev, priv_data);

  // Initialize adapter
  priv_data->adapter.owner = THIS_MODULE;

  priv_data->adapter.algo = &asterics_i2c_algo;
  priv_data->adapter.algo_data = priv_data;
  priv_data->adapter.retries = 5;
  priv_data->adapter.timeout = msecs_to_jiffies(1000);
  priv_data->adapter.dev.of_node = pdev->dev.of_node;
  priv_data->adapter.dev.parent = &pdev->dev;
  strlcpy(priv_data->adapter.name, "ASTERICS I2C", sizeof(priv_data->adapter.name));

  // TODO: Use clock to initialize clock speed
  priv_data->clk = devm_clk_get(&pdev->dev, NULL);

  ret = i2c_add_adapter(&priv_data->adapter);
  return ret;
}

int as_driver_i2c_remove(struct platform_device *pdev) {
  struct asterics_i2c *priv_data = platform_get_drvdata(pdev);

  i2c_del_adapter(&priv_data->adapter);

  return 0;
}
