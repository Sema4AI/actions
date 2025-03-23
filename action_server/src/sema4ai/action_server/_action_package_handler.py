import logging
from pathlib import Path

log = logging.getLogger(__name__)


def _raise_deprecated_conda(found: Path):
    from sema4ai.action_server._settings import is_frozen
    from sema4ai.action_server.vendored_deps.action_package_handling.cli_errors import (
        ActionPackageError,
    )

    if is_frozen():
        cmd = "action-server"
    else:
        cmd = "python -m sema4ai.action_server"
    raise ActionPackageError(
        "Deprecated: The file for defining the environment is now `package.yaml`.\n"
        f"Using {found} is no longer supported.\n"
        "It's not a one to one mapping for but\n"
        f"`{cmd} package update` can be used to make most of the needed changes.\n"
        "See: https://github.com/Sema4AI/actions/blob/master/action_server/docs/guides/01-package-yaml.md for more details."
    )


class ActionPackageHandler:
    def __init__(self, action_package_dir: str, datadir: Path):
        import os

        import yaml

        from sema4ai.action_server.vendored_deps.action_package_handling.cli_errors import (
            ActionPackageError,
        )

        from ._errors_action_server import ActionServerValidationError
        from ._settings import is_frozen

        self._action_package_dir = action_package_dir

        datadir = datadir.absolute()
        import_path = Path(action_package_dir).absolute()
        if not import_path.exists():
            raise ActionPackageError(
                f"Unable to import action package from directory: {import_path} "
                "(directory does not exist).",
            )
        if not import_path.is_dir():
            raise ActionPackageError(
                f"Error: expected {import_path} to be a directory."
            )

        self._datadir = datadir

        # Verify if it's actually a proper package (meaning that it has
        # the package.yaml as well as actions we can run).
        original_package_yaml = import_path / "package.yaml"

        action_package_name = ""
        package_yaml_exists = original_package_yaml.exists()
        package_yaml_contents = None
        if package_yaml_exists:
            try:
                with open(original_package_yaml, "r", encoding="utf-8") as stream:
                    package_yaml_contents = yaml.safe_load(stream)
            except Exception:
                raise ActionPackageError(
                    f"Error loading file as yaml ({original_package_yaml})."
                )
            if not isinstance(package_yaml_contents, dict):
                raise ActionPackageError(
                    f"Error: expected {original_package_yaml} to have a dictionary as top-level."
                )

            version = package_yaml_contents.get("version")
            if version is None:
                log.warn(
                    f"Expected {original_package_yaml} to have a 'version' field (without a version it's not possible to publish the action package)."
                )

            n = package_yaml_contents.get("name")
            if n:
                action_package_name = n
            else:
                log.warn(
                    f"Expected {original_package_yaml} to have a 'name' field (using the directory name as the action package name instead)."
                )

        if not action_package_name:
            action_package_name = import_path.name

        if not package_yaml_exists:
            for yaml_name in ("action-server.yaml", "conda.yaml"):
                if (import_path / yaml_name).exists():
                    _raise_deprecated_conda(import_path / yaml_name)

            if is_frozen() and not os.environ.get(
                "SEMA4AI_INTEGRATION_TEST_ACTION_SERVER_EXECUTABLE"
            ):
                raise ActionServerValidationError(
                    f"Unable to proceed because `package.yaml` is not available at: {original_package_yaml}."
                )

        self._package_yaml_exists = package_yaml_exists
        self._action_package_name = action_package_name
        self._original_package_yaml = original_package_yaml
        self._import_path = import_path
        self._package_yaml_contents = package_yaml_contents
        self._pythonpath_entries: tuple[str, ...] | None = None

    @property
    def package_yaml_contents(self) -> dict | None:
        return self._package_yaml_contents

    @property
    def import_path(self) -> Path:
        return self._import_path

    @property
    def original_package_yaml(self) -> Path:
        return self._original_package_yaml

    @property
    def package_yaml_exists(self) -> bool:
        return self._package_yaml_exists

    @property
    def action_package_name(self) -> str:
        return self._action_package_name

    @property
    def package_root(self) -> str:
        return str(self._original_package_yaml.parent.absolute())

    def get_pythonpath_entries(self) -> tuple[str, ...]:
        """
        Returns:
            Tuple with the entries of the pythonpath (as the user entered them in the package.yaml,
            usually relative to the package.yaml file, although absolute paths are also accepted).
        """
        if self._pythonpath_entries is not None:
            return self._pythonpath_entries

        from sema4ai.action_server._errors_action_server import (
            ActionServerValidationError,
        )

        pythonpath_entries: list[str] = []
        if not self._package_yaml_contents:
            pythonpath_entries.append(".")
        else:
            # Extract the PYTHONPATH from the package.yaml contents.
            pythonpath_in_yaml = self._package_yaml_contents.get("pythonpath")
            if not pythonpath_in_yaml:
                pythonpath_entries.append(".")
            else:
                # Validate that the pythonpath is a list of strings.
                if not isinstance(pythonpath_in_yaml, list):
                    raise ActionServerValidationError(
                        f"The 'pythonpath' field in package.yaml must be a list of strings. Found: {pythonpath_in_yaml!r} (type: {type(pythonpath_in_yaml)})"
                    )

                for p in pythonpath_in_yaml:
                    if not isinstance(p, str):
                        raise ActionServerValidationError(
                            f"The 'pythonpath' field in package.yaml must be a list of strings. Found list with item: {p!r} (type: {type(p)})"
                        )

                    pythonpath_entries.append(p)

        self._pythonpath_entries = tuple(pythonpath_entries)
        return self._pythonpath_entries

    def bootstrap_environment(self, devenv: bool = False) -> tuple[str, dict]:
        """
        Args:
            devenv: Whether the environment is being bootstrapped for the dev
                environment.

        Returns:
            Tuple of condahash and the environment variables.

        Raises:
            ActionPackageError: If it was not possible to bootstrap the environment.
        """
        import os

        from sema4ai.action_server._errors_action_server import (
            ActionServerValidationError,
        )
        from sema4ai.action_server.vendored_deps.action_package_handling.cli_errors import (
            ActionPackageError,
        )
        from sema4ai.action_server.vendored_deps.termcolors import bold_yellow

        if not self.package_yaml_exists:
            log.info(
                """Adding action without a managed environment (package.yaml unavailable).
    Note: no virtual environment will be used for the imported actions, they'll be run in the same environment used to run the action server."""
            )
            condahash = "<unmanaged>"
            use_env = {}
        else:
            from ._rcc import get_rcc

            if self._package_yaml_contents:
                # Verify the version of the package.yaml file.
                spec_version = self._package_yaml_contents.get("spec-version")
                if not spec_version:
                    log.warn(
                        bold_yellow(
                            "The `spec-version` field is missing from `package.yaml`.\n"
                            "It's recommended to update your package.yaml file to include the `spec-version` field.\n"
                            "See: https://github.com/Sema4AI/actions/blob/master/action_server/docs/guides/01-package-yaml.md for more details."
                        )
                    )

                elif spec_version not in ("v1", "v2"):
                    raise ActionServerValidationError(
                        f"This version of the Action Server only supports `spec-version` `v1` or `v2`. Found: `{spec_version}`."
                    )

            log.info(
                "Action package seems ok. "
                "Bootstrapping RCC environment (please wait, this can take a long time)."
            )
            rcc = get_rcc()

            condahash = rcc.get_package_yaml_hash(self._original_package_yaml, devenv)

            env_info = rcc.create_env_and_get_vars(
                self._datadir, self._original_package_yaml, condahash, devenv
            )
            if not env_info.success:
                raise ActionPackageError(
                    f"It was not possible to bootstrap the RCC environment. "
                    f"Error: {env_info.message}"
                )
            if not env_info.result:
                raise ActionPackageError(
                    "It was not possible to get the environment when "
                    "bootstrapping RCC environment."
                )
            use_env = env_info.result.env

        pythonpath_entries = self.get_pythonpath_entries()

        if pythonpath_entries != ["."]:
            if self._package_yaml_contents:
                spec_version = self._package_yaml_contents.get("spec-version")
                if not spec_version:
                    log.critical(
                        "The `pythonpath` entries in `package.yaml` are only supported in `spec-version: v2`.\n"
                        f"Please update {self._original_package_yaml}\n  to include the `spec-version` field.\n"
                        "See: https://github.com/Sema4AI/actions/blob/master/action_server/docs/guides/01-package-yaml.md for more details."
                    )

        package_root = self.package_root
        abspath_entries = []
        for p in pythonpath_entries:
            if not os.path.isabs(p):
                p = os.path.join(package_root, p)
            entry = os.path.abspath(p)
            if not os.path.exists(entry):
                log.critical(
                    f"The pythonpath entry: {p} does not exist in the filesystem (in {package_root}/package.yaml)."
                )
            abspath_entries.append(entry)

        pythonpath = os.pathsep.join(abspath_entries)

        if "PYTHONPATH" in use_env:
            use_env["PYTHONPATH"] = use_env["PYTHONPATH"] + os.pathsep + pythonpath
        else:
            use_env["PYTHONPATH"] = pythonpath

        return condahash, use_env
