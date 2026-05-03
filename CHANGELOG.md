# Changelog

## 0.1.2

- npm dual-publish — installable via `npm i -g predraw` (Node shim delegates to Python)
- `predraw validate` documented in README

## 0.1.1

- Bounding box calculation for paths — `place` pipeline step now uses real geometry instead of font-size heuristic
- Local `fonts/` directory support — project-local fonts searched before system fonts for reproducible rendering
- Component property overrides — `use` elements can override `fill` (replaces) and `opacity` (multiplies) on referenced components

## 0.1.0

- Declarative JSON format for describing visual assets (rect, path, text, group, background)
- `$style` tokens with light/dark mode variants, resolved at render time
- Per-character text styling via `charStyles`
- Component system: `imports` + `use` with property overrides (fill, opacity cascade)
- `text-to-paths` pipeline step via fonttools (converts text to SVG path outlines)
- Pipeline steps: `center`, `place`, `group`, `text-to-paths`
- Output formats: SVG, PNG (via cairosvg), WebP (via Pillow)
- Config-driven outputs with per-output mode selection (`config.json`)
- `predraw build` — render all outputs from a project directory or single file
- `predraw pack` — convert directory project to single portable JSON file
- `predraw unpack` — convert packed file back to directory with components
- JSON Schema for scene and config formats
- `predraw validate` — validate scene/config files against the JSON Schema
