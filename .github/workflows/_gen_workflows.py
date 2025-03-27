import subprocess
from pathlib import Path
from typing import Iterator

import yaml
from typing_extensions import override

CURDIR = Path(__file__).absolute().parent

run_in_env = "uv run --no-project --python ${{ matrix.python }} "


def collect_deps_pyprojects(root_pyproject: Path, found=None) -> Iterator[Path]:
    if found is None:
        found = set()

    import tomlkit  # allows roundtrip of toml files

    contents: dict = tomlkit.loads(root_pyproject.read_bytes().decode("utf-8"))

    dependencies = list(contents["tool"]["poetry"]["dependencies"])
    try:
        dependencies.extend(contents["tool"]["poetry"]["group"]["dev"]["dependencies"])
    except Exception:
        pass  # Ignore if it's not there.
    for key in dependencies:
        if key.startswith("sema4ai-"):
            if key == "sema4ai-data":
                continue
            if key == "sema4ai-http-helper":
                dep_name = key
            else:
                dep_name = key[len("sema4ai-") :].replace("-", "_")
            dep_pyproject = root_pyproject.parent.parent / dep_name / "pyproject.toml"
            assert dep_pyproject.exists(), f"Expected {dep_pyproject} to exist."
            if dep_pyproject not in found:
                found.add(dep_pyproject)
                yield dep_pyproject
                yield from collect_deps_pyprojects(dep_pyproject, found)


def get_python_version(pyproject):
    import tomlkit

    contents: dict = tomlkit.loads(pyproject.read_bytes().decode("utf-8"))
    dependencies = contents["tool"]["poetry"]["dependencies"]
    for key, value in dependencies.items():
        if key == "python":
            version = value.strip("^")
            assert "." in version

            # Extract the first major minor from ">=3.11.0,<3.12"
            if "," in version:
                version = version.split(",")[0]

            version = version.strip(">=")

            assert tuple(int(x) for x in version.split(".")) > (
                3,
                7,
            ), f"Bad version: {version}. pyproject: {pyproject}"
            return version
    raise RuntimeError(f"Unable to get python version in: {pyproject}")


