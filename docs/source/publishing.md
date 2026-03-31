# Publishing and release workflows

This project is set up to publish both documentation and Python distributions.

## Local release flow

```bash
pdm build
pdm publish
```

For safer dry runs, publish to TestPyPI first:

```bash
pdm publish --repository testpypi
```

## Trusted publishing

The repository includes a GitHub Actions workflow that publishes tagged releases
through PyPI Trusted Publishing. Configure the project on PyPI first, then tag
releases like `v0.1.0`.

## Documentation publishing

The docs workflow builds Sphinx HTML on pushes and pull requests. The separate
GitHub Pages workflow deploys the built HTML from the `main` branch.

## Read the Docs

The repository includes a `.readthedocs.yaml` file so Read the Docs can build
this project directly from the repo. The build installs the package with the
`docs` extra and then runs the Sphinx build from `docs/source`.
