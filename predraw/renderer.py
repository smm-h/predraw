"""SVG renderer — converts a resolved Scene into an SVG string."""

from __future__ import annotations

import copy

from .model import CharStyle, Element, Scene, Transform


def render_svg(scene: Scene) -> str:
    """Render a Scene to an SVG string."""
    lines: list[str] = []
    lines.append(
        f'<svg width="{scene.width}" height="{scene.height}" '
        f'viewBox="0 0 {scene.width} {scene.height}" '
        f'xmlns="http://www.w3.org/2000/svg">'
    )

    if scene.background:
        lines.append(
            f'  <rect width="{scene.width}" height="{scene.height}" '
            f'fill="{scene.background}"/>'
        )

    if scene.elements:
        for el in scene.elements:
            lines.append(_render_element(el, scene, indent=2))

    lines.append("</svg>")
    return "\n".join(lines)


def _render_element(el: Element, scene: Scene, indent: int = 2) -> str:
    """Render a single element to SVG string."""
    pad = " " * indent

    if el.type == "background":
        return f'{pad}<rect width="{scene.width}" height="{scene.height}" fill="{el.fill}"/>'

    if el.type == "rect":
        attrs = f'x="{el.x}" y="{el.y}" width="{el.width}" height="{el.height}" fill="{el.fill}"'
        if el.opacity != 1.0:
            attrs += f' opacity="{el.opacity}"'
        return f"{pad}<rect {attrs}/>"

    if el.type == "path":
        attrs = f'd="{el.d}" fill="{el.fill}"'
        if el.opacity != 1.0:
            attrs += f' opacity="{el.opacity}"'
        if el.transform:
            attrs += f' transform="{_render_transform(el.transform)}"'
        return f"{pad}<path {attrs}/>"

    if el.type == "text":
        if el.char_styles:
            return _render_text_with_char_styles(el, indent)
        return _render_plain_text(el, indent)

    if el.type == "group":
        return _render_group(el, scene, indent)

    if el.type == "use" or el.use:
        return _render_use(el, scene, indent)

    return f"{pad}<!-- unknown element type: {el.type} -->"


def _render_transform(t: Transform) -> str:
    """Convert Transform to SVG transform attribute value."""
    parts: list[str] = []
    if t.translate != (0.0, 0.0):
        parts.append(f"translate({t.translate[0]},{t.translate[1]})")
    if t.scale != (1.0, 1.0):
        parts.append(f"scale({t.scale[0]},{t.scale[1]})")
    return " ".join(parts)


def _render_text_with_char_styles(el: Element, indent: int = 2) -> str:
    """Render text element with per-character tspan styling."""
    pad = " " * indent
    content = el.content or ""

    # Build the opening <text> tag
    attrs = f'x="{el.x}" y="{el.y}"'
    if el.fill:
        attrs += f' fill="{el.fill}"'
    if el.font:
        attrs += f' font-family="{el.font.family}" font-size="{el.font.size}" font-weight="{el.font.weight}"'
    attrs += f' text-anchor="{el.anchor}"'
    if el.letter_spacing:
        attrs += f' letter-spacing="{el.letter_spacing}"'

    # Build tspan elements for each character
    tspans: list[str] = []
    for char in content:
        style = _match_char_style(char, el.char_styles or [])
        if style:
            tspan_attrs = ""
            if style.fill:
                tspan_attrs += f' fill="{style.fill}"'
            if style.opacity != 1.0:
                tspan_attrs += f' opacity="{style.opacity}"'
            tspans.append(f"<tspan{tspan_attrs}>{_escape_xml(char)}</tspan>")
        else:
            tspans.append(_escape_xml(char))

    inner = "".join(tspans)
    return f"{pad}<text {attrs}>{inner}</text>"


def _render_plain_text(el: Element, indent: int = 2) -> str:
    """Render a text element without char styles."""
    pad = " " * indent
    attrs = f'x="{el.x}" y="{el.y}"'
    if el.fill:
        attrs += f' fill="{el.fill}"'
    if el.font:
        attrs += f' font-family="{el.font.family}" font-size="{el.font.size}" font-weight="{el.font.weight}"'
    attrs += f' text-anchor="{el.anchor}"'
    if el.letter_spacing:
        attrs += f' letter-spacing="{el.letter_spacing}"'
    content = _escape_xml(el.content or "")
    return f"{pad}<text {attrs}>{content}</text>"


def _render_group(el: Element, scene: Scene, indent: int = 2) -> str:
    """Render a group element with optional transform and children."""
    pad = " " * indent
    tag_open = "<g"
    if el.transform:
        tag_open += f' transform="{_render_transform(el.transform)}"'
    tag_open += ">"

    lines: list[str] = [f"{pad}{tag_open}"]
    if el.elements:
        for child in el.elements:
            lines.append(_render_element(child, scene, indent + 2))
    lines.append(f"{pad}</g>")
    return "\n".join(lines)


def _render_use(el: Element, scene: Scene, indent: int = 2) -> str:
    """Render a component reference by looking up scene.defs."""
    pad = " " * indent
    ref_name = el.use
    if not ref_name or not scene.defs or ref_name not in scene.defs:
        return f'{pad}<!-- unresolved use: {el.use} -->'

    # Deep-copy the target so we never mutate scene.defs
    target = copy.deepcopy(scene.defs[ref_name])

    # Apply property overrides from the use element
    override_fill = el.fill
    override_opacity = el.opacity
    if override_fill is not None or override_opacity != 1.0:
        _apply_overrides(target, override_fill, override_opacity)

    # Wrap in <g> with the use-element's transform if present
    if el.transform:
        lines: list[str] = [f'{pad}<g transform="{_render_transform(el.transform)}">']
        lines.append(_render_element(target, scene, indent + 2))
        lines.append(f"{pad}</g>")
        return "\n".join(lines)

    return _render_element(target, scene, indent)


def _apply_overrides(element: Element, fill: str | None, opacity: float) -> None:
    """Recursively apply fill/opacity overrides to an element tree.

    - fill: replaces child fill entirely (if not None)
    - opacity: multiplies with existing child opacity (if != 1.0)
    """
    if fill is not None and element.fill is not None:
        element.fill = fill
    if opacity != 1.0:
        element.opacity *= opacity

    # Recurse into group children
    if element.elements:
        for child in element.elements:
            _apply_overrides(child, fill, opacity)


def _match_char_style(char: str, styles: list[CharStyle]) -> CharStyle | None:
    """Find the first CharStyle whose chars field contains the given character."""
    for style in styles:
        if char in style.chars:
            return style
    return None


def _escape_xml(text: str) -> str:
    """Escape XML special characters in text content."""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&apos;")
    return text
