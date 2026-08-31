#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"

if [[ -d .git ]]; then
  echo "Git is already initialized."
  git status --short
  exit 0
fi

git init
git config user.name "Himma Repository"
git config user.email "himma-repository@local.invalid"
git add .
git commit -m "chore: establish Himma unified repository baseline"
git branch -M main
git status --short
