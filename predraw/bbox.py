"""Bounding box computation for predraw elements.

Computes axis-aligned bounding boxes from element geometry, including
SVG path data parsing and transform application.
"""

from __future__ import annotations

import re

from .model import Element, Transform


def compute_bbox(element: Element) -> tuple[float, float, float, float] | None:
    """Compute the bounding box (min_x, min_y, max_x, max_y) of an element.

    Handles:
    - rect: (x, y, x+width, y+height)
    - text: (x, y - font_size, x + estimated_width, y) -- rough estimate
    - path: parse the d string and find coordinate extremes
    - group: union of children's bboxes, with transform applied
    - background: (0, 0, 0, 0) -- skip

    Returns None if bbox can't be determined.
    """
    if element.type == "background":
        return None

    if element.type == "rect":
        bbox = (element.x, element.y, element.x + element.width, element.y + element.height)

    elif element.type == "text":
        font_size = element.font.size if element.font else 16
        # Rough width estimate: 0.6 * font_size per character
        content = element.content or ""
        estimated_width = len(content) * font_size * 0.6
        # y is baseline; top is approximately y - font_size
        x = element.x
        if element.anchor == "middle":
            x = element.x - estimated_width / 2
        elif element.anchor == "end":
            x = element.x - estimated_width
        bbox = (x, element.y - font_size, x + estimated_width, element.y)

    elif element.type == "path":
        if not element.d:
            return None
        path_bbox = _bbox_from_path_d(element.d)
        if path_bbox is None:
            return None
        bbox = path_bbox

    elif element.type == "group":
        if not element.elements:
            return None
        # Union of children bboxes
        min_x = float("inf")
        min_y = float("inf")
        max_x = float("-inf")
        max_y = float("-inf")
        has_any = False
        for child in element.elements:
            child_bbox = compute_bbox(child)
            if child_bbox is not None:
                has_any = True
                min_x = min(min_x, child_bbox[0])
                min_y = min(min_y, child_bbox[1])
                max_x = max(max_x, child_bbox[2])
                max_y = max(max_y, child_bbox[3])
        if not has_any:
            return None
        bbox = (min_x, min_y, max_x, max_y)

    else:
        return None

    # Apply element transform if present
    if element.transform is not None:
        bbox = _apply_transform_to_bbox(bbox, element.transform)

    return bbox


# Regex to tokenize SVG path d strings: command letters and numbers
_PATH_TOKEN_RE = re.compile(r"[A-Za-z]|[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?")


