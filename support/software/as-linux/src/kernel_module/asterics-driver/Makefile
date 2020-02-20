#/*--------------------------------------------------------------------------------
#--  This file is part of the ASTERICS Framework. 
#--  Copyright (C) Hochschule Augsburg, University of Applied Sciences
#----------------------------------------------------------------------------------
#-- File:           Makefile
#--
#-- Company:        University of Applied Sciences, Augsburg, Germany
#-- Author:         Alexander Zoellner
#--
#-- Modified:       
#--
#-- Description:    Makefile for ASTERICS Linux Driver Kernel Module. The Xilinx 
#--                 environment has to be sourced first for the Makefile to work.
#--                 
#----------------------------------------------------------------------------------
#--  This program is free software: you can redistribute it and/or modify
#--  it under the terms of the GNU Lesser General Public License as published by
#--  the Free Software Foundation, either version 3 of the License, or
#--  (at your option) any later version.
#--
#--  This program is distributed in the hope that it will be useful,
#--  but WITHOUT ANY WARRANTY; without even the implied warranty of
#--  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#--  GNU Lesser General Public License for more details.
#--
#--  You should have received a copy of the GNU Lesser General Public License
#--  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#----------------------------------------------------------------------------------
#--! @file		Makefile
#--! @brief 	Builds the ASTERICS linux kernel module.
#--------------------------------------------------------------------------------*/


ifneq ($(KERNELRELEASE),)



# Makefile has been called from the kernel build system...

EXTRA_CFLAGS := -I$(src)/build
obj-m := asterics.o
asterics-objs := build/as_driver.o build/as_support.o build/as_memio.o build/as_reader_writer.o  build/as_iic.o



else

### Makefile has been called directly...

# Path to module sources (usually the source directory of a system)
# Here, the relative path within the ASTERICS installation directory is shown for compiling the kernel 
# within ASTERICS. Edit this path for your own project. 
SOURCE_DIR = ../../../../../

# Path to ASTERICS Support Library (ASL) and platform/environment (config.)
# Edit this path for your own project.
ASP_DIR = ./


### Use either cross or native compiling option. Comment out the other one ###

### Settings for cross compiling (Xilinx) on host system

#export ARCH=arm
#export CROSS_COMPILE=arm-linux-gnueabihf-
#CC=$(CROSS_COMPILE)gcc

# Path to kernel headers provided by Xilinx (change if necessary); See also "README"
# Edit this path for your own project.
#KDIR    := /home/eeslabor/EdS2-Praktikum/zybo/sw/linux-xlnx


### Settings for compiling on embedded platform

# Path to kernel headers on target platform
KDIR	:= /lib/modules/$(shell uname -r)



### Copy sources and build kernel module ###

PWD 	:= $(shell pwd)

# Copy all required files into temporary directory and build kernel module
default:
	mkdir -p build
	cp as_driver.[hc] build/
	cp $(ASP_DIR)as_config.h build/
	cp as_linux_kernel_if.h build/
	cp $(SOURCE_DIR)support/software/as_support.[hc] build/
	cp $(SOURCE_DIR)modules/as_memio/software/driver/as_memio.[hc] build/
	cp $(SOURCE_DIR)modules/as_reader_writer/software/driver/as_reader_writer.[hc] build/
	cp $(SOURCE_DIR)modules/as_iic/software/driver/as_iic.[hc] build/

	$(MAKE) -C $(KDIR) SUBDIRS=$(PWD) modules

	rm -fr build

clean:
	rm -fr build
	rm -fr *.o
	rm -fr *.ko
	rm -fr *.mod.c
	rm -fr *.order
	rm -fr *.symvers
	rm -fr .asterics.*
	rm -fr .tmp_versions
	rm -fr .as_driver.*
	rm -fr .asterics*
	rm -fr .tmp_versions
	rm -fr .as_driver*


endif

