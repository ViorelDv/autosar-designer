# AUTOSAR Designer

A lightweight DaVinci Developer-like tool for designing AUTOSAR-style software components with YAML-based configuration and Jinja2 code generation.

## Features

- **Visual Component Design**: Create and configure Software Components (SWCs), Interfaces, Ports, and Runnables
- **Full Data Type Hierarchy**: Application Types, Implementation Types, CompuMethods, Type Mappings
- **Port Connections**: Connect provided ↔ required ports with matching interfaces
- **Multi-File Projects**: Split your project across multiple YAML modules (like ARXML packages)
- **Tree-based Navigation**: Browse project structure with intuitive icons and context menus
- **YAML Persistence**: Human-readable project files
- **Code Generation**: Jinja2-based C code generation
- **Dark Theme**: Modern VS Code-inspired interface

## Installation

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

### Quick Start

1. Click **Load Example** in the toolbar to see a sample project
2. Click on elements in the tree to edit their properties
3. Right-click to add/delete elements
4. Press **F5** or click **Generate Code** to generate C code

## Project Structure

### Single-File Project

```yaml
name: My Project
compu_methods: [...]
application_data_types: [...]
implementation_data_types: [...]
data_type_mappings: [...]
interfaces: [...]
components: [...]
connections: [...]
```

### Multi-File Project

For larger projects, split your configuration across multiple files:

```
project/
├── master.yaml              # Master project file
└── modules/
    ├── datatypes.yaml       # Shared data types & scaling
    ├── interfaces.yaml      # Shared interfaces
    ├── swc_sensor.yaml      # Sensor component
    ├── swc_monitor.yaml     # Monitor component
    └── swc_actuator.yaml    # Actuator component
```

**master.yaml:**
```yaml
name: Multi-Module Project
modules:
  - path: modules/datatypes.yaml
    name: DataTypes
    enabled: true
  - path: modules/interfaces.yaml
    name: Interfaces
    enabled: true
  - path: modules/swc_sensor.yaml
    name: Swc_SpeedSensor
    enabled: true
global_connections:
  - name: Conn_Speed
    provider_swc_uid: abc123
    provider_port_uid: def456
    requester_swc_uid: ghi789
    requester_port_uid: jkl012
```

**modules/interfaces.yaml:**
```yaml
name: Interfaces
interfaces:
  - name: If_VehicleSpeed
    interface_type: sender_receiver
    data_elements:
      - name: Speed
        app_type_uid: xyz789  # References type from datatypes.yaml
```

**modules/swc_sensor.yaml:**
```yaml
name: Swc_SpeedSensor
components:
  - name: Swc_SpeedSensor
    ports:
      - name: Pp_Speed
        direction: provided
        interface_uid: abc123  # References interface from interfaces.yaml
```

### Key Benefits of Multi-File

| Benefit | Description |
|---------|-------------|
| **Modularity** | Each team can own their module |
| **Reusability** | Share interfaces/types across projects |
| **Version Control** | Better diffs, less merge conflicts |
| **Cross-Module Connections** | Connect ports from different modules |

## Data Type Hierarchy

```
📂 Data Types
├── 📐 CompuMethod         # Scaling: physical = internal × factor + offset
│   └── CM_VehicleSpeed    # factor=0.01, unit=km/h
├── 🔷 Application Type    # Abstract/logical type
│   └── VehicleSpeed_T     # Uses CM_VehicleSpeed, range 0-65535
└── 🔶 Implementation Type # Platform-specific C type
    └── Impl_uint16        # Maps to uint16
```

## Port Connections

Connect ports that share the same interface:

```
📦 Swc_SpeedSensor
└── ▶ Pp_VehicleSpeed [If_VehicleSpeed] 🔌
                ↓
📦 Swc_SpeedMonitor  
└── ◀ Rp_VehicleSpeed [If_VehicleSpeed] 🔌
```

**Creating connections:**
- Right-click a PROVIDED port → "Connect to Required Port..."
- Or use toolbar → "+ Connection"

## Generated Code

The code generator produces:

| File | Description |
|------|-------------|
| `Std_Types.h` | Standard AUTOSAR types |
| `Rte_Type.h` | RTE type definitions for interfaces |
| `<SWC>.h` | Component header with runnable prototypes |
| `<SWC>.c` | Component source with USER CODE sections |
| `Rte_<SWC>.h` | RTE API for each component |

### USER CODE Sections

Generated `.c` files include preserved sections:

```c
/* USER CODE BEGIN Includes */
// Your code here - preserved on regeneration
/* USER CODE END Includes */
```

## Customizing Templates

Templates are in `codegen/templates/`. Modify them to match your coding standards:

- `swc_header.h.j2` - Component header
- `swc_source.c.j2` - Component source  
- `rte_header.h.j2` - RTE interface header
- `std_types.h.j2` - Standard types
- `rte_type.h.j2` - Interface types

## API Usage

```python
from model import (
    MultiFileProject, 
    create_example_multifile_project,
    save_multifile_project
)
from pathlib import Path

# Create multi-file project
project = create_example_multifile_project(Path("my_project"))
save_multifile_project(project)

# Load and merge
project = MultiFileProject()
project.load_master(Path("my_project/master.yaml"))
merged = project.get_merged_project()  # Unified view

# Find which module contains an element
module_name = project.find_element_module(some_uid)
```

## Roadmap

- [x] Multi-file project support
- [x] Port connections
- [x] Full data type hierarchy
- [ ] Graphical SWC composition diagram
- [ ] Drag-and-drop port connections
- [ ] Operation argument editor in GUI
- [ ] ARXML import/export
- [ ] Copy/paste elements
- [ ] Undo/redo
- [ ] Code preview panel

## License

MIT License
