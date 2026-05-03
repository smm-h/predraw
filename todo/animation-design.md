# Animation Format Extension Design

## 1. Proposed JSON Format

### Scene-level animation config

```json
{
  "width": 400,
  "height": 200,
  "animation": {
    "duration": 2.0,
    "fps": 30
  },
  "elements": [...]
}
```

| Field | Type | Default | Description |
|---|---|---|---|
| `animation.duration` | number | required | Total animation duration in seconds |
| `animation.fps` | integer | 30 | Frame rate for raster output (GIF/WebM/MP4) |

### Element-level `animate` property

Each element gains an optional `animate` array of keyframe tracks:

```json
{
  "type": "rect",
  "id": "box",
  "x": 0, "y": 50, "width": 80, "height": 80,
  "fill": "#ff0000",
  "opacity": 1.0,
  "animate": [
    {
      "property": "opacity",
      "keyframes": [
        {"at": 0.0, "value": 0.0},
        {"at": 0.5, "value": 1.0}
      ],
      "easing": "ease-in"
    },
    {
      "property": "x",
      "keyframes": [
        {"at": 0.0, "value": 0},
        {"at": 1.0, "value": 300}
      ],
      "easing": "ease-in-out"
    }
  ]
}
```

### Transform animation

Transforms use dot notation for sub-properties:

```json
{
  "type": "path",
  "id": "logo",
  "d": "M10 10...",
  "transform": {"translate": [0, 0], "scale": [1, 1]},
  "animate": [
    {
      "property": "transform.translate",
      "keyframes": [
        {"at": 0.0, "value": [0, 0]},
        {"at": 1.0, "value": [200, 100]}
      ]
    },
    {
      "property": "transform.scale",
      "keyframes": [
        {"at": 0.0, "value": [0.5, 0.5]},
        {"at": 0.8, "value": [1.0, 1.0]}
      ]
    },
    {
      "property": "transform.rotate",
      "keyframes": [
        {"at": 0.0, "value": 0},
        {"at": 1.0, "value": 360}
      ]
    }
  ]
}
```

### Staggered/sequenced animations

Achieved via `delay` on individual tracks, not a separate sequencing concept:

```json
{
  "elements": [
    {
      "type": "rect", "id": "a",
      "animate": [
        {"property": "opacity", "keyframes": [{"at": 0, "value": 0}, {"at": 0.3, "value": 1}]}
      ]
    },
    {
      "type": "rect", "id": "b",
      "animate": [
        {"property": "opacity", "delay": 0.3, "keyframes": [{"at": 0, "value": 0}, {"at": 0.3, "value": 1}]}
      ]
    },
    {
      "type": "rect", "id": "c",
      "animate": [
        {"property": "opacity", "delay": 0.6, "keyframes": [{"at": 0, "value": 0}, {"at": 0.3, "value": 1}]}
      ]
    }
  ]
}
```

### Keyframe track schema

| Field | Type | Default | Description |
|---|---|---|---|
| `property` | string | required | Animated property (see table below) |
| `keyframes` | array | required | Ordered list of `{at, value}` pairs |
| `keyframes[].at` | number | required | Time in seconds from track start |
| `keyframes[].value` | any | required | Value at this time (type matches property) |
| `keyframes[].easing` | string | inherited | Per-segment easing override |
| `easing` | string | `"linear"` | Default easing for all segments in track |
| `delay` | number | `0` | Delay before track starts (seconds) |
| `repeat` | number/string | `1` | Repeat count; `"infinite"` for looping |
| `fill` | string | `"forwards"` | `"forwards"`, `"backwards"`, `"both"`, `"none"` |

### Animatable properties

| Property | Value type | Notes |
|---|---|---|
| `opacity` | number | 0.0 to 1.0 |
| `fill` | string | Color string; interpolated in sRGB |
| `stroke` | string | Color string |
| `x` | number | For rect/text |
| `y` | number | For rect/text |
| `width` | number | For rect |
| `height` | number | For rect |
| `stroke_width` | number | |
| `stroke_opacity` | number | |
| `transform.translate` | [x, y] | Array of 2 numbers |
| `transform.scale` | [sx, sy] | Array of 2 numbers |
| `transform.rotate` | number | Degrees, around element center |

