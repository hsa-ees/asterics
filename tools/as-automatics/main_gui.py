# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_automatics_module.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Thibaut Temkeng

Description:
Class representing an ASTERICS module part of an ASTERICS processing chain.
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
# @file as_automatics_module.py
# @ingroup automatics_intrep
# @author Philip Manke
# @brief Class representing a module of an ASTERICS processing chain.
# -----------------------------------------------------------------------------
import os
import sys
import copy
import pandas as pd
from PyQt5 import uic
import PyQt5.QtGui as qg
import PyQt5.QtCore as qc
import PyQt5.QtWidgets as qw
from collections import defaultdict
import as_automatics_logging as as_log
from asterics import Automatics_version
from as_automatics_generic import Generic
from as_automatics_module import AsModule
import as_automatics_exceptions as as_err
from as_automatics_env import AsAutomatics
from as_automatics_interface import Interface
from as_automatics_helpers import append_to_path
from as_automatics_port import Port, StandardPort
from as_automatics_module_lib import AsModuleLibrary
from as_automatics_proc_chain import AsProcessingChain
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from as_automatics_2d_window_module import AsWindowModule
from as_automatics_register import SlaveRegisterInterface


# Initialization: Get ASTERICS installation directory
asterics_home = None
try:
    asterics_home = os.environ.get("ASTERICS_HOME")
except KeyError:
    print("ERROR: ASTERICS_HOME not set!")
    print("Source the ASTERICS settings.sh file before running Automatics!")
    print("Use: source <path/to/asterics/>settings.sh")
    exit()

automatics_home = None
try:
    automatics_home = os.environ.get("ASTERICS_AUTOMATICS_HOME")
except KeyError:
    print("ERROR: ASTERICS_AUTOMATICS_HOME not set!")
    print("Source the ASTERICS settings.sh file before running Automatics!")
    print("Use: source <path/to/asterics/>settings.sh")
    exit()

sys.path.append(automatics_home)
as_log.init_log(loglevel_console="WARNING", loglevel_file="INFO")


class OutLog:
    def __init__(self, edit, out=None):
        """(edit, out=None) -> can write stdout, stderr to a
        QTextEdit.
        edit = QTextEdit
        out = alternate stream ( can be the original sys.stdout )
        """
        self.edit = edit
        self.out = None
        # self.flush = None

    def write(self, m):
        if self.edit:
            self.edit.moveCursor(qg.QTextCursor.End)
            self.edit.insertPlainText(m)
        if self.out:
            self.out.write(m)

    def flush(self):
        if self.edit:
            self.edit.moveCursor(qg.QTextCursor.End)
            self.edit.insertPlainText("")
        if self.out:
            self.out.flush()


