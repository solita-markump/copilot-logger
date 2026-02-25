if (Get-Command python -ErrorAction SilentlyContinue) {
    python ".\.github\hooks\scripts\logger.py"
}
elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    python3 ".\.github\hooks\scripts\logger.py"
}
