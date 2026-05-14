"""CLI entry point for predraw — strictcli-based with build/pack/unpack subcommands."""

from __future__ import annotations

import copy
import json
import sys
import time
from itertools import groupby
from pathlib import Path

import strictcli

from . import __version__
from .loader import load_config, load_scene, resolve_styles
from .model import Element, Font, Gradient, Scene, Style, Transform
from .output import write_outputs
from .pipeline import execute_pipeline
from .renderer import render_svg
from .validator import validate_config, validate_scene

app = strictcli.App(name="predraw", version=__version__, help="predraw scene builder")


def main():
    """Entry point for the predraw CLI."""
    app.run()


# ─── Build ───────────────────────────────────────────────────────────────────


@app.command(
    "build",
    help="Build scene into output files",
    args=[
        strictcli.Arg(name="path", help="Project directory or scene file (default: .)", required=False, default="."),
    ],
)
@strictcli.flag("dry-run", type=bool, help="Print build plan without writing files")
def _cmd_build(path: str, *, dry_run: bool = False) -> None:
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

    if dry_run:
        # Print the build plan without rendering or writing
        total_outputs = 0
        for mode, group in groupby(sorted_outputs, key=mode_key):
            group_outputs = list(group)
            total_outputs += len(group_outputs)
            print(f"Mode: {mode} ({len(group_outputs)} output(s))")
            for out in group_outputs:
                fmt = out.get("format", "svg")
                filename = out.get("filename", f"output.{fmt}")
                print(f"  {filename} ({fmt})")
        print(f"\n{total_outputs} output(s) across {len(set(o.get('mode', 'dark') for o in outputs))} mode(s).")
        print("Dry run — no files written.")
        return

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


# ─── Pack ────────────────────────────────────────────────────────────────────


@app.command(
    "pack",
    help="Pack a scene directory into a single JSON file",
    args=[
        strictcli.Arg(name="path", help="Project directory or scene file (default: .)", required=False, default="."),
    ],
)
@strictcli.flag("output", short="o", type=str, default="packed.json", help="Output file path (default: packed.json)")
def _cmd_pack(path: str, *, output: str) -> None:
    """Pack a scene directory into a single self-contained JSON file."""
    scene = load_scene(path)
    packed = pack_scene(scene)

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(packed, indent=2), encoding="utf-8")
    print(f"Packed scene written to: {out_path}")


# ─── Unpack ──────────────────────────────────────────────────────────────────


@app.command(
    "unpack",
    help="Unpack a packed JSON file into a project directory",
    args=[
        strictcli.Arg(name="file", help="Packed JSON file to unpack"),
    ],
)
@strictcli.flag("output", short="o", type=str, default=".", help="Output directory (default: .)")
def _cmd_unpack(file: str, *, output: str) -> None:
    """Unpack a packed JSON file into a project directory."""
    file_path = Path(file)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    scene = load_scene(str(file_path))
    unpack_scene(scene, output)


# ─── Init ───────────────────────────────────────────────────────────────────


_STARTER_MAIN = {
    "width": 800,
    "height": 400,
    "styles": {
        "bg": {"light": "#ffffff", "dark": "#1a1a1a"},
        "fg": {"light": "#000000", "dark": "#ffffff"},
    },
    "elements": [
        {"type": "background", "fill": "$bg"},
        {
            "type": "text",
            "id": "title",
            "content": "hello predraw",
            "x": 400,
            "y": 220,
            "anchor": "middle",
            "fill": "$fg",
            "font": {"family": "sans-serif", "size": 64, "weight": 700},
        },
    ],
}

_STARTER_CONFIG = {
    "outputs": [
        {"format": "svg", "path": "output.svg", "mode": "dark"},
        {"format": "png", "path": "output.png", "mode": "dark"},
    ]
}


@app.command(
    "init",
    help="Create a starter project in a directory",
    args=[
        strictcli.Arg(name="path", help="Directory to initialize (default: .)", required=False, default="."),
    ],
)
def _cmd_init(path: str) -> None:
    """Create a starter predraw project in the given directory."""
    target = Path(path)
    main_file = target / "main.json"

    if main_file.exists():
        print(f"Error: {main_file} already exists", file=sys.stderr)
        sys.exit(1)

    target.mkdir(parents=True, exist_ok=True)

    main_file.write_text(json.dumps(_STARTER_MAIN, indent=2), encoding="utf-8")
    config_file = target / "config.json"
    config_file.write_text(json.dumps(_STARTER_CONFIG, indent=2), encoding="utf-8")

    print(f"Created {main_file}")
    print(f"Created {config_file}")


# ─── Watch ──────────────────────────────────────────────────────────────────


