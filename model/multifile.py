"""
Multi-file project management for AUTOSAR Designer.

Supports:
- Multiple YAML module files (like ARXML packages)
- A master project file that references modules
- Cross-module references (interfaces, types, connections)
- Merged view for editing
"""
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from .elements import (
    Project, Interface, SoftwareComponent, PortConnection,
    CompuMethod, ApplicationDataType, ImplementationDataType,
    DataTypeMapping
)


@dataclass
class ModuleReference:
    """Reference to a YAML module file."""
    path: str  # Relative path from master project file
    name: str  # Display name
    description: str = ""
    enabled: bool = True

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ModuleReference":
        return cls(
            path=data["path"],
            name=data.get("name", Path(data["path"]).stem),
            description=data.get("description", ""),
            enabled=data.get("enabled", True),
        )


@dataclass
class MasterProject:
    """
    Master project that references multiple module files.
    
    Structure:
    project/
    ├── master.yaml           # This file - references modules
    ├── modules/
    │   ├── datatypes.yaml    # Shared data types
    │   ├── interfaces.yaml   # Shared interfaces  
    │   ├── swc_sensor.yaml   # Sensor component
    │   ├── swc_monitor.yaml  # Monitor component
    │   └── connections.yaml  # Cross-module connections
    """
    name: str = "Multi-Module Project"
    description: str = ""
    modules: list[ModuleReference] = field(default_factory=list)
    # Connections can span modules, so they're stored in master
    # OR in a dedicated connections module
    global_connections: list[PortConnection] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "modules": [m.to_dict() for m in self.modules],
            "global_connections": [c.to_dict() for c in self.global_connections],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MasterProject":
        return cls(
            name=data.get("name", "Multi-Module Project"),
            description=data.get("description", ""),
            modules=[ModuleReference.from_dict(m) for m in data.get("modules", [])],
            global_connections=[PortConnection.from_dict(c) for c in data.get("global_connections", [])],
        )


@dataclass 
class Module:
    """
    A single YAML module containing a subset of project elements.
    
    Each module can contain any combination of:
    - Data types (CompuMethods, App types, Impl types, mappings)
    - Interfaces
    - Software Components
    - Connections (within this module)
    """
    name: str = "Untitled Module"
    description: str = ""
    # What this module provides
    compu_methods: list[CompuMethod] = field(default_factory=list)
    application_data_types: list[ApplicationDataType] = field(default_factory=list)
    implementation_data_types: list[ImplementationDataType] = field(default_factory=list)
    data_type_mappings: list[DataTypeMapping] = field(default_factory=list)
    interfaces: list[Interface] = field(default_factory=list)
    components: list[SoftwareComponent] = field(default_factory=list)
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
    def from_dict(cls, data: dict) -> "Module":
        return cls(
            name=data.get("name", "Untitled Module"),
            description=data.get("description", ""),
            compu_methods=[CompuMethod.from_dict(cm) for cm in data.get("compu_methods", [])],
            application_data_types=[ApplicationDataType.from_dict(adt) for adt in data.get("application_data_types", [])],
            implementation_data_types=[ImplementationDataType.from_dict(idt) for idt in data.get("implementation_data_types", [])],
            data_type_mappings=[DataTypeMapping.from_dict(dtm) for dtm in data.get("data_type_mappings", [])],
            interfaces=[Interface.from_dict(i) for i in data.get("interfaces", [])],
            components=[SoftwareComponent.from_dict(c) for c in data.get("components", [])],
            connections=[PortConnection.from_dict(conn) for conn in data.get("connections", [])],
        )


