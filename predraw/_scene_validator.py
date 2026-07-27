# strictspec generated validator. DO NOT EDIT.
#
# strictspec generator: 0.1.0
# schema:              PredrawScene (format_version 1)
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
    "scene.schema.toml": "# strictspec schema — predraw Scene (JSON documents).\n#\n# This is predraw's authoritative scene schema. Generated validator code is produced from it\n# via `strictspec gen` (see strictspec.toml); never edit the generated *_validator.py by hand.\n# Documents must carry a top-level integer `format_version = 1` (the strictspec version gate);\n# a document without it is rejected with STRICTSPEC_GATE_ABSENT. The gate is net-new to predraw:\n# existing scenes are stamped once via scripts/stamp_format_version.py.\n# The camelCase field names are canonical; each snake_case `aliases` entry is a co-valid spelling\n# (having BOTH present is STRICTSPEC_ALIAS_BOTH_PRESENT).\n\nname = \"PredrawScene\"\nmeta_version = 1\nformat_version = 1\ndocument_syntax = \"json\"\nrole = \"schema\"\nroot = \"PredrawScene\"\ndescription = \"A predraw scene file defining a vector graphic composition.\"\n\n[types.PredrawScene]\ntype = \"record\"\n\n[types.PredrawScene.fields.width]\ntype = \"number\"\nrequired = true\ndescription = \"Canvas width in pixels.\"\n[types.PredrawScene.fields.height]\ntype = \"number\"\nrequired = true\ndescription = \"Canvas height in pixels.\"\n[types.PredrawScene.fields.background]\ntype = \"string\"\nrequired = false\ndescription = \"Default background color (CSS color or $ref).\"\n[types.PredrawScene.fields.styles]\ntype = \"map\"\nrequired = false\ndescription = \"Named style tokens; referenced via $name in fill values.\"\n[types.PredrawScene.fields.styles.value]\ntype = \"Style\"\n[types.PredrawScene.fields.imports]\ntype = \"map\"\nrequired = false\ndescription = \"Alias name -> relative file path for external component defs.\"\n[types.PredrawScene.fields.imports.value]\ntype = \"string\"\n[types.PredrawScene.fields.defs]\ntype = \"map\"\nrequired = false\ndescription = \"Inline component definitions (packed). Recursive: values are Elements.\"\n[types.PredrawScene.fields.defs.value]\ntype = \"Element\"\n[types.PredrawScene.fields.elements]\ntype = \"array\"\nrequired = true\ndescription = \"Ordered list of elements to render.\"\n[types.PredrawScene.fields.elements.item]\ntype = \"Element\"\n[types.PredrawScene.fields.pipeline]\ntype = \"array\"\nrequired = false\ndescription = \"Post-processing steps applied after initial layout.\"\n[types.PredrawScene.fields.pipeline.item]\ntype = \"PipelineStep\"\n\n# --- leaf sub-types ---\n\n[types.Style]\ntype = \"record\"\ndescription = \"A style token with light and dark color values.\"\n[types.Style.fields.light]\ntype = \"string\"\nrequired = true\n[types.Style.fields.dark]\ntype = \"string\"\nrequired = true\n\n[types.Transform]\ntype = \"record\"\ndescription = \"2D transform. (Source `default` values dropped — decision 30; absence handled consumer-side.)\"\n[types.Transform.fields.translate]\ntype = \"tuple\"\nrequired = false\nelements = [\"number\", \"number\"]\ndescription = \"Translation as [x, y].\"\n[types.Transform.fields.scale]\ntype = \"tuple\"\nrequired = false\nelements = [\"number\", \"number\"]\ndescription = \"Scale as [sx, sy].\"\n\n[types.Font]\ntype = \"record\"\ndescription = \"Font specification for text elements.\"\n[types.Font.fields.family]\ntype = \"string\"\nrequired = true\n[types.Font.fields.size]\ntype = \"number\"\nrequired = true\n[types.Font.fields.weight]\ntype = \"integer\"\nrequired = false\nmin = 100\nmax = 900\ndescription = \"Font weight (100-900). Source default 400 dropped.\"\n\n[types.CharStyle]\ntype = \"record\"\ndescription = \"Per-character styling override for text elements.\"\n[types.CharStyle.fields.chars]\ntype = \"string\"\nrequired = true\n[types.CharStyle.fields.opacity]\ntype = \"number\"\nrequired = false\nmin = 0\nmax = 1\n[types.CharStyle.fields.fill]\ntype = \"string\"\nrequired = false\n\n[types.GradientStop]\ntype = \"record\"\ndescription = \"A single stop in a gradient.\"\n[types.GradientStop.fields.offset]\ntype = \"number\"\nrequired = true\nmin = 0\nmax = 1\n[types.GradientStop.fields.color]\ntype = \"string\"\nrequired = true\n[types.GradientStop.fields.opacity]\ntype = \"number\"\nrequired = false\nmin = 0\nmax = 1\n\n[types.Gradient]\ntype = \"record\"\ndescription = \"A gradient fill/stroke definition.\"\n[types.Gradient.fields.type]\ntype = \"enum\"\nrequired = true\nvalues = [\"linear-gradient\", \"radial-gradient\"]\n[types.Gradient.fields.stops]\ntype = \"array\"\nrequired = true\n[types.Gradient.fields.stops.item]\ntype = \"GradientStop\"\n[types.Gradient.fields.angle]\ntype = \"number\"\nrequired = false\n[types.Gradient.fields.cx]\ntype = \"number\"\nrequired = false\n[types.Gradient.fields.cy]\ntype = \"number\"\nrequired = false\n[types.Gradient.fields.r]\ntype = \"number\"\nrequired = false\n\n# THE node-kind union that motivates the construct (decision 15): a color STRING\n# (scalar arm) or a Gradient OBJECT (record arm) — distinct node kinds, no discriminator.\n# Arms are subtables keyed by an arm name; the input node kind selects the arm.\n[types.FillOrGradient]\ntype = \"node-kind-union\"\ndescription = \"A color string or a gradient object.\"\n[types.FillOrGradient.arms.color]\ntype = \"string\"\n[types.FillOrGradient.arms.gradient]\ntype = \"Gradient\"\n\n# --- element discriminated union (by `type`) ---\n\n[types.Element]\ntype = \"discriminated-union\"\ndiscriminator = \"type\"\ndescription = \"A drawable element; the `type` field selects the arm. NOTE: source useElement makes `type` OPTIONAL (inferred from `use`); this draft makes it REQUIRED (a narrowing) — see gap-note.md #4.\"\n[types.Element.arms.background]\ntype = \"backgroundElement\"\n[types.Element.arms.rect]\ntype = \"rectElement\"\n[types.Element.arms.path]\ntype = \"pathElement\"\n[types.Element.arms.text]\ntype = \"textElement\"\n[types.Element.arms.group]\ntype = \"groupElement\"\n[types.Element.arms.use]\ntype = \"useElement\"\n\n[types.backgroundElement]\ntype = \"record\"\ndescription = \"Fills the entire canvas with a color.\"\n[types.backgroundElement.fields.type]\ntype = \"literal\"\nrequired = true\nvalue = \"background\"\n[types.backgroundElement.fields.id]\ntype = \"string\"\nrequired = false\n[types.backgroundElement.fields.fill]\ntype = \"FillOrGradient\"\nrequired = true\n[types.backgroundElement.fields.opacity]\ntype = \"number\"\nrequired = false\nmin = 0\nmax = 1\n[types.backgroundElement.fields.transform]\ntype = \"Transform\"\nrequired = false\n\n[types.rectElement]\ntype = \"record\"\ndescription = \"A rectangle element.\"\n[types.rectElement.fields.type]\ntype = \"literal\"\nrequired = true\nvalue = \"rect\"\n[types.rectElement.fields.id]\ntype = \"string\"\nrequired = false\n[types.rectElement.fields.x]\ntype = \"number\"\nrequired = false\n[types.rectElement.fields.y]\ntype = \"number\"\nrequired = false\n[types.rectElement.fields.width]\ntype = \"number\"\nrequired = false\n[types.rectElement.fields.height]\ntype = \"number\"\nrequired = false\n[types.rectElement.fields.fill]\ntype = \"FillOrGradient\"\nrequired = false\n[types.rectElement.fields.opacity]\ntype = \"number\"\nrequired = false\nmin = 0\nmax = 1\n[types.rectElement.fields.stroke]\ntype = \"FillOrGradient\"\nrequired = false\n[types.rectElement.fields.strokeWidth]\ntype = \"number\"\nrequired = false\naliases = [\"stroke_width\"]\n[types.rectElement.fields.strokeDasharray]\ntype = \"string\"\nrequired = false\naliases = [\"stroke_dasharray\"]\n[types.rectElement.fields.strokeLinecap]\ntype = \"enum\"\nrequired = false\nvalues = [\"butt\", \"round\", \"square\"]\naliases = [\"stroke_linecap\"]\n[types.rectElement.fields.strokeLinejoin]\ntype = \"enum\"\nrequired = false\nvalues = [\"miter\", \"round\", \"bevel\"]\naliases = [\"stroke_linejoin\"]\n[types.rectElement.fields.strokeOpacity]\ntype = \"number\"\nrequired = false\nmin = 0\nmax = 1\naliases = [\"stroke_opacity\"]\n[types.rectElement.fields.transform]\ntype = \"Transform\"\nrequired = false\n\n[types.pathElement]\ntype = \"record\"\ndescription = \"An SVG path element.\"\n[types.pathElement.fields.type]\ntype = \"literal\"\nrequired = true\nvalue = \"path\"\n[types.pathElement.fields.id]\ntype = \"string\"\nrequired = false\n[types.pathElement.fields.d]\ntype = \"string\"\nrequired = true\ndescription = \"SVG path data string.\"\n[types.pathElement.fields.fill]\ntype = \"FillOrGradient\"\nrequired = false\n[types.pathElement.fields.opacity]\ntype = \"number\"\nrequired = false\nmin = 0\nmax = 1\n[types.pathElement.fields.stroke]\ntype = \"FillOrGradient\"\nrequired = false\n[types.pathElement.fields.strokeWidth]\ntype = \"number\"\nrequired = false\naliases = [\"stroke_width\"]\n[types.pathElement.fields.strokeDasharray]\ntype = \"string\"\nrequired = false\naliases = [\"stroke_dasharray\"]\n[types.pathElement.fields.strokeLinecap]\ntype = \"enum\"\nrequired = false\nvalues = [\"butt\", \"round\", \"square\"]\naliases = [\"stroke_linecap\"]\n[types.pathElement.fields.strokeLinejoin]\ntype = \"enum\"\nrequired = false\nvalues = [\"miter\", \"round\", \"bevel\"]\naliases = [\"stroke_linejoin\"]\n[types.pathElement.fields.strokeOpacity]\ntype = \"number\"\nrequired = false\nmin = 0\nmax = 1\naliases = [\"stroke_opacity\"]\n[types.pathElement.fields.transform]\ntype = \"Transform\"\nrequired = false\n\n[types.textElement]\ntype = \"record\"\ndescription = \"A text element with font and optional per-character styling.\"\n[types.textElement.fields.type]\ntype = \"literal\"\nrequired = true\nvalue = \"text\"\n[types.textElement.fields.id]\ntype = \"string\"\nrequired = false\n[types.textElement.fields.content]\ntype = \"string\"\nrequired = true\n[types.textElement.fields.x]\ntype = \"number\"\nrequired = false\n[types.textElement.fields.y]\ntype = \"number\"\nrequired = false\n[types.textElement.fields.anchor]\ntype = \"enum\"\nrequired = false\nvalues = [\"start\", \"middle\", \"end\"]\n[types.textElement.fields.fill]\ntype = \"FillOrGradient\"\nrequired = false\n[types.textElement.fields.font]\ntype = \"Font\"\nrequired = false\n[types.textElement.fields.letterSpacing]\ntype = \"number\"\nrequired = false\naliases = [\"letter_spacing\"]\n[types.textElement.fields.charStyles]\ntype = \"array\"\nrequired = false\naliases = [\"char_styles\"]\n[types.textElement.fields.charStyles.item]\ntype = \"CharStyle\"\n[types.textElement.fields.opacity]\ntype = \"number\"\nrequired = false\nmin = 0\nmax = 1\n[types.textElement.fields.stroke]\ntype = \"FillOrGradient\"\nrequired = false\n[types.textElement.fields.strokeWidth]\ntype = \"number\"\nrequired = false\naliases = [\"stroke_width\"]\n[types.textElement.fields.strokeDasharray]\ntype = \"string\"\nrequired = false\naliases = [\"stroke_dasharray\"]\n[types.textElement.fields.strokeLinecap]\ntype = \"enum\"\nrequired = false\nvalues = [\"butt\", \"round\", \"square\"]\naliases = [\"stroke_linecap\"]\n[types.textElement.fields.strokeLinejoin]\ntype = \"enum\"\nrequired = false\nvalues = [\"miter\", \"round\", \"bevel\"]\naliases = [\"stroke_linejoin\"]\n[types.textElement.fields.strokeOpacity]\ntype = \"number\"\nrequired = false\nmin = 0\nmax = 1\naliases = [\"stroke_opacity\"]\n[types.textElement.fields.transform]\ntype = \"Transform\"\nrequired = false\n\n[types.groupElement]\ntype = \"record\"\ndescription = \"A group containing child elements. Recursive.\"\n[types.groupElement.fields.type]\ntype = \"literal\"\nrequired = true\nvalue = \"group\"\n[types.groupElement.fields.id]\ntype = \"string\"\nrequired = false\n# `elements` canonical; `children` is the co-valid alias (source: 'children is alias for elements').\n[types.groupElement.fields.elements]\ntype = \"array\"\nrequired = false\naliases = [\"children\"]\n[types.groupElement.fields.elements.item]\ntype = \"Element\"\n[types.groupElement.fields.fill]\ntype = \"FillOrGradient\"\nrequired = false\n[types.groupElement.fields.opacity]\ntype = \"number\"\nrequired = false\nmin = 0\nmax = 1\n[types.groupElement.fields.stroke]\ntype = \"FillOrGradient\"\nrequired = false\n[types.groupElement.fields.strokeWidth]\ntype = \"number\"\nrequired = false\naliases = [\"stroke_width\"]\n[types.groupElement.fields.strokeDasharray]\ntype = \"string\"\nrequired = false\naliases = [\"stroke_dasharray\"]\n[types.groupElement.fields.strokeLinecap]\ntype = \"enum\"\nrequired = false\nvalues = [\"butt\", \"round\", \"square\"]\naliases = [\"stroke_linecap\"]\n[types.groupElement.fields.strokeLinejoin]\ntype = \"enum\"\nrequired = false\nvalues = [\"miter\", \"round\", \"bevel\"]\naliases = [\"stroke_linejoin\"]\n[types.groupElement.fields.strokeOpacity]\ntype = \"number\"\nrequired = false\nmin = 0\nmax = 1\naliases = [\"stroke_opacity\"]\n[types.groupElement.fields.transform]\ntype = \"Transform\"\nrequired = false\n\n[types.useElement]\ntype = \"record\"\ndescription = \"Instantiates a component from defs or imports by name.\"\n[types.useElement.fields.type]\ntype = \"literal\"\nrequired = true\nvalue = \"use\"\ndescription = \"Source makes this OPTIONAL; draft requires it so the discriminated union is well-formed (gap-note.md #4).\"\n[types.useElement.fields.id]\ntype = \"string\"\nrequired = false\n[types.useElement.fields.use]\ntype = \"string\"\nrequired = true\ndescription = \"Name of the def/import to instantiate.\"\n[types.useElement.fields.fill]\ntype = \"FillOrGradient\"\nrequired = false\n[types.useElement.fields.opacity]\ntype = \"number\"\nrequired = false\nmin = 0\nmax = 1\n[types.useElement.fields.stroke]\ntype = \"FillOrGradient\"\nrequired = false\n[types.useElement.fields.strokeWidth]\ntype = \"number\"\nrequired = false\naliases = [\"stroke_width\"]\n[types.useElement.fields.strokeDasharray]\ntype = \"string\"\nrequired = false\naliases = [\"stroke_dasharray\"]\n[types.useElement.fields.strokeLinecap]\ntype = \"enum\"\nrequired = false\nvalues = [\"butt\", \"round\", \"square\"]\naliases = [\"stroke_linecap\"]\n[types.useElement.fields.strokeLinejoin]\ntype = \"enum\"\nrequired = false\nvalues = [\"miter\", \"round\", \"bevel\"]\naliases = [\"stroke_linejoin\"]\n[types.useElement.fields.strokeOpacity]\ntype = \"number\"\nrequired = false\nmin = 0\nmax = 1\naliases = [\"stroke_opacity\"]\n[types.useElement.fields.transform]\ntype = \"Transform\"\nrequired = false\n\n# --- pipeline discriminated union (by `action`) ---\n\n[types.PipelineStep]\ntype = \"discriminated-union\"\ndiscriminator = \"action\"\n[types.PipelineStep.arms.center]\ntype = \"centerStep\"\n[types.PipelineStep.arms.place]\ntype = \"placeStep\"\n[types.PipelineStep.arms.group]\ntype = \"groupStep\"\n[types.PipelineStep.arms.\"text-to-paths\"]\ntype = \"textToPathsStep\"\n\n[types.centerStep]\ntype = \"record\"\n[types.centerStep.fields.action]\ntype = \"literal\"\nrequired = true\nvalue = \"center\"\n[types.centerStep.fields.target]\ntype = \"string\"\nrequired = true\n[types.centerStep.fields.axis]\ntype = \"enum\"\nrequired = false\nvalues = [\"x\", \"y\", \"both\"]\n\n[types.placeStep]\ntype = \"record\"\ndescription = \"Places an element relative to another. anyOf(below/above/left/right) -> at-least-one-of.\"\n[types.placeStep.fields.action]\ntype = \"literal\"\nrequired = true\nvalue = \"place\"\n[types.placeStep.fields.target]\ntype = \"string\"\nrequired = true\n[types.placeStep.fields.below]\ntype = \"string\"\nrequired = false\n[types.placeStep.fields.above]\ntype = \"string\"\nrequired = false\n[types.placeStep.fields.left]\ntype = \"string\"\nrequired = false\n[types.placeStep.fields.right]\ntype = \"string\"\nrequired = false\n[types.placeStep.fields.gap]\ntype = \"number\"\nrequired = false\n[[types.placeStep.constraints]]\nform = \"at-least-one-of\"\nfields = [\"below\", \"above\", \"left\", \"right\"]\n\n[types.groupStep]\ntype = \"record\"\n[types.groupStep.fields.action]\ntype = \"literal\"\nrequired = true\nvalue = \"group\"\n[types.groupStep.fields.targets]\ntype = \"array\"\nrequired = true\n[types.groupStep.fields.targets.item]\ntype = \"string\"\n[types.groupStep.fields.id]\ntype = \"string\"\nrequired = true\n\n[types.textToPathsStep]\ntype = \"record\"\n[types.textToPathsStep.fields.action]\ntype = \"literal\"\nrequired = true\nvalue = \"text-to-paths\"\n[types.textToPathsStep.fields.target]\ntype = \"string\"\nrequired = true\n",
}
_EMBEDDED_MAIN_FILE = "scene.schema.toml"

