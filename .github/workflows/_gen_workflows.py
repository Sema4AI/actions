from pathlib import Path
from typing import Iterator

import yaml

CURDIR = Path(__file__).absolute().parent


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
            assert tuple(int(x) for x in version.split(".")) > (
                3,
                7,
            ), f"Bad version: {version}. pyproject: {pyproject}"
            return version
    raise RuntimeError(f"Unable to get python version in: {pyproject}")


class BaseTests:
    require_node = False
    require_build_frontend = False
    require_build_oauth2_config = False
    validate_docstrings = False
    before_run_custom_additional_steps = ()
    after_run_custom_additional_steps = ()

    run_tests = {
        "name": "Test",
        "env": {
            "GITHUB_ACTIONS_MATRIX_NAME": "${{ matrix.name }}",
            "CI_CREDENTIALS": "${{ secrets.CI_CREDENTIALS }}",
            "CI_ENDPOINT": "${{ secrets.CI_ENDPOINT }}",
            "ACTION_SERVER_TEST_ACCESS_CREDENTIALS": "${{ secrets.ACTION_SERVER_TEST_ACCESS_CREDENTIALS }}",
            "ACTION_SERVER_TEST_HOSTNAME": "${{ secrets.ACTION_SERVER_TEST_HOSTNAME }}",
        },
        "run": "inv test",
    }

    @property
    def matrix(self):
        pyversion = self.minimum_python_version
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
                    "os": "ubuntu-latest",
                },
                {
                    "name": f"windows-py{pyversion}-devmode",
                    "python": pyversion,
                    "os": "windows-latest",
                },
                {
                    "name": f"macos-py{pyversion}-devmode",
                    "os": "macos-latest",
                    "python": pyversion,
                },
            ],
        }
        return matrix

    def __init__(self):
        project_dir = CURDIR.parent.parent / self.project_name
        assert project_dir.exists(), f"{project_dir} does not exist"

        self.target_file = CURDIR / f"{self.target}"
        self.name_part = {"name": self.name}
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

        self.on_part = {
            "on": {
                "push": {
                    "branches": ["master", "wip"],
                    "paths": paths[:],
                },
                "pull_request": {
                    "branches": ["master"],
                    "paths": paths[:],
                },
            }
        }
        self.defaults_part = {
            "defaults": {"run": {"working-directory": f"./{self.project_name}"}}
        }
        self.jobs_build_in_jobs = {
            "runs-on": "${{ matrix.os }}",
            "strategy": {
                "fail-fast": False,
                "matrix": self.matrix,
            },
        }

        steps = self.build_steps()
        self.jobs_steps_in_jobs = {"steps": steps}

        build = {}
        build.update(self.jobs_build_in_jobs)
        build.update(self.jobs_steps_in_jobs)

        self.jobs = {"jobs": {"build": build}}

        self.full = {}
        self.full.update(self.name_part)
        self.full.update(self.on_part)
        self.full.update(self.defaults_part)
        self.full.update(self.jobs)

    def build_steps(self):
        devinstall = {
            "name": "Install project (dev)",
            "if": "contains(matrix.name, '-devmode')",
            "run": "inv devinstall",
        }
        install = {
            "name": "Install project (not dev)",
            "if": "contains(matrix.name, '-devmode') == false",
            "run": "inv install",
        }
        setup_node = {
            "name": "Setup node",
            "uses": "actions/setup-node@v3",
            "with": {
                "node-version": "20.x",
                "registry-url": "https://npm.pkg.github.com",
                "scope": "@robocorp",
            },
        }

        build_frontend = {
            "name": "Build frontend",
            "run": "inv build-frontend",
            "env": {
                "CI": True,
                "NODE_AUTH_TOKEN": "${{ secrets.GH_PAT_READ_PACKAGES }}",
            },
        }

        build_oauth2_config = {
            "name": "Build OAuth2 config",
            "run": "inv build-oauth2-config",
            "env": {"GH_TOKEN": "${{ secrets.GH_PAT_GHA_TO_ANOTHER_REPO }}"},
        }

        install_poetry = {
            "name": "Install poetry",
            "run": "pipx install poetry",
        }
        checkout_repo = {
            "name": "Checkout repository and submodules",
            "uses": "actions/checkout@v3",
        }

        setup_python = {
            "name": "Set up Python ${{ matrix.python }}",
            "uses": "actions/setup-python@v4",
            "with": {
                "python-version": "${{ matrix.python }}",
                "cache": "poetry",
            },
        }

        install_devutils = {
            "name": "Install devutils requirements",
            "run": "python -m pip install -r ../devutils/requirements.txt",
        }

        run_lint = {
            "name": "`inv lint`, potentially fixed with `inv pretty`",
            "if": "always()",
            "run": """
inv lint
""",
        }

        run_typecheck = {
            "name": "`inv typecheck`",
            "if": "always()",
            "run": """
inv typecheck
""",
        }

        run_docs = {
            "name": "`inv docs` with checking on files changed",
            "if": "always()",
            "run": """
inv docs --check
""",
        }

        run_docstrings_validation = {
            "name": "`inv docs --validate`",
            "if": "always()",
            "run": """
inv docs --validate
""",
        }

        steps = [
            checkout_repo,
            install_poetry,
            setup_python,
            install_devutils,
        ]

        steps.extend([install, devinstall])

        if self.require_build_frontend:
            steps.append(setup_node)
            steps.append(build_frontend)

        if self.require_build_oauth2_config:
            steps.append(build_oauth2_config)

        steps.extend(self.before_run_custom_additional_steps)

        steps.extend([self.run_tests, run_lint, run_typecheck, run_docs])

        if self.validate_docstrings:
            steps.append(run_docstrings_validation)

        steps.extend(self.after_run_custom_additional_steps)
        return steps

    def generate(self):
        contents = yaml.safe_dump(self.full, sort_keys=False)
        path = CURDIR / self.target
        print("Writing to ", path)
        path.write_text(
            f"""# Note: auto-generated by `_gen_workflows.py`
{contents}""",
            "utf-8",
        )


class ActionServerTests(BaseTests):
    name = "Action Server Tests"
    target = "action_server_tests.yml"
    project_name = "action_server"
    require_node = True
    require_build_frontend = True
    require_build_oauth2_config = True


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
        if "/tests/" not in f.as_posix()
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
        configs = [
            {
                "package-ecosystem": ecosystem,
                "directories": [
                    f"/{Path(directory).as_posix()}" if directory != "/" else "/"
                    for directory in directories
                ],
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
