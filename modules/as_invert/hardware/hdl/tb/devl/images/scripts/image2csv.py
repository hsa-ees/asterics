#--------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# Copyright (C) Hochschule Augsburg, University of Applied Sciences
#--------------------------------------------------------------------
# File:     image2csv.py
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
# Convert image files to csv format
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
import getopt
import numpy
import Image


def usage_err():
    print 'Wrong or missing parameters. Usage:'
    usage()
    
def usage():    
    print '%s -i <image file> -o <csv file> -d <delimiter>' % sys.argv[0]


def main(argv):
	
    inputfile = ''
    outputfile = ''
    delimiter = ''
        
    found_infile = False
    found_outfile = False
    found_delimiter = False
	
    try:
        opts, args = getopt.getopt(argv[1:],"hi:d:o:",["help","ifile=","ofile=","delim="])
    except getopt.GetoptError:
        usage_err()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'Help:'
            usage()
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
            found_infile = True
        elif opt in ("-o", "--ofile"):
            outputfile = arg
            found_outfile = True
        elif opt in ("-d", "--delim"):
            delimiter = arg
            found_delimiter = True
    if not found_infile or not found_outfile or not found_delimiter:
        usage_err()
        sys.exit(2)
			
		
    print 'Input file is <', inputfile, '>'
    print 'Output file is <', outputfile, '>'
   
    # create csv file:
    image2csv(inputfile, outputfile, delimiter)
        
def image2csv(inputFileName, outputFileName, delimiter):
    img = Image.open(inputFileName).convert('L') 
    imgData = numpy.array(img, dtype = long)
    numpy.savetxt(fname = outputFileName, X = imgData, delimiter=delimiter, fmt = "%d")    
        
if __name__ == "__main__":
    main(sys.argv[0:])
    
