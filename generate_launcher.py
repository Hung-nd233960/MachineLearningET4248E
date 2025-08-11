import os
from pathlib import Path

# Define project root (where this Python script is run)
project_dir = Path.cwd()

# Path to venv activate script
venv_path = project_dir / ".venv" / "bin" / "activate"

# Path to output script
desktop_path = Path.home() / "Desktop" / "MedFabric.sh"

# Ensure venv and main.py exist
main_py = project_dir / "main.py"
if not venv_path.exists():
    raise FileNotFoundError(f"Virtual environment not found: {venv_path}")
if not main_py.exists():
    raise FileNotFoundError(f"main.py not found in: {project_dir}")

# Build Bash script
bash_script = f"""#!/bin/bash
cd "{project_dir}"
source "{venv_path}"
exec streamlit run main.py
"""

# Write the script to Desktop
with open(desktop_path, "w", encoding="utf-8") as f:
    f.write(bash_script)

# Make it executable
os.chmod(desktop_path, 0o755)

print(f"✅ Streamlit launcher script created: {desktop_path}")

