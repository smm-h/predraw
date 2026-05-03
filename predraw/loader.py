"""Load and resolve a predraw project from JSON files."""

from __future__ import annotations

import json
from pathlib import Path

from .model import CharStyle, Element, Font, Gradient, GradientStop, Scene, Style, Transform


def load_scene(path: str) -> Scene:
    """Load a scene from a file or directory.

    If path is a directory, looks for main.json.
    If path is a file, loads it directly.
    """
    p = Path(path)
    if p.is_dir():
        scene_file = p / "main.json"
    else:
        scene_file = p

    data = _load_json(scene_file)
    base_dir = str(scene_file.parent)
    scene = _parse_scene(data, base_dir)
    _resolve_imports(scene, base_dir)
    return scene


def _load_json(path: Path) -> dict:
    """Load and parse a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


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
    cs_key = "charStyles" if "charStyles" in data else "char_styles"
    if cs_key in data:
        char_styles = [
            CharStyle(
                chars=cs["chars"],
                opacity=cs.get("opacity", 1.0),
                fill=cs.get("fill"),
            )
            for cs in data[cs_key]
        ]

    child_elements = None
    children_key = "elements" if "elements" in data else "children" if "children" in data else None
    if children_key:
        child_elements = [_parse_element(el) for el in data[children_key]]

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
        letter_spacing=data.get("letterSpacing", data.get("letter_spacing", 0)),
        char_styles=char_styles,
        elements=child_elements,
        stroke=stroke,
        stroke_width=data.get("strokeWidth", data.get("stroke_width")),
        stroke_dasharray=data.get("strokeDasharray", data.get("stroke_dasharray")),
        stroke_linecap=data.get("strokeLinecap", data.get("stroke_linecap")),
        stroke_linejoin=data.get("strokeLinejoin", data.get("stroke_linejoin")),
        stroke_opacity=data.get("strokeOpacity", data.get("stroke_opacity", 1.0)),
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
        data = _load_json(full_path)
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
    """Load config.json from a directory or return defaults."""
    p = Path(path)
    if p.is_file():
        p = p.parent

    config_file = p / "config.json"
    if config_file.exists():
        return _load_json(config_file)

    return {"outputs": [{"format": "svg", "path": "output.svg"}]}
