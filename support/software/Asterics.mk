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
## Makefile fragment for ASTERICS support packages
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

include Config.mk



# Define all source files of the ASTERICS support package
# TBD: find a smooth way to add module drivers
AS_SRC := as_support.c
AS_CFLAGS := -I./asterics



# Version
AS_VERSION := $(shell git describe --tags --long --dirty='*' --abbrev=4 --always)
AS_BUILD_DATE := $(shell date +%Y-%m-%d)



# Configuration...
AS_DEBUG := 1    # enable debug output

AS_CFG := "\n\#define AS_WITH_DEBUG" $(AS_DEBUG)
AS_CFG += "\n"
AS_CFG += "$(shell grep 'AS_.*:=' Config.mk | awk '{ print "\\n\#define", $$1, $$3 }')"



# config.h/config.c targets...
as_config.c: as_config

.PHONY: as_config
as_config:
	@echo "Updating 'as_config.h' and 'as_config.c'..."; \
	echo -e "#ifndef _AS_CONFIG_\n#define _AS_CONFIG_\n" \
		"\nextern const char *buildVersion;\nextern const char *buildDate;\n" \
		$(AS_CFG) \
		"\n\n#endif" | sed 's/[[:space:]]*$$//g' > as_config-new.h; \
	diff -q as_config.h as_config-new.h > /dev/null 2>&1 || mv as_config-new.h as_config.h; \
	rm -f as_config-new.h; \
	echo -e "const char *buildVersion = \""$(AS_VERSION)"\";\nconst char *buildDate = \""$(AS_BUILD_DATE)"\";" > as_config.c