def _collect_json_files(project_dir: Path) -> list[Path]:
    """Collect all .json files in the project directory, excluding *.local-only dirs."""
    return [f for f in project_dir.rglob("*.json") if ".local-only" not in str(f)]


def _get_mtimes(files: list[Path]) -> dict[Path, float]:
    """Get mtime for each file, skipping files that disappeared."""
    mtimes: dict[Path, float] = {}
    for f in files:
        try:
            mtimes[f] = f.stat().st_mtime
        except OSError:
            pass
    return mtimes


def _detect_changes(prev_mtimes: dict[Path, float], curr_mtimes: dict[Path, float]) -> bool:
    """Return True if any files were added, removed, or modified."""
    if set(curr_mtimes.keys()) != set(prev_mtimes.keys()):
        return True
    for f, mtime in curr_mtimes.items():
        if prev_mtimes.get(f) != mtime:
            return True
    return False


@app.command(
    "watch",
    help="Watch project files and rebuild on change",
    args=[
        strictcli.Arg(name="path", help="Project directory (default: .)", required=False, default="."),
    ],
)
def _cmd_watch(path: str) -> None:
    """Watch project files and rebuild on change."""
    project_dir = Path(path).resolve()

    if not project_dir.is_dir():
        print(f"Error: {project_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    print(f"Watching {project_dir}/ (Ctrl+C to stop)")

    # Initial mtime snapshot
    files = _collect_json_files(project_dir)
    prev_mtimes = _get_mtimes(files)

    try:
        while True:
            time.sleep(0.5)

            # Rescan files (new files may appear)
            files = _collect_json_files(project_dir)
            curr_mtimes = _get_mtimes(files)

            if _detect_changes(prev_mtimes, curr_mtimes):
                # Debounce: wait 0.3s then re-check for further changes
                time.sleep(0.3)
                files = _collect_json_files(project_dir)
                curr_mtimes = _get_mtimes(files)

                # Rebuild
                try:
                    _cmd_build(str(project_dir))
                    n_files = len(curr_mtimes)
                    print(f"Rebuilt ({n_files} files)")
                except Exception as e:
                    print(f"Build error: {e}", file=sys.stderr)

                prev_mtimes = curr_mtimes
    except KeyboardInterrupt:
        print("\nStopped.")


# ─── Validate ───────────────────────────────────────────────────────────────


@app.command(
    "validate",
    help="Validate a scene or config JSON file against its schema",
    args=[
        strictcli.Arg(name="file", help="JSON file to validate"),
    ],
)
@strictcli.flag("schema", type=str, default="", choices=["scene", "config", ""], help="Force schema type (auto-detected if omitted)")
def _cmd_validate(file: str, *, schema: str) -> None:
    """Validate a JSON file against its scene or config schema."""
    file_path = Path(file)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Auto-detect schema type if not forced: presence of "outputs" key means config
    schema_type = schema if schema else ("config" if "outputs" in data else "scene")

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
        data["fill"] = _gradient_to_dict(el.fill) if isinstance(el.fill, Gradient) else el.fill
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

    # stroke
    if el.stroke is not None:
        data["stroke"] = _gradient_to_dict(el.stroke) if isinstance(el.stroke, Gradient) else el.stroke
    if el.stroke_width is not None:
        data["strokeWidth"] = el.stroke_width
    if el.stroke_dasharray is not None:
        data["strokeDasharray"] = el.stroke_dasharray
    if el.stroke_linecap is not None:
        data["strokeLinecap"] = el.stroke_linecap
    if el.stroke_linejoin is not None:
        data["strokeLinejoin"] = el.stroke_linejoin
    if el.stroke_opacity != 1.0:
        data["strokeOpacity"] = el.stroke_opacity

    # component reference
    if el.use:
        data["use"] = el.use

    return data


def _gradient_to_dict(grad: Gradient) -> dict:
    """Convert a Gradient to a JSON-serializable dict, omitting defaults."""
    data: dict = {"type": grad.type}
    if grad.type == "linear-gradient":
        if grad.angle != 0:
            data["angle"] = grad.angle
    elif grad.type == "radial-gradient":
        if grad.cx != 0.5:
            data["cx"] = grad.cx
        if grad.cy != 0.5:
            data["cy"] = grad.cy
        if grad.r != 0.5:
            data["r"] = grad.r
    data["stops"] = []
    for stop in grad.stops:
        stop_data: dict = {"offset": stop.offset, "color": stop.color}
        if stop.opacity != 1.0:
            stop_data["opacity"] = stop.opacity
        data["stops"].append(stop_data)
    return data


def _char_style_to_dict(cs) -> dict:
    """Convert a CharStyle to a dict, omitting defaults."""
    data: dict = {"chars": cs.chars}
    if cs.opacity != 1.0:
        data["opacity"] = cs.opacity
    if cs.fill:
        data["fill"] = cs.fill
    return data
