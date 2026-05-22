#!/usr/bin/env bash

# ----------------------------------------------------------
# install_models.sh 
# Downloads ComfyUI models based on config/models.yaml
# ----------------------------------------------------------

set -e
source "$(dirname "$0")/helper/lib_common.sh"
ensure_python

CONFIG_FILE="$REPO_ROOT/config/models.yaml"
LOCAL_KEYS_FILE="$REPO_ROOT/local/local_keys.yaml"

log "Installing models"

# Run Python model downloader
python3 "$REPO_ROOT/scripts/helper/install_models.py" "$CONFIG_FILE" "$INSTALL_DIR" "$HF_KEY" "$CIVITAI_KEY" "$LOCAL_KEYS_FILE"

log "All model downloads processed."
