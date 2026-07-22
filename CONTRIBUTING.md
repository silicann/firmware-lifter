# Development

firmware-lifter uses [`hatch`](https://hatch.pypa.io/) and the `pyproject.toml` to organise the project.

Dependencies are listed in the `pyproject.toml` and will be installed upon running python commands within the virtual environment created by `hatch`.


# Linting, formatting & testing

- formatting: `just apply-style`
- linting: `just lint`
- test: `just test`
    - with coverage check: `just test --cover`


# Release workflow

1. Update `CHANGELOG.md` by moving relevant entries from `Unreleased` into a
   new version section.
1. Run the *just* target "release" with a version part, e.g. `just release minor`
1. Push commit and tags manually: `git push && git push --tags`
1. Upload to [pypi](https://pypi.org/): `just publish`
