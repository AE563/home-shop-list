#!/bin/bash
set -e

REMOTE=landvps
REMOTE_DIR=~/home-shop-list
SKIP_TESTS=false

for arg in "$@"; do
  case $arg in
    --skip-tests) SKIP_TESTS=true ;;
    *) echo "Unknown argument: $arg"; exit 1 ;;
  esac
done

# Warn if uncommitted changes exist — they won't be deployed
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Warning: uncommitted changes detected — deploy will use last commit only"
  echo ""
fi

if [ "$SKIP_TESTS" = false ]; then
  echo "==> Python tests"
  pytest -q --tb=short

  echo ""
  echo "==> JS tests"
  npm test

  echo ""
  echo "==> All tests passed"
  echo ""
fi

echo "==> Push to GitHub"
git push || {
  echo "Nothing to push or push failed — check remote status with: git status"
  exit 1
}

echo ""
echo "==> Deploy to $REMOTE"
ssh $REMOTE "
  cd $REMOTE_DIR &&
  git pull &&
  docker compose -f docker-compose.prod.yml up -d --build &&
  docker image prune -f
"

echo ""
echo "==> Done"
