Developing actions is very much like other python library development and it's
usually a good idea to use additional tools for testing, code formatting, linting, etc.

To enable such features (since `Action Server 2.0.0`), an action package may contain `dev-dependencies`
and `dev-tasks` and the `Action Server` can be used to run such tasks in the proper environment.

For instance, given the `package.yaml` example below it'd be possible to run the tests by calling:

`action-server devenv task test`

and to lint:

`action-server devenv task lint`

```
name: Action Package Example
description: Example Integrating pytest, ruff, isort and mypy
version: 0.0.1

dependencies:
  conda-forge:
    - python=3.10.14
    - uv=0.4.17
  pypi:
    - sema4ai-actions=1.0.1

dev-dependencies:
  conda-forge:
    - pytest=8.3.3
  pypi:
    - invoke
    - ruff=0.7.0
    - mypy=1.13.0

dev-tasks:
  test: pytest tests
  # If multiple lines are set, each command is run sequentially (note that each line
  # is split with shlex and run as a command without a shell -- so, keep in mind that
  # commands as `cd` or separating with `&` will not work).
  lint: |
    ruff src tests
    ruff format --check src tests
  typecheck: mpypy --follow-imports=silent --strict src tests
  prettify: |
    ruff --fix src tests
    ruff format src tests

# Note: If the pythonpath is not specified, only the directory containing
# the `package.yaml` is added to the pythonpath. i.e.: it's the same as:
# pythonpath:
#  - .
# Important: requires `Action Server 2.0.0` or later to work.
pythonpath:
  - src
  - tests

packaging:
  exclude:
    - ./tests/** # tests don't need to be packaged
    - ./.git/**
    - ./.vscode/**
    - ./devdata/**
    - ./output/**
    - ./venv/**
    - ./.venv/**
    - ./.DS_store/**
    - ./**/*.pyc
    - ./**/*.zip
```
