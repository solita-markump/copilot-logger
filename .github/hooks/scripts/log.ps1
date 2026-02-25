$scriptDir = Split-Path -Parent $PSCommandPath
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path -Path $scriptDir -ChildPath "..\..\.."))
$errorPath = Join-Path -Path $repoRoot -ChildPath "copilot-logger-error.log"

if (Get-Command python -ErrorAction SilentlyContinue) {
    python ".\.github\hooks\scripts\logger.py"
}
elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    python3 ".\.github\hooks\scripts\logger.py"
}
else {
@'
Copilot logger hook failed.
Problem: Python is not installed or not available in PATH.

How to fix:
- Install Python and ensure either `python` or `python3` is available in PATH.
- Verify with `python --version` or `python3 --version`.
- Re-run the Copilot action after Python is installed.
'@ | Set-Content -LiteralPath $errorPath -Encoding UTF8
}
