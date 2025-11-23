#!/usr/bin/env bash

# -----------------------------------------------------------
# lib_common.sh 
# Shared library for env setup, parameter handling, helpers
# -----------------------------------------------------------

set -e

# Helper function for logging
log() { echo -e "[COMFY AUTO SETUP] $*"; }

# Root path of setup repo
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Setup reference date (can be overwritten with TARGET_DATE) 
# Default uses date of last commit in setup repo
COMMIT_DATE=$(git -C "$REPO_ROOT" log -1 --format=%ci | cut -d' ' -f1)
SETUP_DATE="${TARGET_DATE:-$COMMIT_DATE}" 

# Installation directory (can be overridden with COMFY_DIR)
INSTALL_DIR="${COMFY_DIR:-$REPO_ROOT/ComfyUI}"

# Api Keys (can be overriden with HUGGINGFACE_API_KEY and CIVITAI_API_KEY)
HF_KEY="${HUGGINGFACE_API_KEY:-}"
CIVITAI_KEY="${CIVITAI_API_KEY:-}"

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --comfy-dir) INSTALL_DIR="$2"; shift ;;
        --date) SETUP_DATE="$2"; shift ;;
        --hf-key) HF_KEY="$2"; shift ;;
        --civitai-key) CIVITAI_KEY="$2"; shift ;;
    esac
    shift
done

# Dependency checks (base system expected to have git/python preinstalled)
ensure_git() { command -v git >/dev/null || { log "git missing"; exit 1; }; }
ensure_python() { command -v python3 >/dev/null || { log "python3 missing"; exit 1; }; }
