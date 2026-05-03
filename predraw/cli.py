"""CLI entry point for predraw — argparse-based with build/pack/unpack subcommands."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from itertools import groupby
from pathlib import Path

from .loader import load_config, load_scene, resolve_styles
from .model import Element, Font, Scene, Style, Transform
from .output import write_outputs
from .pipeline import execute_pipeline
from .renderer import render_svg
from .validator import validate_config, validate_scene


def main():
    """Entry point for the predraw CLI."""
    parser = argparse.ArgumentParser(prog="predraw", description="predraw scene builder")
    subparsers = parser.add_subparsers(dest="command")

    # -- build --
    build_parser = subparsers.add_parser("build", help="Build scene into output files")
    build_parser.add_argument("path", nargs="?", default=".", help="Project directory or scene file (default: .)")

    # -- pack --
    pack_parser = subparsers.add_parser("pack", help="Pack a scene directory into a single JSON file")
    pack_parser.add_argument("path", nargs="?", default=".", help="Project directory or scene file (default: .)")
    pack_parser.add_argument("-o", "--output", default="packed.json", help="Output file path (default: packed.json)")

    # -- unpack --
    unpack_parser = subparsers.add_parser("unpack", help="Unpack a packed JSON file into a project directory")
    unpack_parser.add_argument("file", help="Packed JSON file to unpack")
    unpack_parser.add_argument("-o", "--output", default=".", help="Output directory (default: .)")

    # -- validate --
    validate_parser = subparsers.add_parser("validate", help="Validate a scene or config JSON file against its schema")
    validate_parser.add_argument("file", help="JSON file to validate")
    validate_parser.add_argument("--schema", choices=["scene", "config"], default=None, help="Force schema type (auto-detected if omitted)")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    try:
        if args.command == "build":
            _cmd_build(args.path)
        elif args.command == "pack":
            _cmd_pack(args.path, args.output)
        elif args.command == "unpack":
            _cmd_unpack(args.file, args.output)
        elif args.command == "validate":
            _cmd_validate(args.file, args.schema)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON — {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


# ─── Build ───────────────────────────────────────────────────────────────────


def _cmd_build(path: str) -> None:
    """Build all outputs for a scene, grouped by mode to avoid redundant work."""
    scene = load_scene(path)
    config = load_config(path)
    outputs = config.get("outputs", [])

    if not outputs:
        print("No outputs defined in config.")
        return

    # Resolve output directory from path
    p = Path(path)
    output_dir = str(p if p.is_dir() else p.parent)

    # Group outputs by mode so we only resolve/render once per mode
    def mode_key(o: dict) -> str:
        return o.get("mode", "dark")

    sorted_outputs = sorted(outputs, key=mode_key)

    total_written: list[str] = []
    for mode, group in groupby(sorted_outputs, key=mode_key):
        group_outputs = list(group)
        print(f"Building mode: {mode} ({len(group_outputs)} output(s))")

        # Deep copy, resolve styles, run pipeline, render
        scene_copy = copy.deepcopy(scene)
        resolve_styles(scene_copy, mode)
        execute_pipeline(scene_copy)
        svg = render_svg(scene_copy)

        # Write all outputs for this mode
        mode_config = {"outputs": group_outputs}
        written = write_outputs(svg, mode_config, output_dir)
        total_written.extend(written)

    print(f"\nDone — {len(total_written)} file(s) written.")


# ─── Validate ───────────────────────────────────────────────────────────────


def _cmd_validate(file: str, schema_type: str | None) -> None:
    """Validate a JSON file against its scene or config schema."""
    file_path = Path(file)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Auto-detect schema type if not forced: presence of "outputs" key means config
    if schema_type is None:
        schema_type = "config" if "outputs" in data else "scene"

    if schema_type == "config":
        errors = validate_config(data)
        label = "config"
    else:
        errors = validate_scene(data)
        label = "scene"

    if errors:
        print(f"Invalid {label} file: {file_path}", file=sys.stderr)
        for err in errors:
            print(f"  {err}", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"Valid {label} file")


# ─── Pack ────────────────────────────────────────────────────────────────────


def _cmd_pack(path: str, output_file: str) -> None:
    """Pack a scene directory into a single self-contained JSON file."""
    scene = load_scene(path)
    packed = pack_scene(scene)

    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(packed, indent=2), encoding="utf-8")
    print(f"Packed scene written to: {out_path}")


def pack_scene(scene: Scene) -> dict:
    """Convert a Scene to a packed JSON-serializable dict.

    Removes imports (already resolved into defs) and assigns IDs
    to elements that lack them for referenceability.
    """
    data = _scene_to_dict(scene)

    # Remove imports — they are already resolved into defs
    data.pop("imports", None)

    # Flatten: assign IDs to elements that don't have one
    _assign_ids(data.get("elements", []))

    return data


def _assign_ids(elements: list[dict], counter: list[int] | None = None) -> None:
    """Recursively assign auto-generated IDs to elements missing one."""
    if counter is None:
        counter = [0]

    for el in elements:
        if not el.get("id"):
            el["id"] = f"el-{counter[0]}"
            counter[0] += 1
        # Recurse into child elements
        if "elements" in el:
            _assign_ids(el["elements"], counter)


# ─── Unpack ──────────────────────────────────────────────────────────────────


def _cmd_unpack(file: str, output_dir: str) -> None:
    """Unpack a packed JSON file into a project directory."""
    file_path = Path(file)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    scene = load_scene(str(file_path))
    unpack_scene(scene, output_dir)


def unpack_scene(scene: Scene, output_dir: str) -> None:
    """Unpack a scene into a directory structure with components/ and main.json."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    imports: dict[str, str] = {}

    # Extract defs into separate component files
    if scene.defs:
        components_dir = out / "components"
        components_dir.mkdir(parents=True, exist_ok=True)

        for name, element in scene.defs.items():
            component_file = f"components/{name}.json"
            component_path = components_dir / f"{name}.json"
            component_data = _element_to_dict(element)
            component_path.write_text(
                json.dumps(component_data, indent=2), encoding="utf-8"
            )
            imports[name] = component_file
            print(f"Extracted component: {component_path}")

    # Build main.json without defs, with imports
    main_data: dict = {
        "width": scene.width,
        "height": scene.height,
    }
    if scene.background:
        main_data["background"] = scene.background
    if scene.styles:
        main_data["styles"] = {
            name: {"light": s.light, "dark": s.dark}
            for name, s in scene.styles.items()
        }
    if imports:
        main_data["imports"] = imports
    if scene.elements:
        main_data["elements"] = [_element_to_dict(el) for el in scene.elements]
    if scene.pipeline:
        main_data["pipeline"] = scene.pipeline

    main_path = out / "main.json"
    main_path.write_text(json.dumps(main_data, indent=2), encoding="utf-8")
    print(f"Wrote: {main_path}")


