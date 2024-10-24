import json
import logging
from pathlib import Path
from typing import Any, Dict

log = logging.getLogger(__name__)


def collect_package_metadata(package_dir: Path, datadir: str) -> str | int:
    """
    Args:
        package_dir: The directory with the action package for which the
            generated metadata is required.
        datadir: The datadir to be used.

    Returns: Either the package metadata to be printed or an error code.
    """
    from fastapi.applications import FastAPI
    from sema4ai.actions._protocols import ActionsListActionTypedDict

    from sema4ai.action_server._actions_import import hook_on_actions_list
    from sema4ai.action_server._cli_impl import _main_retcode
    from sema4ai.action_server._errors_action_server import ActionServerValidationError
    from sema4ai.action_server._models import Action, ActionPackage, create_db

    args = ["start", "--db-file", ":memory:", "--dir", str(package_dir)]
    if datadir:
        args.extend(["--datadir", datadir])

    metadata: Dict[str, Any] = {}
    secrets = {}

    def on_actions_list(
        action_package: "ActionPackage",
        actions_list_result: list[ActionsListActionTypedDict],
    ):
        from sema4ai.action_server._server import build_url_api_run

        action_info: ActionsListActionTypedDict
        for action_info in actions_list_result:
            managed_params_schema = action_info.get("managed_params_schema", {})
            if managed_params_schema and isinstance(managed_params_schema, dict):
                found_secrets = {}
                for k, v in managed_params_schema.items():
                    if isinstance(v, dict) and v.get("type") in (
                        "Secret",
                        "OAuth2Secret",
                    ):
                        found_secrets[k] = v

                if found_secrets:
                    secrets[
                        build_url_api_run(action_package.name, action_info["name"])
                    ] = {
                        "actionPackage": action_package.name,
                        "action": action_info["name"],
                        "secrets": found_secrets,
                    }

        package_yaml_path = Path(package_dir) / "package.yaml"
        action_package_version: str

        if not package_yaml_path.exists():
            action_package_version = "pre-alpha"
            package_description = (
                "Action package without a 'package.yaml' file (testing only)."
            )
            log.info(
                f"The Action Package '{package_dir}' does not contain a 'package.yaml' file (proceeding with default values)."
            )
        else:
            import yaml

            with package_yaml_path.open() as f:
                package_yaml = yaml.safe_load(f)
                if not isinstance(package_yaml, dict):
                    raise ActionServerValidationError(
                        f"Error: expected {package_yaml_path} to have a dictionary as top-level."
                    )
                package_description = package_yaml.get("description", "")
                try:
                    action_package_version = str(package_yaml["version"])
                except KeyError:
                    raise ActionServerValidationError(
                        "The Action Package 'version' is not set. "
                        f"Please set the 'version' field in {package_yaml_path}."
                    )

        metadata["metadata"] = {
            "name": action_package.name,
            "description": package_description,
            "secrets": secrets,
            "action_package_version": action_package_version,
            # This is the version of the metadata itself. Should be raised
            # when the info in the metadata itself changes.
            "metadata_version": 2,  # Version 2 means that the action package has a version now.
        }

    def collect_metadata_and_cancel_startup(app: FastAPI) -> bool:
        nonlocal metadata
        openapi = app.openapi()
        metadata["openapi.json"] = openapi

        return False

    before_start = [collect_metadata_and_cancel_startup]

    with create_db(":memory:") as db, hook_on_actions_list.register(on_actions_list):
        returncode = _main_retcode(
            args, is_subcommand=True, use_db=db, before_start=before_start
        )
        if returncode != 0:
            return returncode
        if not db.all(Action):
            raise ActionServerValidationError("No actions found.")

    if not metadata:
        raise ActionServerValidationError(
            "It was not possible to collect the metadata."
        )
    return json.dumps(metadata)
