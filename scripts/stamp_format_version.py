#!/usr/bin/env python3
"""One-time bootstrap: stamp `format_version: 1` into existing predraw documents.

The strictspec version gate is net-new to predraw: before this migration, scene and
config documents carried no version field. Every existing on-disk scene (`main.json`)
and config (`config.json`) must be stamped once, after which strictspec reads them.

Per the per-consumer bootstrap contract this script STAMPS ONLY — it never reshapes a
document. It inserts `format_version: 1` as the first key and rewrites nothing else
(key order and formatting of the remaining body are preserved as emitted by json). A
document that ALREADY carries a `format_version` is REFUSED (ambiguous: it may have
been stamped already, or hand-authored against a different gate) — such a file is
reported and left untouched, and the script exits non-zero if any refusal occurred.

Usage:
    python scripts/stamp_format_version.py <path> [<path> ...]

Each <path> may be a scene/config JSON file or a directory. Directories are scanned
recursively for `main.json` and `config.json` (these are the two gated document kinds;
imported component files are standalone Element documents and are NOT gated, so they
are intentionally skipped).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

GATE_KEY = "format_version"
GATE_VALUE = 1
GATED_FILENAMES = {"main.json", "config.json"}


def _gather(paths: list[str]) -> list[Path]:
    """Resolve input paths to the concrete gated document files to consider."""
    files: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            for name in sorted(GATED_FILENAMES):
                files.extend(sorted(p.rglob(name)))
        elif p.is_file():
            files.append(p)
        else:
            print(f"skip (not found): {p}", file=sys.stderr)
    # De-duplicate while preserving order.
    seen: set[Path] = set()
    unique: list[Path] = []
    for f in files:
        rp = f.resolve()
        if rp not in seen:
            seen.add(rp)
            unique.append(f)
    return unique


def stamp_file(path: Path) -> str:
    """Stamp one document. Returns a status: 'stamped', 'refused', or 'error'."""
    try:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error  {path}: {exc}", file=sys.stderr)
        return "error"

    if not isinstance(data, dict):
        print(f"error  {path}: top-level value is not a JSON object", file=sys.stderr)
        return "error"

    if GATE_KEY in data:
        print(f"refuse {path}: already carries {GATE_KEY} (ambiguous — not reshaping)")
        return "refused"

    # Stamp: format_version first, body order otherwise unchanged (never reshaped).
    stamped = {GATE_KEY: GATE_VALUE, **data}
    path.write_text(json.dumps(stamped, indent=2) + "\n", encoding="utf-8")
    print(f"stamp  {path}")
    return "stamped"


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2

    files = _gather(argv)
    if not files:
        print("No gated documents (main.json / config.json) found.", file=sys.stderr)
        return 1

    counts = {"stamped": 0, "refused": 0, "error": 0}
    for f in files:
        counts[stamp_file(f)] += 1

    print(
        f"\nDone: {counts['stamped']} stamped, "
        f"{counts['refused']} refused, {counts['error']} error(s)."
    )
    # Non-zero when nothing was stamped or any refusal/error occurred, so the
    # bootstrap surfaces ambiguity instead of silently succeeding.
    return 0 if (counts["stamped"] > 0 and counts["refused"] == 0 and counts["error"] == 0) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
