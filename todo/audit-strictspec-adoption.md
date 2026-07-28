# Audit the strictspec adoption (external session hand-off)

An external session migrated this repo's validation engine from jsonschema to
strictspec 0.1.0 (now a declared dependency in pyproject). The migration is
committed but NOT released — it should ride along with this repo's next
release. This todo exists so the work can be audited first.

## What changed and why

Why: strictspec became the fleet's single validation authority (hard errors,
format versioning, generated validators); this repo's hand-rolled
jsonschema layer was replaced by it.

- `predraw/schema/scene.schema.toml` + `config.schema.toml` (strictspec
  surface syntax) replace the two deleted `*.schema.json`; `strictspec.toml`
  manifest added.
- Generated validators `predraw/_scene_validator.py` / `_config_validator.py`
  (committed, chmod 444, regen via `strictspec gen`).
- `validate_scene`/`validate_config` keep their dict-in/`list[str]`-out shape
  but delegate to the generated validators; `load_scene`/`load_config` now
  hard-error (`SchemaValidationError`).
- NET-NEW BREAKING: documents require integer `format_version = 1`
  (`STRICTSPEC_GATE_ABSENT` otherwise). Remediation:
  `scripts/stamp_format_version.py` (stamps only, refuses already-stamped).
- The loader's 4 hand-rolled alias fallbacks were deleted; 8 alias pairs are
  declared in-schema (both-present is now a hard error) with one
  canonicalization pass post-validation.
- Two additional narrowings: `use` elements require explicit `type: "use"`;
  `elements` is required on scenes.
- jsonschema removed from pyproject/uv.lock; changelog entries added
  (breaking + coverage). Suite: 67 passed.

## Audit points (known leftovers from the external audit)

1. `scene.schema.toml` references a `gap-note.md` (~lines 180, 468) that does
   not exist in this repo — dangling doc reference; fix or drop.
2. The changelog breaking entry does not explicitly enumerate the
   "elements now required" narrowing (only implicitly).
3. `loader._parse_element` retains a dead type-inference default
   (`"use" if "use" in data else "group"`) — dead post-validation; delete.