class BaseWorkflow:
    require_node = False
    require_go = False
    fail_fast = False

    def __init__(self):
        project_dir = CURDIR.parent.parent / self.project_name
        assert project_dir.exists(), f"{project_dir} does not exist"

        self.target_file = CURDIR / f"{self.target}"
        paths = [
            f"{self.project_name}/**",
            f".github/workflows/{self.target}",
            "devutils/**",
        ]

        pyproject_toml_file = project_dir / "pyproject.toml"
        self.pyproject_toml_file = pyproject_toml_file
        self.minimum_python_version = get_python_version(pyproject_toml_file)

        dep_pyprojects = list(collect_deps_pyprojects(pyproject_toml_file))
        for dep_pyproject in dep_pyprojects:
            dep_name = dep_pyproject.parent.name
            add_dep = f"{dep_name}/**"
            if add_dep not in paths:
                paths.append(add_dep)

        self.full = {}
        self.full.update({"name": self.name})
        self.full.update(self.on_part(paths))
        self.full.update(self.defaults_part())
        self.full.update(self.jobs_part())

    def setup_python(self):
        return [
            # {
            # "name": "Set up Python ${{ matrix.python }}",
            # "uses": "actions/setup-python@v4",
            # "with": {
            #     "python-version": "${{ matrix.python }}",
            #     "cache": "poetry",
            # },
            {
                "name": "Install the latest version of uv",
                "uses": "astral-sh/setup-uv@v5",
                "with": {
                    "enable-cache": True,
                },
            },
            {
                "name": "Install Python 3.12",
                "run": "uv python install 3.12",
            },
        ]

    def matrix(self, pyversion: str):
        matrix = {
            "name": [
                f"ubuntu-py{pyversion}-devmode",
                f"windows-py{pyversion}-devmode",
                f"macos-py{pyversion}-devmode",
            ],
            "include": [
                {
                    "name": f"ubuntu-py{pyversion}-devmode",
                    "python": pyversion,
                    "os": "ubuntu-20.04",
                },
                {
                    "name": f"windows-py{pyversion}-devmode",
                    "python": pyversion,
                    "os": "windows-2019",
                },
                {
                    "name": f"macos-py{pyversion}-devmode",
                    "os": "macos-15",
                    "python": pyversion,
                },
            ],
        }
        return matrix

    def matrix_binary_release(self, pyversion: str):
        return {
            # Important: Changing os requires updating the related references in this yml.
            "os": [
                "ubuntu-20.04",
                "windows-2019",
                "macos-13",  # used for the x86_64 binary
                "macos-15",  # used for the arm64 binary
            ],
            "include": [
                {
                    "os": "ubuntu-20.04",
                    "python": pyversion,
                    "asset_path": "action_server/dist/final/action-server",
                },
                {
                    "os": "windows-2019",
                    "python": pyversion,
                    "asset_path": "action_server/dist/final/action-server.exe",
                },
                {
                    "os": "macos-15",
                    "python": pyversion,
                    "asset_path": "action_server/dist/final/action-server",
                },
                {
                    "os": "macos-13",
                    "python": pyversion,
                    "asset_path": "action_server/dist/final/action-server",
                },
            ],
        }

    def matrix_ubuntu(self, pyversion: str):
        matrix = {
            "name": [
                f"ubuntu-py{pyversion}",
            ],
            "include": [
                {
                    "name": f"ubuntu-py{pyversion}",
                    "python": pyversion,
                    "os": "ubuntu-20.04",
                },
            ],
        }
        return matrix

    def jobs_part(self):
        return {"jobs": {"build": self.build_job_part()}}

    def build_job_part(self):
        build = {}
        build.update(self.runs_on_and_strategy_part())
        build.update(self.build_steps_part())
        return build

    def build_steps_part(self):
        return {"steps": self.build_steps()}

    def runs_on_and_strategy_part(self):
        return {
            "runs-on": "${{ matrix.os }}",
            "strategy": {
                "fail-fast": self.fail_fast,
                "matrix": self.matrix(self.minimum_python_version),
            },
        }

    def defaults_part(self):
        return {"defaults": {"run": {"working-directory": f"./{self.project_name}"}}}

    def on_part(self, dep_paths):
        return {
            "on": {
                "push": {
                    "branches": ["master", "wip"],
                    "paths": dep_paths[:],
                },
                "pull_request": {
                    "branches": ["master"],
                    "paths": dep_paths[:],
                },
            }
        }

    def generate(self):
        contents = yaml.safe_dump(self.full, sort_keys=False)
        path = CURDIR / self.target
        print("Writing to ", path)
        path.write_text(
            f"""# Note: auto-generated by `_gen_workflows.py`
{contents}""",
            "utf-8",
        )

    def is_beta_in_outputs(self):
        # A step defining if it's a beta release. Needs 2 things:
        # 1. Add to the outputs
        # 2. Add to the steps
        # 3. Add to the needs
        # Can then be checked with:
        #    if: ${{ needs.<job-name>.outputs.is_beta == 'false' }}
        #
        output = {
            "is_beta": "${{ steps.check_beta.outputs.is_beta }}",
        }
        return output

    def is_beta_in_steps(self):
        step = {
            "name": "Check if this is a beta release",
            "id": "check_beta",
            "run": """
is_beta=${{ endsWith(github.ref_name, '-beta') }}
echo "is_beta: $is_beta"
echo "::set-output name=is_beta::$is_beta"
""",
        }
        return step

    def install_with_devmode(self, env: dict | None = None):
        ret = {
            "name": "Install project (not dev)",
            "if": "contains(matrix.name, '-devmode') == false",
            "run": f"{run_in_env}inv install",
        }
        if env:
            ret["env"] = env.copy()
        return ret

    def install_without_devmode(self, env: dict | None = None):
        ret = {
            "name": "Install project (dev)",
            "if": "contains(matrix.name, '-devmode')",
            "run": f"{run_in_env}inv devinstall",
        }
        if env:
            ret["env"] = env.copy()
        return ret

    def install(self, env: dict | None = None) -> list[dict]:
        return [self.install_with_devmode(env), self.install_without_devmode(env)]

    def setup_node(self):
        return {
            "name": "Setup node",
            "uses": "actions/setup-node@v3",
            "with": {
                "node-version": "20.x",
                "registry-url": "https://npm.pkg.github.com",
                "scope": "@robocorp",
            },
        }

    def setup_go(self):
        return {
            "name": "Setup go",
            "uses": "actions/setup-go@v5",
            "with": {
                "go-version": "1.23",
            },
        }

    def build_frontend(self):
        return {
            "name": "Build frontend",
            "run": f"{run_in_env}inv build-frontend",
            "env": {
                "CI": True,
                "NODE_AUTH_TOKEN": "${{ secrets.GH_PAT_READ_PACKAGES }}",
            },
        }

    def build_oauth2_config(self):
        return {
            "name": "Build OAuth2 config",
            "run": f"{run_in_env}inv build-oauth2-config",
            "env": {"GH_TOKEN": "${{ secrets.GH_PAT_GHA_TO_ANOTHER_REPO }}"},
        }

    def checkout_repo(self):
        return {
            "name": "Checkout repository and submodules",
            "uses": "actions/checkout@v3",
        }

    def install_devutils(self):
        return {
            "name": "Install devutils requirements",
            "run": f"{run_in_env}-m pip install --break-system-packages -r ../devutils/requirements.txt",
        }

    def run_lint(self):
        return {
            "name": "`inv lint`, potentially fixed with `inv pretty`",
            "if": "always()",
            "run": f"{run_in_env}inv lint",
        }

    def run_typecheck(self):
        return {
            "name": "`inv typecheck`",
            "if": "always()",
            "run": f"{run_in_env}inv typecheck",
        }

    def run_docs(self):
        return {
            "name": "`inv docs` with checking on files changed",
            "if": "always()",
            "run": f"{run_in_env}inv docs --check",
        }

    def run_docstrings_validation(self):
        return {
            "name": "`inv docs --validate`",
            "if": "always()",
            "run": f"{run_in_env}inv docs --validate",
        }

    def check_tag_version(self):
        return {
            "name": "Check tag version",
            "run": f"{run_in_env}poetry run inv check-tag-version",
            "if": "${{ !endsWith(github.ref_name, '-beta') }}",  # No need to check if it's a beta release
        }

    def build_action_server_binary(self):
        return {
            "name": "Build binary",
            "env": {
                "RC_ACTION_SERVER_FORCE_DOWNLOAD_RCC": "true",
                "RC_ACTION_SERVER_DO_SELFTEST": "true",
                "MACOS_SIGNING_CERT": "${{ secrets.MACOS_SIGNING_CERT_SEMA4AI }}",
                "MACOS_SIGNING_CERT_PASSWORD": "${{ secrets.MACOS_SIGNING_CERT_PASSWORD_SEMA4AI }}",
                "MACOS_SIGNING_CERT_NAME": "${{ secrets.MACOS_SIGNING_CERT_NAME_SEMA4AI }}",
                "APPLEID": "${{ secrets.MACOS_APP_ID_FOR_NOTARIZATION_SEMA4AI }}",
                "APPLETEAMID": "${{ secrets.MACOS_TEAM_ID_FOR_NOTARIZATION_SEMA4AI }}",
                "APPLEIDPASS": "${{ secrets.MACOS_APP_ID_PASSWORD_FOR_NOTARIZATION_SEMA4AI }}",
                "VAULT_URL": "${{ secrets.WIN_SIGN_AZURE_KEY_VAULT_URL_SEMA4AI }}",
                "CLIENT_ID": "${{ secrets.WIN_SIGN_AZURE_KEY_VAULT_CLIENT_ID_SEMA4AI }}",
                "TENANT_ID": "${{ secrets.WIN_SIGN_AZURE_KEY_VAULT_TENANT_ID_SEMA4AI }}",
                "CLIENT_SECRET": "${{ secrets.WIN_SIGN_AZURE_KEY_VAULT_CLIENT_SECRET_SEMA4AI }}",
                "CERTIFICATE_NAME": "${{ secrets.WIN_SIGN_AZURE_KEY_VAULT_CERTIFICATE_NAME_SEMA4AI }}",
                "GITHUB_EVENT_NAME": "${{ github.event_name }}",
                "GITHUB_REF_NAME": "${{ github.ref_name }}",
                "GITHUB_PR_NUMBER": "${{ github.event.pull_request.number }}",
            },
            "run": f"{run_in_env}poetry run inv build-executable --sign --go-wrapper",
        }

    def build_steps(self) -> list[dict]:
        raise NotImplementedError("Subclasses must implement this method")


