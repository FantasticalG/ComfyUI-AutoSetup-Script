#!/usr/bin/env python3

# ------------------------------------------------------------------
# install_models.py
# Download models / LoRAs from HuggingFace or CivitAI into ComfyUI.
# Orchestration only — the robust download mechanism lives in downloader.py.
# ------------------------------------------------------------------

import os, sys, yaml

from downloader import download_file


# --- Logging ---
def log(msg):
    print(f"[COMFY AUTO SETUP] {msg}")


# --- Skip filters (pure, no I/O) ---
# SKIP_MODEL_FILES holds keyword groups: ';' separates groups, ',' separates
# keywords within a group. A model is skipped when its URL/filename contains ALL
# keywords of ANY group (case-insensitive substring). Empty/unset = skip nothing.
def parse_skip_groups(spec):
    groups = []
    for group in (spec or "").split(";"):
        words = [w.strip().lower() for w in group.split(",") if w.strip()]
        if words:  # drop empty groups so a stray ';' never matches everything
            groups.append(words)
    return groups


def matches_skip(text, groups):
    t = (text or "").lower()
    return any(all(word in t for word in group) for group in groups)


# SKIP_MODEL_DIRS holds folder names separated by ';'. A whole folder entry is
# skipped when the final segment of its target path equals any name (case-
# insensitive). Empty/unset = skip nothing.
def parse_dir_filters(spec):
    return {w.strip().lower() for w in (spec or "").split(";") if w.strip()}


def dir_skipped(target, dir_filters):
    return os.path.basename((target or "").rstrip("/")).lower() in dir_filters


def main():
    # --- Args ---
    if len(sys.argv) < 6:
        print("Usage: install_models.py <config.yaml> <install_dir> <hf_key> <civitai_key> <local_keys.yaml>")
        sys.exit(1)

    config_file, install_dir, hf_key, civitai_key, local_key_file = sys.argv[1:6]

    # --- Load config + optional local key file ---
    with open(config_file) as f:
        cfg = yaml.safe_load(f)
    local_keys = yaml.safe_load(open(local_key_file)) if os.path.exists(local_key_file) else {}

    # --- Resolve API keys ---
    api_keys = {
        "huggingface": hf_key or local_keys.get("huggingface", "") or "",
        "civitai": civitai_key or local_keys.get("civitai", "") or ""
    }

    # --- Resolve skip filters (exported by lib_common.sh) ---
    file_groups = parse_skip_groups(os.environ.get("SKIP_MODEL_FILES", ""))
    dir_filters = parse_dir_filters(os.environ.get("SKIP_MODEL_DIRS", ""))
    if file_groups:
        log(f"Skip-file filter active: {file_groups}")
    if dir_filters:
        log(f"Skip-dir filter active: {sorted(dir_filters)}")

    def should_skip(name):
        return matches_skip(name, file_groups)

    failed = []  # names that could not be downloaded after all retries

    # --- Process folders ---
    for folder in cfg.get("folders", []):
        target = folder["target"]
        # Folder-level skip: drop the whole entry if its final folder name matches.
        if dir_skipped(target, dir_filters):
            log(f"SKIP (dir) - {target}")
            continue
        src = folder.get("source", "").lower()
        key = api_keys.get(src, "")
        headers = {"Authorization": f"Bearer {key}"} if key else {}
        target_dir = os.path.join(install_dir, target)
        os.makedirs(target_dir, exist_ok=True)

        if src == "huggingface":
            for url in folder.get("urls") or []:
                fname = os.path.basename(url)
                # Filter on the full URL (includes the filename for HF) before any request.
                if matches_skip(url, file_groups):
                    log(f"SKIP (filter) - {fname}")
                    continue
                # Cheap local check so re-runs don't even probe the network.
                if os.path.exists(os.path.join(target_dir, fname)):
                    log(f"SKIP - {fname} already exists")
                    continue
                result = download_file(url, target_dir, headers, should_skip, log=log)
                if result.status == "failed":
                    failed.append(result.name)

        elif src == "civitai":
            base = "https://civitai.com/api/download/models/"
            for _id in folder.get("ids") or []:
                url = f"{base}{_id}"
                result = download_file(url, target_dir, headers, should_skip, log=log)
                if result.status == "failed":
                    failed.append(result.name or f"CivitAI ID {_id}")

        else:
            log(f"Unknown source '{src}' → skipped")

    # --- Summary of failures (non-fatal; mirrors the extensions summary) ---
    if failed:
        log(f"Models that FAILED to download ({len(failed)}):")
        for name in failed:
            log(f"  - {name}")


if __name__ == "__main__":
    main()
