# strictspec generated validator. DO NOT EDIT.
#
# strictspec generator: 0.1.0
# schema:              PredrawConfig (format_version 1)
# regenerate:          strictspec gen --manifest strictspec.toml
#
# Released under the MIT license (unencumbered). This file is machine-generated;
# edit the schema and regenerate, never this file.
# ruff: noqa
from __future__ import annotations

from dataclasses import dataclass, replace

import strictspec
from strictspec import Diagnostic, Value

# GENERATED_BY is the strictspec release that produced this file. The runtime
# pairing guard hard-errors unless it matches the linked runtime exactly.
GENERATED_BY = "0.1.0"
SCHEMA_FORMAT_VERSION = 1

# _EMBEDDED_SCHEMA carries the compiled schema (and its imported type-definition
# files and scalar manifest) so the validator is self-contained and does no IO.
_EMBEDDED_SCHEMA = {
    "config.schema.toml": "# strictspec schema — predraw Config (JSON documents).\n# predraw's authoritative config schema; generated validator produced via `strictspec gen`.\n# Documents must carry a top-level integer `format_version = 1` (the strictspec version gate);\n# existing config files are stamped once via scripts/stamp_format_version.py.\n\nname = \"PredrawConfig\"\nmeta_version = 1\nformat_version = 1\ndocument_syntax = \"json\"\nrole = \"schema\"\nroot = \"PredrawConfig\"\ndescription = \"Configuration file for predraw output settings.\"\n\n[types.PredrawConfig]\ntype = \"record\"\n\n[types.PredrawConfig.fields.outputs]\ntype = \"array\"\nrequired = true\nmin_len = 1\ndescription = \"List of output render targets.\"\n[types.PredrawConfig.fields.outputs.item]\ntype = \"Output\"\n\n[types.Output]\ntype = \"record\"\ndescription = \"A single output render target: format, path, and rendering options.\"\n[types.Output.fields.format]\ntype = \"enum\"\nrequired = true\nvalues = [\"svg\", \"png\", \"webp\"]\n[types.Output.fields.path]\ntype = \"string\"\nrequired = true\ndescription = \"Output file path (relative to the project directory).\"\n[types.Output.fields.mode]\ntype = \"enum\"\nrequired = false\nvalues = [\"light\", \"dark\"]\n[types.Output.fields.quality]\ntype = \"integer\"\nrequired = false\nmin = 1\nmax = 100\ndescription = \"Compression quality (lossy formats like webp).\"\n",
}
_EMBEDDED_MAIN_FILE = "config.schema.toml"

# Version pairing: generated code and runtime must be the same release. This runs
# at import, so a skewed runtime hard-errors before any validation is attempted.
strictspec.require_runtime_version(GENERATED_BY)
_program = strictspec.compile_embedded(_EMBEDDED_SCHEMA, _EMBEDDED_MAIN_FILE)


def validate_bytes(input: bytes, syntax: str) -> tuple[PredrawConfig | None, tuple[Diagnostic, ...]]:
    """RAW-BYTES entry point: lossless parse of input in the given syntax
    ("json" | "toml" | "jsonl"), then validate. Returns the typed root value
    (None when any diagnostic fired) and the ordered diagnostics.
    """
    return validate_bytes_with_evidence(input, syntax, None)


def validate_bytes_with_evidence(input: bytes, syntax: str, evidence: dict | None) -> tuple[PredrawConfig | None, tuple[Diagnostic, ...]]:
    """validate_bytes plus cross-document resolver evidence for the phase-2
    constraint vocabulary.
    """
    result = _program.validate_with_evidence(input, syntax, evidence)
    if not result.valid:
        return None, result.diagnostics
    v = strictspec.load_value(input, syntax)
    return _bind_PredrawConfig(v), result.diagnostics


def validate_value(v: Value) -> tuple[PredrawConfig | None, tuple[Diagnostic, ...]]:
    """TAGGED-VALUE entry point: validate an already-parsed tagged document value
    (from strictspec.load_value or a typed constructor). Raw untagged dicts are
    never accepted.
    """
    result = _program.validate_value(v)
    if not result.valid:
        return None, result.diagnostics
    return _bind_PredrawConfig(v), result.diagnostics


@dataclass(frozen=True, kw_only=True)
class PredrawConfig:
    """Frozen typed binding of the "PredrawConfig" record. Immutable; use with_* for
    copy-on-write.
    """

    outputs: list[Output]

    def with_outputs(self, v: list[Output]) -> PredrawConfig:
        return replace(self, outputs=v)


def _bind_PredrawConfig(v: Value) -> PredrawConfig | None:
    if v.kind() != strictspec.Kind.RECORD:
        return None
    f_outputs = v.field("outputs")
    return PredrawConfig(
        outputs=([_bind_Output(e) for e in f_outputs[0].items()] if f_outputs[1] else []),
    )


@dataclass(frozen=True, kw_only=True)
class Output:
    """Frozen typed binding of the "Output" record. Immutable; use with_* for
    copy-on-write.
    """

    format: str
    path: str
    mode: str
    quality: int

    def with_format(self, v: str) -> Output:
        return replace(self, format=v)

    def with_path(self, v: str) -> Output:
        return replace(self, path=v)

    def with_mode(self, v: str) -> Output:
        return replace(self, mode=v)

    def with_quality(self, v: int) -> Output:
        return replace(self, quality=v)


def _bind_Output(v: Value) -> Output | None:
    if v.kind() != strictspec.Kind.RECORD:
        return None
    f_format = v.field("format")
    f_path = v.field("path")
    f_mode = v.field("mode")
    f_quality = v.field("quality")
    return Output(
        format=(f_format[0].string()[0] if f_format[1] else ""),
        path=(f_path[0].string()[0] if f_path[1] else ""),
        mode=(f_mode[0].string()[0] if f_mode[1] else ""),
        quality=(f_quality[0].int()[0] if f_quality[1] else 0),
    )


