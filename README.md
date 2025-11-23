# ComfyUI-AutoSetup-Script
Custom Setup Script for ComfyUI with Extensions and Resources

## Overview
Lightweight installation system for ComfyUI, extensions, models, workflows, and resources.

### Features
- Deterministic installation based on commit date
- Modular, testable scripts
- Automatic installation of ComfyUI, extensions, resources, and models (CivitAI + HuggingFace)
- Config-driven behavior (YAML, TXT)
- CLI or environment variable configuration

## Repository Structure
```
config/
  extensions.txt
  resources.yaml
  models.yaml
scripts/
  install_base.sh
  install_comfy.sh
  install_ext.sh
  install_resources.sh
  install_models.sh
  lib_common.sh
  install_resources.py
  install_models.py
  get_commit_for_repo.py
README.md
```

## Usage
### Full installation
```bash
./scripts/install_base.sh
```

### Manual module installation
```bash
./scripts/install_comfy.sh # only ComfyUI
./scripts/install_ext.sh   # only Extensions
./scripts/install_resources.sh   # only Resources
./scripts/install_models.sh   # only Models
```

## Environment Variables
| Name | Purpose |
|------|---------|
| COMFY_DIR | Path where ComfyUI is installed |
| TARGET_DATE | Commit date for deterministic installation |
| CIVITAI_API_KEY | Token for model downloads |
| HUGGINGFACE_API_KEY | Token for HF download |

- API keys may also be stored in a local, git-ignored file `config/local_keys.yaml`.
```bash
huggingface: "YOUR_KEY"
civitai: "YOUR_KEY"
```

- CLI arguments can override environment variables.
  - `--comfy-dir <path>`
  - `--date <yyyy-mm-dd>`
  - `--hf-key <key>`
  - `--civitai-key <key>`
