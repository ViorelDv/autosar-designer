"""
AUTOSAR-like element model using dataclasses.
Supports serialization to/from YAML.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import uuid


class PortDirection(Enum):
    PROVIDED = "provided"  # Server / Sender
    REQUIRED = "required"  # Client / Receiver


class InterfaceType(Enum):
    SENDER_RECEIVER = "sender_receiver"
    CLIENT_SERVER = "client_server"


class DataType(Enum):
    UINT8 = "uint8"
    UINT16 = "uint16"
    UINT32 = "uint32"
    INT8 = "int8"
    INT16 = "int16"
    INT32 = "int32"
    FLOAT32 = "float32"
    FLOAT64 = "float64"
    BOOLEAN = "boolean"


@dataclass
class DataElement:
    """Data element within a Sender/Receiver interface."""
    name: str
    data_type: DataType = DataType.UINT8
    init_value: str = "0"
    description: str = ""
    uid: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "data_type": self.data_type.value,
            "init_value": self.init_value,
            "description": self.description,
            "uid": self.uid,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DataElement":
        return cls(
            name=data["name"],
            data_type=DataType(data.get("data_type", "uint8")),
            init_value=data.get("init_value", "0"),
            description=data.get("description", ""),
            uid=data.get("uid", str(uuid.uuid4())[:8]),
        )


@dataclass
class Operation:
    """Operation within a Client/Server interface."""
    name: str
    return_type: DataType = DataType.UINT8
    arguments: list[tuple[str, DataType, str]] = field(default_factory=list)  # (name, type, direction: in/out/inout)
    description: str = ""
    uid: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "return_type": self.return_type.value,
            "arguments": [
                {"name": arg[0], "type": arg[1].value, "direction": arg[2]}
                for arg in self.arguments
            ],
            "description": self.description,
            "uid": self.uid,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Operation":
        args = [
            (arg["name"], DataType(arg["type"]), arg["direction"])
            for arg in data.get("arguments", [])
        ]
        return cls(
            name=data["name"],
            return_type=DataType(data.get("return_type", "uint8")),
            arguments=args,
            description=data.get("description", ""),
            uid=data.get("uid", str(uuid.uuid4())[:8]),
        )


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


@dataclass
class Project:
    """Container for all project elements."""
    name: str = "Untitled Project"
    interfaces: list[Interface] = field(default_factory=list)
    components: list[SoftwareComponent] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "interfaces": [i.to_dict() for i in self.interfaces],
            "components": [c.to_dict() for c in self.components],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Project":
        return cls(
            name=data.get("name", "Untitled Project"),
            description=data.get("description", ""),
            interfaces=[Interface.from_dict(i) for i in data.get("interfaces", [])],
            components=[SoftwareComponent.from_dict(c) for c in data.get("components", [])],
        )

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