# Version pairing: generated code and runtime must be the same release. This runs
# at import, so a skewed runtime hard-errors before any validation is attempted.
strictspec.require_runtime_version(GENERATED_BY)
_program = strictspec.compile_embedded(_EMBEDDED_SCHEMA, _EMBEDDED_MAIN_FILE)


def validate_bytes(input: bytes, syntax: str) -> tuple[PredrawScene | None, tuple[Diagnostic, ...]]:
    """RAW-BYTES entry point: lossless parse of input in the given syntax
    ("json" | "toml" | "jsonl"), then validate. Returns the typed root value
    (None when any diagnostic fired) and the ordered diagnostics.
    """
    return validate_bytes_with_evidence(input, syntax, None)


def validate_bytes_with_evidence(input: bytes, syntax: str, evidence: dict | None) -> tuple[PredrawScene | None, tuple[Diagnostic, ...]]:
    """validate_bytes plus cross-document resolver evidence for the phase-2
    constraint vocabulary.
    """
    result = _program.validate_with_evidence(input, syntax, evidence)
    if not result.valid:
        return None, result.diagnostics
    v = strictspec.load_value(input, syntax)
    return _bind_PredrawScene(v), result.diagnostics


def validate_value(v: Value) -> tuple[PredrawScene | None, tuple[Diagnostic, ...]]:
    """TAGGED-VALUE entry point: validate an already-parsed tagged document value
    (from strictspec.load_value or a typed constructor). Raw untagged dicts are
    never accepted.
    """
    result = _program.validate_value(v)
    if not result.valid:
        return None, result.diagnostics
    return _bind_PredrawScene(v), result.diagnostics


