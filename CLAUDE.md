# CLAUDE.md — ComfyUI-AutoSetup-Script

Guidance for Claude Code working in this repo. Read this before making changes.

## What this repo is

A lightweight, **config-driven** installer that builds a reproducible ComfyUI
environment: ComfyUI itself, custom-node extensions, models/LoRAs (HuggingFace +
CivitAI), and bundled workflows. Everything installable is declared in
`config/*.yaml` — prefer editing config over scripts.

It is consumed by the sibling repo **ComfyUI-AutoSetup-RunPod-Container**
(a Docker/RunPod wrapper that clones and runs this repo). The real target is a
**CUDA/Linux** box; local **macOS** runs are for testing script *logic* only —
some CUDA-only deps (e.g. `onnxruntime-gpu`) cannot install on macOS.

## Safety rules (non-negotiable — a past mistake destroyed user data)

- **Never run destructive commands against live paths.** No `rm -rf`,
  `git clean -fdx`, `git checkout`/`reset` that discards work, or overwrite/move
  on project, home, or any real directory.
- **Never execute the install scripts or clone/delete logic to "verify" them.**
  Do not run `install_*.sh`, `clone_or_checkout`, or anything that clones/removes
  against the filesystem. Verify with `bash -n` and static reading only.
- **Confirm before any outward-facing or irreversible action.**

## Commits / version control

Make **working-tree edits only**. Do **not** commit, branch, or open PRs unless
explicitly asked — the user reviews and commits everything.

## Architecture & conventions

- **Pipeline:** `install_all.sh` orchestrates → `install_comfy.sh`,
  `install_ext.sh`, `install_resources.sh`, `install_models.sh`. Each step script
  is standalone and sources `scripts/helper/lib_common.sh`.
- **`lib_common.sh` is the shared core.** It provides:
  - `log()` — all user-facing messages go through it.
  - Config resolution with precedence **CLI flag → env var → default**, then
    **exports** the canonical vars (`COMFY_DIR`, `TARGET_DATE`,
    `HUGGINGFACE_API_KEY`, `CIVITAI_API_KEY`) so child `bash` processes inherit
    them. Do not break this — it's why `install_all.sh` flags reach the steps.
  - `ensure_git` / `ensure_python` dependency checks.
  - `clone_or_checkout <url> <dir> <date>` and `pip_install_quiet <args…>` —
    **reuse these; do not duplicate git-clone or pip logic** in the step scripts.
- **Config-driven:** `config/extensions.yaml` (git URLs), `config/models.yaml`
  (HF urls / CivitAI ids), `config/resources.yaml` (folders to copy/symlink).
  Add/remove things here, not in code.
- **Deterministic-date pinning:** `get_commit_for_repo.sh` resolves a target date
  to a commit; ComfyUI and extensions are pinned by date, not `HEAD`.
- **Python helpers** (`scripts/helper/*.py`) parse YAML and do IO only; keep them
  small and single-purpose. `install_models.py` orchestrates (config/loop/filter/
  summary) and delegates the robust transfer mechanism to `downloader.py`
  (`download_file()` — resumable, atomic, size-verified).
- Docs live in `README.md` + `docs/` (configuration, architecture, workflows,
  known-issues). See `docs/known-issues.md` for tracked limitations.

## Coding style

Match these conventions when adding code; the existing scripts already follow them.

**Bash** — lint with `shellcheck`, format with `shfmt` (Google Shell Style Guide):
- `set -eo pipefail` at the top of every script (not `set -e` alone). Avoid `set -u`
  here — it breaks the `lib_common.sh` arg parser; use `${var:-}` if you need a guard.
- 2-space indentation; `[[ … ]]` for tests (not `[ … ]`); always quote expansions
  (`"$var"`); `$(…)` not backticks; `local` for function vars; lowercase snake_case.
- Route messages through `log()`; put shared logic in `lib_common.sh` functions
  (don't duplicate git/pip logic); keep each script's `# ---` header comment.

**Python** — format with `black`, lint with `ruff` (PEP 8):
- 4-space indentation; double quotes; stdlib + `pyyaml` + `requests` only;
  target Python ≥ 3.11 (3.12 matches the container).
- Each helper starts with `#!/usr/bin/env python3` and a `# ---` header; route
  human-facing output through a `log()` helper (`[COMFY AUTO SETUP]` prefix).
  Exceptions: `parse_extensions.py` prints raw URLs (machine-parsed) and
  `cuda_check.py` prints a plain diagnostics banner — leave those as-is.

**Compact, clean, readable (both languages):**
- Keep functions small and single-purpose; **separate mechanism from orchestration**
  (e.g. `downloader.py` owns *how* to download; `install_models.py` owns *what*).
- When one concern outgrows ~a screen, extract a focused helper (function or module)
  rather than nesting deeper.
- Prefer **explicit return values** (a `namedtuple`/status) over sentinel-by-convention
  (`None`/magic objects); guard-clause and `continue`/early-return to keep nesting shallow.
- Make scripts importable for testing: wrap top-level work in `main()` +
  `if __name__ == "__main__":` so pure logic can be unit-tested without side effects.

## Verification & docs

- Shell changes: `bash -n` (and `shellcheck` if available) + static reasoning.
  Never run installs against the real filesystem.
- Keep `README.md` and `docs/*.md` in sync when behavior changes — but **ask
  before large README rewrites**.
