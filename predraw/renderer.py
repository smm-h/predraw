"""SVG renderer — converts a resolved Scene into an SVG string."""

from __future__ import annotations

import copy
import math

from .model import CharStyle, Element, Gradient, Scene, Transform


def render_svg(scene: Scene) -> str:
    """Render a Scene to an SVG string."""
    # Collect all unique gradient objects used in the scene and assign IDs
    gradient_list = _collect_gradients(scene)

    lines: list[str] = []
    lines.append(
        f'<svg width="{scene.width}" height="{scene.height}" '
        f'viewBox="0 0 {scene.width} {scene.height}" '
        f'xmlns="http://www.w3.org/2000/svg">'
    )

    # Render <defs> block if there are gradients
    if gradient_list:
        lines.append(_render_defs(gradient_list))

    if scene.background:
        lines.append(
            f'  <rect width="{scene.width}" height="{scene.height}" '
            f'fill="{scene.background}"/>'
        )

    if scene.elements:
        for el in scene.elements:
            lines.append(_render_element(el, scene, indent=2, gradient_list=gradient_list))

    lines.append("</svg>")
    return "\n".join(lines)


def _stroke_attrs(el: Element, gradient_list: list | None = None) -> str:
    """Build SVG stroke attribute string from element stroke fields."""
    parts: list[str] = []
    if el.stroke is not None:
        parts.append(f'stroke="{_fill_value(el.stroke, gradient_list)}"')
    if el.stroke_width is not None:
        parts.append(f'stroke-width="{el.stroke_width}"')
    if el.stroke_dasharray is not None:
        parts.append(f'stroke-dasharray="{el.stroke_dasharray}"')
    if el.stroke_linecap is not None:
        parts.append(f'stroke-linecap="{el.stroke_linecap}"')
    if el.stroke_linejoin is not None:
        parts.append(f'stroke-linejoin="{el.stroke_linejoin}"')
    if el.stroke_opacity != 1.0:
        parts.append(f'stroke-opacity="{el.stroke_opacity}"')
    if parts:
        return " " + " ".join(parts)
    return ""


def _render_element(el: Element, scene: Scene, indent: int = 2, gradient_list: list | None = None) -> str:
    """Render a single element to SVG string."""
    pad = " " * indent

    if el.type == "background":
        fill_val = _fill_value(el.fill, gradient_list)
        return f'{pad}<rect width="{scene.width}" height="{scene.height}" fill="{fill_val}"/>'

    if el.type == "rect":
        fill_val = _fill_value(el.fill, gradient_list)
        attrs = f'x="{el.x}" y="{el.y}" width="{el.width}" height="{el.height}" fill="{fill_val}"'
        if el.opacity != 1.0:
            attrs += f' opacity="{el.opacity}"'
        attrs += _stroke_attrs(el, gradient_list)
        return f"{pad}<rect {attrs}/>"

    if el.type == "path":
        fill_val = _fill_value(el.fill, gradient_list)
        attrs = f'd="{el.d}" fill="{fill_val}"'
        if el.opacity != 1.0:
            attrs += f' opacity="{el.opacity}"'
        if el.transform:
            attrs += f' transform="{_render_transform(el.transform)}"'
        attrs += _stroke_attrs(el, gradient_list)
        return f"{pad}<path {attrs}/>"

    if el.type == "text":
        if el.char_styles:
            return _render_text_with_char_styles(el, indent, gradient_list)
        return _render_plain_text(el, indent, gradient_list)

    if el.type == "group":
        return _render_group(el, scene, indent, gradient_list)

    if el.type == "use" or el.use:
        return _render_use(el, scene, indent, gradient_list)

    return f"{pad}<!-- unknown element type: {el.type} -->"


def _render_transform(t: Transform) -> str:
    """Convert Transform to SVG transform attribute value."""
    parts: list[str] = []
    if t.translate != (0.0, 0.0):
        parts.append(f"translate({t.translate[0]},{t.translate[1]})")
    if t.scale != (1.0, 1.0):
        parts.append(f"scale({t.scale[0]},{t.scale[1]})")
    return " ".join(parts)


def _render_text_with_char_styles(el: Element, indent: int = 2, gradient_list: list | None = None) -> str:
    """Render text element with per-character tspan styling."""
    pad = " " * indent
    content = el.content or ""

    # Build the opening <text> tag
    attrs = f'x="{el.x}" y="{el.y}"'
    if el.fill:
        attrs += f' fill="{_fill_value(el.fill, gradient_list)}"'
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

    attrs += _stroke_attrs(el, gradient_list)
    inner = "".join(tspans)
    return f"{pad}<text {attrs}>{inner}</text>"


def _render_plain_text(el: Element, indent: int = 2, gradient_list: list | None = None) -> str:
    """Render a text element without char styles."""
    pad = " " * indent
    attrs = f'x="{el.x}" y="{el.y}"'
    if el.fill:
        attrs += f' fill="{_fill_value(el.fill, gradient_list)}"'
    if el.font:
        attrs += f' font-family="{el.font.family}" font-size="{el.font.size}" font-weight="{el.font.weight}"'
    attrs += f' text-anchor="{el.anchor}"'
    if el.letter_spacing:
        attrs += f' letter-spacing="{el.letter_spacing}"'
    attrs += _stroke_attrs(el, gradient_list)
    content = _escape_xml(el.content or "")
    return f"{pad}<text {attrs}>{content}</text>"


