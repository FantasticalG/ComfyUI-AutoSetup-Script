#!/usr/bin/env bash

# ----------------------------------------------------
# install_all.sh 
# Installs ComfyUI, Extensions, Resources and Models
# ----------------------------------------------------

set -e
source "$(dirname "$0")/helper/lib_common.sh"

log "TARGET DATE: $SETUP_DATE"
log "INSTALL DIR: $INSTALL_DIR"

log "=== STEP 1: ComfyUI Base Setup ==="
bash "$REPO_ROOT/scripts/install_comfy.sh"
bash "$REPO_ROOT/scripts/install_ext.sh"
log "=== Base setup complete ==="

log "=== STEP 2: Deploy Resources ==="
bash "$REPO_ROOT/scripts/install_resources.sh"
log "=== Resource deployment complete ==="

log "=== STEP 3: Download Models ==="
bash "$REPO_ROOT/scripts/install_models.sh"
log "=== Model download complete ==="

log "=== INSTALL COMPLETE ==="
