"""
Main application window for AUTOSAR Designer.
"""
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTreeWidget, QTreeWidgetItem, QStackedWidget,
    QToolBar, QStatusBar, QFileDialog, QMessageBox, QMenu,
    QLabel, QPushButton, QStyle, QTabWidget
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QIcon, QFont

from model import (
    Project, SoftwareComponent, Interface, Port, Runnable,
    DataElement, Operation, OperationArgument, InterfaceType, PortDirection, 
    BaseDataType, ApplicationDataType, ImplementationDataType, CompuMethod,
    DataTypeMapping, AppDataCategory, ArgumentDirection, PortConnection,
    save_project, load_project, create_example_project,
    MultiFileProject
)
from codegen import generate_project_code
from gui.editors import (
    WelcomePanel, SwcEditor, InterfaceEditor, PortEditor,
    RunnableEditor, DataElementEditor, OperationEditor,
    AppDataTypeEditor, ImplDataTypeEditor, CompuMethodEditor,
    ConnectionEditor
)
from gui.composition_view import CompositionWidget


class ProjectTreeWidget(QTreeWidget):
    """Tree widget for browsing project elements."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabel("Project Explorer")
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.setMinimumWidth(250)
        
        # Style
        self.setStyleSheet("""
            QTreeWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
                font-size: 13px;
            }
            QTreeWidget::item {
                padding: 4px;
            }
            QTreeWidget::item:selected {
                background-color: #094771;
            }
            QTreeWidget::item:hover {
                background-color: #2a2d2e;
            }
        """)

    def _show_context_menu(self, position):
        """Show context menu for tree items."""
        item = self.itemAt(position)
        menu = QMenu(self)

        if item is None:
            # Right-click on empty space
            add_swc = menu.addAction("Add Software Component")
            add_iface = menu.addAction("Add Interface")
            add_swc.triggered.connect(lambda: self.parent().parent()._add_swc())
            add_iface.triggered.connect(lambda: self.parent().parent()._add_interface())
        else:
            item_type = item.data(0, Qt.ItemDataRole.UserRole + 1)
            
            if item_type == "swc":
                add_port = menu.addAction("Add Port")
                add_run = menu.addAction("Add Runnable")
                menu.addSeparator()
                delete = menu.addAction("Delete Component")
                add_port.triggered.connect(lambda: self.parent().parent()._add_port(item))
                add_run.triggered.connect(lambda: self.parent().parent()._add_runnable(item))
                delete.triggered.connect(lambda: self.parent().parent()._delete_item(item))
            
            elif item_type == "interface":
                iface = item.data(0, Qt.ItemDataRole.UserRole)
                if iface.interface_type == InterfaceType.SENDER_RECEIVER:
                    add_de = menu.addAction("Add Data Element")
                    add_de.triggered.connect(lambda: self.parent().parent()._add_data_element(item))
                else:
                    add_op = menu.addAction("Add Operation")
                    add_op.triggered.connect(lambda: self.parent().parent()._add_operation(item))
                menu.addSeparator()
                delete = menu.addAction("Delete Interface")
                delete.triggered.connect(lambda: self.parent().parent()._delete_item(item))
            
            elif item_type in ("port", "runnable", "data_element", "operation", 
                               "app_data_type", "impl_data_type", "compu_method", "connection"):
                # For ports, also offer connection creation
                if item_type == "port":
                    port = item.data(0, Qt.ItemDataRole.UserRole)
                    swc = item.data(0, Qt.ItemDataRole.UserRole + 2)
                    if port.direction == PortDirection.PROVIDED:
                        connect_action = menu.addAction("Connect to Required Port...")
                        connect_action.triggered.connect(
                            lambda: self.parent().parent()._create_connection_from_port(swc, port))
                        menu.addSeparator()
                delete = menu.addAction("Delete")
                delete.triggered.connect(lambda: self.parent().parent()._delete_item(item))
            
            elif item_type == "components_folder":
                add_swc = menu.addAction("Add Software Component")
                add_swc.triggered.connect(lambda: self.parent().parent()._add_swc())
            
            elif item_type == "interfaces_folder":
                add_iface = menu.addAction("Add Interface")
                add_iface.triggered.connect(lambda: self.parent().parent()._add_interface())

            elif item_type == "connections_folder":
                add_conn = menu.addAction("Add Connection...")
                add_conn.triggered.connect(lambda: self.parent().parent()._add_connection())

            elif item_type == "app_types_folder":
                add_adt = menu.addAction("Add Application Data Type")
                add_adt.triggered.connect(lambda: self.parent().parent()._add_app_data_type())

            elif item_type == "impl_types_folder":
                add_idt = menu.addAction("Add Implementation Data Type")
                add_idt.triggered.connect(lambda: self.parent().parent()._add_impl_data_type())

            elif item_type == "compu_methods_folder":
                add_cm = menu.addAction("Add CompuMethod")
                add_cm.triggered.connect(lambda: self.parent().parent()._add_compu_method())

        menu.exec(self.mapToGlobal(position))


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.project: Project = Project(name="New Project")
        self.project_path: Path = None
        self._modified = False
        
        self._setup_ui()
        self._setup_toolbar()
        self._setup_menubar()
        self._refresh_tree()

    def _setup_ui(self):
        """Setup the main UI layout."""
        self.setWindowTitle("AUTOSAR Designer")
        self.setMinimumSize(1200, 800)
        
        # Apply dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #252526;
            }
            QMenuBar {
                background-color: #3c3c3c;
                color: #d4d4d4;
            }
            QMenuBar::item:selected {
                background-color: #094771;
            }
            QMenu {
                background-color: #252526;
                color: #d4d4d4;
                border: 1px solid #454545;
            }
            QMenu::item:selected {
                background-color: #094771;
            }
            QToolBar {
                background-color: #3c3c3c;
                border: none;
                spacing: 5px;
                padding: 5px;
            }
            QToolButton {
                background-color: transparent;
                color: #d4d4d4;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QToolButton:hover {
                background-color: #4a4a4a;
            }
            QStatusBar {
                background-color: #007acc;
                color: white;
            }
            QSplitter::handle {
                background-color: #3c3c3c;
            }
        """)

        # Central widget with splitter
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Left panel: Project tree
        self.tree = ProjectTreeWidget(self)
        self.tree.itemSelectionChanged.connect(self._on_selection_changed)
        splitter.addWidget(self.tree)

        # Right panel: Tabs for Editor and Composition View
        self.right_tabs = QTabWidget()
        self.right_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background-color: #2d2d30;
                color: #808080;
                padding: 8px 20px;
                border: none;
                border-bottom: 2px solid transparent;
            }
            QTabBar::tab:selected {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border-bottom: 2px solid #007acc;
            }
            QTabBar::tab:hover {
                background-color: #3e3e42;
            }
        """)
        splitter.addWidget(self.right_tabs)

        # Tab 1: Property Editor
        self.editor_stack = QStackedWidget()
        self.editor_stack.setStyleSheet("""
            QStackedWidget {
                background-color: #1e1e1e;
            }
        """)
        self.right_tabs.addTab(self.editor_stack, "📝 Properties")

        # Tab 2: Composition View (Graphical)
        self.composition_view = CompositionWidget()
        self.right_tabs.addTab(self.composition_view, "📊 Composition Diagram")

        # Add editors
        self.welcome_panel = WelcomePanel()
        self.swc_editor = SwcEditor()
        self.interface_editor = InterfaceEditor()
        self.port_editor = PortEditor()
        self.runnable_editor = RunnableEditor()
        self.data_element_editor = DataElementEditor()
        self.operation_editor = OperationEditor()
        self.app_type_editor = AppDataTypeEditor()
        self.impl_type_editor = ImplDataTypeEditor()
        self.compu_method_editor = CompuMethodEditor()
        self.connection_editor = ConnectionEditor()

        self.editor_stack.addWidget(self.welcome_panel)       # 0
        self.editor_stack.addWidget(self.swc_editor)          # 1
        self.editor_stack.addWidget(self.interface_editor)    # 2
        self.editor_stack.addWidget(self.port_editor)         # 3
        self.editor_stack.addWidget(self.runnable_editor)     # 4
        self.editor_stack.addWidget(self.data_element_editor) # 5
        self.editor_stack.addWidget(self.operation_editor)    # 6
        self.editor_stack.addWidget(self.app_type_editor)     # 7
        self.editor_stack.addWidget(self.impl_type_editor)    # 8
        self.editor_stack.addWidget(self.compu_method_editor) # 9
        self.editor_stack.addWidget(self.connection_editor)   # 10

        # Connect editor signals
        self.swc_editor.changed.connect(self._on_editor_changed)
        self.interface_editor.changed.connect(self._on_editor_changed)
        self.port_editor.changed.connect(self._on_editor_changed)
        self.runnable_editor.changed.connect(self._on_editor_changed)
        self.data_element_editor.changed.connect(self._on_editor_changed)
        self.operation_editor.changed.connect(self._on_editor_changed)
        self.app_type_editor.changed.connect(self._on_editor_changed)
        self.impl_type_editor.changed.connect(self._on_editor_changed)
        self.compu_method_editor.changed.connect(self._on_editor_changed)
        self.connection_editor.changed.connect(self._on_editor_changed)

        splitter.setSizes([300, 900])

        # Status bar
        self.statusBar().showMessage("Ready")

    def _setup_toolbar(self):
        """Setup the main toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(toolbar)

        # New Project
        new_action = QAction("New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._new_project)
        toolbar.addAction(new_action)

        # Open
        open_action = QAction("Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_project)
        toolbar.addAction(open_action)

        # Save
        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save_project)
        toolbar.addAction(save_action)

        toolbar.addSeparator()

        # Add SWC
        add_swc_action = QAction("+ Component", self)
        add_swc_action.triggered.connect(self._add_swc)
        toolbar.addAction(add_swc_action)

        # Add Interface
        add_iface_action = QAction("+ Interface", self)
        add_iface_action.triggered.connect(self._add_interface)
        toolbar.addAction(add_iface_action)

        # Add Connection
        add_conn_action = QAction("+ Connection", self)
        add_conn_action.triggered.connect(self._add_connection)
        toolbar.addAction(add_conn_action)

        toolbar.addSeparator()

        # Generate Code
        generate_action = QAction("Generate Code", self)
        generate_action.setShortcut("F5")
        generate_action.triggered.connect(self._generate_code)
        toolbar.addAction(generate_action)

        toolbar.addSeparator()

        # Load Example
        example_action = QAction("Load Example", self)
        example_action.triggered.connect(self._load_example)
        toolbar.addAction(example_action)

    def _setup_menubar(self):
        """Setup the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")
        
        new_action = file_menu.addAction("New Project")
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._new_project)
        
        open_action = file_menu.addAction("Open Project...")
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_project)
        
        save_action = file_menu.addAction("Save")
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save_project)
        
        save_as_action = file_menu.addAction("Save As...")
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self._save_project_as)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("Exit")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)

        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        
        add_swc = edit_menu.addAction("Add Software Component")
        add_swc.triggered.connect(self._add_swc)
        
        add_iface = edit_menu.addAction("Add Interface")
        add_iface.triggered.connect(self._add_interface)

        # Generate menu
        gen_menu = menubar.addMenu("Generate")
        
        gen_code = gen_menu.addAction("Generate Code...")
        gen_code.setShortcut("F5")
        gen_code.triggered.connect(self._generate_code)

        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about = help_menu.addAction("About")
        about.triggered.connect(self._show_about)

    def _refresh_tree(self):
        """Refresh the project tree."""
        self.tree.clear()

        # Project root
        root = QTreeWidgetItem([f"📁 {self.project.name}"])
        root.setData(0, Qt.ItemDataRole.UserRole, self.project)
        root.setData(0, Qt.ItemDataRole.UserRole + 1, "project")
        self.tree.addTopLevelItem(root)

        # ==========================================================================
        # DATA TYPES FOLDER
        # ==========================================================================
        types_folder = QTreeWidgetItem(["📂 Data Types"])
        types_folder.setData(0, Qt.ItemDataRole.UserRole + 1, "types_folder")
        root.addChild(types_folder)

        # Compu Methods
        compu_folder = QTreeWidgetItem(["📂 CompuMethods"])
        compu_folder.setData(0, Qt.ItemDataRole.UserRole + 1, "compu_methods_folder")
        types_folder.addChild(compu_folder)
        for cm in self.project.compu_methods:
            cm_item = QTreeWidgetItem([f"📐 {cm.name}"])
            cm_item.setData(0, Qt.ItemDataRole.UserRole, cm)
            cm_item.setData(0, Qt.ItemDataRole.UserRole + 1, "compu_method")
            compu_folder.addChild(cm_item)

        # Application Data Types
        app_types_folder = QTreeWidgetItem(["📂 Application Types"])
        app_types_folder.setData(0, Qt.ItemDataRole.UserRole + 1, "app_types_folder")
        types_folder.addChild(app_types_folder)
        for adt in self.project.application_data_types:
            adt_item = QTreeWidgetItem([f"🔷 {adt.name}"])
            adt_item.setData(0, Qt.ItemDataRole.UserRole, adt)
            adt_item.setData(0, Qt.ItemDataRole.UserRole + 1, "app_data_type")
            app_types_folder.addChild(adt_item)

        # Implementation Data Types
        impl_types_folder = QTreeWidgetItem(["📂 Implementation Types"])
        impl_types_folder.setData(0, Qt.ItemDataRole.UserRole + 1, "impl_types_folder")
        types_folder.addChild(impl_types_folder)
        for idt in self.project.implementation_data_types:
            idt_item = QTreeWidgetItem([f"🔶 {idt.name}"])
            idt_item.setData(0, Qt.ItemDataRole.UserRole, idt)
            idt_item.setData(0, Qt.ItemDataRole.UserRole + 1, "impl_data_type")
            impl_types_folder.addChild(idt_item)

        # ==========================================================================
        # INTERFACES FOLDER
        # ==========================================================================
        ifaces_folder = QTreeWidgetItem(["📂 Interfaces"])
        ifaces_folder.setData(0, Qt.ItemDataRole.UserRole + 1, "interfaces_folder")
        root.addChild(ifaces_folder)

        for iface in self.project.interfaces:
            icon = "🔗" if iface.interface_type == InterfaceType.SENDER_RECEIVER else "⚡"
            iface_item = QTreeWidgetItem([f"{icon} {iface.name}"])
            iface_item.setData(0, Qt.ItemDataRole.UserRole, iface)
            iface_item.setData(0, Qt.ItemDataRole.UserRole + 1, "interface")
            ifaces_folder.addChild(iface_item)

            if iface.interface_type == InterfaceType.SENDER_RECEIVER:
                for de in iface.data_elements:
                    de_item = QTreeWidgetItem([f"  📊 {de.name}"])
                    de_item.setData(0, Qt.ItemDataRole.UserRole, de)
                    de_item.setData(0, Qt.ItemDataRole.UserRole + 1, "data_element")
                    de_item.setData(0, Qt.ItemDataRole.UserRole + 2, iface)
                    iface_item.addChild(de_item)
            else:
                for op in iface.operations:
                    op_item = QTreeWidgetItem([f"  ⚙️ {op.name}"])
                    op_item.setData(0, Qt.ItemDataRole.UserRole, op)
                    op_item.setData(0, Qt.ItemDataRole.UserRole + 1, "operation")
                    op_item.setData(0, Qt.ItemDataRole.UserRole + 2, iface)
                    iface_item.addChild(op_item)

        # ==========================================================================
        # COMPONENTS FOLDER
        # ==========================================================================
        comps_folder = QTreeWidgetItem(["📂 Software Components"])
        comps_folder.setData(0, Qt.ItemDataRole.UserRole + 1, "components_folder")
        root.addChild(comps_folder)

        for swc in self.project.components:
            swc_item = QTreeWidgetItem([f"📦 {swc.name}"])
            swc_item.setData(0, Qt.ItemDataRole.UserRole, swc)
            swc_item.setData(0, Qt.ItemDataRole.UserRole + 1, "swc")
            comps_folder.addChild(swc_item)

            # Ports
            for port in swc.ports:
                icon = "◀" if port.direction == PortDirection.REQUIRED else "▶"
                # Show connection status
                connections = self.project.get_connections_for_port(port.uid)
                conn_indicator = " 🔌" if connections else ""
                port_item = QTreeWidgetItem([f"  {icon} {port.name}{conn_indicator}"])
                port_item.setData(0, Qt.ItemDataRole.UserRole, port)
                port_item.setData(0, Qt.ItemDataRole.UserRole + 1, "port")
                port_item.setData(0, Qt.ItemDataRole.UserRole + 2, swc)
                swc_item.addChild(port_item)

            # Runnables
            for run in swc.runnables:
                run_item = QTreeWidgetItem([f"  ▷ {run.name}"])
                run_item.setData(0, Qt.ItemDataRole.UserRole, run)
                run_item.setData(0, Qt.ItemDataRole.UserRole + 1, "runnable")
                run_item.setData(0, Qt.ItemDataRole.UserRole + 2, swc)
                swc_item.addChild(run_item)

        # ==========================================================================
        # CONNECTIONS FOLDER
        # ==========================================================================
        conns_folder = QTreeWidgetItem(["📂 Connections"])
        conns_folder.setData(0, Qt.ItemDataRole.UserRole + 1, "connections_folder")
        root.addChild(conns_folder)

        for conn in self.project.connections:
            conn_item = QTreeWidgetItem([f"🔌 {conn.name}"])
            conn_item.setData(0, Qt.ItemDataRole.UserRole, conn)
            conn_item.setData(0, Qt.ItemDataRole.UserRole + 1, "connection")
            conns_folder.addChild(conn_item)

        # Expand main folders
        root.setExpanded(True)
        types_folder.setExpanded(True)
        ifaces_folder.setExpanded(True)
        comps_folder.setExpanded(True)
        conns_folder.setExpanded(True)
        
        # Also refresh composition view
        self._refresh_composition_view()

    def _on_selection_changed(self):
        """Handle tree selection change."""
        items = self.tree.selectedItems()
        if not items:
            self.editor_stack.setCurrentIndex(0)
            return

        item = items[0]
        item_type = item.data(0, Qt.ItemDataRole.UserRole + 1)
        obj = item.data(0, Qt.ItemDataRole.UserRole)

        if item_type == "swc":
            self.swc_editor.set_swc(obj)
            self.editor_stack.setCurrentIndex(1)
        elif item_type == "interface":
            self.interface_editor.set_interface(obj)
            self.editor_stack.setCurrentIndex(2)
        elif item_type == "port":
            swc = item.data(0, Qt.ItemDataRole.UserRole + 2)
            self.port_editor.set_port(obj, self.project.interfaces, self.project)
            self.editor_stack.setCurrentIndex(3)
        elif item_type == "runnable":
            self.runnable_editor.set_runnable(obj)
            self.editor_stack.setCurrentIndex(4)
        elif item_type == "data_element":
            self.data_element_editor.set_data_element(obj, self.project.application_data_types)
            self.editor_stack.setCurrentIndex(5)
        elif item_type == "operation":
            self.operation_editor.set_operation(obj, self.project.application_data_types)
            self.editor_stack.setCurrentIndex(6)
        elif item_type == "app_data_type":
            self.app_type_editor.set_app_type(obj, self.project.compu_methods)
            self.editor_stack.setCurrentIndex(7)
        elif item_type == "impl_data_type":
            self.impl_type_editor.set_impl_type(obj)
            self.editor_stack.setCurrentIndex(8)
        elif item_type == "compu_method":
            self.compu_method_editor.set_compu_method(obj)
            self.editor_stack.setCurrentIndex(9)
        elif item_type == "connection":
            self.connection_editor.set_connection(obj, self.project)
            self.editor_stack.setCurrentIndex(10)
        else:
            self.editor_stack.setCurrentIndex(0)

    def _on_editor_changed(self):
        """Handle editor value changes."""
        self._modified = True
        self._update_title()
        self._refresh_tree()
        self._refresh_composition_view()

    def _refresh_composition_view(self):
        """Refresh the graphical composition view."""
        self.composition_view.load_project(self.project)

    def _update_title(self):
        """Update window title."""
        title = f"AUTOSAR Designer - {self.project.name}"
        if self._modified:
            title += " *"
        self.setWindowTitle(title)

    # --- Project operations ---

    def _new_project(self):
        """Create a new project."""
        if self._modified:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "Save changes before creating new project?",
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Save:
                self._save_project()
            elif reply == QMessageBox.StandardButton.Cancel:
                return

        self.project = Project(name="New Project")
        self.project_path = None
        self._modified = False
        self._refresh_tree()
        self._update_title()
        self.statusBar().showMessage("New project created")

    def _open_project(self):
        """Open a project from YAML file."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "", "YAML Files (*.yaml *.yml);;All Files (*)"
        )
        if filepath:
            try:
                self.project = load_project(Path(filepath))
                self.project_path = Path(filepath)
                self._modified = False
                self._refresh_tree()
                self._update_title()
                self.statusBar().showMessage(f"Opened: {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open project:\n{e}")

    def _save_project(self):
        """Save the current project."""
        if self.project_path is None:
            self._save_project_as()
        else:
            try:
                save_project(self.project, self.project_path)
                self._modified = False
                self._update_title()
                self.statusBar().showMessage(f"Saved: {self.project_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save project:\n{e}")

    def _save_project_as(self):
        """Save project to a new file."""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Project", f"{self.project.name}.yaml",
            "YAML Files (*.yaml);;All Files (*)"
        )
        if filepath:
            self.project_path = Path(filepath)
            self._save_project()

    def _load_example(self):
        """Load the example project."""
        if self._modified:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "Discard changes and load example?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        self.project = create_example_project()
        self.project_path = None
        self._modified = False
        self._refresh_tree()
        self._update_title()
        self.statusBar().showMessage("Example project loaded")

    # --- Add operations ---

    def _add_swc(self):
        """Add a new software component."""
        name = f"Swc_New{len(self.project.components) + 1}"
        swc = SoftwareComponent(name=name)
        self.project.components.append(swc)
        self._modified = True
        self._refresh_tree()
        self._update_title()
        self.statusBar().showMessage(f"Added component: {name}")

    def _add_interface(self):
        """Add a new interface."""
        name = f"If_New{len(self.project.interfaces) + 1}"
        iface = Interface(name=name)
        self.project.interfaces.append(iface)
        self._modified = True
        self._refresh_tree()
        self._update_title()
        self.statusBar().showMessage(f"Added interface: {name}")

    def _add_port(self, swc_item: QTreeWidgetItem):
        """Add a port to an SWC."""
        swc = swc_item.data(0, Qt.ItemDataRole.UserRole)
        name = f"Port_{len(swc.ports) + 1}"
        port = Port(name=name)
        swc.ports.append(port)
        self._modified = True
        self._refresh_tree()
        self._update_title()

    def _add_runnable(self, swc_item: QTreeWidgetItem):
        """Add a runnable to an SWC."""
        swc = swc_item.data(0, Qt.ItemDataRole.UserRole)
        name = f"Run_{len(swc.runnables) + 1}"
        runnable = Runnable(name=name)
        swc.runnables.append(runnable)
        self._modified = True
        self._refresh_tree()
        self._update_title()

    def _add_data_element(self, iface_item: QTreeWidgetItem):
        """Add a data element to an interface."""
        iface = iface_item.data(0, Qt.ItemDataRole.UserRole)
        name = f"DataElement_{len(iface.data_elements) + 1}"
        de = DataElement(name=name)
        iface.data_elements.append(de)
        self._modified = True
        self._refresh_tree()
        self._update_title()

    def _add_operation(self, iface_item: QTreeWidgetItem):
        """Add an operation to an interface."""
        iface = iface_item.data(0, Qt.ItemDataRole.UserRole)
        name = f"Operation_{len(iface.operations) + 1}"
        op = Operation(name=name)
        iface.operations.append(op)
        self._modified = True
        self._refresh_tree()
        self._update_title()

    def _add_app_data_type(self):
        """Add a new application data type."""
        name = f"AppType_{len(self.project.application_data_types) + 1}"
        adt = ApplicationDataType(name=name)
        self.project.application_data_types.append(adt)
        self._modified = True
        self._refresh_tree()
        self._update_title()
        self.statusBar().showMessage(f"Added application type: {name}")

    def _add_impl_data_type(self):
        """Add a new implementation data type."""
        name = f"ImplType_{len(self.project.implementation_data_types) + 1}"
        idt = ImplementationDataType(name=name)
        self.project.implementation_data_types.append(idt)
        self._modified = True
        self._refresh_tree()
        self._update_title()
        self.statusBar().showMessage(f"Added implementation type: {name}")

    def _add_compu_method(self):
        """Add a new compu method."""
        name = f"CM_{len(self.project.compu_methods) + 1}"
        cm = CompuMethod(name=name)
        self.project.compu_methods.append(cm)
        self._modified = True
        self._refresh_tree()
        self._update_title()
        self.statusBar().showMessage(f"Added CompuMethod: {name}")

    def _add_connection(self):
        """Add a new port connection via dialog."""
        from gui.dialogs import ConnectionDialog
        dialog = ConnectionDialog(self.project, self)
        if dialog.exec():
            conn = dialog.get_connection()
            if conn:
                self.project.connections.append(conn)
                self._modified = True
                self._refresh_tree()
                self._update_title()
                self.statusBar().showMessage(f"Added connection: {conn.name}")

    def _create_connection_from_port(self, provider_swc: SoftwareComponent, provider_port: Port):
        """Create a connection starting from a provided port."""
        from gui.dialogs import ConnectionDialog
        dialog = ConnectionDialog(self.project, self, provider_swc, provider_port)
        if dialog.exec():
            conn = dialog.get_connection()
            if conn:
                self.project.connections.append(conn)
                self._modified = True
                self._refresh_tree()
                self._update_title()
                self.statusBar().showMessage(f"Added connection: {conn.name}")

    def _delete_item(self, item: QTreeWidgetItem):
        """Delete a tree item."""
        item_type = item.data(0, Qt.ItemDataRole.UserRole + 1)
        obj = item.data(0, Qt.ItemDataRole.UserRole)

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete {item_type}: {obj.name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        if item_type == "swc":
            # Also remove any connections involving this SWC's ports
            ports_to_remove = [p.uid for p in obj.ports]
            self.project.connections = [
                c for c in self.project.connections
                if c.provider_port_uid not in ports_to_remove and c.requester_port_uid not in ports_to_remove
            ]
            self.project.components.remove(obj)
        elif item_type == "interface":
            self.project.interfaces.remove(obj)
        elif item_type == "port":
            parent_swc = item.data(0, Qt.ItemDataRole.UserRole + 2)
            # Remove any connections involving this port
            self.project.connections = [
                c for c in self.project.connections
                if c.provider_port_uid != obj.uid and c.requester_port_uid != obj.uid
            ]
            parent_swc.ports.remove(obj)
        elif item_type == "runnable":
            parent_swc = item.data(0, Qt.ItemDataRole.UserRole + 2)
            parent_swc.runnables.remove(obj)
        elif item_type == "data_element":
            parent_iface = item.data(0, Qt.ItemDataRole.UserRole + 2)
            parent_iface.data_elements.remove(obj)
        elif item_type == "operation":
            parent_iface = item.data(0, Qt.ItemDataRole.UserRole + 2)
            parent_iface.operations.remove(obj)
        elif item_type == "app_data_type":
            self.project.application_data_types.remove(obj)
        elif item_type == "impl_data_type":
            self.project.implementation_data_types.remove(obj)
        elif item_type == "compu_method":
            self.project.compu_methods.remove(obj)
        elif item_type == "connection":
            self.project.connections.remove(obj)

        self._modified = True
        self._refresh_tree()
        self._update_title()

    # --- Code generation ---

    def _generate_code(self):
        """Generate code for the project."""
        if not self.project.components:
            QMessageBox.warning(self, "No Components", "Add at least one component before generating code.")
            return

        output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if output_dir:
            try:
                generated = generate_project_code(self.project, Path(output_dir))
                file_list = "\n".join([f.name for f in generated])
                QMessageBox.information(
                    self, "Code Generated",
                    f"Generated {len(generated)} files:\n\n{file_list}"
                )
                self.statusBar().showMessage(f"Generated {len(generated)} files to {output_dir}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Code generation failed:\n{e}")

    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self, "About AUTOSAR Designer",
            "AUTOSAR Designer v0.1\n\n"
            "A lightweight tool for designing AUTOSAR-like software components "
            "with YAML-based configuration and Jinja2 code generation.\n\n"
            "Built with PyQt6 and Python."
        )


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Set application font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
