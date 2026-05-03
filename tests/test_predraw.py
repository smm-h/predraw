"""Comprehensive test suite for predraw."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from predraw.cli import pack_scene, unpack_scene
from predraw.fonts import find_font, get_glyph_paths
from predraw.loader import load_config, load_scene, resolve_styles
from predraw.model import CharStyle, Element, Font, Scene, Style, Transform
from predraw.output import write_outputs
from predraw.pipeline import execute_pipeline
from predraw.renderer import render_svg

# ─── Helpers ────────────────────────────────────────────────────────────────────


def _make_scene(
    width: float = 200,
    height: float = 100,
    background: str | None = None,
    elements: list[Element] | None = None,
    styles: dict[str, Style] | None = None,
    defs: dict[str, Element] | None = None,
    pipeline: list[dict] | None = None,
) -> Scene:
    """Create a Scene with sensible defaults for testing."""
    return Scene(
        width=width,
        height=height,
        background=background,
        elements=elements,
        styles=styles,
        defs=defs,
        pipeline=pipeline,
    )


def _make_rect(
    id: str | None = None,
    x: float = 0,
    y: float = 0,
    width: float = 50,
    height: float = 30,
    fill: str = "#ff0000",
    opacity: float = 1.0,
) -> Element:
    """Create a rect Element."""
    return Element(type="rect", id=id, x=x, y=y, width=width, height=height, fill=fill, opacity=opacity)


def _make_text(
    id: str | None = None,
    content: str = "Hello",
    x: float = 10,
    y: float = 20,
    fill: str = "#000000",
    font: Font | None = None,
    anchor: str = "start",
    char_styles: list[CharStyle] | None = None,
) -> Element:
    """Create a text Element."""
    return Element(
        type="text",
        id=id,
        content=content,
        x=x,
        y=y,
        fill=fill,
        font=font or Font(family="Liberation Sans", size=24),
        anchor=anchor,
        char_styles=char_styles,
    )


def _make_path(
    id: str | None = None,
    d: str = "M0 0 L10 10",
    fill: str = "#00ff00",
    opacity: float = 1.0,
    transform: Transform | None = None,
) -> Element:
    """Create a path Element."""
    return Element(type="path", id=id, d=d, fill=fill, opacity=opacity, transform=transform)


# Detect Liberation Sans availability once for skipif decorators
_LIBERATION_SANS_PATH = find_font("Liberation Sans", 400)
_HAS_LIBERATION_SANS = _LIBERATION_SANS_PATH is not None


# ─── Loader tests ──────────────────────────────────────────────────────────────


class TestLoader:
    def test_load_scene_from_file(self, tmp_path: Path):
        """Load a JSON file directly."""
        scene_data = {"width": 400, "height": 300, "elements": []}
        scene_file = tmp_path / "scene.json"
        scene_file.write_text(json.dumps(scene_data), encoding="utf-8")

        scene = load_scene(str(scene_file))

        assert scene.width == 400
        assert scene.height == 300
        assert scene.elements == []

    def test_load_scene_from_directory(self, tmp_path: Path):
        """Load from dir with main.json."""
        scene_data = {"width": 800, "height": 600, "background": "#111"}
        main_file = tmp_path / "main.json"
        main_file.write_text(json.dumps(scene_data), encoding="utf-8")

        scene = load_scene(str(tmp_path))

        assert scene.width == 800
        assert scene.height == 600
        assert scene.background == "#111"

    def test_parse_element_rect(self, tmp_path: Path):
        """Parse a rect element."""
        scene_data = {
            "width": 100,
            "height": 100,
            "elements": [
                {"type": "rect", "x": 10, "y": 20, "width": 50, "height": 30, "fill": "#abc"}
            ],
        }
        f = tmp_path / "scene.json"
        f.write_text(json.dumps(scene_data), encoding="utf-8")

        scene = load_scene(str(f))

        el = scene.elements[0]
        assert el.type == "rect"
        assert el.x == 10
        assert el.y == 20
        assert el.width == 50
        assert el.height == 30
        assert el.fill == "#abc"

    def test_parse_element_path(self, tmp_path: Path):
        """Parse a path with transform."""
        scene_data = {
            "width": 100,
            "height": 100,
            "elements": [
                {
                    "type": "path",
                    "d": "M0 0 L50 50",
                    "fill": "#f00",
                    "transform": {"translate": [10, 20], "scale": [2.0, 2.0]},
                }
            ],
        }
        f = tmp_path / "scene.json"
        f.write_text(json.dumps(scene_data), encoding="utf-8")

        scene = load_scene(str(f))

        el = scene.elements[0]
        assert el.type == "path"
        assert el.d == "M0 0 L50 50"
        assert el.transform is not None
        assert el.transform.translate == (10, 20)
        assert el.transform.scale == (2.0, 2.0)

    def test_parse_element_text(self, tmp_path: Path):
        """Parse text with font and charStyles (camelCase)."""
        scene_data = {
            "width": 100,
            "height": 100,
            "elements": [
                {
                    "type": "text",
                    "content": "Hi",
                    "x": 5,
                    "y": 15,
                    "fill": "#000",
                    "font": {"family": "Arial", "size": 16, "weight": 700},
                    "charStyles": [
                        {"chars": "H", "opacity": 0.5, "fill": "#f00"},
                    ],
                }
            ],
        }
        f = tmp_path / "scene.json"
        f.write_text(json.dumps(scene_data), encoding="utf-8")

        scene = load_scene(str(f))

        el = scene.elements[0]
        assert el.type == "text"
        assert el.content == "Hi"
        assert el.font.family == "Arial"
        assert el.font.size == 16
        assert el.font.weight == 700
        assert el.char_styles is not None
        assert len(el.char_styles) == 1
        assert el.char_styles[0].chars == "H"
        assert el.char_styles[0].opacity == 0.5
        assert el.char_styles[0].fill == "#f00"

    def test_parse_use_element_no_type(self, tmp_path: Path):
        """Parse {"use": "x"} without explicit type."""
        scene_data = {
            "width": 100,
            "height": 100,
            "elements": [{"use": "mycomp"}],
        }
        f = tmp_path / "scene.json"
        f.write_text(json.dumps(scene_data), encoding="utf-8")

        scene = load_scene(str(f))

        el = scene.elements[0]
        assert el.type == "use"
        assert el.use == "mycomp"

    def test_children_alias(self, tmp_path: Path):
        """Parse group with 'children' key instead of 'elements'."""
        scene_data = {
            "width": 100,
            "height": 100,
            "elements": [
                {
                    "type": "group",
                    "children": [
                        {"type": "rect", "x": 0, "y": 0, "width": 10, "height": 10, "fill": "#000"}
                    ],
                }
            ],
        }
        f = tmp_path / "scene.json"
        f.write_text(json.dumps(scene_data), encoding="utf-8")

        scene = load_scene(str(f))

        group = scene.elements[0]
        assert group.type == "group"
        assert group.elements is not None
        assert len(group.elements) == 1
        assert group.elements[0].type == "rect"

    def test_resolve_imports(self, tmp_path: Path):
        """Create a component file, import it, verify it lands in defs."""
        # Create component file
        comp_dir = tmp_path / "components"
        comp_dir.mkdir()
        comp_data = {"type": "rect", "x": 0, "y": 0, "width": 20, "height": 20, "fill": "#0f0"}
        (comp_dir / "box.json").write_text(json.dumps(comp_data), encoding="utf-8")

        # Create scene that imports it
        scene_data = {
            "width": 100,
            "height": 100,
            "imports": {"box": "components/box.json"},
            "elements": [{"use": "box"}],
        }
        (tmp_path / "main.json").write_text(json.dumps(scene_data), encoding="utf-8")

        scene = load_scene(str(tmp_path))

        assert scene.defs is not None
        assert "box" in scene.defs
        assert scene.defs["box"].type == "rect"
        assert scene.defs["box"].fill == "#0f0"

    def test_resolve_styles_dark(self, tmp_path: Path):
        """$style tokens resolve to dark mode values."""
        scene_data = {
            "width": 100,
            "height": 100,
            "styles": {"fg": {"light": "#000", "dark": "#fff"}},
            "elements": [{"type": "rect", "fill": "$fg", "width": 10, "height": 10}],
        }
        f = tmp_path / "scene.json"
        f.write_text(json.dumps(scene_data), encoding="utf-8")

        scene = load_scene(str(f))
        resolve_styles(scene, "dark")

        assert scene.elements[0].fill == "#fff"

    def test_resolve_styles_light(self, tmp_path: Path):
        """$style tokens resolve to light mode values."""
        scene_data = {
            "width": 100,
            "height": 100,
            "styles": {"fg": {"light": "#111", "dark": "#eee"}},
            "elements": [{"type": "rect", "fill": "$fg", "width": 10, "height": 10}],
        }
        f = tmp_path / "scene.json"
        f.write_text(json.dumps(scene_data), encoding="utf-8")

        scene = load_scene(str(f))
        resolve_styles(scene, "light")

        assert scene.elements[0].fill == "#111"

    def test_load_config_defaults(self, tmp_path: Path):
        """Loading from dir without config.json returns defaults."""
        # Create a minimal main.json but no config.json
        scene_data = {"width": 100, "height": 100}
        (tmp_path / "main.json").write_text(json.dumps(scene_data), encoding="utf-8")

        config = load_config(str(tmp_path))

        assert config == {"outputs": [{"format": "svg", "path": "output.svg"}]}


# ─── Renderer tests ─────────────────────────────────────────────────────────────


class TestRenderer:
    def test_render_empty_scene(self):
        """Just width/height, no elements."""
        scene = _make_scene(width=300, height=150)
        svg = render_svg(scene)

        assert 'width="300"' in svg
        assert 'height="150"' in svg
        assert "<rect" not in svg
        assert "</svg>" in svg

    def test_render_background(self):
        """Scene with background produces rect."""
        scene = _make_scene(width=200, height=100, background="#123456")
        svg = render_svg(scene)

        assert 'fill="#123456"' in svg
        assert 'width="200"' in svg
        assert 'height="100"' in svg

    def test_render_rect(self):
        """Rect element renders correctly."""
        rect = _make_rect(x=10, y=20, width=50, height=30, fill="#ff0000")
        scene = _make_scene(elements=[rect])
        svg = render_svg(scene)

        assert '<rect x="10" y="20" width="50" height="30" fill="#ff0000"/>' in svg

    def test_render_path_with_transform(self):
        """Path with translate+scale."""
        path = _make_path(
            d="M0 0 L10 10",
            fill="#00ff00",
            transform=Transform(translate=(5.0, 10.0), scale=(2.0, 3.0)),
        )
        scene = _make_scene(elements=[path])
        svg = render_svg(scene)

        assert 'd="M0 0 L10 10"' in svg
        assert 'fill="#00ff00"' in svg
        assert "translate(5.0,10.0)" in svg
        assert "scale(2.0,3.0)" in svg

    def test_render_path_opacity(self):
        """Opacity attribute rendered when != 1."""
        path = _make_path(opacity=0.5)
        scene = _make_scene(elements=[path])
        svg = render_svg(scene)

        assert 'opacity="0.5"' in svg

    def test_render_text_plain(self):
        """Text without charStyles."""
        text = _make_text(content="Hello", x=10, y=30, fill="#000")
        scene = _make_scene(elements=[text])
        svg = render_svg(scene)

        assert ">Hello</text>" in svg
        assert 'x="10"' in svg
        assert 'y="30"' in svg
        assert 'fill="#000"' in svg
        assert 'font-family="Liberation Sans"' in svg

    def test_render_text_with_char_styles(self):
        """Text with tspan per character."""
        char_styles = [CharStyle(chars="H", opacity=0.5, fill="#f00")]
        text = _make_text(content="Hi", char_styles=char_styles)
        scene = _make_scene(elements=[text])
        svg = render_svg(scene)

        assert "<tspan" in svg
        assert 'fill="#f00"' in svg
        assert 'opacity="0.5"' in svg

    def test_render_group(self):
        """Nested group."""
        rect = _make_rect(fill="#aaa")
        group = Element(type="group", elements=[rect])
        scene = _make_scene(elements=[group])
        svg = render_svg(scene)

        assert "<g>" in svg
        assert "</g>" in svg
        assert 'fill="#aaa"' in svg

    def test_render_use(self):
        """Use element resolves def."""
        # Create a def
        target = _make_rect(fill="#bbb", width=20, height=20)
        defs = {"mybox": target}
        use_el = Element(type="use", use="mybox")
        scene = _make_scene(elements=[use_el], defs=defs)
        svg = render_svg(scene)

        assert 'fill="#bbb"' in svg
        assert 'width="20"' in svg

    def test_render_use_with_fill_override(self):
        """Use with fill cascades to children."""
        target = _make_rect(fill="#original", width=10, height=10)
        defs = {"comp": target}
        use_el = Element(type="use", use="comp", fill="#override")
        scene = _make_scene(elements=[use_el], defs=defs)
        svg = render_svg(scene)

        assert 'fill="#override"' in svg
        assert 'fill="#original"' not in svg

    def test_render_use_with_opacity_override(self):
        """Use with opacity multiplies."""
        target = _make_path(fill="#abc", opacity=0.8)
        defs = {"comp": target}
        use_el = Element(type="use", use="comp", opacity=0.5)
        scene = _make_scene(elements=[use_el], defs=defs)
        svg = render_svg(scene)

        # 0.8 * 0.5 = 0.4
        assert 'opacity="0.4"' in svg


# ─── Pipeline tests ──────────────────────────────────────────────────────────────


class TestPipeline:
    def test_center_text_x(self):
        """Centers text horizontally (sets anchor=middle, x=width/2)."""
        text = _make_text(id="title", x=0, y=50)
        scene = _make_scene(
            width=200,
            height=100,
            elements=[text],
            pipeline=[{"action": "center", "target": "title", "axis": "x"}],
        )
        execute_pipeline(scene)

        assert scene.elements[0].x == 100.0  # width/2
        assert scene.elements[0].anchor == "middle"

    def test_center_rect(self):
        """Centers rect (adjusts x)."""
        rect = _make_rect(id="box", x=0, y=0, width=50, height=30)
        scene = _make_scene(
            width=200,
            height=100,
            elements=[rect],
            pipeline=[{"action": "center", "target": "box", "axis": "x"}],
        )
        execute_pipeline(scene)

        # (200 - 50) / 2 = 75
        assert scene.elements[0].x == 75.0

    def test_place_below(self):
        """Places element below another with gap."""
        rect_a = _make_rect(id="a", x=0, y=10, width=50, height=30)
        rect_b = _make_rect(id="b", x=0, y=0, width=50, height=20)
        scene = _make_scene(
            elements=[rect_a, rect_b],
            pipeline=[{"action": "place", "target": "b", "below": "a", "gap": 5}],
        )
        execute_pipeline(scene)

        # rect_a bottom = y + height = 10 + 30 = 40; b.y = 40 + 5 = 45
        assert scene.elements[1].y == 45.0

    def test_group_elements(self):
        """Groups elements, removes from top level."""
        el_a = _make_rect(id="a")
        el_b = _make_rect(id="b")
        el_c = _make_rect(id="c")
        scene = _make_scene(
            elements=[el_a, el_b, el_c],
            pipeline=[{"action": "group", "targets": ["a", "b"], "id": "grp"}],
        )
        execute_pipeline(scene)

        # 'a' and 'b' removed from top level, replaced by new group 'grp'
        top_ids = [el.id for el in scene.elements]
        assert "a" not in top_ids
        assert "b" not in top_ids
        assert "c" in top_ids
        assert "grp" in top_ids

        grp = next(el for el in scene.elements if el.id == "grp")
        assert grp.type == "group"
        assert len(grp.elements) == 2

    @pytest.mark.skipif(not _HAS_LIBERATION_SANS, reason="Liberation Sans not installed")
    def test_text_to_paths(self):
        """Converts text to group of paths (requires Liberation Sans)."""
        text = _make_text(id="txt", content="AB", font=Font(family="Liberation Sans", size=48))
        scene = _make_scene(
            elements=[text],
            pipeline=[{"action": "text-to-paths", "target": "txt"}],
        )
        execute_pipeline(scene)

        # The text element should have been replaced by a group
        result = scene.elements[0]
        assert result.type == "group"
        assert result.id == "txt"
        assert result.elements is not None
        assert len(result.elements) >= 2  # at least one path per character
        for child in result.elements:
            assert child.type == "path"
            assert child.d  # non-empty path data


# ─── Pack / Unpack tests ────────────────────────────────────────────────────────


class TestPackUnpack:
    def test_pack_and_unpack_round_trip(self, tmp_path: Path):
        """Create a scene with imports, pack it, unpack it, verify structure matches."""
        # Set up a project dir with a component
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        comp_dir = project_dir / "components"
        comp_dir.mkdir()

        comp_data = {"type": "path", "d": "M0 0 L5 5", "fill": "#abc"}
        (comp_dir / "arrow.json").write_text(json.dumps(comp_data), encoding="utf-8")

        scene_data = {
            "width": 400,
            "height": 200,
            "background": "#222",
            "imports": {"arrow": "components/arrow.json"},
            "elements": [{"use": "arrow", "fill": "#fff"}],
        }
        (project_dir / "main.json").write_text(json.dumps(scene_data), encoding="utf-8")

        # Load and pack
        scene = load_scene(str(project_dir))
        packed = pack_scene(scene)

        # Verify packed structure
        assert packed["width"] == 400
        assert packed["height"] == 200
        assert packed["background"] == "#222"
        assert "imports" not in packed  # imports stripped
        assert "defs" in packed
        assert "arrow" in packed["defs"]

        # Write packed file
        packed_file = tmp_path / "packed.json"
        packed_file.write_text(json.dumps(packed, indent=2), encoding="utf-8")

        # Unpack into a new directory
        unpack_dir = tmp_path / "unpacked"
        # Load the packed scene and unpack it
        packed_scene = load_scene(str(packed_file))
        unpack_scene(packed_scene, str(unpack_dir))

        # Verify unpacked structure
        assert (unpack_dir / "main.json").exists()
        assert (unpack_dir / "components" / "arrow.json").exists()

        # Reload from unpacked and verify semantics
        reloaded = load_scene(str(unpack_dir))
        assert reloaded.width == 400
        assert reloaded.height == 200
        assert reloaded.background == "#222"
        assert reloaded.defs is not None
        assert "arrow" in reloaded.defs


# ─── Output tests ───────────────────────────────────────────────────────────────


class TestOutput:
    _SVG_CONTENT = (
        '<svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">'
        '<rect width="100" height="100" fill="#fff"/>'
        "</svg>"
    )

    def test_write_svg(self, tmp_path: Path):
        """Writes SVG string to file."""
        config = {"outputs": [{"format": "svg", "path": "out.svg"}]}
        written = write_outputs(self._SVG_CONTENT, config, str(tmp_path))

        assert len(written) == 1
        out_file = Path(written[0])
        assert out_file.exists()
        content = out_file.read_text(encoding="utf-8")
        assert "<svg" in content
        assert "</svg>" in content

    def test_write_png(self, tmp_path: Path):
        """Converts SVG to PNG (verify file exists and is non-empty)."""
        config = {"outputs": [{"format": "png", "path": "out.png"}]}
        written = write_outputs(self._SVG_CONTENT, config, str(tmp_path))

        assert len(written) == 1
        out_file = Path(written[0])
        assert out_file.exists()
        assert out_file.stat().st_size > 0

    def test_write_webp(self, tmp_path: Path):
        """Converts SVG to WebP (verify file exists and is non-empty)."""
        config = {"outputs": [{"format": "webp", "path": "out.webp", "quality": 80}]}
        written = write_outputs(self._SVG_CONTENT, config, str(tmp_path))

        assert len(written) == 1
        out_file = Path(written[0])
        assert out_file.exists()
        assert out_file.stat().st_size > 0


# ─── Font tests ──────────────────────────────────────────────────────────────────


class TestFonts:
    @pytest.mark.skipif(not _HAS_LIBERATION_SANS, reason="Liberation Sans not installed")
    def test_find_font_existing(self):
        """Finds Liberation Sans."""
        path = find_font("Liberation Sans", 400)
        assert path is not None
        assert Path(path).exists()
        assert "liberation" in path.lower() or "Liberation" in path

    def test_find_font_missing(self):
        """Returns None for nonexistent font."""
        path = find_font("NonExistentFontFamily12345", 400)
        assert path is None

    @pytest.mark.skipif(not _HAS_LIBERATION_SANS, reason="Liberation Sans not installed")
    def test_get_glyph_paths(self):
        """Extracts paths for 'AB'."""
        font_path = find_font("Liberation Sans", 400)
        assert font_path is not None

        glyphs = get_glyph_paths(font_path, "AB", 48.0)

        assert len(glyphs) == 2
        assert glyphs[0]["char"] == "A"
        assert glyphs[1]["char"] == "B"
        # Both should have non-empty path data
        assert glyphs[0]["d"]
        assert glyphs[1]["d"]
        # Both should have positive advance widths
        assert glyphs[0]["advance"] > 0
        assert glyphs[1]["advance"] > 0
