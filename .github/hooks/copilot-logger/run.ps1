$scriptDir = Split-Path -Parent $PSCommandPath
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path -Path $scriptDir -ChildPath "..\..\.."))
$errorPath = Join-Path -Path $repoRoot -ChildPath "copilot-logger-error.log"
$loggerPath = Join-Path -Path $repoRoot -ChildPath ".github\hooks\copilot-logger\logger.py"

if (Get-Command python -ErrorAction SilentlyContinue) {
    python $loggerPath
}
elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    python3 $loggerPath
}
else {
@'
Python is not available in PATH. Install Python and verify with `python --version` or `python3 --version`.
'@ | Set-Content -LiteralPath $errorPath -Encoding UTF8
}
