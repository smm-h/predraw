# predraw

Declarative rendering pipeline: JSON in, SVG/PNG/WebP out.

The missing link between your AI and the SVGs you want to make.

## Install

```
uv tool install predraw
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

## Commands

### build [path]

Render all outputs defined in `config.json`. Path can be a directory (looks for `main.json`) or a file.

```
predraw build                    # current directory
predraw build path/to/project    # explicit path
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

## Format

### Element types

| Type | Purpose | Key properties |
|---|---|---|
| `background` | Full-canvas fill | `fill` |
| `rect` | Rectangle | `x`, `y`, `width`, `height`, `fill` |
| `path` | SVG path | `d`, `fill`, `opacity`, `transform` |
| `text` | Text (can convert to paths) | `content`, `font`, `anchor`, `charStyles` |
| `group` | Container | `elements`, `transform` |

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
| `place` | `target`, `below`, `gap` | Position element below another |
| `group` | `targets`, `id` | Wrap elements into a group |

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

- `schema/scene.schema.json` -- scene format
- `schema/config.schema.json` -- config format

## Requirements

- Python 3.11+
- System fonts for `text-to-paths` (searches standard font directories)

## License

MIT
