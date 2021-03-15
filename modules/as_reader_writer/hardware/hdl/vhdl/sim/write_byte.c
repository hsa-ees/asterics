/*--------------------------------------------------------------------
-- This file is part of the ASTERICS Framework.
-- Copyright (C) Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------
-- File:     write_byte.c
--
-- Company:  Efficient Embedded Systems Group
--           University of Applied Sciences, Augsburg, Germany
--           http://ees.hs-augsburg.de
--
-- Author:   Markus Bihler
--           Alexander Zoellner
--           Michael Schaeferling <michael.schaeferling@hs-augsburg.de>
-- Date:     
-- Modified: 
--
-- Description:
--
----------------------------------------------------------------------
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
--------------------------------------------------------------------*/


#include "write_byte.h"

#include "stdio.h"
#include "string.h"

#define FILE_NAME_SIZE 256

int write_byte(int addr, int data) {
    
    char file_name[FILE_NAME_SIZE] = {0};
    FILE *temp_file;

    temp_file = fopen("temp.file","r");
    if (temp_file == NULL) {
        perror("Error in write_byte.c: Can not find 'temp.file', which should contain a filename.");
        return 1;
    }
    
    if ( fgets(file_name, FILE_NAME_SIZE-1, temp_file) == NULL ) {
        perror("Error in write_byte.c: 'temp.file' is empty. 'temp.file' should hold the filename to be read.\n");
        return 1;
    }
    fclose(temp_file);

    FILE * pFile;

    int len;

    len = strlen(file_name);
    file_name[len-1] = 0;

    if(addr == 0) {
        pFile = fopen(file_name, "wb");
    }
    else {
        pFile = fopen(file_name,"a+b");
    }
    if (pFile==NULL) {
        perror("Error in write_byte.c: fopen() failed.\n");
        return 1;
    }

    fputc(data, pFile);
    fclose(pFile);

    return 0;
}
