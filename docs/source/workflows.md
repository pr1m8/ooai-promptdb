# CI and workflow overview

The repository ships with three GitHub Actions workflows:

## `ci.yml`

Runs Ruff, MyPy, pytest, and a strict Sphinx build on pushes and pull requests.

## `docs.yml`

Builds the documentation and uploads the generated HTML as a workflow artifact.

## `release.yml`

Publishes distributions to PyPI using Trusted Publishing whenever a tag matching
`v*` is pushed.

## Suggested branch protections

- require `ci` to pass before merge
- require linear history or squash merge
- restrict release tags to maintainers
- protect `main`
