#!/usr/bin/env bash

# --------------------------------------------------------------
# install_resources.sh 
# Deploys ComfyUI resources based on config/resources.yaml
# --------------------------------------------------------------

set -e
source "$(dirname "$0")/helper/lib_common.sh"
ensure_python

CONFIG="$REPO_ROOT/config/resources.yaml"

log "Installing resources"

# Run Python resource deployment
python3 "$REPO_ROOT/scripts/helper/install_resources.py" "$CONFIG" "$REPO_ROOT" "$INSTALL_DIR"

log "All resource folders processed."
