#--------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# Copyright (C) Hochschule Augsburg, University of Applied Sciences
#--------------------------------------------------------------------
# File:     csv2image.py
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
# Convert image files in csv format (integers) to png format
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
import scipy
import scipy.ndimage
import cv2
                  

def usage_err():
    print 'Wrong or missing parameters. Usage:'
    usage()
    
def usage():    
    print '%s -i <csv file> -o <image file> -d <delimiter>' % sys.argv[0]


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
    
    csv2image(inputfile, outputfile, delimiter)


def csv2image(inputFileName, outputFileName, delimiter):
    csvData = numpy.genfromtxt(fname = inputFileName, delimiter = delimiter, dtype=int)
    params = list()
    params.append(cv2.IMWRITE_PNG_COMPRESSION)
    params.append(0)
    cv2.imwrite(outputFileName, csvData, params)


if __name__ == "__main__":
    main(sys.argv[0:])
    
