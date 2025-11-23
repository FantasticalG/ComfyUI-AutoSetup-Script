#!/usr/bin/env python3

# --------------------------------------------------------------
# install_models.py
# Merge/copy or symlink resource folders into target directory
# --------------------------------------------------------------

import os, shutil, yaml, sys

# --- Args ---
if len(sys.argv) < 4:
    print("Usage: install_resources.py <config.yaml> <setup_repo_root> <install_dir>")
    sys.exit(1)

config_file, root, target_root = sys.argv[1:4]

with open(config_file) as f:
    data = yaml.safe_load(f)

# --- Process folders ---
for item in data.get("folders", []):
    src_dir = os.path.join(root, item["source"])
    dst_dir = os.path.join(target_root, item["target"])
    mode = item.get("mode", "copy")

    print(f"[COMFY AUTO SETUP] {mode.capitalize()} {src_dir} → {dst_dir}")

    if mode == "symlink":
        # ensure parent of target exists
        os.makedirs(os.path.dirname(dst_dir), exist_ok=True)

         # remove existing target if exists
        if os.path.exists(dst_dir) or os.path.islink(dst_dir):
            if os.path.isdir(dst_dir) and not os.path.islink(dst_dir):
                shutil.rmtree(dst_dir)
            else:
                os.remove(dst_dir)

        # create folder-level symlink
        os.symlink(os.path.abspath(src_dir), dst_dir)
    else:
        # Copy individual files recursively
        for subdir, _, files in os.walk(src_dir):
            rel = os.path.relpath(subdir, src_dir)
            dst_sub = os.path.join(dst_dir, rel)
            os.makedirs(dst_sub, exist_ok=True)
            for f in files:
                print(f"[COMFY AUTO SETUP]  - Copy {f}")
                shutil.copy2(os.path.join(subdir, f), os.path.join(dst_sub, f))