@dataclass(frozen=True, kw_only=True)
class PredrawScene:
    """Frozen typed binding of the "PredrawScene" record. Immutable; use with_* for
    copy-on-write.
    """

    width: float
    height: float
    background: str
    styles: Value
    imports: Value
    defs: Value
    elements: list[Value]
    pipeline: list[Value]

    def with_width(self, v: float) -> PredrawScene:
        return replace(self, width=v)

    def with_height(self, v: float) -> PredrawScene:
        return replace(self, height=v)

    def with_background(self, v: str) -> PredrawScene:
        return replace(self, background=v)

    def with_styles(self, v: Value) -> PredrawScene:
        return replace(self, styles=v)

    def with_imports(self, v: Value) -> PredrawScene:
        return replace(self, imports=v)

    def with_defs(self, v: Value) -> PredrawScene:
        return replace(self, defs=v)

    def with_elements(self, v: list[Value]) -> PredrawScene:
        return replace(self, elements=v)

    def with_pipeline(self, v: list[Value]) -> PredrawScene:
        return replace(self, pipeline=v)


def _bind_PredrawScene(v: Value) -> PredrawScene | None:
    if v.kind() != strictspec.Kind.RECORD:
        return None
    f_width = v.field("width")
    f_height = v.field("height")
    f_background = v.field("background")
    f_styles = v.field("styles")
    f_imports = v.field("imports")
    f_defs = v.field("defs")
    f_elements = v.field("elements")
    f_pipeline = v.field("pipeline")
    return PredrawScene(
        width=(f_width[0].number()[0] if f_width[1] else 0.0),
        height=(f_height[0].number()[0] if f_height[1] else 0.0),
        background=(f_background[0].string()[0] if f_background[1] else ""),
        styles=(f_styles[0] if f_styles[1] else Value(None, "json")),
        imports=(f_imports[0] if f_imports[1] else Value(None, "json")),
        defs=(f_defs[0] if f_defs[1] else Value(None, "json")),
        elements=([e for e in f_elements[0].items()] if f_elements[1] else []),
        pipeline=([e for e in f_pipeline[0].items()] if f_pipeline[1] else []),
    )


