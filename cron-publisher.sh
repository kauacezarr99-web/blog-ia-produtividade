#!/usr/bin/env bash
# cron-publisher.sh -- writes new article + rebuilds + git commits (push is non-fatal).
# Invoked by the Hermes cron job.
set -euo pipefail

PROJ="/c/Users/User/blog-ia-produtividade"

echo "=== PUBLISHER TICK $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

cd "$PROJ"

# Latest content file (by mtime) for status — skip internal _files
LATEST="$(ls -1t content/*.md 2>/dev/null | grep -v '^_.*\.md' | head -n 1 || true)"
if [ -n "$LATEST" ]; then
  echo "[publisher] latest article: $LATEST"
else
  echo "[publisher] no content files found"
fi

# Build
python build.py

# Git commit (always commit, even if push fails)
git add -A
if git diff --cached --quiet; then
  echo "[publisher] no new files to commit"
else
  git commit -m "publish: new article $(basename "$LATEST" .md)"
fi

# Push (non-fatal: no remote / no creds yet)
BR="$(git rev-parse --abbrev-ref HEAD)"
if git remote get-url origin >/dev/null 2>&1; then
  git pull --rebase origin "$BR" 2>/dev/null || true
  git push origin "$BR" \
    && echo "[publisher] pushed to GitHub Pages" \
    || echo "[publisher] push failed -- local build only, no remote creds yet"
else
  echo "[publisher] no remote set -- skipping push (site built locally in ./public)"
fi

echo "[publisher] DONE"
