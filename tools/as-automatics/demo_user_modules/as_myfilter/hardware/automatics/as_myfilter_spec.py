# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_myfilter_spec.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Description:
Python module used by as_automatics used to build the generators internal model
of the ASTERICS hardware module as_myfilter.
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
# @file as_myfilter_spec.py
# @author Philip Manke
# @brief Specifics for as_myfilter used by as_automatics
# -----------------------------------------------------------------------------

from as_automatics_module import AsModule
# from as_automatics_interface import Interface
# from as_automatics_port import Port
# from as_automatics_generic import Generic

# class <InterfaceNameInCamelCase>(Interface):
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
# This method can be used to
#        self.set_prefix_suffix(prefix="<prefix>", suffix="<suffix>")


# This is a template for a module specification used by the generator tool
# tool for ASTERICS: as_automatics

# This type of Python script is used by as_automatics to define the internal
# representation of your hardware module as an AsModule class instance.

# Important: For as_automatics to recognize the script, it aas to be placed in the
# module's folder under "modules/<module folder>/software/automatics/<script file>.py"!
# The file name must be: "as_<module name>_spec.py"!

def get_module_instance(module_dir: str) -> AsModule:
    # In this line the generic module data is set up.
    # Enter the module name in the parenthenses.
    # (By convention it should match the name of the toplevel VHDL file):
    module = AsModule()

    # Pre-Discovery configuration:
    # Here, certain configuration options can be used:

    # Add a custom interface template, defined above, as a possible interface
    # of this module:
    # module.add_local_interface_template(<InterfaceClass>())

    # TODO

    # Here the toplevel file for the module has to be defined.
    # Example, for the file:
    # "modules/as_memwriter/hardware/hdl/vhdl/writer/as_memwriter.vhd"
    # The path to spedify is: "hdl/vhdl/writer/as_memwriter.vhd"
    toplevel_file = "hardware/vhdl/as_myfilter.vhd"

    # Here all other required files in the module's folder need to be specified.
    # The search path starts at the module top-folder, as with the toplevel.
    module.files = []

    # If this module uses files from other modules or from a shared module
    # such as the files in the "as_misc" folder (not technically a module),
    # these have to be declared here.
    # Only the module name has to be listed here
    # (not the folder name, the module name!).
    module.dependencies = ["helpers"]

    # as_automatics now automatically parses the toplevel file and discovers
    # ports, generics, existing interfaces and register interfaces
    module.discover_module("{mdir}/{toplevel}"
                           .format(mdir=module_dir, toplevel=toplevel_file))

    # Special Interfaces:
    # Your module may implement a new interface that the generator could
    # manage automatically. There are two places where you can specify new
    # Interface: In this file, above the definition of the function
    # "get_module_instance", or

    # Module configuration:
    # Here you can add configuration parameters for interfaces, generics,
    # ports, register interfaces and the module itself.
    # Here is a list o possible configuration options along with a brief
    # explanation of what they do. For more detailed information, check
    # the chapter about as_automatics in the ASTERICS manual.

    # Rules for ports:
    # Ports need to be assigned rules.
    # These rules tell the generator what to do with the ports when it
    # comes time to build a system. When the generator integrates a module
    # into a system it will match up interfaces of modules and their ports.
    # Depending on the condition, which ports are available, the generator
    # needs to choose which rules to follow.

    # Valid rule conditions:
    # Conditions for comparing two ports of interfaces:
    #  - "any_missing"
    #  - "any_present"
    #  - "both_missing"
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
    #     Only applicable on the condition "single_port".
    #     The generator will connect the port through to the toplevel
    #     of the ASTERICS IP-Core, keeping the original name of the port
    # "error"
    #     Applicable for any condition.
    #     Raises an error message and stops as_automatics.
    # "warning"
    #     Applicable for any condition.
    #     Raises a warning message and halts as_automatics,
    #     waiting for user input.
    # "note"
    #     Applicable for any condition.
    #     Prints an note to the console output and build logs.
    # "set_value(<value>)"
    #     Applicable to the conditions "any_missing", "single_port",
    #     "sink_missing" and "source_missing".
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
    #     This rule behaves exactly like "bundle_and", exceept that for
    #     this rule the signals are bundled using a big OR gate.
    # "fallback_port(<port name>)"
    #     This action defines another port the port may be connected to, if its
    #     counterpart is missing.
    # "none"
    #     The default rule action: Do nothing. Basically a placeholder.

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

    # More configuration functions:

    # Configure generics:
    # "to_external"-attribute: If you set this attribute to "True", the generic
    # will be propagated to the top-level of the ASTERICS ip-core.
    #module.get_generic("<generic_name>").to_external = True

    # "link_to"-attribute: The generic will be set to the generic provided.
    # The generator will search each higher level file for matching generics.
    # Using this attribute you can set a custom generic to any of the external
    # or standard toplevel generics (such as AXI specific generics).
    # This attribute supports wildcard characters:
    # '?' for single characters, '*' for multiple characters
    #module.get_generic("<generic name>").link_to = "<generic to link to>"

    # You can define a function that is used to check the values the generic
    # is "allowed" to take on:
    # module.get_generic(<Generic name>).set_value_check(<function>)
    # The function can be any Python function that takes one value and returns
    # True or False. It is recommended to use lambda expressions for brevity
    # Example: Allow only values between 16 and 256 for generic "DIN_WIDTH"
    #func = lambda value: (value > 15) and (value < 257)
    # module.get_generic("DIN_WIDTH").set_value_check(func)
    # Example: Allow only the values 16, 32, 48 and 64 for generic "BUS_WIDTH"
    #func = lambda value: value in (16, 32, 48, 64)
    # module.get_generic("BUS_WIDTH").set_value_check(func)

    # TODO

    return module