### Easing functions

| Value | Description |
|---|---|
| `"linear"` | Constant speed |
| `"ease-in"` | Slow start (cubic-bezier 0.42, 0, 1, 1) |
| `"ease-out"` | Slow end (cubic-bezier 0, 0, 0.58, 1) |
| `"ease-in-out"` | Slow start and end (cubic-bezier 0.42, 0, 0.58, 1) |
| `"cubic-bezier(x1,y1,x2,y2)"` | Custom cubic bezier |

## 2. Mapping to SVG SMIL Output

Each keyframe track becomes one SMIL element nested inside the target SVG element.

| Track property | SMIL element | `attributeName` | Notes |
|---|---|---|---|
| `opacity` | `<animate>` | `opacity` | |
| `fill` | `<animate>` | `fill` | values= semicolon-separated colors |
| `x` | `<animate>` | `x` | |
| `y` | `<animate>` | `y` | |
| `width` | `<animate>` | `width` | |
| `height` | `<animate>` | `height` | |
| `stroke` | `<animate>` | `stroke` | |
| `stroke_width` | `<animate>` | `stroke-width` | |
| `transform.translate` | `<animateTransform>` | `transform` | type="translate" |
| `transform.scale` | `<animateTransform>` | `transform` | type="scale"; additive="sum" |
| `transform.rotate` | `<animateTransform>` | `transform` | type="rotate" |

### SMIL attribute mapping

| Keyframe track field | SMIL attribute |
|---|---|
| `keyframes[].at` | `keyTimes` (normalized to 0-1 by dividing by last `at`) |
| `keyframes[].value` | `values` (semicolon-separated) |
| `easing` | `calcMode="spline"` + `keySplines` |
| `delay` | `begin="<delay>s"` |
| `repeat` | `repeatCount` |
| `fill` (the fill-mode) | `fill="freeze"` or `fill="remove"` |
| total `at` span | `dur` |

### Example SVG output

Input:
```json
{"property": "opacity", "keyframes": [{"at": 0, "value": 0}, {"at": 0.5, "value": 1}], "easing": "ease-in"}
```

Output:
```xml
<rect x="0" y="50" width="80" height="80" fill="#ff0000" opacity="0">
  <animate attributeName="opacity"
           values="0;1"
           keyTimes="0;1"
           dur="0.5s"
           calcMode="spline"
           keySplines="0.42 0 1 1"
           fill="freeze"/>
</rect>
```

## 3. Frame-by-Frame Rendering (GIF/WebM/MP4)

### Pipeline

```
scene.json --> resolve animation at time t --> static Scene --> render_svg() --> cairosvg --> PNG frame
                                                                                              |
                                                               (repeat for each frame)        |
                                                                                              v
                                                                           stitch: Pillow (GIF) or ffmpeg (WebM/MP4)
```

### Interpolation engine

For each frame at time `t`:
1. For each element with `animate` tracks:
   - For each track, find the two surrounding keyframes `k_before` and `k_after`
   - Compute normalized progress `p = (t - k_before.at - delay) / (k_after.at - k_before.at)`
   - Apply easing function to `p` to get `p_eased`
   - Interpolate: `value = lerp(k_before.value, k_after.value, p_eased)`
2. Patch the element's property with the interpolated value
3. Render the patched scene as a static SVG frame
4. Convert to PNG via cairosvg

### Interpolation types by value

| Value type | Method |
|---|---|
| number | Linear interpolation |
| [x, y] array | Per-component linear interpolation |
| color string | Parse to RGB, interpolate each channel, emit hex |

### Stitching

| Format | Tool | Method |
|---|---|---|
| GIF | Pillow | `Image.save(append_images=frames, save_all=True, loop=0)` |
| WebM | ffmpeg | `ffmpeg -framerate {fps} -i frame_%04d.png -c:v libvpx-vp9 out.webm` |
| MP4 | ffmpeg | `ffmpeg -framerate {fps} -i frame_%04d.png -c:v libx264 -pix_fmt yuv420p out.mp4` |

