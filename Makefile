##--------------------------------------------------------------------
## This file is part of the ASTERICS Framework.
## Copyright (C) Hochschule Augsburg, University of Applied Sciences
##--------------------------------------------------------------------
## File:     Makefile
##
## Company:  Efficient Embedded Systems Group
##           University of Applied Sciences, Augsburg, Germany
##           https://ees.hs-augsburg.de
##
## Author:   Michael Schaeferling <michael.schaeferling@hs-augsburg.de>
## Date:     2020-09-28
## Modified: 
##
## Description:
##   The ASTERICS main Makefile.
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


# Needed by the 'install' target:
PREFIX ?= /opt/asterics
DISTRIB_PARTS ?= README.md LICENSE settings.sh doc/ ipcores/ modules/ support/ systems/ tools/


.PHONY: download
download:
	@# Nothing to do

.PHONY: build
build:
	@# Nothing to do

.PHONY: clean
clean:
	@# Nothing to do

.PHONY: install
install:
	@test "$(PREFIX)" != "" || ( echo "ERROR: Make variable PREFIX must be set for the 'install' target."; exit 3; )
	mkdir $(PREFIX) && \
	for p in $(DISTRIB_PARTS); do \
	  cp -ar $$p $(PREFIX); \
	done
