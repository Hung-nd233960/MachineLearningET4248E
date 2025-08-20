#!/usr/bin/env python3
import os
from pathlib import Path


def create_launcher_script(to_desktop=True):
    project_dir = Path.cwd()
    if to_desktop:
        output_path = Path.home() / "Desktop" / "MedFabric.sh"
    else:
        output_path = project_dir / "MedFabric.sh"

    main_py = project_dir / "main.py"
    if not main_py.exists():
        raise FileNotFoundError(f"main.py not found in: {project_dir}")

    bash_script = f"""#!/bin/bash
set -e

cd "{project_dir}"

# Activate Poetry environment
echo "🔹 Activating Poetry environment..."
$(poetry env activate)

# Start Streamlit in background
echo "🔹 Starting Streamlit..."
streamlit run main.py --server.headless true &
STREAMLIT_PID=$!

# Wait for Streamlit to start
echo "🔹 Waiting for Streamlit to become available..."
until nc -z localhost 8501; do
    sleep 1
done

cd "{project_dir}/electron-app"
# Launch Electron
echo "🔹 Launching Electron..."
npx electron . --no-sandbox

# Cleanup when Electron closes
echo "🔹 Stopping Streamlit..."
pids=$(lsof -ti tcp:8501)

for pid in $pids; do
  # Check if the process name contains "streamlit"
  if ps -p $pid -o comm= | grep -qi streamlit; then
    echo "Killing Streamlit process $pid"
    kill $pid
  fi
done
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(bash_script)

    os.chmod(output_path, 0o755)
    print(f"✅ Launcher script created: {output_path}")


def create_desktop_entry(
    icon_path: str, app_name: str, shell_script_path: Path, to_desktop=True
):
    desktop_entry_content = f"""[Desktop Entry]
Type=Application
Name={app_name}
Exec={shell_script_path}
Icon={icon_path}
Terminal=true
Categories=Utility;Development;
"""

    if to_desktop:
        desktop_path = Path.home() / "Desktop" / f"{app_name}.desktop"
    else:
        desktop_path = Path.cwd() / f"{app_name}.desktop"

    with open(desktop_path, "w", encoding="utf-8") as f:
        f.write(desktop_entry_content)

    os.chmod(desktop_path, 0o755)
    print(f"✅ Desktop entry created: {desktop_path}")
    return desktop_path


def create_desktop_entry(
    icon_path: Path, app_name: str, shell_script_path: Path, to_desktop: bool = True
):
    if not icon_path.exists():
        raise FileNotFoundError(f"Icon file not found: {icon_path}")

    desktop_entry_content = f"""[Desktop Entry]
Type=Application
Name={app_name}
Exec={shell_script_path}
Icon={icon_path}
Terminal=true
Categories=Utility;Development;
"""

    desktop_path = (
        Path.home() / "Desktop" if to_desktop else Path.cwd()
    ) / f"{app_name}.desktop"

    with open(desktop_path, "w", encoding="utf-8") as f:
        f.write(desktop_entry_content)

    os.chmod(desktop_path, 0o755)
    print(f"✅ Desktop entry created: {desktop_path}")
    return desktop_path


if __name__ == "__main__":
    # Change to False to create script in current directory instead of Desktop
    create_launcher_script(to_desktop=False)
    icon_path = Path.cwd() / "icon.png"  # Adjust path to your icon
    app_name = "MedFabric"
    shell_script_path = Path.cwd() / "MedFabric.sh"
    create_desktop_entry(icon_path, app_name, shell_script_path, to_desktop=True)
    print("✅ All setup complete!")
