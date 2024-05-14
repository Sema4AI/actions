import io
import datetime
import logging
import os
import zipfile
import yaml
import requests
from pathlib import Path
from typing import Dict, List, Union, Optional
from pydantic.main import BaseModel

from ._settings import get_default_settings_dir

TEMPLATES_METADATA_URL = "https://downloads.robocorp.com/action-templates/action-templates.yaml"
TEMPLATES_PACKAGE_URL = "https://downloads.robocorp.com/action-templates/action-templates.zip"

ACTION_TEMPLATES_METADATA_FILENAME = "action-templates.yaml"

ACTION_TEMPLATES_DIR = Path(f"{get_default_settings_dir()}/action-templates")
ACTION_TEMPLATES_METADATA_PATH = Path(f"{ACTION_TEMPLATES_DIR}/{ACTION_TEMPLATES_METADATA_FILENAME}")

log = logging.getLogger(__name__)


class ActionTemplate(BaseModel):
    name: str
    description: str


class ActionTemplatesMetadata(BaseModel):
    hash: str
    url: str
    date: datetime.datetime
    templates: List[ActionTemplate]


def _ensure_latest_templates():
    # Ensures the existence of the latest templates package.
    # It downloads the latest templates metadata file, and compares the hash with
    # the metadata hold locally (if exists).
    # If there is no match (or metadata is not available locally), it will download
    # the templates package.

    os.makedirs(ACTION_TEMPLATES_DIR, exist_ok=True)

    local_metadata = _get_local_templates_metadata()

    new_metadata_content = requests.get(TEMPLATES_METADATA_URL).text
    new_metadata = _parse_templates_metadata(new_metadata_content)

    # @TODO:
    # Provide fallback when no templates are available.
    if not local_metadata and not new_metadata:
        log.critical("No templates available")
        return

    if not local_metadata or local_metadata.hash != new_metadata.hash:
        _download_and_unzip_templates(ACTION_TEMPLATES_DIR)

        with open(ACTION_TEMPLATES_METADATA_PATH, "w+") as f:
            f.write(new_metadata_content)


def _download_and_unzip_templates(action_templates_dir: Path):
    # Downloads the action templates package and unpacks particular template zip files.

    templates_response = requests.get(TEMPLATES_PACKAGE_URL)

    with zipfile.ZipFile(io.BytesIO(templates_response.content)) as zip_ref:
        zip_ref.extractall(action_templates_dir)

def _get_local_templates_metadata() -> Optional[ActionTemplatesMetadata]:
    # Loads templates metadata YAML file.

    if not os.path.isfile(ACTION_TEMPLATES_METADATA_PATH):
        return None

    return _parse_templates_metadata(ACTION_TEMPLATES_METADATA_PATH.read_text())

def _parse_templates_metadata(yaml_content: str) -> Optional[ActionTemplatesMetadata]:
    # Parses templates YAML metadata into ActionTemplatesMetadata model.

    try:
        metadata: Dict[str, Union[str, Dict[str, str]]] = yaml.safe_load(yaml_content)

        templates: List[ActionTemplate] = list()

        for name, description in metadata["templates"].items():
            templates.append(ActionTemplate(name=name, description=description))

        return ActionTemplatesMetadata(
            hash=metadata.get("hash"),
            url=metadata.get("url"),
            date=metadata.get("date"),
            templates=templates
        )
    except yaml.YAMLError as e:
        log.warning(f"Error reading metadata: {e}")
        return None

def _unpack_template(template_name: str, directory: str = "."):
    # Unzips the template to given directory.
    template_path = f"{ACTION_TEMPLATES_DIR}/{template_name}.zip"

    if not os.path.isfile(template_path):
        raise RuntimeError(f"Template {template_name} does not exist")

    with zipfile.ZipFile(template_path, "r") as zip_ref:
        zip_ref.extractall(directory)

