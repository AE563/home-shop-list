#!/bin/bash
# Auto-lint after Claude edits a file.
# Runs ruff on .py files, eslint on .js files.

DATA=$(cat)
FILE=$(echo "$DATA" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('file_path', ''))
except Exception:
    print('')
" 2>/dev/null)

[[ -z "$FILE" ]] && exit 0

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

if [[ "$FILE" == *.py ]]; then
    "$ROOT/.venv2/bin/ruff" check "$FILE" --fix -q 2>/dev/null || true
    "$ROOT/.venv2/bin/ruff" format "$FILE" -q 2>/dev/null || true
elif [[ "$FILE" == *.js ]] && [[ "$FILE" != *node_modules* ]] && [[ "$FILE" != *coverage* ]]; then
    cd "$ROOT" && npx eslint "$FILE" --fix --quiet 2>/dev/null || true
fi

exit 0
