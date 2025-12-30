"""
AUTOSAR-like element model using dataclasses.
Supports serialization to/from YAML.

Enhanced with:
- Application Data Types (abstract)
- Implementation Data Types (platform-specific)
- Data Type Mapping Sets
- CompuMethods (scaling)
- Port Connections (Assembly Connectors)
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import uuid


# =============================================================================
# ENUMERATIONS
# =============================================================================

class PortDirection(Enum):
    PROVIDED = "provided"  # Server / Sender
    REQUIRED = "required"  # Client / Receiver


class InterfaceType(Enum):
    SENDER_RECEIVER = "sender_receiver"
    CLIENT_SERVER = "client_server"


class BaseDataType(Enum):
    """Primitive/base types for implementation."""
    UINT8 = "uint8"
    UINT16 = "uint16"
    UINT32 = "uint32"
    UINT64 = "uint64"
    INT8 = "int8"
    INT16 = "int16"
    INT32 = "int32"
    INT64 = "int64"
    FLOAT32 = "float32"
    FLOAT64 = "float64"
    BOOLEAN = "boolean"


class AppDataCategory(Enum):
    """Application data type categories."""
    VALUE = "value"           # Simple value type
    ARRAY = "array"           # Array type
    STRUCTURE = "structure"   # Struct/record type
    ENUM = "enum"             # Enumeration


class ArgumentDirection(Enum):
    IN = "in"
    OUT = "out"
    INOUT = "inout"


# =============================================================================
# COMPU METHODS (Scaling/Conversion)
# =============================================================================

@dataclass
class CompuMethod:
    """
    Computation method for scaling between physical and internal values.
    physical = (internal * factor) + offset
    """
    name: str
    factor: float = 1.0
    offset: float = 0.0
    unit: str = ""
    description: str = ""
    uid: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "factor": self.factor,
            "offset": self.offset,
            "unit": self.unit,
            "description": self.description,
            "uid": self.uid,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CompuMethod":
        return cls(
            name=data["name"],
            factor=data.get("factor", 1.0),
            offset=data.get("offset", 0.0),
            unit=data.get("unit", ""),
            description=data.get("description", ""),
            uid=data.get("uid", str(uuid.uuid4())[:8]),
        )


# =============================================================================
# DATA TYPES
# =============================================================================

@dataclass
class ApplicationDataType:
    """
    Abstract application-level data type.
    Represents the logical/physical meaning without platform details.
    """
    name: str
    category: AppDataCategory = AppDataCategory.VALUE
    compu_method_uid: Optional[str] = None  # Reference to CompuMethod
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    init_value: str = "0"
    description: str = ""
    # For ARRAY category
    array_size: int = 1
    element_type_uid: Optional[str] = None  # Reference to another AppDataType
    # For STRUCTURE category
    struct_members: list[tuple[str, str]] = field(default_factory=list)  # (name, type_uid)
    # For ENUM category
    enum_literals: list[tuple[str, int]] = field(default_factory=list)  # (name, value)
    uid: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "category": self.category.value,
            "compu_method_uid": self.compu_method_uid,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "init_value": self.init_value,
            "description": self.description,
            "array_size": self.array_size,
            "element_type_uid": self.element_type_uid,
            "struct_members": [{"name": m[0], "type_uid": m[1]} for m in self.struct_members],
            "enum_literals": [{"name": e[0], "value": e[1]} for e in self.enum_literals],
            "uid": self.uid,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ApplicationDataType":
        struct_members = [(m["name"], m["type_uid"]) for m in data.get("struct_members", [])]
        enum_literals = [(e["name"], e["value"]) for e in data.get("enum_literals", [])]
        return cls(
            name=data["name"],
            category=AppDataCategory(data.get("category", "value")),
            compu_method_uid=data.get("compu_method_uid"),
            min_value=data.get("min_value"),
            max_value=data.get("max_value"),
            init_value=data.get("init_value", "0"),
            description=data.get("description", ""),
            array_size=data.get("array_size", 1),
            element_type_uid=data.get("element_type_uid"),
            struct_members=struct_members,
            enum_literals=enum_literals,
            uid=data.get("uid", str(uuid.uuid4())[:8]),
        )


@dataclass
class ImplementationDataType:
    """
    Platform-specific implementation data type.
    Maps to actual C types.
    """
    name: str
    base_type: BaseDataType = BaseDataType.UINT8
    # For arrays
    is_array: bool = False
    array_size: int = 1
    # For structures
    is_struct: bool = False
    struct_members: list[tuple[str, str]] = field(default_factory=list)  # (name, impl_type_uid or base_type)
    description: str = ""
    uid: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "base_type": self.base_type.value,
            "is_array": self.is_array,
            "array_size": self.array_size,
            "is_struct": self.is_struct,
            "struct_members": [{"name": m[0], "type": m[1]} for m in self.struct_members],
            "description": self.description,
            "uid": self.uid,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ImplementationDataType":
        struct_members = [(m["name"], m["type"]) for m in data.get("struct_members", [])]
        return cls(
            name=data["name"],
            base_type=BaseDataType(data.get("base_type", "uint8")),
            is_array=data.get("is_array", False),
            array_size=data.get("array_size", 1),
            is_struct=data.get("is_struct", False),
            struct_members=struct_members,
            description=data.get("description", ""),
            uid=data.get("uid", str(uuid.uuid4())[:8]),
        )


@dataclass
class DataTypeMapping:
    """Maps an Application Data Type to an Implementation Data Type."""
    app_type_uid: str
    impl_type_uid: str
    uid: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_dict(self) -> dict:
        return {
            "app_type_uid": self.app_type_uid,
            "impl_type_uid": self.impl_type_uid,
            "uid": self.uid,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DataTypeMapping":
        return cls(
            app_type_uid=data["app_type_uid"],
            impl_type_uid=data["impl_type_uid"],
            uid=data.get("uid", str(uuid.uuid4())[:8]),
        )


# =============================================================================
# INTERFACE ELEMENTS
# =============================================================================

@dataclass
class DataElement:
    """Data element within a Sender/Receiver interface."""
    name: str
    app_type_uid: Optional[str] = None  # Reference to ApplicationDataType
    # Fallback to base type if no app type defined
    base_type: BaseDataType = BaseDataType.UINT8
    init_value: str = "0"
    description: str = ""
    uid: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "app_type_uid": self.app_type_uid,
            "base_type": self.base_type.value,
            "init_value": self.init_value,
            "description": self.description,
            "uid": self.uid,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DataElement":
        return cls(
            name=data["name"],
            app_type_uid=data.get("app_type_uid"),
            base_type=BaseDataType(data.get("base_type", "uint8")),
            init_value=data.get("init_value", "0"),
            description=data.get("description", ""),
            uid=data.get("uid", str(uuid.uuid4())[:8]),
        )


@dataclass
class OperationArgument:
    """Argument for a Client/Server operation."""
    name: str
    direction: ArgumentDirection = ArgumentDirection.IN
    app_type_uid: Optional[str] = None
    base_type: BaseDataType = BaseDataType.UINT8
    description: str = ""
    uid: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "direction": self.direction.value,
            "app_type_uid": self.app_type_uid,
            "base_type": self.base_type.value,
            "description": self.description,
            "uid": self.uid,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "OperationArgument":
        return cls(
            name=data["name"],
            direction=ArgumentDirection(data.get("direction", "in")),
            app_type_uid=data.get("app_type_uid"),
            base_type=BaseDataType(data.get("base_type", "uint8")),
            description=data.get("description", ""),
            uid=data.get("uid", str(uuid.uuid4())[:8]),
        )


@dataclass
class Operation:
    """Operation within a Client/Server interface."""
    name: str
    return_type_uid: Optional[str] = None  # Reference to ApplicationDataType
    return_base_type: BaseDataType = BaseDataType.UINT8
    arguments: list[OperationArgument] = field(default_factory=list)
    description: str = ""
    uid: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "return_type_uid": self.return_type_uid,
            "return_base_type": self.return_base_type.value,
            "arguments": [arg.to_dict() for arg in self.arguments],
            "description": self.description,
            "uid": self.uid,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Operation":
        args = [OperationArgument.from_dict(a) for a in data.get("arguments", [])]
        return cls(
            name=data["name"],
            return_type_uid=data.get("return_type_uid"),
            return_base_type=BaseDataType(data.get("return_base_type", "uint8")),
            arguments=args,
            description=data.get("description", ""),
            uid=data.get("uid", str(uuid.uuid4())[:8]),
        )


# =============================================================================
# INTERFACES
# =============================================================================

@dataclass
class Interface:
    """AUTOSAR-like interface (Sender/Receiver or Client/Server)."""
    name: str
    interface_type: InterfaceType = InterfaceType.SENDER_RECEIVER
    data_elements: list[DataElement] = field(default_factory=list)
    operations: list[Operation] = field(default_factory=list)
    description: str = ""
    uid: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "interface_type": self.interface_type.value,
            "data_elements": [de.to_dict() for de in self.data_elements],
            "operations": [op.to_dict() for op in self.operations],
            "description": self.description,
            "uid": self.uid,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Interface":
        return cls(
            name=data["name"],
            interface_type=InterfaceType(data.get("interface_type", "sender_receiver")),
            data_elements=[DataElement.from_dict(de) for de in data.get("data_elements", [])],
            operations=[Operation.from_dict(op) for op in data.get("operations", [])],
            description=data.get("description", ""),
            uid=data.get("uid", str(uuid.uuid4())[:8]),
        )


# =============================================================================
# SOFTWARE COMPONENT ELEMENTS
# =============================================================================

@dataclass
class Port:
    """Port on a Software Component."""
    name: str
    direction: PortDirection = PortDirection.REQUIRED
    interface_uid: Optional[str] = None  # Reference to Interface by UID
    description: str = ""
    uid: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "direction": self.direction.value,
            "interface_uid": self.interface_uid,
            "description": self.description,
            "uid": self.uid,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Port":
        return cls(
            name=data["name"],
            direction=PortDirection(data.get("direction", "required")),
            interface_uid=data.get("interface_uid"),
            description=data.get("description", ""),
            uid=data.get("uid", str(uuid.uuid4())[:8]),
        )


@dataclass
class Runnable:
    """Runnable entity within an SWC."""
    name: str
    period_ms: int = 10  # 0 = event-triggered
    description: str = ""
    uid: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "period_ms": self.period_ms,
            "description": self.description,
            "uid": self.uid,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Runnable":
        return cls(
            name=data["name"],
            period_ms=data.get("period_ms", 10),
            description=data.get("description", ""),
            uid=data.get("uid", str(uuid.uuid4())[:8]),
        )


@dataclass
class SoftwareComponent:
    """AUTOSAR-like Software Component."""
    name: str
    ports: list[Port] = field(default_factory=list)
    runnables: list[Runnable] = field(default_factory=list)
    description: str = ""
    uid: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "ports": [p.to_dict() for p in self.ports],
            "runnables": [r.to_dict() for r in self.runnables],
            "description": self.description,
            "uid": self.uid,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SoftwareComponent":
        return cls(
            name=data["name"],
            ports=[Port.from_dict(p) for p in data.get("ports", [])],
            runnables=[Runnable.from_dict(r) for r in data.get("runnables", [])],
            description=data.get("description", ""),
            uid=data.get("uid", str(uuid.uuid4())[:8]),
        )

    def get_port_by_uid(self, uid: str) -> Optional[Port]:
        for port in self.ports:
            if port.uid == uid:
                return port
        return None


# =============================================================================
# PORT CONNECTIONS (Assembly Connectors)
# =============================================================================

@dataclass
class PortConnection:
    """
    Assembly connector between two ports.
    Connects a REQUIRED port to a PROVIDED port with matching interface.
    """
    name: str
    # Provider side (Sender / Server)
    provider_swc_uid: str
    provider_port_uid: str
    # Requester side (Receiver / Client)
    requester_swc_uid: str
    requester_port_uid: str
    description: str = ""
    uid: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "provider_swc_uid": self.provider_swc_uid,
            "provider_port_uid": self.provider_port_uid,
            "requester_swc_uid": self.requester_swc_uid,
            "requester_port_uid": self.requester_port_uid,
            "description": self.description,
            "uid": self.uid,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PortConnection":
        return cls(
            name=data["name"],
            provider_swc_uid=data["provider_swc_uid"],
            provider_port_uid=data["provider_port_uid"],
            requester_swc_uid=data["requester_swc_uid"],
            requester_port_uid=data["requester_port_uid"],
            description=data.get("description", ""),
            uid=data.get("uid", str(uuid.uuid4())[:8]),
        )


# =============================================================================
# PROJECT
# =============================================================================

@dataclass
class Project:
    """Container for all project elements."""
    name: str = "Untitled Project"
    description: str = ""
    # Data Types
    compu_methods: list[CompuMethod] = field(default_factory=list)
    application_data_types: list[ApplicationDataType] = field(default_factory=list)
    implementation_data_types: list[ImplementationDataType] = field(default_factory=list)
    data_type_mappings: list[DataTypeMapping] = field(default_factory=list)
    # Interfaces & Components
    interfaces: list[Interface] = field(default_factory=list)
    components: list[SoftwareComponent] = field(default_factory=list)
    # Connections
    connections: list[PortConnection] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "compu_methods": [cm.to_dict() for cm in self.compu_methods],
            "application_data_types": [adt.to_dict() for adt in self.application_data_types],
            "implementation_data_types": [idt.to_dict() for idt in self.implementation_data_types],
            "data_type_mappings": [dtm.to_dict() for dtm in self.data_type_mappings],
            "interfaces": [i.to_dict() for i in self.interfaces],
            "components": [c.to_dict() for c in self.components],
            "connections": [conn.to_dict() for conn in self.connections],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Project":
        return cls(
            name=data.get("name", "Untitled Project"),
            description=data.get("description", ""),
            compu_methods=[CompuMethod.from_dict(cm) for cm in data.get("compu_methods", [])],
            application_data_types=[ApplicationDataType.from_dict(adt) for adt in data.get("application_data_types", [])],
            implementation_data_types=[ImplementationDataType.from_dict(idt) for idt in data.get("implementation_data_types", [])],
            data_type_mappings=[DataTypeMapping.from_dict(dtm) for dtm in data.get("data_type_mappings", [])],
            interfaces=[Interface.from_dict(i) for i in data.get("interfaces", [])],
            components=[SoftwareComponent.from_dict(c) for c in data.get("components", [])],
            connections=[PortConnection.from_dict(conn) for conn in data.get("connections", [])],
        )

    # --- Lookup helpers ---

    def get_interface_by_uid(self, uid: str) -> Optional[Interface]:
        for iface in self.interfaces:
            if iface.uid == uid:
                return iface
        return None

    def get_component_by_uid(self, uid: str) -> Optional[SoftwareComponent]:
        for comp in self.components:
            if comp.uid == uid:
                return comp
        return None

    def get_app_type_by_uid(self, uid: str) -> Optional[ApplicationDataType]:
        for adt in self.application_data_types:
            if adt.uid == uid:
                return adt
        return None

    def get_impl_type_by_uid(self, uid: str) -> Optional[ImplementationDataType]:
        for idt in self.implementation_data_types:
            if idt.uid == uid:
                return idt
        return None

    def get_compu_method_by_uid(self, uid: str) -> Optional[CompuMethod]:
        for cm in self.compu_methods:
            if cm.uid == uid:
                return cm
        return None

    def get_impl_type_for_app_type(self, app_type_uid: str) -> Optional[ImplementationDataType]:
        """Get the implementation type mapped to an application type."""
        for mapping in self.data_type_mappings:
            if mapping.app_type_uid == app_type_uid:
                return self.get_impl_type_by_uid(mapping.impl_type_uid)
        return None

    def get_connection_by_uid(self, uid: str) -> Optional[PortConnection]:
        for conn in self.connections:
            if conn.uid == uid:
                return conn
        return None

    # --- Connection helpers ---

    def get_compatible_ports_for_connection(self, provider_port: Port) -> list[tuple["SoftwareComponent", Port]]:
        """Find all required ports that can connect to a provided port."""
        if provider_port.direction != PortDirection.PROVIDED:
            return []
        
        compatible = []
        for swc in self.components:
            for port in swc.ports:
                if (port.direction == PortDirection.REQUIRED and 
                    port.interface_uid == provider_port.interface_uid and
                    port.uid != provider_port.uid):
                    compatible.append((swc, port))
        return compatible

    def get_connections_for_port(self, port_uid: str) -> list[PortConnection]:
        """Get all connections involving a specific port."""
        return [
            conn for conn in self.connections
            if conn.provider_port_uid == port_uid or conn.requester_port_uid == port_uid
        ]

    def validate_connection(self, provider_swc_uid: str, provider_port_uid: str,
                           requester_swc_uid: str, requester_port_uid: str) -> tuple[bool, str]:
        """Validate that a connection is valid."""
        provider_swc = self.get_component_by_uid(provider_swc_uid)
        requester_swc = self.get_component_by_uid(requester_swc_uid)
        
        if not provider_swc:
            return False, "Provider SWC not found"
        if not requester_swc:
            return False, "Requester SWC not found"
        
        provider_port = provider_swc.get_port_by_uid(provider_port_uid)
        requester_port = requester_swc.get_port_by_uid(requester_port_uid)
        
        if not provider_port:
            return False, "Provider port not found"
        if not requester_port:
            return False, "Requester port not found"
        
        if provider_port.direction != PortDirection.PROVIDED:
            return False, "Provider port must have 'provided' direction"
        if requester_port.direction != PortDirection.REQUIRED:
            return False, "Requester port must have 'required' direction"
        
        if provider_port.interface_uid != requester_port.interface_uid:
            return False, "Ports must share the same interface"
        
        # Check for duplicate connection
        for conn in self.connections:
            if (conn.provider_port_uid == provider_port_uid and 
                conn.requester_port_uid == requester_port_uid):
                return False, "Connection already exists"
        
        return True, "Valid"


# =============================================================================
# BACKWARDS COMPATIBILITY - Keep old DataType enum as alias
# =============================================================================
DataType = BaseDataType
