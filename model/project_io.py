"""
YAML-based project persistence.
"""
import yaml
from pathlib import Path
from .elements import Project


def save_project(project: Project, filepath: Path) -> None:
    """Save project to YAML file."""
    with open(filepath, 'w') as f:
        yaml.dump(
            project.to_dict(),
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            indent=2,
        )


def load_project(filepath: Path) -> Project:
    """Load project from YAML file."""
    with open(filepath, 'r') as f:
        data = yaml.safe_load(f)
    return Project.from_dict(data)


def create_example_project() -> Project:
    """Create an example project for testing with full AUTOSAR-style data types."""
    from .elements import (
        Interface, InterfaceType, DataElement, BaseDataType,
        Operation, OperationArgument, ArgumentDirection,
        SoftwareComponent, Port, PortDirection, Runnable,
        CompuMethod, ApplicationDataType, ImplementationDataType,
        DataTypeMapping, AppDataCategory, PortConnection
    )

    # ==========================================================================
    # COMPU METHODS (Scaling)
    # ==========================================================================
    cm_speed = CompuMethod(
        name="CM_VehicleSpeed",
        factor=0.01,  # internal * 0.01 = physical (km/h)
        offset=0.0,
        unit="km/h",
        description="Vehicle speed scaling: 0-655.35 km/h",
    )

    cm_temperature = CompuMethod(
        name="CM_Temperature",
        factor=0.1,
        offset=-40.0,  # internal * 0.1 - 40 = physical (°C)
        unit="°C",
        description="Temperature scaling: -40 to +215 °C",
    )

    # ==========================================================================
    # APPLICATION DATA TYPES (Abstract/Logical)
    # ==========================================================================
    adt_speed = ApplicationDataType(
        name="VehicleSpeed_T",
        category=AppDataCategory.VALUE,
        compu_method_uid=cm_speed.uid,
        min_value=0.0,
        max_value=65535.0,
        init_value="0",
        description="Vehicle speed in km/h (physical), scaled by 100",
    )

    adt_speed_valid = ApplicationDataType(
        name="SpeedValid_T",
        category=AppDataCategory.VALUE,
        min_value=0,
        max_value=1,
        init_value="0",
        description="Speed validity flag",
    )

    adt_diag_id = ApplicationDataType(
        name="DiagId_T",
        category=AppDataCategory.VALUE,
        min_value=0,
        max_value=65535,
        init_value="0",
        description="Diagnostic data identifier",
    )

    adt_diag_status = ApplicationDataType(
        name="DiagStatus_T",
        category=AppDataCategory.ENUM,
        enum_literals=[
            ("DIAG_OK", 0),
            ("DIAG_PENDING", 1),
            ("DIAG_NOT_SUPPORTED", 2),
            ("DIAG_ERROR", 3),
        ],
        init_value="0",
        description="Diagnostic operation status",
    )

    # ==========================================================================
    # IMPLEMENTATION DATA TYPES (Platform-specific)
    # ==========================================================================
    idt_uint16 = ImplementationDataType(
        name="Impl_uint16",
        base_type=BaseDataType.UINT16,
        description="16-bit unsigned integer",
    )

    idt_boolean = ImplementationDataType(
        name="Impl_boolean",
        base_type=BaseDataType.BOOLEAN,
        description="Boolean type",
    )

    idt_uint8 = ImplementationDataType(
        name="Impl_uint8",
        base_type=BaseDataType.UINT8,
        description="8-bit unsigned integer",
    )

    # ==========================================================================
    # DATA TYPE MAPPINGS (App -> Impl)
    # ==========================================================================
    map_speed = DataTypeMapping(
        app_type_uid=adt_speed.uid,
        impl_type_uid=idt_uint16.uid,
    )

    map_speed_valid = DataTypeMapping(
        app_type_uid=adt_speed_valid.uid,
        impl_type_uid=idt_boolean.uid,
    )

    map_diag_id = DataTypeMapping(
        app_type_uid=adt_diag_id.uid,
        impl_type_uid=idt_uint16.uid,
    )

    map_diag_status = DataTypeMapping(
        app_type_uid=adt_diag_status.uid,
        impl_type_uid=idt_uint8.uid,
    )

    # ==========================================================================
    # INTERFACES
    # ==========================================================================
    
    # Sender/Receiver interface for vehicle speed
    speed_interface = Interface(
        name="If_VehicleSpeed",
        interface_type=InterfaceType.SENDER_RECEIVER,
        description="Vehicle speed data interface",
        data_elements=[
            DataElement(
                name="VehicleSpeed",
                app_type_uid=adt_speed.uid,
                base_type=BaseDataType.UINT16,
                init_value="0",
                description="Vehicle speed in km/h * 100",
            ),
            DataElement(
                name="SpeedValid",
                app_type_uid=adt_speed_valid.uid,
                base_type=BaseDataType.BOOLEAN,
                init_value="false",
                description="Speed validity flag",
            ),
        ],
    )

    # Client/Server interface for diagnostics
    diag_interface = Interface(
        name="If_DiagService",
        interface_type=InterfaceType.CLIENT_SERVER,
        description="Diagnostic service interface",
        operations=[
            Operation(
                name="ReadDataById",
                return_type_uid=adt_diag_status.uid,
                return_base_type=BaseDataType.UINT8,
                arguments=[
                    OperationArgument(
                        name="dataId",
                        direction=ArgumentDirection.IN,
                        app_type_uid=adt_diag_id.uid,
                        base_type=BaseDataType.UINT16,
                        description="Data identifier to read",
                    ),
                    OperationArgument(
                        name="data",
                        direction=ArgumentDirection.OUT,
                        base_type=BaseDataType.UINT8,
                        description="Output data buffer",
                    ),
                ],
                description="Read diagnostic data by ID",
            ),
        ],
    )

    # ==========================================================================
    # SOFTWARE COMPONENTS
    # ==========================================================================
    
    speed_sensor = SoftwareComponent(
        name="Swc_SpeedSensor",
        description="Speed sensor software component",
        ports=[
            Port(
                name="Pp_VehicleSpeed",
                direction=PortDirection.PROVIDED,
                interface_uid=speed_interface.uid,
                description="Provides vehicle speed",
            ),
        ],
        runnables=[
            Runnable(
                name="Run_ReadSpeed",
                period_ms=10,
                description="Read speed sensor every 10ms",
            ),
        ],
    )

    speed_monitor = SoftwareComponent(
        name="Swc_SpeedMonitor",
        description="Speed monitoring component",
        ports=[
            Port(
                name="Rp_VehicleSpeed",
                direction=PortDirection.REQUIRED,
                interface_uid=speed_interface.uid,
                description="Receives vehicle speed",
            ),
            Port(
                name="Ps_DiagService",
                direction=PortDirection.PROVIDED,
                interface_uid=diag_interface.uid,
                description="Provides diagnostic services",
            ),
        ],
        runnables=[
            Runnable(
                name="Run_MonitorSpeed",
                period_ms=20,
                description="Monitor speed every 20ms",
            ),
            Runnable(
                name="Run_DiagHandler",
                period_ms=0,
                description="Event-triggered diagnostic handler",
            ),
        ],
    )

    diag_tester = SoftwareComponent(
        name="Swc_DiagTester",
        description="Diagnostic tester component (client)",
        ports=[
            Port(
                name="Rc_DiagService",
                direction=PortDirection.REQUIRED,
                interface_uid=diag_interface.uid,
                description="Calls diagnostic services",
            ),
        ],
        runnables=[
            Runnable(
                name="Run_DiagRequest",
                period_ms=100,
                description="Periodic diagnostic request",
            ),
        ],
    )

    # ==========================================================================
    # PORT CONNECTIONS (Assembly Connectors)
    # ==========================================================================
    
    # Connect SpeedSensor -> SpeedMonitor (Sender/Receiver)
    conn_speed = PortConnection(
        name="Conn_VehicleSpeed",
        provider_swc_uid=speed_sensor.uid,
        provider_port_uid=speed_sensor.ports[0].uid,  # Pp_VehicleSpeed
        requester_swc_uid=speed_monitor.uid,
        requester_port_uid=speed_monitor.ports[0].uid,  # Rp_VehicleSpeed
        description="Vehicle speed data connection",
    )

    # Connect SpeedMonitor -> DiagTester (Client/Server)
    conn_diag = PortConnection(
        name="Conn_DiagService",
        provider_swc_uid=speed_monitor.uid,
        provider_port_uid=speed_monitor.ports[1].uid,  # Ps_DiagService
        requester_swc_uid=diag_tester.uid,
        requester_port_uid=diag_tester.ports[0].uid,  # Rc_DiagService
        description="Diagnostic service connection",
    )

    # ==========================================================================
    # ASSEMBLE PROJECT
    # ==========================================================================
    return Project(
        name="Example Automotive Project",
        description="A sample project demonstrating AUTOSAR-like configuration with full data type support",
        compu_methods=[cm_speed, cm_temperature],
        application_data_types=[adt_speed, adt_speed_valid, adt_diag_id, adt_diag_status],
        implementation_data_types=[idt_uint16, idt_boolean, idt_uint8],
        data_type_mappings=[map_speed, map_speed_valid, map_diag_id, map_diag_status],
        interfaces=[speed_interface, diag_interface],
        components=[speed_sensor, speed_monitor, diag_tester],
        connections=[conn_speed, conn_diag],
    )
