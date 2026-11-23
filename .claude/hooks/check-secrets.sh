#!/usr/bin/env bash
set -euo pipefail

STAGED_DIFF="$(git diff --cached -- . ':!*.lock' ':!.env.example' 2>/dev/null || true)"
if printf '%s\n' "$STAGED_DIFF" | grep -E '(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|ATATT3x[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,})' >/dev/null 2>&1; then
  echo "BLOCKED: Potential token or secret detected in staged changes." >&2
  exit 2
fi

exit 0
