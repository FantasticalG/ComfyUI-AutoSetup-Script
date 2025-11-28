#!/usr/bin/env bash

# ----------------------------------------------------
# install_comfy.sh 
# Clones or updates ComfyUI to match the $SETUP_DATE
# ----------------------------------------------------

set -e
source "$(dirname "$0")/helper/lib_common.sh"

ensure_git; ensure_python
COMFY_REPO="https://github.com/comfyanonymous/ComfyUI.git"

log "Installing/Updating ComfyUI..."

# Remove partial/broken ComfyUI folder
if [ -d "$INSTALL_DIR" ] && [ ! -d "$INSTALL_DIR/.git" ]; then
  log "[COMFYUI AUTO SETUP] Removing incomplete clone at $INSTALL_DIR"
  rm -rf "$INSTALL_DIR"
fi

# Clone if not installed yet
if [ ! -d "$INSTALL_DIR/.git" ]; then
  git clone --depth 1 "$COMFY_REPO" "$INSTALL_DIR"
fi

# Check out target commit based on the setup date
commit=$(bash "$REPO_ROOT/scripts/helper/get_commit_for_repo.sh" "$INSTALL_DIR" "$SETUP_DATE")
git -C "$INSTALL_DIR" -c advice.detachedHead=false checkout "$commit"

# Update pip + install requirements
{
  python3 -m pip install --upgrade pip 2>&1 \
    | awk '!/already satisfied/' # skip already satisfied warning
} >&2
{
  python3 -m pip install -r "$INSTALL_DIR/requirements.txt" 2>&1 \
    | awk '!/already satisfied/' # skip already satisfied warning
} >&2

log "ComfyUI ready @ $commit"
