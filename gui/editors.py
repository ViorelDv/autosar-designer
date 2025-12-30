"""
Property editors for project elements.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QTextEdit, QSpinBox, QComboBox, QPushButton,
    QGroupBox, QFrame, QScrollArea, QSizePolicy, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from model import (
    SoftwareComponent, Interface, Port, Runnable,
    DataElement, Operation, OperationArgument, InterfaceType, PortDirection, 
    BaseDataType, ApplicationDataType, ImplementationDataType, CompuMethod,
    DataTypeMapping, AppDataCategory, ArgumentDirection, PortConnection, Project
)


class EditorStyleMixin:
    """Common styling for editors."""

    EDITOR_STYLE = """
        QWidget {
            background-color: #1e1e1e;
            color: #d4d4d4;
        }
        QLabel {
            color: #9cdcfe;
            font-weight: bold;
        }
        QLineEdit, QTextEdit, QSpinBox, QComboBox {
            background-color: #3c3c3c;
            color: #d4d4d4;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 5px;
        }
        QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {
            border: 1px solid #007acc;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #454545;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
            color: #569cd6;
        }
        QPushButton {
            background-color: #0e639c;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #1177bb;
        }
        QPushButton:pressed {
            background-color: #094771;
        }
    """

    def apply_editor_style(self):
        self.setStyleSheet(self.EDITOR_STYLE)


class WelcomePanel(QWidget, EditorStyleMixin):
    """Welcome panel shown when no item is selected."""

    def __init__(self):
        super().__init__()
        self.apply_editor_style()
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("AUTOSAR Designer")
        title.setStyleSheet("font-size: 24px; color: #569cd6; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Select an item from the tree to edit its properties")
        subtitle.setStyleSheet("font-size: 14px; color: #808080;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        tips = QLabel(
            "\n\n"
            "Quick Tips:\n"
            "• Right-click on tree items to add/delete elements\n"
            "• Use toolbar buttons to add Components and Interfaces\n"
            "• Press F5 to generate code\n"
            "• Load the example project to see a complete setup"
        )
        tips.setStyleSheet("font-size: 12px; color: #6a9955;")
        tips.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(tips)


class SwcEditor(QWidget, EditorStyleMixin):
    """Editor for Software Components."""
    
    changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.swc: SoftwareComponent = None
        self._updating = False
        self.apply_editor_style()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("Software Component")
        header.setStyleSheet("font-size: 18px; color: #569cd6; font-weight: bold; padding-bottom: 10px;")
        layout.addWidget(header)

        # Form
        form = QFormLayout()
        form.setSpacing(10)

        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self._on_name_changed)
        form.addRow("Name:", self.name_edit)

        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(100)
        self.desc_edit.textChanged.connect(self._on_desc_changed)
        form.addRow("Description:", self.desc_edit)

        self.uid_label = QLabel()
        self.uid_label.setStyleSheet("color: #808080;")
        form.addRow("UID:", self.uid_label)

        layout.addLayout(form)

        # Info section
        info_group = QGroupBox("Component Info")
        info_layout = QFormLayout(info_group)
        self.ports_count = QLabel("0")
        self.runnables_count = QLabel("0")
        info_layout.addRow("Ports:", self.ports_count)
        info_layout.addRow("Runnables:", self.runnables_count)
        layout.addWidget(info_group)

        layout.addStretch()

    def set_swc(self, swc: SoftwareComponent):
        self._updating = True
        self.swc = swc
        self.name_edit.setText(swc.name)
        self.desc_edit.setPlainText(swc.description)
        self.uid_label.setText(swc.uid)
        self.ports_count.setText(str(len(swc.ports)))
        self.runnables_count.setText(str(len(swc.runnables)))
        self._updating = False

    def _on_name_changed(self, text):
        if not self._updating and self.swc:
            self.swc.name = text
            self.changed.emit()

    def _on_desc_changed(self):
        if not self._updating and self.swc:
            self.swc.description = self.desc_edit.toPlainText()
            self.changed.emit()


class InterfaceEditor(QWidget, EditorStyleMixin):
    """Editor for Interfaces."""
    
    changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.interface: Interface = None
        self._updating = False
        self.apply_editor_style()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("Interface")
        header.setStyleSheet("font-size: 18px; color: #569cd6; font-weight: bold; padding-bottom: 10px;")
        layout.addWidget(header)

        form = QFormLayout()
        form.setSpacing(10)

        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self._on_name_changed)
        form.addRow("Name:", self.name_edit)

        self.type_combo = QComboBox()
        self.type_combo.addItem("Sender/Receiver", InterfaceType.SENDER_RECEIVER)
        self.type_combo.addItem("Client/Server", InterfaceType.CLIENT_SERVER)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        form.addRow("Type:", self.type_combo)

        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(100)
        self.desc_edit.textChanged.connect(self._on_desc_changed)
        form.addRow("Description:", self.desc_edit)

        self.uid_label = QLabel()
        self.uid_label.setStyleSheet("color: #808080;")
        form.addRow("UID:", self.uid_label)

        layout.addLayout(form)
        layout.addStretch()

    def set_interface(self, interface: Interface):
        self._updating = True
        self.interface = interface
        self.name_edit.setText(interface.name)
        self.desc_edit.setPlainText(interface.description)
        self.uid_label.setText(interface.uid)
        
        idx = 0 if interface.interface_type == InterfaceType.SENDER_RECEIVER else 1
        self.type_combo.setCurrentIndex(idx)
        self._updating = False

    def _on_name_changed(self, text):
        if not self._updating and self.interface:
            self.interface.name = text
            self.changed.emit()

    def _on_desc_changed(self):
        if not self._updating and self.interface:
            self.interface.description = self.desc_edit.toPlainText()
            self.changed.emit()

    def _on_type_changed(self, index):
        if not self._updating and self.interface:
            self.interface.interface_type = self.type_combo.currentData()
            self.changed.emit()


class PortEditor(QWidget, EditorStyleMixin):
    """Editor for Ports."""
    
    changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.port: Port = None
        self._updating = False
        self._interfaces = []
        self.apply_editor_style()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("Port")
        header.setStyleSheet("font-size: 18px; color: #569cd6; font-weight: bold; padding-bottom: 10px;")
        layout.addWidget(header)

        form = QFormLayout()
        form.setSpacing(10)

        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self._on_name_changed)
        form.addRow("Name:", self.name_edit)

        self.dir_combo = QComboBox()
        self.dir_combo.addItem("Required (Client/Receiver)", PortDirection.REQUIRED)
        self.dir_combo.addItem("Provided (Server/Sender)", PortDirection.PROVIDED)
        self.dir_combo.currentIndexChanged.connect(self._on_dir_changed)
        form.addRow("Direction:", self.dir_combo)

        self.iface_combo = QComboBox()
        self.iface_combo.currentIndexChanged.connect(self._on_iface_changed)
        form.addRow("Interface:", self.iface_combo)

        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(100)
        self.desc_edit.textChanged.connect(self._on_desc_changed)
        form.addRow("Description:", self.desc_edit)

        layout.addLayout(form)

        # Connections section
        conn_group = QGroupBox("Connections")
        conn_layout = QVBoxLayout(conn_group)
        self.conn_label = QLabel("No connections")
        self.conn_label.setStyleSheet("color: #808080;")
        conn_layout.addWidget(self.conn_label)
        layout.addWidget(conn_group)

        layout.addStretch()

    def set_port(self, port: Port, interfaces: list, project: Project = None):
        self._updating = True
        self.port = port
        self._interfaces = interfaces
        
        self.name_edit.setText(port.name)
        self.desc_edit.setPlainText(port.description)
        
        idx = 0 if port.direction == PortDirection.REQUIRED else 1
        self.dir_combo.setCurrentIndex(idx)
        
        # Populate interface combo
        self.iface_combo.clear()
        self.iface_combo.addItem("(None)", None)
        selected_idx = 0
        for i, iface in enumerate(interfaces):
            self.iface_combo.addItem(iface.name, iface.uid)
            if iface.uid == port.interface_uid:
                selected_idx = i + 1
        self.iface_combo.setCurrentIndex(selected_idx)
        
        # Show connections
        if project:
            connections = project.get_connections_for_port(port.uid)
            if connections:
                conn_texts = []
                for conn in connections:
                    # Find the other end
                    if conn.provider_port_uid == port.uid:
                        other_swc = project.get_component_by_uid(conn.requester_swc_uid)
                        other_port = other_swc.get_port_by_uid(conn.requester_port_uid) if other_swc else None
                        direction = "→"
                    else:
                        other_swc = project.get_component_by_uid(conn.provider_swc_uid)
                        other_port = other_swc.get_port_by_uid(conn.provider_port_uid) if other_swc else None
                        direction = "←"
                    
                    if other_swc and other_port:
                        conn_texts.append(f"🔌 {direction} {other_swc.name}.{other_port.name}")
                
                self.conn_label.setText("\n".join(conn_texts))
                self.conn_label.setStyleSheet("color: #4ec9b0;")
            else:
                self.conn_label.setText("No connections")
                self.conn_label.setStyleSheet("color: #808080;")
        
        self._updating = False

    def _on_name_changed(self, text):
        if not self._updating and self.port:
            self.port.name = text
            self.changed.emit()

    def _on_desc_changed(self):
        if not self._updating and self.port:
            self.port.description = self.desc_edit.toPlainText()
            self.changed.emit()

    def _on_dir_changed(self, index):
        if not self._updating and self.port:
            self.port.direction = self.dir_combo.currentData()
            self.changed.emit()

    def _on_iface_changed(self, index):
        if not self._updating and self.port:
            self.port.interface_uid = self.iface_combo.currentData()
            self.changed.emit()


class RunnableEditor(QWidget, EditorStyleMixin):
    """Editor for Runnables."""
    
    changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.runnable: Runnable = None
        self._updating = False
        self.apply_editor_style()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("Runnable")
        header.setStyleSheet("font-size: 18px; color: #569cd6; font-weight: bold; padding-bottom: 10px;")
        layout.addWidget(header)

        form = QFormLayout()
        form.setSpacing(10)

        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self._on_name_changed)
        form.addRow("Name:", self.name_edit)

        self.period_spin = QSpinBox()
        self.period_spin.setRange(0, 10000)
        self.period_spin.setSuffix(" ms")
        self.period_spin.setSpecialValueText("Event-triggered")
        self.period_spin.valueChanged.connect(self._on_period_changed)
        form.addRow("Period:", self.period_spin)

        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(100)
        self.desc_edit.textChanged.connect(self._on_desc_changed)
        form.addRow("Description:", self.desc_edit)

        layout.addLayout(form)

        # Tip
        tip = QLabel("💡 Set period to 0 for event-triggered runnables")
        tip.setStyleSheet("color: #6a9955; padding-top: 10px;")
        layout.addWidget(tip)

        layout.addStretch()

    def set_runnable(self, runnable: Runnable):
        self._updating = True
        self.runnable = runnable
        self.name_edit.setText(runnable.name)
        self.period_spin.setValue(runnable.period_ms)
        self.desc_edit.setPlainText(runnable.description)
        self._updating = False

    def _on_name_changed(self, text):
        if not self._updating and self.runnable:
            self.runnable.name = text
            self.changed.emit()

    def _on_period_changed(self, value):
        if not self._updating and self.runnable:
            self.runnable.period_ms = value
            self.changed.emit()

    def _on_desc_changed(self):
        if not self._updating and self.runnable:
            self.runnable.description = self.desc_edit.toPlainText()
            self.changed.emit()


class DataElementEditor(QWidget, EditorStyleMixin):
    """Editor for Data Elements."""
    
    changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.data_element: DataElement = None
        self._app_types = []
        self._updating = False
        self.apply_editor_style()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("Data Element")
        header.setStyleSheet("font-size: 18px; color: #569cd6; font-weight: bold; padding-bottom: 10px;")
        layout.addWidget(header)

        form = QFormLayout()
        form.setSpacing(10)

        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self._on_name_changed)
        form.addRow("Name:", self.name_edit)

        self.app_type_combo = QComboBox()
        self.app_type_combo.currentIndexChanged.connect(self._on_app_type_changed)
        form.addRow("Application Type:", self.app_type_combo)

        self.type_combo = QComboBox()
        for dt in BaseDataType:
            self.type_combo.addItem(dt.value, dt)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        form.addRow("Base Type (fallback):", self.type_combo)

        self.init_edit = QLineEdit()
        self.init_edit.textChanged.connect(self._on_init_changed)
        form.addRow("Init Value:", self.init_edit)

        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(100)
        self.desc_edit.textChanged.connect(self._on_desc_changed)
        form.addRow("Description:", self.desc_edit)

        layout.addLayout(form)
        layout.addStretch()

    def set_data_element(self, de: DataElement, app_types: list = None):
        self._updating = True
        self.data_element = de
        self._app_types = app_types or []
        
        self.name_edit.setText(de.name)
        self.init_edit.setText(de.init_value)
        self.desc_edit.setPlainText(de.description)
        
        # Populate app type combo
        self.app_type_combo.clear()
        self.app_type_combo.addItem("(None - use base type)", None)
        selected_idx = 0
        for i, adt in enumerate(self._app_types):
            self.app_type_combo.addItem(adt.name, adt.uid)
            if adt.uid == de.app_type_uid:
                selected_idx = i + 1
        self.app_type_combo.setCurrentIndex(selected_idx)
        
        # Base type
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == de.base_type:
                self.type_combo.setCurrentIndex(i)
                break
        
        self._updating = False

    def _on_name_changed(self, text):
        if not self._updating and self.data_element:
            self.data_element.name = text
            self.changed.emit()

    def _on_app_type_changed(self, index):
        if not self._updating and self.data_element:
            self.data_element.app_type_uid = self.app_type_combo.currentData()
            self.changed.emit()

    def _on_type_changed(self, index):
        if not self._updating and self.data_element:
            self.data_element.base_type = self.type_combo.currentData()
            self.changed.emit()

    def _on_init_changed(self, text):
        if not self._updating and self.data_element:
            self.data_element.init_value = text
            self.changed.emit()

    def _on_desc_changed(self):
        if not self._updating and self.data_element:
            self.data_element.description = self.desc_edit.toPlainText()
            self.changed.emit()


class OperationEditor(QWidget, EditorStyleMixin):
    """Editor for Operations."""
    
    changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.operation: Operation = None
        self._app_types = []
        self._updating = False
        self.apply_editor_style()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("Operation")
        header.setStyleSheet("font-size: 18px; color: #569cd6; font-weight: bold; padding-bottom: 10px;")
        layout.addWidget(header)

        form = QFormLayout()
        form.setSpacing(10)

        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self._on_name_changed)
        form.addRow("Name:", self.name_edit)

        self.return_combo = QComboBox()
        for dt in BaseDataType:
            self.return_combo.addItem(dt.value, dt)
        self.return_combo.currentIndexChanged.connect(self._on_return_changed)
        form.addRow("Return Type:", self.return_combo)

        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(100)
        self.desc_edit.textChanged.connect(self._on_desc_changed)
        form.addRow("Description:", self.desc_edit)

        layout.addLayout(form)

        # Arguments section
        args_group = QGroupBox("Arguments")
        args_layout = QVBoxLayout(args_group)
        self.args_label = QLabel("No arguments defined")
        args_layout.addWidget(self.args_label)
        layout.addWidget(args_group)

        layout.addStretch()

    def set_operation(self, op: Operation, app_types: list = None):
        self._updating = True
        self.operation = op
        self._app_types = app_types or []
        
        self.name_edit.setText(op.name)
        self.desc_edit.setPlainText(op.description)
        
        for i in range(self.return_combo.count()):
            if self.return_combo.itemData(i) == op.return_base_type:
                self.return_combo.setCurrentIndex(i)
                break
        
        # Update arguments display
        if op.arguments:
            args_text = "\n".join([
                f"• {arg.name}: {arg.base_type.value} ({arg.direction.value})"
                for arg in op.arguments
            ])
            self.args_label.setText(args_text)
        else:
            self.args_label.setText("No arguments defined")
        
        self._updating = False

    def _on_name_changed(self, text):
        if not self._updating and self.operation:
            self.operation.name = text
            self.changed.emit()

    def _on_return_changed(self, index):
        if not self._updating and self.operation:
            self.operation.return_base_type = self.return_combo.currentData()
            self.changed.emit()

    def _on_desc_changed(self):
        if not self._updating and self.operation:
            self.operation.description = self.desc_edit.toPlainText()
            self.changed.emit()


# =============================================================================
# NEW EDITORS FOR DATA TYPES AND CONNECTIONS
# =============================================================================

class AppDataTypeEditor(QWidget, EditorStyleMixin):
    """Editor for Application Data Types."""
    
    changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.app_type: ApplicationDataType = None
        self._compu_methods = []
        self._updating = False
        self.apply_editor_style()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("Application Data Type")
        header.setStyleSheet("font-size: 18px; color: #569cd6; font-weight: bold; padding-bottom: 10px;")
        layout.addWidget(header)

        form = QFormLayout()
        form.setSpacing(10)

        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self._on_name_changed)
        form.addRow("Name:", self.name_edit)

        self.category_combo = QComboBox()
        for cat in AppDataCategory:
            self.category_combo.addItem(cat.value.title(), cat)
        self.category_combo.currentIndexChanged.connect(self._on_category_changed)
        form.addRow("Category:", self.category_combo)

        self.compu_combo = QComboBox()
        self.compu_combo.currentIndexChanged.connect(self._on_compu_changed)
        form.addRow("CompuMethod:", self.compu_combo)

        self.min_spin = QDoubleSpinBox()
        self.min_spin.setRange(-1e9, 1e9)
        self.min_spin.setDecimals(2)
        self.min_spin.valueChanged.connect(self._on_min_changed)
        form.addRow("Min Value:", self.min_spin)

        self.max_spin = QDoubleSpinBox()
        self.max_spin.setRange(-1e9, 1e9)
        self.max_spin.setDecimals(2)
        self.max_spin.valueChanged.connect(self._on_max_changed)
        form.addRow("Max Value:", self.max_spin)

        self.init_edit = QLineEdit()
        self.init_edit.textChanged.connect(self._on_init_changed)
        form.addRow("Init Value:", self.init_edit)

        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(80)
        self.desc_edit.textChanged.connect(self._on_desc_changed)
        form.addRow("Description:", self.desc_edit)

        self.uid_label = QLabel()
        self.uid_label.setStyleSheet("color: #808080;")
        form.addRow("UID:", self.uid_label)

        layout.addLayout(form)
        layout.addStretch()

    def set_app_type(self, adt: ApplicationDataType, compu_methods: list = None):
        self._updating = True
        self.app_type = adt
        self._compu_methods = compu_methods or []
        
        self.name_edit.setText(adt.name)
        self.init_edit.setText(adt.init_value)
        self.desc_edit.setPlainText(adt.description)
        self.uid_label.setText(adt.uid)
        
        if adt.min_value is not None:
            self.min_spin.setValue(adt.min_value)
        if adt.max_value is not None:
            self.max_spin.setValue(adt.max_value)
        
        # Category
        for i in range(self.category_combo.count()):
            if self.category_combo.itemData(i) == adt.category:
                self.category_combo.setCurrentIndex(i)
                break
        
        # CompuMethod combo
        self.compu_combo.clear()
        self.compu_combo.addItem("(None)", None)
        selected_idx = 0
        for i, cm in enumerate(self._compu_methods):
            self.compu_combo.addItem(f"{cm.name} ({cm.unit})", cm.uid)
            if cm.uid == adt.compu_method_uid:
                selected_idx = i + 1
        self.compu_combo.setCurrentIndex(selected_idx)
        
        self._updating = False

    def _on_name_changed(self, text):
        if not self._updating and self.app_type:
            self.app_type.name = text
            self.changed.emit()

    def _on_category_changed(self, index):
        if not self._updating and self.app_type:
            self.app_type.category = self.category_combo.currentData()
            self.changed.emit()

    def _on_compu_changed(self, index):
        if not self._updating and self.app_type:
            self.app_type.compu_method_uid = self.compu_combo.currentData()
            self.changed.emit()

    def _on_min_changed(self, value):
        if not self._updating and self.app_type:
            self.app_type.min_value = value
            self.changed.emit()

    def _on_max_changed(self, value):
        if not self._updating and self.app_type:
            self.app_type.max_value = value
            self.changed.emit()

    def _on_init_changed(self, text):
        if not self._updating and self.app_type:
            self.app_type.init_value = text
            self.changed.emit()

    def _on_desc_changed(self):
        if not self._updating and self.app_type:
            self.app_type.description = self.desc_edit.toPlainText()
            self.changed.emit()


class ImplDataTypeEditor(QWidget, EditorStyleMixin):
    """Editor for Implementation Data Types."""
    
    changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.impl_type: ImplementationDataType = None
        self._updating = False
        self.apply_editor_style()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("Implementation Data Type")
        header.setStyleSheet("font-size: 18px; color: #569cd6; font-weight: bold; padding-bottom: 10px;")
        layout.addWidget(header)

        form = QFormLayout()
        form.setSpacing(10)

        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self._on_name_changed)
        form.addRow("Name:", self.name_edit)

        self.base_type_combo = QComboBox()
        for dt in BaseDataType:
            self.base_type_combo.addItem(dt.value, dt)
        self.base_type_combo.currentIndexChanged.connect(self._on_base_type_changed)
        form.addRow("Base Type:", self.base_type_combo)

        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(80)
        self.desc_edit.textChanged.connect(self._on_desc_changed)
        form.addRow("Description:", self.desc_edit)

        self.uid_label = QLabel()
        self.uid_label.setStyleSheet("color: #808080;")
        form.addRow("UID:", self.uid_label)

        layout.addLayout(form)
        layout.addStretch()

    def set_impl_type(self, idt: ImplementationDataType):
        self._updating = True
        self.impl_type = idt
        
        self.name_edit.setText(idt.name)
        self.desc_edit.setPlainText(idt.description)
        self.uid_label.setText(idt.uid)
        
        for i in range(self.base_type_combo.count()):
            if self.base_type_combo.itemData(i) == idt.base_type:
                self.base_type_combo.setCurrentIndex(i)
                break
        
        self._updating = False

    def _on_name_changed(self, text):
        if not self._updating and self.impl_type:
            self.impl_type.name = text
            self.changed.emit()

    def _on_base_type_changed(self, index):
        if not self._updating and self.impl_type:
            self.impl_type.base_type = self.base_type_combo.currentData()
            self.changed.emit()

    def _on_desc_changed(self):
        if not self._updating and self.impl_type:
            self.impl_type.description = self.desc_edit.toPlainText()
            self.changed.emit()


class CompuMethodEditor(QWidget, EditorStyleMixin):
    """Editor for Computation Methods (scaling)."""
    
    changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.compu_method: CompuMethod = None
        self._updating = False
        self.apply_editor_style()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("CompuMethod (Scaling)")
        header.setStyleSheet("font-size: 18px; color: #569cd6; font-weight: bold; padding-bottom: 10px;")
        layout.addWidget(header)

        form = QFormLayout()
        form.setSpacing(10)

        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self._on_name_changed)
        form.addRow("Name:", self.name_edit)

        self.factor_spin = QDoubleSpinBox()
        self.factor_spin.setRange(-1e9, 1e9)
        self.factor_spin.setDecimals(6)
        self.factor_spin.valueChanged.connect(self._on_factor_changed)
        form.addRow("Factor:", self.factor_spin)

        self.offset_spin = QDoubleSpinBox()
        self.offset_spin.setRange(-1e9, 1e9)
        self.offset_spin.setDecimals(6)
        self.offset_spin.valueChanged.connect(self._on_offset_changed)
        form.addRow("Offset:", self.offset_spin)

        self.unit_edit = QLineEdit()
        self.unit_edit.textChanged.connect(self._on_unit_changed)
        form.addRow("Unit:", self.unit_edit)

        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(80)
        self.desc_edit.textChanged.connect(self._on_desc_changed)
        form.addRow("Description:", self.desc_edit)

        layout.addLayout(form)

        # Formula display
        formula_group = QGroupBox("Formula")
        formula_layout = QVBoxLayout(formula_group)
        self.formula_label = QLabel("physical = (internal × factor) + offset")
        self.formula_label.setStyleSheet("color: #6a9955; font-family: monospace;")
        formula_layout.addWidget(self.formula_label)
        layout.addWidget(formula_group)

        layout.addStretch()

    def set_compu_method(self, cm: CompuMethod):
        self._updating = True
        self.compu_method = cm
        
        self.name_edit.setText(cm.name)
        self.factor_spin.setValue(cm.factor)
        self.offset_spin.setValue(cm.offset)
        self.unit_edit.setText(cm.unit)
        self.desc_edit.setPlainText(cm.description)
        
        self._update_formula()
        self._updating = False

    def _update_formula(self):
        if self.compu_method:
            f = self.compu_method.factor
            o = self.compu_method.offset
            u = self.compu_method.unit or "?"
            self.formula_label.setText(f"physical [{u}] = (internal × {f}) + {o}")

    def _on_name_changed(self, text):
        if not self._updating and self.compu_method:
            self.compu_method.name = text
            self.changed.emit()

    def _on_factor_changed(self, value):
        if not self._updating and self.compu_method:
            self.compu_method.factor = value
            self._update_formula()
            self.changed.emit()

    def _on_offset_changed(self, value):
        if not self._updating and self.compu_method:
            self.compu_method.offset = value
            self._update_formula()
            self.changed.emit()

    def _on_unit_changed(self, text):
        if not self._updating and self.compu_method:
            self.compu_method.unit = text
            self._update_formula()
            self.changed.emit()

    def _on_desc_changed(self):
        if not self._updating and self.compu_method:
            self.compu_method.description = self.desc_edit.toPlainText()
            self.changed.emit()


class ConnectionEditor(QWidget, EditorStyleMixin):
    """Editor for Port Connections."""
    
    changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.connection: PortConnection = None
        self._project: Project = None
        self._updating = False
        self.apply_editor_style()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("Port Connection")
        header.setStyleSheet("font-size: 18px; color: #569cd6; font-weight: bold; padding-bottom: 10px;")
        layout.addWidget(header)

        form = QFormLayout()
        form.setSpacing(10)

        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self._on_name_changed)
        form.addRow("Name:", self.name_edit)

        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(80)
        self.desc_edit.textChanged.connect(self._on_desc_changed)
        form.addRow("Description:", self.desc_edit)

        layout.addLayout(form)

        # Provider info
        provider_group = QGroupBox("Provider (Sender/Server)")
        provider_layout = QFormLayout(provider_group)
        self.provider_swc_label = QLabel()
        self.provider_port_label = QLabel()
        provider_layout.addRow("Component:", self.provider_swc_label)
        provider_layout.addRow("Port:", self.provider_port_label)
        layout.addWidget(provider_group)

        # Requester info
        requester_group = QGroupBox("Requester (Receiver/Client)")
        requester_layout = QFormLayout(requester_group)
        self.requester_swc_label = QLabel()
        self.requester_port_label = QLabel()
        requester_layout.addRow("Component:", self.requester_swc_label)
        requester_layout.addRow("Port:", self.requester_port_label)
        layout.addWidget(requester_group)

        # Interface info
        iface_group = QGroupBox("Interface")
        iface_layout = QFormLayout(iface_group)
        self.interface_label = QLabel()
        iface_layout.addRow("Name:", self.interface_label)
        layout.addWidget(iface_group)

        layout.addStretch()

    def set_connection(self, conn: PortConnection, project: Project):
        self._updating = True
        self.connection = conn
        self._project = project
        
        self.name_edit.setText(conn.name)
        self.desc_edit.setPlainText(conn.description)
        
        # Resolve references
        provider_swc = project.get_component_by_uid(conn.provider_swc_uid)
        requester_swc = project.get_component_by_uid(conn.requester_swc_uid)
        
        if provider_swc:
            self.provider_swc_label.setText(provider_swc.name)
            provider_port = provider_swc.get_port_by_uid(conn.provider_port_uid)
            if provider_port:
                self.provider_port_label.setText(provider_port.name)
                iface = project.get_interface_by_uid(provider_port.interface_uid)
                if iface:
                    self.interface_label.setText(iface.name)
        
        if requester_swc:
            self.requester_swc_label.setText(requester_swc.name)
            requester_port = requester_swc.get_port_by_uid(conn.requester_port_uid)
            if requester_port:
                self.requester_port_label.setText(requester_port.name)
        
        self._updating = False

    def _on_name_changed(self, text):
        if not self._updating and self.connection:
            self.connection.name = text
            self.changed.emit()

    def _on_desc_changed(self):
        if not self._updating and self.connection:
            self.connection.description = self.desc_edit.toPlainText()
            self.changed.emit()
