##--------------------------------------------------------------------
## This file is part of the ASTERICS Framework.
## Copyright (C) Hochschule Augsburg, University of Applied Sciences
##--------------------------------------------------------------------
## File:     image_sensor_ov7670.xdc
##
## Company:  Efficient Embedded Systems Group
##           University of Applied Sciences, Augsburg, Germany
##           http://ees.hs-augsburg.de
##
## Author:   Gundolf Kiefer <gundolf.kiefer@hs-augsburg.de>
## Date:     
## Modified: 
##
## Description:
## Platform and OS configuration of an ASTERICS chain
##
##--------------------------------------------------------------------
##  This program is free software; you can redistribute it and/or
##  modify it under the terms of the GNU Lesser General Public
##  License as published by the Free Software Foundation; either
##  version 3 of the License, or (at your option) any later version.
##  
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
##  Lesser General Public License for more details.
##  
##  You should have received a copy of the GNU Lesser General Public License
##  along with this program; if not, see <http://www.gnu.org/licenses/>
##  or write to the Free Software Foundation, Inc.,
##  51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
##--------------------------------------------------------------------

# -----8<-----

# This is a manually created example for a 'config.mk' file.
# In the future, this file will be auto-generated.
# This file is auto-generated - do not edit by hand!



# Platform settings...

# General properties...
AS_BIG_ENDIAN_HW := 0			# endianess of hardware modules; 0 = little endian, 1 = big endian
AS_BIG_ENDIAN_SW := 0			# endianess of software modules; 0 = little endian, 1 = big endian (TBD: autogenerate this in 'Asterics.mk' based on 'AS_OS_*')

# FPGA device platform ... (exactly one of the following must be '1')
AS_BSP_DUMMY := 1			# We have no BSP (used for test compilations)
AS_BSP_XILINX := 0		# We have a Xilinx board support package (BSP)
AS_BSP_ALTERA := 0		# We have an Altera BSP



# OS Settings...

# General properties...
AS_WITH_MULTIPROCESSING := 0
  # Enable the use of thread synchronization mechanisms for multi-processing
  # environments.
  # Set this to 1 if the OS supports multi-processing and the ASTERICS
  # software may run in different threads. If the complete ASTERICS-related
  # software is running in the same thread, this flag can be set to 0.
  # (TBD: auto-generate this in 'Asterics.mk' based on 'AS_OS_*'?)

  # NOTE: AS_WITH_MULTIPROCESSING == 1 is presently not supported by all modules.

# OS/system library selection... (exactly one of the following must be '1')
AS_OS_NONE := 0           # No OS (software running on "bare metal")
AS_OS_POSIX := 1          # We have a POSIX-compliant OS (including Linux)
AS_OS_LINUX_KERNEL := 0   # Code is part of a Linux driver
AS_OS_WINDOWS := 0        # OS is Microsoft Windows (user mode) (not supported yet)
AS_OS_WINDOWS_KERNEL := 0 # OS is Microsoft Windows (kernel mode) (not supported yet)



# Misc. library settings...
# (TBD: auto-generate those in 'Asterics.mk' based on 'AS_OS_*'?)
AS_HAVE_HEAP := 1
AS_HAVE_PRINTF := 0     // TBD: Move to 'Config.mk'
