# Bundled Workflows

The repo ships a set of ready-to-use ComfyUI workflows under [resources/workflows/](../resources/workflows). They are deployed by [install_resources.sh](../scripts/install_resources.sh) and, by default, **symlinked** into:

```
<ComfyUI>/user/default/workflows/Fantastical/
```

So they appear in the ComfyUI sidebar under the **Fantastical** folder. Because they are symlinked, pulling repo updates refreshes the workflows with no re-deploy step. (See [configuration.md](configuration.md) → `resources.yaml`.)

Each workflow assumes the matching models from [models.yaml](../config/models.yaml) and the extensions from [extensions.yaml](../config/extensions.yaml) are installed — run the full setup, or at least the relevant model family, before opening one.

## Image

| Workflow | Purpose |
|----------|---------|
| `(G) [QWEN] Image Gen.json` | Text-to-image with QWEN Image |
| `(G) [QWEN] Image Edit.json` | Instruction-based image editing with QWEN Image-Edit |
| `(G) [Z-Image] Image Gen.json` | Text-to-image with Z-Image |
| `(G) [Z-Image Turbo] Image Gen.json` | Fast few-step text-to-image with Z-Image Turbo |
| `(G) [SDXL] RealVisXL Simple.json` | Simple SDXL (RealVisXL) generation |
| `(G) [SeedVR2] 4K Image Upscale.json` | 4K image upscaling with SeedVR2 |
| `(G) [Z-Turbo] 4K Image Upscale.json` | 4K image upscaling using a Z-Image Turbo pipeline |

## Video

| Workflow | Purpose |
|----------|---------|
| `(G) [WAN] I2V.json` | Image-to-video with WAN 2.2 |
| `(G) [WAN] S2V.json` | Sound/speech-to-video with WAN 2.2 |
| `(G) [WAN] V2V ControlNet.json` | Video-to-video with WAN 2.2 Fun Control (ControlNet) |
| `(G) [WAN] Animate.json` | WAN 2.2 Animate |
| `(G) [WAN] 4K Video Upscale.json` | 4K video upscaling via a WAN pipeline |
| `(G) [SeedVR2] 4K Video Upscale.json` | 4K video upscaling with SeedVR2 |

## Audio

| Workflow | Purpose |
|----------|---------|
| `(G) [MMAudio] Video-to-Audio.json` | Generate a matching audio track for a video with MMAudio |

## Customizing

To ship your own workflows, drop `.json` files into `resources/workflows/` (or a subfolder) and re-run [install_resources.sh](../scripts/install_resources.sh). To deploy from a different location or use copy instead of symlink, edit [config/resources.yaml](../config/resources.yaml).
