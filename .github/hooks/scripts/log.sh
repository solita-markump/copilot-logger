#!/usr/bin/env bash

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "$script_dir/../../.." && pwd)"
error_file="$repo_root/copilot-logger-error.log"
logger_path="$repo_root/.github/hooks/scripts/logger.py"

if command -v python >/dev/null 2>&1; then
  python "$logger_path"
elif command -v python3 >/dev/null 2>&1; then
  python3 "$logger_path"
else
  cat > "$error_file" <<'EOF'
Copilot logger hook failed.
Problem: Python is not installed or not available in PATH.

How to fix:
- Install Python and ensure either `python` or `python3` is available in PATH.
- Verify with `python --version` or `python3 --version`.
- Re-run the Copilot action after Python is installed.
EOF
fi
