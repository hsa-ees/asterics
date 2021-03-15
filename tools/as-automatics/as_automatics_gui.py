# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# This file is part of the ASTERICS Framework.
# (C) 2019 Hochschule Augsburg, University of Applied Sciences
# -----------------------------------------------------------------------------
"""
as_automatics_gui.py

Company:
Efficient Embedded Systems Group
University of Applied Sciences, Augsburg, Germany
http://ees.hs-augsburg.de

Author:
Philip Manke - 2019

Description:
Module containing a minimalistic GUI based on PyQT5 for the interactive mode
of Automatics.
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
# @file as_automatics_gui.py
# @ingroup automatics_gui_legacy
# @author Philip Manke
# @brief GUI module (PyQT5) for the interactive mode of Automatics.
# -----------------------------------------------------------------------------

import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg

import os
import sys
import copy


if __name__ == "__main__":

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

    # print("Importing Automatics from '{}'...".format(source_dir))
    sys.path.append(automatics_home)

    # Import Automatics

    import as_automatics_logging as as_log

    as_log.init_log(loglevel_console="WARNING", loglevel_file="INFO")
    import as_automatics_exceptions as as_err
    from asterics import Automatics_version
    from as_automatics_env import AsAutomatics
    from as_automatics_proc_chain import AsProcessingChain
    from as_automatics_module import AsModule
    from as_automatics_port import Port, StandardPort
    from as_automatics_interface import Interface
    from as_automatics_module_lib import AsModuleLibrary
    from as_automatics_generic import Generic
    from as_automatics_2d_window_module import AsWindowModule
    from as_automatics_register import SlaveRegisterInterface

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
                self.edit.moveCursor(qtg.QTextCursor.End)
                self.edit.insertPlainText(m)
            if self.out:
                self.out.write(m)

        def flush(self):
            if self.edit:
                self.edit.moveCursor(qtg.QTextCursor.End)
                self.edit.insertPlainText("")
            if self.out:
                self.out.flush()

    ## @ingroup automatics_gui_legacy
    class GUI(qtw.QMainWindow):
        MODULE_VIEW = "mod"
        INTERFACE_VIEW = "inter"
        PORT_VIEW = "port"

        def __init__(self, auto: AsAutomatics):
            super(GUI, self).__init__()
            self.auto = auto
            # File menu
            main_menu = self.menuBar()
            file_menu = main_menu.addMenu("File")

            # Exit button
            exit_button = qtw.QAction("Exit", self)
            exit_button.setShortcut("Ctrl+Q")
            exit_button.setStatusTip("Exit application")
            exit_button.triggered.connect(self.close)
            file_menu.addAction(exit_button)

            # Add repo button
            add_repo_button = qtw.QAction("Add Repository", self)
            add_repo_button.setShortcut("Ctrl+N")
            add_repo_button.setStatusTip(
                "Select a Folder to Scan for ASTERICS Modules"
            )
            add_repo_button.triggered.connect(self.add_repo_action)
            file_menu.addAction(add_repo_button)

            # Text fixed font
            fixedfont = qtg.QFontDatabase.systemFont(
                qtg.QFontDatabase.FixedFont
            )
            fixedfont.setPointSize(12)

            # Main vertical layout
            self.main_layout = qtw.QVBoxLayout()
            self.main_layout.addSpacing(1)
            self.main_layout.activate()

            # Layout:
            #     /<- control(H) < button(V)
            # main(V) < content(H) < text(V)
            #              \<- tables

            # Content layout (top section of main layout)
            self.content_layout = qtw.QHBoxLayout()
            self.main_layout.addLayout(self.content_layout)
            self.content_layout.addSpacing(1)
            self.content_layout.activate()

            # Layout for the console and infobox
            self.textlayout = qtw.QVBoxLayout()
            self.textlayout.activate()
            self.content_layout.addLayout(self.textlayout)

            # Console. For all automatics output
            self.console_label = qtw.QLabel()
            self.console_label.setText("Automatics Log:")
            self.textlayout.addWidget(self.console_label)

            self.console = qtw.QTextBrowser()
            self.console.setMaximumWidth(4000)
            self.console.setFont(fixedfont)
            self.textlayout.addWidget(self.console)

            # Infobox for module details
            self.infobox_label = qtw.QLabel()
            self.infobox_label.setText("Infobox:")
            self.textlayout.addWidget(self.infobox_label)

            self.infobox = qtw.QTextBrowser()
            self.infobox.setFont(fixedfont)
            self.infobox.setMaximumWidth(4000)
            self.textlayout.addWidget(self.infobox)

            self.table_layout = qtw.QVBoxLayout()
            self.content_layout.addLayout(self.table_layout)

            # Table Widgets:
            # Module list
            self.modlist_label = qtw.QLabel()
            self.modlist_label.setText("ASTERICS Module List:")
            self.table_layout.addWidget(self.modlist_label)

            self.modlist = qtw.QTableWidget(self)
            self.modlist.setEditTriggers(qtw.QAbstractItemView.NoEditTriggers)
            self.modlist.setColumnCount(3)
            self.modlist.setHorizontalHeaderLabels(
                ("Module Name", "Type", "Repository")
            )
            self.modlist.setSelectionBehavior(qtw.QAbstractItemView.SelectItems)
            self.modlist.setSelectionMode(qtw.QAbstractItemView.SingleSelection)
            self.modlist.itemSelectionChanged.connect(self.module_clicked)
            self.modlist.doubleClicked.connect(self.detailed_view_action)
            self.modlist.clicked.connect(self.module_clicked)
            self.table_layout.addWidget(self.modlist)

            # Interface list
            self.interlist = qtw.QTableWidget(self)
            self.interlist.setEditTriggers(qtw.QAbstractItemView.NoEditTriggers)
            self.interlist.setMinimumSize(10, 10)
            self.interlist.setColumnCount(3)
            self.interlist.setHorizontalHeaderLabels(
                ("Name", "Type", "Direction / Value")
            )
            self.interlist.setSelectionBehavior(
                qtw.QAbstractItemView.SelectItems
            )
            self.interlist.setSelectionMode(
                qtw.QAbstractItemView.SingleSelection
            )
            self.interlist.doubleClicked.connect(self.detailed_view_action)
            self.interlist.clicked.connect(self.inter_clicked)
            self.table_layout.addWidget(self.interlist)
            self.interlist.hide()

            # Port list
            self.portlist = qtw.QTableWidget(self)
            self.portlist.setMinimumSize(10, 10)
            self.portlist.setEditTriggers(qtw.QAbstractItemView.NoEditTriggers)
            self.portlist.setColumnCount(3)
            self.portlist.setHorizontalHeaderLabels(
                ("Name", "Type", "Direction")
            )
            self.portlist.setSelectionBehavior(
                qtw.QAbstractItemView.SelectItems
            )
            self.portlist.setSelectionMode(
                qtw.QAbstractItemView.SingleSelection
            )
            self.portlist.doubleClicked.connect(self.detailed_view_action)
            self.portlist.clicked.connect(self.port_clicked)
            self.table_layout.addWidget(self.portlist)
            self.portlist.hide()

            # input bar. needed?
            # self.input_bar = qtw.QLineEdit()
            # self.input_bar.setFont(fixedfont)
            # self.textlayout.addWidget(self.input_bar)

            # Control layout for buttons and Co (lower section of main layout)
            self.control_layout = qtw.QHBoxLayout()
            self.control_layout.activate()
            self.main_layout.addLayout(self.control_layout)

            # Button layout
            self.button_layout = qtw.QVBoxLayout()
            self.button_layout.activate()
            self.control_layout.addLayout(self.button_layout)

            # Create buttons
            self.exit_button = qtw.QPushButton("Quit Automatics")
            self.details_button = qtw.QPushButton("Detailed View")
            self.overview_button = qtw.QPushButton("Module Selection")
            # ↓ Move to file menu?
            # self.add_repo_button = qtw.QPushButton("Scan Folder for Modules")
            self.list_details_button = qtw.QPushButton("List Details")

            # Connect buttons with action functions
            self.exit_button.clicked.connect(self.close)
            self.details_button.clicked.connect(self.detailed_view_action)
            self.overview_button.clicked.connect(self.module_overview_action)
            # self.add_repo_button.clicked.connect(self.add_repo_action)
            self.list_details_button.clicked.connect(self.list_details_action)

            # Enable keyboard control for buttons (Enter can activate button)
            self.exit_button.setAutoDefault(True)
            self.details_button.setAutoDefault(True)
            self.overview_button.setAutoDefault(True)
            # self.add_repo_button.setAutoDefault(True)
            self.list_details_button.setAutoDefault(True)

            # Add to buttonlayout
            self.button_layout.addWidget(self.list_details_button)
            self.button_layout.addWidget(self.details_button)
            self.button_layout.addWidget(self.overview_button)
            # self.button_layout.addWidget(self.add_repo_button)
            self.button_layout.addWidget(self.exit_button)

            self.overview_button.hide()

            # Main GUI container
            container = qtw.QWidget()
            container.setMinimumWidth(1280)
            container.setMinimumHeight(720)
            container.setLayout(self.main_layout)
            self.setCentralWidget(container)

            # Status bar
            self.status_container = qtw.QStatusBar()
            self.status = qtw.QLabel()
            self.status.setAlignment(qtc.Qt.AlignLeft)
            self.status.setText("Nothing selected...")
            self.status_container.addPermanentWidget(self.status)
            self.setStatusBar(self.status_container)

            # Set up stdout
            # Save/Store original stdout
            self.stdout_orig = sys.stdout
            # Set up alternate stdouts
            self.infobox_out_stream = OutLog(self.infobox, self.stdout_orig)
            self.console_out_stream = OutLog(self.console, self.stdout_orig)
            # Default output to console
            sys.stdout = self.console_out_stream

            # Status attributes
            self.view = self.MODULE_VIEW
            self.crt_module = None
            self.crt_interface = None
            self.crt_port = None
            self.crt_generic = None
            print("Hello from ASTERICS Automatics!")
            # Show GUI
            self.show()

        def build_modlist(self):
            """Add all modules in the module library to the module list."""
            library = self.auto.library
            modules = library.get_module_names()
            for modname in sorted(modules):
                self.add_module(modname)
            self.fit_table_to_contents(self.modlist)
            print("Loaded {} modules!".format(self.modlist.rowCount()))

        def module_clicked(self):
            """Print brief description and select the module clicked in the
            QTableWidget - module list"""
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

        def inter_clicked(self):
            """Print brief description and select the interface clicked in the
            QTableWidget - interface list"""
            intername, intertype, direction = self.get_selected_item(
                self.interlist
            )
            if intertype in ("Port", "StandardPort"):
                self.port_clicked((intername, intertype, direction))
            elif intertype == "Generic":
                self.generic_clicked((intername, intertype, direction))
            else:
                inter = None
                if intertype == "slv_reg_interface":
                    inter = self.crt_module.get_slave_register_interface(
                        intername
                    )
                elif intertype == "as_window":
                    inter = self.crt_module.get_window_interface(intername)
                else:
                    inter = self.crt_module.get_interface(
                        intername, direction, intertype
                    )
                if inter:
                    self.crt_interface = inter
                    self.crt_port = None
                    self.crt_generic = None
                    select_text = (
                        "Selected interface '{}' of module '{}'".format(
                            intername, self.crt_module.entity_name
                        )
                    )
                    self.status.setText(select_text)
                    print(str(inter))
                    self.infobox.setText(
                        "Interface '{}' ({}) with direction '{}' of:\n{}".format(
                            intername,
                            intertype,
                            direction,
                            str(self.crt_module),
                        )
                    )
                else:
                    print("No info for interface '{}'".format(intername))

        def port_clicked(self, from_interlist: tuple = None):
            if from_interlist:
                portname, porttype, direction = from_interlist
                port = self.crt_module.get_port(portname, suppress_error=True)
            else:
                portname, porttype, direction = self.get_selected_item(
                    self.portlist
                )
                port = self.crt_interface.get_port(
                    portname, suppress_error=True
                )
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
                        portname,
                        port.code_name,
                        direction,
                        str(self.crt_module),
                    )
                )
            else:
                print("Port '{}' not found!".format(portname))

        def generic_clicked(self, from_interlist: tuple):
            genericname, _, defaultval = from_interlist
            gen = self.crt_module.get_generic(genericname, suppress_error=True)
            if gen:
                self.crt_generic = gen
                self.crt_port = None
                self.crt_interface = None
                select_text = (
                    "Generic '{}' ({}) with default value [{}] of "
                    "module '{}'"
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

        def close(self):
            sys.stdout = self.stdout_orig
            super().close()

        def add_module(self, modname: str, reponame: str = ""):
            mod = self.auto.library.get_module_template(modname, reponame)
            y = self.modlist.rowCount()
            self.modlist.insertRow(y)
            tablerow = [
                mod.entity_name,
                "AsWindowModule"
                if isinstance(mod, AsWindowModule)
                else "AsModule",
                mod.repository_name,
            ]

            for x in range(3):
                item = qtw.QTableWidgetItem(tablerow[x])
                item.setToolTip(tablerow[x])
                self.modlist.setItem(y, x, item)

        @staticmethod
        def get_selected_item(table: qtw.QTableWidget) -> tuple:
            for item in table.selectedItems():
                crt_row = table.row(item)
            name = table.item(crt_row, 0).text()
            d1 = table.item(crt_row, 1).text()
            d2 = table.item(crt_row, 2).text()
            return (name, d1, d2)

        def build_interlist(self, module: AsModule):
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
                    tablerow = [inter.name, port_type, inter.direction]
                elif isinstance(inter, Generic):
                    tablerow = [
                        inter.code_name,
                        "Generic",
                        str(inter.default_value),
                    ]
                elif isinstance(inter, SlaveRegisterInterface):
                    tablerow = [str(inter), inter.type, inter.direction]
                else:
                    tablerow = [str(inter), inter.type, inter.direction]
                y = self.interlist.rowCount()
                self.interlist.insertRow(y)
                for x in range(3):
                    item = qtw.QTableWidgetItem(tablerow[x])
                    item.setToolTip(tablerow[x])
                    self.interlist.setItem(y, x, item)
            self.fit_table_to_contents(self.interlist)
            print(
                "Showing {} interfaces/ports/generics of module '{}'".format(
                    self.interlist.rowCount(), self.crt_module.entity_name
                )
            )

        def detailed_view_action(self):
            if self.view is self.PORT_VIEW:
                print("Already in most detailed view!")
            elif self.view is self.MODULE_VIEW:
                if self.crt_module is None:
                    print("No module selected!")
                    return False
                # Remove all rows of the interface list
                self.interlist.setRowCount(0)
                self.build_interlist(self.crt_module)
                self.modlist.hide()
                self.interlist.show()
                self.view = self.INTERFACE_VIEW
                self.modlist_label.setText(
                    "Interfaces of {}:".format(self.crt_module)
                )
                self.details_button.hide()
                self.overview_button.show()
            else:
                if self.crt_interface is None:
                    return False
                print("Showing ports of interface '{}'.")
                # TODO
            return True

        def module_overview_action(self):
            self.interlist.hide()
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
            self.overview_button.hide()
            self.details_button.show()

        def list_details_action(self):
            self.infobox.setText("")
            if self.view is self.PORT_VIEW:
                print(
                    "Listing details of port '{}'".format(
                        self.crt_port.code_name
                    )
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
                    if mod.files:
                        print("\nToplevel file: {}".format(mod.files[-1]))
                        if len(mod.files) > 1:
                            print("\nHDL files:")
                            for filename in mod.files[:-1]:
                                print("  - {}".format(filename))
                    if mod.dependencies:
                        print("\nDependencies:")
                        for dep in mod.dependencies:
                            print("  - {}".format(dep))
                    if mod.driver_files:
                        print("\nSoftware driver files:")
                        for filename in mod.driver_files:
                            print(" - " + filename)
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
                    print(
                        "Listing details for interface '{}'".format(intername)
                    )
                    sys.stdout = self.infobox_out_stream
                    self.crt_interface.print_interface(True)
                    print("\nOf module:")
                    print(self.crt_module)
                else:
                    print("Nothing selected!")
            self.infobox.moveCursor(qtg.QTextCursor.Start)
            # Switch stdout back to console
            sys.stdout = self.console_out_stream

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
                    self.fit_table_to_contents(self.modlist)
                    print(
                        "Added {} modules to repository 'user'!".format(
                            len(mods)
                        )
                    )
                else:
                    print("No modules found in '{}'.".format(folder))

        def add_repo_folder_dialog(self):
            """Allows the user to select a folder and returns the path."""
            options = qtw.QFileDialog.Options()
            options |= qtw.QFileDialog.DontUseNativeDialog
            folder_name = qtw.QFileDialog.getExistingDirectory(
                self, "QFileDialog.getExistingDirectory()", "", options=options
            )
            return folder_name

        def fit_table_to_contents(self, table: qtw.QTableWidget):
            table.resizeRowsToContents()
            table.resizeColumnsToContents()
            width = 10
            for x in range(table.columnCount()):
                width += table.columnWidth(x)
            table.resize(width, table.height())

        # TODO:
        # Functionality:
        # Add switches when selecting those ports.
        # Make list_detail work in all views
        # Make brief info (single click) work in all views

    ## @ingroup automatics_gui_legacy
    def start_gui(asterics_path):
        app = qtw.QApplication([])
        app.setApplicationName("Automatics Module Explorer (Legacy)")
        auto = AsAutomatics(asterics_path, Automatics_version)
        auto.add_module_repository(asterics_path + "/modules", "default")
        gui = GUI(auto)
        gui.build_modlist()
        app.exec_()

    start_gui(asterics_home)
