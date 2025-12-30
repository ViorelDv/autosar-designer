"""
Dialogs for AUTOSAR Designer.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt

from model import (
    Project, SoftwareComponent, Port, PortDirection, PortConnection
)


class ConnectionDialog(QDialog):
    """Dialog for creating a new port connection."""

    def __init__(self, project: Project, parent=None, 
                 preset_provider_swc: SoftwareComponent = None,
                 preset_provider_port: Port = None):
        super().__init__(parent)
        self.project = project
        self._preset_provider_swc = preset_provider_swc
        self._preset_provider_port = preset_provider_port
        self._connection: PortConnection = None
        
        self.setWindowTitle("Create Port Connection")
        self.setMinimumWidth(450)
        self._setup_ui()
        self._apply_style()
        
        # Apply presets if provided
        if preset_provider_swc and preset_provider_port:
            self._apply_preset()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Connection name
        name_layout = QFormLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., Conn_VehicleSpeed")
        name_layout.addRow("Connection Name:", self.name_edit)
        layout.addLayout(name_layout)

        # Provider (Sender/Server) section
        provider_group = QGroupBox("Provider (Sender/Server)")
        provider_layout = QFormLayout(provider_group)
        
        self.provider_swc_combo = QComboBox()
        self.provider_swc_combo.currentIndexChanged.connect(self._on_provider_swc_changed)
        provider_layout.addRow("Component:", self.provider_swc_combo)
        
        self.provider_port_combo = QComboBox()
        self.provider_port_combo.currentIndexChanged.connect(self._on_provider_port_changed)
        provider_layout.addRow("Port:", self.provider_port_combo)
        
        layout.addWidget(provider_group)

        # Arrow indicator
        arrow_label = QLabel("↓")
        arrow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        arrow_label.setStyleSheet("font-size: 24px; color: #4ec9b0;")
        layout.addWidget(arrow_label)

        # Requester (Receiver/Client) section
        requester_group = QGroupBox("Requester (Receiver/Client)")
        requester_layout = QFormLayout(requester_group)
        
        self.requester_swc_combo = QComboBox()
        self.requester_swc_combo.currentIndexChanged.connect(self._on_requester_swc_changed)
        requester_layout.addRow("Component:", self.requester_swc_combo)
        
        self.requester_port_combo = QComboBox()
        requester_layout.addRow("Port:", self.requester_port_combo)
        
        layout.addWidget(requester_group)

        # Interface info
        self.interface_label = QLabel("Select ports with matching interface")
        self.interface_label.setStyleSheet("color: #808080; font-style: italic;")
        layout.addWidget(self.interface_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        self.create_btn = QPushButton("Create Connection")
        self.create_btn.clicked.connect(self._create_connection)
        self.create_btn.setEnabled(False)
        button_layout.addWidget(self.create_btn)
        
        layout.addLayout(button_layout)

        # Populate provider SWC combo
        self._populate_provider_swcs()

    def _apply_style(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #252526;
                color: #d4d4d4;
            }
            QLabel {
                color: #d4d4d4;
            }
            QLineEdit, QComboBox {
                background-color: #3c3c3c;
                color: #d4d4d4;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px;
                min-height: 25px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #007acc;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #454545;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: #569cd6;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:disabled {
                background-color: #4a4a4a;
                color: #808080;
            }
        """)

    def _populate_provider_swcs(self):
        """Populate provider SWC combo with components that have provided ports."""
        self.provider_swc_combo.clear()
        self.provider_swc_combo.addItem("(Select component)", None)
        
        for swc in self.project.components:
            # Only show SWCs that have provided ports
            provided_ports = [p for p in swc.ports if p.direction == PortDirection.PROVIDED]
            if provided_ports:
                self.provider_swc_combo.addItem(swc.name, swc)

    def _on_provider_swc_changed(self, index):
        """Update provider port combo when SWC changes."""
        self.provider_port_combo.clear()
        self.provider_port_combo.addItem("(Select port)", None)
        
        swc = self.provider_swc_combo.currentData()
        if swc:
            for port in swc.ports:
                if port.direction == PortDirection.PROVIDED and port.interface_uid:
                    iface = self.project.get_interface_by_uid(port.interface_uid)
                    iface_name = iface.name if iface else "?"
                    self.provider_port_combo.addItem(f"{port.name} [{iface_name}]", port)
        
        self._update_requester_options()

    def _on_provider_port_changed(self, index):
        """Update requester options when provider port changes."""
        self._update_requester_options()
        self._update_interface_label()
        self._validate()

    def _update_requester_options(self):
        """Update requester combos based on selected provider port."""
        self.requester_swc_combo.clear()
        self.requester_swc_combo.addItem("(Select component)", None)
        
        provider_port = self.provider_port_combo.currentData()
        if not provider_port or not provider_port.interface_uid:
            return
        
        # Find all SWCs with required ports matching the interface
        for swc in self.project.components:
            matching_ports = [
                p for p in swc.ports 
                if p.direction == PortDirection.REQUIRED and 
                   p.interface_uid == provider_port.interface_uid
            ]
            if matching_ports:
                self.requester_swc_combo.addItem(swc.name, swc)

    def _on_requester_swc_changed(self, index):
        """Update requester port combo when SWC changes."""
        self.requester_port_combo.clear()
        self.requester_port_combo.addItem("(Select port)", None)
        
        swc = self.requester_swc_combo.currentData()
        provider_port = self.provider_port_combo.currentData()
        
        if swc and provider_port:
            for port in swc.ports:
                if (port.direction == PortDirection.REQUIRED and 
                    port.interface_uid == provider_port.interface_uid):
                    self.requester_port_combo.addItem(port.name, port)
        
        self._validate()

    def _update_interface_label(self):
        """Update the interface info label."""
        provider_port = self.provider_port_combo.currentData()
        if provider_port and provider_port.interface_uid:
            iface = self.project.get_interface_by_uid(provider_port.interface_uid)
            if iface:
                self.interface_label.setText(f"Interface: {iface.name} ({iface.interface_type.value})")
                self.interface_label.setStyleSheet("color: #4ec9b0;")
                return
        
        self.interface_label.setText("Select ports with matching interface")
        self.interface_label.setStyleSheet("color: #808080; font-style: italic;")

    def _validate(self):
        """Validate selections and enable/disable create button."""
        provider_swc = self.provider_swc_combo.currentData()
        provider_port = self.provider_port_combo.currentData()
        requester_swc = self.requester_swc_combo.currentData()
        requester_port = self.requester_port_combo.currentData()
        
        valid = all([provider_swc, provider_port, requester_swc, requester_port])
        
        if valid:
            # Check for existing connection
            is_valid, msg = self.project.validate_connection(
                provider_swc.uid, provider_port.uid,
                requester_swc.uid, requester_port.uid
            )
            valid = is_valid
            if not is_valid:
                self.interface_label.setText(f"⚠️ {msg}")
                self.interface_label.setStyleSheet("color: #f14c4c;")
        
        self.create_btn.setEnabled(valid)

    def _apply_preset(self):
        """Apply preset provider SWC and port."""
        # Find and select provider SWC
        for i in range(self.provider_swc_combo.count()):
            if self.provider_swc_combo.itemData(i) == self._preset_provider_swc:
                self.provider_swc_combo.setCurrentIndex(i)
                break
        
        # Find and select provider port
        for i in range(self.provider_port_combo.count()):
            if self.provider_port_combo.itemData(i) == self._preset_provider_port:
                self.provider_port_combo.setCurrentIndex(i)
                break

    def _create_connection(self):
        """Create the connection and close dialog."""
        provider_swc = self.provider_swc_combo.currentData()
        provider_port = self.provider_port_combo.currentData()
        requester_swc = self.requester_swc_combo.currentData()
        requester_port = self.requester_port_combo.currentData()
        
        name = self.name_edit.text().strip()
        if not name:
            name = f"Conn_{provider_port.name}_{requester_port.name}"
        
        self._connection = PortConnection(
            name=name,
            provider_swc_uid=provider_swc.uid,
            provider_port_uid=provider_port.uid,
            requester_swc_uid=requester_swc.uid,
            requester_port_uid=requester_port.uid,
        )
        
        self.accept()

    def get_connection(self) -> PortConnection:
        """Return the created connection."""
        return self._connection
