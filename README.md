# predraw

Declarative rendering pipeline: JSON in, SVG/PNG/WebP out.

The missing link between your AI and the SVGs you want to make.

## Install

From PyPI:

```
uv tool install predraw
```

From npm (requires Python 3.11+):

```
npm i -g predraw
```

## Quick start

Create a project directory:

```
my-asset/
  main.json
  config.json
```

**main.json** -- the scene:

```json
{
  "width": 400,
  "height": 200,
  "styles": {
    "bg": {"light": "#ffffff", "dark": "#1a1a1a"},
    "fg": {"light": "#000000", "dark": "#ffffff"}
  },
  "elements": [
    {"type": "background", "fill": "$bg"},
    {
      "type": "text",
      "id": "title",
      "content": "hello world",
      "x": 200,
      "y": 110,
      "anchor": "middle",
      "fill": "$fg",
      "font": {"family": "Liberation Sans", "size": 48, "weight": 700}
    }
  ],
  "pipeline": [
    {"action": "text-to-paths", "target": "title"}
  ]
}
```

**config.json** -- output targets:

```json
{
  "outputs": [
    {"format": "svg", "path": "hello-dark.svg", "mode": "dark"},
    {"format": "png", "path": "hello-light.png", "mode": "light"},
    {"format": "webp", "path": "hello-dark.webp", "mode": "dark", "quality": 90}
  ]
}
```

Build:

```
predraw build my-asset/
```

Or auto-rebuild on changes:

```
predraw watch my-asset/
```

## Commands

### init [path]

Create a starter project with `main.json` and `config.json`.

```
predraw init                     # current directory
predraw init my-asset/           # create in new directory
```

### build [path] [--dry-run]

Render all outputs defined in `config.json`. Path can be a directory (looks for `main.json`) or a file.

```
predraw build                    # current directory
predraw build path/to/project    # explicit path
predraw build --dry-run          # preview without rendering
```

### watch [path]

Auto-rebuild when project files change. Polls for changes every 0.5s with 0.3s debounce.

```
predraw watch                    # watch current directory
predraw watch my-asset/          # watch specific project
```

### pack [path] [-o file]

Convert a directory project into a single portable JSON file. Imports are resolved and inlined as `defs`.

```
predraw pack my-asset/ -o packed.json
```

### unpack \<file\> [-o dir]

Convert a packed JSON file back into a directory project with separate component files.

```
predraw unpack packed.json -o my-asset/
```

### validate \<file\> [--schema scene|config]

Validate a scene or config file against the JSON Schema. Auto-detects file type (presence of `"outputs"` key = config, otherwise = scene).

```
predraw validate main.json
predraw validate config.json --schema config
```

## Format

### Element types

| Type | Purpose | Key properties |
|---|---|---|
| `background` | Full-canvas fill | `fill` |
| `rect` | Rectangle | `x`, `y`, `width`, `height`, `fill`, `stroke` |
| `path` | SVG path | `d`, `fill`, `opacity`, `transform`, `stroke` |
| `text` | Text (can convert to paths) | `content`, `font`, `anchor`, `charStyles`, `stroke` |
| `group` | Container | `elements`, `transform` |

### Stroke

All visible elements support stroke properties:

```json
{"type": "rect", "width": 100, "height": 50, "stroke": "#ff0000", "strokeWidth": 2, "strokeDasharray": "5 3"}
```

Properties: `stroke`, `strokeWidth`, `strokeDasharray`, `strokeLinecap` (butt/round/square), `strokeLinejoin` (miter/round/bevel), `strokeOpacity`.

### Gradients

Fill and stroke accept gradient objects:

```json
{"fill": {"type": "linear-gradient", "angle": 90, "stops": [
  {"offset": 0, "color": "#ff0000"},
  {"offset": 1, "color": "#0000ff"}
]}}

{"fill": {"type": "radial-gradient", "cx": 0.5, "cy": 0.5, "r": 0.5, "stops": [
  {"offset": 0, "color": "#ffffff"},
  {"offset": 1, "color": "#000000", "opacity": 0.5}
]}}
```

### Use (component instantiation)

Reference a component from `imports` or `defs`:

```json
{"use": "logo", "transform": {"translate": [100, 50], "scale": [2, 2]}}
```

Property overrides cascade to children:

```json
{"use": "logo", "fill": "#ff0000", "opacity": 0.5}
```

### Styles

Define color tokens with light/dark variants:

```json
{
  "styles": {
    "primary": {"light": "#000000", "dark": "#ffffff"},
    "muted": {"light": "#666666", "dark": "#999999"}
  }
}
```

Reference with `$` prefix: `"fill": "$primary"`. Mode is selected per-output in `config.json`.

### charStyles

Style individual characters differently:

```json
{
  "type": "text",
  "content": "releasable",
  "fill": "#ffffff",
  "charStyles": [
    {"chars": "rlsbl", "opacity": 1.0},
    {"chars": "eeaa", "opacity": 0.12}
  ]
}
```

### Pipeline

Ordered postprocessing steps:

| Action | Fields | Description |
|---|---|---|
| `text-to-paths` | `target` | Convert text to path outlines via font glyphs |
| `center` | `target`, `axis` (x/y/both) | Center element on canvas |
| `place` | `target`, `below`/`above`/`left`/`right`, `gap` | Position element relative to another |
| `group` | `targets`, `id` | Wrap elements into a group |

### Local fonts

Place `.ttf` or `.otf` files in a `fonts/` directory in your project. These are searched before system fonts, enabling reproducible rendering across machines.

```
my-asset/
  main.json
  config.json
  fonts/
    Inter-Bold.ttf
```

### Components

Split reusable parts into separate files:

```
project/
  main.json
  config.json
  components/
    logo.json
```

**main.json:**
```json
{
  "imports": {"logo": "./components/logo.json"},
  "elements": [
    {"use": "logo", "transform": {"translate": [10, 10]}}
  ]
}
```

### Packed format

`predraw pack` inlines imports as `defs`:

```json
{
  "defs": {
    "logo": {"type": "group", "elements": [...]}
  },
  "elements": [
    {"use": "logo"}
  ]
}
```

## Config

`config.json` defines output targets:

```json
{
  "outputs": [
    {"format": "svg", "path": "out.svg"},
    {"format": "png", "path": "out-dark.png", "mode": "dark"},
    {"format": "webp", "path": "out.webp", "mode": "dark", "quality": 90}
  ]
}
```

| Field | Required | Description |
|---|---|---|
| `format` | Yes | `svg`, `png`, or `webp` |
| `path` | Yes | Output file path (relative to project dir) |
| `mode` | No | `light` or `dark` (default: `dark`) |
| `quality` | No | WebP quality 1-100 (default: 90) |

## JSON Schema

Formal schemas for editor validation and LLM structured output:

- `predraw/schema/scene.schema.json` -- scene format
- `predraw/schema/config.schema.json` -- config format

## Requirements

- Python 3.11+
- System fonts for `text-to-paths` (searches standard font directories)

## License

MIT