@dataclass(frozen=True, kw_only=True)
class Style:
    """Frozen typed binding of the "Style" record. Immutable; use with_* for
    copy-on-write.
    """

    light: str
    dark: str

    def with_light(self, v: str) -> Style:
        return replace(self, light=v)

    def with_dark(self, v: str) -> Style:
        return replace(self, dark=v)


def _bind_Style(v: Value) -> Style | None:
    if v.kind() != strictspec.Kind.RECORD:
        return None
    f_light = v.field("light")
    f_dark = v.field("dark")
    return Style(
        light=(f_light[0].string()[0] if f_light[1] else ""),
        dark=(f_dark[0].string()[0] if f_dark[1] else ""),
    )


@dataclass(frozen=True, kw_only=True)
class Transform:
    """Frozen typed binding of the "Transform" record. Immutable; use with_* for
    copy-on-write.
    """

    translate: Value
    scale: Value

    def with_translate(self, v: Value) -> Transform:
        return replace(self, translate=v)

    def with_scale(self, v: Value) -> Transform:
        return replace(self, scale=v)


def _bind_Transform(v: Value) -> Transform | None:
    if v.kind() != strictspec.Kind.RECORD:
        return None
    f_translate = v.field("translate")
    f_scale = v.field("scale")
    return Transform(
        translate=(f_translate[0] if f_translate[1] else Value(None, "json")),
        scale=(f_scale[0] if f_scale[1] else Value(None, "json")),
    )


@dataclass(frozen=True, kw_only=True)
class Font:
    """Frozen typed binding of the "Font" record. Immutable; use with_* for
    copy-on-write.
    """

    family: str
    size: float
    weight: int

    def with_family(self, v: str) -> Font:
        return replace(self, family=v)

    def with_size(self, v: float) -> Font:
        return replace(self, size=v)

    def with_weight(self, v: int) -> Font:
        return replace(self, weight=v)


def _bind_Font(v: Value) -> Font | None:
    if v.kind() != strictspec.Kind.RECORD:
        return None
    f_family = v.field("family")
    f_size = v.field("size")
    f_weight = v.field("weight")
    return Font(
        family=(f_family[0].string()[0] if f_family[1] else ""),
        size=(f_size[0].number()[0] if f_size[1] else 0.0),
        weight=(f_weight[0].int()[0] if f_weight[1] else 0),
    )


@dataclass(frozen=True, kw_only=True)
class CharStyle:
    """Frozen typed binding of the "CharStyle" record. Immutable; use with_* for
    copy-on-write.
    """

    chars: str
    opacity: float
    fill: str

    def with_chars(self, v: str) -> CharStyle:
        return replace(self, chars=v)

    def with_opacity(self, v: float) -> CharStyle:
        return replace(self, opacity=v)

    def with_fill(self, v: str) -> CharStyle:
        return replace(self, fill=v)


def _bind_CharStyle(v: Value) -> CharStyle | None:
    if v.kind() != strictspec.Kind.RECORD:
        return None
    f_chars = v.field("chars")
    f_opacity = v.field("opacity")
    f_fill = v.field("fill")
    return CharStyle(
        chars=(f_chars[0].string()[0] if f_chars[1] else ""),
        opacity=(f_opacity[0].number()[0] if f_opacity[1] else 0.0),
        fill=(f_fill[0].string()[0] if f_fill[1] else ""),
    )


@dataclass(frozen=True, kw_only=True)
class GradientStop:
    """Frozen typed binding of the "GradientStop" record. Immutable; use with_* for
    copy-on-write.
    """

    offset: float
    color: str
    opacity: float

    def with_offset(self, v: float) -> GradientStop:
        return replace(self, offset=v)

    def with_color(self, v: str) -> GradientStop:
        return replace(self, color=v)

    def with_opacity(self, v: float) -> GradientStop:
        return replace(self, opacity=v)


