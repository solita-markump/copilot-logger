# Copilot Logger

Automatically saves Copilot chat transcripts as readable logs that get committed alongside your code. The main purpose is to make code reviews easier so reviewers can see exactly which prompts led to which code changes. Logs are organized by user email.

## File Structure

```
copilot-logger/
├── .github/
│   └── hooks/
│       ├── copilot-logger-cli.json      # Hook config for Copilot CLI
│       ├── copilot-logger-vscode.json   # Hook config for Copilot in VS Code (empty/WIP)
│       └── scripts/
│           └── logger.ps1               # PowerShell script that parses transcripts into logs
├── copilot-logs/                        # Output directory for generated log files
│   └── <user-email>/                    # Subdirectory per git user email
│       └── <date>_<session-id>.log      # One log file per session
└── README.md
```

## Installation

1. Copy the `.github/hooks/` folder (including `scripts/`) into your target project's `.github/` directory.
2. Create an empty `copilot-logs/` directory in your project root.
3. Commit both to your repo.

Copilot CLI automatically picks up the hooks when it finds `.github/hooks/copilot-logger-cli.json` in the repo.

**Note:** The hooks only take effect when you start a new chat session. Any session that was already running before installation will not produce logs.

## How It Works

1. When a Copilot CLI agent or sub-agent finishes (`agentStop` / `subagentStop`), the hook fires `logger.ps1`.
2. The script receives the session ID and transcript path from Copilot via stdin (JSON).
3. It parses the transcript for `user.message` events and `ask_user` tool interactions, extracting timestamps and content.
4. It writes a log file to `copilot-logs/<git-user-email>/<date>_<session-short-id>.log`.

## Log Format

Logs are plain text with timestamped entries:

```
2026-02-25T10:00:00Z [User]
How do I add authentication?

2026-02-25T10:00:05Z [Agent]
What auth strategy should I use?
Choices: JWT, Session-based, OAuth

2026-02-25T10:00:10Z [User]
JWT
```

## Requirements

- **PowerShell** (ships with Windows; available on macOS/Linux via [PowerShell Core](https://github.com/PowerShell/PowerShell))
- **Git** (used to determine `user.email` for log directory naming)
- **GitHub Copilot CLI** with hooks support
