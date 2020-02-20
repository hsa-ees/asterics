# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# Copyright (C) Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_<module>_spec.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
<module author>

Description:
Python module used by as_automatics used to build the generators internal model
of the ASTERICS hardware module <module name here>.
"""
# --------------------- LICENSE -----------------------------------------------
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>
# or write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# --------------------- DOXYGEN -----------------------------------------------
##
# @file as_<module_name>_spec.py
# @author <module author>
# @brief Specifics for <module> used by as_automatics
# -----------------------------------------------------------------------------

from as_automatics_module import AsModule
# from as_automatics_interface import Interface
# from as_automatics_port import Port
# from as_automatics_generic import Generic

# class <InterfaceName>(Interface):
#     def __init__(self):
#        super().__init__("<interface_name>")
# Each port of the interface needs to be defined in this manner:
# The default value for each parameter is marked with curly braces {}
# For single signal data types, the data_width parameter can be ignored
#        self.add_port(Port("<name>",
#                           direction="<{in}/out>",
#                           data_type="<data_type>{std_logic}",
#                           data_width=Port.DataWidth(a="from"{1},
#                                                     sep="[down]to"{None},
#                                                     b="to"{None}),
#                           optional=<True/{False}>))
# This method can be used to set a common pre/suffix for ALL ports
#        self.set_prefix_suffix(prefix="<prefix>", suffix="<suffix>")


# This is a template for a module specification used by the generator tool
# tool for ASTERICS: as_automatics

# This type of Python script is used by as_automatics to define the internal
# representation of your hardware module as an AsModule class instance.

# Important: For as_automatics to recognize the script,
# it has to be placed in the module's folder under
# "<module repository>/<module folder>/hardware/automatics/<script file>.py"!
# The file name must be: "as_<module name>_spec.py"!

def get_module_instance(module_dir: str) -> AsModule:
    # Instantiate 'module' as a new ASTERICS module
    module = AsModule()

    # Pre-Discovery configuration:
    # Here, certain configuration options can be used:

    # Add a custom interface template, defined above, as a possible interface
    # of this module:
    # module.add_local_interface_template(<InterfaceClass>())

    # Here the toplevel file for the module has to be defined.
    # Example, for the file:
    # "modules/as_memwriter/hardware/hdl/vhdl/writer/as_memwriter.vhd"
    # The path to spedify is: "hdl/vhdl/writer/as_memwriter.vhd"
    toplevel_file = "path/to/toplevel/toplevel_filename.vhd"

    # Here all other required files in the module's folder need to be specified.
    # The search path starts at the module's folder, as with the toplevel.
    module.files = ["hardware/hdl/vhdl/common_file.vhd",
                    "hardware/hdl/vhdl/library.vhd",
                    "hardware/hdl/vhdl/extra_component.vhd",
                    "hardware/hdl/verilog/vendor_lib.v",
                    "hardware/hdl/vhdl/subfolder/shared_component.vhd"]

    # If this module uses files from other modules or from a shared module
    # such as the files in the "as_misc" folder (not technically a module),
    # these have to be declared here.
    # Only the module name has to be listed here
    # (not the folder name, the module name!).
    module.dependencies = ["as_memwriter", "as_lib", "helpers"]

    # as_automatics now automatically parses the toplevel file and discovers
    # ports, generics, existing interfaces and register interfaces
    module.discover_module("{mdir}/{toplevel}"
                           .format(mdir=module_dir, toplevel=toplevel_file))

    # Custom Interfaces:
    # Your module may implement a new interface that the generator could
    # manage automatically. There are two places where you can specify a new
    # Interface: In this file, above the definition of the function
    # "get_module_instance", or in the user script.
    # To add the defined interface to Automatics, you may use one of two methods
    # Use: 'AsModule.add_global_interface_template(InterfaceClassName())'
    # for interfaces used in more than one module.
    # If the interface is exclusive to this module, use:
    # 'module.add_local_interface_template(InterfaceClassName()):

    # Module configuration:
    # Here you can add/modify configuration parameters for interfaces, generics,
    # ports, register interfaces and the module itself.
    # Here is a list o possible configuration options along with a brief
    # explanation of what they do. For more detailed information, check
    # the chapter about as_automatics in the ASTERICS manual.

    # Rules for ports:
    # Ports need to be assigned rules.
    # These rules tell Automatics what to do with the ports when it
    # comes time to build a system. When the generator integrates a module
    # into a system it will match up interfaces of modules and their ports.
    # Depending on the condition, which ports are available, Automatics
    # needs to choose which rules to follow.

    # Valid rule conditions:
    # Conditions for comparing two ports of interfaces:
    #  - "any_missing"
    #  - "any_present" (this is always true)
    #  - "both_present"
    #  - "sink_present"
    #  - "sink_missing"
    #  - "source_present"
    #  - "source_missing"
    # Conditions for ports not part of an interface:
    #  - "single_port"
    #  - "external_port"

    # Valid rule-actions:
    # "connect":
    #     Only applicable on the condition "both_present".
    #     Connects the two ports to each other
    # "make_external":
    #     Only applicable on the condition "single_port" or "external_port".
    #     The generator will connect the port through to the toplevel
    #     of the ASTERICS IP-Core.
    # "error"
    #     Applicable for any condition.
    #     Raises an error message and stops as_automatics.
    # "warning"
    #     Applicable for any condition.
    #     Prints a warning message, continuing the process.
    # "note"
    #     Applicable for any condition.
    #     Prints a note to the console output and build logs.
    # "set_value(<value>)"
    #     Applicable to the conditions "any_missing", "single_port",
    #     "sink_missing", "any_present" and "source_missing".
    #     Sets the port to the user defined <value>.
    #     This can be a VHDL signal name, VHDL keyword,
    #     number or data representation (eg. '1', X"F00BA5", open, reg_03).
    #     The "value" given will be directly copied into the VHDL source code.
    # "bundle_and"
    #     Applicable to all conditions except for "both_missing",
    #     "source_missing" and "any_missing"
    #     Similar to "make_external", but bundles all ports with the same
    #     rule and name of all ASTERICS modules in this system.
    #     The signals are bundled together using a single big AND gate.
    # "bundle_or"
    #     This rule behaves exactly like "bundle_and", except that for
    #     this rule the signals are bundled using a big OR gate.
    # "fallback_port(<port name>)"
    #     Applicable to "source_missing" and "sink_missing",
    #     depending on the ports data direction.
    #     This action defines another port the port may be connected to, if its
    #     counterpart is missing.
    # "none"
    #     The default rule action: Do nothing.

    # By default all ports are assigned a minimal ruleset:
    #   1. "both_present" -> "connect"
    #   2. "sink_missing" -> "warning"

    # Use the following functions to modify the rulesets of ports to fit
    # your needs:

    # Use this line to add a rule to a port, one rule action at a time.
    # module.get_port("<Port name>").add_rule("<rule_condition>", "<rule_action>")

    # Use this line to replace all rule actions for a single condition with
    # a new rule action.
    # module.get_port("<Port name>").overwrite_rule("<rule_condition>", "<new_rule_action>")

    # Use this line to remove a rule condition from a port
    # module.get_port("<Port name>").remove_rule("<rule_condition>")

    # Use this line to remove all rules from a port
    # module.get_port("<Port name>").set_ruleset([])

    # More configuration functions:

    # Configure generics:
    # "to_external"-attribute: Default value is "True", setting this to "False"
    # will cause Automatics to not propagate this Generic to toplevel, if no
    # value is set.
    # module.get_generic("<generic name>").to_external = True

    # "link_to"-attribute: The generic will be set to the generic provided.
    # Automatics will search each higher level module for matching generics.
    # Using this attribute you can set a custom generic to any of the external
    # or standard toplevel generics (such as AXI specific generics).
    # module.get_generic("<generic name>").link_to = "<generic to link to>"

    # You can define a function that is used to check the values the generic
    # is "allowed" to take on:
    # module.get_generic(<Generic name>).set_value_check(<function>)
    # The function can be any Python function that takes one value and returns
    # True or False. It is recommended to use lambda expressions for brevity
    # Example: Allow only values between 16 and 256 for generic "DIN_WIDTH"
    #func = lambda value: (value > 15) and (value < 257)
    # module.get_generic("DIN_WIDTH").set_value_check(func)
    # This function will check the value that
    # the generic is set to in the user script.

    return module