class BaseTests(BaseWorkflow):
    require_build_frontend = False
    require_build_oauth2_config = False
    validate_docstrings = False

    def run_tests(self):
        return {
            "name": "Test",
            "env": {
                "GITHUB_ACTIONS_MATRIX_NAME": "${{ matrix.name }}",
                "CI_CREDENTIALS": "${{ secrets.CI_CREDENTIALS }}",
                "CI_ENDPOINT": "${{ secrets.CI_ENDPOINT }}",
                "ACTION_SERVER_TEST_ACCESS_CREDENTIALS": "${{ secrets.ACTION_SERVER_TEST_ACCESS_CREDENTIALS }}",
                "ACTION_SERVER_TEST_HOSTNAME": "${{ secrets.ACTION_SERVER_TEST_HOSTNAME }}",
            },
            "run": f"{run_in_env}inv test",
        }

    def build_steps(self) -> list[dict]:
        steps = [self.checkout_repo()] + self.setup_python() + [self.install_devutils()]

        steps.extend(self.install())

        if self.require_go:
            steps.append(self.setup_go())

        if self.require_build_frontend or self.require_node:
            steps.append(self.setup_node())

        if self.require_build_frontend:
            steps.append(self.build_frontend())

        if self.require_build_oauth2_config:
            steps.append(self.build_oauth2_config())

        run_tests = self.run_tests()
        if isinstance(run_tests, list):
            steps.extend(run_tests)
        else:
            steps.append(run_tests)

        steps.extend([self.run_lint(), self.run_typecheck(), self.run_docs()])

        if self.validate_docstrings:
            steps.append(self.run_docstrings_validation())

        return steps


