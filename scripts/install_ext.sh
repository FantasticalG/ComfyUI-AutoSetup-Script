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

  # Remove partial/broken clone folders
  if [ -d "$target" ] && [ ! -d "$target/.git" ]; then
    log "[COMFYUI AUTO SETUP] Removing incomplete clone at $target"
    rm -rf "$target"
  fi

  # Clone if not checked out yet
  if [ ! -d "$target/.git" ]; then
    git clone "$url" "$target"
  fi

  # Check out target commit based on the setup date
  commit=$(bash "$REPO_ROOT/scripts/helper/get_commit_for_repo.sh" "$target" "$SETUP_DATE")
  git -C "$target" -c advice.detachedHead=false checkout "$commit"

  # Install extension-specific requirements if present
  if [ -f "$target/requirements.txt" ]; then
    {
      python3 -m pip install -r "$target/requirements.txt" 2>&1 \
        | awk '!/already satisfied/' # skip already satisfied warning
    } >&2
  fi

  log "$name ready @ $commit"

done <<< "$EXT_URLS"

log "All extensions processed."
