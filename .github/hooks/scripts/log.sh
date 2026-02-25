#!/usr/bin/env bash

if command -v python >/dev/null 2>&1; then
  python ./.github/hooks/scripts/logger.py
elif command -v python3 >/dev/null 2>&1; then
  python3 ./.github/hooks/scripts/logger.py
fi
