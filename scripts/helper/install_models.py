#!/usr/bin/env python3

# ------------------------------------------------------------------
# install_models.py 
# Download models / LoRAs from HuggingFace or CivitAI into ComfyUI
# ------------------------------------------------------------------

import os, sys, yaml, requests, time

# --- Args ---
if len(sys.argv) < 3:
    print("Usage: install_models.py <config.yaml> <install_dir>")
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

# --- Helper: download with filename auto-detection and progress info  ---
def download(url, dst_dir, headers, retries=3, step_percent=10):
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

                dst_path = os.path.join(dst_dir, fname)
                if os.path.exists(dst_path):
                    print(f"[COMFY AUTO SETUP] SKIP - {fname} already exists")
                    return dst_path

                # --- Progress bar setup ---
                total = int(r.headers.get("Content-Length", 0))
                downloaded = 0
                chunk_size = 8192
                bar_width = 100
                next_step = step_percent

                print(f"[COMFY AUTO SETUP] DOWN - {fname}")

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
                    print("[COMFY AUTO SETUP]   Done (size unknown)")
            return dst_path
        except Exception as e:
            print(f"[COMFY AUTO SETUP] Download failed ({attempt}/{retries}): {e}")
            time.sleep(2)
    return None

# --- Process folders ---
for folder in cfg.get("folders", []):
    src = folder.get("source", "").lower()
    key = api_keys.get(src, "")
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    target_dir = os.path.join(install_dir, folder["target"])
    os.makedirs(target_dir, exist_ok=True)

    if src == "huggingface":
        if not folder.get("urls") is None:
            for url in folder.get("urls", []):
                fname = os.path.basename(url)
                path = os.path.join(target_dir, fname)
                if os.path.exists(path):
                    print(f"[COMFY AUTO SETUP] SKIP - {fname} already exists")
                    continue
                download(url, target_dir, headers)

    elif src == "civitai":
        base =  "https://civitai.com/api/download/models/"
        if not folder.get("ids") is None:
            for _id in folder.get("ids", []):
                url = f"{base}{_id}"
                out = download(url, target_dir, headers)
                if not out:
                    print(f"[COMFY AUTO SETUP] Failed CivitAI download for ID {_id}")

    else:
        print(f"[COMFY AUTO SETUP] Unknown source '{src}' → skipped")