def _bind_GradientStop(v: Value) -> GradientStop | None:
    if v.kind() != strictspec.Kind.RECORD:
        return None
    f_offset = v.field("offset")
    f_color = v.field("color")
    f_opacity = v.field("opacity")
    return GradientStop(
        offset=(f_offset[0].number()[0] if f_offset[1] else 0.0),
        color=(f_color[0].string()[0] if f_color[1] else ""),
        opacity=(f_opacity[0].number()[0] if f_opacity[1] else 0.0),
    )


@dataclass(frozen=True, kw_only=True)
class Gradient:
    """Frozen typed binding of the "Gradient" record. Immutable; use with_* for
    copy-on-write.
    """

    type: str
    stops: list[GradientStop]
    angle: float
    cx: float
    cy: float
    r: float

    def with_type(self, v: str) -> Gradient:
        return replace(self, type=v)

    def with_stops(self, v: list[GradientStop]) -> Gradient:
        return replace(self, stops=v)

    def with_angle(self, v: float) -> Gradient:
        return replace(self, angle=v)

    def with_cx(self, v: float) -> Gradient:
        return replace(self, cx=v)

    def with_cy(self, v: float) -> Gradient:
        return replace(self, cy=v)

    def with_r(self, v: float) -> Gradient:
        return replace(self, r=v)


def _bind_Gradient(v: Value) -> Gradient | None:
    if v.kind() != strictspec.Kind.RECORD:
        return None
    f_type = v.field("type")
    f_stops = v.field("stops")
    f_angle = v.field("angle")
    f_cx = v.field("cx")
    f_cy = v.field("cy")
    f_r = v.field("r")
    return Gradient(
        type=(f_type[0].string()[0] if f_type[1] else ""),
        stops=([_bind_GradientStop(e) for e in f_stops[0].items()] if f_stops[1] else []),
        angle=(f_angle[0].number()[0] if f_angle[1] else 0.0),
        cx=(f_cx[0].number()[0] if f_cx[1] else 0.0),
        cy=(f_cy[0].number()[0] if f_cy[1] else 0.0),
        r=(f_r[0].number()[0] if f_r[1] else 0.0),
    )


@dataclass(frozen=True, kw_only=True)
class BackgroundElement:
    """Frozen typed binding of the "backgroundElement" record. Immutable; use with_* for
    copy-on-write.
    """

    type: str
    id: str
    fill: Value
    opacity: float
    transform: Transform | None = None

    def with_type(self, v: str) -> BackgroundElement:
        return replace(self, type=v)

    def with_id(self, v: str) -> BackgroundElement:
        return replace(self, id=v)

    def with_fill(self, v: Value) -> BackgroundElement:
        return replace(self, fill=v)

    def with_opacity(self, v: float) -> BackgroundElement:
        return replace(self, opacity=v)

    def with_transform(self, v: Transform | None) -> BackgroundElement:
        return replace(self, transform=v)


def _bind_BackgroundElement(v: Value) -> BackgroundElement | None:
    if v.kind() != strictspec.Kind.RECORD:
        return None
    f_type = v.field("type")
    f_id = v.field("id")
    f_fill = v.field("fill")
    f_opacity = v.field("opacity")
    f_transform = v.field("transform")
    return BackgroundElement(
        type=(f_type[0].string()[0] if f_type[1] else ""),
        id=(f_id[0].string()[0] if f_id[1] else ""),
        fill=(f_fill[0] if f_fill[1] else Value(None, "json")),
        opacity=(f_opacity[0].number()[0] if f_opacity[1] else 0.0),
        transform=(_bind_Transform(f_transform[0]) if f_transform[1] else None),
    )


@dataclass(frozen=True, kw_only=True)
class RectElement:
    """Frozen typed binding of the "rectElement" record. Immutable; use with_* for
    copy-on-write.
    """

    type: str
    id: str
    x: float
    y: float
    width: float
    height: float
    fill: Value
    opacity: float
    stroke: Value
    strokeWidth: float
    strokeDasharray: str
    strokeLinecap: str
    strokeLinejoin: str
    strokeOpacity: float
    transform: Transform | None = None

    def with_type(self, v: str) -> RectElement:
        return replace(self, type=v)

    def with_id(self, v: str) -> RectElement:
        return replace(self, id=v)

    def with_x(self, v: float) -> RectElement:
        return replace(self, x=v)

    def with_y(self, v: float) -> RectElement:
        return replace(self, y=v)

    def with_width(self, v: float) -> RectElement:
        return replace(self, width=v)

    def with_height(self, v: float) -> RectElement:
        return replace(self, height=v)

    def with_fill(self, v: Value) -> RectElement:
        return replace(self, fill=v)

    def with_opacity(self, v: float) -> RectElement:
        return replace(self, opacity=v)

    def with_stroke(self, v: Value) -> RectElement:
        return replace(self, stroke=v)

    def with_strokeWidth(self, v: float) -> RectElement:
        return replace(self, strokeWidth=v)

    def with_strokeDasharray(self, v: str) -> RectElement:
        return replace(self, strokeDasharray=v)

    def with_strokeLinecap(self, v: str) -> RectElement:
        return replace(self, strokeLinecap=v)

    def with_strokeLinejoin(self, v: str) -> RectElement:
        return replace(self, strokeLinejoin=v)

    def with_strokeOpacity(self, v: float) -> RectElement:
        return replace(self, strokeOpacity=v)

    def with_transform(self, v: Transform | None) -> RectElement:
        return replace(self, transform=v)


def _bind_RectElement(v: Value) -> RectElement | None:
    if v.kind() != strictspec.Kind.RECORD:
        return None
    f_type = v.field("type")
    f_id = v.field("id")
    f_x = v.field("x")
    f_y = v.field("y")
    f_width = v.field("width")
    f_height = v.field("height")
    f_fill = v.field("fill")
    f_opacity = v.field("opacity")
    f_stroke = v.field("stroke")
    f_strokeWidth = v.field("strokeWidth")
    f_strokeDasharray = v.field("strokeDasharray")
    f_strokeLinecap = v.field("strokeLinecap")
    f_strokeLinejoin = v.field("strokeLinejoin")
    f_strokeOpacity = v.field("strokeOpacity")
    f_transform = v.field("transform")
    return RectElement(
        type=(f_type[0].string()[0] if f_type[1] else ""),
        id=(f_id[0].string()[0] if f_id[1] else ""),
        x=(f_x[0].number()[0] if f_x[1] else 0.0),
        y=(f_y[0].number()[0] if f_y[1] else 0.0),
        width=(f_width[0].number()[0] if f_width[1] else 0.0),
        height=(f_height[0].number()[0] if f_height[1] else 0.0),
        fill=(f_fill[0] if f_fill[1] else Value(None, "json")),
        opacity=(f_opacity[0].number()[0] if f_opacity[1] else 0.0),
        stroke=(f_stroke[0] if f_stroke[1] else Value(None, "json")),
        strokeWidth=(f_strokeWidth[0].number()[0] if f_strokeWidth[1] else 0.0),
        strokeDasharray=(f_strokeDasharray[0].string()[0] if f_strokeDasharray[1] else ""),
        strokeLinecap=(f_strokeLinecap[0].string()[0] if f_strokeLinecap[1] else ""),
        strokeLinejoin=(f_strokeLinejoin[0].string()[0] if f_strokeLinejoin[1] else ""),
        strokeOpacity=(f_strokeOpacity[0].number()[0] if f_strokeOpacity[1] else 0.0),
        transform=(_bind_Transform(f_transform[0]) if f_transform[1] else None),
    )


