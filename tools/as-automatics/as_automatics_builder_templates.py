# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_automatics_builder_templates.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Contains static strings and templates for as_automatics_builder.py.
"""
# --------------------- LICENSE -----------------------------------------------
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>
# or write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# --------------------- DOXYGEN -----------------------------------------------
##
# @file as_automatics_builder_templates.py
# @ingroup automatics_generate
# @author Philip Manke
# @brief Contains static strings and templates for as_automatics_builder.py.
# -----------------------------------------------------------------------------

##
# @addtogroup automatics_generate
# @{

ASP_FILES = [
    "{asterics_root}/support/software/asp/as_support.c",
    "{asterics_root}/support/software/asp/as_support.h",
    "{asterics_root}/support/software/asp/README",
]

VEARS_REL_PATH = "ipcores/VEARS/"
IPCORE_FOLDER = "vivado_cores/"


ASTERICS_H_NAME = "asterics.h"
ASTERICS_H_DESCRIPTION = """-- Description:    Driver (header file) for the ASTERICS IP core.
--                 This header file
--                  a) incorporates drivers of implemented ASTERICS modules and
--                  b) defines register mapping for low level hardware access."""

ASTERICS_HEADER_SW = """/*------------------------------------------------------------------------------
--  This file is part of the ASTERICS Framework.
--  (C) 2019 Hochschule Augsburg, University of Applied Sciences
--------------------------------------------------------------------------------
-- File:           {filename}
--
-- Company:        University of Applied Sciences, Augsburg, Germany
-- Author:         ASTERICS Automatics
--
{description}
--------------------------------------------------------------------------------
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
------------------------------------------------------------------------------*/
"""

# Template for the ASTERICS toplevel C header file
ASTERICS_H_TEMPLATE = """{header}
/**
 * @file  asterics.h
 * @brief Incorporating drivers for ASTERICS IP core modules and register mapping definition.
 *
 * \\defgroup asterics_mod ASTERICS modules
 *
 */

#ifndef ASTERICS_H
#define ASTERICS_H

#ifdef __cplusplus
extern "C"
{{
#endif

#include "as_support.h"
#include "as_config.h"


/************************** Integrated Modules ***************************/

{module_driver_includes}

/************************** ASTERICS IP-Core Base Address ***************************/
#define ASTERICS_BASEADDR {base_addr:#8X}

#define AS_REGISTERS_PER_MODULE {regs_per_mod}

/************************** Module Register Mapping ***************************/

{base_regs}

/************************** Module Address Mapping ***************************/

{addr_map}


{module_additions}

#ifdef __cplusplus
}}
#endif

#endif /** ASTERICS_H */
"""

AS_CONFIG_C_NAME = "as_config.c"
AS_CONFIG_C_DESCRIPTION = "-- Description: Defines system constants."

AS_CONFIG_C_TEMPLATE = """{header}

#include "as_config.h"

// SHA256 hash identifying the ASTERICS system
// compatible with this software version.
const uint8_t asterics_hw_config[64] =
{{
    {hashstr}
}};

const char *buildVersion = "{version}";
const char *buildDate = "{date}";
"""

AS_CONFIG_H_NAME = "as_config.h"
AS_CONFIG_H_DESCRIPTION = """-- Description:
-- Configuration file for the ASTERICS Support Library"""
AS_CONFIG_H_TEMPLATE = """{header}

#ifndef _AS_CONFIG_
#define _AS_CONFIG_

#include <stdint.h>

extern const char *buildVersion;
extern const char *buildDate;
extern const uint8_t asterics_hw_config[64];

#define AS_WITH_DEBUG 0

#define AS_BIG_ENDIAN_HW 0
#define AS_BIG_ENDIAN_SW 0
#define AS_BSP_DUMMY 0
#define AS_BSP_XILINX 1
#define AS_BSP_ALTERA 0
#define AS_WITH_MULTIPROCESSING 0
#define AS_OS_NONE 1
#define AS_OS_POSIX 0
#define AS_OS_LINUX_KERNEL 0
#define AS_OS_WINDOWS 0
#define AS_OS_WINDOWS_KERNEL 0
#define AS_HAVE_HEAP 1
#define AS_HAVE_PRINTF 0