### config.json extension

```json
{
  "outputs": [
    {"format": "svg", "path": "anim.svg", "mode": "dark"},
    {"format": "gif", "path": "anim.gif", "mode": "dark"},
    {"format": "webm", "path": "anim.webm", "mode": "dark"},
    {"format": "mp4", "path": "anim.mp4", "mode": "dark"}
  ]
}
```

Static formats (svg/png/webp) continue to render frame 0 (or the element's base values) when `animation` is present.

## 4. New Dependencies

| Dependency | Purpose | Required for |
|---|---|---|
| (none new) | Pillow already present | GIF stitching |
| (none new) | cairosvg already present | Per-frame SVG-to-PNG |
| ffmpeg (system) | Video encoding | WebM/MP4 only |

No new Python packages required. ffmpeg is an optional system dependency gated behind the webm/mp4 output formats (raise clear error if missing).

## 5. Modules That Need Changes

| Module | Change |
|---|---|
| `model.py` | Add `Keyframe`, `AnimationTrack`, `AnimationConfig` dataclasses; add `animate` field to `Element`; add `animation` field to `Scene` |
| `schema/scene.schema.json` | Add `animation` top-level property; add `animate` to all element definitions; add `keyframeTrack` and `keyframe` to `$defs` |
| `loader.py` | Parse `animation` from scene dict; parse `animate` arrays on elements |
| `renderer.py` | When `animate` tracks present on elements, emit nested SMIL elements inside SVG tags; refactor `_render_element` to produce open/close tags instead of self-closing |
| `output.py` | Add `_write_gif`, `_write_webm`, `_write_mp4` functions; implement frame-by-frame render loop with interpolation |
| `cli.py` | No changes needed (output format driven by config.json) |
| New: `interpolate.py` | Easing functions, value interpolation, keyframe sampling at time t |
| New: `animate.py` | Apply interpolated values to a Scene snapshot; orchestrate frame generation |

## 6. Scope Recommendation

### v0.3 (minimum viable animation)

| Feature | Included |
|---|---|
| `animation` top-level with `duration` and `fps` | Yes |
| `animate` property on elements | Yes |
| Animatable: `opacity`, `x`, `y`, `fill`, `transform.translate` | Yes |
| Easing: `linear`, `ease-in`, `ease-out`, `ease-in-out` | Yes |
| `delay` and `repeat` (finite only) | Yes |
| Output: animated SVG (SMIL) | Yes |
| Output: GIF | Yes |
| Interpolation engine | Yes |
| Schema validation for new fields | Yes |

### v0.4 (full animation)

| Feature | Deferred to |
|---|---|
| `transform.scale`, `transform.rotate` | v0.4 |
| `cubic-bezier(...)` custom easing | v0.4 |
| `repeat: "infinite"` | v0.4 |
| Per-keyframe easing overrides | v0.4 |
| `width`, `height`, `stroke_width`, `stroke_opacity`, `stroke` animation | v0.4 |
| Output: WebM/MP4 (ffmpeg dependency) | v0.4 |
| `fill` mode (`forwards`/`backwards`/`both`/`none`) | v0.4 |
| Color interpolation in perceptual color space (OKLab) | v0.4 |
| Path morphing (`d` property animation) | future |

### Rationale

v0.3 covers the most common animation patterns (fade in, slide in, color change, staggered entrance) with the two most portable output formats (SVG works everywhere; GIF is universal for short loops). This avoids the ffmpeg system dependency and keeps the interpolation engine simple (numbers and 2-tuples only, plus basic color lerp in sRGB). Transform rotation adds complexity around origin points; scale interacts with existing translate; both are deferred.

## 7. Open Questions (Resolved)

| Question | Decision |
|---|---|
| Sequencing model | Add timeline groups alongside delay-based sequencing |
| Static frame for animated scenes | Default to frame 0, optional `time` field in config outputs |
| Color interpolation | sRGB for v0.3, OKLab for v0.4 |
| Path morphing | Keep on roadmap (future, post-v0.4) |
