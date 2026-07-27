"""Load and resolve a predraw project from JSON files."""

from __future__ import annotations

import json
from pathlib import Path

from .model import CharStyle, Element, Font, Gradient, GradientStop, Scene, Style, Transform
from .validator import ensure_valid_config, ensure_valid_scene

# camelCase canonical spelling -> its snake_case alias. These are the strictspec
# `aliases` declared on the scene schema (predraw/schema/scene.schema.toml). strictspec
# owns alias correctness: it rejects a document that carries BOTH spellings
# (STRICTSPEC_ALIAS_BOTH_PRESENT), so once validation passes at most one spelling of
# each pair is present and the rewrite below is unambiguous. This single write-side
# canonicalization replaces the per-field fallbacks the loader used to hand-roll.
_ALIAS_TO_CANONICAL = {
    "stroke_width": "strokeWidth",
    "stroke_dasharray": "strokeDasharray",
    "stroke_linecap": "strokeLinecap",
    "stroke_linejoin": "strokeLinejoin",
    "stroke_opacity": "strokeOpacity",
    "letter_spacing": "letterSpacing",
    "char_styles": "charStyles",
    "children": "elements",
}


def load_scene(path: str) -> Scene:
    """Load a scene from a file or directory.

    If path is a directory, looks for main.json.
    If path is a file, loads it directly.

    The document is validated against the strictspec scene schema before parsing
    (version gate + full structural validation); an invalid document raises
    SchemaValidationError.
    """
    p = Path(path)
    if p.is_dir():
        scene_file = p / "main.json"
    else:
        scene_file = p

    raw = scene_file.read_bytes()
    ensure_valid_scene(raw)
    data = _canonicalize_aliases(json.loads(raw))
    base_dir = str(scene_file.parent)
    scene = _parse_scene(data, base_dir)
    _resolve_imports(scene, base_dir)
    return scene


