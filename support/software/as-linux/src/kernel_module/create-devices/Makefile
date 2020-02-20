#/*--------------------------------------------------------------------------------
#--  This file is part of the ASTERICS Framework. 
#--  Copyright (C) Hochschule Augsburg, University of Applied Sciences
#----------------------------------------------------------------------------------
#-- File:           Makefile
#--
#-- Company:        University of Applied Sciences, Augsburg, Germany
#-- Author:         Alexander Zoellner
#--
#-- Description:    Makefile for creating devices for ASTERICS Linux Driver
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
#--! @brief 	Makefile for creating devices for ASTERICS Linux Driver 
#--------------------------------------------------------------------------------*/

FLAGS = -g -c

# Directory where the source files are located. The "create-devices" directory 
# is usually copied to a system.
SOURCEDIR = ../../vivado_cores/ASTERICS/drivers/asterics_v1_0/src
BUILDDIR = build

CFLAGS = -I. -I$(SOURCEDIR)

EXECUTABLE = create-devices
# List all sources but exclude non-userspace files (e.g. as_memio)
SOURCES = $(filter-out $($(SOURCEDIR)/as_memio.c, $(wildcard $(SOURCEDIR)/*.c))
OBJECTS = $(patsubst $(SOURCEDIR)/%.c,$(BUILDDIR)/%.o,$(SOURCES))

all: dir $(EXECUTABLE)

# Create temporary build directory for object files
dir:
	mkdir -p $(BUILDDIR)

# Build the executable
$(EXECUTABLE): $(OBJECTS) $(EXECUTABLE).o
	$(CC) $^ -o $@

# Build object files of all C files
$(OBJECTS): $(BUILDDIR)/%.o : $(SOURCEDIR)/%.c
	$(CC) $(FLAGS) $< -o $@

# Build source file "create-devices" separately since it is not at the same location as all other C files
$(BUILDDIR)/$(EXECUTABLE).o : $(BUILDDIR)/$(EXECUTABLE).c 
	$(CC) $(FLAGS) $(CFLAGS)  $< -o $@

clean:
	rm -f $(BUILDDIR)/*o $(EXECUTABLE) *.o
