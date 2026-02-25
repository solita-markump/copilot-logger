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
Python is not available in PATH. Install Python and verify with `python --version` or `python3 --version`.
EOF
fi
