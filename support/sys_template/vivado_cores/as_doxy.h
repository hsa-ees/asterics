/** @mainpage ASTERICS
 *
 *  @section intro Introduction
 *  Image processing on embedded platforms is a challenging task, especially when implementing extensive computer vision applications. Field-programmable gate arrays (FPGAs) offer a suitable technology to accelerate image processing by customized hardware.
 *
 *  The ASTERICS ("Augsburg Sophisticated Toolbox for Embedded Real-time Image Crunching Systems") framework is designed as a modular building set to perform various real-time image processing tasks. It offers modules and interfaces to perform various image processing operations. These range from (a) pixel-based (thresholding, contrast adjustment, ...) and (b) window-oriented filter operations (noise filters, edge enhancement, ...) to more complex, higher-level operations, which are likely to be defined in software. This way, the framework also covers the integration of complex, higher-level (c) semi-global and (d) global algorithms (e.g. needed for object recognition applications). Several high-level algorithms have been adopted and integrated into the frameworks image processing flow, such as undistortion and rectification, natural feature description and edge detection and Hough transform.
 *
 *  Due to the ASTERICS frameworks open structure in terms of flexible data types and the extensibility of the module library, it is an ideal platform to build systems for sophisticated image processing tasks.
 *
 *  Visit the <a href="http://ees.hs-augsburg.de">website of the 'Efficient Embedded Systems' workgroup</a>.
 *
 *  Get the recent code base from the <a href="http://ti-srv.informatik.hs-augsburg.de/repo/asterics.git/">Git-Repository</a>.
 *
 *  @section modules Modules
 *  Modules can be found in the ["Modules" tab](modules.html).
 *
 *  @section asp ASTERICS software support
 *  The purpose of an ASTERICS support package (ASP) is to provide information on the ASTERICS hardware to application programs and to encapsulate FPGA- and OS-specific functionality.
 *
 *  For details on the ASP, see the [ASP Readme](../support/software/README).
 */