# ─── Serialization helpers ───────────────────────────────────────────────────


def _scene_to_dict(scene: Scene) -> dict:
    """Convert a Scene back to a JSON-serializable dict."""
    data: dict = {
        "width": scene.width,
        "height": scene.height,
    }
    if scene.background:
        data["background"] = scene.background
    if scene.styles:
        data["styles"] = {
            name: {"light": s.light, "dark": s.dark}
            for name, s in scene.styles.items()
        }
    if scene.imports:
        data["imports"] = scene.imports
    if scene.defs:
        data["defs"] = {name: _element_to_dict(el) for name, el in scene.defs.items()}
    if scene.elements:
        data["elements"] = [_element_to_dict(el) for el in scene.elements]
    if scene.pipeline:
        data["pipeline"] = scene.pipeline
    return data


def _element_to_dict(el: Element) -> dict:
    """Convert an Element back to a JSON-serializable dict.

    Omits default/None values to keep output clean.
    """
    data: dict = {"type": el.type}

    if el.id:
        data["id"] = el.id
    if el.fill:
        data["fill"] = el.fill
    if el.opacity != 1.0:
        data["opacity"] = el.opacity
    if el.transform:
        t: dict = {}
        if el.transform.translate != (0.0, 0.0):
            t["translate"] = list(el.transform.translate)
        if el.transform.scale != (1.0, 1.0):
            t["scale"] = list(el.transform.scale)
        if t:
            data["transform"] = t

    # rect fields
    if el.x != 0:
        data["x"] = el.x
    if el.y != 0:
        data["y"] = el.y
    if el.width != 0:
        data["width"] = el.width
    if el.height != 0:
        data["height"] = el.height

    # path
    if el.d:
        data["d"] = el.d

    # text
    if el.content:
        data["content"] = el.content
    if el.font:
        font_data: dict = {"family": el.font.family, "size": el.font.size}
        if el.font.weight != 400:
            font_data["weight"] = el.font.weight
        data["font"] = font_data
    if el.anchor != "start":
        data["anchor"] = el.anchor
    if el.letter_spacing != 0:
        data["letter_spacing"] = el.letter_spacing
    if el.char_styles:
        data["char_styles"] = [
            _char_style_to_dict(cs) for cs in el.char_styles
        ]

    # group children
    if el.elements:
        data["elements"] = [_element_to_dict(child) for child in el.elements]

    # component reference
    if el.use:
        data["use"] = el.use

    return data


def _char_style_to_dict(cs) -> dict:
    """Convert a CharStyle to a dict, omitting defaults."""
    data: dict = {"chars": cs.chars}
    if cs.opacity != 1.0:
        data["opacity"] = cs.opacity
    if cs.fill:
        data["fill"] = cs.fill
    return data
