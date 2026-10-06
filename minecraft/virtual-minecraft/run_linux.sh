#!/usr/bin/env bash
# ./run_linux.sh                -> menu
# ./run_linux.sh test w.mcworld -> any vmc.py command
cd "$(dirname "$0")"
PY="$(cat .python_cmd 2>/dev/null || echo python3)"
if [ $# -eq 0 ]; then exec "$PY" vmc.py menu; fi
exec "$PY" vmc.py "$@"
