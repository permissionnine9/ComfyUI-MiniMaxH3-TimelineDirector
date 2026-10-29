# ComfyUI MiniMax H3 Timeline Director

Start with the [**MiniMaxH3 All-in-One Full Timeline Director workflow**](example_workflows/剪枝_蒸馏%208%20步.json):
one lightweight graph covers text-to-video, image reference, audio-driven generation, video editing,
character replacement, motion transfer, digital humans, and manually segmented long-video generation. It now also supports **long-form digital humans and character singing**: a reference image preserves identity while a locked long soundtrack is sample-sliced across GEN windows, injected into every segment's AV latent, and restored continuously in the final output.

[简体中文](README_CN.md) · English

## Headline feature: lightweight unlimited-length video generation

The plugin splits any target duration into continuous segments and completes them in one ComfyUI
execution: per-segment generation with one shared seed, direct continuation from the previous
AV-latent tail, adaptive Drift-Control video masking, Soft AV audio continuity, overlap removal, and final synchronized assembly. Extend the result by increasing
the segment count—without generic Loop nodes or duplicated sampler chains. Practical length is limited
only by local VRAM, RAM, disk space, and ComfyUI execution limits.

[Download the all-in-one workflow](example_workflows/剪枝_蒸馏%208%20步.json) ·
[Chinese guide](docs/FINITE_SEGMENT_EXPANSION_CN.md) ·
[Chinese prompt specification](docs/MiniMax_H3_循环分段提示词_Agent规范.md)

