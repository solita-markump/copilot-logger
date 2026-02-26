import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Change this to suit your needs. Related to repo root.
LOGS_DIR = "copilot-logs"


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = (SCRIPT_DIR / ".." / ".." / "..").resolve()
FULL_LOGS_DIR = REPO_ROOT / LOGS_DIR

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


def _write_error_file(message):
    try:
        (REPO_ROOT / "copilot-logger-error.log").write_text(
            f"{_stringify(message).rstrip()}\n", encoding="utf-8"
        )
    except OSError:
        pass


def _fail(message):
    _write_error_file(message)
    return 1


def _get_git_email():
    try:
        result = subprocess.run(
            ["git", "config", "--get", "user.email"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        result = None

    email = ""
    if result is not None and result.returncode == 0:
        email = result.stdout.strip()

    if not email:
        _write_error_file(
            f"Failed to fetch email with `git config --get user.email`.\n"
            "Possible causes:\n"
            "- Git is not installed or not available in PATH.\n"
            "- Current directory is not a Git repository.\n"
            "- `user.email` is not configured."
        )
        return ""

    return email


def _iter_transcript_events(transcript_file):
    # Transcript is JSONL; skip empty/malformed lines.
    with transcript_file.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            try:
                evt = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(evt, dict):
                yield evt


def _collect_entries(events):
    entries = []
    # ask_user prompts are split across start/complete events.
    pending_ask_user = {}

    for evt in events:
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
                # Hold until completion so question and answer stay adjacent.
                entry = f"{_stringify(_get_nested(evt, 'timestamp'))} [Agent]\n{question}"
                if isinstance(choices, list) and choices:
                    entry += "\nChoices:\n" + "\n".join(f"  - {choice}" for choice in choices)
                pending_ask_user[tool_call_id] = entry
        elif evt_type == "tool.execution_complete":
            tool_call_id = _stringify(_get_nested(evt, "data", "toolCallId")).strip()
            if tool_call_id and tool_call_id in pending_ask_user:
                entries.append(pending_ask_user.pop(tool_call_id))
                answer = _stringify(_get_nested(evt, "data", "result", "content")).strip()
                if answer:
                    entries.append(f"{_stringify(_get_nested(evt, 'timestamp'))} [User]\n{answer}")

    return entries


def main():
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return _fail("Hook input is invalid JSON.")

    if not isinstance(payload, dict):
        return _fail("Hook input has an unexpected format (expected JSON object).")

    session_id = payload.get("sessionId")
    transcript_path = payload.get("transcriptPath")
    if not session_id or not transcript_path:
        return _fail("Hook input is missing `sessionId` or `transcriptPath`.")

    transcript_file = Path(str(transcript_path))
    if not transcript_file.exists():
        return _fail(f"Transcript file not found: {transcript_file}")

    email = _get_git_email()
    if not email:
        return 1

    log_dir = FULL_LOGS_DIR / email
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        return _fail(f"Could not create log directory: {log_dir}")

    date = datetime.now().strftime("%Y-%m-%d")
    # Keep file names readable while still mapping to a session.
    short_id = str(session_id).split("-")[0]
    log_path = log_dir / f"{date}_{short_id}.log"

    try:
        entries = _collect_entries(_iter_transcript_events(transcript_file))
    except OSError:
        return _fail(f"Could not read transcript file: {transcript_file}")

    if entries:
        try:
            log_path.write_text("\n\n".join(entries), encoding="utf-8")
        except OSError:
            return _fail(f"Could not write log file: {log_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
