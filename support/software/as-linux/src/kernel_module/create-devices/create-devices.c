/*--------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework and the VEARS core. 
--  Copyright (C) Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------------------
-- File:           create-devices.c
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Author:         Alexander Zoellner  
--
-- Description:    Program for creating devices for the ASTERICS device driver.
--                 Provide "-d" as single calling parameter for deleting all 
--                 devices. For creating, provide "-c".
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
----------------------------------------------------------------------------------*/

#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include "asterics.h"
#include "as_linux_kernel_if.h"


/* Fill the device parameters into the structure for the ioctl method of the as_control device */
void fill_as_ctrl_params (int cmd, char dev_name[20], int dev_type, uint32_t * dev_address, uint32_t address_range_size, 
                          uint32_t interface_width, uint8_t flags, as_ctrl_params_t* structure)
{
    structure->cmd = cmd;
    strcpy(structure->dev_name, dev_name);
    structure->dev_type = dev_type;
    structure->dev_address = dev_address;
    structure->address_range_size = address_range_size;
    structure->interface_width = interface_width;
    structure->flags = flags; 
}

int main(int argc, char *argv[]) {
  
    int i = 0;
    int as_devices;
    as_device_t * as_device_tree;
    as_ctrl_params_t tmp_param;
    
    /* Open the as_control device by using its device node (has exist at this point already) */
    as_control_fd = open("/dev/as_control", O_RDWR);
    if ((void*)as_control_fd == NULL) {
        perror("fopen()");
        printf("Cannot open /dev/as_control.\n");
        exit(1);
    }

    /* One calling parameter is expected (the first one is the program itself, therefore 2) */
    if(2 == argc) {
        /* Delete devices */
        if(!strcmp(argv[1], "-d")) {
            tmp_param.cmd = CMD_REMOVE_DEVICE;
            ioctl(as_control_fd, CALLED_FROM_USER, &tmp_param);
        }
        /* Create devices */
        else if (!strcmp(argv[1], "-c")) {
            /* Get list of devices from as_hardware.c */
            as_device_tree = get_devices();
            /* Get number of devices from as_hardware.c */
            as_devices = get_num_devices();

            /* Iterate the device list and create all devices */
            for(i=0; i<as_devices; i++) {
                fill_as_ctrl_params(CMD_CREATE_DEVICE, as_device_tree[i].dev_name, as_device_tree[i].dev_type, as_device_tree[i].dev_addr, as_device_tree[i].addr_range, 
                                as_device_tree[i].interface_width, as_device_tree[i].flags, &tmp_param);
                if (ioctl(as_control_fd, CALLED_FROM_USER, &tmp_param) != 0) {
                    printf("error creating %s\n", as_device_tree[i].dev_name);
                }
            }
        }
        else {
            printf("Unknown command line parameter");
        }
    }
    else {
        printf("Missing command line parameter");
    }

    close(as_control_fd);
    
    return 0;
}
