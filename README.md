# ComfyUI-AutoSetup-Script
Custom Setup Script for ComfyUI with Extensions and Resources

## Overview
Lightweight installation system for ComfyUI, extensions, models, workflows, and resources.

### Features
- Automatic installation of ComfyUI, extensions, resources, and models (CivitAI + HuggingFace)
- Deterministic installation based on target date (ComfyUI and extensions)
- Config-driven setup (YAML)
- Modular scripts to update ComfyUI, extensions and models individually
- CLI or environment variable configuration

## Repository Structure
```
config/
  extensions.yaml
  resources.yaml
  models.yaml
resources/
  workflows/
scripts/
  helper/
  install_all.sh
  install_comfy.sh
  install_ext.sh
  install_models.sh
  install_resources.sh
```

## Usage
### Full installation
```bash
./scripts/install_all.sh
```

### Manual module installation
```bash
./scripts/install_comfy.sh # only ComfyUI
./scripts/install_ext.sh   # only Extensions
./scripts/install_resources.sh   # only Resources
./scripts/install_models.sh   # only Models
```

## Environment Variables / CLI Arguments
| Name | Purpose |
|------|---------|
| COMFY_DIR | Path where ComfyUI is installed |
| TARGET_DATE | Commit date for deterministic installation |
| CIVITAI_API_KEY | Token for model downloads |
| HUGGINGFACE_API_KEY | Token for HF download |

- API keys can also be stored in a local config file `local/local_keys.yaml`. The `local/` folder is git-ignored and kept private.
```bash
huggingface: "YOUR_KEY"
civitai: "YOUR_KEY"
```

- CLI arguments can override the environment variables.
  - `--comfy-dir <path>`
  - `--date <yyyy-mm-dd>`
  - `--hf-key <key>`
  - `--civitai-key <key>`

If no arguments are passed and no environment variables are set, the defaults are:
  - `COMFY_DIR`: `ComfyUI/` subfolder in the root directory
  - `TARGET_DATE`: date of latest commit in this repository
  - `CIVITAI_API_KEY`: not set
  - `HUGGINGFACE_API_KEY`: not set
