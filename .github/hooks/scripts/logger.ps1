$raw = [Console]::In.ReadToEnd()
$json = $null
try { $json = $raw | ConvertFrom-Json } catch { exit 1 }

$sessionId = $json.sessionId
$transcriptPath = $json.transcriptPath
if (-not $sessionId -or -not $transcriptPath -or -not (Test-Path $transcriptPath)) { exit 0 }

$email = git config --get user.email 2>$null
if (-not $email) { exit 0 }
$email = $email.Trim()
if (-not $email) { exit 0 }

$scriptDir = Split-Path -Parent $PSCommandPath
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path -Path $scriptDir -ChildPath "..\..\.."))
$projectRoot = Join-Path -Path $repoRoot -ChildPath "copilot-logger"
$logDir = Join-Path -Path $projectRoot -ChildPath "logs\$email"
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$logPath = Join-Path -Path $logDir -ChildPath "$sessionId.log"

$lines = Get-Content -Path $transcriptPath -Encoding UTF8
$entries = @()
$pendingAskUser = @{}

foreach ($line in $lines) {
    $line = $line.Trim()
    if (-not $line) { continue }
    $evt = $null
    try { $evt = $line | ConvertFrom-Json } catch { continue }

    if ($evt.type -eq 'user.message') {
        $content = $evt.data.content
        $ts = $evt.timestamp
        if ($content) {
            $entries += "$ts [User]`n$content"
        }
    }
    elseif ($evt.type -eq 'tool.execution_start' -and $evt.data.toolName -eq 'ask_user') {
        $toolCallId = $evt.data.toolCallId
        $question = $evt.data.arguments.question
        $choices = $evt.data.arguments.choices
        if ($toolCallId -and $question) {
            $entry = "$($evt.timestamp) [Agent]`n$question"
            if ($choices -and $choices.Count -gt 0) {
                $entry += "`nChoices: $($choices -join ', ')"
            }
            $pendingAskUser[$toolCallId] = $entry
        }
    }
    elseif ($evt.type -eq 'tool.execution_complete' -and $pendingAskUser.ContainsKey($evt.data.toolCallId)) {
        $toolCallId = $evt.data.toolCallId
        $entries += $pendingAskUser[$toolCallId]
        $answer = $evt.data.result.content
        if ($answer) {
            $entries += "$($evt.timestamp) [User]`n$answer"
        }
        $pendingAskUser.Remove($toolCallId)
    }
}

if ($entries.Count -gt 0) {
    $entries -join "`n`n" | Set-Content -Path $logPath -Encoding UTF8
}