class MultiFileProject:
    """
    Manager for multi-file projects.
    
    Handles loading, merging, and saving of modular projects.
    """

    def __init__(self):
        self.master: MasterProject = MasterProject()
        self.master_path: Optional[Path] = None
        self.modules: dict[str, Module] = {}  # path -> Module
        self.module_paths: dict[str, Path] = {}  # module name -> absolute path
        self._merged: Optional[Project] = None

    def new_project(self, name: str = "New Project"):
        """Create a new empty multi-file project."""
        self.master = MasterProject(name=name)
        self.master_path = None
        self.modules = {}
        self.module_paths = {}
        self._merged = None

    def load_master(self, master_path: Path) -> None:
        """Load a master project file and all its modules."""
        with open(master_path, 'r') as f:
            data = yaml.safe_load(f)
        
        self.master = MasterProject.from_dict(data)
        self.master_path = master_path.resolve()
        self.modules = {}
        self.module_paths = {}

        # Load each referenced module
        base_dir = master_path.parent
        for mod_ref in self.master.modules:
            if mod_ref.enabled:
                mod_path = (base_dir / mod_ref.path).resolve()
                if mod_path.exists():
                    self.load_module(mod_path, mod_ref.name)
                else:
                    print(f"Warning: Module not found: {mod_path}")

        self._merged = None

    def load_module(self, module_path: Path, name: str = None) -> Module:
        """Load a single module file."""
        with open(module_path, 'r') as f:
            data = yaml.safe_load(f)
        
        module = Module.from_dict(data)
        if name:
            module.name = name
        
        key = str(module_path)
        self.modules[key] = module
        self.module_paths[module.name] = module_path
        self._merged = None
        
        return module

    def save_master(self, master_path: Path = None) -> None:
        """Save the master project file."""
        if master_path:
            self.master_path = master_path.resolve()
        
        if not self.master_path:
            raise ValueError("No master path specified")
        
        with open(self.master_path, 'w') as f:
            yaml.dump(
                self.master.to_dict(),
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
                indent=2,
            )

    def save_module(self, module_name: str) -> None:
        """Save a specific module file."""
        if module_name not in self.module_paths:
            raise ValueError(f"Unknown module: {module_name}")
        
        module_path = self.module_paths[module_name]
        module = self.modules[str(module_path)]
        
        with open(module_path, 'w') as f:
            yaml.dump(
                module.to_dict(),
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
                indent=2,
            )

    def save_all(self) -> None:
        """Save master and all modules."""
        self.save_master()
        for module_name in self.module_paths:
            self.save_module(module_name)

    def add_module(self, module: Module, relative_path: str) -> None:
        """Add a new module to the project."""
        if not self.master_path:
            raise ValueError("Save master project first")
        
        # Create module reference
        mod_ref = ModuleReference(
            path=relative_path,
            name=module.name,
            description=module.description,
        )
        self.master.modules.append(mod_ref)
        
        # Calculate absolute path and store
        abs_path = (self.master_path.parent / relative_path).resolve()
        self.modules[str(abs_path)] = module
        self.module_paths[module.name] = abs_path
        
        # Save the module file
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        with open(abs_path, 'w') as f:
            yaml.dump(
                module.to_dict(),
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
                indent=2,
            )
        
        self._merged = None

    def remove_module(self, module_name: str, delete_file: bool = False) -> None:
        """Remove a module from the project."""
        # Remove from master references
        self.master.modules = [m for m in self.master.modules if m.name != module_name]
        
        # Remove from loaded modules
        if module_name in self.module_paths:
            path = self.module_paths[module_name]
            del self.modules[str(path)]
            del self.module_paths[module_name]
            
            if delete_file and path.exists():
                path.unlink()
        
        self._merged = None

    def get_merged_project(self) -> Project:
        """
        Merge all modules into a single Project for editing/viewing.
        
        This creates a unified view where all elements from all modules
        are combined. UIDs remain unique across modules.
        """
        if self._merged is not None:
            return self._merged
        
        merged = Project(
            name=self.master.name,
            description=self.master.description,
        )
        
        # Merge all modules
        for module in self.modules.values():
            merged.compu_methods.extend(module.compu_methods)
            merged.application_data_types.extend(module.application_data_types)
            merged.implementation_data_types.extend(module.implementation_data_types)
            merged.data_type_mappings.extend(module.data_type_mappings)
            merged.interfaces.extend(module.interfaces)
            merged.components.extend(module.components)
            merged.connections.extend(module.connections)
        
        # Add global connections from master
        merged.connections.extend(self.master.global_connections)
        
        self._merged = merged
        return merged

    def find_element_module(self, uid: str) -> Optional[str]:
        """Find which module contains an element by UID."""
        for module_path, module in self.modules.items():
            # Check all element lists
            for cm in module.compu_methods:
                if cm.uid == uid:
                    return module.name
            for adt in module.application_data_types:
                if adt.uid == uid:
                    return module.name
            for idt in module.implementation_data_types:
                if idt.uid == uid:
                    return module.name
            for iface in module.interfaces:
                if iface.uid == uid:
                    return module.name
            for swc in module.components:
                if swc.uid == uid:
                    return module.name
                for port in swc.ports:
                    if port.uid == uid:
                        return module.name
        return None

    def get_module_by_name(self, name: str) -> Optional[Module]:
        """Get a module by its name."""
        if name in self.module_paths:
            return self.modules[str(self.module_paths[name])]
        return None

    def invalidate_cache(self):
        """Invalidate the merged project cache after changes."""
        self._merged = None


