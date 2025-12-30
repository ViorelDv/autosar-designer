"""
Graphical Composition View for AUTOSAR Designer.

Displays:
- Software Components as boxes
- Ports as connection points on the sides
- Connections as lines/curves between ports
- Module grouping (optional)
"""
from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem,
    QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsTextItem,
    QGraphicsLineItem, QGraphicsPathItem, QGraphicsItemGroup,
    QWidget, QVBoxLayout, QHBoxLayout, QToolBar, QPushButton,
    QComboBox, QLabel, QGraphicsDropShadowEffect, QMenu
)
from PyQt6.QtCore import Qt, QRectF, QPointF, QLineF
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPainterPath,
    QLinearGradient, QRadialGradient, QAction, QWheelEvent
)
from typing import Optional
from model import (
    Project, SoftwareComponent, Port, PortDirection, 
    Interface, PortConnection, InterfaceType
)


# =============================================================================
# COLORS
# =============================================================================
class Colors:
    """Color scheme for the composition view."""
    BACKGROUND = QColor("#1e1e1e")
    GRID = QColor("#2d2d2d")
    
    SWC_FILL = QColor("#2d2d30")
    SWC_BORDER = QColor("#3e3e42")
    SWC_HEADER = QColor("#007acc")
    SWC_TEXT = QColor("#d4d4d4")
    SWC_SELECTED = QColor("#094771")
    
    PORT_PROVIDED = QColor("#4ec9b0")  # Teal - sender/server
    PORT_REQUIRED = QColor("#dcdcaa")  # Yellow - receiver/client
    PORT_BORDER = QColor("#1e1e1e")
    PORT_HOVER = QColor("#ffffff")
    
    CONNECTION_SR = QColor("#4ec9b0")  # Sender/Receiver
    CONNECTION_CS = QColor("#c586c0")  # Client/Server
    CONNECTION_HOVER = QColor("#ffffff")
    
    MODULE_BORDER = QColor("#454545")
    MODULE_FILL = QColor(37, 37, 38, 80)  # Semi-transparent
    MODULE_TEXT = QColor("#808080")


# =============================================================================
# PORT GRAPHICS ITEM
# =============================================================================
class PortGraphicsItem(QGraphicsEllipseItem):
    """Visual representation of a port."""
    
    PORT_SIZE = 12
    
    def __init__(self, port: Port, direction: PortDirection, 
                 interface: Optional[Interface], parent_swc: "SwcGraphicsItem"):
        super().__init__(-self.PORT_SIZE/2, -self.PORT_SIZE/2, 
                        self.PORT_SIZE, self.PORT_SIZE)
        self.port = port
        self.direction = direction
        self.interface = interface
        self.parent_swc = parent_swc
        
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setZValue(10)
        
        # Set color based on direction
        color = Colors.PORT_PROVIDED if direction == PortDirection.PROVIDED else Colors.PORT_REQUIRED
        self.default_brush = QBrush(color)
        self.setBrush(self.default_brush)
        self.setPen(QPen(Colors.PORT_BORDER, 2))
        
        # Tooltip
        iface_name = interface.name if interface else "No interface"
        iface_type = interface.interface_type.value if interface else ""
        self.setToolTip(f"{port.name}\n{iface_name} ({iface_type})\n{direction.value}")

    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(Colors.PORT_HOVER))
        self.setScale(1.3)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setBrush(self.default_brush)
        self.setScale(1.0)
        super().hoverLeaveEvent(event)

    def get_connection_point(self) -> QPointF:
        """Get the center point in scene coordinates for connections."""
        return self.scenePos()