def _load_json(path: Path) -> dict:
    """Load and parse a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _canonicalize_aliases(node):
    """Recursively rewrite alias spellings to their canonical camelCase form.

    Runs after strictspec validation, which guarantees no alias pair has both
    spellings present, so each rename is unambiguous. After this pass the parser
    reads canonical keys only.
    """
    if isinstance(node, dict):
        out = {}
        for key, value in node.items():
            out[_ALIAS_TO_CANONICAL.get(key, key)] = _canonicalize_aliases(value)
        return out
    if isinstance(node, list):
        return [_canonicalize_aliases(item) for item in node]
    return node


def _parse_scene(data: dict, base_dir: str) -> Scene:
    """Parse raw JSON dict into a Scene, resolving imports."""
    styles = None
    if "styles" in data:
        styles = {
            name: Style(light=s["light"], dark=s["dark"])
            for name, s in data["styles"].items()
        }

    defs = None
    if "defs" in data:
        defs = {name: _parse_element(el) for name, el in data["defs"].items()}

    elements = None
    if "elements" in data:
        elements = [_parse_element(el) for el in data["elements"]]

    return Scene(
        width=data["width"],
        height=data["height"],
        format_version=data["format_version"],
        background=data.get("background"),
        styles=styles,
        imports=data.get("imports"),
        defs=defs,
        elements=elements,
        pipeline=data.get("pipeline"),
    )


def _parse_element(data: dict) -> Element:
    """Parse a raw JSON dict into an Element."""
    transform = None
    if "transform" in data:
        t = data["transform"]
        transform = Transform(
            translate=tuple(t.get("translate", [0.0, 0.0])),
            scale=tuple(t.get("scale", [1.0, 1.0])),
        )

    font = None
    if "font" in data:
        f = data["font"]
        font = Font(
            family=f["family"],
            size=f["size"],
            weight=f.get("weight", 400),
        )

    char_styles = None
    if "charStyles" in data:
        char_styles = [
            CharStyle(
                chars=cs["chars"],
                opacity=cs.get("opacity", 1.0),
                fill=cs.get("fill"),
            )
            for cs in data["charStyles"]
        ]

    child_elements = None
    if "elements" in data:
        child_elements = [_parse_element(el) for el in data["elements"]]

    # Parse fill: can be a string (color/$ref) or a dict (gradient)
    fill_raw = data.get("fill")
    fill = _parse_gradient(fill_raw) if isinstance(fill_raw, dict) else fill_raw

    # Parse stroke: can be a string or a dict (gradient)
    stroke_raw = data.get("stroke")
    stroke = _parse_gradient(stroke_raw) if isinstance(stroke_raw, dict) else stroke_raw

    return Element(
        type=data.get("type", "use" if "use" in data else "group"),
        id=data.get("id"),
        fill=fill,
        opacity=data.get("opacity", 1.0),
        transform=transform,
        x=data.get("x", 0),
        y=data.get("y", 0),
        width=data.get("width", 0),
        height=data.get("height", 0),
        d=data.get("d"),
        content=data.get("content"),
        font=font,
        anchor=data.get("anchor", "start"),
        letter_spacing=data.get("letterSpacing", 0),
        char_styles=char_styles,
        elements=child_elements,
        stroke=stroke,
        stroke_width=data.get("strokeWidth"),
        stroke_dasharray=data.get("strokeDasharray"),
        stroke_linecap=data.get("strokeLinecap"),
        stroke_linejoin=data.get("strokeLinejoin"),
        stroke_opacity=data.get("strokeOpacity", 1.0),
        use=data.get("use"),
    )


def _parse_gradient(data: dict) -> Gradient:
    """Parse a gradient dict into a Gradient object."""
    stops = [
        GradientStop(
            offset=s["offset"],
            color=s["color"],
            opacity=s.get("opacity", 1.0),
        )
        for s in data.get("stops", [])
    ]
    return Gradient(
        type=data["type"],
        stops=stops,
        angle=data.get("angle", 0),
        cx=data.get("cx", 0.5),
        cy=data.get("cy", 0.5),
        r=data.get("r", 0.5),
    )


def _resolve_imports(scene: Scene, base_dir: str) -> None:
    """Load imported component files and store in scene.defs."""
    if not scene.imports:
        return

    if scene.defs is None:
        scene.defs = {}

    base = Path(base_dir)
    for alias, file_path in scene.imports.items():
        full_path = base / file_path
        # Imported components are standalone Element documents (not scenes), so they
        # are not gated by the scene schema; still canonicalize their alias spellings
        # so the parser sees canonical keys only.
        data = _canonicalize_aliases(_load_json(full_path))
        scene.defs[alias] = _parse_element(data)


def resolve_styles(scene: Scene, mode: str = "dark") -> Scene:
    """Resolve all $ref style tokens in the scene for the given mode.

    Walks all elements, replaces any fill value starting with "$"
    with the resolved color from scene.styles for the given mode.
    """
    if not scene.styles:
        return scene

    if scene.elements:
        for element in scene.elements:
            _resolve_element_styles(element, scene.styles, mode)

    if scene.defs:
        for element in scene.defs.values():
            _resolve_element_styles(element, scene.styles, mode)

    return scene


def _resolve_element_styles(
    element: Element, styles: dict[str, Style], mode: str
) -> None:
    """Recursively resolve style references in an element."""
    # Only resolve string fills (skip Gradient objects)
    if isinstance(element.fill, str) and element.fill.startswith("$"):
        style_name = element.fill[1:]  # strip the leading $
        if style_name in styles:
            style = styles[style_name]
            element.fill = style.dark if mode == "dark" else style.light

    # Resolve stroke style token (skip Gradient objects)
    if isinstance(element.stroke, str) and element.stroke.startswith("$"):
        style_name = element.stroke[1:]
        if style_name in styles:
            style = styles[style_name]
            element.stroke = style.dark if mode == "dark" else style.light

    # Resolve char_styles fills
    if element.char_styles:
        for cs in element.char_styles:
            if cs.fill and cs.fill.startswith("$"):
                style_name = cs.fill[1:]
                if style_name in styles:
                    style = styles[style_name]
                    cs.fill = style.dark if mode == "dark" else style.light

    # Recurse into child elements
    if element.elements:
        for child in element.elements:
            _resolve_element_styles(child, styles, mode)


def load_config(path: str) -> dict:
    """Load config.json from a directory or return defaults.

    When a config.json is present it is validated against the strictspec config
    schema (version gate + full validation) before being returned; an invalid
    config raises SchemaValidationError. When absent, the in-memory default is
    returned as-is.
    """
    p = Path(path)
    if p.is_file():
        p = p.parent

    config_file = p / "config.json"
    if config_file.exists():
        raw = config_file.read_bytes()
        ensure_valid_config(raw)
        return json.loads(raw)

    return {"format_version": 1, "outputs": [{"format": "svg", "path": "output.svg"}]}