def create_example_multifile_project(base_dir: Path) -> MultiFileProject:
    """
    Create an example multi-file project structure.
    
    Creates:
    - master.yaml
    - modules/datatypes.yaml
    - modules/interfaces.yaml
    - modules/swc_sensor.yaml
    - modules/swc_monitor.yaml
    """
    from .elements import (
        CompuMethod, ApplicationDataType, ImplementationDataType,
        DataTypeMapping, Interface, InterfaceType, DataElement,
        SoftwareComponent, Port, PortDirection, Runnable,
        BaseDataType, AppDataCategory, PortConnection
    )

    project = MultiFileProject()
    
    # Create master
    project.master = MasterProject(
        name="Multi-Module Automotive Project",
        description="Example project split across multiple YAML files",
    )
    project.master_path = base_dir / "master.yaml"

    # Create modules directory
    modules_dir = base_dir / "modules"
    modules_dir.mkdir(parents=True, exist_ok=True)

    # ==========================================================================
    # MODULE 1: Data Types
    # ==========================================================================
    datatypes_module = Module(
        name="DataTypes",
        description="Shared data types and scaling definitions",
    )
    
    cm_speed = CompuMethod(
        name="CM_VehicleSpeed",
        factor=0.01,
        offset=0.0,
        unit="km/h",
    )
    datatypes_module.compu_methods.append(cm_speed)
    
    adt_speed = ApplicationDataType(
        name="VehicleSpeed_T",
        category=AppDataCategory.VALUE,
        compu_method_uid=cm_speed.uid,
        min_value=0.0,
        max_value=65535.0,
    )
    datatypes_module.application_data_types.append(adt_speed)
    
    idt_uint16 = ImplementationDataType(
        name="Impl_uint16",
        base_type=BaseDataType.UINT16,
    )
    datatypes_module.implementation_data_types.append(idt_uint16)
    
    datatypes_module.data_type_mappings.append(
        DataTypeMapping(app_type_uid=adt_speed.uid, impl_type_uid=idt_uint16.uid)
    )

    # ==========================================================================
    # MODULE 2: Interfaces
    # ==========================================================================
    interfaces_module = Module(
        name="Interfaces",
        description="Shared interface definitions",
    )
    
    speed_interface = Interface(
        name="If_VehicleSpeed",
        interface_type=InterfaceType.SENDER_RECEIVER,
        data_elements=[
            DataElement(
                name="VehicleSpeed",
                app_type_uid=adt_speed.uid,
                base_type=BaseDataType.UINT16,
            ),
        ],
    )
    interfaces_module.interfaces.append(speed_interface)

    # ==========================================================================
    # MODULE 3: Speed Sensor SWC
    # ==========================================================================
    sensor_module = Module(
        name="Swc_SpeedSensor",
        description="Speed sensor software component",
    )
    
    speed_sensor = SoftwareComponent(
        name="Swc_SpeedSensor",
        description="Reads vehicle speed from sensor",
        ports=[
            Port(
                name="Pp_VehicleSpeed",
                direction=PortDirection.PROVIDED,
                interface_uid=speed_interface.uid,
            ),
        ],
        runnables=[
            Runnable(name="Run_ReadSpeed", period_ms=10),
        ],
    )
    sensor_module.components.append(speed_sensor)

    # ==========================================================================
    # MODULE 4: Speed Monitor SWC
    # ==========================================================================
    monitor_module = Module(
        name="Swc_SpeedMonitor", 
        description="Speed monitoring software component",
    )
    
    speed_monitor = SoftwareComponent(
        name="Swc_SpeedMonitor",
        description="Monitors vehicle speed",
        ports=[
            Port(
                name="Rp_VehicleSpeed",
                direction=PortDirection.REQUIRED,
                interface_uid=speed_interface.uid,
            ),
        ],
        runnables=[
            Runnable(name="Run_MonitorSpeed", period_ms=20),
        ],
    )
    monitor_module.components.append(speed_monitor)

    # ==========================================================================
    # GLOBAL CONNECTION (in master, spans modules)
    # ==========================================================================
    project.master.global_connections.append(
        PortConnection(
            name="Conn_VehicleSpeed",
            provider_swc_uid=speed_sensor.uid,
            provider_port_uid=speed_sensor.ports[0].uid,
            requester_swc_uid=speed_monitor.uid,
            requester_port_uid=speed_monitor.ports[0].uid,
            description="Cross-module connection: Sensor -> Monitor",
        )
    )

    # ==========================================================================
    # Register modules
    # ==========================================================================
    modules = [
        (datatypes_module, "modules/datatypes.yaml"),
        (interfaces_module, "modules/interfaces.yaml"),
        (sensor_module, "modules/swc_sensor.yaml"),
        (monitor_module, "modules/swc_monitor.yaml"),
    ]
    
    for module, rel_path in modules:
        abs_path = (base_dir / rel_path).resolve()
        project.modules[str(abs_path)] = module
        project.module_paths[module.name] = abs_path
        project.master.modules.append(
            ModuleReference(path=rel_path, name=module.name, description=module.description)
        )
    
    return project


def save_multifile_project(project: MultiFileProject) -> None:
    """Save a complete multi-file project."""
    if not project.master_path:
        raise ValueError("Master path not set")
    
    # Ensure directories exist
    project.master_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save all modules
    for module_name, module_path in project.module_paths.items():
        module_path.parent.mkdir(parents=True, exist_ok=True)
        module = project.modules[str(module_path)]
        with open(module_path, 'w') as f:
            yaml.dump(
                module.to_dict(),
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
                indent=2,
            )
    
    # Save master
    with open(project.master_path, 'w') as f:
        yaml.dump(
            project.master.to_dict(),
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            indent=2,
        )