class ActionServerTests(BaseTests):
    name = "Action Server Tests"
    target = "action_server_tests.yml"
    project_name = "action_server"
    require_node = True
    require_go = True
    require_build_frontend = True
    require_build_oauth2_config = True

    def run_tests(self):
        return [
            # As we want to run the tests in the binary, we do the following:
            # 1. Build the binary
            # 2. Run the unit-tests (not integration) in the current environment
            # 3. Run the integration-tests in the binary
            self.build_action_server_binary(),
            {
                "name": "Upload artifact",
                "uses": "actions/upload-artifact@v4",
                "with": {
                    "name": "action-server-${{ matrix.os }}",
                    "path": "action_server/dist/final/",
                },
            },
            {
                "name": "Test (not integration)",
                "env": {
                    "GITHUB_ACTIONS_MATRIX_NAME": "${{ matrix.name }}",
                    "CI_CREDENTIALS": "${{ secrets.CI_CREDENTIALS }}",
                    "CI_ENDPOINT": "${{ secrets.CI_ENDPOINT }}",
                    "ACTION_SERVER_TEST_ACCESS_CREDENTIALS": "${{ secrets.ACTION_SERVER_TEST_ACCESS_CREDENTIALS }}",
                    "ACTION_SERVER_TEST_HOSTNAME": "${{ secrets.ACTION_SERVER_TEST_HOSTNAME }}",
                },
                "run": f"{run_in_env}poetry run inv test-not-integration",
            },
            {
                "name": "Test (integration)",
                "env": {
                    "GITHUB_ACTIONS_MATRIX_NAME": "${{ matrix.name }}",
                    "CI_CREDENTIALS": "${{ secrets.CI_CREDENTIALS }}",
                    "CI_ENDPOINT": "${{ secrets.CI_ENDPOINT }}",
                    "ACTION_SERVER_TEST_ACCESS_CREDENTIALS": "${{ secrets.ACTION_SERVER_TEST_ACCESS_CREDENTIALS }}",
                    "ACTION_SERVER_TEST_HOSTNAME": "${{ secrets.ACTION_SERVER_TEST_HOSTNAME }}",
                },
                "run": f"{run_in_env}poetry run inv test-binary --jobs 0",
            },
        ]


class ActionServerPyPiRelease(BaseWorkflow):
    name = "Action Server PYPI Release"
    target = "action_server_pypi_release.yml"
    project_name = "action_server"
    fail_fast = True

    @override
    def on_part(self, dep_paths):
        return {
            "on": {
                "push": {
                    "tags": ["sema4ai-action_server-*"],
                    "branches": ["*-beta"],
                },
            }
        }

    @override
    def runs_on_and_strategy_part(self):
        return {
            "runs-on": "${{ matrix.os }}",
            "strategy": {
                "fail-fast": self.fail_fast,
                "matrix": self.matrix_ubuntu(self.minimum_python_version),
            },
        }

    def build_with_poetry(self):
        return {
            "name": "Build with poetry",
            "run": f"""
# Make sure that we have no binaries present when doing the build.
rm src/sema4ai/bin/rcc* -f
# Just sdist here, wheels are built in the manylinux job.
{run_in_env}poetry build -f sdist
""",
            "env": {
                "CI": True,
                "NODE_AUTH_TOKEN": "${{ secrets.GH_PAT_READ_PACKAGES }}",
                "GH_TOKEN": "${{ secrets.GH_PAT_GHA_TO_ANOTHER_REPO }}",
                "ACTION_SERVER_SKIP_DOWNLOAD_IN_BUILD": True,
            },
        }

    def upload_artifact_action_server_dist(self):
        return {
            "name": "Upload artifact",
            "uses": "actions/upload-artifact@v4",
            "with": {
                "name": "action-server-dist",
                "path": "action_server/dist/*",
            },
        }

    def upload_to_pypi(self):
        return {
            "name": "Upload to PyPI",
            "run": f"""
{run_in_env}poetry config pypi-token.pypi  ${{ secrets.PYPI_TOKEN_SEMA4AI_ACTION_SERVER }}
{run_in_env}poetry publish
""",
            "env": {
                "ACTION_SERVER_SKIP_DOWNLOAD_IN_BUILD": True,
            },
            "if": "${{ !endsWith(github.ref_name, '-beta') }}",
        }

    def build_steps(self) -> list[dict]:
        steps = [self.checkout_repo()] + self.setup_python() + [self.install_devutils()]

        steps.extend(self.install(env={"ACTION_SERVER_SKIP_DOWNLOAD_IN_BUILD": "true"}))

        steps.append(self.setup_node())

        steps.append(self.check_tag_version())
        steps.append(self.build_frontend())
        steps.append(self.build_oauth2_config())
        steps.append(self.build_with_poetry())
        steps.append(self.upload_artifact_action_server_dist())
        steps.append(self.upload_to_pypi())

        return steps


