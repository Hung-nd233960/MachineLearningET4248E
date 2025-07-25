import os
from pathlib import Path

# Get the current working directory (the project root, where this script is run)
project_dir = Path.cwd()

# Assume venv is in the project directory (change if needed)
venv_path = project_dir / ".venv" / "bin" / "activate"

# Script content
bash_script = f"""#!/bin/bash
cd "{project_dir}"
source "{venv_path}"
streamlit run main.py
"""

# Path to Desktop
desktop_path = Path.home() / "Desktop" / "MedFabric.sh"

# Write the script to Desktop
with open(desktop_path, "w", encoding="utf-8") as f:
    f.write(bash_script)

# Make it executable
os.chmod(desktop_path, 0o755)

print(f"Launcher script created at: {desktop_path}")
