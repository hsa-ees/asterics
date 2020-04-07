#! /bin/bash
############################################################################
# This file is part of the ASTERICS Framework.
# Copyright (C) Hochschule Augsburg, University of Applied Sciences
############################################################################
#
# Author: Michael Schaeferling <michael.schaeferling@hs-augsburg.de>
# 
# Modified: 2019-07-05 Philip Manke <philip.manke@hs-augsburg.de> 
#
######## USAGE #############################################################
#
# These settings are needed for proper operation of scripts and Makefiles 
# e.g. to generate an ASTERICS IP core or a complete system.
# Usage:
#  > . settings.sh
# or 
#  > source settings.sh
#
######## LICENCE ###########################################################
#
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
############################################################################

# Set ASTERICS_HOME
export ASTERICS_HOME="$( cd "$(dirname "$BASH_SOURCE")" >/dev/null 2>&1 ; pwd -P )";
# Add ASTERICS Automatics tools to PATH
PATH=$PATH:${ASTERICS_HOME}/tools/as-automatics/;
# Append to PYTHONPATH, so Automatics is found by Python3
export PYTHONPATH=$PYTHONPATH:${ASTERICS_HOME}/tools/as-automatics/;

# The general UAS EES-Lab environment already includes following setup steps, 
# thus they are omitted in that case:
if [ -z $EES_HOME ]; then

  # Add EES tools to PATH
  PATH=$PATH:${ASTERICS_HOME}/tools/ees/

  if [ -z $XILINX_VIVADO ]; then
    echo "Vivado is not sourced! Assuming it is located in /opt/Xilinx/Vivado/2017.2/ .";
    echo "If this is not correct, either modify this file (<asterics>/settings.sh)";
    echo "or source Vivado by setting XILINX_VIVADO.";
    export EES_VIVADO_SETTINGS=/opt/Xilinx/Vivado/2017.2/settings64.sh
  else
    export EES_VIVADO_SETTINGS=$XILINX_VIVADO/settings64.sh
  fi
  
fi