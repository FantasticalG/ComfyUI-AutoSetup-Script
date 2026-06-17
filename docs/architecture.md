# Architecture

This document explains how the setup works internally: the install pipeline, the helper scripts, and the deterministic-versioning design.

## Install pipeline

[install_all.sh](../scripts/install_all.sh) is the orchestrator. It sources the shared library and runs four steps in order:

```
install_all.sh
├── 1a. install_comfy.sh      → clone/update ComfyUI, checkout dated commit, pip install
├── 1b. install_ext.sh        → clone each extension, checkout dated commit, pip install
├── 2.  install_resources.sh  → deploy workflows/resources into ComfyUI
└── 3.  install_models.sh     → download models/LoRAs from HuggingFace + CivitAI
```

Each step script is standalone — it sources [lib_common.sh](../scripts/helper/lib_common.sh) itself and can be run on its own (see the README *Quick start*). This makes targeted updates cheap: e.g. re-run only `install_ext.sh` after editing `extensions.yaml`.

Extensions are installed **before** models on purpose: some model targets live inside an extension's folder (e.g. RIFE checkpoints under `custom_nodes/ComfyUI-Frame-Interpolation/`).

## Shared library — lib_common.sh

[lib_common.sh](../scripts/helper/lib_common.sh) is sourced by every step script. It provides:

- `log()` — prefixed logging (`[COMFY AUTO SETUP] …`).
- `REPO_ROOT` — absolute path to this repo (derived from the script location).
- **Configuration resolution** with this precedence: CLI arguments override environment variables, which override built-in defaults.

| Internal var | CLI arg | Env var | Default |
|--------------|---------|---------|---------|
| `INSTALL_DIR` | `--comfy-dir` | `COMFY_DIR` | `$PWD/ComfyUI` |
| `SETUP_DATE` | `--date` | `TARGET_DATE` | date of the latest commit in **this** repo |
| `HF_KEY` | `--hf-key` | `HUGGINGFACE_API_KEY` | empty |
| `CIVITAI_KEY` | `--civitai-key` | `CIVITAI_API_KEY` | empty |

- `ensure_git()` / `ensure_python()` — fail fast with a clear message if `git` or `python3` is missing.

## Deterministic versioning

ComfyUI and its extensions move fast, and a node update can break a working setup. To keep installs reproducible, every Git repo is pinned to a **date**, not to `HEAD`.

- The active date is `SETUP_DATE` — by default the date of the latest commit in this setup repo, overridable with `--date` / `TARGET_DATE`.
- For each repo, [get_commit_for_repo.sh](../scripts/helper/get_commit_for_repo.sh) resolves that date to a concrete commit:
  1. `git fetch --prune` to get full remote history (handles shallow clones).
  2. Determine the remote default branch (`origin/HEAD`, falling back to `origin/main`, then `origin/master`).
  3. `git rev-list -1 --before="<date> 23:59:59" <branch>` — the last commit on or before the target date.
- The step scripts then check that commit out in detached-HEAD mode.

**Consequence:** committing to this repo (which advances the default `SETUP_DATE`) is what "updates" ComfyUI and the extensions. Pin an explicit `--date 2025-06-15` to rebuild an older, known-good state.

## Helper scripts

| Script | Role |
|--------|------|
| [lib_common.sh](../scripts/helper/lib_common.sh) | Shared env resolution, logging, dependency checks |
| [get_commit_for_repo.sh](../scripts/helper/get_commit_for_repo.sh) | Resolve a date to a commit hash for any repo |
| [parse_extensions.py](../scripts/helper/parse_extensions.py) | Read `extensions.yaml`, print Git URLs one per line for the shell loop |
| [install_models.py](../scripts/helper/install_models.py) | Parse `models.yaml`; download from HuggingFace/CivitAI with skip-if-exists, retries, and TTY/non-TTY progress |
| [install_resources.py](../scripts/helper/install_resources.py) | Parse `resources.yaml`; copy or symlink folders into ComfyUI |
| [cuda_check.py](../scripts/helper/cuda_check.py) | Diagnostics: Python/PyTorch versions, `torch.cuda.is_available()`, device count/name, `nvidia-smi`, `torch.cuda.init()`. Run by the Docker entrypoint at boot |

## Idempotency & error handling

- **ComfyUI / extensions:** a directory without a `.git` folder is treated as an incomplete clone, removed, and re-cloned. Otherwise the existing clone is reused and just re-checked-out to the dated commit.
- **Models:** existing files are skipped; downloads retry 3× before giving up.
- **Resources:** `symlink` mode replaces the target each run; `copy` mode overwrites files in place.
- All step scripts run under `set -e`, so a hard failure stops the pipeline rather than continuing in a broken state.
