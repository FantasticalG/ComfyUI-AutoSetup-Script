# ComfyUI-AutoSetup-Script

Custom setup script for ComfyUI with extensions, models, workflows, and resources.

## Overview

A lightweight, config-driven installation system that builds a complete, reproducible ComfyUI environment from a set of YAML files. Point it at a directory and it will install ComfyUI, custom-node extensions, models/LoRAs (HuggingFace + CivitAI), and ready-to-use workflows.

### Features

- **One-command install** of ComfyUI, extensions, resources, and models.
- **Deterministic, date-pinned versioning** — ComfyUI and extensions are checked out to a commit matching a target date, so setups are reproducible (no surprise breakage from upstream updates).
- **Config-driven** — everything to install is declared in three YAML files; you rarely touch the scripts.
- **Modular** — update ComfyUI, extensions, resources, or models independently.
- **Flexible credentials** — API keys via CLI flag, environment variable, or a local file.
- **Resumable downloads** — existing files are skipped; failed downloads retry.

> Looking to run this in Docker / on RunPod? See the companion [ComfyUI-AutoSetup-RunPod-Container](https://github.com/FantasticalG/ComfyUI-AutoSetup-RunPod-Container), which wraps this script in a GPU container with ComfyUI + JupyterLab.

## Prerequisites

- `git` and `python3` (with `pip`) on `PATH` — the scripts check for these and exit early if missing.
- `bash`.
- For GPU inference, a working CUDA + PyTorch environment. This script installs ComfyUI's Python requirements but does **not** install a CUDA build of PyTorch — provide that yourself (a venv is recommended), or use the [container](https://github.com/FantasticalG/ComfyUI-AutoSetup-RunPod-Container), which sets it up for you.
- Enough disk space for the model families you enable (the defaults pull several large diffusion models — tens of GB).

## Repository structure

```
config/
  extensions.yaml        # custom-node extensions to install
  models.yaml            # models / LoRAs / VAEs to download
  resources.yaml         # folders (workflows) to deploy into ComfyUI
resources/
  workflows/             # bundled ComfyUI workflows (Image / Video / Audio)
scripts/
  install_all.sh         # orchestrator (runs the four steps below)
  install_comfy.sh       # clone/update ComfyUI to the dated commit
  install_ext.sh         # install extensions
  install_resources.sh   # deploy workflows/resources
  install_models.sh      # download models
  helper/
    lib_common.sh             # shared env, logging, arg parsing
    get_commit_for_repo.sh    # resolve a date to a commit hash
    parse_extensions.py       # read extensions.yaml
    install_models.py         # download from HuggingFace / CivitAI
    install_resources.py      # copy / symlink resource folders
    cuda_check.py             # CUDA / PyTorch diagnostics
docs/                    # detailed reference (see below)
```

## Quick start

Full installation (installs into `./ComfyUI` by default):

```bash
./scripts/install_all.sh
```

Run individual steps (each is standalone — handy for targeted updates):

```bash
./scripts/install_comfy.sh       # only ComfyUI
./scripts/install_ext.sh         # only extensions
./scripts/install_resources.sh   # only resources/workflows
./scripts/install_models.sh      # only models
```

Examples with options:

```bash
# Install into a specific directory
./scripts/install_all.sh --comfy-dir /workspace/ComfyUI

# Reproduce a known-good state from a past date
./scripts/install_all.sh --date 2025-06-15

# Provide API keys inline
./scripts/install_models.sh --hf-key hf_xxx --civitai-key xxxx
```

## How it works

ComfyUI and custom nodes update constantly, and an upstream change can break a working graph. To stay reproducible, this setup pins every Git repo to a **date** rather than to `HEAD`:

1. A target date is chosen — by default the date of the latest commit in *this* repo, or whatever you pass via `--date` / `TARGET_DATE`.
2. For each repo, [get_commit_for_repo.sh](scripts/helper/get_commit_for_repo.sh) finds the last commit on or before that date and checks it out.

So committing to this repo is what "updates" your stack, and pinning an explicit date rebuilds an older state exactly. Full details and the install pipeline are in [docs/architecture.md](docs/architecture.md).

## Configuration

What gets installed is declared entirely in [config/](config):

| File | Controls |
|------|----------|
| [`extensions.yaml`](config/extensions.yaml) | Custom-node extensions (Git URLs) |
| [`models.yaml`](config/models.yaml) | Models / LoRAs / VAEs (HuggingFace URLs or CivitAI IDs) |
| [`resources.yaml`](config/resources.yaml) | Folders (workflows) to copy or symlink into ComfyUI |

See **[docs/configuration.md](docs/configuration.md)** for the full schema of each file with annotated examples.

## Environment variables / CLI arguments

CLI arguments override environment variables, which override the defaults.

| Env var | CLI flag | Purpose | Default |
|---------|----------|---------|---------|
| `COMFY_DIR` | `--comfy-dir <path>` | ComfyUI installation directory | `./ComfyUI` (relative to `$PWD`) |
| `TARGET_DATE` | `--date <yyyy-mm-dd>` | Commit date for deterministic installs | date of the latest commit in this repo |
| `HUGGINGFACE_API_KEY` | `--hf-key <key>` | HuggingFace download token | not set |
| `CIVITAI_API_KEY` | `--civitai-key <key>` | CivitAI download token | not set |

API keys may also be stored in `local/local_keys.yaml`, relative to your current working directory (`$PWD`):

```yaml
huggingface: "YOUR_KEY"
civitai: "YOUR_KEY"
```

Resolution order per source: **CLI flag → environment variable → local keys file**. See [docs/configuration.md](docs/configuration.md#api-keys) for where to obtain the tokens.

## Customizing

- **Add/remove an extension:** edit [config/extensions.yaml](config/extensions.yaml) and re-run `install_ext.sh`.
- **Add/remove models:** edit [config/models.yaml](config/models.yaml) and re-run `install_models.sh`. Comment out model families you don't need to save bandwidth and disk.
- **Ship your own workflows:** drop `.json` files into [resources/workflows/](resources/workflows) and re-run `install_resources.sh`.

See [docs/workflows.md](docs/workflows.md) for the catalog of bundled workflows.

## Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| `git missing` / `python3 missing` | Install the tool and ensure it is on `PATH`. |
| Re-clone every run / "Removing incomplete clone" | A repo folder exists without `.git`. The script removes and re-clones it automatically; just let it finish. |
| `401`/`403` on a download | The file is gated/private, or a CivitAI download needs a token. Provide an API key (see above). |
| CivitAI download produces a strange filename | The real name comes from the server's `Content-Disposition` header — this is expected. |
| Model "already exists", not re-downloaded | Existing files are skipped by design. Delete the file to force a re-download. |
| ComfyUI starts but no CUDA | This script doesn't install a CUDA build of PyTorch. Install one in your environment, or use the [container](https://github.com/FantasticalG/ComfyUI-AutoSetup-RunPod-Container). Run `python3 scripts/helper/cuda_check.py` to diagnose. |

## Documentation

- [docs/configuration.md](docs/configuration.md) — full YAML schema reference for all three config files.
- [docs/architecture.md](docs/architecture.md) — install pipeline, helper scripts, and the deterministic-versioning design.
- [docs/workflows.md](docs/workflows.md) — catalog of the bundled workflows.
- [docs/known-issues.md](docs/known-issues.md) — known limitations, rough edges, and planned improvements.

## License

See [LICENSE](LICENSE).
