import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = (SCRIPT_DIR / ".." / ".." / "..").resolve()
ERROR_FILE = REPO_ROOT / "copilot-logger-error.log"


def _get_nested(data, *keys):
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _stringify(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def _write_error_file(problem, actions):
    lines = [
        "Copilot logger hook failed.",
        f"Problem: {problem}",
        "",
        "How to fix:",
    ]
    lines.extend(f"- {action}" for action in actions)
    try:
        ERROR_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except OSError:
        pass


def _get_git_email():
    try:
        result = subprocess.run(
            ["git", "config", "--get", "user.email"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        _write_error_file(
            "The git command is not available.",
            [
                "Install Git and ensure `git` is available in PATH.",
                "Run `git --version` in this repository to verify access.",
            ],
        )
        return ""
    email = result.stdout.strip()
    if not email:
        _write_error_file(
            "Git email is not configured.",
            [
                'Set a repo email: `git config user.email "you@example.com"`.',
                'Or set a global email: `git config --global user.email "you@example.com"`.',
                "Run `git config --get user.email` to confirm.",
            ],
        )
    return email


def main():
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        _write_error_file(
            "Hook input from Copilot is invalid JSON.",
            [
                "Restart the Copilot session and try again.",
                "If this persists, verify hook configuration JSON is valid.",
            ],
        )
        return 1

    if not isinstance(payload, dict):
        _write_error_file(
            "Hook input has an unexpected format.",
            [
                "Restart the Copilot session.",
                "Ensure the hook receives JSON object input from Copilot.",
            ],
        )
        return 1

    session_id = payload.get("sessionId")
    transcript_path = payload.get("transcriptPath")
    if not session_id or not transcript_path:
        _write_error_file(
            "Hook input is missing sessionId or transcriptPath.",
            [
                "Restart the Copilot session so hook payload is regenerated.",
                "Confirm `.github/hooks/copilot-logger-cli.json` is being loaded.",
            ],
        )
        return 1

    transcript_file = Path(str(transcript_path))
    if not transcript_file.exists():
        _write_error_file(
            f"Transcript file was not found: {transcript_file}",
            [
                "Restart the Copilot session and run another prompt.",
                "Verify the transcript path is accessible from this machine.",
            ],
        )
        return 1

    email = _get_git_email()
    if not email:
        return 1

    log_dir = REPO_ROOT / "copilot-logs" / email
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        _write_error_file(
            f"Could not create log directory: {log_dir}",
            [
                "Create the folder manually and ensure write permissions are available.",
                "Verify the repository directory is writable.",
            ],
        )
        return 1

    date = datetime.now().strftime("%Y-%m-%d")
    short_id = str(session_id).split("-")[0]
    log_path = log_dir / f"{date}_{short_id}.log"

    entries = []
    pending_ask_user = {}

    try:
        lines = transcript_file.read_text(encoding="utf-8").splitlines()
    except OSError:
        _write_error_file(
            f"Could not read transcript file: {transcript_file}",
            [
                "Ensure the transcript file exists and is readable.",
                "Restart Copilot and rerun your prompt.",
            ],
        )
        return 1

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        try:
            evt = json.loads(line)
        except json.JSONDecodeError:
            continue

        evt_type = _get_nested(evt, "type")
        if evt_type == "user.message":
            content = _stringify(_get_nested(evt, "data", "content")).strip()
            timestamp = _stringify(_get_nested(evt, "timestamp")).strip()
            if content:
                entries.append(f"{timestamp} [User]\n{content}")
        elif evt_type == "tool.execution_start" and _get_nested(evt, "data", "toolName") == "ask_user":
            tool_call_id = _stringify(_get_nested(evt, "data", "toolCallId")).strip()
            question = _stringify(_get_nested(evt, "data", "arguments", "question")).strip()
            choices = _get_nested(evt, "data", "arguments", "choices")
            if tool_call_id and question:
                entry = f"{_stringify(_get_nested(evt, 'timestamp'))} [Agent]\n{question}"
                if isinstance(choices, list) and choices:
                    entry += f"\nChoices: {', '.join(str(choice) for choice in choices)}"
                pending_ask_user[tool_call_id] = entry
        elif evt_type == "tool.execution_complete":
            tool_call_id = _stringify(_get_nested(evt, "data", "toolCallId")).strip()
            if tool_call_id and tool_call_id in pending_ask_user:
                entries.append(pending_ask_user.pop(tool_call_id))
                answer = _stringify(_get_nested(evt, "data", "result", "content")).strip()
                if answer:
                    entries.append(f"{_stringify(_get_nested(evt, 'timestamp'))} [User]\n{answer}")

    if entries:
        try:
            log_path.write_text("\n\n".join(entries), encoding="utf-8")
        except OSError:
            _write_error_file(
                f"Could not write log file: {log_path}",
                [
                    "Ensure `copilot-logs` is writable in this repository.",
                    "Retry after fixing file permissions.",
                ],
            )
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
