import datetime
import io
import logging
import os
import zipfile
from pathlib import Path
from typing import Optional, TypedDict

import yaml
from pydantic.main import BaseModel

from ._settings import get_default_settings_dir

TEMPLATES_METADATA_URL = "https://cdn.sema4.ai/action-templates/action-templates.yaml"
TEMPLATES_PACKAGE_URL = "https://cdn.sema4.ai/action-templates/action-templates.zip"

ACTION_TEMPLATES_METADATA_FILENAME = "action-templates.yaml"

log = logging.getLogger(__name__)


class ActionTemplatesYaml(TypedDict):
    hash: str
    url: str
    date: datetime.datetime
    templates: dict[str, str]


class ActionTemplate(BaseModel):
    name: str
    description: str


class ActionTemplatesMetadata(BaseModel):
    hash: str
    url: str
    date: datetime.datetime | None
    templates: list[ActionTemplate]


def _ensure_latest_templates() -> None:
    # Ensures the existence of the latest templates package.
    # It downloads the latest templates metadata file, and compares the hash with the metadata held locally (if exists).
    # If there is no match (or metadata is not available locally), it will download the templates package.
    from sema4ai.action_server._session import session

    action_templates_dir_path = _get_action_templates_dir_path()

    os.makedirs(action_templates_dir_path, exist_ok=True)

    local_metadata = _get_local_templates_metadata()

    response = session.get(TEMPLATES_METADATA_URL)
    response.raise_for_status()

    new_metadata_content = response.text

    new_metadata = _parse_templates_metadata(new_metadata_content)

    if (
        not local_metadata
        or not new_metadata
        or local_metadata.hash != new_metadata.hash
    ):
        _download_and_unzip_templates(action_templates_dir_path)

        with open(_get_action_templates_metadata_path(), "w+") as f:
            f.write(new_metadata_content)


def _download_and_unzip_templates(action_templates_dir: Path) -> None:
    from sema4ai.action_server._session import session

    templates_response = session.get(TEMPLATES_PACKAGE_URL)

    with zipfile.ZipFile(io.BytesIO(templates_response.content)) as zip_ref:
        zip_ref.extractall(action_templates_dir)


def _get_local_templates_metadata() -> Optional[ActionTemplatesMetadata]:
    action_templates_metadata_path = _get_action_templates_metadata_path()

    if not os.path.isfile(action_templates_metadata_path):
        return None

    return _parse_templates_metadata(action_templates_metadata_path.read_text())


def _parse_templates_metadata(yaml_content: str) -> Optional[ActionTemplatesMetadata]:
    try:
        metadata: ActionTemplatesYaml = yaml.safe_load(yaml_content)

        templates: list[ActionTemplate] = []

        for name, description in metadata.get("templates", {}).items():
            templates.append(ActionTemplate(name=name, description=description))

        return ActionTemplatesMetadata(
            hash=metadata.get("hash", ""),
            url=metadata.get("url", ""),
            date=metadata.get("date", None),
            templates=templates,
        )
    except yaml.YAMLError as e:
        log.warning(f"Error reading metadata: {e}")
        return None


def _unpack_template(template_name: str, directory: str = ".") -> None:
    template_path = _get_action_templates_dir_path() / f"{template_name}.zip"

    if not os.path.isfile(template_path):
        raise RuntimeError(f"Template {template_name} does not exist")

    with zipfile.ZipFile(template_path, "r") as zip_ref:
        zip_ref.extractall(directory)


def _get_action_templates_dir_path() -> Path:
    return Path(get_default_settings_dir() / "action-templates")


def _get_action_templates_metadata_path() -> Path:
    return Path(_get_action_templates_dir_path() / ACTION_TEMPLATES_METADATA_FILENAME)


def _print_templates_list(templates: list[ActionTemplate]) -> None:
    from sema4ai.action_server.vendored_deps.termcolors import colored

    for index, template in enumerate(templates, start=1):
        log.info(colored(f" > {index}. {template.description}", "cyan"))