class ActionServerBinaryRelease(BaseWorkflow):
    name = "Action Server BINARY Release"
    target = "action_server_binary_release.yml"
    project_name = "action_server"
    fail_fast = True

    @override
    def on_part(self, dep_paths):
        return {
            "on": {
                "push": {
                    "tags": ["sema4ai-action_server-*"],
                    "branches": ["*-beta"],
                },
            }
        }

    @override
    def runs_on_and_strategy_part(self):
        return {
            "runs-on": "${{ matrix.os }}",
            "strategy": {
                "fail-fast": self.fail_fast,
                "matrix": self.matrix_binary_release(self.minimum_python_version),
            },
        }

    def upload_artifact_with_asset_path(self):
        return {
            "name": "Upload artifact",
            "uses": "actions/upload-artifact@v4",
            "with": {
                "name": "action-server-${{ matrix.os }}",
                "path": "action_server/dist/final/",
            },
        }

    def set_version_on_ubuntu(self):
        return {
            "name": "Set version",
            "run": f"""
{run_in_env}poetry version | awk '{{print $2}}' > version.txt
VERSION=$(cat version.txt)

echo "Version: $VERSION"
echo "version=$VERSION" >> "$GITHUB_OUTPUT"
""",
            "id": "set_version",
            "if": "${{ matrix.os == 'ubuntu-20.04' }}",
        }

    def upload_artifact_action_server_version_on_ubuntu(self):
        # Having a separate artifact for version.txt helps downstream workflows
        return {
            "name": "Upload artifact",
            "uses": "actions/upload-artifact@v4",
            "with": {
                "name": "action-server-version",
                "path": "action_server/version.txt",
            },
            "if": "${{ matrix.os == 'ubuntu-20.04' }}",
        }

    def build_steps(self) -> list[dict]:
        steps = [self.checkout_repo()] + self.setup_python() + [self.install_devutils()]

        steps.extend(self.install())

        steps.append(self.setup_node())
        steps.append(self.setup_go())

        steps.append(self.check_tag_version())
        steps.append(self.build_frontend())
        steps.append(self.build_oauth2_config())

        steps.append(self.set_version_on_ubuntu())
        steps.append(self.build_action_server_binary())
        steps.append(self.upload_artifact_with_asset_path())
        steps.append(self.upload_artifact_action_server_version_on_ubuntu())

        return steps

    def build_job_part(self):
        build = super().build_job_part()
        build["outputs"] = {"version": "${{ steps.set_version.outputs.version }}"}
        return build

    @override
    def jobs_part(self):
        jobs = super().jobs_part()
        jobs["jobs"]["deploy-s3"] = self.deploy_s3_job_part()
        jobs["jobs"].update(self.trigger_brew_workflow_job_part())
        jobs["jobs"].update(self.release_job_part())
        return jobs

    def trigger_brew_workflow_job_part(self):
        return {
            "trigger-brew-workflow": {
                "needs": ["build", "deploy-s3"],
                "defaults": {"run": {"working-directory": "."}},
                "if": "${{ needs.deploy-s3.outputs.is_beta == 'false' }}",
                "runs-on": "ubuntu-latest",
                "steps": [
                    {
                        "name": "Wait for Downloads S3 Bucket to have the right content",
                        "timeout-minutes": 5,
                        "run": """
VERSION_URL="https://cdn.sema4.ai/action-server/releases/latest/version.txt"
EXPECTED_VERSION=${{ needs.build.outputs.version }}
echo "Expected version: $EXPECTED_VERSION"
while true; do
  DOWNLOADED_VERSION=$(curl -sS $VERSION_URL)
  echo "Downloaded version: $DOWNLOADED_VERSION"
  echo "Expected version: $EXPECTED_VERSION"
    if [ "$DOWNLOADED_VERSION" = "$EXPECTED_VERSION" ]; then
      echo "Versions match."
      break
    else
      echo "Versions do not match. Retrying in 30 seconds."
    fi
    sleep 30
    done
""",
                    },
                    {
                        "name": "Trigger Brew Deploy Workflow",
                        "run": """curl -X POST \
           -H "Authorization: token ${{ secrets.GH_PAT_GHA_TO_ANOTHER_REPO }}" \
           -H "Accept: application/vnd.github.v3+json" \
           https://api.github.com/repos/sema4ai/homebrew-tools/actions/workflows/publish.yml/dispatches \
           -d '{"ref":"main","inputs":{"version":"${{ needs.sign-macos.outputs.version }}"}}'""",
                    },
                ],
            },
        }

    def release_job_part(self):
        return {
            "release": {
                "if": "${{ needs.deploy-s3.outputs.is_beta == 'false' }}",
                "permissions": {"contents": "write"},
                "needs": ["deploy-s3", "trigger-brew-workflow"],
                "defaults": {"run": {"working-directory": "."}},
                "runs-on": "ubuntu-latest",
                "steps": [
                    {"uses": "actions/checkout@v4"},
                    {
                        "name": "Create GitHub release",
                        "uses": "Roang-zero1/github-create-release-action@57eb9bdce7a964e48788b9e78b5ac766cb684803",
                        "with": {
                            "release_title": "${{ github.ref_name }}",
                            "changelog_file": "action_server/docs/CHANGELOG.md",
                            "release_text": "Binaries available as assets. Run `action-server -h` for usage instructions.",
                        },
                        "env": {"GITHUB_TOKEN": "${{ secrets.GITHUB_TOKEN }}"},
                    },
                    {
                        "uses": "actions/download-artifact@v4",
                        "with": {
                            "name": "action-server-windows-2019",
                            "path": "windows64/",
                        },
                    },
                    {
                        "uses": "actions/download-artifact@v4",
                        "with": {"name": "action-server-macos-13", "path": "macos64/"},
                    },
                    {
                        "uses": "actions/download-artifact@v4",
                        "with": {
                            "name": "action-server-macos-15",
                            "path": "macos-arm64/",
                        },
                    },
                    {
                        "uses": "actions/download-artifact@v4",
                        "with": {
                            "name": "action-server-ubuntu-20.04",
                            "path": "linux64/",
                        },
                    },
                    {
                        "name": "Print contents",
                        "run": """
          pwd
          ls -l
          echo "Windows64:"
          cd windows64
          ls -l
          cd ../macos64
          echo "MacOS64:"
          ls -l
          cd ../macos-arm64
          echo "MacOS-arm64:"
          ls -l
          cd ../linux64
          echo "Linux64:"
          ls -l
          cd ..
          echo "GitHub ref: ${{ github.ref }}"
          """,
                    },
                    {
                        "name": "Upload Linux binary",
                        "uses": "svenstaro/upload-release-action@04733e069f2d7f7f0b4aebc4fbdbce8613b03ccd",  # v2
                        "with": {
                            "repo_token": "${{ secrets.GITHUB_TOKEN }}",
                            "file": "./linux64/action-server",
                            "asset_name": "$tag-linux64",
                            "tag": "${{ github.ref }}",
                            "overwrite": True,
                        },
                    },
                    {
                        "name": "Upload MacOS binary",
                        "uses": "svenstaro/upload-release-action@04733e069f2d7f7f0b4aebc4fbdbce8613b03ccd",  # v2
                        "with": {
                            "repo_token": "${{ secrets.GITHUB_TOKEN }}",
                            "file": "./macos64/action-server",
                            "asset_name": "$tag-macos64",
                            "tag": "${{ github.ref }}",
                            "overwrite": True,
                        },
                    },
                    {
                        "name": "Upload MacOS arm binary",
                        "uses": "svenstaro/upload-release-action@04733e069f2d7f7f0b4aebc4fbdbce8613b03ccd",  # v2
                        "with": {
                            "repo_token": "${{ secrets.GITHUB_TOKEN }}",
                            "file": "./macos-arm64/action-server",
                            "asset_name": "$tag-macos-arm64",
                            "tag": "${{ github.ref }}",
                            "overwrite": True,
                        },
                    },
                    {
                        "name": "Upload Windows binary",
                        "uses": "svenstaro/upload-release-action@04733e069f2d7f7f0b4aebc4fbdbce8613b03ccd",  # v2
                        "with": {
                            "repo_token": "${{ secrets.GITHUB_TOKEN }}",
                            "file": "./windows64/action-server.exe",
                            "asset_name": "$tag-windows64",
                            "tag": "${{ github.ref }}",
                            "overwrite": True,
                        },
                    },
                ],
            }
        }

    def deploy_s3_job_part(self):
        return {
            "permissions": {
                "id-token": "write",  # required by AWS aws-actions/configure-aws-credentials
                "contents": "read",
            },
            "needs": ["build"],
            "defaults": {
                "run": {
                    "working-directory": "./action_server",
                },
            },
            "runs-on": "ubuntu-latest",
            "outputs": {"is_beta": "${{ steps.check_beta.outputs.is_beta }}"},
            "steps": self.deploy_s3_steps(),
        }

    def download_artifacts(self):
        #   - uses: actions/download-artifact@v4
        #     with:
        #       name: action-server-windows-2019
        #       path: action_server/build/windows64/
        #   - uses: actions/download-artifact@v4
        #     with:
        #       name: action-server-macos-13
        #       path: action_server/build/macos64/
        #   - uses: actions/download-artifact@v4
        #     with:
        #       name: action-server-macos-15
        #       path: action_server/build/macos-arm64/
        #   - uses: actions/download-artifact@v4
        #     with:
        #       name: action-server-ubuntu-20.04
        #       path: action_server/build/linux64/
        #   - uses: actions/download-artifact@v4
        #     with:
        #       name: action-server-version
        #       path: action_server/build/
        ret = []
        for os, path in [
            ("windows-2019", "windows64"),
            ("macos-13", "macos64"),
            ("macos-15", "macos-arm64"),
            ("ubuntu-20.04", "linux64"),
        ]:
            ret.append(
                {
                    "name": f"Download artifact {os}",
                    "uses": "actions/download-artifact@v4",
                    "with": {
                        "name": f"action-server-{os}",
                        "path": f"action_server/build/{path}/",
                    },
                }
            )

        ret.append(
            {
                "name": "Download artifact version",
                "uses": "actions/download-artifact@v4",
                "with": {
                    "name": "action-server-version",
                    "path": "action_server/build/",
                },
            }
        )
        return ret

    def deploy_s3_steps(self):
        steps = []
        steps.append(self.checkout_repo())
        steps.append(self.is_beta_in_steps())
        steps.extend(self.download_artifacts())
        steps.extend(self.upload_to_s3())
        return steps

    def upload_to_s3(self):
        ret = []

        ret.append(
            {
                "name": "Put files in s3-drop",
                "run": """
ls -l
pwd
ls -l build
mkdir s3-drop
mv build/version.txt s3-drop/
mv build/macos64 s3-drop/
mv build/macos-arm64 s3-drop/
mv build/linux64 s3-drop/
mv build/windows64 s3-drop/
ls -l s3-drop/
ver=`cat s3-drop/version.txt`
echo "actionServerVersion=${ver}" >> $GITHUB_ENV
""",
            }
        )

        ret.append(
            {
                "name": "Upload artifact",
                "uses": "actions/upload-artifact@v4",
                "with": {
                    "name": "action-server-artifacts-for-s3-${{ env.actionServerVersion }}",
                    "path": "action_server/s3-drop",
                },
            }
        )

        ret.append(
            {
                "name": "Configure AWS credentials Dropbox bucket",
                "uses": "aws-actions/configure-aws-credentials@v4",
                "with": {
                    "aws-region": "eu-west-1",
                    "role-to-assume": "arn:aws:iam::710450854638:role/github-action-robocorp-action-server",
                },
            }
        )

        ret.append(
            {
                "name": "AWS S3 copies",
                "run": """
if [ "${{ steps.check_beta.outputs.is_beta }}" = "false" ]; then
  echo "Normal release, aws sync to drop-box, full pipeline"
  aws s3 sync s3-drop s3://robocorp-action-server-build-drop-box
else
  echo "BETA RELEASE, only copy the executable for testing"
  S3_BASE_URL="s3://downloads.robocorp.com/action-server/beta"
  aws s3 cp s3-drop/version.txt $S3_BASE_URL/version.txt --cache-control max-age=120 --content-type "text/plain"
  aws s3 cp s3-drop/windows64/action-server.exe $S3_BASE_URL/windows64/action-server.exe --cache-control max-age=120 --content-type "application/octet-stream"
  aws s3 cp s3-drop/macos64/action-server $S3_BASE_URL/macos64/action-server --cache-control max-age=120 --content-type "application/octet-stream"
  aws s3 cp s3-drop/macos-arm64/action-server $S3_BASE_URL/macos-arm64/action-server --cache-control max-age=120 --content-type "application/octet-stream"
  aws s3 cp s3-drop/linux64/action-server $S3_BASE_URL/linux64/action-server --cache-control max-age=120 --content-type "application/octet-stream"
fi
""",
            }
        )

        return ret


