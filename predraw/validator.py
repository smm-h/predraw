"""JSON Schema validation for predraw scene and config files."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator


def validate_scene(data: dict) -> list[str]:
    """Validate a dict against the scene schema. Returns list of error messages (empty = valid)."""
    schema = _load_schema("scene")
    return _validate(data, schema)


def validate_config(data: dict) -> list[str]:
    """Validate a dict against the config schema. Returns list of error messages (empty = valid)."""
    schema = _load_schema("config")
    return _validate(data, schema)


def _validate(data: dict, schema: dict) -> list[str]:
    """Run validation and collect error messages with path context."""
    validator = Draft202012Validator(schema)
    errors: list[str] = []
    for error in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path)):
        path = ".".join(str(p) for p in error.absolute_path) or "(root)"
        errors.append(f"{path}: {error.message}")
    return errors


def _load_schema(name: str) -> dict:
    """Load a schema file from the schema/ directory inside the package."""
    schema_dir = Path(__file__).parent / "schema"
    schema_path = schema_dir / f"{name}.schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)
