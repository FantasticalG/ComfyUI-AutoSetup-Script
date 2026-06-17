#!/usr/bin/env bash

# --------------------------------------------------------------
# install_ext.sh 
# Installs ComfyUI extensions based on config/extensions.yaml
# --------------------------------------------------------------

set -e
source "$(dirname "$0")/helper/lib_common.sh"

EXT_DIR="$INSTALL_DIR/custom_nodes"
mkdir -p "$EXT_DIR"

YAML_FILE="$REPO_ROOT/config/extensions.yaml"

log "Installing extensions"

# Parse YAML → list of URLs
EXT_URLS=$(python3 "$REPO_ROOT/scripts/helper/parse_extensions.py" "$YAML_FILE")

# Process extensions
while IFS= read -r url; do
  [[ -z "$url" ]] && continue

  name=$(basename "$url" .git)
  log "Setting up extension: $name"

  target="$EXT_DIR/$name"

  # Clone/update the extension and check out the commit matching the setup date
  commit=$(clone_or_checkout "$url" "$target" "$SETUP_DATE")

  # Install extension-specific requirements if present
  if [ -f "$target/requirements.txt" ]; then
    pip_install_quiet -r "$target/requirements.txt"
  fi

  log "$name ready @ $commit"

done <<< "$EXT_URLS"

log "All extensions processed."
