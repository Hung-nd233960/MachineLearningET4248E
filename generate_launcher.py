#!/usr/bin/env python3
import os
from pathlib import Path

# Define project root (where this Python script is run)
project_dir = Path.cwd()

# Output launcher path
desktop_path = Path.home() / "Desktop" / "MedFabric.sh"

# Ensure main.py exists
main_py = project_dir / "main.py"
if not main_py.exists():
    raise FileNotFoundError(f"main.py not found in: {project_dir}")

# Build Bash launcher script
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
npx electron .

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

# Write the script to Desktop
with open(desktop_path, "w", encoding="utf-8") as f:
    f.write(bash_script)

# Make it executable
os.chmod(desktop_path, 0o755)

print(f"✅ Launcher script created: {desktop_path}")
