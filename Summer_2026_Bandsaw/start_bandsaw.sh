#!/bin/bash
export DISPLAY=:0

LOCKFILE=/tmp/bandsaw.lock
exec 9>"$LOCKFILE"
flock -n 9 || {
  echo "Script already running."
  exit 1
}

echo "LOCK acquired. Starting script..."

sleep 3

echo "Changing directory..."
cd /home/pi/Desktop/object_detection || { echo "❌ Failed to cd"; exit 1; }

echo "Activating virtual environment..."
source myenv/bin/activate || { echo "❌ Failed to activate venv"; exit 1; }

echo "Running Python script..."
python bandsaw_monitor.py

echo "Script finished."
