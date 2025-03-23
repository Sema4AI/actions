# ⚡️ sema4ai-build-common

A Python library containing common utilities for building Sema4AI projects.

-- it deals with things such as building and signing executables.

Notes on how it works:

- The `sema4ai.build_common.workflows` module contains the entry points that should be called by other projects.

- `build_and_sign_executable` should be called to actually build the executable and sign it.

- This function handles building and signing an executable, with these main steps:

  - Build: Uses PyInstaller to create an executable from Python code. It always builds in "not onefile" mode, meaning it creates a directory containing the executable and its dependencies.

  - Signing (Optional): If the sign parameter is True:

    - On macOS: Signs using macOS code signing and properly notarizes afterwards
    - On Windows: Signs using Windows code signing

  - Go Wrapper (Optional): If go_wrapper is True:

    - Zips the PyInstaller-built application assets
    - Builds a Go wrapper around the application
    - Creates a final executable that combines both
    - Signs the final executable if signing is enabled

- Requirements for build:

  - A `<project-name>.spec` file must be available in the root of the project with the pyinstaller spec to build the executable (the build process will use it to build with pyinstaller)

  - The `go-wrapper` for the app must also be in the root of the project (at this point, each app needs its own, although in the future a common base should probably be used). The build utilities will put a `version.txt` and an `assets.zip` in `/go-wrapper/assets` (if the `/go-wrapper` directory does not exist the build will fail).

Example of integration in `sai-server` -- note that `sai-server` uses typer to create a command line instead of `invoke`:

```python
import typer

app = typer.Typer()

@app.command()
def build_executable(
    debug: bool = typer.Option(False, help="Build in debug mode"),
    ci: bool = typer.Option(
        True, help="Build in CI mode, disabling interactive prompts"
    ),
    dist_path: Path = typer.Option("dist", help="Path to the dist directory"),
    sign: bool = typer.Option(False, help="Sign the executable"),
    go_wrapper: bool = typer.Option(False, help="Build the Go wrapper too"),
    version: str | None = typer.Option(
        None, help="Version of the executable (gotten from github tag/pr if not passed)"
    ),
) -> None:
    """Build the project executable via PyInstaller."""
    from sema4ai.build_common.root_dir import get_root_dir
    from sema4ai.build_common.workflows import build_and_sign_executable

    from sema4ai.action_server import __version__

    if version is None:
        version = __version__  # Get version from the project...

    root_dir = get_root_dir()
    build_and_sign_executable(
        root_dir=root_dir,
        name="action-server",
        debug=debug,
        ci=ci,
        dist_path=root_dir / dist_path,
        sign=sign,
        go_wrapper=go_wrapper,
        version=__version__,
    )
```

The job that integrates it needs several environment variables for the signing and version gathering
-- Note that the version is gotten from the tag or pr or branch name (based on the `GITUB_EVENT_NAME`,
`GITHUB_REF_NAME` and `GITHUB_PR_NUMBER`), but applications that handle the version differently
could pass the version in the command-line or call to `build_and_sign_executable`.

```yaml
- name: Build SAI Server binary
  run: uv run python -m sai_tasks build-executable --sign --go-wrapper
  env:
    MACOS_SIGNING_CERT: ${{ secrets.MACOS_SIGNING_CERT_SEMA4AI }}
    MACOS_SIGNING_CERT_PASSWORD: ${{ secrets.MACOS_SIGNING_CERT_PASSWORD_SEMA4AI }}
    MACOS_SIGNING_CERT_NAME: ${{ secrets.MACOS_SIGNING_CERT_NAME_SEMA4AI }}

    APPLEID: ${{ secrets.MACOS_APP_ID_FOR_NOTARIZATION_SEMA4AI }}
    APPLETEAMID: ${{ secrets.MACOS_TEAM_ID_FOR_NOTARIZATION_SEMA4AI }}
    APPLEIDPASS: ${{ secrets.MACOS_APP_ID_PASSWORD_FOR_NOTARIZATION_SEMA4AI }}

    VAULT_URL: ${{ secrets.WIN_SIGN_AZURE_KEY_VAULT_URL_SEMA4AI }}
    CLIENT_ID: ${{ secrets.WIN_SIGN_AZURE_KEY_VAULT_CLIENT_ID_SEMA4AI }}
    TENANT_ID: ${{ secrets.WIN_SIGN_AZURE_KEY_VAULT_TENANT_ID_SEMA4AI }}
    CLIENT_SECRET: ${{ secrets.WIN_SIGN_AZURE_KEY_VAULT_CLIENT_SECRET_SEMA4AI }}
    CERTIFICATE_NAME: ${{ secrets.WIN_SIGN_AZURE_KEY_VAULT_CERTIFICATE_NAME_SEMA4AI }}

    GITHUB_EVENT_NAME: ${{ github.event_name }}
    GITHUB_REF_NAME: ${{ github.ref_name }}
    GITHUB_PR_NUMBER: ${{ github.event.pull_request.number }}
```
