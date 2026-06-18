#!/usr/bin/env bash

# -----------------------------------------------------------
# lib_common.sh 
# Shared library for env setup, parameter handling, helpers
# -----------------------------------------------------------

# pipefail so a failing command in a pipe (e.g. `pip install ... | awk`)
# is not masked by the exit status of the last pipe stage.
set -eo pipefail

# Helper function for logging
log() { echo -e "[COMFY AUTO SETUP] $*"; }

# Root path of setup repo
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Setup reference date (can be overwritten with TARGET_DATE) 
# Default uses date of last commit in setup repo
COMMIT_DATE=$(git -C "$REPO_ROOT" log -1 --format=%ci | cut -d' ' -f1)
SETUP_DATE="${TARGET_DATE:-$COMMIT_DATE}" 

# Installation directory (can be overridden with COMFY_DIR)
INSTALL_DIR="${COMFY_DIR:-$PWD/ComfyUI}"

# Api Keys (can be overriden with HUGGINGFACE_API_KEY and CIVITAI_API_KEY)
HF_KEY="${HUGGINGFACE_API_KEY:-}"
CIVITAI_KEY="${CIVITAI_API_KEY:-}"

# Optional model-download skip filters (see docs/configuration.md):
#   SKIP_MODEL_FILES — skip individual models by URL/filename
#   SKIP_MODEL_DIRS  — skip whole target folders by their final folder name
SKIP_MODEL_FILES="${SKIP_MODEL_FILES:-}"
SKIP_MODEL_DIRS="${SKIP_MODEL_DIRS:-}"

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --comfy-dir) INSTALL_DIR="$2"; shift ;;
    --date) SETUP_DATE="$2"; shift ;;
    --hf-key) HF_KEY="$2"; shift ;;
    --civitai-key) CIVITAI_KEY="$2"; shift ;;
    --skip-model-files) SKIP_MODEL_FILES="$2"; shift ;;
    --skip-model-dirs) SKIP_MODEL_DIRS="$2"; shift ;;
  esac
  shift
done

# Re-export the resolved values as the canonical env vars. install_all.sh
# launches the step scripts as separate `bash` processes that re-source this
# file, so without exporting these the children would fall back to defaults and
# silently drop any CLI flags (--comfy-dir, --date, --hf-key, --civitai-key).
export COMFY_DIR="$INSTALL_DIR"
export TARGET_DATE="$SETUP_DATE"
export HUGGINGFACE_API_KEY="$HF_KEY"
export CIVITAI_API_KEY="$CIVITAI_KEY"
export SKIP_MODEL_FILES="$SKIP_MODEL_FILES"
export SKIP_MODEL_DIRS="$SKIP_MODEL_DIRS"

# Dependency checks (base system expected to have git/python preinstalled)
ensure_git() { command -v git >/dev/null || { log "git missing"; exit 1; }; }
ensure_python() { command -v python3 >/dev/null || { log "python3 missing"; exit 1; }; }

# Clone a repo if needed, then check out the commit matching the given date.
# Echoes the resolved commit hash on stdout; all other output goes to stderr so
# callers can capture the hash with:  commit=$(clone_or_checkout url dir date)
#
# SAFETY: this function never deletes anything. If the target exists but is not a
# git repository AND is not empty, it ABORTS instead of removing it.
# Usage: clone_or_checkout <git-url> <target-dir> <date>
clone_or_checkout() {
  local url="$1" target="$2" date="$3" commit

  if [[ -z "$target" ]]; then
    log "clone_or_checkout: empty target path — refusing." >&2
    return 1
  fi

  # Clone only when there is no git repo there yet.
  if [[ ! -d "$target/.git" ]]; then
    # Never touch a populated, non-git directory — abort loudly instead.
    if [[ -d "$target" && -n "$(ls -A "$target" 2>/dev/null)" ]]; then
      log "ERROR: '$target' exists, is not a git repository, and is not empty." >&2
      log "       Refusing to modify it. If it is a stale/partial clone, remove it" >&2
      log "       manually and re-run. (No files were deleted.)" >&2
      return 1
    fi
    # Safe: target is missing or an empty dir, which 'git clone' handles.
    git clone "$url" "$target" >&2
  fi

  # Check out the commit matching the setup date.
  commit=$(bash "$REPO_ROOT/scripts/helper/get_commit_for_repo.sh" "$target" "$date")
  if [[ -z "$commit" ]]; then
    log "ERROR: no commit found at/before $date for $target" >&2
    return 1
  fi
  git -C "$target" -c advice.detachedHead=false checkout "$commit" >&2

  echo "$commit"
}

# Run `pip install`, dropping noisy "already satisfied" lines and sending all
# output to stderr. With pipefail (set above) a pip failure still propagates.
# Usage: pip_install_quiet <pip-install-args...>
pip_install_quiet() {
  python3 -m pip install "$@" 2>&1 | awk '!/already satisfied/' >&2
}