@dataclass(frozen=True, kw_only=True)
class PathElement:
    """Frozen typed binding of the "pathElement" record. Immutable; use with_* for
    copy-on-write.
    """

    type: str
    id: str
    d: str
    fill: Value
    opacity: float
    stroke: Value
    strokeWidth: float
    strokeDasharray: str
    strokeLinecap: str
    strokeLinejoin: str
    strokeOpacity: float
    transform: Transform | None = None

    def with_type(self, v: str) -> PathElement:
        return replace(self, type=v)

    def with_id(self, v: str) -> PathElement:
        return replace(self, id=v)

    def with_d(self, v: str) -> PathElement:
        return replace(self, d=v)

    def with_fill(self, v: Value) -> PathElement:
        return replace(self, fill=v)

    def with_opacity(self, v: float) -> PathElement:
        return replace(self, opacity=v)

    def with_stroke(self, v: Value) -> PathElement:
        return replace(self, stroke=v)

    def with_strokeWidth(self, v: float) -> PathElement:
        return replace(self, strokeWidth=v)

    def with_strokeDasharray(self, v: str) -> PathElement:
        return replace(self, strokeDasharray=v)

    def with_strokeLinecap(self, v: str) -> PathElement:
        return replace(self, strokeLinecap=v)

    def with_strokeLinejoin(self, v: str) -> PathElement:
        return replace(self, strokeLinejoin=v)

    def with_strokeOpacity(self, v: float) -> PathElement:
        return replace(self, strokeOpacity=v)

    def with_transform(self, v: Transform | None) -> PathElement:
        return replace(self, transform=v)


def _bind_PathElement(v: Value) -> PathElement | None:
    if v.kind() != strictspec.Kind.RECORD:
        return None
    f_type = v.field("type")
    f_id = v.field("id")
    f_d = v.field("d")
    f_fill = v.field("fill")
    f_opacity = v.field("opacity")
    f_stroke = v.field("stroke")
    f_strokeWidth = v.field("strokeWidth")
    f_strokeDasharray = v.field("strokeDasharray")
    f_strokeLinecap = v.field("strokeLinecap")
    f_strokeLinejoin = v.field("strokeLinejoin")
    f_strokeOpacity = v.field("strokeOpacity")
    f_transform = v.field("transform")
    return PathElement(
        type=(f_type[0].string()[0] if f_type[1] else ""),
        id=(f_id[0].string()[0] if f_id[1] else ""),
        d=(f_d[0].string()[0] if f_d[1] else ""),
        fill=(f_fill[0] if f_fill[1] else Value(None, "json")),
        opacity=(f_opacity[0].number()[0] if f_opacity[1] else 0.0),
        stroke=(f_stroke[0] if f_stroke[1] else Value(None, "json")),
        strokeWidth=(f_strokeWidth[0].number()[0] if f_strokeWidth[1] else 0.0),
        strokeDasharray=(f_strokeDasharray[0].string()[0] if f_strokeDasharray[1] else ""),
        strokeLinecap=(f_strokeLinecap[0].string()[0] if f_strokeLinecap[1] else ""),
        strokeLinejoin=(f_strokeLinejoin[0].string()[0] if f_strokeLinejoin[1] else ""),
        strokeOpacity=(f_strokeOpacity[0].number()[0] if f_strokeOpacity[1] else 0.0),
        transform=(_bind_Transform(f_transform[0]) if f_transform[1] else None),
    )


@dataclass(frozen=True, kw_only=True)
class TextElement:
    """Frozen typed binding of the "textElement" record. Immutable; use with_* for
    copy-on-write.
    """

    type: str
    id: str
    content: str
    x: float
    y: float
    anchor: str
    fill: Value
    font: Font | None = None
    letterSpacing: float
    charStyles: list[CharStyle]
    opacity: float
    stroke: Value
    strokeWidth: float
    strokeDasharray: str
    strokeLinecap: str
    strokeLinejoin: str
    strokeOpacity: float
    transform: Transform | None = None

    def with_type(self, v: str) -> TextElement:
        return replace(self, type=v)

    def with_id(self, v: str) -> TextElement:
        return replace(self, id=v)

    def with_content(self, v: str) -> TextElement:
        return replace(self, content=v)

    def with_x(self, v: float) -> TextElement:
        return replace(self, x=v)

    def with_y(self, v: float) -> TextElement:
        return replace(self, y=v)

    def with_anchor(self, v: str) -> TextElement:
        return replace(self, anchor=v)

    def with_fill(self, v: Value) -> TextElement:
        return replace(self, fill=v)

    def with_font(self, v: Font | None) -> TextElement:
        return replace(self, font=v)

    def with_letterSpacing(self, v: float) -> TextElement:
        return replace(self, letterSpacing=v)

    def with_charStyles(self, v: list[CharStyle]) -> TextElement:
        return replace(self, charStyles=v)

    def with_opacity(self, v: float) -> TextElement:
        return replace(self, opacity=v)

    def with_stroke(self, v: Value) -> TextElement:
        return replace(self, stroke=v)

    def with_strokeWidth(self, v: float) -> TextElement:
        return replace(self, strokeWidth=v)

    def with_strokeDasharray(self, v: str) -> TextElement:
        return replace(self, strokeDasharray=v)

    def with_strokeLinecap(self, v: str) -> TextElement:
        return replace(self, strokeLinecap=v)

    def with_strokeLinejoin(self, v: str) -> TextElement:
        return replace(self, strokeLinejoin=v)

    def with_strokeOpacity(self, v: float) -> TextElement:
        return replace(self, strokeOpacity=v)

    def with_transform(self, v: Transform | None) -> TextElement:
        return replace(self, transform=v)