[![Lightweight unlimited-length workflow](https://github.com/Songssx/ComfyUI-MiniMaxH3-TimelineDirector/releases/download/v0.6.0/infinite-workflow.webp)](example_workflows/剪枝_蒸馏%208%20步.json)

### Two directly generated, approximately one-minute examples

Both videos were produced in one plugin execution and are `52.625 seconds / 1263 frames / 24fps`.
Click a poster to play or download the original MP4. All media is hosted as GitHub Release assets, so
it adds nothing to the plugin clone or installation size.

| Finite direct-latent continuation | References with a 48-frame overlap |
| --- | --- |
| [![Play example one](https://github.com/Songssx/ComfyUI-MiniMaxH3-TimelineDirector/releases/download/v0.6.0/case-finite-segments-60s.webp)](https://github.com/Songssx/ComfyUI-MiniMaxH3-TimelineDirector/releases/download/v0.6.0/H3_finite_segments_60s.mp4) | [![Play example two](https://github.com/Songssx/ComfyUI-MiniMaxH3-TimelineDirector/releases/download/v0.6.0/case-reference-overlap-60s.webp)](https://github.com/Songssx/ComfyUI-MiniMaxH3-TimelineDirector/releases/download/v0.6.0/H3_reference_overlap48_60s.mp4) |

<p align="center">
  <img src="docs/images/creator-wecom.webp" alt="Creator WeCom contact card" width="360">
</p>

<p align="center">
  Creator: <strong>Shi Xiongsong</strong><br>
  <a href="https://space.bilibili.com/219572544?spm_id_from=333.40164.0.0">Bilibili</a>
  ·
  <a href="https://www.youtube.com/@shixiongsong">YouTube</a>
</p>

An editable reference-media timeline for ComfyUI's native **MiniMax H3 Reference to Video** workflow. It brings reference videos, paired soundtracks, fixed Guides, standalone images, and standalone audio into one compact editing surface.

> Video-generation agents should read the [Chinese segmented long-video guide](docs/AGENT_LONG_VIDEO_GUIDE_CN.md).

## Highlights

- Multi-clip timeline with move, trim, split, delete, snapping, and numeric positioning.
- Only media intersecting the cyan generation range participates in the current reference or Guide plan.
- Three per-clip modes: `Fixed Guide`, `Editable Reference`, and `Boundary Only`.
- Native text-to-video: with no uploaded media and no segment windows, Finite Segment Sampling internally creates a standard empty H3 AV latent from the Global Prompt and current GEN duration. Manual windows extend the same path to long-form T2V.
- Long-form digital humans and singing: assign the character image to each segment and mark one long soundtrack as `Locked Original Audio`. Manual GEN windows then drive multi-segment lip-sync or singing; the source is decoded once, sliced by exact sample position, injected into each AV latent with a zero audio-denoise mask, and restored as the continuous final soundtrack.
- Automatic locked-audio fitting: shorter timelines truncate the source, while timelines extending past the source preserve all available audio and pad only the excess with silence. Users do not need to frame-match MP3 metadata, H3-valid durations, or codec priming delays.
- Bound source audio follows video edits and can be disabled independently.
- Silent low-resolution monitoring proxies up to `480×270 / 12fps`.
- Multi-select, external file drop, deletion, and drag reordering for image/audio bins.
- Stable `<Picture N>`, `<Video N>`, and `<Audio N>` ordering from UI to H3 inputs.
- Global and per-segment prompts: the global prompt is reused only when all segment prompts are empty; entering any segment prompt requires completing every segment and disables the global prompt.
- Decode-time resizing to the node's `width × height` for VRAM protection.
- Separate merged outputs for timeline soundtracks and standalone reference audio.
- Timeline state is serialized into the ComfyUI workflow JSON.

## Main long-video workflow nodes

| Node | Purpose |
| --- | --- |
| **MiniMax H3 Material Planner** | Edits media and outputs a compact H3 plan plus an ordered Omni media bundle. |
| **MiniMax H3 Omni Media-Bundle Prompt Bridge** | Sends the bundle to an installed Prompt Rewriter Omni backend and returns only `rewritten_prompt`. |
| **MiniMax H3 Finite Segment Sampling** | Expands an acyclic graph for direct-latent continuation, masking, sampling, deduplication, and assembly. |
| **MiniMax H3 Timeline Director (Compatibility)** | Preserves the original all-in-one workflow and older saved workflows. |

Long-video generation needs only **Material Planner Segment Plan → Finite Segment Sampling**. The Plan Encoder remains registered as a hidden internal node for expanded execution graphs and old workflow compatibility.

The split architecture avoids a ComfyUI dependency cycle:

```text
Material Planner ──Omni bundle──> Omni Prompt Bridge ──rewritten_prompt──> Plan Encoder
       └────────────────────H3 plan─────────────────────────────────────> Plan Encoder
```

## Installation

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/Songssx/ComfyUI-MiniMaxH3-TimelineDirector.git
```

Restart ComfyUI and search for `MiniMax H3`.

The source UI is English. Simplified Chinese is provided through ComfyUI's official localization
system and follows the language selected in ComfyUI settings; restart or reload the frontend after
changing the locale.

### Requirements

- A recent ComfyUI build with the native MiniMax H3 nodes; `MiniMaxH3AddGuide` is additionally required only when Guides are used.
- MiniMax H3 Ref2VA model, CLIP, video VAE, and audio VAE.
- Python 3.10 or newer.
- ComfyUI's `imageio-ffmpeg` package for low-resolution preview proxies.

No extra pip dependency is declared. The plugin uses PyAV, Pillow, NumPy, PyTorch, torchaudio, aiohttp, and imageio-ffmpeg normally included with a compatible ComfyUI installation.

## Example workflows

Only the following two examples are shipped. The first is the normal generation entry point; the second adds Omni prompt expansion.

### 1. All-in-One Full Timeline Director (recommended)

[Download workflow](example_workflows/剪枝_蒸馏%208%20步.json)

This is the **all-task, lightweight, no-rewiring** workflow. Configure only the Material Planner's media, time windows, and prompts to run:

- Text-to-video with no media, as one segment.
- Long-form text-to-video with no media and multiple segments.
- Single-segment image-reference generation.
- Multi-segment image-reference generation.
- Single-segment image-and-audio reference generation.
- Multi-segment image-and-audio generation, long-form digital-human lip sync, and long-form character singing; use `Locked Original Audio` when the source signal must remain unchanged.
- Single-segment editable-video reference, character replacement, and motion transfer.
- Manually segmented long-video reference generation, character replacement, motion transfer, and final AV assembly.

Connect the Material Planner's **Segment Plan** directly to **MiniMax H3 Finite Segment Sampling**. With no uploaded media it creates an empty AV latent; with references it encodes each segment's assigned media. Drag GEN windows to define duration and seam overlap, reuse one Global Prompt, or enter complete per-segment prompts. The plugin handles legal-frame alignment, Drift-Control, Soft AV, overlap removal, tail trimming, and final assembly.

> The plugin does not auto-segment by reference-media duration or infer whether character identity should continue. Segment ranges, overlaps, and assignments are explicitly controlled on the timeline. For character replacement, use **Editable Reference** in most cases.

### 2. Timeline planning with Prompt generation

[Download workflow](example_workflows/MiniMax_H3时间规划+Prompt提示词生成.json)

This variant adds the **MiniMax H3 Omni Media-Bundle Prompt Bridge**, allowing Prompt Rewriter Omni to inspect ordered images, videos, and audio before expanding an H3 prompt. Use it when multimodal material understanding should precede H3 generation.

> This workflow requires [MiniMax-H3-Prompt-Rewriter-ComfyUI](https://github.com/pytraveler/MiniMax-H3-Prompt-Rewriter-ComfyUI). Follow that project for model, quantization, and VRAM requirements.

## Basic usage

1. Set `width`, `height`, and `generation_seconds`.
2. Add video, image, and audio files using the toolbar or direct file drop.
3. Move, trim, or split video clips, then place the cyan range over the interval to generate.
4. Select a purpose for each video:
   - `Fixed Guide` anchors the overlap at its generated-frame positions.
   - `Editable Reference` sends it as `<Video N>` without hard-locking the original subject.
   - `Boundary Only` anchors only the first and last overlap frames.
5. Enable or disable paired video soundtracks as needed.
6. Verify the reference labels at the bottom and run the connected encoder or prompt workflow.

Videos are numbered left-to-right by their intersections with the cyan range. Standalone images and audio follow their visible bin order; drag reordering immediately updates the underlying H3 order.

## Segmented long-video generation

Generate long videos in overlapping segments. Use the previous segment's final shot as the next segment's opening Guide, and describe that overlap as `Shot 1` before new content. When assembling segments, remove the repeated Guide interval from the later segment. See the [Chinese agent guide](docs/AGENT_LONG_VIDEO_GUIDE_CN.md) for the full procedure.

### Finite direct-latent continuation

Finite sampling carries the previous sampled AV latent tail directly into the next opening and
avoids an RGB decode/re-encode round trip. Drift-Control is always active and has no user-facing mode
selector. The requested overlap is aligned down to H3's legal temporal grid (for example, 24 becomes
22 and 48 becomes 39), and that same actual value drives latent carry, decoded trimming, and assembly.
The mask adapts both to the aligned overlap's video-token count and to the connected sampler's sigma
schedule, including accelerated 4-step and 8-step schedules. It dynamically re-noises only the disposable video prefix while keeping the seam-side
latent clean. When audio continuation is enabled, the carried overlap stays exact until its final eight
audio-latent ticks, where a half-cosine Soft AV mask releases it into newly generated sound. Assembly
replaces the preceding audio tail with this incoming Soft AV overlap so the transition is retained in the final output. All segments use
exactly the seed shown on the sampling node. The old generic-loop helper nodes and PR #15923 dependency
have been removed.

Drift-Control AV is adapted from
[ComfyUI-MiniMaxH3-Contex-Loop](https://github.com/ethanfel/ComfyUI-MiniMaxH3-Contex-Loop)
under GPL-3.0. It remains experimental and is intended for same-shot long-chain comparisons.

## Credits

- The Omni bridge and prompt-generation workflow reference and adapt [pytraveler/MiniMax-H3-Prompt-Rewriter-ComfyUI](https://github.com/pytraveler/MiniMax-H3-Prompt-Rewriter-ComfyUI).
- See [MiniMax-AI/MiniMax-H3](https://github.com/MiniMax-AI/MiniMax-H3) for the official model and prompt guidance.
- Thanks to the maintainers of ComfyUI's native MiniMax H3 and Guide nodes.

## License

[GPL-3.0](LICENSE)
