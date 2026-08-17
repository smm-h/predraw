"""The CLI's presence declarations, pinned the way the effect table is.

strictcli 0.41 makes presence a declaration on every flag and every positional
argument -- exactly one of ``presence="required"``, ``presence="optional"`` or
``default=<value>`` -- and forbids a value default on a command declaring
``effect="mutating"``: on a mutating command a value the framework picked is a
value the framework writes.

Five of predraw's six commands are mutating, and every one of them took a path
or an output location that defaulted to a value nobody typed. Those fallbacks
are unchanged in behavior; what changed is that the framework no longer supplies
them, the handler does, and each one is stated in its declaration's own help.
"""

from __future__ import annotations

import json

import pytest

from predraw.cli import app

_COMMANDS = ("build", "pack", "unpack", "init", "watch", "validate")


def _command(name: str):
    return app._commands[name]


def _arg(command: str, name: str):
    return next(a for a in _command(command).args if a.name == name)


def _flag(command: str, name: str):
    return next(f for f in _command(command).flags if f.name == name)


@pytest.mark.parametrize("name", _COMMANDS)
def test_no_mutating_command_declares_a_value_default(name: str) -> None:
    command = _command(name)
    if command.effect != "mutating":
        return
    for declaration in (*command.flags, *command.args):
        assert declaration.presence != "default", f"{name} {declaration.name}"


@pytest.mark.parametrize(
    ("command", "arg", "presence"),
    [
        ("build", "path", "optional"),
        ("pack", "path", "optional"),
        ("init", "path", "optional"),
        ("watch", "path", "optional"),
        ("unpack", "file", "required"),
        ("validate", "file", "required"),
    ],
)
def test_every_positional_declares_its_presence(command: str, arg: str, presence: str) -> None:
    """``required=False, default="."`` is two spellings of one fact, and the

    ``required=`` field is gone. A path argument that may be omitted declares
    optional; one the command cannot run without declares required.
    """
    assert _arg(command, arg).presence == presence


@pytest.mark.parametrize(("command", "flag"), [("pack", "output"), ("unpack", "output")])
def test_output_flags_are_optional_rather_than_defaulted(command: str, flag: str) -> None:
    assert _flag(command, flag).presence == "optional"


def test_omitting_a_path_still_means_the_current_directory(tmp_path, monkeypatch) -> None:
    """The fallback moved into the handler; it did not change.

    ``predraw init`` with no argument initializes the current directory, which
    is what ``default="."`` used to say and what the argument's help says now.
    """
    monkeypatch.chdir(tmp_path)
    result = app.test(["init"])
    assert result.exit_code == 0
    assert (tmp_path / "main.json").exists()
    assert (tmp_path / "config.json").exists()


def test_naming_the_path_still_reaches_the_handler(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = app.test(["init", "somewhere"])
    assert result.exit_code == 0
    assert (tmp_path / "somewhere" / "main.json").exists()


# -- The --schema flag ----------------------------------------------------------


def test_schema_choices_are_the_two_real_schemas() -> None:
    """The third choice used to be the empty string.

    ``choices=["scene", "config", ""]`` with ``default=""`` made absence a value
    the caller could also type, so ``--schema ""`` and omitting the flag were
    the same request written two ways. Absence spells itself now.
    """
    entries = _flag("validate", "schema").choice_records
    assert [c.value for c in entries] == ["scene", "config"]
    assert all(c.help for c in entries)


def test_schema_declares_optional_rather_than_an_empty_default() -> None:
    assert _flag("validate", "schema").presence == "optional"


def _write_scene(tmp_path):
    path = tmp_path / "main.json"
    path.write_text(
        json.dumps({"format_version": 1, "width": 10, "height": 10, "elements": []}),
        encoding="utf-8",
    )
    return path


def test_an_omitted_schema_is_detected_from_the_file(tmp_path) -> None:
    result = app.test(["validate", str(_write_scene(tmp_path))])
    assert result.exit_code == 0
    assert "Valid scene file" in result.stdout


def test_an_empty_schema_is_refused_rather_than_read_as_absence(tmp_path) -> None:
    result = app.test(["validate", str(_write_scene(tmp_path)), "--schema", ""])
    assert result.exit_code == 1
    assert "--schema" in result.stderr


def test_a_forced_schema_overrides_detection(tmp_path) -> None:
    result = app.test(["validate", str(_write_scene(tmp_path)), "--schema", "config"])
    assert result.exit_code == 1
    assert "Invalid config file" in result.stderr
