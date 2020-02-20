############################################################################
#
# This file is part of the ASTERICS Framework.
# 
# Author: Philip Manke <philip.manke@hs-augsburg.de> 2019-07-05
#
######## USAGE #############################################################
#
# This short script starts Automatics into the interactive mode.
#
######## LICENCE ###########################################################
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
############################################################################

if [ -z $ASTERICS_HOME ]; then
    echo "ASTERICS_HOME is not set! Cannot start Automatics!";
    echo "Source the settings.sh file in the root directory of the ASTERICS installation!";
    echo "";
    exit 1;
fi

if [ -z $(which ipython3) ]; then
    ipython -i $ASTERICS_HOME/tools/as-automatics/as_automatics_env_init.py;
else
    ipython3 -i $ASTERICS_HOME/tools/as-automatics/as_automatics_env_init.py;
fi

