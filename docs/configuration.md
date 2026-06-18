# Configuration Reference

All of what the setup installs is defined by three YAML files in [config/](../config). Editing them is the supported way to customize a setup — you should rarely need to touch the scripts themselves.

| File | Controls | Consumed by |
|------|----------|-------------|
| [extensions.yaml](../config/extensions.yaml) | Custom-node extensions to clone | [install_ext.sh](../scripts/install_ext.sh) via [parse_extensions.py](../scripts/helper/parse_extensions.py) |
| [models.yaml](../config/models.yaml) | Models / LoRAs / VAEs to download | [install_models.sh](../scripts/install_models.sh) via [install_models.py](../scripts/helper/install_models.py) |
| [resources.yaml](../config/resources.yaml) | Folders (e.g. workflows) to deploy into ComfyUI | [install_resources.sh](../scripts/install_resources.sh) via [install_resources.py](../scripts/helper/install_resources.py) |

---

## extensions.yaml

A flat list of Git repositories to install into `ComfyUI/custom_nodes/`.

```yaml
extensions:
  - url: https://github.com/Comfy-Org/ComfyUI-Manager.git   # comments after the URL are free-form
  - url: https://github.com/rgthree/rgthree-comfy.git
```

**Schema**

| Key | Type | Required | Notes |
|-----|------|----------|-------|
| `extensions` | list | yes | Top-level list |
| `extensions[].url` | string | yes | Git URL. The folder name is derived from the repo name (`basename <url> .git`) |

**Behavior** ([install_ext.sh](../scripts/install_ext.sh))

- Each repo is cloned into `custom_nodes/<name>`.
- The clone is checked out to the commit matching the active target date (see [architecture.md](architecture.md) → *Deterministic versioning*).
- If the extension ships a `requirements.txt`, it is installed with `pip`.
- An incomplete clone (a directory without `.git`) is removed and re-cloned.

**Add an extension:** append a `- url:` line. **Disable one:** comment the line out with `#`.

---

## models.yaml

A list of download targets. Each entry maps a destination folder (relative to the ComfyUI root) to a source and a set of files.

```yaml
folders:

  # HuggingFace — direct file URLs
  - target: models/upscale_models
    source: huggingface
    urls:
      - https://huggingface.co/LS110824/upscale/resolve/main/4xLSDIR.pth

  # CivitAI — numeric model version IDs
  - target: models/loras/qwen
    source: civitai
    ids:
      - 2424051   # comments document what each ID is
```

**Schema**

| Key | Type | Required | Notes |
|-----|------|----------|-------|
| `folders` | list | yes | Top-level list |
| `folders[].target` | string | yes | Destination relative to the ComfyUI install dir; created if missing |
| `folders[].source` | string | yes | `huggingface` or `civitai` (case-insensitive) |
| `folders[].urls` | list of strings | for HuggingFace | Direct `resolve/` download URLs |
| `folders[].ids` | list of integers | for CivitAI | CivitAI download IDs (`https://civitai.com/api/download/models/<id>`) |

**Behavior** ([install_models.py](../scripts/helper/install_models.py))

- Files already present in the target folder are **skipped**, so re-running is cheap and resumable.
- Authentication: a `Bearer` token is attached when a key is available for that source (see *API keys* below). Public files download without a key; gated/private files and most CivitAI downloads require one.
- Filenames come from the URL, or from the `Content-Disposition` header (this is how CivitAI IDs resolve to real filenames).
- Downloads are **robust** ([downloader.py](../scripts/helper/downloader.py)): each file streams to a `.part` temp file, **resumes** where it left off on retry (HTTP `Range`, with a clean restart if the server ignores it), is **size-verified** against `Content-Length`, and only then **atomically renamed** into place — so an interrupted transfer never leaves a truncated file that looks complete. Each download retries up to 3 times; anything still failing is removed (no broken `.part`) and listed in an end-of-run **failure summary**. Progress prints as a live bar on a TTY and stepped percentage lines in non-TTY logs (e.g. RunPod).
- Multiple entries may point at the **same** `target` — this is used throughout `models.yaml` to group families (e.g. several `models/diffusion_models/wan22` blocks).

