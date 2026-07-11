# Schema/loader contradiction on `groupElement.type`

## Context

Found during a code audit (2026-07) comparing the published schema against the loader's
actual behavior.

## Problem

The schema and the loader disagree about `groupElement.type`: what the schema declares valid
is not what the loader accepts (or vice versa). A document can therefore validate against the
schema yet fail (or misbehave) in the loader, or pass the loader while violating the schema —
the two sources of truth have drifted.

## Suggested fix

1. Determine which side is correct by intent (what do real documents in the corpus use?).
2. Red test: a document exercising the contradictory case, asserted against the intended
   behavior.
3. Fix the wrong side; ensure validation runs in the load path itself so schema and loader
   cannot express different opinions about the same field.
4. Scan for other schema/loader divergences — one confirmed contradiction usually has
   siblings.

## Affected area

`groupElement.type` handling in the schema and the loader.

## Effort

Small for the single field; the divergence scan is the real value (compare every schema field
against the loader's switch/branch structure once).
