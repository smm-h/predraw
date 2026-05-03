"""Data classes representing the predraw element tree."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Style:
    light: str
    dark: str


@dataclass
class Font:
    family: str
    size: float
    weight: int = 400


@dataclass
class Transform:
    translate: tuple[float, float] = (0.0, 0.0)
    scale: tuple[float, float] = (1.0, 1.0)


@dataclass
class GradientStop:
    offset: float  # 0.0 to 1.0
    color: str
    opacity: float = 1.0


@dataclass
class Gradient:
    type: str  # "linear-gradient" or "radial-gradient"
    stops: list[GradientStop]
    # linear-gradient: angle in degrees, 0=left-to-right, 90=top-to-bottom
    angle: float = 0
    # radial-gradient: center and radius (0.0 to 1.0, relative)
    cx: float = 0.5
    cy: float = 0.5
    r: float = 0.5


@dataclass
class CharStyle:
    chars: str  # which characters to match
    opacity: float = 1.0
    fill: str | None = None  # can be a $ref or resolved color


@dataclass
class Element:
    type: str  # "rect", "path", "text", "group", "background"
    id: str | None = None
    # common
    fill: str | Gradient | None = None
    opacity: float = 1.0
    transform: Transform | None = None
    # rect
    x: float = 0
    y: float = 0
    width: float = 0
    height: float = 0
    # path
    d: str | None = None
    # text
    content: str | None = None
    font: Font | None = None
    anchor: str = "start"  # start, middle, end
    letter_spacing: float = 0
    char_styles: list[CharStyle] | None = None
    # group / component
    elements: list[Element] | None = None
    # stroke
    stroke: str | Gradient | None = None
    stroke_width: float | None = None
    stroke_dasharray: str | None = None
    stroke_linecap: str | None = None  # butt, round, square
    stroke_linejoin: str | None = None  # miter, round, bevel
    stroke_opacity: float = 1.0
    # component instantiation — references a def by name
    use: str | None = None


@dataclass
class Scene:
    width: float
    height: float
    background: str | None = None
    styles: dict[str, Style] | None = None
    imports: dict[str, str] | None = None  # alias -> file path
    defs: dict[str, Element] | None = None  # for packed format
    elements: list[Element] | None = None
    pipeline: list[dict] | None = None  # pipeline steps as raw dicts
