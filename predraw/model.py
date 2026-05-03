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
class CharStyle:
    chars: str  # which characters to match
    opacity: float = 1.0
    fill: str | None = None  # can be a $ref or resolved color


@dataclass
class Element:
    type: str  # "rect", "path", "text", "group", "background"
    id: str | None = None
    # common
    fill: str | None = None
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
