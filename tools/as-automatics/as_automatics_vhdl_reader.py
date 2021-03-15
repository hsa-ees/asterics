# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_automatics_vhdl_reader.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke

Modified: Thibaut Temkeng

Description:
Small VHDL Parser part of as_automatics.
Can only parse and understand simple entity definitions.
Can extract generics and ports into lists of Python objects.
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
# @file as_automatics_vhdl_reader.py
# @ingroup automatics_analyze
# @author Philip Manke
# @brief Contains methods for parsing the entity definition from a VHDL-file.
# -----------------------------------------------------------------------------

from typing import Sequence
import as_automatics_logging as as_log

from as_automatics_port import Port
from as_automatics_generic import Generic
from as_automatics_constant import Constant
from as_automatics_helpers import eval_vhdl_expr
from as_automatics_vhdl_static import PIPE_WINDOW_TYPE, PIPE_LINE_TYPE
from as_automatics_exceptions import AsAnalysisError, AsFileError

LOG = as_log.get_log()


##
# @addtogroup automatics_analyze
# @{


class VHDLReader:
    """! @brief This class implements methods used to read and partially parse VHDL-files.
    It is only capable of parsing the entity portion
    of the file. The entity name, generics, ports and ASTERICS-specific
    register interfaces are extracted, translated into Python objects
    and returned in lists."""

    keywords = [
        "entity",
        "port",
        "generic",
        "end",
        "architecture",
        "constant",
        "component",
        "begin",
    ]
    constant_names = ["slave_register_configuration"]

    def __init__(self, filename: str, window_module: bool = False):
        self.vhdl_file = filename
        self.file_analyzed = False
        self.found_ports = []
        self.found_generics = []
        self.found_constants = []
        self.errors = []
        self.entity_name = ""
        self.arch_name = ""
        self.component_name = ""
        self.line = ""
        
        self.defgroup = ""
        self.addtogroup = ""
        self.description = ""
        self.brief_description = ""
        self.window_module = window_module

    @staticmethod
    def __isDirtyLine__(line: str) -> bool:
        """ the function checks if the information from the line can be used"""
        line = line.strip()
        if len(line) == 0:
            return True
        if "--" not in line:
            return False
        return (
            len(line[line.find("--") + 2 :].strip()) == 0
            or line.find("---") == 0 or line.find("--! @{") == 0
        )

    @classmethod
    def __valide_line__(cls, file_obj, description: str, lenght: int    ) -> (str, int):
        i = 0
        while i < lenght:
            i += 1
            line = file_obj.readline()
            if cls.__isDirtyLine__(line) or "@brief" in line or "@file" in line or "@addtogroup" in line or "@defgroup" in line:
                return description.strip(), i
            else:
                if "--!" in line:
                    description += " " + line[line.find("--!") + 3 :].strip()
                else:
                    description += "  " + line[line.find("--") + 2 :].strip()
        return "", 0

    @staticmethod
    def __find_element__(file_obj, name, lenght) -> (str, int):
        """ !brief Search the 'name' in the file 'file_obj'"""
        i = 0
        while i < lenght:
            i += 1
            line = file_obj.readline().strip()
            if name in line:
                data = line.find(name)
                data = line[data + len(name) + 1 :]
                return data, i
        return "", 0

    def __get_description__(self, file_obj):
        """Return the description  and brief description of the module from the file that was analyzed."""

        with open(file_obj.name) as file:
            lenght = len(file.readlines())
            file.seek(0)

            data, pos = self.__find_element__(
                file, "Description", lenght
            )
            # Write the module description
            lenght -= pos
            self.description, pos = self.__valide_line__(
                file, data, lenght
            )
            lenght -= pos
            # The module brief description
            data, pos = self.__find_element__(
                file, "@brief", lenght
            )
            lenght -= pos
            self.brief_description, _ = self.__valide_line__(
                file, data, lenght
            )
            
            lenght -= pos
            # The module addtogroup
            data, pos = self.__find_element__(
                file, "@addtogroup", lenght
            )
            lenght -= pos
            self.defgroup, _ = self.__valide_line__(
                file, data, lenght            )

            lenght -= pos
            # The module defgroup
            data, pos = self.__find_element__(
                file, "@defgroup", lenght
            )
            lenght -= pos
            self.defgroup, _ = self.__valide_line__(
                file, data, lenght            )

    @staticmethod
    def __get_generic_line__(file):
        generic_comment = ""
        while True:
            line = file.readline().strip()
            if line.find("generic") == 0:
                line = line.replace("generic", "").strip()
                pos = line.find("(")
                line = line[pos + 1 :]
            # Doxygene comment
            if "--!" in line:
                comment_pos = line.find("--!")
                if comment_pos == 0:
                    generic_comment += (
                        line.replace("--!", "").replace("@brief", "").strip()
                    )
                    # line = file.readline()
                    line = "many_comment"
                else:
                    line, generic_comment = [
                        i.strip() for i in line.split("--! @brief")
                    ]
            elif "--" in line:
                # VHDL comment
                comment_pos = line.find("--")
                if comment_pos == 0:
                    generic_comment += line.replace("--", "").strip()
                    # line = file.readline()
                    line = "many_comment"
                else:
                    line, generic_comment = [
                        i.strip() for i in line.split("--")
                    ]
            elif line == ");":
                line = "fin"
            elif line == "(":
                line = ""
            if line != "many_comment":
                return (generic_comment, line)

    def get_entity_name(self) -> str:
        """! @brief Return the name of the entity from the file that was analyzed."""
        if not self.file_analyzed:
            self.__analyze__()
        return self.entity_name

    def get_port_list(self) -> Sequence[Port]:
        """! @brief Return a list of port objects, extracted from the VHDL-file."""
        if not self.file_analyzed:
            self.__analyze__()
        return self.found_ports

    def get_generic_list(self) -> Sequence[Generic]:
        """! @brief Return a list of generic objects, extracted from the VHDL-file."""
        if not self.file_analyzed:
            self.__analyze__()
        return self.found_generics

    def get_constant_list(self) -> Sequence[Constant]:
        """! @brief Return a list of constant objects, extracted from the VHDL-file."""
        if not self.file_analyzed:
            self.__analyze__()
        return self.found_constants

    def __analyze__(self):
        LOG.info("Start analysis of VHDL file '%s' ...", self.vhdl_file)
        try:
            self.file_analyzed = False
            # Open the source file
            with open(self.vhdl_file) as file:
                LOG.debug("File opened, reading...")
                self.__analyze_readfile__(file)
        except IOError as err:
            LOG.error(
                "File '%s' couldn't be opened: '%s'", self.vhdl_file, str(err)
            )
            raise AsFileError(self.vhdl_file, "File could not be opened!")
        if self.errors:
            LOG.error(
                "VHDL analysis function returned with %s error(s).",
                str(len(self.errors)),
            )
            raise AsAnalysisError(
                self.vhdl_file,
                "{} error(s) encountered!".format(len(self.errors)),
            )

    def __analyze_readfile__(self, file_obj):
        # Marker variables, where in the VHDL file are we currently?
        in_arch = False
        in_entity = False
        in_component = False
        # While not done...
        while not self.file_analyzed:
            # Move to the next 'interesting' line (with a keyword)
            self.__get_description__(file_obj)
            ret = self.__find_next_keyword__(file_obj).strip()

            if ret == "":  # find_next_keyword() returns "" in case of EOF
                return True
            # On keyword 'entity'
            if ret in ["component", "architecture", "entity"]:
                name = self._get_target_name__(ret)
                if name == "":
                    LOG.error(
                        (name + " declaration of '%s' is " "malformed!"),
                        file_obj.name,
                    )
                    self.errors.append(
                        AsAnalysisError(
                            self.vhdl_file,
                            name + "" + "declaration is malformed!",
                            ret,
                        )
                    )
                if ret.strip() == "entity":
                    in_entity = True
                    self.entity_name = name
                elif ret == "architecture":
                    in_arch = True
                    self.arch_name = name
                else:
                    in_component = True
                    self.component_name = name
                    LOG.debug(
                        "Found " + ret + " '%s' of '%s'",
                        self.arch_name,
                        file_obj.name,
                    )

            # On keyword 'begin': used to detect when the functional body of
            # of the VHDL file starts. That doesn't need analysis, used as a
            # stop condition for this VHDLReader
            elif ret == "begin":
                if not in_entity and in_arch and not in_component:
                    self.file_analyzed = True
                    LOG.debug(
                        (
                            "Found 'begin' in 'architecture', skipping"
                            " rest of '%s'."
                        ),
                        file_obj.name,
                    )
            # On keyword 'port', call port anaylsis method when in entity
            elif ret == "port":
                if in_entity and not (in_component or in_arch):
                    self.__get_ports__(file_obj)
                else:
                    LOG.debug("Skipped port keyword: Not in entity")
            # Analogous to 'port'
            elif ret == "generic":
                if in_entity and not (in_component or in_arch):
                    self.__get_generics__(file_obj)
                else:
                    LOG.debug("Skipped generic keyword: Not in entity")
            # Analogous to 'port', only call the method when in architecture
            elif ret == "constant":
                if in_arch:
                    result = self.__get_constant__(file_obj)
                    if result:
                        LOG.warning(
                            ("Malformed constant found, '%s', " "line: '%s'"),
                            result,
                            self.line,
                        )
                else:
                    LOG.warning(
                        (
                            "Found 'constant' keyword outside of "
                            "'architecture' in '%s'"
                        ),
                        file_obj.name,
                    )
            # On keyword 'end': Determine what 'ended' and adjust state
            elif ret == "end":
                if "entity" in self.line or self.entity_name in self.line:
                    in_entity = False
                    LOG.debug("Found 'end' of entity '%s'", self.entity_name)

                elif "architecture" in self.line or self.arch_name in self.line:
                    in_arch = False
                    self.file_analyzed = True
                    LOG.debug(
                        "Found 'end' of architecture '%s'", self.arch_name
                    )

                elif (
                    "component" in self.line or self.component_name in self.line
                ):
                    in_component = False
                    LOG.debug(
                        "Found 'end' of component '%s'", self.component_name
                    )
                elif in_component:
                    # "end" might be encountered as a port/generic name in
                    # a component declaration
                    # Within the entity this is handled,
                    # we need to ignore it here for components
                    pass
                else:
                    LOG.warning(
                        (
                            "Unrecognized use of 'end' in line '%s' "
                            "of file '%s'"
                        ),
                        self.line,
                        file_obj.name,
                    )
            # Log unrecognized keywords
            else:
                LOG.info("Unhandled keyword detected: '%s' - Ignored...", ret)
        return ""

    def __get_entity__(self) -> str:
        # Get the positions of the identifiers ('entity' and 'is')
        entity_pos = self.line.find("entity")
        is_pos = self.line.rfind("is")
        if is_pos < 1:
            # If 'is' is not present, error!
            LOG.critical("Entity declaration is malformed, missing 'is'!")
            return ""
        # else, return everything between 'entity' and 'is'
        return self.line[entity_pos + len("entity") : is_pos - 1].strip()

    def _get_target_name__(self, name) -> str:
        name_pos = self.line.find(name)
        is_pos = self.line.rfind("is")
        if is_pos < 1:
            LOG.critical((name + " declaration is malformed," " missing 'is'!"))
            return ""
        return self.line[name_pos + len(name) : is_pos - 1].strip()

    def __get_arch_name__(self) -> str:
        # Analog functionality as '__get_entity__'
        arch_pos = self.line.find("architecture")
        is_pos = self.line.rfind("is")
        if is_pos < 1:
            LOG.critical(
                ("Architecture declaration is malformed," " missing 'is'!")
            )
            return ""
        return self.line[arch_pos + len("architecture") : is_pos - 1].strip()

    def __get_component_name__(self) -> str:
        # First we get the position of the regular identifiers (component, is)
        comp_pos = self.line.find("component")
        is_pos = self.line.rfind("is")
        if is_pos < 1:  # The component declaration doesn't require the 'is'!
            LOG.debug("Component declaration is missing 'is'!")
            # If 'is' is not present, just return everything after 'component'
            return self.line[comp_pos + len("component") :].strip()
        # else, return everything between 'component' and 'is'
        return self.line[comp_pos + len("component") : is_pos - 1].strip()

    def __get_generics__(self, file_obj) -> int:
        # while True:
        #     # Get the next line with some code in it
        #     test = self.__peek_next_clean_line__(file_obj)
        #     # If that line is not a port declaration (no ':'), return
        #     if ":" not in test:
        #         return len(self.found_generics)
        #     # Advance to the next line
        #     # Get new lines as long as we keep finding a ':'.
        #     line = self.__next_clean_line__(file_obj)
        generic_comment = ""
        line = ""
        while True:

            if ":" in self.line:
                line = (
                    self.line.replace("generic", "")
                    .strip()
                    .replace("(", "")
                    .strip()
                )
            if len(line) == 0:
                generic_comment, line = self.__get_generic_line__(file_obj)
                if line == "fin":
                    return 1
                elif line == "":
                    continue
            # Typical generic declaration:
            # " <name> : <data type> [:= <default value>]"
            words = line.split(":", 1)  # Split off the generics name
            # Split between data type and potential default value
            params = words[1].strip(' ";\n').split(":=", 1)
            # Clean up and capitalize the name
            name = words[0].strip().upper()

            # If a default value is present
            if len(params) > 1:
                params[1] = params[1].strip(' "')
                params[0] = params[0].strip()
                # If its only digits
                if params[0] in ("integer", "natural"):
                    try:
                        default_value = int(params[1])
                    except ValueError:
                        default_value = params[1]
                elif params[0] == "boolean":
                    default_value = params[1].title()
                elif params[0] == "string":
                    default_value = '"' + params[1] + '"'
                elif params[1].isdigit():  # for std_logic[_vector] and similar
                    if "vector" in params[0]:
                        default_value = '"' + params[1] + '"'
                    else:
                        default_value = "'" + params[1] + "'"
                else:
                    # Try to have Pythons 'eval' function evaluate the
                    # expression describing the value
                    # (if it's a mathematical expression)
                    default_value = eval_vhdl_expr(
                        params[1], "generic default value"
                    )
            else:
                default_value = None
            self.found_generics.append(
                Generic(
                    name=name,
                    code_name=name,
                    data_type=params[0].strip(),
                    default_value=default_value,
                    comment=generic_comment,
                )
            )
            self.line = line = ""
            LOG.debug(
                "Found generic '%s' with default value '%s'",
                name,
                default_value,
            )

    def __get_ports__(self, file_obj) -> int:
        while True:
            # Get the next line with some code in it
            test = self.__peek_next_clean_line__(file_obj)
            # If that line is not a port declaration (no ':'), return
            if ":" not in test:
                return len(self.found_ports)
            # Advance to the next line
            line = self.__next_clean_line__(file_obj)
            # Clean and split the input
            line = line.strip("\n; ")
            words = line.split(":", 1)
            # Split the part after the ':' on the first whitespace
            params = words[1].strip().split(maxsplit=1)
            # Now we should have this arrangement for the code:
            #  <port name> : <direction> ' ' <data type>[(<data width>)]
            #   words[0]   :   words[1]
            #              :  params[0]  ' ' params[1]  '('
            direction = params[0]
            name = words[0].strip()  # Get the cleaned name
            LOG.debug("Found port '%s' in line '%s'", name, line)
            # If there's a parenthenses, we need to decode the data width
            parens_pos = params[1].find("(")
            if parens_pos > -1:
                # Extract data type and pass the data width definition
                data_type = params[1][:parens_pos]
                parens = params[1][parens_pos:]
                data_width = self.__get_data_width__(parens[1:-1])
                LOG.debug("Data width translated as '%s'", data_width)
            else:
                # If no data width definition is present, assume width 1
                data_type = params[1]
                data_width = Port.DataWidth(1, None, None)
            # Instantiate and add a new Port to the found ports list
            port = Port(
                name=name,
                code_name=name,
                direction=direction,
                data_type=data_type,
                data_width=data_width,
            )
            if self.window_module and data_type == PIPE_WINDOW_TYPE:
                if len(data_width) < 3:
                    LOG.error(
                        (
                            "Data type '%s' requires 3 dimensions! "
                            "Instead got: '%s' - in file '%s'"
                        ),
                        PIPE_WINDOW_TYPE,
                        parens,
                        self.vhdl_file,
                    )
                else:
                    port.window_config = data_width[:2]
                    port.data_width = data_width[2]
                    LOG.debug(
                        "Found window in '%s' for '%s': '%s'",
                        self.entity_name,
                        name,
                        port.window_config,
                    )
            elif self.window_module and data_type == PIPE_LINE_TYPE:
                if len(data_width) < 2:
                    LOG.error(
                        (
                            "Data type '%s' requires 2 dimensions! "
                            "Instead got: '%s' - in file '%s'"
                        ),
                        PIPE_LINE_TYPE,
                        parens,
                        self.vhdl_file,
                    )
                else:
                    port.data_width = data_width[1]
                    port.line_width = data_width[0]
                    LOG.debug(
                        "Found generic line in '%s' for '%s': '%s'",
                        self.entity_name,
                        name,
                        port.line_width,
                    )

            self.found_ports.append(port)

    def __get_constant__(self, file_obj) -> str:
        # Make sure the current line is the complete constant definition
        if ";" not in self.line:
            self.line = self.line.strip(" \n") + self.__next_clean_statement__(
                file_obj
            )
        # Clean current line, remove the 'constant' keyword and split on ':'
        words = self.line.replace("constant", "", 1).strip(" \n").split(":", 1)
        if len(words) > 1:  # Was there a ':' in this line?
            # If so, we can extract the constant's name
            name = words[0].strip()
            # Split on value assignment
            words = words[1].strip().split(":=", 1)
            if len(words) > 1:  # Was there a ':=' in this line?
                # If so, we can extract both the data type and value.
                data_type = words[0].strip()
                value = words[1].strip(" ;").upper()
                data_width = Port.DataWidth(1, None, None)
                # If the data type is a vector (contains a "(a to/downto b)")
                if "(" in data_type:
                    words = data_type.strip().split("(", maxsplit=1)
                    data_type = words[0].strip()
                    # Get the data width (remove closing bracket)
                    data_width = self.__get_data_width__(words[1][:-1])

                # That's all infos for this constant! Create and add it:
                self.found_constants.append(
                    Constant(
                        code_name=name,
                        data_type=data_type,
                        value=value,
                        data_width=data_width,
                    )
                )
                LOG.debug(
                    "Found constant '%s' of type '%s' with value '%s'",
                    name,
                    data_type,
                    value,
                )
                return ""

            LOG.error(
                (
                    "Malformed 'constant' declaration: '%s' in '%s': "
                    "Missing ':='!"
                ),
                self.line,
                file_obj.name,
            )
            return "malformed constant declaration"

        LOG.error(
            ("Malformed 'constant' declaration: '%s' in '%s': " "Missing ':'!"),
            self.line,
            file_obj.name,
        )
        return "malformed constant declaration"

    def __find_next_keyword__(self, file_obj) -> str:
        while True:
            line = self.__next_clean_line__(file_obj).strip()
            if line == "":
                return ""
            comp = [line.find(key) == 0 for key in self.keywords]
            if any(comp):
                self.line = line
                comp = [i for i, x in enumerate(comp) if x]
                return self.keywords[comp[0]]

    def __get_data_width__(self, parens: str) -> str:
        if "," in parens:  # For data widths with multiple dimensions
            data_width = []
            for width in parens.split(","):
                data_width.append(self.__get_data_width__(width))
            return [width for width in data_width if width is not None]
        # Determine the "direction" of the data width assignment
        dt_pos = parens.find(" downto ")
        to_pos = parens.find(" to ")
        if dt_pos > -1:
            spliton = "downto"
        elif to_pos > -1:
            spliton = "to"
        else:
            return None

        values = parens.split(spliton, 1)
        value0 = eval_vhdl_expr(values[0].strip().upper(), "data width")
        value1 = eval_vhdl_expr(values[1].strip().upper(), "data width")
        return Port.DataWidth(a=value0, sep=spliton, b=value1)

    @classmethod
    def __next_clean_line__(cls, file_obj, *, ret_on_semi: bool = False) -> str:
        while True:
            line = file_obj.readline().lower().strip(" \t")
            if line == "\n":
                continue
            if line == "":
                return line
            line = cls.__remove_vhdl_comment__(line)
            if (not ret_on_semi) and line.strip("\n();") == "":
                continue
            else:
                return line

    @classmethod
    def __peek_next_clean_line__(cls, file_obj, pos: int = -1) -> str:
        if pos == -1:
            this_pos = file_obj.tell()
        else:
            this_pos = pos
            file_obj.seek(this_pos)

        line = cls.__next_clean_line__(file_obj)
        file_obj.seek(this_pos)
        return line

    @classmethod
    def __next_clean_statement__(cls, file_obj, advance: bool = True) -> str:
        if not advance:
            pos = file_obj.tell()

        line = ""
        while ";" not in line:
            line += cls.__next_clean_line__(file_obj, ret_on_semi=True).strip(
                " \n"
            )
        line = line[: line.index(";")]
        if not advance:
            file_obj.seek(pos)

        return line

    @staticmethod
    def __remove_vhdl_comment__(line: str) -> str:
        comment = line.find("--")
        if comment > -1:
            line = line[0:comment]
        return line


## @}
