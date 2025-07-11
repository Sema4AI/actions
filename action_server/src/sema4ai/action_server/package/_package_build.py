import os
from logging import getLogger
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

log = getLogger(__name__)


class BuildResult(BaseModel):
    return_code: int
    package_path: Optional[str]


def build_package(
    input_dir: Path, output_dir: str, datadir: str, override: bool
) -> BuildResult:
    """
    Builds an action package.

    Note: The actions are imported in the datadir with :memory: database
        for validation (so it won't affect the real database but will still
        be able to use the environments from it).

    Args:
        input_dir: The working dir (where the package.yaml is located).
        output_dir: The output directory for the package.
        datadir: The datadir to be used.
        override: Whether an existing .zip can be overridden.

    Returns:
        The return code for the process (0 for success) and package path.
    """
    import yaml

    from sema4ai.action_server._ask_user import ask_user_input_to_proceed
    from sema4ai.action_server._cli_impl import _main_retcode
    from sema4ai.action_server._slugify import slugify
    from sema4ai.action_server.package.package_exclude import PackageExcludeHandler

    from .._errors_action_server import ActionServerValidationError

    # We expect a package.yaml to be there!
    package_yaml = input_dir / "package.yaml"
    if not package_yaml.exists():
        raise ActionServerValidationError("package.yaml required for build.")

    # Additional validations based on the package.yaml
    try:
        with open(package_yaml, "r", encoding="utf-8") as stream:
            package_yaml_contents = yaml.safe_load(stream)
    except Exception:
        raise ActionServerValidationError(
            f"Error loading file as yaml ({package_yaml})."
        )

    name = package_yaml_contents.get("name")
    if not name:
        raise ActionServerValidationError(
            f"The 'name' of the action package must be specified in the package.yaml ({package_yaml})."
        )

    slugified_name = slugify(name)
    target_zip_name = f"{slugified_name}.zip"

    output_file = Path(output_dir, target_zip_name)
    if not override and output_file.exists():
        if not ask_user_input_to_proceed(
            f"It seems that {target_zip_name} already exists. Do you want to override it? (y/n)\n"
        ):
            return BuildResult(return_code=1, package_path=None)

    packaging: dict = {}

    # packaging:
    #   # By default all files and folders in this directory are packaged when uploaded.
    #   # Add exclusion rules below (expects glob format: https://docs.python.org/3/library/glob.html)
    #   exclude:
    #    - *.temp
    #    - .vscode/**

    if isinstance(package_yaml_contents, dict):
        found = package_yaml_contents.get("packaging", {})
        if found and not isinstance(found, dict):
            raise ActionServerValidationError(
                "Expected 'packaging' section in package.yaml to be a dict."
            )
        packaging = found

    exclude_list = packaging.get("exclude")
    exclude_handler = PackageExcludeHandler()
    exclude_handler.fill_exclude_patterns(exclude_list)

    # Check the spec version
    spec_version = package_yaml_contents.get("spec-version", "v1")

    if not isinstance(spec_version, str):
        raise ActionServerValidationError(
            "Expected 'spec-version' in package.yaml to be a str."
        )

    if spec_version not in ("v1", "v2"):
        raise ActionServerValidationError(
            f"This Action Server version can only work with `Action Packages` that have 'spec-version' set to either 'v1' or 'v2'. Found: {spec_version}."
        )

    if spec_version == "v1":
        if "pythonpath" in package_yaml_contents:
            raise ActionServerValidationError(
                "The 'pythonpath' field is not supported in v1 of the Action Package specification. Please update the spec-version to v2 (this Action Package will require Action Server v2.0.0 or later to run)."
            )

    # `package metadata`` will validate everything and as it's
    # in-memory it should not affect existing data. We still need the system
    # mutex lock on the datadir due to environment updates that can't happen in
    # parallel.
    metadata_file = input_dir / "__action_server_metadata__.json"
    args_metadata = [
        "package",
        "metadata",
        "--input-dir",
        str(input_dir),
        "--db-file",
        ":memory:",
        "--output-file",
        str(metadata_file),
    ]
    if datadir:
        args_metadata.extend(["--datadir", datadir])

    returncode = _main_retcode(args_metadata, is_subcommand=True)
    if returncode != 0:
        return BuildResult(return_code=returncode, package_path=None)

    # Ok, it seems we're good to go. Package everything based on the
    # package.yaml exclude rules.
    # https://github.com/Sema4ai/actions/blob/master/action_server/docs/guides/01-package-yaml.md
    import zipfile

    with zipfile.ZipFile(output_file, "w") as zip_file:
        for path, relative_path in exclude_handler.collect_files_excluding_patterns(
            input_dir
        ):
            # Don't add the .zip itself.
            if os.path.samefile(path, output_file):
                continue
            zip_file.writestr(relative_path, path.read_bytes())

    log.info(f"Created {output_file}")
    try:
        # Remove temporary file that was created.
        os.remove(metadata_file)
    except OSError:
        pass

    return BuildResult(return_code=0, package_path=str(output_file))
