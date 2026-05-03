"""Font loading and glyph extraction for text-to-paths conversion.

Uses fonttools to read .ttf/.otf files and extract SVG path data for each glyph.
"""

from __future__ import annotations

import os
import platform
import warnings
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

# Weight keywords to numeric values for font file name matching
_WEIGHT_NAMES: dict[str, int] = {
    "thin": 100,
    "hairline": 100,
    "extralight": 200,
    "ultralight": 200,
    "light": 300,
    "regular": 400,
    "normal": 400,
    "medium": 500,
    "semibold": 600,
    "demibold": 600,
    "bold": 700,
    "extrabold": 800,
    "ultrabold": 800,
    "black": 900,
    "heavy": 900,
}

# Reverse: numeric weight to preferred file name suffix
_WEIGHT_SUFFIXES: dict[int, list[str]] = {
    100: ["Thin", "Hairline"],
    200: ["ExtraLight", "UltraLight"],
    300: ["Light"],
    400: ["Regular", "Normal", ""],
    500: ["Medium"],
    600: ["SemiBold", "DemiBold"],
    700: ["Bold"],
    800: ["ExtraBold", "UltraBold"],
    900: ["Black", "Heavy"],
}


def _font_directories() -> list[Path]:
    """Return platform-appropriate font search directories."""
    dirs: list[Path] = []
    system = platform.system()

    if system == "Linux":
        dirs.append(Path("/usr/share/fonts"))
        dirs.append(Path("/usr/local/share/fonts"))
        home = Path.home()
        dirs.append(home / ".local" / "share" / "fonts")
        dirs.append(home / ".fonts")
    elif system == "Darwin":
        dirs.append(Path("/System/Library/Fonts"))
        dirs.append(Path("/Library/Fonts"))
        dirs.append(Path.home() / "Library" / "Fonts")
    elif system == "Windows":
        windir = os.environ.get("WINDIR", r"C:\Windows")
        dirs.append(Path(windir) / "Fonts")
        dirs.append(Path.home() / "AppData" / "Local" / "Microsoft" / "Windows" / "Fonts")

    return [d for d in dirs if d.exists()]


def find_font(family: str, weight: int = 400, project_dir: str | None = None) -> str | None:
    """Find a font file path for the given family and weight.

    Searches font directories for .ttf/.otf files matching the family
    name and weight. Returns the path to the font file, or None if not found.

    Search order:
    1. {project_dir}/fonts/ (if project_dir is provided and exists)
    2. System font directories
    """
    # Normalize family name for comparison (lowercase, no spaces/hyphens)
    family_normalized = family.lower().replace(" ", "").replace("-", "")

    # Build candidate suffixes for the requested weight
    suffixes = _WEIGHT_SUFFIXES.get(weight, ["Regular"])

    # Build search directories: project fonts first, then system
    search_dirs: list[Path] = []
    if project_dir:
        local_fonts = Path(project_dir) / "fonts"
        if local_fonts.is_dir():
            search_dirs.append(local_fonts)
    search_dirs.extend(_font_directories())

    # Search all font directories
    candidates: list[tuple[int, str]] = []  # (priority, path)

    for font_dir in search_dirs:
        for path in font_dir.rglob("*"):
            if path.suffix.lower() not in (".ttf", ".otf"):
                continue

            stem = path.stem
            stem_lower = stem.lower().replace(" ", "").replace("-", "")

            # Check if the font file name contains the family name
            if family_normalized not in stem_lower:
                continue

            # Score based on weight suffix match
            # Extract the part after the family name
            remainder = stem_lower[stem_lower.index(family_normalized) + len(family_normalized):]

            # Check for weight match in the remainder
            priority = 100  # default: low priority match
            for i, suffix in enumerate(suffixes):
                if suffix.lower() == remainder or suffix.lower() == remainder.lstrip("-_"):
                    priority = i  # exact weight match
                    break
            else:
                # Check if it's a generic weight match
                for wname, wval in _WEIGHT_NAMES.items():
                    if wname in remainder and wval == weight:
                        priority = 10
                        break

            candidates.append((priority, str(path)))

    if not candidates:
        return None

    # Return the best match (lowest priority number)
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]


def get_glyph_paths(
    font_path: str,
    text: str,
    font_size: float,
    letter_spacing: float = 0,
) -> list[dict]:
    """Extract SVG path data for each character in text.

    Returns a list of dicts, one per character:
        {"char": "A", "d": "M10 20 L...", "advance": 33.12}

    Each glyph's path data is scaled to the requested font_size and positioned
    at its correct horizontal offset. Font Y-axis is flipped for SVG.
    """
    font = TTFont(font_path)
    cmap = font.getBestCmap()
    glyph_set = font.getGlyphSet()
    units_per_em = font["head"].unitsPerEm
    scale = font_size / units_per_em

    results: list[dict] = []
    x_offset = 0.0

    for char in text:
        code_point = ord(char)

        # Handle missing glyph
        if code_point not in cmap:
            warnings.warn(f"text-to-paths: no glyph for '{char}' (U+{code_point:04X}), skipping")
            continue

        glyph_name = cmap[code_point]
        advance_raw = font["hmtx"][glyph_name][0]
        advance_scaled = advance_raw * scale

        # Draw the glyph with scaling, Y-flip, and horizontal offset
        svg_pen = SVGPathPen(glyph_set)
        transform_pen = TransformPen(svg_pen, (scale, 0, 0, -scale, x_offset, 0))
        glyph_set[glyph_name].draw(transform_pen)
        path_data = svg_pen.getCommands()

        # Skip empty glyphs (e.g. space) but still advance
        if path_data:
            results.append({
                "char": char,
                "d": path_data,
                "advance": advance_scaled,
            })
        else:
            # Space or other non-drawing glyph: record advance only
            results.append({
                "char": char,
                "d": "",
                "advance": advance_scaled,
            })

        x_offset += advance_scaled + letter_spacing

    font.close()
    return results
