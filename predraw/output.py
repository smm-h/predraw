"""Output generator: converts SVG content to various file formats."""

import io
from pathlib import Path

import cairosvg
from PIL import Image


def write_outputs(svg_content: str, config: dict, output_dir: str) -> list[str]:
    """Write all outputs defined in config, returning list of written file paths.

    config is the parsed config.json dict with an "outputs" list like:
    [
        {"format": "svg", "path": "out/social.svg"},
        {"format": "png", "path": "out/social.png"},
        {"format": "webp", "path": "out/social.webp", "quality": 90}
    ]

    output_dir is the base directory for resolving relative paths.
    """
    written: list[str] = []
    base = Path(output_dir)

    for entry in config.get("outputs", []):
        fmt = entry.get("format", "")
        raw_path = entry.get("path", "")
        path = base / raw_path

        # Ensure parent directories exist
        path.parent.mkdir(parents=True, exist_ok=True)

        if fmt == "svg":
            _write_svg(svg_content, str(path))
        elif fmt == "png":
            _write_png(svg_content, str(path))
        elif fmt == "webp":
            quality = entry.get("quality", 90)
            _write_webp(svg_content, str(path), quality=quality)
        else:
            print(f"Warning: unknown format '{fmt}', skipping")
            continue

        print(f"Wrote: {path}")
        written.append(str(path))

    return written


def _write_svg(svg_content: str, path: str) -> None:
    """Write SVG string to file."""
    Path(path).write_text(svg_content, encoding="utf-8")


def _write_png(svg_content: str, path: str) -> None:
    """Convert SVG to PNG using cairosvg and write to file."""
    cairosvg.svg2png(bytestring=svg_content.encode(), write_to=path)


def _write_webp(svg_content: str, path: str, quality: int = 90) -> None:
    """Convert SVG to PNG via cairosvg, then convert to WebP via Pillow."""
    png_bytes = cairosvg.svg2png(bytestring=svg_content.encode())
    image = Image.open(io.BytesIO(png_bytes))
    image.save(path, "WEBP", quality=quality)
