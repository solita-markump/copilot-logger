#!/usr/bin/env bash

set -uo pipefail

if ! command -v jq >/dev/null 2>&1; then
  exit 0
fi

raw_input="$(cat)"
if ! parsed_input="$(printf '%s' "$raw_input" | jq -c . 2>/dev/null)"; then
  exit 1
fi

session_id="$(printf '%s' "$parsed_input" | jq -r '.sessionId // empty')"
transcript_path="$(printf '%s' "$parsed_input" | jq -r '.transcriptPath // empty')"
if [[ -z "$session_id" || -z "$transcript_path" || ! -f "$transcript_path" ]]; then
  exit 0
fi

email="$(git config --get user.email 2>/dev/null | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
if [[ -z "$email" ]]; then
  exit 0
fi

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "$script_dir/../../.." && pwd)"
log_dir="$repo_root/copilot-logs/$email"
mkdir -p "$log_dir"

date_str="$(date +%Y-%m-%d)"
short_id="${session_id%%-*}"
log_path="$log_dir/${date_str}_${short_id}.log"

if ! entries="$(
  jq -Rrs '
    [split("\n")[] | select(length > 0) | (try fromjson catch empty)] as $events
    | reduce $events[] as $evt (
        {entries: [], pending: {}};
        if $evt.type == "user.message" then
          ($evt.data.content // empty | tostring) as $content
          | if ($content | length) > 0 then
              .entries += [($evt.timestamp | tostring) + " [User]\n" + $content]
            else . end
        elif $evt.type == "tool.execution_start" and ($evt.data.toolName // "") == "ask_user" then
          ($evt.data.toolCallId // empty | tostring) as $id
          | ($evt.data.arguments.question // empty | tostring) as $question
          | ($evt.data.arguments.choices // null) as $choices
          | if ($id | length) > 0 and ($question | length) > 0 then
              ($evt.timestamp | tostring) + " [Agent]\n" + $question
              + (
                  if ($choices | type) == "array" and ($choices | length) > 0
                  then "\nChoices: " + ($choices | map(tostring) | join(", "))
                  else ""
                  end
                ) as $entry
              | .pending[$id] = $entry
            else . end
        elif $evt.type == "tool.execution_complete" then
          ($evt.data.toolCallId // empty | tostring) as $id
          | if ($id | length) > 0 and (.pending | has($id)) then
              .entries += [.pending[$id]]
              | ($evt.data.result.content // empty | tostring) as $answer
              | if ($answer | length) > 0 then
                  .entries += [($evt.timestamp | tostring) + " [User]\n" + $answer]
                else . end
              | .pending |= del(.[$id])
            else . end
        else . end
      )
    | .entries
    | join("\n\n")
  ' "$transcript_path"
)"; then
  exit 0
fi

if [[ -n "$entries" ]]; then
  printf '%s\n' "$entries" > "$log_path"
fi
