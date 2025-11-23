#!/usr/bin/env bash

# -------------------------------------------------------
# get_commit_for_repo.sh 
# Finds matching commit for target date in a repository
# -------------------------------------------------------

# Usage: get_commit_for_repo.sh <repo_path> <date>
set -e

repo="$1"; date="$2"
git -C "$repo" fetch --all --quiet
git -C "$repo" rev-list -1 --before="$date 23:59:59" HEAD || true
