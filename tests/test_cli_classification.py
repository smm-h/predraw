"""The CLI's effect classification, pinned so a change has to be deliberate.

strictcli requires every command to declare ``effect="read_only"`` or
``effect="mutating"``; there is no default and a missing declaration is a
registration-time hard error. The classification answers exactly one question:
*should a dry run record this operation rather than perform it?*

Separately, a command may declare itself ``consequential``, which is what the
framework's confirm protocol keys on. It is NOT inferred from ``mutating`` --
that inference was measured at a ~1:10 signal-to-noise ratio across the fleet
and removed, because a guardrail that fires on two thirds of a CLI's commands
trains the reflex that hollows it out.

This file pins both tables in both directions. A new command shows up as an
unexpected entry; a reclassified one shows up as a mismatch. Either way the
edit has to come here, which is the point.
"""

from typing import Any

from predraw.cli import app

# Five of predraw's six commands write files; that is what a scene builder is.
#
# `build` renders the scene and writes every output the config declares.
# `pack` writes the packed scene to --output. `unpack` writes main.json and a
# components/ tree. `init` creates the starter project. `watch` is a build loop
# and inherits `build`'s classification for the same reason.
#
# `validate` is the one read: it loads a JSON file, runs the schema validator
# and prints the verdict. It never rewrites the file it checked.
EFFECTS = {
    "build": "mutating",
    "pack": "mutating",
    "unpack": "mutating",
    "init": "mutating",
    "watch": "mutating",
    "validate": "read_only",
}

# Empty, deliberately.
#
# `consequential` means "this act is worth interrupting someone for", and none
# of these are. Every write goes to a path the user named on the same command
# line -- the project directory, --output, the init target -- so the effect is
# exactly the one they asked for and nothing further. `init` additionally
# refuses outright when main.json already exists rather than clobbering it.
#
# The closest candidate is `unpack`, whose --output defaults to `.` and which
# will overwrite an existing main.json there. That is a sharp edge, but it is a
# sharp edge in `unpack`'s default, and the fix for a bad default is a better
# default or a handler-level guard -- not a blind `Proceed? [y/N]` in front of
# every correct unpack too. predraw is also run from build scripts and file
# watchers, where an unanswerable prompt is a hang, not a safety net.
CONSEQUENTIAL: set[str] = set()

# strictcli owns these four names at every level -- command flags, flag-set
# flags, mutex-group flags and app globals alike. `yes` names no framework flag
# any more (the skip flag is --approve-consequential) but stays banned so a
# consumer cannot restate it in the spelling the rename removed.
#
# predraw had a real collision here: `build` declared its own `--dry-run`.
# It is gone; the handler reads `ctx.dry_run` and passes it to `_build`.
RESERVED_FLAG_NAMES = {
    "dry-run",
    "approve-consequential",
    "quiet",
    "verbose",
    "yes",
}


def _registry(container: Any) -> dict[str, Any]:
    """App stores commands on `_commands`, Group on `commands`.

    Written as an explicit None test rather than `or`, because an app whose
    commands all live in groups has an EMPTY `_commands` dict, and `or` would
    fall through it to an attribute App does not have.
    """
    found = getattr(container, "_commands", None)
    return container.commands if found is None else found


def _walk() -> dict[str, Any]:
    """Map dotted command path -> Command for every registered command."""
    found: dict[str, Any] = {}

    def visit(container: Any, prefix: str) -> None:
        for name, cmd in _registry(container).items():
            found[prefix + name] = cmd
        for name, group in container._groups.items():
            visit(group, prefix + name + ".")

    visit(app, "")
    return found


def test_every_command_is_classified_exactly_as_reviewed() -> None:
    declared = {path: cmd.effect for path, cmd in _walk().items()}
    assert declared == EFFECTS


def test_consequential_declarations_match_the_reviewed_set() -> None:
    """Both directions matter.

    A missing declaration removes a prompt somebody decided was owed; a stray
    one puts a blind ``Proceed? [y/N]`` in front of routine work and hangs
    every script and file watcher that calls it.
    """
    declared = {path for path, cmd in _walk().items() if cmd.consequential}
    assert declared == CONSEQUENTIAL


def test_no_command_redeclares_a_framework_reserved_flag_name() -> None:
    """A collision is a registration-time error, so reaching here means it built.

    This is the regression pin for the `build --dry-run` collision that broke
    the CLI at import time under strictcli 0.36.0.
    """
    assert not ({f.name for f in app._global_flags} & RESERVED_FLAG_NAMES)
    for path, cmd in _walk().items():
        names = {f.name for f in cmd.flags}
        collisions = names & RESERVED_FLAG_NAMES
        assert not collisions, f"'{path}' declares reserved flag(s) {sorted(collisions)}"


def test_build_dry_run_comes_off_the_context(tmp_path) -> None:
    """`predraw build --dry-run` still prints a plan and writes nothing.

    The flag moved from a declared command flag to the framework-owned quartet,
    so this exercises the whole path: pre-scan, Context, handler, `_build`.
    """
    import json

    (tmp_path / "main.json").write_text(
        json.dumps(
            {
                "format_version": 1,
                "width": 200,
                "height": 100,
                "elements": [
                    {"type": "rect", "x": 0, "y": 0, "width": 50, "height": 30, "fill": "#f00"}
                ],
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "config.json").write_text(
        json.dumps({"format_version": 1, "outputs": [{"format": "svg", "path": "output.svg"}]}),
        encoding="utf-8",
    )

    result = app.test(["build", str(tmp_path), "--dry-run"])

    assert result.exit_code == 0
    assert not (tmp_path / "output.svg").exists()
