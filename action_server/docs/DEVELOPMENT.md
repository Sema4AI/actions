# Development


## Requirements

- Python 3.12 or later
- invoke 2.2.0 or later

- `inv -l`

```
  build                  Build distributable .tar.gz and .wheel files
  build-executable       Build the project executable via PyInstaller.
  build-frontend         Build static .html frontend
  build-go-wrapper
  build-oauth2-config    Build static OAuth2 .yaml config.
  check-all              Run all checks
  check-tag-version      Checks if the current tag matches the latest version (exits with 1 if it
  clean                  Clean build artifacts.
  dev-frontend           Run the frontend in dev mode (starts its own localhost server using vite).
  devinstall             Install the package in develop mode and its dependencies.
  docs                   Build API documentation
  doctest                Statically verify documentation examples.
  download-rcc           Downloads RCC in the place where the action server expects it
  install                Optionally updates then also installs dependencies.
  lint                   Run static analysis and formatting checks.
  make-release           Create a release tag
  pretty                 Auto-format code and sort imports
  print-env
  publish                Publish to PyPI
  set-version            Sets a new version for the project in all the needed files
  test                   Run unittests
  test-binary            Test the binary
  test-not-integration
  test-run-in-parallel   Just runs the action server in dist/final/action-server 3 times in parallel
  typecheck              Type check code
```

- To run `inv test`: you need to set `ACTION_SERVER_TEST_ACCESS_CREDENTIALS` which is an access credential to `ci.robocloud.dev`
- To run individual tests: `python -m pytest tests/action_server_tests/mcp/test_mcp_integration.py::test_mcp_integration_with_actions_in_no_conda_mcp -v`

## Release process

To release a new version use `inv` commands (in the `/action_server` directory):

- 👉 Remember CVE cadence ando check the dependabot for items that can be fixed
  - Handle direct deps. in pyproject.toml 
  - Use `inv install --update` to bump the poetry.lock transient deps 
- First, check that the `CHANGELOG.md` is updated with the new changes (keep the `## Unreleased` section for the current release).
- `inv set-version <version>`: will set the version and update the `CHANGELOG.md` `## Unreleased` section to have the specified version/current date.
- Commit/get the changes (open a PR, merge it, get the contents locally).
- `inv make-release`: will create a tag and push it to the remote repository (which will in turn trigger the release pipeline).

## Beta releases

If for creating a normal release of version 0.0.1 you would need to create
a tag `sema4ai-action_server-0.0.1`, for creating a beta release you only
need to create a similar tag that ends in `-beta`, so it would be
`sema4ai-action_server-0.0.1-beta`. Pushing this tag will automatically
start a release pipeline that will build and upload to S3 the binaries.
Keep in mind that only one beta version can exist at a time and if you run
the pipeline again, it will overwrite the previous version.

In order to use the beta binaries, you can just download them directly.
For example this is the URL for Windows: `https://cdn.sema4.ai/action-server/beta/windows64/action-server.exe`
The name for the Linux and Mac binaries is just `action-server` and you can just replace
windows64 with linux64 or mac64 for the respective OS's. If you also need to
have a reference of what version was used, you can find the version file at:
`https://cdn.sema4.ai/action-server/beta/version.txt`
