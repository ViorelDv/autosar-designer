"""
Property editors for project elements.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QTextEdit, QSpinBox, QComboBox, QPushButton,
    QGroupBox, QFrame, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from model import (
    SoftwareComponent, Interface, Port, Runnable,
    DataElement, Operation, InterfaceType, PortDirection, DataType
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
        layout.addStretch()

    def set_port(self, port: Port, interfaces: list):
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

        self.type_combo = QComboBox()
        for dt in DataType:
            self.type_combo.addItem(dt.value, dt)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        form.addRow("Data Type:", self.type_combo)

        self.init_edit = QLineEdit()
        self.init_edit.textChanged.connect(self._on_init_changed)
        form.addRow("Init Value:", self.init_edit)

        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(100)
        self.desc_edit.textChanged.connect(self._on_desc_changed)
        form.addRow("Description:", self.desc_edit)

        layout.addLayout(form)
        layout.addStretch()

    def set_data_element(self, de: DataElement):
        self._updating = True
        self.data_element = de
        self.name_edit.setText(de.name)
        self.init_edit.setText(de.init_value)
        self.desc_edit.setPlainText(de.description)
        
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == de.data_type:
                self.type_combo.setCurrentIndex(i)
                break
        
        self._updating = False

    def _on_name_changed(self, text):
        if not self._updating and self.data_element:
            self.data_element.name = text
            self.changed.emit()

    def _on_type_changed(self, index):
        if not self._updating and self.data_element:
            self.data_element.data_type = self.type_combo.currentData()
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
        for dt in DataType:
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
        args_layout.addWidget(QLabel("Arguments editor coming soon..."))
        args_layout.addWidget(QLabel("(Currently only editable via YAML)"))
        layout.addWidget(args_group)

        layout.addStretch()

    def set_operation(self, op: Operation):
        self._updating = True
        self.operation = op
        self.name_edit.setText(op.name)
        self.desc_edit.setPlainText(op.description)
        
        for i in range(self.return_combo.count()):
            if self.return_combo.itemData(i) == op.return_type:
                self.return_combo.setCurrentIndex(i)
                break
        
        self._updating = False

    def _on_name_changed(self, text):
        if not self._updating and self.operation:
            self.operation.name = text
            self.changed.emit()

    def _on_return_changed(self, index):
        if not self._updating and self.operation:
            self.operation.return_type = self.return_combo.currentData()
            self.changed.emit()

    def _on_desc_changed(self):
        if not self._updating and self.operation:
            self.operation.description = self.desc_edit.toPlainText()
            self.changed.emit()
