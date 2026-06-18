#!/usr/bin/env python3

# ------------------------------------------------------------------
# install_models.py
# Download models / LoRAs from HuggingFace or CivitAI into ComfyUI
# ------------------------------------------------------------------

import os, sys, yaml, requests, time


# --- Logging ---
def log(msg):
    print(f"[COMFY AUTO SETUP] {msg}")


# --- Skip filter (pure, no I/O) ---
# SKIP_MODELS holds keyword groups: ';' separates groups, ',' separates keywords
# within a group. A model is skipped when its URL/filename contains ALL keywords
# of ANY group (case-insensitive substring). Empty/unset = skip nothing.
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


# Sentinel returned by download() when a file was filtered out (not an error).
FILTERED = object()


# --- Helper: download with filename auto-detection and progress info ---
def download(url, dst_dir, headers, skip_groups=(), retries=3, step_percent=10):
    is_tty = sys.stdout.isatty() # runpod can not re-render lines to update progress
    for attempt in range(1, retries + 1):
        try:
            with requests.get(url, headers=headers, stream=True, timeout=60, allow_redirects=True) as r:
                r.raise_for_status()

                # --- Filename extraction from Content-Disposition ---
                cd = r.headers.get("Content-Disposition", "")
                if "filename=" in cd:
                    fname = cd.split("filename=")[-1].strip().strip('"').rstrip(';').strip('"')
                else:
                    fname = os.path.basename(r.url.split("?")[0])

                # Skip filter on the resolved filename (covers CivitAI, whose URL is
                # only a numeric id) — abort before downloading the body.
                if matches_skip(fname, skip_groups):
                    log(f"SKIP (filter) - {fname}")
                    return FILTERED

                dst_path = os.path.join(dst_dir, fname)
                if os.path.exists(dst_path):
                    log(f"SKIP - {fname} already exists")
                    return dst_path

                # --- Progress bar setup ---
                total = int(r.headers.get("Content-Length", 0))
                downloaded = 0
                chunk_size = 8192
                bar_width = 100
                next_step = step_percent

                log(f"DOWN - {fname}")

                with open(dst_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=chunk_size):
                        if not chunk:
                            continue
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total > 0:
                            percent = downloaded * 100 // total
                            done = int(bar_width * downloaded / total)

                            if is_tty:
                                # single-line progress bar for real terminals
                                sys.stdout.write(f"\r[{'#'*done}{'.'*(bar_width-done)}] {percent}%")
                                sys.stdout.flush()
                            else:
                                # RunPod-safe stepped logging
                                if percent >= next_step:
                                    sys.stdout.write(f"[{'#'*done}{'.'*(bar_width-done)}] {percent}%\n")
                                    sys.stdout.flush()
                                    next_step += step_percent
                if total > 0:
                    sys.stdout.write("\n")
                else:
                    log("  Done (size unknown)")
            return dst_path
        except Exception as e:
            log(f"Download failed ({attempt}/{retries}): {e}")
            time.sleep(2)
    return None


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

    # --- Resolve skip filter (exported by lib_common.sh) ---
    skip_groups = parse_skip_groups(os.environ.get("SKIP_MODELS", ""))
    if skip_groups:
        log(f"Model skip filter active: {skip_groups}")

    # --- Process folders ---
    for folder in cfg.get("folders", []):
        src = folder.get("source", "").lower()
        key = api_keys.get(src, "")
        headers = {"Authorization": f"Bearer {key}"} if key else {}
        target_dir = os.path.join(install_dir, folder["target"])
        os.makedirs(target_dir, exist_ok=True)

        if src == "huggingface":
            if folder.get("urls"):
                for url in folder.get("urls", []):
                    fname = os.path.basename(url)
                    # Skip filter on the full URL (includes the filename for HF) —
                    # skipped before any network request.
                    if matches_skip(url, skip_groups):
                        log(f"SKIP (filter) - {fname}")
                        continue
                    path = os.path.join(target_dir, fname)
                    if os.path.exists(path):
                        log(f"SKIP - {fname} already exists")
                        continue
                    download(url, target_dir, headers, skip_groups)

        elif src == "civitai":
            base = "https://civitai.com/api/download/models/"
            if folder.get("ids"):
                for _id in folder.get("ids", []):
                    url = f"{base}{_id}"
                    out = download(url, target_dir, headers, skip_groups)
                    if out is None:
                        log(f"Failed CivitAI download for ID {_id}")

        else:
            log(f"Unknown source '{src}' → skipped")


if __name__ == "__main__":
    main()