class ActionsTests(BaseTests):
    name = "Actions Tests"
    target = "actions_tests.yml"
    project_name = "actions"
    require_node = True


class CommonTests(BaseTests):
    name = "Common Tests"
    target = "common_tests.yml"
    project_name = "common"


class HttpHelperTests(BaseTests):
    name = "HTTP Helper Tests"
    target = "http_helper_tests.yml"
    project_name = "sema4ai-http-helper"


TEST_TARGETS = [
    ActionServerTests(),
    ActionsTests(),
    HttpHelperTests(),
    CommonTests(),
    ActionServerPyPiRelease(),
    ActionServerBinaryRelease(),
]


def main():
    for t in TEST_TARGETS:
        t.generate()


def generate_dependabot_config():
    """
    We want to generate a dependabot yaml that's roughly as what's below, but
    we want to define `directories` instead of `directory` where the directories
    has the paths that have the files that need to be targeted.

    For:
    - "gomod" this is any file with a `go.mod` file
    - "pip" this is any file with a `pyproject.toml` file.
    - "github-actions" this is any file with a `workflow` file.
    - "npm" this is any file with a `package.json` file.

    Template yaml is below (note: in the code we must actually create a python dict and then dump it as yaml)

    # See: https://docs.github.com/en/code-security/dependabot/working-with-dependabot/dependabot-options-reference

    --- Template yaml ---
    version: 2
    updates:
    - package-ecosystem: "gomod"
        directory: "/"
        schedule:
        interval: "daily" # Options: "daily", "weekly", "monthly"
        allow:
        - dependency-type: "all" # Allows updates for all types of dependencies (direct and indirect)
        # Disable all pull requests (we just want notifications)
        open-pull-requests-limit: 0

    # Enable version updates for GitHub Actions
    - package-ecosystem: "github-actions"
        # Workflow files stored in the default location of `.github/workflows`
        # You don't need to specify `/.github/workflows` for `directory`. You can use `directory: "/"`.
        directory: "/"
        schedule:
        interval: "daily"
        # Disable all pull requests (we just want notifications)
        open-pull-requests-limit: 0

    - package-ecosystem: "pip"
        directory: "/"
        schedule:
        interval: "daily" # Options: "daily", "weekly", "monthly"
        allow:
        - dependency-type: "all" # Allows updates for all types of dependencies (direct and indirect)
        commit-message:
        prefix: "deps" # Prefix to add to the commit message
        # Disable all pull requests (we just want notifications)
        open-pull-requests-limit: 0

    # Enable version updates for npm
    - package-ecosystem: "npm"
        # Look for `package.json` and `lock` files in the `root` directory
        directory: "/"
        schedule:
        interval: "daily"
        # Disable all pull requests (we just want notifications)
        open-pull-requests-limit: 0
    """
    """Generate dependabot.yml configuration based on repository structure."""
    from pathlib import Path

    root = CURDIR.parent.parent

    # Find all relevant files
    go_mod_dirs = {str(f.parent.relative_to(root)) for f in root.rglob("go.mod")}
    pyproject_dirs = {
        str(f.parent.relative_to(root))
        for f in root.rglob("pyproject.toml")
        if ("/tests/" not in f.as_posix() and "/.venv/" not in f.as_posix())
    }
    package_json_dirs = {
        str(f.parent.relative_to(root))
        for f in root.rglob("package.json")
        if "node_modules" not in str(f)
    }

    # GitHub Actions is always in .github/workflows
    github_actions_dirs = {"/"}  # Root directory contains .github/workflows

    # Base configuration
    config = {"version": 2, "updates": []}

    # Helper to create ecosystem config
    def create_ecosystem_config(ecosystem, directories):
        directories = sorted(
            [
                f"{Path(directory).as_posix()}" if directory != "/" else "/"
                for directory in directories
            ]
        )
        configs = [
            {
                "package-ecosystem": ecosystem,
                "directories": directories,
                "schedule": {"interval": "daily"},
                "open-pull-requests-limit": 0,  # Only notifications, no PRs
                "allow": [{"dependency-type": "all"}],
            }
        ]

        return configs

    # Add configurations for each ecosystem
    if go_mod_dirs:
        config["updates"].extend(create_ecosystem_config("gomod", go_mod_dirs))

    if pyproject_dirs:
        config["updates"].extend(create_ecosystem_config("pip", pyproject_dirs))

    if package_json_dirs:
        config["updates"].extend(create_ecosystem_config("npm", package_json_dirs))

    # Always add GitHub Actions
    config["updates"].extend(
        create_ecosystem_config("github-actions", github_actions_dirs)
    )

    # Write the configuration file
    dependabot_file = root / ".github" / "dependabot.yml"
    dependabot_file.parent.mkdir(exist_ok=True)

    contents = yaml.safe_dump(config, sort_keys=False)
    print(f"Writing dependabot config to {dependabot_file}")

    dependabot_file.write_text(
        f"""# Note: auto-generated by `_gen_workflows.py`
{contents}""",
        encoding="utf-8",
    )


def load_curr():
    ON_PART = yaml.safe_load(
        r"""
    - name: Set up chrome for tests
      run: choco install googlechrome --ignore-checksums

"""
    )
    print(ON_PART)


if __name__ == "__main__":
    # load_curr()
    main()
    generate_dependabot_config()