# =============================================================================
# SWC GRAPHICS ITEM
# =============================================================================
class SwcGraphicsItem(QGraphicsRectItem):
    """Visual representation of a Software Component."""
    
    MIN_WIDTH = 180
    MIN_HEIGHT = 100
    HEADER_HEIGHT = 30
    PORT_MARGIN = 20
    PORT_SPACING = 25
    
    def __init__(self, swc: SoftwareComponent, project: Project, 
                 module_name: str = None):
        super().__init__()
        self.swc = swc
        self.project = project
        self.module_name = module_name
        self.port_items: dict[str, PortGraphicsItem] = {}  # port_uid -> PortGraphicsItem
        
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        self.setZValue(5)
        
        self._setup_graphics()

    def _setup_graphics(self):
        """Setup the visual elements."""
        # Calculate size based on ports
        provided_ports = [p for p in self.swc.ports if p.direction == PortDirection.PROVIDED]
        required_ports = [p for p in self.swc.ports if p.direction == PortDirection.REQUIRED]
        
        max_ports = max(len(provided_ports), len(required_ports), 1)
        height = max(self.MIN_HEIGHT, 
                    self.HEADER_HEIGHT + self.PORT_MARGIN * 2 + max_ports * self.PORT_SPACING)
        width = self.MIN_WIDTH
        
        self.setRect(0, 0, width, height)
        
        # Background with gradient
        gradient = QLinearGradient(0, 0, 0, height)
        gradient.setColorAt(0, Colors.SWC_FILL)
        gradient.setColorAt(1, Colors.SWC_FILL.darker(110))
        self.setBrush(QBrush(gradient))
        self.setPen(QPen(Colors.SWC_BORDER, 2))
        
        # Header bar
        header = QGraphicsRectItem(0, 0, width, self.HEADER_HEIGHT, self)
        header.setBrush(QBrush(Colors.SWC_HEADER))
        header.setPen(QPen(Qt.PenStyle.NoPen))
        
        # Component name
        name_text = QGraphicsTextItem(self.swc.name, self)
        name_text.setDefaultTextColor(Colors.SWC_TEXT)
        name_text.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        name_text.setPos(10, 5)
        
        # Module label (if available)
        if self.module_name:
            module_text = QGraphicsTextItem(f"[{self.module_name}]", self)
            module_text.setDefaultTextColor(Colors.MODULE_TEXT)
            module_text.setFont(QFont("Segoe UI", 8))
            module_text.setPos(10, height - 20)
        
        # Runnables count
        run_count = len(self.swc.runnables)
        if run_count > 0:
            run_text = QGraphicsTextItem(f"▷ {run_count} runnable(s)", self)
            run_text.setDefaultTextColor(QColor("#808080"))
            run_text.setFont(QFont("Segoe UI", 8))
            run_text.setPos(10, self.HEADER_HEIGHT + 5)
        
        # Add ports
        self._add_ports(provided_ports, required_ports, height)

    def _add_ports(self, provided_ports: list, required_ports: list, height: float):
        """Add port graphics items."""
        # Provided ports on the right
        for i, port in enumerate(provided_ports):
            interface = self.project.get_interface_by_uid(port.interface_uid)
            port_item = PortGraphicsItem(port, port.direction, interface, self)
            y = self.HEADER_HEIGHT + self.PORT_MARGIN + i * self.PORT_SPACING
            port_item.setPos(self.rect().width(), y)
            port_item.setParentItem(self)
            self.port_items[port.uid] = port_item
            
            # Port label
            label = QGraphicsTextItem(port.name, self)
            label.setDefaultTextColor(Colors.PORT_PROVIDED)
            label.setFont(QFont("Segoe UI", 8))
            label.setPos(self.rect().width() - label.boundingRect().width() - 15, y - 8)
        
        # Required ports on the left
        for i, port in enumerate(required_ports):
            interface = self.project.get_interface_by_uid(port.interface_uid)
            port_item = PortGraphicsItem(port, port.direction, interface, self)
            y = self.HEADER_HEIGHT + self.PORT_MARGIN + i * self.PORT_SPACING
            port_item.setPos(0, y)
            port_item.setParentItem(self)
            self.port_items[port.uid] = port_item
            
            # Port label
            label = QGraphicsTextItem(port.name, self)
            label.setDefaultTextColor(Colors.PORT_REQUIRED)
            label.setFont(QFont("Segoe UI", 8))
            label.setPos(15, y - 8)

    def itemChange(self, change, value):
        """Handle item changes (e.g., position changes for updating connections)."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Notify scene to update connections
            scene = self.scene()
            if scene and hasattr(scene, 'update_connections'):
                scene.update_connections()
        return super().itemChange(change, value)

    def paint(self, painter, option, widget):
        """Custom paint for selection highlight."""
        if self.isSelected():
            self.setPen(QPen(Colors.SWC_SELECTED, 3))
        else:
            self.setPen(QPen(Colors.SWC_BORDER, 2))
        super().paint(painter, option, widget)


# =============================================================================
# CONNECTION GRAPHICS ITEM
# =============================================================================
class ConnectionGraphicsItem(QGraphicsPathItem):
    """Visual representation of a port connection."""
    
    def __init__(self, connection: PortConnection, 
                 provider_port_item: PortGraphicsItem,
                 requester_port_item: PortGraphicsItem,
                 interface: Optional[Interface]):
        super().__init__()
        self.connection = connection
        self.provider_port_item = provider_port_item
        self.requester_port_item = requester_port_item
        self.interface = interface
        
        self.setAcceptHoverEvents(True)
        self.setZValue(1)
        
        # Color based on interface type
        if interface:
            if interface.interface_type == InterfaceType.SENDER_RECEIVER:
                self.line_color = Colors.CONNECTION_SR
            else:
                self.line_color = Colors.CONNECTION_CS
        else:
            self.line_color = QColor("#808080")
        
        self.default_pen = QPen(self.line_color, 2)
        self.default_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.setPen(self.default_pen)
        
        # Tooltip
        iface_name = interface.name if interface else "Unknown"
        self.setToolTip(f"{connection.name}\nInterface: {iface_name}")
        
        self.update_path()

    def update_path(self):
        """Update the connection path based on port positions."""
        start = self.provider_port_item.get_connection_point()
        end = self.requester_port_item.get_connection_point()
        
        # Create a bezier curve
        path = QPainterPath()
        path.moveTo(start)
        
        # Control points for smooth curve
        dx = abs(end.x() - start.x())
        ctrl_offset = max(50, dx * 0.4)
        
        ctrl1 = QPointF(start.x() + ctrl_offset, start.y())
        ctrl2 = QPointF(end.x() - ctrl_offset, end.y())
        
        path.cubicTo(ctrl1, ctrl2, end)
        self.setPath(path)

    def hoverEnterEvent(self, event):
        pen = QPen(Colors.CONNECTION_HOVER, 3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.setPen(pen)
        self.setZValue(2)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setPen(self.default_pen)
        self.setZValue(1)
        super().hoverLeaveEvent(event)


# =============================================================================
# COMPOSITION SCENE
# =============================================================================
class CompositionScene(QGraphicsScene):
    """Scene containing all composition elements."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackgroundBrush(QBrush(Colors.BACKGROUND))
        
        self.swc_items: dict[str, SwcGraphicsItem] = {}  # swc_uid -> SwcGraphicsItem
        self.connection_items: list[ConnectionGraphicsItem] = []
        self.project: Optional[Project] = None

    def load_project(self, project: Project, module_info: dict = None):
        """Load a project into the scene."""
        self.clear()
        self.swc_items.clear()
        self.connection_items.clear()
        self.project = project
        
        if not project:
            return
        
        # Create SWC items
        x, y = 50, 50
        row_height = 0
        col = 0
        
        for swc in project.components:
            module_name = module_info.get(swc.uid) if module_info else None
            swc_item = SwcGraphicsItem(swc, project, module_name)
            swc_item.setPos(x, y)
            self.addItem(swc_item)
            self.swc_items[swc.uid] = swc_item
            
            # Simple grid layout
            row_height = max(row_height, swc_item.rect().height())
            x += swc_item.rect().width() + 100
            col += 1
            
            if col >= 3:  # 3 columns
                col = 0
                x = 50
                y += row_height + 80
                row_height = 0
        
        # Create connection items
        for conn in project.connections:
            self._create_connection(conn)
        
        # Fit scene to items
        self.setSceneRect(self.itemsBoundingRect().adjusted(-50, -50, 50, 50))

    def _create_connection(self, conn: PortConnection):
        """Create a connection graphics item."""
        # Find provider and requester port items
        provider_swc_item = self.swc_items.get(conn.provider_swc_uid)
        requester_swc_item = self.swc_items.get(conn.requester_swc_uid)
        
        if not provider_swc_item or not requester_swc_item:
            return
        
        provider_port_item = provider_swc_item.port_items.get(conn.provider_port_uid)
        requester_port_item = requester_swc_item.port_items.get(conn.requester_port_uid)
        
        if not provider_port_item or not requester_port_item:
            return
        
        # Get interface for color
        interface = None
        if provider_port_item.interface:
            interface = provider_port_item.interface
        
        conn_item = ConnectionGraphicsItem(
            conn, provider_port_item, requester_port_item, interface
        )
        self.addItem(conn_item)
        self.connection_items.append(conn_item)

    def update_connections(self):
        """Update all connection paths (called when SWCs move)."""
        for conn_item in self.connection_items:
            conn_item.update_path()

    def auto_layout(self):
        """Automatically arrange components."""
        if not self.swc_items:
            return
        
        # Simple force-directed-like layout
        # For now, just arrange in a grid with connections considered
        items = list(self.swc_items.values())
        
        # Find components with no required ports (sources)
        sources = [item for item in items 
                   if not any(p.direction == PortDirection.REQUIRED for p in item.swc.ports)]
        
        # Find components with no provided ports (sinks)
        sinks = [item for item in items
                 if not any(p.direction == PortDirection.PROVIDED for p in item.swc.ports)]
        
        # Middle components
        middle = [item for item in items if item not in sources and item not in sinks]
        
        # Arrange: sources on left, middle in center, sinks on right
        x = 50
        y = 50
        
        for item in sources:
            item.setPos(x, y)
            y += item.rect().height() + 60
        
        x = 350
        y = 50
        for item in middle:
            item.setPos(x, y)
            y += item.rect().height() + 60
        
        x = 650
        y = 50
        for item in sinks:
            item.setPos(x, y)
            y += item.rect().height() + 60
        
        self.update_connections()
        self.setSceneRect(self.itemsBoundingRect().adjusted(-50, -50, 50, 50))


