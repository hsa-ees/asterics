# ASTERICS - Introduction

Image processing on embedded platforms is a challenging task, especially when implementing extensive computer vision applications. Field-programmable gate arrays (FPGAs) offer a suitable technology to accelerate image processing by customized hardware.
The ASTERICS ("Augsburg Sophisticated Toolbox for Embedded Real-time Image Crunching Systems") framework is designed as a modular building set to perform various real-time image processing tasks. It offers modules and interfaces to perform various image processing operations. These range from (a) pixel-based (thresholding, contrast adjustment, ...) and (b) window-oriented filter operations (noise filters, edge enhancement, ...) to more complex, higher-level operations, which are likely to be defined in software. This way, the framework also covers the integration of complex, higher-level (c) semi-global and (d) global algorithms (e.g. needed for object recognition applications). Several high-level algorithms have been adopted and integrated into the frameworks image processing flow, such as undistortion and rectification, natural feature description and edge detection and Hough transform.
Due to the ASTERICS frameworks open structure in terms of flexible data types and the extensibility of the module library, it is an ideal platform to build systems for sophisticated image processing tasks.

---

# ASTERICS VHDL Code Doxygen Documentation

This documentation is mainly meant as a reference for developers building hardware systems using ASTERICS 
and for developers looking to contribute to ASTERICS hardware modules 
or developing new hardware modules compatible with ASTERICS.

This documentation is structured using Doxygen modules to group hardware to ASTERICS modules.
Access these by clicking the "Modules" section in the sidebar to the left.

## Resources

If you are new or for a general overview of the ASTERICS framework,
we refer to the ASTERICS page of the [EES Website](https://ees.hs-augsburg.de/asterics).

The [ASTERICS manual](./../../asterics-manual.pdf) contains a comprehensive 
documentation of the entire framework, including "Getting Started" chapters if you
are new to ASTERICS and developer guides and reference chapters.

Doxygen documentations for other parts of ASTERICS, 
such as the [embedded software](./../../C_doxygen/html/index.html)
and the [Automatics system generator](./../../Python_doxygen/html/index.html),
are also available.

Of particular interest may be chapter 3 of the ASTERICS manual, the VHDL coding style guide.

## Licensing

Most parts of VHDL code in ASTERICS is licensed under the Lesser GNU Puplic License (LGPL) of revision 3 or newer.
Exeptions are clearly marked in the header of each file and listed in the "LICENSE" file in the root of the ASTERICS distribution.

This documentation is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.
To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/4.0/ 
or send a letter to Creative Commons, PO Box 1866, Mountain View, CA 94042, USA.

