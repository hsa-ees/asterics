/*--------------------------------------------------------------------
-- This file is part of the ASTERICS Framework.
-- Copyright (C) Hochschule Augsburg, University of Applied Sciences
----------------------------------------------------------------------
-- File:     read_byte.c
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


#include "read_byte.h"

#include "stdio.h"
#include "string.h"

#define FILE_NAME_SIZE 256

int read_byte(int addr) {
    
    char file_name[FILE_NAME_SIZE] = {0};
    int last_pos = 0;
    int c = 0;
    int len = 0;
    FILE *temp_file;
    FILE *pFile;

    temp_file = fopen("temp.file","r");
    if (temp_file == NULL) {
        perror("Error: Can not find 'temp.file', which should contain a filename");
        return 0;
    }
    
    if ( fgets(file_name, FILE_NAME_SIZE-1, temp_file) == NULL ) {
        perror("Error: 'temp.file' is empty. 'temp.file' should hold the filename to be read\n");
        return 0;
    }
    fclose(temp_file);

    len = strlen(file_name);
    file_name[len-1] = 0;

    pFile = fopen(file_name,"rb");
    if (pFile==NULL) {
        perror("Error: read_byte.c: fopen() failed\n");
        return 0;
    }
    fseek (pFile, 0L, SEEK_END);
    last_pos = ftell(pFile);
    if (last_pos > addr) {
        fseek ( pFile , addr , SEEK_SET );
        c = fgetc(pFile);
    }
    else {
        c = -2;
    }
    fclose(pFile);

    return c;
}