# =============================================================================
# COMPOSITION VIEW
# =============================================================================
class CompositionView(QGraphicsView):
    """Main view widget for the composition diagram."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.composition_scene = CompositionScene(self)
        self.setScene(self.composition_scene)
        
        # View settings
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        # Enable scroll with middle mouse button
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self._zoom = 1.0

    def load_project(self, project: Project, module_info: dict = None):
        """Load a project into the view."""
        self.composition_scene.load_project(project, module_info)
        self.fit_in_view()

    def fit_in_view(self):
        """Fit the entire diagram in the view."""
        self.fitInView(self.composition_scene.sceneRect(), 
                      Qt.AspectRatioMode.KeepAspectRatio)
        self._zoom = self.transform().m11()

    def auto_layout(self):
        """Trigger auto-layout."""
        self.composition_scene.auto_layout()

    def wheelEvent(self, event: QWheelEvent):
        """Handle zoom with mouse wheel."""
        factor = 1.15
        if event.angleDelta().y() > 0:
            # Zoom in
            if self._zoom < 3.0:
                self.scale(factor, factor)
                self._zoom *= factor
        else:
            # Zoom out
            if self._zoom > 0.2:
                self.scale(1/factor, 1/factor)
                self._zoom /= factor

    def contextMenuEvent(self, event):
        """Context menu for the view."""
        menu = QMenu(self)
        
        fit_action = menu.addAction("Fit in View")
        fit_action.triggered.connect(self.fit_in_view)
        
        layout_action = menu.addAction("Auto Layout")
        layout_action.triggered.connect(self.auto_layout)
        
        menu.addSeparator()
        
        zoom_in = menu.addAction("Zoom In")
        zoom_in.triggered.connect(lambda: self.scale(1.15, 1.15))
        
        zoom_out = menu.addAction("Zoom Out")
        zoom_out.triggered.connect(lambda: self.scale(1/1.15, 1/1.15))
        
        reset_zoom = menu.addAction("Reset Zoom")
        reset_zoom.triggered.connect(lambda: self.resetTransform())
        
        menu.exec(event.globalPos())


# =============================================================================
# COMPOSITION WIDGET (with toolbar)
# =============================================================================
class CompositionWidget(QWidget):
    """Complete composition view widget with toolbar."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toolbar
        toolbar = QToolBar()
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #2d2d30;
                border: none;
                padding: 5px;
                spacing: 5px;
            }
            QToolButton {
                background-color: transparent;
                color: #d4d4d4;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QToolButton:hover {
                background-color: #3e3e42;
            }
        """)
        
        fit_btn = QPushButton("Fit View")
        fit_btn.clicked.connect(self._fit_view)
        toolbar.addWidget(fit_btn)
        
        layout_btn = QPushButton("Auto Layout")
        layout_btn.clicked.connect(self._auto_layout)
        toolbar.addWidget(layout_btn)
        
        toolbar.addSeparator()
        
        zoom_in_btn = QPushButton("Zoom +")
        zoom_in_btn.clicked.connect(lambda: self.view.scale(1.2, 1.2))
        toolbar.addWidget(zoom_in_btn)
        
        zoom_out_btn = QPushButton("Zoom -")
        zoom_out_btn.clicked.connect(lambda: self.view.scale(1/1.2, 1/1.2))
        toolbar.addWidget(zoom_out_btn)
        
        toolbar.addSeparator()
        
        # Legend
        legend = QLabel(
            "  <span style='color:#4ec9b0'>● Provided (Sender/Server)</span>"
            "  <span style='color:#dcdcaa'>● Required (Receiver/Client)</span>"
            "  <span style='color:#4ec9b0'>― S/R Connection</span>"
            "  <span style='color:#c586c0'>― C/S Connection</span>"
        )
        legend.setStyleSheet("color: #808080; font-size: 11px;")
        toolbar.addWidget(legend)
        
        layout.addWidget(toolbar)
        
        # Composition view
        self.view = CompositionView()
        layout.addWidget(self.view)

    def load_project(self, project: Project, module_info: dict = None):
        """Load a project into the composition view."""
        self.view.load_project(project, module_info)

    def _fit_view(self):
        self.view.fit_in_view()

    def _auto_layout(self):
        self.view.auto_layout()
