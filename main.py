#!/usr/bin/env python3
"""
AUTOSAR Designer - Main entry point.

A lightweight tool for designing AUTOSAR-like software components
with YAML-based configuration and Jinja2 code generation.
"""
import sys
import subprocess
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def install_requirements():
    """Automatically install required packages if not available."""
    required_packages = {
        'PyQt6': 'PyQt6>=6.4.0',
        'yaml': 'PyYAML>=6.0',
        'jinja2': 'Jinja2>=3.0'
    }
    
    missing_packages = []
    
    for module_name, package_spec in required_packages.items():
        try:
            __import__(module_name)
        except ImportError:
            missing_packages.append(package_spec)
    
    if missing_packages:
        print("Installing missing dependencies...")
        print(f"Packages to install: {', '.join(missing_packages)}")
        
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'
            ])
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', *missing_packages
            ])
            print("✓ All dependencies installed successfully!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Error installing dependencies: {e}")
            print("Please install manually using: pip install -r requirements.txt")
            return False
    
    return True


if __name__ == "__main__":
    # Install requirements before importing GUI modules
    if install_requirements():
        from gui import main
        main()
    else:
        sys.exit(1)