def _bind_TextElement(v: Value) -> TextElement | None:
    if v.kind() != strictspec.Kind.RECORD:
        return None
    f_type = v.field("type")
    f_id = v.field("id")
    f_content = v.field("content")
    f_x = v.field("x")
    f_y = v.field("y")
    f_anchor = v.field("anchor")
    f_fill = v.field("fill")
    f_font = v.field("font")
    f_letterSpacing = v.field("letterSpacing")
    f_charStyles = v.field("charStyles")
    f_opacity = v.field("opacity")
    f_stroke = v.field("stroke")
    f_strokeWidth = v.field("strokeWidth")
    f_strokeDasharray = v.field("strokeDasharray")
    f_strokeLinecap = v.field("strokeLinecap")
    f_strokeLinejoin = v.field("strokeLinejoin")
    f_strokeOpacity = v.field("strokeOpacity")
    f_transform = v.field("transform")
    return TextElement(
        type=(f_type[0].string()[0] if f_type[1] else ""),
        id=(f_id[0].string()[0] if f_id[1] else ""),
        content=(f_content[0].string()[0] if f_content[1] else ""),
        x=(f_x[0].number()[0] if f_x[1] else 0.0),
        y=(f_y[0].number()[0] if f_y[1] else 0.0),
        anchor=(f_anchor[0].string()[0] if f_anchor[1] else ""),
        fill=(f_fill[0] if f_fill[1] else Value(None, "json")),
        font=(_bind_Font(f_font[0]) if f_font[1] else None),
        letterSpacing=(f_letterSpacing[0].number()[0] if f_letterSpacing[1] else 0.0),
        charStyles=([_bind_CharStyle(e) for e in f_charStyles[0].items()] if f_charStyles[1] else []),
        opacity=(f_opacity[0].number()[0] if f_opacity[1] else 0.0),
        stroke=(f_stroke[0] if f_stroke[1] else Value(None, "json")),
        strokeWidth=(f_strokeWidth[0].number()[0] if f_strokeWidth[1] else 0.0),
        strokeDasharray=(f_strokeDasharray[0].string()[0] if f_strokeDasharray[1] else ""),
        strokeLinecap=(f_strokeLinecap[0].string()[0] if f_strokeLinecap[1] else ""),
        strokeLinejoin=(f_strokeLinejoin[0].string()[0] if f_strokeLinejoin[1] else ""),
        strokeOpacity=(f_strokeOpacity[0].number()[0] if f_strokeOpacity[1] else 0.0),
        transform=(_bind_Transform(f_transform[0]) if f_transform[1] else None),
    )


@dataclass(frozen=True, kw_only=True)
class GroupElement:
    """Frozen typed binding of the "groupElement" record. Immutable; use with_* for
    copy-on-write.
    """

    type: str
    id: str
    elements: list[Value]
    fill: Value
    opacity: float
    stroke: Value
    strokeWidth: float
    strokeDasharray: str
    strokeLinecap: str
    strokeLinejoin: str
    strokeOpacity: float
    transform: Transform | None = None

    def with_type(self, v: str) -> GroupElement:
        return replace(self, type=v)

    def with_id(self, v: str) -> GroupElement:
        return replace(self, id=v)

    def with_elements(self, v: list[Value]) -> GroupElement:
        return replace(self, elements=v)

    def with_fill(self, v: Value) -> GroupElement:
        return replace(self, fill=v)

    def with_opacity(self, v: float) -> GroupElement:
        return replace(self, opacity=v)

    def with_stroke(self, v: Value) -> GroupElement:
        return replace(self, stroke=v)

    def with_strokeWidth(self, v: float) -> GroupElement:
        return replace(self, strokeWidth=v)

    def with_strokeDasharray(self, v: str) -> GroupElement:
        return replace(self, strokeDasharray=v)

    def with_strokeLinecap(self, v: str) -> GroupElement:
        return replace(self, strokeLinecap=v)

    def with_strokeLinejoin(self, v: str) -> GroupElement:
        return replace(self, strokeLinejoin=v)

    def with_strokeOpacity(self, v: float) -> GroupElement:
        return replace(self, strokeOpacity=v)

    def with_transform(self, v: Transform | None) -> GroupElement:
        return replace(self, transform=v)


def _bind_GroupElement(v: Value) -> GroupElement | None:
    if v.kind() != strictspec.Kind.RECORD:
        return None
    f_type = v.field("type")
    f_id = v.field("id")
    f_elements = v.field("elements")
    f_fill = v.field("fill")
    f_opacity = v.field("opacity")
    f_stroke = v.field("stroke")
    f_strokeWidth = v.field("strokeWidth")
    f_strokeDasharray = v.field("strokeDasharray")
    f_strokeLinecap = v.field("strokeLinecap")
    f_strokeLinejoin = v.field("strokeLinejoin")
    f_strokeOpacity = v.field("strokeOpacity")
    f_transform = v.field("transform")
    return GroupElement(
        type=(f_type[0].string()[0] if f_type[1] else ""),
        id=(f_id[0].string()[0] if f_id[1] else ""),
        elements=([e for e in f_elements[0].items()] if f_elements[1] else []),
        fill=(f_fill[0] if f_fill[1] else Value(None, "json")),
        opacity=(f_opacity[0].number()[0] if f_opacity[1] else 0.0),
        stroke=(f_stroke[0] if f_stroke[1] else Value(None, "json")),
        strokeWidth=(f_strokeWidth[0].number()[0] if f_strokeWidth[1] else 0.0),
        strokeDasharray=(f_strokeDasharray[0].string()[0] if f_strokeDasharray[1] else ""),
        strokeLinecap=(f_strokeLinecap[0].string()[0] if f_strokeLinecap[1] else ""),
        strokeLinejoin=(f_strokeLinejoin[0].string()[0] if f_strokeLinejoin[1] else ""),
        strokeOpacity=(f_strokeOpacity[0].number()[0] if f_strokeOpacity[1] else 0.0),
        transform=(_bind_Transform(f_transform[0]) if f_transform[1] else None),
    )


@dataclass(frozen=True, kw_only=True)
class UseElement:
    """Frozen typed binding of the "useElement" record. Immutable; use with_* for
    copy-on-write.
    """

    type: str
    id: str
    use: str
    fill: Value
    opacity: float
    stroke: Value
    strokeWidth: float
    strokeDasharray: str
    strokeLinecap: str
    strokeLinejoin: str
    strokeOpacity: float
    transform: Transform | None = None

    def with_type(self, v: str) -> UseElement:
        return replace(self, type=v)

    def with_id(self, v: str) -> UseElement:
        return replace(self, id=v)

    def with_use(self, v: str) -> UseElement:
        return replace(self, use=v)

    def with_fill(self, v: Value) -> UseElement:
        return replace(self, fill=v)

    def with_opacity(self, v: float) -> UseElement:
        return replace(self, opacity=v)

    def with_stroke(self, v: Value) -> UseElement:
        return replace(self, stroke=v)

    def with_strokeWidth(self, v: float) -> UseElement:
        return replace(self, strokeWidth=v)

    def with_strokeDasharray(self, v: str) -> UseElement:
        return replace(self, strokeDasharray=v)

    def with_strokeLinecap(self, v: str) -> UseElement:
        return replace(self, strokeLinecap=v)

    def with_strokeLinejoin(self, v: str) -> UseElement:
        return replace(self, strokeLinejoin=v)

    def with_strokeOpacity(self, v: float) -> UseElement:
        return replace(self, strokeOpacity=v)

    def with_transform(self, v: Transform | None) -> UseElement:
        return replace(self, transform=v)


