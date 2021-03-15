# ASTERICS Automatics - The System Generator for ASTERICS

Automatics allows the automated generation of ASTERICS systems using 
Automatics Script - concise Python scripts using simple method calls.
As Automatics Script files are essentially written in Python, 
all features of the Python language can be used by expierenced users, 
while people with little or no knowledge of programming languages 
can treat it as a text configuration file, 
as no complex syntax constructs are required.

---

# Automatics Doxygen Documentation

This documentation is mainly for developers writing Automatics scripts 
and for developers looking to contribute to the Automatics system generator.
It includes a full account of all methods meant for use in Automatics Scripts with detailed descriptions.

This documentation is structured using Doxygen modules by broad topics.
Access these by clicking the "Modules" section in the sidebar to the left.

Alternatively, each class page refers to a Python class or module with all included methods.
These are available through the "Classes" section in the sidebar.

Furthermore, as Automatics is implemented using Python, the Automatics CLI can be started using:
```sh
$ source asterics/settings.sh
$ asterics_browser_cli
```

Then, the built-in Python functionality can be used to read the description, for example using:
```python
In [1]: AsProcessingChain.add_module?
```
## Resources

If you are new or for a general overview of the ASTERICS framework,
we refer to the ASTERICS page of the [EES Website](https://ees.hs-augsburg.de/asterics).

The [ASTERICS manual](./../../asterics-manual.pdf) contains a comprehensive 
documentation of the entire framework, including "Getting Started" chapters if you
are new to ASTERICS, developer guides and reference chapters.

Doxygen documentations for developers looking to contribute to other parts of ASTERICS, 
such as the [embedded software](./../../C_doxygen/html/index.html)
and the [hardware modules](./../../VHDL_doxygen/html/index.html), are available.

Of particular interest may be chapter 3 of the ASTERICS manual, the Python coding style guide.

## Licensing

Most parts of ASTERICS are licensed under the Lesser GNU Puplic License (LGPL) of revision 3 or newer.
Exeptions are clearly marked in the header of each file and listed in the "LICENSE" file in the root of the ASTERICS distribution.
Automatics is completely licensed under the LGPL-3 or newer revisions.

This documentation is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.
To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/4.0/ 
or send a letter to Creative Commons, PO Box 1866, Mountain View, CA 94042, USA.

