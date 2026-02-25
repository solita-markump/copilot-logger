import json
import sys
from datetime import datetime
from pathlib import Path

USERNAME = "testing"


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


def main():
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return 1

    if not isinstance(payload, dict):
        return 1

    session_id = payload.get("sessionId")
    transcript_path = payload.get("transcriptPath")
    if not session_id or not transcript_path:
        return 0

    transcript_file = Path(str(transcript_path))
    if not transcript_file.exists():
        return 0

    username = USERNAME

    script_dir = Path(__file__).resolve().parent
    repo_root = (script_dir / ".." / ".." / "..").resolve()
    log_dir = repo_root / "copilot-logs" / username
    log_dir.mkdir(parents=True, exist_ok=True)

    date = datetime.now().strftime("%Y-%m-%d")
    short_id = str(session_id).split("-")[0]
    log_path = log_dir / f"{date}_{short_id}.log"

    entries = []
    pending_ask_user = {}

    try:
        lines = transcript_file.read_text(encoding="utf-8").splitlines()
    except OSError:
        return 0

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
        log_path.write_text("\n\n".join(entries), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
