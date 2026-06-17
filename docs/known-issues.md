# Known Issues & Roadmap

A tracking list of known limitations, rough edges, and planned improvements across the
[setup script](https://github.com/FantasticalG/ComfyUI-AutoSetup-Script) and the
[RunPod container](https://github.com/FantasticalG/ComfyUI-AutoSetup-RunPod-Container).

Items are grouped by area and roughly ordered by impact. **Fixed** items are kept for context.

---

## Reliability / correctness

### ✅ CLI flags ignored by `install_all.sh` — *fixed*
Previously, flags like `--comfy-dir` / `--date` passed to `install_all.sh` were parsed only for
the orchestrator and not propagated to the step scripts (which run as separate `bash` processes
and re-derived defaults). Fixed by exporting the resolved values as canonical env vars
(`COMFY_DIR`, `TARGET_DATE`, …) in [lib_common.sh](../scripts/helper/lib_common.sh).

### ✅ Failed `pip install` masked by log filter — *fixed*
The `pip install ... | awk '!/already satisfied/'` pattern hid pip's exit status (no `pipefail`),
so dependency-install failures were swallowed and the script still reported success. Fixed by
adding `set -o pipefail` in [lib_common.sh](../scripts/helper/lib_common.sh).

### Interrupted downloads corrupt silently and are never re-fetched
[install_models.py](../scripts/helper/install_models.py) writes directly to the final file and
skips downloads based purely on **file existence**. If a download is interrupted (network drop,
container OOM/kill — common on RunPod with multi-GB files), the partial file remains and is
treated as complete on every later run.
- **Planned fix:** download to a `.part` temp file, validate size against `Content-Length`, then
  rename on success. Optionally support resume via HTTP `Range`.
- **Workaround:** if a model misbehaves, delete the file in its target folder and re-run
  `install_models.sh` to force a fresh download.

### No checksum / integrity verification
Even a complete download isn't validated against a known hash. Low priority, but worth adding
optional `sha256` checks for critical models.

---

## Reproducibility

### "Deterministic" only covers git checkouts, not the Python dependency tree
The date mechanism pins ComfyUI and extension **commits**, but `pip install -r requirements.txt`
resolves whatever versions satisfy the (often unpinned) requirements at install time — including
`torch`, `numpy`, etc. Rebuilding the same `--date` later can still yield a different environment.
- **Planned:** pin/lock Python dependencies (lockfile or pinned wheels) for true reproducibility.

### The "version" is a commit *date*, decoupled from content
Default `SETUP_DATE` = date of the latest commit in this repo. Any commit (even docs-only)
advances the date, which on the next install can roll ComfyUI and every extension *forward* to
whatever upstream shipped by that date.
- **Workaround:** pin an explicit `TARGET_DATE` / `--date` for a stable, known-good build.

### flash-attn wheel pinned to a torch version that torch isn't pinned to
In the container [Dockerfile](https://github.com/FantasticalG/ComfyUI-AutoSetup-RunPod-Container/blob/main/Dockerfile),
`torch` is installed unpinned from the cu130 index, but the prebuilt flash-attn wheel targets a
specific torch ABI (`…+cu130torch2.10…`). When the index ships a newer torch, the ABI mismatches
and `flash_attn` import breaks.
- **Planned fix:** pin `torch`/`torchvision`/`torchaudio` to the version the flash-attn wheel was
  built against.

---

## Security

### Open, unauthenticated services (documented)
JupyterLab runs with no token/password and `allow_origin='*'`; both Jupyter (8888) and ComfyUI
(8188) bind `0.0.0.0`. Reaching 8888 = arbitrary code execution on the host. Safe only behind
RunPod's authenticated proxy or a trusted network. This is now called out in the container
[README](https://github.com/FantasticalG/ComfyUI-AutoSetup-RunPod-Container#accessing-the-services).
- **Planned:** default to a generated Jupyter token (overridable), and document binding to
  loopback for local use.

### API keys passed via argv
[install_models.sh](../scripts/install_models.sh) passes the HuggingFace/CivitAI tokens as
command-line arguments to the Python helper, so they can appear in process listings (`ps`).
- **Planned fix:** pass secrets via environment variables or stdin instead of argv.

---

## Maintainability / smaller items

- **Stale extensions are never pruned.** [install_ext.sh](../scripts/install_ext.sh) only adds/
  updates. Removing an entry from `extensions.yaml` leaves the cloned node in `custom_nodes/`
  (and it keeps loading). A prune step (or "managed by setup" manifest) would help.
- **`git fetch --prune` runs for every repo on every run**
  ([get_commit_for_repo.sh](../scripts/helper/get_commit_for_repo.sh)) — requires network even when
  already on the correct commit and is slow across many extensions.
- **Downloads are fully sequential.** Parallelizing model downloads would cut first-boot time
  significantly.
- **`install_models.py` arg check is off.** It guards `len(sys.argv) < 3` but unpacks
  `sys.argv[1:6]` (needs 5), so a partial invocation raises `ValueError` instead of printing the
  usage message. Latent — the shell wrapper always passes 5.
- **Workflows symlink to `/opt/setup`** (ephemeral, re-cloned each boot) rather than the persistent
  volume. Works today because the entrypoint always re-clones, but fragile if that assumption
  changes.
- **`docker-compose.yaml` uses obsolete `version: "3.9"`** — ignored with a warning by modern
  Compose; can be removed.
