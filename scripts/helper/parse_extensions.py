#!/usr/bin/env python3

# --------------------------------------------------------
# parse_extensions.py
# Reads extensions.yaml and prints Git URLs line-by-line
# --------------------------------------------------------

import yaml
import sys
from pathlib import Path

# --- Args ---
config_path = Path(sys.argv[1]).resolve()

with open(config_path, "r") as f:
    data = yaml.safe_load(f)

# --- Print extension URLs ---
exts = data.get("extensions", [])
for ext in exts:
    url = ext.get("url")
    if url:
        print(url)