class AlignDelegate(qw.QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super(AlignDelegate, self).initStyleOption(option, index)
        option.displayAlignment = qc.Qt.AlignCenter


class GUI(qw.QMainWindow):

    PORT_VIEW = "port"
    MODULE_VIEW = "mod"
    INTERFACE_VIEW = "inter"

    def __init__(self, auto: AsAutomatics):
        super(GUI, self).__init__()
        self.auto = auto
        self.module_names_dict = dict()
        self.generics = defaultdict(list)
        self.module_names_asterics = defaultdict(dict)
        self.module_names_automatics = defaultdict(dict)
        self.source_dir = sys.argv[0].rsplit("/", maxsplit=1)[0]
        self.root_path = self.source_dir.split("asterics")[0]
        uic.loadUi(os.path.join(self.source_dir, "gui.ui"), self)

        self.showAllModul.setChecked(True)
        self.showOther.clicked.connect(self.autofill)
        self.showAllModul.clicked.connect(self.autofill)
        self.completer.textChanged.connect(self.autofill)
        self.showAutomatics.clicked.connect(self.autofill)
        self.nn.clicked.connect(self.showAstericsFunction)
        self.completer.setPlaceholderText("Search for module")

        # Icons
        NEW_ICON = os.path.join(self.source_dir, "images", "new.png")
        EXIT_ICON = os.path.join(self.source_dir, "images", "exit.png")
        SAVE_ICON = os.path.join(self.source_dir, "images", "save.png")
        SHOW_ICON = os.path.join(self.source_dir, "images", "show.png")
        HIDE_ICON = os.path.join(self.source_dir, "images", "hide.png")
        START_ICON = os.path.join(self.source_dir, "images", "start.jpeg")
        SYSTEM_ICON = os.path.join(self.source_dir, "images", "system.png")
        CLOSE_ICON = os.path.join(self.source_dir, "images", "delete.png")
        self.EES_ICON = EES_ICON = os.path.join(
            self.source_dir, "images", "ees_logo_chip.png"
        )

        # Application icon and title
        self.setWindowIcon(qg.QIcon(EES_ICON))
        self.statusBar().setStyleSheet("color: orange;")
        backgroundColor = self.palette().color(qg.QPalette.Background).name()
        # Set module list header toolTip
        self.modCategoryColumn = self.modlist.horizontalHeaderItem(1)
        self.modDevStatusColumn = self.modlist.horizontalHeaderItem(3)
        self.modlist.horizontalHeaderItem(1).setToolTip("Module type:\n In ASTERICS there are the following modules type\n\n{}".format(
            AsModule.ModuleTypes.STR))

        self.modlist.horizontalHeaderItem(3).setToolTip("Development status:\n In ASTERICS there are the following development states\n\n{}".format(
            AsModule.DevStatus.STR))
        self.modlist.horizontalHeaderItem(5).setToolTip(
            "The link to the doxygene documentation")
        self.modlist.horizontalHeaderItem(6).setToolTip(
            "A rough overview of the module")

        # Symbol bar: File
        # Exit button
        self.actionExit.setIcon(qg.QIcon(EXIT_ICON))
        self.actionExit.triggered.connect(self.close)
        self.actionExit.setShortcut(qg.QKeySequence.Close)
        self.actionExit.setWhatsThis(
            self.tr("Click this option to create a new file.")
        )
        # Add repository button
        self.actionAddRepository.setEnabled(False)
        self.actionAddRepository.setIcon(qg.QIcon(NEW_ICON))
        self.actionAddRepository.setShortcut(qg.QKeySequence.New)
        self.actionAddRepository.triggered.connect(self.add_repo_action)

        # Symbol bar: View
        # Hide or show console view
        self.actionConsole.triggered.connect(
            lambda: self.hide_or_show_view("console")
        )
        # Hide or show System/Template view
        self.actionTemplate.triggered.connect(
            lambda: self.hide_or_show_view("template")
        )
        # Hide or show Port/Generic/Interface view
        self.actionPortInterface.triggered.connect(
            lambda: self.hide_or_show_view("port_interface")
        )
        # Hide or show Module description view
        self.actionModules_description.triggered.connect(
            lambda: self.hide_or_show_view("Modules_description")
        )
        # Restore alle views
        self.action_Restore_all_views.triggered.connect(
            lambda: self.hide_or_show_view("restore")
        )

        # Symbol bar: Wizard:
        # Start wizard button
        self.actionStartWizard.setIcon(qg.QIcon(START_ICON))
        self.actionStartWizard.setShortcut(qg.QKeySequence.Open)
        self.actionStartWizard.triggered.connect(self.show_wizard)
        # Close wizard button
        self.action_cLose_wizard.setIcon(qg.QIcon(CLOSE_ICON))
        self.action_cLose_wizard.triggered.connect(
            lambda:  self.wizard.close())

        # Symbol bar: Help
        self.menuHelp.setEnabled(False)
        # Save generated script
        self.saveTemplate.setFixedSize(30, 30)
        self.saveTemplate.setIcon(qg.QIcon(SAVE_ICON))
        self.saveTemplate.setIconSize(self.saveTemplate.size())
        # Center the text in table
        delegate = AlignDelegate(self.modlist)
        self.modlist.setItemDelegateForColumn(2, delegate)

        delegate = AlignDelegate(self.portInterfaceView)
        self.portInterfaceView.setItemDelegateForColumn(0, delegate)
        self.portInterfaceView.setItemDelegateForColumn(1, delegate)
        self.portInterfaceView.setItemDelegateForColumn(2, delegate)

        # Modules description view
        self.modDescriptionReduce.setIcon(qg.QIcon(CLOSE_ICON))
        self.modDescriptionReduce.clicked.connect(self.hide_or_show_view)
        self.modDescriptionReduce.setStyleSheet("background-color:#ffffff;")
        # Log/Console view
        self.log_clear.clicked.connect(self.clear_log)
        self.reduceConsole.setIcon(qg.QIcon(CLOSE_ICON))
        self.reduceConsole.clicked.connect(self.hide_or_show_view)
        self.reduceConsole.setStyleSheet("background-color:#ffffff;")
        # Template view
        self.reduceTemplate.setIcon(qg.QIcon(CLOSE_ICON))
        self.reduceTemplate.clicked.connect(self.hide_or_show_view)
        self.saveTemplate.clicked.connect(self.Save_template_content)
        self.reduceTemplate.setStyleSheet("background-color:#ffffff;")
        # Port/Interface view
        self.reducePI.setIcon(qg.QIcon(CLOSE_ICON))
        self.reducePI.clicked.connect(self.hide_or_show_view)
        self.reducePI.setStyleSheet("background-color:#ffffff;")
        self.clear_all_btn.clicked.connect(self.clear_all)
        self.clear_all_btn.setStyleSheet("background-color:#ff0000;")
        # self.portInterfaceView.setSelectionBehavior(qw.QAbstractItemView.SelectItems)
        self.portInterfaceView.setSelectionMode(
            qw.QAbstractItemView.SingleSelection
        )
        self.portInterfaceView.doubleClicked.connect(self.detailed_view_action)
        self.portInterfaceView.clicked.connect(self.inter_clicked)
        # Port view
        self.portList.setSelectionMode(qw.QAbstractItemView.SingleSelection)
        self.portList.doubleClicked.connect(self.detailed_view_action)
        self.portList.clicked.connect(self.port_clicked)
        self.portList.hide()

        # module list
        # self.modlist.setEditTriggers(qw.QAbstractItemView.NoEditTriggers)
        self.modlist.setSelectionBehavior(qw.QAbstractItemView.SelectRows)
        self.modlist.setSelectionMode(qw.QAbstractItemView.SingleSelection)
        self.modlist.itemSelectionChanged.connect(self.module_clicked)
        self.modlist.doubleClicked.connect(self.detailed_view_action)
        self.modlist.clicked.connect(self.module_clicked)
        # self.modlist.clicked.connect(self.detailed_view_action)

        # Search bar
        self.nn.setVisible(False)
        # Set up stdout
        # Save/Store original stdout
        self.stdout_orig = sys.stdout
        # Set up alternate stdouts
        self.infobox_out_stream = OutLog(self.infobox, self.stdout_orig)
        self.console_out_stream = OutLog(self.log_bro, self.stdout_orig)
        # Default output to console
        sys.stdout = self.console_out_stream

        # Status attributes
        self.crt_port = None
        self.crt_module = None
        self.crt_generic = None
        self.crt_interface = None
        self.view = self.MODULE_VIEW
        print("Hello from ASTERICS Automatics!")
        # Show GUI
        self.wizard = None
        self.show()

    def add_generic_info(self, module: AsModule):
        """ Add the generic information in the field named `Template`"""
        if len(module.generics) < 1:
            return
        if "as_sensor_ov7670" in module.entity_name:
            module_name = "camera"
        else:
            module_name = module.entity_name.replace(
                "as_mem", "").replace("as_", "")
        # self.setTextInView(
        #     '""" {0}\n {1} """\n'.format(
        #         module.brief_description, module.description
        #     ),
        #     "green",
        # )
        self.setTextInView('""" {0} """\n'.format(module.description),"green",)
        self.setTextInView("import ", "blue")
        self.setTextInView("asterics \nchain = asterics.new_chain()\n")
        self.setTextInView("\n#-------Module intantiations-------\n", "green")
        self.setTextInView(module_name + " = chain.add_module(")
        self.setTextInView("'{}'".format(module.entity_name), "orange")
        self.setTextInView(")\n\n#------Module configuration-----\n", "green")

        for gen in module.generics:
            if gen.comment.strip() != "":
                self.setTextInView("# " + gen.comment + "\n", "green")
            self.setTextInView(module_name + ".set_generic_value(")
            self.setTextInView("'{}'".format(gen.code_name), "orange")
            self.setTextInView(",")
            self.setTextInView("'{}'".format(gen.default_value), "orange")
            self.setTextInView(")\n")

    def add_generics_info(self, modules: [AsModule], connexion: dict = {}):
        """ Add the generic informations from the ASTERICS modules `modules`  in the field named `Template`"""

        self.template_bro.setText("")
        self.setTextInView(
            " # _____ Setup ASTERICS environment______\n", "green"
        )
        self.setTextInView("import ", "blue")
        self.setTextInView("asterics \nchain = asterics.new_chain()\n")
        self.setTextInView(
            "\n#_______ Define hardware modules ________\n", "green"
        )
        for module in modules:
            if "as_sensor_ov7670" in module.entity_name:
                module_name = "camera"
            else:
                module_name = module.entity_name.replace("as_mem", "")
                module_name = module_name.replace("as_", "")
            self.setTextInView(module_name + " = chain.add_module(")
            self.setTextInView("'" + module.entity_name + "'", "orange")
            self.setTextInView(")\n")
        for module in modules:
            self.setTextInView(
                '\n# Configuration of "{}" module\n'.format(
                    module.entity_name),
                "green",
            )
            if "as_sensor_ov7670" in module.entity_name:
                module_name = "camera"
            else:
                module_name = module.entity_name.replace("as_mem", "")
                module_name = module_name.replace("as_", "")
            for gen in module.generics:
                if gen.comment.strip() != "":
                    self.setTextInView(
                        "# {}\n".format(gen.comment.strip()), "green"
                    )
                self.setTextInView(module_name + ".set_generic_value(")
                self.setTextInView("'{}'".format(gen.code_name), "orange")
                self.setTextInView(",")
                self.setTextInView("'{}'".format(gen.default_value), "orange")
                self.setTextInView(")\n")
        if len(connexion.keys()) == 0:
            self.setTextInView(
                "\n# Todo modules connexion __________\n", "red")
        else:
            self.setTextInView("\n# Connect module \n", "green")
            for module_name in connexion:
                connect_tos = connexion[module_name]
                for connect_to in connect_tos:
                    if "as_sensor_ov7670" in module_name:
                        module_name = "camera"
                    else:
                        module_name = module_name.replace("as_mem", "")
                        module_name = module_name.replace("as_", "")

                    if "as_sensor_ov7670" in module_name:
                        connect_to = "camera"
                    else:
                        connect_to = connect_to.replace("as_mem", "")
                        connect_to = connect_to.replace("as_", "")
                    self.setTextInView(
                        "{}.connect({})\n".format(module_name, str(connect_to))
                    )

            self.setTextInView(
                "\n# Automatics output products \n#All possible output products are listed below and it is not necessary to generate all of them.\n#vivado\n", "green"
            )
            # Vivado
            self.setTextInView("chain.write_ip_core_xilinx(path=")
            self.setTextInView("'destination_dir'", "orange")
            self.setTextInView(", use_symlinks=")
            self.setTextInView("True", "blue")
            self.setTextInView(",force=")
            self.setTextInView("False", "blue")
            self.setTextInView(", module_driver_dirs=")
            self.setTextInView("False", "blue")
            self.setTextInView(")\n")
            # VEARS
            self.setTextInView("#Create link to the VEARS IP-Core\n", "green")
            self.setTextInView("asterics.vears(path=")
            self.setTextInView("'destination_dir'", "orange")
            self.setTextInView(", use_symlinks=")
            self.setTextInView("True", "blue")
            self.setTextInView(",force=")
            self.setTextInView("False", "blue")
            self.setTextInView(")\n")
            # Core
            self.setTextInView("#Core\n", "green")
            self.setTextInView("chain.write_asterics_core(path=")
            self.setTextInView("'destination_dir'", "orange")
            self.setTextInView(", use_symlinks=")
            self.setTextInView("True", "blue")
            self.setTextInView(",force=")
            self.setTextInView("False", "blue")
            self.setTextInView(", module_driver_dirs=")
            self.setTextInView("False", "blue")
            self.setTextInView(")\n")
            # System
            self.setTextInView("#System\n", "green")
            self.setTextInView("chain.write_system(path=")
            self.setTextInView("'destination_dir'", "orange")
            self.setTextInView(", use_symlinks=")
            self.setTextInView("True", "blue")
            self.setTextInView(",force=")
            self.setTextInView("False", "blue")
            self.setTextInView(", module_driver_dirs=")
            self.setTextInView("False", "blue")
            self.setTextInView(", add_vears=")
            self.setTextInView("False", "blue")
            self.setTextInView(")\n")
            # Graph
            self.setTextInView("#SVG graph\n", "green")
            self.setTextInView("chain.write_system_graph(out_file=")
            self.setTextInView("'output_file'", "orange")
            self.setTextInView(", show_toplevels=")
            self.setTextInView("False", "blue")
            self.setTextInView(",show_auto_inst=")
            self.setTextInView("False", "blue")
            self.setTextInView(", show_ports=")
            self.setTextInView("False", "blue")
            self.setTextInView(", show_unconnected=")
            self.setTextInView("False", "blue")
            self.setTextInView(", show_line_buffers=")
            self.setTextInView("False", "blue")
            self.setTextInView(")\n")

    def add_module(self, modname: str, reponame: str = ""):
        """ Add the ASTERICS module with name `modname` in the modulelist """

        mod = self.auto.library.get_module_template(modname, reponame)
        status_column = 3
        mod_type_column = 1

        self.module_names_dict[modname] = len(self.module_names_dict)
        y = self.modlist.rowCount()
        self.modlist.insertRow(y)

        tablerow = [
            mod.entity_name,
            mod.module_type.status,
            mod.repository_name,
            mod.dev_status.status,
            mod.module_category,
            "",
            mod.brief_description,
        ]  # one tablerow

        self.module_names_automatics[modname]["name"] = mod.entity_name
        self.module_names_automatics[modname]["mod_show"] = mod.show_in_browser
        self.module_names_automatics[modname]["repository"] = mod.repository_name
        self.module_names_automatics[modname]["dev_status"] = mod.dev_status.status
        self.module_names_automatics[modname]["mod_status"] = mod.module_type.status
        self.module_names_automatics[modname]["mod_descrip"] = mod.brief_description
        self.module_names_automatics[modname]["mod_comment"] = mod.brief_description
        self.module_names_automatics[modname]["dev_comment"] = mod.dev_status.comment
        self.module_names_automatics[modname]["module_category"] = mod.module_category

        for x in range(len(tablerow)):
            item = qw.QTableWidgetItem(tablerow[x])
            if x == 0:
                item.setToolTip(mod.brief_description)
            elif x == status_column:
                toolTip = mod.dev_status.comment
                item.setToolTip(toolTip)
            elif x == mod_type_column:
                toolTip = mod.module_type.comment
                item.setToolTip(toolTip)
            else:
                item.setToolTip(tablerow[x])
            self.modlist.setItem(y, x, item)

    def add_repo_action(self):
        """Add a folder as a new repository to the module library.
        Add all new modules to the module list."""
        folder = self.add_repo_folder_dialog()
        if not folder:
            print("Invalid folder selection!\nAborted!")
        else:
            print("Scanning for ASTERICS modules in '{}'".format(folder))
            mods = self.auto.add_module_repository(folder, "user")
            if mods:
                for modname in mods:
                    self.add_module(modname, "user")
                self.modlist.resizeColumnsToContents()
                print(
                    "Added {} modules to repository 'user'!".format(len(mods))
                )
            else:
                print("No modules found in '{}'.".format(folder))

    def add_repo_folder_dialog(self):
        """Allows the user to select a folder and returns the path."""
        options = qw.QFileDialog.Options()
        options |= qw.QFileDialog.DontUseNativeDialog
        folder_name = qw.QFileDialog.getExistingDirectory(
            self, "Select already exit directory", "", options=options
        )
        return folder_name

    def autofill(self):
        """fills in the module list table according to the text entered in the search field"""
        searchText = self.completer.text().lower()
        self.portList.hide()
        modNames = []
        for modName in self.module_names_automatics:
            rowData = self.module_names_automatics[modName]
            if (self.showOther.isChecked() and rowData["mod_show"]) or (
                self.showAutomatics.isChecked() and not rowData["mod_show"]
            ):
                continue

            modName = modName.lower()
            if searchText == modName:
                if self.modlist.rowCount() != 1:
                    modNames.append(modName)
                    continue
                else:
                    self.modlist.selectRow(0)
                    selectedRow = self.modlist.selectedItems()[0]
                    self.modlist.scrollToItem(selectedRow)
                    return
            elif (
                searchText in modName
                or searchText in rowData["mod_status"].lower()
                or searchText in rowData["dev_status"].lower()
                or searchText in rowData["module_category"].lower()
            ):
                modNames.append(modName)
        if len(modNames) == 0:
            modNames = list(self.module_names_dict.keys())
            if len(searchText) > 0:
                print("The word `{}` can not fund".format(searchText))
        self.fillModuleListTable(modNames)
        if len(modName) == 1:
            self.modlist.selectRow(0)
            selectedRow = self.modlist.selectedItems()[0]
            self.modlist.scrollToItem(selectedRow)

    def build_interlist(self, module: AsModule):
        """
        Add the interface informations of ASTERICS module `module` in the table interface. \n

        """
        self.template_bro.setText("")
        intercol = copy.copy(module.interfaces)
        if isinstance(module, AsWindowModule):
            intercol.extend(module.window_interfaces)
        # intercol.extend(module.register_ifs)
        intercol.extend(module.ports)
        intercol.extend(module.standard_ports)
        intercol.extend(module.generics)

        for inter in intercol:
            if isinstance(inter, Port):
                port_type = (
                    "StandardPort"
                    if isinstance(inter, StandardPort)
                    else "Port"
                )
                tablerow = [inter.name, port_type, inter.direction, ""]
            elif isinstance(inter, Generic):
                tablerow = [
                    inter.code_name,
                    "Generic",
                    str(inter.default_value),
                    inter.comment.strip(),
                ]

            elif isinstance(inter, SlaveRegisterInterface):
                tablerow = [str(inter), inter.type, inter.direction, ""]
            else:
                tablerow = [str(inter), inter.type, inter.direction, ""]
            y = self.portInterfaceView.rowCount()
            self.portInterfaceView.insertRow(y)
            for x in range(len(tablerow)):
                item = qw.QTableWidgetItem(tablerow[x])
                item.setToolTip(tablerow[x])
                self.portInterfaceView.setItem(y, x, item)
        self.portInterfaceView.resizeColumnsToContents()

        print(
            "Showing {} interfaces/ports/generics of module '{}'".format(
                self.portInterfaceView.rowCount(), self.crt_module.entity_name
            )
        )

        self.add_generic_info(module)

    def build_modlist(self):
        """Add all modules in the module library to the module list."""
        library = self.auto.library
        module_names = sorted(library.get_module_names())
        # print("Current number of ASTERICS modules: ", len(module_names))
        for modname in module_names:
            self.add_module(modname)
        self.modlist.resizeColumnsToContents()

        self.completer.setCompleter(
            qw.QCompleter(sorted(self.module_names_automatics))
        )
        # print("Loaded {} modules!".format(self.modlist.rowCount()))
        self.showAllModul.setText("All({})".format(self.modlist.rowCount()))
        df = pd.DataFrame.from_dict(self.module_names_automatics).T
        self.showAutomatics.setText(
            "Automatics({})".format(len(df[df["mod_show"] == True]))
        )
        self.showOther.setText(
            "Other({})".format(
                self.modlist.rowCount() - len(df[df["mod_show"] == True])
            )
        )

    def clear_all(self):
        """Clear the GUI information"""

        self.infobox.setText("")
        self.log_bro.setText("")
        self.portList.setRowCount(0)
        self.portInterfaceView.setRowCount(0)
        self.template_bro.setText("")

    def clear_log(self):
        """Clear the log field in the GUI"""
        self.log_bro.setText("")

    def close(self):
        """CLose the ASTERICS GUI"""
        sys.stdout = self.stdout_orig
        super().close()

    def closeEvent(self, event):
        self.wizard.close()
        event.accept()

    def detailed_view_action(self):
        if self.view is self.PORT_VIEW:
            print("Already in most detailed view!")
        elif self.view is self.MODULE_VIEW:
            if self.crt_module is None:
                print("No module selected!")
                return False
            # Remove all rows of the interface list
            self.portInterfaceView.setRowCount(0)
            self.build_interlist(self.crt_module)
            self.portInterfaceView.show()
            self.view = self.INTERFACE_VIEW
            self.modlist_label.setText(
                "Interfaces of {}:".format(self.crt_module)
            )
            # self.details_button.hide()
            # self.overview_button.show()
        else:
            if self.crt_interface is None:
                return False
            print("Showing ports of interface '{}'.")
            # TODO
        return True

    def fillModuleListTable(self, modNames):
        """Fill the module list table with modules from `modNames`"""
        self.modlist.setRowCount(0)
        for row, modname in enumerate(modNames):
            self.modlist.insertRow(row)
            name = qw.QTableWidgetItem(
                self.module_names_automatics[modname]["name"])
            name.setToolTip(
                self.module_names_automatics[modname]["mod_descrip"])

            mod_status = qw.QTableWidgetItem(
                self.module_names_automatics[modname]["mod_status"])
            mod_status.setToolTip(
                self.module_names_automatics[modname]["mod_comment"])

            repository = qw.QTableWidgetItem(
                self.module_names_automatics[modname]["repository"])
            repository.setToolTip(
                self.module_names_automatics[modname]["repository"])

            dev_status = qw.QTableWidgetItem(
                self.module_names_automatics[modname]["dev_status"])
            dev_status.setToolTip(
                self.module_names_automatics[modname]["dev_comment"])

            module_category = qw.QTableWidgetItem(
                self.module_names_automatics[modname]["module_category"])
            mod_descrip = qw.QTableWidgetItem(
                self.module_names_automatics[modname]["mod_descrip"])
            mod_descrip.setToolTip(
                self.module_names_automatics[modname]["mod_comment"])

            self.modlist.setItem(row, 0, name)
            self.modlist.setItem(row, 1, mod_status)
            self.modlist.setItem(row, 2, repository)
            self.modlist.setItem(row, 3, dev_status)
            self.modlist.setItem(row, 4, module_category)
            self.modlist.setItem(row, 5, mod_descrip)

    def generate_asterics_systems(self, modules: list, connexion: dict = {}):
        """Generate a ASTERICS system from the ASTERICS modules `modules`.\n
        Parameters:\n
        modules: The modules involved in the system.\n
        connexion: Describes how the modules are connected

        """

        as_modules = []
        for module in modules:
            try:
                mod = self.auto.library.get_module_template(module, "default")
                as_modules.append(mod)
            except:
                self.writeException("The system can not be generated!")
                return
        self.add_generics_info(as_modules, connexion)
        print("System generated!")

    def generic_clicked(self, from_interlist: tuple):
        genericname, _, defaultval = from_interlist
        gen = self.crt_module.get_generic(genericname, suppress_error=True)
        if gen:
            self.crt_port = None
            self.crt_generic = gen
            self.crt_interface = None
            select_text = (
                "Generic '{}' ({}) with default value [{}] of " "module '{}'"
            ).format(
                genericname,
                gen.data_type,
                defaultval,
                self.crt_module.entity_name,
            )
            print(str(gen))
            self.status.setText(select_text)
            self.infobox.setText(select_text)
        else:
            print("Generic '{}' not found!".format(genericname))

    @staticmethod
    def get_selected_item(table: qw.QTableWidget) -> tuple:
        if len(table.selectedItems()) == 0:
            return ("", "", "")
        for item in table.selectedItems():
            crt_row = table.row(item)
        name = table.item(crt_row, 0).text()
        d1 = table.item(crt_row, 1).text()
        d2 = table.item(crt_row, 2).text()
        return (name, d1, d2)

    def hide_or_show_view(self, message: str = None):
        """Hidden or show a view"""
        if message:
            message = message.lower()
        else:
            message = ""
        button_text = self.sender().text()
        # self.frame_console.setStyleSheet('background-color: orange')
        # Restore all view
        if "restore" in message:
            self.frame_infobox.show()
            self.frame_console.show()
            self.frame_details.show()
            self.frame_template.show()
            self.frame_right.show()
            self.frame_mittle.show()
            self.actionConsole.setStatusTip("Hide the Console view")
            self.actionTemplate.setStatusTip("Hide the Template view")
            self.actionPortInterface.setStatusTip(
                "Hide the Port/Interface view"
            )
            self.actionModules_description.setStatusTip(
                "Hide the Modules description view"
            )
        # hidden view
        elif button_text == "reducePI":
            self.frame_details.hide()
            if not self.frame_console.isVisible():
                self.frame_mittle.hide()
            print("Details view are hidden")
        elif button_text == "reduceConsole":
            self.frame_console.hide()
            if not self.frame_details.isVisible():
                self.frame_mittle.hide()
            print("Console view are hidden")
        elif button_text == "reduceTemplate":
            self.frame_template.hide()
            if not self.frame_infobox.isVisible():
                self.frame_right.hide()
            print("Template view are hidden")
        elif button_text == "reduceMD":
            self.frame_infobox.hide()
            if not self.frame_template.isVisible():
                self.frame_right.hide()
            print("Infobox view are hidden")
        # Hidden or show
        elif "port" in message or "interface" in message:
            if self.frame_details.isVisible():
                self.frame_details.hide()
                if not self.frame_console.isVisible():
                    self.frame_mittle.hide()
                print("Port/Interface view are hidden")
                self.actionPortInterface.setStatusTip(
                    "Show the Port/Interface view"
                )
            else:
                self.frame_mittle.show()
                self.frame_details.show()
                print("Show Port/Interface view ")
                self.actionPortInterface.setStatusTip(
                    "Hide the Port/Interface view"
                )
        elif "console" in message:
            if self.frame_console.isVisible():
                self.frame_console.hide()
                if not self.frame_details.isVisible():
                    self.frame_mittle.hide()
                print("Console view are hidden")
                self.actionConsole.setStatusTip("Show the console view")
            else:
                self.frame_mittle.show()
                self.frame_console.show()
                print("Show Console view ")
                self.actionConsole.setStatusTip("Hide the console view")
        elif "template" in message:
            if self.frame_template.isVisible():
                self.frame_template.hide()
                if not self.frame_infobox.isVisible():
                    self.frame_right.hide()
                print("Template view are hidden")
                self.actionTemplate.setStatusTip("Show the template view")
            else:
                self.frame_right.show()
                self.frame_template.show()
                print("Show Template view ")
                self.actionTemplate.setStatusTip("Hide the template view")
        elif "module" in message or "description" in message:
            if self.frame_infobox.isVisible():
                self.frame_infobox.hide()
                if not self.frame_template.isVisible():
                    self.frame_right.hide()
                print("Modules description view are hidden")
                self.actionModules_description.setStatusTip(
                    "Show the Modules description view"
                )
            else:
                self.frame_right.show()
                self.frame_infobox.show()
                print("Show Modules description view ")
                self.actionModules_description.setStatusTip(
                    "Hide the Modules description view"
                )

    def inter_clicked(self):
        """Print brief description and select the interface clicked in the
        QTableWidget - interface list"""
        # print("\nTEMKENG interface list")
        self.view = self.INTERFACE_VIEW
        intername, intertype, direction = self.get_selected_item(
            self.portInterfaceView
        )
        if intertype in ("Port", "StandardPort"):
            self.port_clicked((intername, intertype, direction))
        elif intertype == "Generic":
            self.generic_clicked((intername, intertype, direction))
        else:
            if isinstance(self.crt_interface, SlaveRegisterInterface):
                inter = self.crt_module.get_slave_register_interface(intername)
            inter = self.crt_module.get_interface(
                intername, direction, intertype
            )
            if inter:
                self.crt_port = None
                self.crt_generic = None
                self.crt_interface = inter
                select_text = "Selected interface '{}' of module '{}'".format(
                    intername, self.crt_module.entity_name
                )
                self.status.setText(select_text)
                print(str(inter))
                self.infobox.setText(
                    "Interface '{}' ({}) with direction '{}' of:\n{}".format(
                        intername, intertype, direction, str(self.crt_module)
                    )
                )
            else:
                print("No info for interface '{}'".format(intername))
        self.list_details_action()

    def list_details_action(self):
        self.infobox.setText("")
        if self.view is self.PORT_VIEW:
            print(
                "Listing details of port '{}'".format(self.crt_port.code_name)
            )
            sys.stdout = self.infobox_out_stream
            print("\n", self.crt_port)
            print("\nDefault port rules:")
            self.crt_port.list_ruleset()
            print("\nOf interface:")
            self.crt_interface.print_interface(True)
            print("\nOf module:")
            print(self.crt_module)
        elif self.view is self.MODULE_VIEW:
            if self.crt_module is None:
                print("No module selected!")
            else:
                mod = self.crt_module
                print("Listing details for {}".format(mod))
                # Switch stdout to infobox:
                sys.stdout = self.infobox_out_stream
                mod.list_module(2)

                print("\nToplevel file: {}".format(mod.files[-1]))
                if len(mod.files) > 1:
                    print("\nHDL files:")
                    for filename in mod.files[:-1]:
                        print("  - {}".format(filename))
                if mod.dependencies:
                    print("\nDependencies:")
                    for dep in mod.dependencies:
                        print("  - {}".format(dep))
        else:
            if self.crt_generic:
                print(
                    "Listing details for generic '{}'".format(
                        self.crt_generic.code_name
                    )
                )
                sys.stdout = self.infobox_out_stream
                print(self.crt_generic)
                print("\nOf module:")
                print(self.crt_module)

            elif self.crt_port:
                print(
                    "Listing details of port '{}'".format(
                        self.crt_port.code_name
                    )
                )
                sys.stdout = self.infobox_out_stream
                print(self.crt_port)
                print("\nDefault port rules:")
                self.crt_port.list_ruleset()
                print("\nOf module:")
                print(self.crt_module)
            elif self.crt_interface:
                intername = self.crt_interface.name
                if not intername:
                    intername = self.crt_interface.type
                print("Listing details for interface '{}'".format(intername))
                sys.stdout = self.infobox_out_stream
                self.crt_interface.print_interface(True)
                print("\nOf module:")
                print(self.crt_module)
            else:
                print("Nothing selected!")
        self.infobox.moveCursor(qg.QTextCursor.Start)
        # Switch stdout back to console
        sys.stdout = self.console_out_stream

    def module_clicked(self):
        """Print brief description and select the module clicked in the
        QTableWidget - module list"""
        self.modlist_label.setText("ASTERICS Module List:")

        modname, _, modrepo = self.get_selected_item(self.modlist)

        if (self.crt_module is None) or (
            modname != self.crt_module.entity_name
        ):
            # print("Looking up {} in {}...".format(modname, modrepo))

            module = self.auto.library.get_module_template(modname, modrepo)
            print(str(module))
            if module:
                self.crt_module = module
                self.status.setText(
                    "Selected module: {}".format(module.entity_name)
                )
                self.infobox.setText(
                    "{} from repository {}".format(module, modrepo)
                )
            else:
                print("No info for module '{}'.".format(modname))
                return
            # Remove all rows of the interface list
            self.portInterfaceView.setRowCount(0)
            self.build_interlist(self.crt_module)
            # self.modlist.hide()
            self.portInterfaceView.show()
            # self.view = self.INTERFACE_VIEW
            # self.modlist_label.setText(
            #     "Interfaces of {}:".format(self.crt_module))
            self.view = self.MODULE_VIEW
            self.list_details_action()

    def module_overview_action(self):
        self.portInterfaceView.hide()
        self.portlist.hide()
        self.modlist.show()
        self.infobox.setText("")
        self.console.append("\nModule overview...\n")
        self.view = self.MODULE_VIEW
        self.crt_interface = None
        self.crt_port = None
        self.crt_generic = None
        if self.crt_module:
            self.module_clicked()
        self.modlist_label.setText("ASTERICS Module List:")
        # self.overview_button.hide()
        self.details_button.show()

    def port_clicked(self, from_interlist: tuple = None):
        # print("\nTEMKENG  port list")
        if from_interlist:
            portname, porttype, direction = from_interlist
            port = self.crt_module.get_port(portname, suppress_error=True)
        else:
            portname, porttype, direction = self.get_selected_item(
                self.portlist
            )
            port = self.crt_interface.get_port(portname, suppress_error=True)
        if port:
            self.crt_port = port
            self.crt_generic = None
            self.crt_interface = None
            if not from_interlist:
                select_text = (
                    "{} '{}' ({}) with direction '{}' of "
                    "interface '{}' of module '{}'"
                ).format(
                    porttype,
                    portname,
                    port.code_name,
                    direction,
                    self.crt_interface.name,
                    self.crt_module.entity_name,
                )
            else:
                select_text = (
                    "Port '{}' ({}) with direction '{}' of " "module '{}'"
                ).format(
                    portname,
                    port.code_name,
                    direction,
                    self.crt_module.entity_name,
                )
            self.status.setText(select_text)
            print(str(port))
            self.infobox.setText(
                "Port '{}' ({}) with direction '{}' of:\n{}".format(
                    portname, port.code_name, direction, str(self.crt_module)
                )
            )
        else:
            print("Port '{}' not found!".format(portname))

    def Save_template_content(self):
        """
        Save the content from the template view in a selected file.
        """
        options = qw.QFileDialog.Options()
        options |= qw.QFileDialog.DontUseNativeDialog
        filename = qw.QFileDialog.getSaveFileName(
            None,
            "Select destination folder and file name",
            "",
            "Python files (*.py);; All files (*.*)",
            options=options,
        )[0]
        if filename == "":
            print("You have not selected any file!")
            return
        if "." not in filename:
            filename += ".py"
        with open(filename, "w") as file:
            file.write(self.template_bro.toPlainText())
            print("Content was saved with success in :")
            print("Path: ", filename)
        return

    def setTextInView(self, text: str = "", color: str = "black", view=None):
        if view is None:
            view = self.template_bro
        view.setTextColor(qg.QColor(color))
        view.textCursor().insertText(text)
        view.setTextColor(qg.QColor("black"))

    def show_wizard(self):
        """Show the wizard"""
        if self.wizard:
            self.wizard.close()

        self.wizard = Wizard(self)
        self.wizard.show()
        print("The wizard is open")

    def showAstericsFunction(self):
        import types
        import asterics

        self.infobox.setText("")
        sys.stdout = self.infobox_out_stream
        var = vars(asterics)
        result = dict()
        for key in var:
            if (
                type(var[key]) != str
                and var[key] is not None
                and isinstance(var[key], types.FunctionType)
                and var[key].__doc__ is not None
            ):
                result[key] = var[key].__doc__
                self.setTextInView(key + ":", "orange", self.infobox)
                self.setTextInView(" ", "black", self.infobox)
                print("\n{}".format(var[key].__doc__))

        sys.stdout = self.console_out_stream
        self.frame_mittle.hide()
        self.frame_infobox.show()
        self.frame_template.hide()

    def writeException(self, message):
        self.log_bro.setTextColor(qg.QColor("red"))
        self.log_bro.textCursor().insertText(message)
        self.log_bro.setTextColor(qg.QColor("black"))
        self.log_bro.textCursor().insertText(".\n")


class Wizard(qw.QWizard):
    # Bild-Entzerrung
    # Feature-Detektion,
    ANSWER = "@"
    MODULE = "@@"
    SUBTITLE = "::"
    SYSTEM = ">>>>"
    QUESTIONS = "---"
    COMMENT = "@comment"
    NUM_PAGES = 6

    (
        PageIntro_nr,
        ExistedSystemPage_nr,
        InputPage_nr,
        OutputPage_nr,
        ChooseModulePage_nr,
        ConnexionPage_nr,
    ) = range(NUM_PAGES)

    class ChooseModulePage(qw.QWizardPage):
        def __init__(self, owner=None):
            super().__init__(owner)
            self.owner = owner
            self.modules = set()
            combo = qw.QComboBox()
            self.gui = self.owner.gui
            layout = qw.QVBoxLayout()
            layout1 = qw.QHBoxLayout()
            info_btn = qw.QPushButton()
            INFORMATION_ICON = os.path.join(
                self.gui.source_dir, "images", "information.jpg"
            )

            self.setLayout(layout)
            self.helpMessage = "1.Here you should select all modules that will be needed to process the input.\n2.click on `Next` button to continue."
            self.setTitle("Choose the ASTERICS Modules")
            layout.addWidget(
                qw.QLabel(
                    "\nA large number of modules that you can insert into your image processing chain are available in ASTERICS\n"
                )
            )

            df = pd.DataFrame.from_dict(self.gui.module_names_automatics).T
            df = df[df["mod_show"] == True]
            modules = list(df.index)
            modules.remove("as_sensor_ov7670")
            modules.remove("as_memreader")
            modules.remove("as_memwriter")
            combo.addItems(modules)
            layout1.addWidget(combo)
            # layout1.addWidget(info_btn)
            layout.addLayout(layout1)

            combo.activated[str].connect(self.addModule)
            for i in range(combo.count()):
                combo.setItemData(i, qc.Qt.AlignCenter,
                                  qc.Qt.TextAlignmentRole)
            self.layout = layout
            # infobox view
            info_btn.setIcon(qg.QIcon(INFORMATION_ICON))
            # info_btn.setStyleSheet("background-color:#ffffff;")
            info_btn.setFixedSize(30, 30)
            info_btn.setIconSize(info_btn.sizeHint())

            self.adjustSize()

        def addResult(self):
            if (
                self.sender().text()
                in self.owner.results[Wizard.ChooseModulePage_nr]
            ):
                self.owner.results[Wizard.ChooseModulePage_nr].remove(
                    self.sender().text()
                )
                print("Remove choice to result")
            else:
                self.owner.results[Wizard.ChooseModulePage_nr].add(
                    self.sender().text()
                )
                print("Add choice to result")
            print(self.owner.results)

        def addModule(self):

            if type(self.sender()) == qw.QComboBox:
                text = self.sender().currentText()
                if text not in self.owner.results[Wizard.ChooseModulePage_nr]:
                    self.owner.results[Wizard.ChooseModulePage_nr].add(text)
                    for cb in self.modules:
                        if text == cb.text():
                            cb.setChecked(True)
                            return
                    checkbox = qw.QCheckBox(text)
                    self.modules.add(checkbox)
                    checkbox.setChecked(True)
                    self.layout.addWidget(checkbox)
                    checkbox.stateChanged.connect(self.addModule)
                    print("Module added")
            else:
                checkbox = self.sender()
                if checkbox.isChecked():
                    print("Module added")
                    self.owner.results[Wizard.ChooseModulePage_nr].add(
                        checkbox.text()
                    )
                else:
                    print("Module removed")
                    self.owner.results[Wizard.ChooseModulePage_nr].remove(
                        checkbox.text()
                    )

        def setVisible(self, visible):
            qw.QWizardPage.setVisible(self, visible)

            if visible:
                btnList = [
                    qw.QWizard.Stretch,
                    qw.QWizard.BackButton,
                    qw.QWizard.NextButton,
                    qw.QWizard.FinishButton,
                    qw.QWizard.CancelButton,
                    qw.QWizard.HelpButton,
                ]
                self.wizard().setButtonLayout(btnList)
                # self.owner.infobox.show()

            else:
                self.owner.infobox.hide()
                self.owner.infobox.close()
            self.adjustSize()

        def closeEvent(self, event):
            event.accept()
            print("The dialog is closed")

    class ConnexionPage(qw.QWizardPage):
        """ Establishes the connection between the previously modules, that selected in `ChooseModulePage`  """

        def __init__(self, owner=None):
            super().__init__(owner)

            self.modules = []
            self.owner = owner
            self.gui = self.owner.gui
            self.table = qw.QTableWidget()
            self.layouts = qw.QVBoxLayout()
            self.modules_list = qw.QLabel()
            self.add_btn = qw.QPushButton("Add connection")
            self.title_message = qw.QLabel(
                "\nEstablishes the connection between the previously selected modules"
            )
            self.legend = qw.QLabel(
                '<font color="green">Input module</font>: <font color="red">Intermediate module</font>:<font color="orange">Output module</font>'
            )

            self.setLayout(self.layouts)
            self.layouts.addWidget(self.title_message)
            self.layouts.addWidget(self.modules_list)
            self.layouts.addWidget(self.table)
            self.layouts.addWidget(self.add_btn)
            self.layouts.addWidget(self.legend)
            self.table.setColumnCount(2)
            self.table.setHorizontalHeaderLabels(["Modul", "Connect to"])
            self.helpMessage = "-Complete the column `connect to` of the `connexion` table with names of module.\n -click on 'Next' button to continue"
            self.helpMessage = self.tr(
                "-Now the selected ASTERICS modules should be connected.\n "
                "The connection between two modules is made in the column 'connect to'.\n\n"
                "-Assume that we have the following configuration:\n"
                "Module\n"
                "1.as_pipeline_flush\n"
                "2.as_pipeline_row\n"
                "3.as_pixel_conv\n"
                "4.as_pixel_diff\n\n"
                "for example, to connect 'as_pipeline_flush' with 'as_pixel_diff' ( as_pipeline_flush --> as_pixel_diff), (as_pipeline_flush , 4) is inserted in the table 'connexion'.\n"
                "-click on 'Generate' button to generate system.\n\n"
                "Note: -1 means that the module has no outgoing edge \nYou must complete the table `connexion` so that everything works well.\n"
            )
            self.setTitle("Connect the selected ASTERICS modules")
            self.finish = self.owner.button(qw.QWizard.FinishButton)
            self.generate = self.owner.button(qw.QWizard.CustomButton1)
            self.add_btn.clicked.connect(self.addRow)
            self.adjustSize()

        def addRow(self):
            self.table.insertRow(self.table.rowCount())

        def generateSystem(self):

            result_dict = defaultdict(dict)
            for y in range(self.table.rowCount()):
                mod = self.table.item(y, 0)
                connect = self.table.item(y, 1)
                if mod is not None and connect is not None:
                    result_dict[str(y)]["mod"] = mod.text()
                    result_dict[str(y)]["connect"] = connect.text()

            connexion = defaultdict(list)
            for key in list(result_dict.keys()):
                mod_connect_dict = result_dict[key]
                connect_to = mod_connect_dict["connect"]
                if connect_to != "-1":
                    if "mod" not in mod_connect_dict.keys():
                        self.gui.writeException(
                            "The system cannot be generated. The `connexion` table must be filled in correctly"
                        )
                        return
                    mod = mod_connect_dict["mod"]
                    try:
                        connect_to = result_dict[connect_to]["mod"]
                        connexion[mod].append(connect_to)
                    except:
                        self.gui.writeException(
                            "The system cannot be generated. The `connexion` table must be filled in correctly"
                        )
                        return

            string = "The system are successful generated\nYou can find and modified the generated script in Template view. At the end you can save the script to main memory by clicking the `save as...` button"
            error = "The system was not generated"
            try:
                self.gui.generate_asterics_systems(self.modules, connexion)
                qw.QMessageBox.information(
                    self, self.tr("ASTERICS GUI"), string
                )
                if self.sender() == self.finish:
                    self.owner.close()
                self.gui.activateWindow()
                self.gui.frame_mittle.hide()
                self.gui.frame_infobox.hide()
            except Exception:
                # qw.QMessageBox.warning(self, self.tr("ASTERICS GUI"), self.warning_msg.format(key))
                qw.QMessageBox.warning(self, self.tr("ASTERICS GUI"), error)

        def setVisible(self, visible):
            qw.QWizardPage.setVisible(self, visible)

            if visible:
                self.wizard().setButtonText(
                    qw.QWizard.CustomButton2, self.tr("&Preview")
                )
                self.wizard().setButtonText(
                    qw.QWizard.CustomButton1, self.tr("&Generate")
                )
                self.wizard().setOption(qw.QWizard.HaveCustomButton1, True)
                self.wizard().setOption(qw.QWizard.HaveCustomButton2, True)
                self.generate.clicked.connect(self.generateSystem)
                self.finish.clicked.connect(self.generateSystem)
                btnList = [
                    qw.QWizard.Stretch,
                    qw.QWizard.BackButton,
                    qw.QWizard.NextButton,
                    qw.QWizard.CustomButton2,
                    qw.QWizard.CustomButton1,
                    qw.QWizard.FinishButton,
                    qw.QWizard.CancelButton,
                    qw.QWizard.HelpButton,
                ]
                self.wizard().setButtonLayout(btnList)
                self.modules = list(
                    (
                        self.owner.results[Wizard.InputPage_nr]
                        | self.owner.results[Wizard.ChooseModulePage_nr]
                    )
                    | self.owner.results[Wizard.OutputPage_nr]
                )

                inputs = list(self.owner.results[Wizard.InputPage_nr])
                outputs = list(self.owner.results[Wizard.OutputPage_nr])
                interModules = list(
                    self.owner.results[Wizard.ChooseModulePage_nr]
                )
                self.modules = inputs + interModules + outputs
                s = "Module:\n"
                for index, module in enumerate(self.modules):
                    s += "{}.{}\n".format(index + 1, module)
                s += "\nConnexion:"

                self.table.setRowCount(0)
                self.modules_list.setText(s)
                for i, module in enumerate(self.modules):
                    if i < len(inputs):
                        color = "green"
                    elif i < len(inputs) + len(interModules):
                        color = "red"
                    else:
                        color = "orange"
                    y = self.table.rowCount()
                    self.table.insertRow(y)

                    tablerow = [
                        module,
                        str(i + 1 if i + 1 != len(self.modules) else -1),
                    ]

                    for x in range(len(tablerow)):
                        item = qw.QTableWidgetItem(tablerow[x])
                        if x + 1 == len(tablerow) and int(tablerow[x]) == -1:
                            item.setToolTip(
                                tablerow[0] +
                                " has no outgoing edges/connexion"
                            )
                        elif x + 1 == len(tablerow):
                            item.setToolTip(
                                tablerow[0]
                                + " are connect to "
                                + self.modules[int(tablerow[x])]
                            )
                        else:
                            item.setToolTip(tablerow[x])
                        self.table.setItem(y, x, item)
                        self.table.item(y, x).setForeground(qg.QColor(color))
                self.table.resizeColumnsToContents()
                self.adjustSize()
            else:
                self.owner.infobox.hide()
                self.owner.infobox.close()
                btnList = [
                    qw.QWizard.Stretch,
                    qw.QWizard.BackButton,
                    qw.QWizard.NextButton,
                    qw.QWizard.FinishButton,
                    qw.QWizard.CancelButton,
                    qw.QWizard.HelpButton,
                ]
                self.wizard().setButtonLayout(btnList)
                try:
                    # self.wizard().customButtonClicked.disconnect()
                    self.generate.clicked.disconnect()
                    self.finish.clicked.disconnect()
                except Exception:
                    pass

        def closeEvent(self, event):
            event.accept()
            print("The dialog is closed")

    class ExistedSystemPage(qw.QWizardPage):
        """
        Here some systems are shown, which can be created with ASTERICS.
        """

        def __init__(self, owner=None):
            super().__init__(owner)
            self.owner = owner
            self.gui = owner.gui
            self.modList = qw.QLabel()
            self.overview = qw.QLabel()
            self.modListTitle = qw.QLabel()
            self.systems = defaultdict(dict)
            self.next_btn = self.owner.button(qw.QWizard.NextButton)
            self.preview = self.owner.button(qw.QWizard.CustomButton2)
            self.generateButton = self.owner.button(qw.QWizard.CustomButton1)
            self.warning_msg = "Informations about the {} system is regrettably not yet available"
            self.generateButton.setToolTip(
                "Generates the system \nIf the system is generated successfully, then the generated script is displayed in the template view."
            )
            self.preview.setToolTip(
                "This option is not currently supported, but is under development.\nWith this option it should be possible to visualize the system as a graph."
            )
            self.setTitle("ASTERICS systems")
            self.helpMessage = self.tr(
                "1. Choose one of the items in the list of systems\n2. Click on the `Detail` button to get more details \nabout the selected system"
            )
            # Comment
            self.systems["Inverter"][
                "comment"
            ] = "The inverter system allow you to invert pixel of an image"
            self.systems["New system..."][
                "comment"
            ] = " This option allows you to create your own ASTERICS system from scratch. "

            self.systems["Image differencing"]["comment"] = self.tr(
                "This ASTERICS reference design implements a set of ASTERICS modules to "
                "perform image differencing on subsequent camera images.\n"
                "Images are acquired by an OmniVision OV7670 image sensor.\n"
                "This imaga data stream is split to two streams:\n"
                "1) The original image is stored unmodified to main memory.\n"
                "2) The stream data and data from the previous image, fetched from main "
                "memory, are synchronized prior to calculating pixel differences. \n"
                "The resulting difference image is also stored to main memory.\n"
                "The VEARS ipcore is used to display the images on a monitor."
            )
            self.systems["Canny_pipeline"]["comment"] = self.tr(
                "This ASTERICS reference design implements a set of ASTERICS modules to "
                "calculate a Canny edge image and write the edge direction and edge coordinates "
                "to main memory. \nThe VEARS ipcore is used to display the original camera image "
                "and the returned features on a monitor."
            )
            # self.systems["Canny_pipeline_with_debug"]["comment"] = self.tr(
            #     "This ASTERICS reference design implements a set of ASTERICS modules to "
            #     "calculate a Canny edge image and write the edge direction and edge coordinates "
            #     "to main memory. \nThis version of the design includes a second output to memory "
            #     "providing intermediate states of the pipeline processing for debug purposes.\n"
            #     "The VEARS ipcore is used to display the debug images on a monitor."
            # )
            # PageId
            self.systems["New system..."]["id"] = Wizard.InputPage_nr
            # self.systems["Inverter"]["id"] = Wizard.InverterPage_nr
            # self.systems["Canny_pipeline"]["id"] = Wizard.CannyPage_nr
            # self.systems["Image differencing"]["id"] = Wizard.DifferencingPage_nr
            # self.systems["Canny_pipeline_with_debug"]["id"] = Wizard.Canny_dbg_Page_nr
            # Modules
            self.systems["New system..."]["modules"] = []
            self.systems["Inverter"]["modules"] = [
                "as_sensor_ov7670",
                "as_invert",
                "as_collect",
                "as_memwriter",
            ]
            self.systems["Canny_pipeline"]["modules"] = [
                "as_sensor_ov7670",
                "as_collect",
                "as_memwriter",
                "as_pipeline_flush",
                "as_2d_conv_filter_internal",
                "as_cordic_direction",
                "as_edge_list",
                "as_edge_nms",
                "as_edge_threshold",
                "as_feature_counter",
                "as_gradient_weight",
                "as_pipeline_flush",
                "as_pipeline_row",
            ]
            self.systems["Image differencing"]["modules"] = [
                "as_sensor_ov7670",
                "as_stream_splitter",
                "as_memreader",
                "as_stream_sync",
                "as_pixel_diff",
                "as_disperse",
                "as_collect",
                "as_memwriter",
            ]
            # self.systems["Canny_pipeline_with_debug"]["modules"] = [
            #     "as_sensor_ov7670",
            #     "as_mux",
            #     "as_collect",
            #     "as_memwriter",
            #     "as_pipeline_flush",
            #     "as_2d_conv_filter_internal",
            #     "as_cordic_direction",
            #     "as_edge_list",
            #     "as_edge_nms",
            #     "as_edge_threshold",
            #     "as_feature_counter",
            #     "as_gradient_weight",
            #     "as_pipeline_flush",
            #     "as_pipeline_row",
            # ]
            # Filenames
            self.systems["Canny_pipeline"][
                "filename"
            ] = "asterics/systems/as_refdesign_canny/asterics/canny_pipeline/asterics-gen.py"
            self.systems["Image differencing"][
                "filename"
            ] = "asterics/systems/as_refdesign_zynq/asterics/image_differencing/asterics-gen.py"
            # self.systems["Canny_pipeline_with_debug"][
            #     "filename"
            # ] = "asterics/systems/as_refdesign_canny_dbg/asterics/canny_pipeline_with_debug/asterics-gen.py"
            # Connexions
            connexion = dict()
            connexion["as_invert"] = ["as_collect"]
            connexion["as_collect"] = ["as_memwriter"]
            connexion["as_sensor_ov7670"] = ["as_invert"]
            self.systems["Inverter"]["connexion"] = connexion

            self.comboBox = qw.QComboBox()
            self.comboBox.addItems(sorted(self.systems.keys()))
            self.comboBox.setCurrentIndex(
                self.comboBox.findText("New system...")
            )
            layout = qw.QVBoxLayout()
            self.setLayout(layout)

            self.overviewTitle = qw.QLabel("Overview:")
            self.modListTitle.setStyleSheet("font-weight: bold;")
            self.overviewTitle.setStyleSheet("font-weight: bold;")
            layout.addWidget(
                qw.QLabel(
                    self.tr(
                        "\nHere is a list of predefined template,"
                        "that you can use to generate a image processing system with ASTERICS"
                    )
                )
            )
            layout.addWidget(self.comboBox)
            layout.addWidget(self.overviewTitle)
            layout.addWidget(self.overview)
            layout.addWidget(self.modListTitle)
            layout.addWidget(self.modList)

            self.preview.setVisible(False)
            self.overview.setVisible(False)
            self.comboBox.activated[str].connect(self.__show_details__)

        def __show_details__(self):
            self.preview.setVisible(True)
            self.modList.setVisible(True)
            self.next_btn.setVisible(False)
            key = self.comboBox.currentText()
            self.modListTitle.setVisible(True)
            self.generateButton.setVisible(True)

            if (
                key not in self.systems.keys()
                or "comment" not in self.systems[key].keys()
            ):
                self.overviewTitle.setVisible(False)
                self.overview.setText(
                    "Something is wrong\n" + self.warning_msg.format(key)
                )
                self.overview.setStyleSheet(
                    "color: red; background-color: white;"
                )
                self.overview.setWordWrap(True)
                self.next_btn.setEnabled(False)
            else:
                if "New system..." in key:
                    self.modList.setVisible(False)
                    self.preview.setVisible(False)
                    self.next_btn.setVisible(True)
                    self.modListTitle.setVisible(False)
                    self.generateButton.setVisible(False)
                modNames = ""
                for index, module in enumerate(self.systems[key]["modules"]):
                    modNames += "{}.{}\n".format(index + 1, module)
                self.modListTitle.setText(
                    "Module List: #({})".format(
                        len(self.systems[key]["modules"])
                    )
                )
                self.modList.setText(modNames)
                self.overview.setVisible(True)
                self.next_btn.setEnabled(True)
                self.overviewTitle.setVisible(True)
                self.overview.setText(self.systems[key]["comment"])
                self.overview.setStyleSheet("background-color: white;")
                self.overview.setWordWrap(True)
            self.adjustSize()

        def generateSystem(self):
            system = self.comboBox.currentText()
            string = "The system are successful generated\nYou can find and modified the generated script in Template view. At the end you can save the script to main memory by clicking the `save as...` button"
            error = "The system was not generated"
            try:
                # msg = self.systems[system]["comment"]
                # qw.QMessageBox.information(self, self.tr("ASTERICS GUI"), msg)
                if system == "Inverter":
                    self.gui.generate_asterics_systems(
                        self.systems[system]["modules"],
                        self.systems[system]["connexion"],
                    )
                else:
                    self.generate_or_warning(self.systems[system]["filename"])
                qw.QMessageBox.information(
                    self, self.tr("ASTERICS GUI"), string
                )
                self.gui.activateWindow()
                self.gui.frame_mittle.hide()
                self.gui.frame_infobox.hide()
            except Exception:
                # qw.QMessageBox.warning(self, self.tr("ASTERICS GUI"), self.warning_msg.format(key))
                qw.QMessageBox.warning(self, self.tr("ASTERICS GUI"), error)

        def generate_or_warning(self, filename):
            msg = "Something are wrong.\n"
            msg += "You should run the file 'as-gui' only from any subdirectory of the directory `asterics`.\n"
            msg += "However, the image differencing system are already generated. See the path {}".format(
                filename
            )

            path = get_absolut_path(filename)
            if path != False:
                with open(path) as file:
                    file = file.read()
                    self.gui.template_bro.setText(file)
                self.generated = True
            else:
                qw.QMessageBox.warning(self, "ASTERICS GUI", msg)

        def setVisible(self, visible):
            qw.QWizardPage.setVisible(self, visible)
            if visible:
                self.wizard().setButtonText(
                    qw.QWizard.CustomButton2, self.tr("&Preview")
                )
                self.wizard().setButtonText(
                    qw.QWizard.CustomButton1, self.tr("&Generate")
                )
                self.wizard().setOption(qw.QWizard.HaveCustomButton1, True)
                self.wizard().setOption(qw.QWizard.HaveCustomButton2, True)
                self.__configWizBtns__(True)
                self.preview.setVisible(False)
                self.preview.setEnabled(False)
                self.generateButton.setVisible(False)
                self.generateButton.clicked.connect(self.generateSystem)
                self.__show_details__()
            else:
                self.wizard().setOption(qw.QWizard.HaveCustomButton1, False)
                self.wizard().setOption(qw.QWizard.HaveCustomButton2, False)
                self.__configWizBtns__(False)
                try:
                    self.generateButton.clicked.disconnect()
                    self.preview.clicked.disconnect()
                except Exception:
                    pass

        def closeEvent(self, event):
            event.accept()
            print("The dialog is closed")

        def __configWizBtns__(self, state):
            if state:
                btnList = [
                    qw.QWizard.Stretch,
                    qw.QWizard.BackButton,
                    qw.QWizard.NextButton,
                    qw.QWizard.CustomButton2,
                    qw.QWizard.CustomButton1,
                    qw.QWizard.FinishButton,
                    qw.QWizard.CancelButton,
                    qw.QWizard.HelpButton,
                ]
                self.wizard().setButtonLayout(btnList)
            else:
                btnList = [
                    qw.QWizard.Stretch,
                    qw.QWizard.BackButton,
                    qw.QWizard.NextButton,
                    qw.QWizard.FinishButton,
                    qw.QWizard.CancelButton,
                    qw.QWizard.HelpButton,
                ]
                self.wizard().setButtonLayout(btnList)

        def nextId(self):
            system = self.comboBox.currentText()
            try:
                if system == "New system...":
                    # id = self.systems[key]["id"]
                    return Wizard.InputPage_nr
                else:
                    return Wizard.ExistedSystemPage_nr
            except Exception:
                qw.QMessageBox.warning(
                    self,
                    self.tr("ASTERICS GUI"),
                    self.warning_msg.format(system),
                )
                return Wizard.ExistedSystemPage_nr

    class IntroPage(qw.QWizardPage):
        def __init__(self, owner=None):
            # super(IntroPage, self).__init__(owner)
            super().__init__(owner)
            self.gui = owner.gui
            self.setTitle(self.tr("Welcome to the ASTRICS Wizard"))
            self.helpMessage = self.tr(
                "-They have to decide whether they want to build "
                "an ASTERICS image processing chain from the beginning or from scratch\n"
                "-The decision you make here will affect which page you  get to see next."
            )
            layout = qw.QVBoxLayout()
            self.setLayout(layout)
            intro = qw.QLabel(
                "The wizard helps you step by step to create an ASTERICS image processing chain "
                " or shows you how to build an image processing chain\n\n"
            )
            msg = qw.QLabel("Would you like to generate a system ")
            self.ja = qw.QRadioButton("from existing modules (demo system)")
            self.nein = qw.QRadioButton("from scratch")
            self.ja.setChecked(True)
            msg.setWordWrap(True)
            intro.setWordWrap(True)
            intro.setAlignment(qc.Qt.AlignCenter)
            layout.addWidget(intro)
            # layout.addWidget(msg)
            # layout.addWidget(self.ja)
            # layout.addWidget(self.nein)
            layout.addWidget(qw.QLabel("\n\nClick Next to continue."))
            self.adjustSize()

        def nextId(self):
            return Wizard.ExistedSystemPage_nr

        def setVisible(self, visible):
            qw.QWizardPage.setVisible(self, visible)
            if visible:
                btnList = [
                    qw.QWizard.Stretch,
                    qw.QWizard.BackButton,
                    qw.QWizard.NextButton,
                    qw.QWizard.FinishButton,
                    qw.QWizard.CancelButton,
                ]
                self.wizard().setButtonLayout(btnList)
            else:
                # remove it if it's not visible
                btnList = [
                    qw.QWizard.Stretch,
                    qw.QWizard.BackButton,
                    qw.QWizard.NextButton,
                    qw.QWizard.FinishButton,
                    qw.QWizard.CancelButton,
                    qw.QWizard.HelpButton,
                ]
                self.wizard().setButtonLayout(btnList)

    class InputPage(qw.QWizardPage):
        def __init__(self, owner=None):
            super().__init__(owner)
            self.owner = owner
            self.gui = self.owner.gui
            self.clickNext = qw.QLabel("\n\n\nClick Next to continue.")
            self.warning_label = qw.QLabel(
                '<font color="red">You must select at least one option</font>'
            )
            self.helpMessage = self.tr(
                "-The ASTERICS system should process data, so they must select how the input data should be read.\n"
                "-Please choose one of the suggested options, then click on `Next` button."
            )
            self.setTitle(self.tr("Data input"))
            layout = qw.QVBoxLayout()
            self.setLayout(layout)
            self.other = qw.QCheckBox("other")
            self.camera = qw.QCheckBox("camera (as_sensor_ov7670)")
            self.reader = qw.QCheckBox("Memory reader (as_memReader)")
            layout.addWidget(
                qw.QLabel("\nHow should the input data be read?\n")
            )
            layout.addWidget(self.camera)
            layout.addWidget(self.reader)
            layout.addWidget(self.other)
            layout.addWidget(self.warning_label)
            self.next_btn = owner.button(qw.QWizard.NextButton)
            self.next_btn.clicked.connect(self.isClicked)
            self.camera.clicked.connect(self.isClicked)
            self.reader.clicked.connect(self.isClicked)

            self.camera.clicked.connect(self.addResult)
            self.reader.clicked.connect(self.addResult)
            self.other.clicked.connect(self.isClicked)
            self.isClicked()
            layout.addWidget(self.clickNext)
            self.warning_label.setVisible(False)

        def nextId(self):
            if (
                self.camera.isChecked()
                or self.reader.isChecked()
                or self.other.isChecked()
            ):
                self.next_btn.setEnabled(True)
                return Wizard.OutputPage_nr
            else:
                self.next_btn.setEnabled(False)
                return Wizard.InputPage_nr

        def isClicked(self):
            if self.isVisible():
                if self.other.isChecked():
                    self.next_btn.setEnabled(False)
                    self.warning_label.setVisible(True)
                    self.next_btn.setToolTip(
                        '<font color="red">You must select at least one option or one correct option</font>'
                    )
                    self.warning_label.setText(
                        '<font color="red">This option is currently not supported by ASTERICS </font>'
                    )
                elif self.camera.isChecked() and self.reader.isChecked():
                    self.next_btn.setEnabled(False)
                    self.warning_label.setVisible(True)
                    self.next_btn.setToolTip(
                        '<font color="red">You can choose only one data source</font>'
                    )
                    self.warning_label.setText(
                        '<font color="red">With the ASTERICS GUI currently can not generate a system with multiple inputs </font>'
                    )
                elif self.camera.isChecked() or self.reader.isChecked():
                    self.warning_label.setVisible(False)
                    self.next_btn.setEnabled(True)
                    self.next_btn.setToolTip("")
                else:
                    self.next_btn.setEnabled(False)
                    if self.warning_label.isVisible():
                        self.warning_label.setVisible(False)
                    self.next_btn.setToolTip(
                        '<font color="red">You must select at least one option</font>'
                    )

        def addResult(self):
            text = self.sender().text()
            if "as_memReader" in text:
                text = "as_memReader"
            if "as_sensor_ov7670" in text:
                text = "as_sensor_ov7670"
            if text in self.owner.results[Wizard.InputPage_nr]:
                self.owner.results[Wizard.InputPage_nr].remove(text)
                print("Remove choice to result")
            else:
                self.owner.results[Wizard.InputPage_nr].add(text)
                print("Add choice to result")

        def setVisible(self, visible):
            qw.QWizardPage.setVisible(self, visible)
            if visible:
                btnList = [
                    qw.QWizard.Stretch,
                    qw.QWizard.BackButton,
                    qw.QWizard.NextButton,
                    qw.QWizard.FinishButton,
                    qw.QWizard.CancelButton,
                    qw.QWizard.HelpButton,
                ]
                self.wizard().setButtonLayout(btnList)
                self.adjustSize()
            else:
                self.owner.infobox.hide()
                self.owner.infobox.close()
                self.next_btn.setToolTip("")

        def closeEvent(self, event):
            event.accept()
            print("The dialog is closed")

    class OutputPage(qw.QWizardPage):
        def __init__(self, owner=None):
            super().__init__(owner)
            self.owner = owner
            self.gui = self.owner.gui
            self.warning_label = qw.QLabel()
            self.setTitle(self.tr("Data Output"))
            self.helpMessage = self.tr(
                "The ASTERICS system should process data, so they must select how the input data should be read.\n"
                "  Please choose one of the suggested options, then click on `Next` button."
            )
            layout = qw.QVBoxLayout()
            self.setLayout(layout)
            layout.addWidget(
                qw.QLabel("\nHow should the output data be written?\n")
            )
            self.writer = qw.QCheckBox("Memory writer (as_memWriter)")
            self.other = qw.QCheckBox("other")

            layout.addWidget(self.writer)
            layout.addWidget(self.other)
            layout.addWidget(self.warning_label)

            self.other.clicked.connect(self.isClicked)
            self.writer.clicked.connect(self.isClicked)
            self.writer.clicked.connect(self.addResult)
            self.next_btn = owner.button(qw.QWizard.NextButton)
            layout.addWidget(qw.QLabel("\n\n\nClick Next to continue."))
            self.adjustSize()

        def addResult(self):
            text = self.sender().text().lower()
            if "writer" in text:
                text = "as_memwriter"
            if text in self.owner.results[Wizard.OutputPage_nr]:
                self.owner.results[Wizard.OutputPage_nr].remove(text)
                print("Module removed")
            else:
                self.owner.results[Wizard.OutputPage_nr].add(text)
                print("Module added")

        def isClicked(self):
            if self.isVisible():
                if self.other.isChecked():
                    self.next_btn.setEnabled(False)
                    self.warning_label.setVisible(True)
                    self.next_btn.setToolTip(
                        '<font color="red">You must select at least one option</font>'
                    )
                    self.warning_label.setText(
                        '<font color="red">This option is currently not supported by ASTERICS </font>'
                    )
                elif self.writer.isChecked():
                    self.warning_label.setVisible(False)
                    self.next_btn.setEnabled(True)
                    self.next_btn.setToolTip("")
                else:
                    self.next_btn.setEnabled(False)
                    if self.warning_label.isVisible():
                        self.warning_label.setVisible(False)
                    self.next_btn.setToolTip(
                        '<font color="red">You must select at least one option</font>'
                    )

        def nextId(self):
            if self.writer.isChecked() or self.other.isChecked():
                self.next_btn.setEnabled(True)
                return Wizard.ChooseModulePage_nr
            else:
                self.next_btn.setEnabled(False)
                return Wizard.OutputPage_nr

        def setVisible(self, visible):
            qw.QWizardPage.setVisible(self, visible)

            if visible:
                btnList = [
                    qw.QWizard.Stretch,
                    qw.QWizard.BackButton,
                    qw.QWizard.NextButton,
                    qw.QWizard.FinishButton,
                    qw.QWizard.CancelButton,
                    qw.QWizard.HelpButton,
                ]

                self.wizard().setButtonLayout(btnList)
                self.adjustSize()

            else:
                btnList = [
                    qw.QWizard.Stretch,
                    qw.QWizard.BackButton,
                    qw.QWizard.NextButton,
                    qw.QWizard.FinishButton,
                    qw.QWizard.CancelButton,
                    qw.QWizard.HelpButton,
                ]
                self.wizard().setButtonLayout(btnList)
                self.owner.infobox.hide()
                self.owner.infobox.close()
                try:
                    self.generate.disconnect()
                except:
                    pass

        def closeEvent(self, event):
            event.accept()
            print("The dialog is closed")

    def __init__(self, parent: GUI):
        super(Wizard, self).__init__()
        self.gui = parent
        self.results = defaultdict(set)
        self.setWizardStyle(qw.QWizard.ModernStyle)

        self.EES_ICON = os.path.join(
            self.gui.source_dir, "images/ees_logo_chip.png"
        )
        self.infobox = uic.loadUi(self.gui.source_dir + "/images/infobox.ui")
        self.infobox.setWindowIcon(qg.QIcon(self.EES_ICON))
        cancelButton = self.button(qw.QWizard.CancelButton)
        cancelButton.setStyleSheet(":hover{background-color: red;}")
        self.BOTTOM_ICON = os.path.join(
            self.gui.source_dir, "images", "bottom.png"
        )
        self.setStyleSheet(
            "QPushButton:hover {  background-color: orange; }"
            "QLabel {  alignment: center; }"
        )

        self.setPage(self.PageIntro_nr, self.IntroPage(self))
        self.setPage(self.InputPage_nr, self.InputPage(self))
        self.setPage(self.OutputPage_nr, self.OutputPage(self))
        self.setPage(self.ChooseModulePage_nr, self.ChooseModulePage(self))
        self.setPage(self.ConnexionPage_nr, self.ConnexionPage(self))
        self.setPage(self.ExistedSystemPage_nr, self.ExistedSystemPage(self))
        self.setPixmap(
            qw.QWizard.WatermarkPixmap, qg.QPixmap(self.gui.EES_ICON)
        )
        self.setStartId(self.PageIntro_nr)
        # set up help messages
        self._lastHelpMsg = ""
        self.helpRequested.connect(self._showHelp)
        self.adjustSize()

    @qc.pyqtSlot()
    def _showHelp(self):
        # get the help message for the current page
        page = self.currentPage()
        msg = page.helpMessage
        if msg == self._lastHelpMsg:
            # if same as last message, display alternate message
            msg = self.tr(
                "Sorry, I already gave what help I could. "
                "\nMaybe you should try asking a human?"
            )

            qw.QMessageBox.information(self, self.tr("ASTERICS GUI"), msg)
            self._lastHelpMsg = msg
        elif 1 == 1:
            if page.helpMessage is not None:
                qw.QMessageBox.information(self, self.tr("ASTERICS GUI"), msg)
            self._lastHelpMsg = msg

    def closeEvent(self, event):
        event.accept()
        print("The wizard is closed")
        return
        reply = qw.QMessageBox.question(
            self,
            "Window Close",
            "Are you sure you want to close the ASTERICS wizard?",
            qw.QMessageBox.Yes | qw.QMessageBox.No,
            qw.QMessageBox.No,
        )

        if reply == qw.QMessageBox.Yes:
            event.accept()
            print("Wizard closed")
        else:
            event.ignore()

    def setLabelText(self, label):
        label.setText(self.sender().currentText())

    def wizard_result(self, title, layout=None):

        if type(self.sender()) == qw.QComboBox:
            text = self.sender().currentText()
            if text not in self.results[title]:
                self.results[title].add(text)
                checkbox = qw.QCheckBox(text)
                checkbox.setChecked(True)
                layout.addWidget(checkbox)
                checkbox.stateChanged.connect(
                    lambda: self.wizard_result(title))
        else:
            checkbox = self.sender()
            if checkbox.isChecked():
                self.results[title].add(checkbox.text())
            else:
                self.results[title].discard(checkbox.text())


def start_gui():
    source_dir = sys.argv[0].rsplit("/", maxsplit=1)[0]
    # asterics_dir = source_dir.rsplit("/", maxsplit=2)[0]
    # print("Importing Automatics from '{}'...".format(source_dir))
    sys.path.append(source_dir)
    app = qw.QApplication(sys.argv)
    app.setApplicationName("ASTERICS GUI")
    auto = AsAutomatics(asterics_home, Automatics_version)
    auto.add_module_repository(
        append_to_path(asterics_home, "modules"), "default"
    )
    # auto.add_module_repository(
    #   "/home/phil/EES/asterics-nonfree/modules/", "nonfree")  # DEBUG
    gui = GUI(auto)
    gui.build_modlist()

    app.exec_()


def get_absolut_path(filename):
    """ Return the absolut path that content 'filename' """
    dirs = os.getcwd()  # from who you execute the as-module-browser
    for _ in range(20):
        path = os.path.join(dirs, filename)
        if os.path.exists(path):
            return path
        else:
            dirs = os.path.dirname(dirs)
    return False


if __name__ == "__main__":
    # print(get_absolut_path("as_support.h"), 88888)
    start_gui()