#endif // _AS_CONFIG_
"""

# Names for the TCL fragments
TCL1_NAME = "package_config.tcl"
TCL2_NAME = "package_interface_config.tcl"
TCL3_NAME = "package_ooc_config.tcl"
# Path in the project directory to store the TCL fragments in
TCL_FOLDER = "vivado_cores/ASTERICS/"

# Generic file header, adapted for TCL files
TCL_HEADER = """
#------------------------------------------------------------------------------
#-  This file is part of the ASTERICS Framework.
#-  (C) 2019 Hochschule Augsburg, University of Applied Sciences
#-------------------------------------------------------------------------------
#- File:           {}
#-
#- Company:        University of Applied Sciences, Augsburg, Germany
#- Author:         ASTERICS Automatics
#-
#- Description:    {}
#-------------------------------------------------------------------------------
#- This program is free software; you can redistribute it and/or
#- modify it under the terms of the GNU Lesser General Public
#- License as published by the Free Software Foundation; either
#- version 3 of the License, or (at your option) any later version.
#- 
#- This program is distributed in the hope that it will be useful,
#- but WITHOUT ANY WARRANTY; without even the implied warranty of
#- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#- Lesser General Public License for more details.
#- 
#- You should have received a copy of the GNU Lesser General Public License
#- along with this program; if not, see <http://www.gnu.org/licenses/>
#- or write to the Free Software Foundation, Inc.,
#- 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#-----------------------------------------------------------------------------*/