def _render_group(el: Element, scene: Scene, indent: int = 2, gradient_list: list | None = None) -> str:
    """Render a group element with optional transform and children."""
    pad = " " * indent
    tag_open = "<g"
    if el.transform:
        tag_open += f' transform="{_render_transform(el.transform)}"'
    tag_open += _stroke_attrs(el, gradient_list)
    tag_open += ">"

    lines: list[str] = [f"{pad}{tag_open}"]
    if el.elements:
        for child in el.elements:
            lines.append(_render_element(child, scene, indent + 2, gradient_list))
    lines.append(f"{pad}</g>")
    return "\n".join(lines)


def _render_use(el: Element, scene: Scene, indent: int = 2, gradient_list: list | None = None) -> str:
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
        lines.append(_render_element(target, scene, indent + 2, gradient_list))
        lines.append(f"{pad}</g>")
        return "\n".join(lines)

    return _render_element(target, scene, indent, gradient_list)


def _apply_overrides(element: Element, fill: str | Gradient | None, opacity: float) -> None:
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


# ─── Gradient helpers ─────────────────────────────────────────────────────────


def _collect_gradients(scene: Scene) -> list[tuple[Gradient, str]]:
    """Walk the scene tree and collect unique Gradient objects, assigning IDs.

    Uses dataclass equality to deduplicate gradients (identical gradients share
    one ID). Returns a list of (Gradient, grad_id) tuples for all unique gradients.
    """
    unique: list[Gradient] = []
    counter = [0]

    def _register(grad: Gradient) -> None:
        """Add gradient to unique list if not already present (by equality)."""
        if grad not in unique:
            unique.append(grad)
            counter[0] += 1

    def _visit_element(el: Element) -> None:
        """Recursively visit an element and register its gradients."""
        if isinstance(el.fill, Gradient):
            _register(el.fill)
        if isinstance(el.stroke, Gradient):
            _register(el.stroke)
        if el.elements:
            for child in el.elements:
                _visit_element(child)

    if scene.elements:
        for el in scene.elements:
            _visit_element(el)
    if scene.defs:
        for el in scene.defs.values():
            _visit_element(el)

    return [(grad, f"grad-{i}") for i, grad in enumerate(unique)]


def _render_defs(gradient_list: list[tuple[Gradient, str]]) -> str:
    """Render the <defs> SVG block containing all gradient definitions."""
    lines: list[str] = ["  <defs>"]
    for grad, grad_id in gradient_list:
        if grad.type == "linear-gradient":
            lines.append(_render_linear_gradient(grad, grad_id))
        elif grad.type == "radial-gradient":
            lines.append(_render_radial_gradient(grad, grad_id))
    lines.append("  </defs>")
    return "\n".join(lines)


def _render_linear_gradient(grad: Gradient, grad_id: str) -> str:
    """Render a linearGradient SVG element."""
    # Convert angle to x1/y1/x2/y2 coordinates (percentages)
    rad = math.radians(grad.angle)
    x1 = 50 - 50 * math.cos(rad)
    y1 = 50 - 50 * math.sin(rad)
    x2 = 50 + 50 * math.cos(rad)
    y2 = 50 + 50 * math.sin(rad)

    lines: list[str] = [
        f'    <linearGradient id="{grad_id}" '
        f'x1="{x1:.1f}%" y1="{y1:.1f}%" x2="{x2:.1f}%" y2="{y2:.1f}%">'
    ]
    for stop in grad.stops:
        stop_attrs = f'offset="{stop.offset}" stop-color="{stop.color}"'
        if stop.opacity != 1.0:
            stop_attrs += f' stop-opacity="{stop.opacity}"'
        lines.append(f"      <stop {stop_attrs}/>")
    lines.append("    </linearGradient>")
    return "\n".join(lines)


def _render_radial_gradient(grad: Gradient, grad_id: str) -> str:
    """Render a radialGradient SVG element."""
    # cx/cy/r are 0-1 relative values; convert to percentages for SVG
    cx_pct = grad.cx * 100
    cy_pct = grad.cy * 100
    r_pct = grad.r * 100

    lines: list[str] = [
        f'    <radialGradient id="{grad_id}" '
        f'cx="{cx_pct:.1f}%" cy="{cy_pct:.1f}%" r="{r_pct:.1f}%">'
    ]
    for stop in grad.stops:
        stop_attrs = f'offset="{stop.offset}" stop-color="{stop.color}"'
        if stop.opacity != 1.0:
            stop_attrs += f' stop-opacity="{stop.opacity}"'
        lines.append(f"      <stop {stop_attrs}/>")
    lines.append("    </radialGradient>")
    return "\n".join(lines)


def _fill_value(fill, gradient_list: list[tuple[Gradient, str]] | None = None) -> str:
    """Return the SVG fill attribute value: either a color string or url(#id) reference.

    Uses equality-based lookup so deep-copied Gradient objects still resolve correctly.
    """
    if isinstance(fill, Gradient) and gradient_list:
        for grad, grad_id in gradient_list:
            if grad == fill:
                return f"url(#{grad_id})"
    # For plain strings or if gradient not found in mapping, return as-is
    return str(fill) if fill is not None else "none"