The shipped `models.yaml` covers several model families. They are independent — comment out blocks you do not need to save bandwidth and disk:

| Family | Example targets |
|--------|-----------------|
| Upscale models | `models/upscale_models` |
| RIFE frame interpolation | `custom_nodes/ComfyUI-Frame-Interpolation/ckpts/rife` |
| Lotus Depth | `models/vae/lotus_depth`, `models/diffusion_models/lotus_depth` |
| QWEN Image / Image-Edit | `models/{vae,text_encoders,diffusion_models,loras,controlnet}/qwen` |
| Z-Image / Z-Image Turbo | `models/{vae,text_encoders,diffusion_models,model_patches}/zimage` |
| WAN 2.2 (T2V/I2V/TI2V, Fun Control, S2V) | `models/{vae,text_encoders,clip_vision,audio_encoders,diffusion_models,loras}/wan22` |
| MMAudio (video-to-audio) | `models/mmaudio` |

> Note: targets such as the RIFE checkpoints are written **inside** a `custom_nodes/` extension folder, so that extension must be installed first. The default pipeline installs extensions before models, so ordering is handled for you.

### API keys

Keys are resolved per source in this order (first non-empty wins):

1. CLI argument — `--hf-key` / `--civitai-key`
2. Environment variable — `HUGGINGFACE_API_KEY` / `CIVITAI_API_KEY`
3. Local keys file — `local/local_keys.yaml` relative to your current working directory (`$PWD`)

The local keys file (git-ignored; keep it out of commits) uses these exact keys:

```yaml
huggingface: "hf_xxx"
civitai: "xxxxxxxx"
```

- Get a HuggingFace token: <https://huggingface.co/settings/tokens> (read scope is enough).
- Get a CivitAI token: account settings → **API Keys** at <https://civitai.com/user/account>.

### Skipping models (`SKIP_MODELS`)

To install only a subset without editing `models.yaml`, set the **`SKIP_MODELS`** env
var or the **`--skip-models`** flag to a filter. Default (unset/empty) downloads
everything.

**Syntax** — keyword groups:
- `;` separates groups (**OR** between groups).
- `,` separates keywords within a group (**AND** within a group).

A model is **skipped** when its URL/filename contains **all** keywords of **any** group.
Matching is **case-insensitive substring**.

```bash
# Skip WAN-Animate models AND everything Qwen:
./scripts/install_models.sh --skip-models "wan,animate;qwen"

# Same via environment variable:
SKIP_MODELS="wan,animate;qwen" ./scripts/install_all.sh
```

| Filter | Effect |
|--------|--------|
| `wan` | skip every model whose URL/name contains `wan` |
| `wan,animate` | skip only models containing **both** `wan` and `animate` |
| `wan,animate;qwen` | skip WAN-Animate models **and** all Qwen models |
| *(empty / unset)* | download everything (default) |

**What is matched (and a caveat):** keywords are tested against the **URL/filename**. CivitAI entries are matched against the **resolved filename** from the response headers, so they are still skipped without downloading the file body.

---

## resources.yaml

Maps folders from this repo into the ComfyUI installation. Used to deploy the bundled workflows.

```yaml
folders:
  - source: resources/workflows
    target: user/default/workflows/Fantastical
    mode: symlink
```

**Schema**

| Key | Type | Required | Notes |
|-----|------|----------|-------|
| `folders` | list | yes | Top-level list |
| `folders[].source` | string | yes | Path relative to this repo's root |
| `folders[].target` | string | yes | Path relative to the ComfyUI install dir |
| `folders[].mode` | string | no | `copy` (default) or `symlink` |

**Behavior** ([install_resources.py](../scripts/helper/install_resources.py))

- `symlink` — replaces the target with a single folder-level symlink to the absolute source path. Edits to files in this repo show up live in ComfyUI; pulling repo updates updates the workflows with no re-deploy. This is the default for workflows.
- `copy` — recursively copies files into the target, creating subdirectories as needed.

See [workflows.md](workflows.md) for what ships under `resources/workflows/`.
