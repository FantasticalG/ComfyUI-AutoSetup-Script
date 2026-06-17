#!/usr/bin/env bash

# ----------------------------------------------------
# install_comfy.sh 
# Clones or updates ComfyUI to match the $SETUP_DATE
# ----------------------------------------------------

set -eo pipefail
source "$(dirname "$0")/helper/lib_common.sh"

ensure_git; ensure_python
COMFY_REPO="https://github.com/Comfy-Org/ComfyUI.git"

log "Installing/Updating ComfyUI..."

# Clone/update ComfyUI and check out the commit matching the setup date
commit=$(clone_or_checkout "$COMFY_REPO" "$INSTALL_DIR" "$SETUP_DATE")

# Update pip + install requirements
pip_install_quiet --upgrade pip
pip_install_quiet -r "$INSTALL_DIR/requirements.txt"

log "ComfyUI ready @ $commit"
