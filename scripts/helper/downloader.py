#!/usr/bin/env python3

# ------------------------------------------------------------------
# downloader.py
# Robust single-file downloader: resumes interrupted transfers, writes
# to a .part temp file and only atomically renames it into place once the
# full, size-verified content has arrived. Never leaves a broken file behind.
# ------------------------------------------------------------------

import os
import time
from collections import namedtuple

import requests

# status: "ok" | "skipped" | "filtered" | "failed"
DownloadResult = namedtuple("DownloadResult", "status path name")

CHUNK_SIZE = 8192
BAR_WIDTH = 100
TIMEOUT = (10, 60)  # (connect, read) — a read stall triggers a resume, not a hang


def _resolve_filename(resp, url):
    """Filename from Content-Disposition, else the URL basename."""
    cd = resp.headers.get("Content-Disposition", "")
    if "filename=" in cd:
        return cd.split("filename=")[-1].strip().strip('"').rstrip(";").strip('"')
    return os.path.basename(resp.url.split("?")[0]) or os.path.basename(url.split("?")[0])


def _render_progress(downloaded, total, is_tty, state):
    """Single-line bar on a TTY; stepped percentage lines otherwise (RunPod-safe)."""
    if total <= 0:
        return
    percent = downloaded * 100 // total
    done = int(BAR_WIDTH * downloaded / total)
    bar = f"[{'#' * done}{'.' * (BAR_WIDTH - done)}] {percent}%"
    if is_tty:
        print(f"\r{bar}", end="", flush=True)
    elif percent >= state["next_step"]:
        print(bar, flush=True)
        state["next_step"] += state["step"]


def _stream_to_part(resp, part_path, mode, offset, total, is_tty, log):
    """Write the response body into part_path, reporting progress from `offset`."""
    downloaded = offset
    state = {"next_step": 10, "step": 10}
    with open(part_path, mode) as f:
        for chunk in resp.iter_content(chunk_size=CHUNK_SIZE):
            if not chunk:
                continue
            f.write(chunk)
            downloaded += len(chunk)
            _render_progress(downloaded, total, is_tty, state)
    if total > 0 and is_tty:
        print()  # end the progress line
    elif total <= 0:
        log("  Done (size unknown)")


def download_file(url, dest_dir, headers, should_skip=None, retries=3, log=print):
    """Download `url` into `dest_dir`, resuming and verifying. Returns a DownloadResult."""
    import sys
    is_tty = sys.stdout.isatty()

    # --- Header probe: resolve filename / total size / range support up front ---
    try:
        with requests.get(url, headers=headers, stream=True, timeout=TIMEOUT,
                          allow_redirects=True) as r:
            r.raise_for_status()
            fname = _resolve_filename(r, url)
            total = int(r.headers.get("Content-Length", 0))
            accept_ranges = r.headers.get("Accept-Ranges", "").lower() == "bytes"
    except Exception as e:
        log(f"Download failed (probe): {e}")
        return DownloadResult("failed", None, os.path.basename(url.split("?")[0]) or url)

    if should_skip and should_skip(fname):
        log(f"SKIP (filter) - {fname}")
        return DownloadResult("filtered", None, fname)

    dst_path = os.path.join(dest_dir, fname)
    part_path = dst_path + ".part"

    if os.path.exists(dst_path):
        log(f"SKIP - {fname} already exists")
        return DownloadResult("skipped", dst_path, fname)

    for attempt in range(1, retries + 1):
        try:
            existing = os.path.getsize(part_path) if os.path.exists(part_path) else 0
            req_headers = dict(headers)
            mode = "wb"
            if existing and accept_ranges:
                req_headers["Range"] = f"bytes={existing}-"
                mode = "ab"
            elif existing:
                existing = 0  # cannot resume → restart from scratch

            with requests.get(url, headers=req_headers, stream=True, timeout=TIMEOUT,
                              allow_redirects=True) as r:
                r.raise_for_status()
                if mode == "ab" and r.status_code != 206:
                    # server ignored the Range request → restart cleanly
                    existing, mode = 0, "wb"
                log(f"{'RESUME' if mode == 'ab' else 'DOWN'} - {fname}")
                _stream_to_part(r, part_path, mode, existing, total, is_tty, log)

            # Verify completeness before finalizing
            got = os.path.getsize(part_path)
            if total and got != total:
                raise IOError(f"incomplete download: {got}/{total} bytes")

            os.replace(part_path, dst_path)  # atomic: final path appears only when complete
            return DownloadResult("ok", dst_path, fname)
        except Exception as e:
            log(f"Download failed ({attempt}/{retries}): {e}")
            time.sleep(2)

    # All retries exhausted → leave no broken file behind
    if os.path.exists(part_path):
        try:
            os.remove(part_path)
        except OSError:
            pass
    return DownloadResult("failed", None, fname)
