# Copilot Logger

Automatically saves Copilot chat transcripts as readable logs that get committed alongside your code. The main purpose is to make code reviews easier so reviewers can see exactly which prompts led to which code changes. Logs are organized by user email.

## File Structure

```
copilot-logger/
├── .github/
│   └── hooks/
│       ├── copilot-logger-cli.json      # Hook config for Copilot CLI
│       └── copilot-logger/
│           ├── logger.py                # Python script that parses transcripts into logs
│           ├── run.ps1                  # PowerShell entry point (Windows)
│           └── run.sh                   # Bash entry point (Linux/macOS)
├── copilot-logs/                        # Output directory for generated log files
│   └── <user-email>/                    # Subdirectory per git user email
│       └── <date>_<session-id>.log      # One log file per session
└── README.md
```

## Installation

1. Ensure Python is installed and available as `python` or `python3` on your PATH.
2. Copy the `.github/hooks/` folder (including `copilot-logger/`) into your target project's `.github/` directory.
3. Commit to your repo.

Copilot CLI automatically picks up the hooks when it finds `.github/hooks/copilot-logger-cli.json` in the repo.

**Note:** The hooks only take effect when you start a new chat session. Any session that was already running before installation will not produce logs.

## How It Works

1. When a Copilot CLI agent or sub-agent finishes (`agentStop` / `subagentStop`), the hook fires and invokes `logger.py`.
2. The script receives the session ID and transcript path from Copilot via stdin (JSON).
3. It parses the transcript for `user.message` events and `ask_user` tool interactions, extracting timestamps and content.
4. It writes a log file to `copilot-logs/<git-user-email>/<date>_<session-short-id>.log`.

## Log Format

Logs are plain text with timestamped entries:

```
2026-02-25T12:52:35.042Z [User]
Analyze the codebase. Is there any refactoring we can do?

2026-02-25T12:54:18.521Z [Agent]
Which refactoring focus should be first when we move to implementation?
Choices:
  - Parser tests + parser modularization (Recommended)
  - Runner script deduplication first
  - Balanced pass across both areas

2026-02-25T12:55:39.641Z [User]
User selected: Parser tests + parser modularization (Recommended)
```

## VS Code Support

VS Code support is not yet available. Copilot hooks are currently disabled in VS Code due to organization-level restrictions. Once those restrictions are lifted, VS Code support will be added.