"""

AS_IIC_MAP_TCL_TEMPLATE = (
    "# Set up interface properties:\n"
    "ipx::add_bus_interface {iic_if_name} [ipx::current_core]\n"
    "set_property abstraction_type_vlnv xilinx.com:interface:iic_rtl:1.0 "
    "[ipx::get_bus_interfaces {iic_if_name} -of_objects [ipx::current_core]]\n"
    "set_property bus_type_vlnv xilinx.com:interface:iic:1.0 "
    "[ipx::get_bus_interfaces {iic_if_name} -of_objects [ipx::current_core]]\n"
    "set_property interface_mode master "
    "[ipx::get_bus_interfaces {iic_if_name} -of_objects [ipx::current_core]]\n"
    "set_property display_name asterics_{iic_if_name} "
    "[ipx::get_bus_interfaces {iic_if_name} -of_objects [ipx::current_core]]\n"
    "# IIC port mapping:\n"
    "ipx::add_port_map SCL_T [ipx::get_bus_interfaces {iic_if_name} "
    "-of_objects [ipx::current_core]]\n"
    "set_property physical_name {iic_signal_prefix}scl_out_enable "
    "[ipx::get_port_maps SCL_T -of_objects "
    "[ipx::get_bus_interfaces {iic_if_name} -of_objects [ipx::current_core]]]\n"
    "ipx::add_port_map SDA_O [ipx::get_bus_interfaces {iic_if_name} "
    "-of_objects [ipx::current_core]]\n"
    "set_property physical_name {iic_signal_prefix}sda_out "
    "[ipx::get_port_maps SDA_O -of_objects "
    "[ipx::get_bus_interfaces {iic_if_name} -of_objects [ipx::current_core]]]\n"
    "ipx::add_port_map SDA_I [ipx::get_bus_interfaces {iic_if_name} "
    "-of_objects [ipx::current_core]]\n"
    "set_property physical_name {iic_signal_prefix}sda_in "
    "[ipx::get_port_maps SDA_I -of_objects "
    "[ipx::get_bus_interfaces {iic_if_name} -of_objects [ipx::current_core]]]\n"
    "ipx::add_port_map SDA_T [ipx::get_bus_interfaces {iic_if_name} "
    "-of_objects [ipx::current_core]]\n"
    "set_property physical_name {iic_signal_prefix}sda_out_enable "
    "[ipx::get_port_maps SDA_T -of_objects "
    "[ipx::get_bus_interfaces {iic_if_name} -of_objects [ipx::current_core]]]\n"
    "ipx::add_port_map SCL_O [ipx::get_bus_interfaces {iic_if_name}"
    " -of_objects [ipx::current_core]]\n"
    "set_property physical_name {iic_signal_prefix}scl_out "
    "[ipx::get_port_maps SCL_O -of_objects "
    "[ipx::get_bus_interfaces {iic_if_name} -of_objects [ipx::current_core]]]\n"
    "ipx::add_port_map SCL_I [ipx::get_bus_interfaces {iic_if_name} "
    "-of_objects [ipx::current_core]]\n"
    "set_property physical_name {iic_signal_prefix}scl_in "
    "[ipx::get_port_maps SCL_I -of_objects "
    "[ipx::get_bus_interfaces {iic_if_name} -of_objects [ipx::current_core]]]\n"
)

# TCL command templates:
BUS_IF_ASSOCIATION_TCL_TEMPLATE = (
    "ipx::associate_bus_interfaces -clock {clk} -busif {busif} -clear "
    "[ipx::current_core]\n"
    "# ^ Dissassociate any signals with this AXI interface"
    " (to be save)\n"
    "# Associate the correct clock and reset signals\n"
    "ipx::associate_bus_interfaces -clock {clk} -reset {rst} "
    "-busif {busif} [ipx::current_core]\n"
    "# Store the interface object in a variable with known name\n"
    "set {ref} [ipx::get_bus_interfaces -of_objects "
    "[ipx::current_core] {busif}]\n"
)

MEMORY_MAP_TCL_TEMPLATE = (
    "ipx::remove_memory_map slave_s_axi [ipx::current_core]\n"
    "ipx::remove_memory_map {ref} [ipx::current_core]\n"
    "# ^ Remove any memory maps from the interface\n"
    "# (potentially) Re-add a memory map\n"
    "ipx::add_memory_map {mem_map_ref} [ipx::current_core]\n"
    "# Add a slave memory map reference\n"
    "set_property slave_memory_map_ref {mem_map_ref} ${ref}\n"
    "# Add an address block to the memory map "
    "using the above reference\n"
    "ipx::add_address_block {{{axi_type}}} [ipx::get_memory_maps "
    "{mem_map_ref} -of_objects [ipx::current_core]]\n"
    "# Set the address block range\n"
    "set_property range {{{mem_range}}} [ipx::get_address_blocks "
    "{{{axi_type}}} -of_objects [ipx::get_memory_maps "
    "{{{mem_map_ref}}}  -of_objects [ipx::current_core]]]\n"
)

VIVADO_TCL_COMMANDLINE_TEMPLATE = (
    "ees-vivado -mode tcl -source {}packaging.tcl "
    '-notrace -tclargs "{}package_config.tcl"'
    #' -tclargs "{}package_config.tcl"'
)

TCL_OOC_TEMPLATE = (
    # Command this tries to emulate. Using the below is waaaayyyy slower
    # "create_fileset -blockset -define_from {ent_name} {ent_name}"
    "# OOC for {ent_name}\n"
    # User feedback
    'puts "{progress}"\n'
    # Create a new OOC block fileset
    "create_fileset -blockset {ent_name}\n"
    # Add all required files
    "add_files -fileset {ent_name} [get_files {{{source_files}}}]\n"
    # Define toplevel VHDL source file
    "set_property top {ent_name} [get_fileset {ent_name}]\n"
    # Set properties: used_in, file_type and library name
    "set_property file_type {{VHDL 2008}} [get_files -of_objects [get_filesets {ent_name}]]\n"
    "set_property library {{asterics}} [get_files -of_objects [get_filesets {ent_name}]]\n"
    "set_property used_in {{out_of_context synthesis implementation}} [get_files {top_source}]\n"
    # Update the OOC run's compile order (speeds up the process for some reason)
    "update_compile_order -fileset {ent_name}\n"
)

HOUSE_CLEANING_LIST_VIVADO = (
    "package_interface_config.tcl",
    "package_config.tcl",
    "package_ooc_config.tcl",
    "asterics.hw",
    "asterics.cache",
    "asterics.ip_user_files",
    "asterics.xpr",
    "asterics.zip",
    "vivado.log",
    "vivado.jou",
)

## @}
