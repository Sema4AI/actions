# package.yaml

The `package.yaml` file is the base file which defines everything related to the
actions available in the `Action Package`.

See below for a commented example of a `package.yaml` file:

```yaml
# Required: Defines the name of the `Action Package`.
name: My awesome cookie maker
# Required: Defines the version of the `Action Package`.
# Must be defined as 3 integers separated by dots (major, minor, patch).
version: 0.0.1

# The version of the `package.yaml` format. If not specified, defaults to v1.
# Note that newer versions of the `Action Server` can usually run an older version
# of the `package.yaml` format, but the reverse is not true (older `Action Server`
# versions may not be able to run a `package.yaml` with a newer format version).
spec-version: v2

# Required: A description of the `Action Package`.
description: This does cookies

# Required:
# Defines the Python dependencies which should be used to launch the
# actions.
# The `Action Server` will automatically create a new python environment
# based on this specification.
# Note that at this point the only operator supported is `=`.
dependencies:
  conda-forge:
    # This section is required: at least the python version must be specified.
    - python=3.10.12
    - uv=0.4.19

  pypi:
    # This section is required: at least `sema4ai-actions` must
    # be specified.
    # Note: sema4ai-actions is special case because the `Action Server`
    # has coupling with the library (so, a newer version of the `Action Server`
    # might require a newer version of `sema4ai-actions`).
    - sema4ai-actions=1.3.13
    - robocorp=1.4.3
    - pytz=2023.3

# Optional (requires Action Server 2.0.0): Defines the development dependencies
# which should be used to run development tasks.
dev-dependencies:
  conda-forge:
    - pytest=8.3.3
  pypi:
    - ruff=0.7.0
    - mypy=1.13.0

# Optional (requires Action Server 2.0.0): Defines tasks used during development (they are
# run with an environment which has both `dependencies` and `dev-dependencies`).
dev-tasks:
  test: pytest tests
  lint: ruff check src tests

# Optional (requires Action Server 2.0.0): specifies directories to add to the PYTHONPATH.
# If it is not specified, only the directory containing the `package.yaml` is added to the pythonpath.
pythonpath:
  - src
  - tests

post-install:
    # This can be used to run custom commands which will still affect the
    # environment after it is created (the changes to the environment will
    # be cached).
    - python -m robocorp.browser install chrome --isolated

packaging:
  # This section is optional.
  # By default all files and folders in this directory are packaged when uploaded.
  # Add exclusion rules below (expects glob format: https://docs.python.org/3/library/glob.html)
  exclude:
    - tests/**
    - *.temp
    - .vscode/**
```

**Note**: a `package.png` file can be added to the root of the `Action Package` to specify an icon for the `Action Package`.

> Note: previous versions of the action server used a `conda.yaml` or `action-server.yaml`,
> which are not directly compatible to `package.yaml` (so, they can't be just renamed
> directly and some changes are expected in how to define the environment).

> Running: `action-server package update` can usually be used to automatically
> upgrade a package in an older version to the new expected format.

## Changes in the package.yaml format

### Action Server 0.0.21 introduced the `package.yaml` file format.

Fields:

- `name`: string with the name of the `Action Package`.
- `version`: string with the version of the `Action Package`.
- `description`: string with the description of the `Action Package`.
- `dependencies`
  - `conda-forge`: list of conda-forge packages to install.
  - `pypi`: list of pypi packages to install.
- `post-install`: list of commands to run (once) after the environment is created.
- `packaging`:
  - `exclude`: list of glob patterns to exclude files from the `Action Package` when packaging.
- `spec-version: v1`: recommended (if not specified, the `spec-version` will default to `v1`).

**Note**: additional top-level fields can be added, but they will be ignored.

### Action Server 2.0.0 introduced support for the following changes in the `package.yaml` format:

- `spec-version: v2`: field added to specify the version of the `package.yaml` format.
- `pythonpath`: list of paths (relative to the `package.yaml` file location) to add to the `PYTHONPATH` when running actions.
  - **Important**: using `pythonpath` will make the `Action Package` incompatible with older versions of the `Action Server`.
  - If not specified, `.` (the directory with the `package.yaml` file) is added to the `PYTHONPATH`.
- `dev-tasks`: list of development tasks to run (mapping of task name to command to run).
- `dev-dependencies`: list of development dependencies to install.
  - `conda-forge`: list of conda-forge packages to install.
  - `pypi`: list of pypi packages to install.

See also:

- [Structuring Actions](./09-structuring-actions.md) for more information on how to structure python code in an `Action Package`.

- [Package Distribution](./06-package-distribution.md) for more information on distributing an `Action Package` (such as documentation, icon and building an `Action Package`).

- [Dev Tasks](./14-dev-tasks.md) for more information on how to define and run development tasks.