def _bind_UseElement(v: Value) -> UseElement | None:
    if v.kind() != strictspec.Kind.RECORD:
        return None
    f_type = v.field("type")
    f_id = v.field("id")
    f_use = v.field("use")
    f_fill = v.field("fill")
    f_opacity = v.field("opacity")
    f_stroke = v.field("stroke")
    f_strokeWidth = v.field("strokeWidth")
    f_strokeDasharray = v.field("strokeDasharray")
    f_strokeLinecap = v.field("strokeLinecap")
    f_strokeLinejoin = v.field("strokeLinejoin")
    f_strokeOpacity = v.field("strokeOpacity")
    f_transform = v.field("transform")
    return UseElement(
        type=(f_type[0].string()[0] if f_type[1] else ""),
        id=(f_id[0].string()[0] if f_id[1] else ""),
        use=(f_use[0].string()[0] if f_use[1] else ""),
        fill=(f_fill[0] if f_fill[1] else Value(None, "json")),
        opacity=(f_opacity[0].number()[0] if f_opacity[1] else 0.0),
        stroke=(f_stroke[0] if f_stroke[1] else Value(None, "json")),
        strokeWidth=(f_strokeWidth[0].number()[0] if f_strokeWidth[1] else 0.0),
        strokeDasharray=(f_strokeDasharray[0].string()[0] if f_strokeDasharray[1] else ""),
        strokeLinecap=(f_strokeLinecap[0].string()[0] if f_strokeLinecap[1] else ""),
        strokeLinejoin=(f_strokeLinejoin[0].string()[0] if f_strokeLinejoin[1] else ""),
        strokeOpacity=(f_strokeOpacity[0].number()[0] if f_strokeOpacity[1] else 0.0),
        transform=(_bind_Transform(f_transform[0]) if f_transform[1] else None),
    )


@dataclass(frozen=True, kw_only=True)
class CenterStep:
    """Frozen typed binding of the "centerStep" record. Immutable; use with_* for
    copy-on-write.
    """

    action: str
    target: str
    axis: str

    def with_action(self, v: str) -> CenterStep:
        return replace(self, action=v)

    def with_target(self, v: str) -> CenterStep:
        return replace(self, target=v)

    def with_axis(self, v: str) -> CenterStep:
        return replace(self, axis=v)


def _bind_CenterStep(v: Value) -> CenterStep | None:
    if v.kind() != strictspec.Kind.RECORD:
        return None
    f_action = v.field("action")
    f_target = v.field("target")
    f_axis = v.field("axis")
    return CenterStep(
        action=(f_action[0].string()[0] if f_action[1] else ""),
        target=(f_target[0].string()[0] if f_target[1] else ""),
        axis=(f_axis[0].string()[0] if f_axis[1] else ""),
    )


@dataclass(frozen=True, kw_only=True)
class PlaceStep:
    """Frozen typed binding of the "placeStep" record. Immutable; use with_* for
    copy-on-write.
    """

    action: str
    target: str
    below: str
    above: str
    left: str
    right: str
    gap: float

    def with_action(self, v: str) -> PlaceStep:
        return replace(self, action=v)

    def with_target(self, v: str) -> PlaceStep:
        return replace(self, target=v)

    def with_below(self, v: str) -> PlaceStep:
        return replace(self, below=v)

    def with_above(self, v: str) -> PlaceStep:
        return replace(self, above=v)

    def with_left(self, v: str) -> PlaceStep:
        return replace(self, left=v)

    def with_right(self, v: str) -> PlaceStep:
        return replace(self, right=v)

    def with_gap(self, v: float) -> PlaceStep:
        return replace(self, gap=v)


def _bind_PlaceStep(v: Value) -> PlaceStep | None:
    if v.kind() != strictspec.Kind.RECORD:
        return None
    f_action = v.field("action")
    f_target = v.field("target")
    f_below = v.field("below")
    f_above = v.field("above")
    f_left = v.field("left")
    f_right = v.field("right")
    f_gap = v.field("gap")
    return PlaceStep(
        action=(f_action[0].string()[0] if f_action[1] else ""),
        target=(f_target[0].string()[0] if f_target[1] else ""),
        below=(f_below[0].string()[0] if f_below[1] else ""),
        above=(f_above[0].string()[0] if f_above[1] else ""),
        left=(f_left[0].string()[0] if f_left[1] else ""),
        right=(f_right[0].string()[0] if f_right[1] else ""),
        gap=(f_gap[0].number()[0] if f_gap[1] else 0.0),
    )


@dataclass(frozen=True, kw_only=True)
class GroupStep:
    """Frozen typed binding of the "groupStep" record. Immutable; use with_* for
    copy-on-write.
    """

    action: str
    targets: list[str]
    id: str

    def with_action(self, v: str) -> GroupStep:
        return replace(self, action=v)

    def with_targets(self, v: list[str]) -> GroupStep:
        return replace(self, targets=v)

    def with_id(self, v: str) -> GroupStep:
        return replace(self, id=v)


def _bind_GroupStep(v: Value) -> GroupStep | None:
    if v.kind() != strictspec.Kind.RECORD:
        return None
    f_action = v.field("action")
    f_targets = v.field("targets")
    f_id = v.field("id")
    return GroupStep(
        action=(f_action[0].string()[0] if f_action[1] else ""),
        targets=([e.string()[0] for e in f_targets[0].items()] if f_targets[1] else []),
        id=(f_id[0].string()[0] if f_id[1] else ""),
    )


@dataclass(frozen=True, kw_only=True)
class TextToPathsStep:
    """Frozen typed binding of the "textToPathsStep" record. Immutable; use with_* for
    copy-on-write.
    """

    action: str
    target: str

    def with_action(self, v: str) -> TextToPathsStep:
        return replace(self, action=v)

    def with_target(self, v: str) -> TextToPathsStep:
        return replace(self, target=v)


def _bind_TextToPathsStep(v: Value) -> TextToPathsStep | None:
    if v.kind() != strictspec.Kind.RECORD:
        return None
    f_action = v.field("action")
    f_target = v.field("target")
    return TextToPathsStep(
        action=(f_action[0].string()[0] if f_action[1] else ""),
        target=(f_target[0].string()[0] if f_target[1] else ""),
    )


