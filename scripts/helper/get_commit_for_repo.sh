#!/usr/bin/env bash

# -------------------------------------------------------
# get_commit_for_repo.sh 
# Finds matching commit for target date in a repository
# -------------------------------------------------------

# Usage: get_commit_for_repo.sh <repo_path> <date>
set -e

repo="$1"
date="$2"

# Fetch full remote history (fixes shallow and detached-head issues)
git -C "$repo" fetch --prune --quiet

# Determine remote default branch (origin/HEAD → origin/main/master)
remote_ref=$(git -C "$repo" symbolic-ref --quiet refs/remotes/origin/HEAD 2>/dev/null \
             | sed 's|^refs/remotes/||')
# Fallbacks
if [[ -z "${remote_ref:-}" ]]; then
  if git -C "$repo" rev-parse --verify --quiet origin/main; then
    remote_ref="origin/main"
  else
    remote_ref="origin/master"
  fi
fi

# Commit at/before target date (correct even on detached HEAD)
git -C "$repo" rev-list -1 --before="$date 23:59:59" "$remote_ref"