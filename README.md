# AUTOSAR Designer

A lightweight DaVinci Developer-like tool for designing AUTOSAR-style software components with YAML-based configuration and Jinja2 code generation.

## Features

- **Visual Component Design**: Create and configure Software Components (SWCs), Interfaces, Ports, and Runnables
- **Tree-based Navigation**: Browse project structure with intuitive icons and context menus
- **YAML Persistence**: Human-readable project files
- **Code Generation**: Generate C skeleton code with Jinja2 templates
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

### Project Structure

```
📁 Project
├── 📂 Interfaces
│   ├── 🔗 Sender/Receiver Interfaces
│   │   └── 📊 Data Elements
│   └── ⚡ Client/Server Interfaces
│       └── ⚙️ Operations
└── 📂 Software Components
    ├── 📦 SWC 1
    │   ├── ◀ Required Ports
    │   ├── ▶ Provided Ports
    │   └── ▷ Runnables
    └── 📦 SWC 2
        └── ...
```

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

## YAML Project Format

```yaml
name: My Project
description: Example automotive project
interfaces:
  - name: If_VehicleSpeed
    interface_type: sender_receiver
    data_elements:
      - name: VehicleSpeed
        data_type: uint16
        init_value: "0"
components:
  - name: Swc_SpeedSensor
    ports:
      - name: Pp_Speed
        direction: provided
        interface_uid: abc12345
    runnables:
      - name: Run_ReadSpeed
        period_ms: 10
```

## Customizing Templates

Templates are in `codegen/templates/`. Modify them to match your coding standards:

- `swc_header.h.j2` - Component header
- `swc_source.c.j2` - Component source  
- `rte_header.h.j2` - RTE interface header
- `std_types.h.j2` - Standard types
- `rte_type.h.j2` - Interface types

## Roadmap

- [ ] Graphical SWC composition diagram
- [ ] Drag-and-drop port connections
- [ ] Operation argument editor
- [ ] ARXML import/export
- [ ] Copy/paste elements
- [ ] Undo/redo
- [ ] Code preview panel

## License

MIT License
