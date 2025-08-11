#!/bin/bash
set -e

cd "/home/Plutonium/Documents/MachineLearningET4248E"

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

cd "/home/Plutonium/Documents/MachineLearningET4248E/electron-app"
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
