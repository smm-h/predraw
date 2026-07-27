"""strictspec-backed validation for predraw scene and config documents.

The validation engine is generated from ``predraw/schema/*.schema.toml`` by
``strictspec gen`` (driven by ``strictspec.toml``); the generated modules are
``predraw._scene_validator`` and ``predraw._config_validator``. This module is a
thin adapter that keeps predraw's dict-in / ``list[str]``-out surface for callers
(the CLI ``validate`` command and the test suite) and provides the load-path gate
that hard-errors on any diagnostic.

Behaviour differences from the legacy jsonschema engine are intentional and
enforced by strictspec: documents must carry a top-level integer ``format_version``
(the version gate); alias pairs (camelCase canonical + snake_case) may not both be
present; numeric lexemes that ``float64`` cannot represent exactly are refused;
unknown keys are always a hard error.
"""

from __future__ import annotations

import json

from . import _config_validator, _scene_validator


class SchemaValidationError(ValueError):
    """Raised by the load path when a scene or config document fails validation."""

    def __init__(self, label: str, errors: list[str]) -> None:
        self.label = label
        self.errors = errors
        detail = "\n".join(f"  {e}" for e in errors)
        super().__init__(f"Invalid {label} document:\n{detail}")


def validate_scene(data: dict) -> list[str]:
    """Validate a scene dict. Returns rendered diagnostics (empty = valid)."""
    return _diagnostics(_scene_validator, json.dumps(data).encode("utf-8"))


def validate_config(data: dict) -> list[str]:
    """Validate a config dict. Returns rendered diagnostics (empty = valid)."""
    return _diagnostics(_config_validator, json.dumps(data).encode("utf-8"))


def ensure_valid_scene(raw: bytes) -> None:
    """Validate raw scene JSON bytes; raise SchemaValidationError on any diagnostic.

    Raw bytes (not a re-serialized dict) are validated so the byte-level lexeme
    checks (e.g. unrepresentable numbers) see the document exactly as written.
    """
    errors = _diagnostics(_scene_validator, raw)
    if errors:
        raise SchemaValidationError("scene", errors)


def ensure_valid_config(raw: bytes) -> None:
    """Validate raw config JSON bytes; raise SchemaValidationError on any diagnostic."""
    errors = _diagnostics(_config_validator, raw)
    if errors:
        raise SchemaValidationError("config", errors)


def _diagnostics(module, raw: bytes) -> list[str]:
    """Run a generated validator over raw JSON bytes and render its diagnostics."""
    _root, diags = module.validate_bytes(raw, "json")
    return [f"{d.path}: {d.message}" for d in diags]
