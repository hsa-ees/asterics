#! /bin/bash
############################################################################
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
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

if [ -e ${ASTERICS_HOME}/tools/ ]; then
  # Add ASTERICS Automatics tools to PATH
  export PATH=$PATH:${ASTERICS_HOME}/tools/as-automatics/;
  # Append to PYTHONPATH, so Automatics is found by Python3
  export PYTHONPATH=$PYTHONPATH:${ASTERICS_HOME}/tools/as-automatics/;
  export ASTERICS_AUTOMATICS_HOME=${ASTERICS_HOME}/tools/as-automatics
else
  # Add ASTERICS Automatics tools to PATH
  export PATH=$PATH:${ASTERICS_HOME}/bin/;
  # Append to PYTHONPATH, so Automatics is found by Python3
  export PYTHONPATH=$PYTHONPATH:${ASTERICS_HOME}/lib/;
  export ASTERICS_AUTOMATICS_HOME=${ASTERICS_HOME}/lib/
fi


# The general UAS EES-Lab environment already includes following setup steps, 
# thus they are omitted in that case:
if [ -z $EES_HOME ]; then

  if [ -e ${ASTERICS_HOME}/tools/ ]; then
    # Add EES tools to PATH
    PATH=$PATH:${ASTERICS_HOME}/tools/ees/
  else
    # Add EES tools to PATH
    PATH=$PATH:${ASTERICS_HOME}/bin/ees/
  fi

  if [ "$XILINX_VIVADO" != "" ]; then
    export EES_VIVADO_SETTINGS=$XILINX_VIVADO/settings64.sh
  fi
fi