def _bbox_from_path_d(d: str) -> tuple[float, float, float, float] | None:
    """Parse SVG path d string and extract coordinate bounding box.

    Handles M, L, H, V, C, S, Q, T, A, Z commands (uppercase = absolute).
    For curves (C, S, Q), use control points as bbox approximation.
    Lowercase (relative) commands need accumulation from current point.
    """
    tokens = _PATH_TOKEN_RE.findall(d)
    if not tokens:
        return None

    xs: list[float] = []
    ys: list[float] = []
    # Current point for relative commands
    cx, cy = 0.0, 0.0
    i = 0

    def next_num() -> float:
        nonlocal i
        i += 1
        return float(tokens[i])

    while i < len(tokens):
        token = tokens[i]

        if token == "M":
            # Absolute moveto; consumes pairs of coordinates
            cx = next_num()
            cy = next_num()
            xs.append(cx)
            ys.append(cy)
            # Implicit lineto pairs follow
            while i + 1 < len(tokens) and not tokens[i + 1].isalpha():
                cx = next_num()
                cy = next_num()
                xs.append(cx)
                ys.append(cy)

        elif token == "m":
            # Relative moveto
            cx += next_num()
            cy += next_num()
            xs.append(cx)
            ys.append(cy)
            while i + 1 < len(tokens) and not tokens[i + 1].isalpha():
                cx += next_num()
                cy += next_num()
                xs.append(cx)
                ys.append(cy)

        elif token == "L":
            while i + 1 < len(tokens) and not tokens[i + 1].isalpha():
                cx = next_num()
                cy = next_num()
                xs.append(cx)
                ys.append(cy)

        elif token == "l":
            while i + 1 < len(tokens) and not tokens[i + 1].isalpha():
                cx += next_num()
                cy += next_num()
                xs.append(cx)
                ys.append(cy)

        elif token == "H":
            while i + 1 < len(tokens) and not tokens[i + 1].isalpha():
                cx = next_num()
                xs.append(cx)

        elif token == "h":
            while i + 1 < len(tokens) and not tokens[i + 1].isalpha():
                cx += next_num()
                xs.append(cx)

        elif token == "V":
            while i + 1 < len(tokens) and not tokens[i + 1].isalpha():
                cy = next_num()
                ys.append(cy)

        elif token == "v":
            while i + 1 < len(tokens) and not tokens[i + 1].isalpha():
                cy += next_num()
                ys.append(cy)

        elif token == "C":
            # Cubic bezier: 3 pairs of coords (control1, control2, endpoint)
            while i + 1 < len(tokens) and not tokens[i + 1].isalpha():
                for _ in range(3):
                    px = next_num()
                    py = next_num()
                    xs.append(px)
                    ys.append(py)
                # Endpoint becomes current
                cx, cy = xs[-1], ys[-1]

        elif token == "c":
            # Relative cubic bezier
            while i + 1 < len(tokens) and not tokens[i + 1].isalpha():
                for _ in range(3):
                    px = cx + next_num()
                    py = cy + next_num()
                    xs.append(px)
                    ys.append(py)
                # Endpoint becomes current (last appended pair)
                cx, cy = xs[-1], ys[-1]

        elif token == "S":
            # Smooth cubic: 2 pairs (control2, endpoint)
            while i + 1 < len(tokens) and not tokens[i + 1].isalpha():
                for _ in range(2):
                    px = next_num()
                    py = next_num()
                    xs.append(px)
                    ys.append(py)
                cx, cy = xs[-1], ys[-1]

        elif token == "s":
            while i + 1 < len(tokens) and not tokens[i + 1].isalpha():
                for _ in range(2):
                    px = cx + next_num()
                    py = cy + next_num()
                    xs.append(px)
                    ys.append(py)
                cx, cy = xs[-1], ys[-1]

        elif token == "Q":
            # Quadratic bezier: 2 pairs (control, endpoint)
            while i + 1 < len(tokens) and not tokens[i + 1].isalpha():
                for _ in range(2):
                    px = next_num()
                    py = next_num()
                    xs.append(px)
                    ys.append(py)
                cx, cy = xs[-1], ys[-1]

        elif token == "q":
            while i + 1 < len(tokens) and not tokens[i + 1].isalpha():
                for _ in range(2):
                    px = cx + next_num()
                    py = cy + next_num()
                    xs.append(px)
                    ys.append(py)
                cx, cy = xs[-1], ys[-1]

        elif token == "T":
            # Smooth quadratic: 1 pair (endpoint)
            while i + 1 < len(tokens) and not tokens[i + 1].isalpha():
                cx = next_num()
                cy = next_num()
                xs.append(cx)
                ys.append(cy)

        elif token == "t":
            while i + 1 < len(tokens) and not tokens[i + 1].isalpha():
                cx += next_num()
                cy += next_num()
                xs.append(cx)
                ys.append(cy)

        elif token == "A":
            # Arc: rx ry x-rotation large-arc-flag sweep-flag x y
            while i + 1 < len(tokens) and not tokens[i + 1].isalpha():
                # Skip rx, ry, x-rotation, large-arc-flag, sweep-flag
                next_num()  # rx
                next_num()  # ry
                next_num()  # x-rotation
                next_num()  # large-arc-flag
                next_num()  # sweep-flag
                cx = next_num()
                cy = next_num()
                xs.append(cx)
                ys.append(cy)

        elif token == "a":
            while i + 1 < len(tokens) and not tokens[i + 1].isalpha():
                next_num()  # rx
                next_num()  # ry
                next_num()  # x-rotation
                next_num()  # large-arc-flag
                next_num()  # sweep-flag
                cx += next_num()
                cy += next_num()
                xs.append(cx)
                ys.append(cy)

        elif token in ("Z", "z"):
            pass  # Close path, no coordinates

        i += 1

    if not xs or not ys:
        return None

    return (min(xs), min(ys), max(xs), max(ys))


def _apply_transform_to_bbox(
    bbox: tuple[float, float, float, float], transform: Transform
) -> tuple[float, float, float, float]:
    """Apply translate and scale to a bounding box."""
    min_x, min_y, max_x, max_y = bbox
    tx, ty = transform.translate
    sx, sy = transform.scale

    # Scale then translate
    new_min_x = min_x * sx + tx
    new_min_y = min_y * sy + ty
    new_max_x = max_x * sx + tx
    new_max_y = max_y * sy + ty

    # Handle negative scales flipping min/max
    return (
        min(new_min_x, new_max_x),
        min(new_min_y, new_max_y),
        max(new_min_x, new_max_x),
        max(new_min_y, new_max_y),
    )
