#!/usr/bin/env bash

# --------------------------------------------------------------
# install_ext.sh 
# Installs ComfyUI extensions based on config/extensions.yaml
# --------------------------------------------------------------

set -eo pipefail
source "$(dirname "$0")/helper/lib_common.sh"

EXT_DIR="$INSTALL_DIR/custom_nodes"
mkdir -p "$EXT_DIR"

YAML_FILE="$REPO_ROOT/config/extensions.yaml"

log "Installing extensions"

# Parse YAML → list of URLs
EXT_URLS=$(python3 "$REPO_ROOT/scripts/helper/parse_extensions.py" "$YAML_FILE")

# Extensions whose requirements failed to install (reported at the end)
FAILED_REQS=()

# Process extensions
while IFS= read -r url; do
  [[ -z "$url" ]] && continue

  name=$(basename "$url" .git)
  log "Setting up extension: $name"

  target="$EXT_DIR/$name"

  # Clone/update the extension and check out the commit matching the setup date
  commit=$(clone_or_checkout "$url" "$target" "$SETUP_DATE")

  # Install extension-specific requirements if present. A failure here is
  # non-fatal: one extension's deps (e.g. CUDA-only packages such as
  # onnxruntime-gpu on macOS) shouldn't abort the whole install. We warn and
  # record it so it's visible, then continue with the next extension.
  if [[ -f "$target/requirements.txt" ]]; then
    if ! pip_install_quiet -r "$target/requirements.txt"; then
      log "WARNING: requirements failed for '$name' — continuing. The node may not work until its dependencies are installed."
      FAILED_REQS+=("$name")
    fi
  fi

  log "$name ready @ $commit"

done <<< "$EXT_URLS"

if [[ "${#FAILED_REQS[@]}" -gt 0 ]]; then
  log "Extensions with FAILED requirements (review the log above): ${FAILED_REQS[*]}"
fi

log "All extensions processed."
