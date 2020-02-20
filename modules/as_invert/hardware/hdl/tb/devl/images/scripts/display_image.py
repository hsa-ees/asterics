#--------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# Copyright (C) Hochschule Augsburg, University of Applied Sciences
#--------------------------------------------------------------------
# File:     display_image.py
#
# Company:  Efficient Embedded Systems Group
#           University of Applied Sciences, Augsburg, Germany
#           http://ees.hs-augsburg.de
#
# Author:   
# Date:     
# Modified: 
#
# Description:
# Display image files using Python
#
#--------------------------------------------------------------------
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3 of the License, or (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#  
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program; if not, see <http://www.gnu.org/licenses/>
#  or write to the Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#--------------------------------------------------------------------

import sys
import numpy
import scipy
import scipy.ndimage
import Image                                                                                

def main(argv):
	
    if (len(argv) < 2):
        print 'Usage: %s <image file> [<image file 2> ...]' % argv[0]
        sys.exit(2)
    
    else:    
    
        # display image(s):
        for filename in argv[1:]:
            img = Image.open(filename)
            img.show()

if __name__ == "__main__":
    main(sys.argv[0:])
