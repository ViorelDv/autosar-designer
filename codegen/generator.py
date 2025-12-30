"""
Jinja2-based code generator for AUTOSAR-like components.
"""
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from model import Project, SoftwareComponent, Interface, DataType


# Map model DataType to C types
C_TYPE_MAP = {
    "uint8": "uint8",
    "uint16": "uint16",
    "uint32": "uint32",
    "int8": "int8",
    "int16": "int16",
    "int32": "int32",
    "float32": "float32",
    "float64": "float64",
    "boolean": "boolean",
}


def c_type_filter(data_type: str) -> str:
    """Jinja2 filter to convert DataType to C type string."""
    return C_TYPE_MAP.get(data_type, "uint8")


class CodeGenerator:
    """Generates C code from project configuration."""

    def __init__(self, template_dir: Path = None):
        if template_dir is None:
            template_dir = Path(__file__).parent / "templates"
        
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.env.filters["c_type"] = c_type_filter

    def _resolve_port_interfaces(self, swc: SoftwareComponent, project: Project):
        """Attach interface objects to ports for template access."""
        for port in swc.ports:
            if port.interface_uid:
                port.interface = project.get_interface_by_uid(port.interface_uid)
            else:
                port.interface = None

    def generate_swc_header(self, swc: SoftwareComponent, project: Project) -> str:
        """Generate SWC header file content."""
        self._resolve_port_interfaces(swc, project)
        template = self.env.get_template("swc_header.h.j2")
        return template.render(swc=swc)

    def generate_swc_source(self, swc: SoftwareComponent, project: Project) -> str:
        """Generate SWC source file content."""
        self._resolve_port_interfaces(swc, project)
        template = self.env.get_template("swc_source.c.j2")
        return template.render(swc=swc)

    def generate_rte_header(self, swc: SoftwareComponent, project: Project) -> str:
        """Generate RTE header for an SWC."""
        self._resolve_port_interfaces(swc, project)
        template = self.env.get_template("rte_header.h.j2")
        return template.render(swc=swc)

    def generate_std_types(self) -> str:
        """Generate Std_Types.h."""
        template = self.env.get_template("std_types.h.j2")
        return template.render()

    def generate_rte_types(self, project: Project) -> str:
        """Generate Rte_Type.h with all interface types."""
        template = self.env.get_template("rte_type.h.j2")
        return template.render(interfaces=project.interfaces)

    def generate_all(self, project: Project, output_dir: Path) -> list[Path]:
        """Generate all code files for the project."""
        output_dir.mkdir(parents=True, exist_ok=True)
        generated_files = []

        # Generate common headers
        std_types_path = output_dir / "Std_Types.h"
        std_types_path.write_text(self.generate_std_types())
        generated_files.append(std_types_path)

        rte_types_path = output_dir / "Rte_Type.h"
        rte_types_path.write_text(self.generate_rte_types(project))
        generated_files.append(rte_types_path)

        # Generate per-SWC files
        for swc in project.components:
            # SWC header
            header_path = output_dir / f"{swc.name}.h"
            header_path.write_text(self.generate_swc_header(swc, project))
            generated_files.append(header_path)

            # SWC source
            source_path = output_dir / f"{swc.name}.c"
            source_path.write_text(self.generate_swc_source(swc, project))
            generated_files.append(source_path)

            # RTE header
            rte_path = output_dir / f"Rte_{swc.name}.h"
            rte_path.write_text(self.generate_rte_header(swc, project))
            generated_files.append(rte_path)

        return generated_files


def generate_project_code(project: Project, output_dir: Path) -> list[Path]:
    """Convenience function to generate all code."""
    generator = CodeGenerator()
    return generator.generate_all(project, output_dir)
