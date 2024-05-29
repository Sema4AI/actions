import tempfile
from logging import getLogger
from pathlib import Path

log = getLogger(__name__)


def __extract_package(tmpdirname: Path, package_path: Path) -> None:
    import zipfile

    log.debug(f"Extracting {package_path} to {tmpdirname}")

    with zipfile.ZipFile(package_path, "r") as zip_ref:
        zip_ref.extractall(tmpdirname)


def read_package_name(package_path: Path) -> str:
    """
    Reading package content and extracting the name.

    Arguments:
        Verified path to built action package (.zip) file

    Returns:
        Name of the package in the package.yaml
    """
    import yaml

    from sema4ai.action_server._errors_action_server import ActionServerValidationError

    with tempfile.TemporaryDirectory() as tmpdirname:
        __extract_package(Path(tmpdirname), package_path)

        package_yaml_path = Path(tmpdirname, "package.yaml")
        if not package_yaml_path.exists():
            raise ActionServerValidationError(
                f"Could not find package.yaml from {package_path}"
            )

        try:
            with open(package_yaml_path, "r", encoding="utf-8") as stream:
                package_yaml_contents = yaml.safe_load(stream)
        except Exception:
            raise ActionServerValidationError(
                f"Error loading file as yaml ({package_yaml_contents})."
            )
        if isinstance(package_yaml_contents, dict):
            name = package_yaml_contents.get("name")
            if name:
                return name

        raise ActionServerValidationError(
            f"Error finding package name from ({package_yaml_contents})."
        )
