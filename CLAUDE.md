# predraw

## Release workflow

This project uses [rlsbl](https://github.com/smm-h/rlsbl) for release orchestration.

- Update CHANGELOG.md with a `## X.Y.Z` entry describing changes
- Run `rlsbl release [patch|minor|major]` to bump version and create a GitHub Release
- CI handles publishing automatically via the publish workflow
- Never publish manually — always use `rlsbl release`
<<<<<<< /home/m/Projects/predraw/tmpthd8ts5m.ours
- Requires `NPM_TOKEN` secret on GitHub (for npm projects)
=======
- Requires NPM_TOKEN secret on GitHub (Settings > Secrets > Actions)
>>>>>>> /home/m/Projects/predraw/tmpja8cwyqh.theirs
- Use `rlsbl release --dry-run` to preview a release without making changes
- Always release with `rlsbl release [patch|minor|major] --registry pypi` to keep pyproject.toml as the version source.

## Conventions

- No tokens or secrets in command-line arguments (use env vars or config files)
- All file writes to shared state should be atomic (write to tmp, then rename)
- External calls (APIs, CLI tools) must have timeouts and graceful fallbacks
- Use `npm link` (npm) or `uv pip install -e .` (Python) for local development
- CI runs smoke tests on every push; manual testing for UI/UX changes
