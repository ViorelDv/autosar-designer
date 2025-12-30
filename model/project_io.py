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
    """Create an example project for testing."""
    from .elements import (
        Interface, InterfaceType, DataElement, DataType,
        Operation, SoftwareComponent, Port, PortDirection, Runnable
    )

    # Create a Sender/Receiver interface
    speed_interface = Interface(
        name="If_VehicleSpeed",
        interface_type=InterfaceType.SENDER_RECEIVER,
        description="Vehicle speed data interface",
        data_elements=[
            DataElement(
                name="VehicleSpeed",
                data_type=DataType.UINT16,
                init_value="0",
                description="Vehicle speed in km/h * 100",
            ),
            DataElement(
                name="SpeedValid",
                data_type=DataType.BOOLEAN,
                init_value="false",
                description="Speed validity flag",
            ),
        ],
    )

    # Create a Client/Server interface
    diag_interface = Interface(
        name="If_DiagService",
        interface_type=InterfaceType.CLIENT_SERVER,
        description="Diagnostic service interface",
        operations=[
            Operation(
                name="ReadDataById",
                return_type=DataType.UINT8,
                arguments=[
                    ("dataId", DataType.UINT16, "in"),
                    ("data", DataType.UINT8, "out"),
                ],
                description="Read diagnostic data by ID",
            ),
        ],
    )

    # Create SWCs
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

    return Project(
        name="Example Automotive Project",
        description="A sample project demonstrating AUTOSAR-like configuration",
        interfaces=[speed_interface, diag_interface],
        components=[speed_sensor, speed_monitor],
    )
