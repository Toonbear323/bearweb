#!/usr/bin/env bash
# One-time setup on Linux: finds (or installs) Python 3.8+, then downloads the Bedrock Dedicated Server.
set -e
cd "$(dirname "$0")"
if [ "$(uname -s)" != "Linux" ]; then
  echo "Bedrock Dedicated Server only exists for Windows and Linux (this is $(uname -s))."
  exit 1
fi
PY=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)'; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ]; then
  echo "Python 3.8+ not found - installing it (needs sudo)..."
  if command -v apt-get >/dev/null 2>&1; then sudo apt-get update && sudo apt-get install -y python3
  elif command -v dnf >/dev/null 2>&1; then sudo dnf install -y python3
  elif command -v pacman >/dev/null 2>&1; then sudo pacman -S --noconfirm python
  else echo "Please install Python 3.8+ and run this script again."; exit 1
  fi
  PY=python3
fi
echo "$PY" > .python_cmd
chmod +x run_linux.sh 2>/dev/null || true
"$PY" vmc.py setup "$@"
echo
echo "Setup finished. Next: ./run_linux.sh   (or ./run_linux.sh test my_world.mcworld)"
