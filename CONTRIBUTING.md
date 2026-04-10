# Contributing

This is a contribution guide for the Sema4ai actions and action server projects and its associated libraries.

## Libraries

### Prerequisites

The tool used for Python dependency management is Poetry (`poetry`), and the commands to manage the project are run
with Invoke (`invoke` / `inv`). We use [uv](https://docs.astral.sh/uv/) for Python version management and running
tools.

Install uv first (if not already available):

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then install the dev dependencies:

```
uv run --python 3.12 pip install -r devutils/requirements.txt
```

> Note that Invoke will automatically call its commands under the Poetry context (`poetry run` prefix), therefore you
> don't need to usually activate any virtual environment before running such commands.

### Development

To start working on a library, you need to install the project's development-time dependencies. This can be done by
navigating to the package's folder and running:

```
inv install
```

### Calling Invoke tasks

To see all the available tasks, run `invoke --list` (`inv -l` for short).

For instance, linting can be run with:

```
inv lint
```

If linting fails, auto-format can be applied with:

```
inv pretty
```

Type-checking can be checked with:

```
inv typecheck
```

Docs should be generated after each change with:

```
inv docs
```

And everything combined with:

```
inv check-all
```

### Testing

Testing is done with `pytest` for the Python libraries. For javascript `jest` is the used one.

To run all tests for a given project, go to the project's folder in the monorepo and then run `inv test`. If you want
a specific test to be run, then `inv test -t path/to/test.py::function_name` would do it.

> It's recommended that you configure your favorite editor/IDE to use the test framework inside your IDE.

### Releasing

To make a new release for a library, ensure the following steps are accomplished in order:

1. Documentation is up-to-date in the _docs_ dir through the `inv docs` command and `inv check-all` is passing.
2. The version is bumped according to [semantic versioning](https://semver.org/). This can be done by running
   `inv set-version <version>`, which updates all relevant files with the new version number, then adds an entry to the
   _docs/CHANGELOG.md_ describing the changes.
3. The changes above are already committed/integrated into `master`, the test workflows in GitHub Actions are passing,
   and you're operating on the `master` branch locally.
4. You run `inv make-release` to create and push the release tag which will trigger the GitHub workflow that makes the
   release.

> To trigger a release, a commit should be tagged with the name and version of the library. The tag can be generated
> and pushed automatically with `inv make-release`. After the tag has been pushed, a corresponding GitHub Actions 
> workflow will be triggered that builds the library and publishes it to PyPI.
