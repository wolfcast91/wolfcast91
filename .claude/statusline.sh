#!/usr/bin/env bash
# Claude Code statusline: Berlin clock + model + dir + git branch.
# Receives session JSON on stdin.

input=$(cat)

read -r model cwd <<<"$(printf '%s' "$input" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    d = {}
model = d.get("model", {}).get("display_name", "") or "-"
cwd = d.get("workspace", {}).get("current_dir", "") or d.get("cwd", "") or "-"
print(model.replace(" ", " "), cwd)
' 2>/dev/null)"

[ -z "$cwd" ] || [ "$cwd" = "-" ] && cwd=$PWD
dir=$(basename "$cwd")

clock=$(TZ=Europe/Berlin date '+%H:%M')
day=$(TZ=Europe/Berlin date '+%a %d %b')

branch=$(git -C "$cwd" rev-parse --abbrev-ref HEAD 2>/dev/null)

out="🕐 ${clock} · ${day}"
[ -n "$model" ] && [ "$model" != "-" ] && out="${out} │ ${model//$' '/ }"
out="${out} │ 📁 ${dir}"
[ -n "$branch" ] && out="${out} │ ⎇ ${branch}"

printf '%s' "$out"
