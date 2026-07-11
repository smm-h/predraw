# Dry-run reads `filename` where the schema/pipeline uses `path`

## Context

Found during a code audit (2026-07) of the dry-run code path.

## Problem

The dry-run implementation reads a `filename` key while the rest of the pipeline (and the
documented input format) uses `path`. Result: dry-run either silently sees nothing where the
real run sees a file, or diverges from real-run behavior on the same input — the exact
opposite of what a dry-run must guarantee (identical decisions, zero writes).

## Suggested fix

1. Red test: an input using `path` must produce the same plan under dry-run as the real run
   executes.
2. Unify on the documented key; remove the stray `filename` read (no fallback chain — one key,
   hard error if absent where required).
3. Audit the dry-run path for other key-name divergences from the real path; divergence here
   suggests the dry-run reimplements reading instead of sharing the loader. If so, the
   structural fix is to make dry-run consume the same parsed representation as the real run.

## Affected area

Dry-run input reading.

## Effort

Small for the key fix; medium if the structural share-the-loader refactor is taken (it should
be — it makes this bug class impossible).
