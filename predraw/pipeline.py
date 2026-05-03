"""Pipeline executor for predraw scenes.

Executes ordered postprocessing steps that modify the element tree in place.
"""

from __future__ import annotations

import warnings

from .model import Element, Scene, Transform


def execute_pipeline(scene: Scene) -> None:
    """Execute all pipeline steps on the scene, modifying it in place."""
    if not scene.pipeline:
        return

    for step in scene.pipeline:
        _execute_step(scene, step)


def _execute_step(scene: Scene, step: dict) -> None:
    """Execute a single pipeline step."""
    action = step.get("action")
    if action == "center":
        _center(scene, step["target"], step.get("axis", "both"))
    elif action == "place":
        _place(scene, step["target"], step["below"], step.get("gap", 0))
    elif action == "group":
        _group(scene, step["targets"], step["id"])
    elif action == "text-to-paths":
        _text_to_paths(scene, step["target"])
    else:
        warnings.warn(f"Unknown pipeline action: {action}")


def _find_element(elements: list[Element], element_id: str) -> Element | None:
    """Find an element by ID, searching recursively through groups."""
    for el in elements:
        if el.id == element_id:
            return el
        if el.elements:
            found = _find_element(el.elements, element_id)
            if found is not None:
                return found
    return None


def _find_and_remove(elements: list[Element], element_id: str) -> Element | None:
    """Find and remove an element by ID from the list (top-level only)."""
    for i, el in enumerate(elements):
        if el.id == element_id:
            return elements.pop(i)
    return None


def _center(scene: Scene, target_id: str, axis: str) -> None:
    """Center an element within the scene canvas."""
    if not scene.elements:
        return

    element = _find_element(scene.elements, target_id)
    if element is None:
        warnings.warn(f"center: element '{target_id}' not found, skipping")
        return

    if element.type == "text":
        _center_text(scene, element, axis)
    elif element.type == "rect":
        _center_rect(scene, element, axis)
    elif element.type == "group":
        _center_group(scene, element, axis)
    else:
        # For paths and other types, use a translate transform
        _center_with_transform(scene, element, axis)


def _center_text(scene: Scene, element: Element, axis: str) -> None:
    """Center a text element. Uses anchor=middle for x, baseline offset for y."""
    font_size = element.font.size if element.font else 16

    if axis in ("x", "both"):
        element.x = scene.width / 2
        element.anchor = "middle"

    if axis in ("y", "both"):
        # Rough baseline adjustment: place baseline at vertical center + 1/3 font size
        element.y = scene.height / 2 + font_size / 3


def _center_rect(scene: Scene, element: Element, axis: str) -> None:
    """Center a rect element by adjusting x/y."""
    if axis in ("x", "both"):
        element.x = (scene.width - element.width) / 2

    if axis in ("y", "both"):
        element.y = (scene.height - element.height) / 2


def _center_group(scene: Scene, element: Element, axis: str) -> None:
    """Center a group by wrapping in a translate transform."""
    # For groups we use translate since we don't know the bounding box trivially.
    # Approximate by using width/height if set, otherwise center at canvas midpoint.
    tx = 0.0
    ty = 0.0

    if axis in ("x", "both"):
        if element.width > 0:
            tx = (scene.width - element.width) / 2 - element.x
        else:
            tx = scene.width / 2

    if axis in ("y", "both"):
        if element.height > 0:
            ty = (scene.height - element.height) / 2 - element.y
        else:
            ty = scene.height / 2

    if element.transform is None:
        element.transform = Transform(translate=(tx, ty))
    else:
        # Compose with existing translate
        existing = element.transform.translate
        element.transform.translate = (existing[0] + tx, existing[1] + ty)


def _center_with_transform(scene: Scene, element: Element, axis: str) -> None:
    """Center an element using a translate transform (fallback for unknown geometry)."""
    tx = scene.width / 2 if axis in ("x", "both") else 0.0
    ty = scene.height / 2 if axis in ("y", "both") else 0.0

    if element.transform is None:
        element.transform = Transform(translate=(tx, ty))
    else:
        existing = element.transform.translate
        element.transform.translate = (existing[0] + tx, existing[1] + ty)


def _place(scene: Scene, target_id: str, below_id: str, gap: float) -> None:
    """Position an element relative to another (below it with a gap)."""
    if not scene.elements:
        return

    reference = _find_element(scene.elements, below_id)
    if reference is None:
        warnings.warn(f"place: reference element '{below_id}' not found, skipping")
        return

    target = _find_element(scene.elements, target_id)
    if target is None:
        warnings.warn(f"place: target element '{target_id}' not found, skipping")
        return

    # Compute the bottom edge of the reference element
    if reference.type == "text":
        # For text, y is the baseline; bottom is approximately at y
        ref_bottom = reference.y
    elif reference.type in ("rect", "group"):
        ref_bottom = reference.y + reference.height
    else:
        # Fallback: use y as bottom
        ref_bottom = reference.y

    # Place target below reference with the given gap
    target.y = ref_bottom + gap


def _group(scene: Scene, target_ids: list[str], group_id: str) -> None:
    """Wrap multiple elements into a new group."""
    if not scene.elements:
        return

    collected: list[Element] = []
    for tid in target_ids:
        el = _find_and_remove(scene.elements, tid)
        if el is None:
            warnings.warn(f"group: element '{tid}' not found, skipping it")
        else:
            collected.append(el)

    if not collected:
        return

    group = Element(
        type="group",
        id=group_id,
        elements=collected,
    )
    scene.elements.append(group)


def _text_to_paths(scene: Scene, target_id: str) -> None:
    """Convert text to paths (stub — not yet implemented)."""
    if not scene.elements:
        return

    element = _find_element(scene.elements, target_id)
    if element is None:
        warnings.warn(f"text-to-paths: element '{target_id}' not found, skipping")
        return

    warnings.warn("text-to-paths not yet implemented, rendering as text")
