import logging
from dataclasses import dataclass
from typing import List

from fastapi.routing import APIRouter

from sema4ai.action_server._models import Action, ActionPackage

action_package_api_router = APIRouter(prefix="/api/actionPackages")
log = logging.getLogger(__name__)


@dataclass
class ActionPackageApi:
    id: str  # primary key (uuid)
    name: str  # The name for the action package
    actions: List[Action]
    version: str


@action_package_api_router.get("", response_model=List[ActionPackageApi])
def list_action_packages():
    from sema4ai.action_server._models import get_db
    from sema4ai.action_server._settings import get_settings
    from sema4ai.action_server._actions_run_helpers import get_action_package_cwd
    import yaml

    db = get_db()
    settings = get_settings()
    with db.connect():
        # We're running in the threadpool used by fast api, so, we need
        # to make a new connection (maybe it'd make sense to create a
        # connection pool instead of always creating a new connection...).
        action_packages = db.all(ActionPackage)

        id_to_action_package = {}
        for action_package in action_packages:
            version = ""
            try:
                directory = get_action_package_cwd(settings, action_package)
                package_yaml_path = directory / "package.yaml"
                if package_yaml_path.exists():
                    with package_yaml_path.open("r", encoding="utf-8") as stream:
                        contents = yaml.safe_load(stream)
                    if isinstance(contents, dict):
                        v = contents.get("version")
                        if v is not None:
                            version = str(v)
            except Exception:
                # Keep version empty if it can't be determined, but log for troubleshooting.
                log.debug(
                    "Unable to determine version for action package %s",
                    action_package.name,
                    exc_info=True,
                )

            id_to_action_package[action_package.id] = ActionPackageApi(
                action_package.id, action_package.name, [], version
            )

        for action in db.all(Action):
            id_to_action_package[action.action_package_id].actions.append(action)

    return list(id_to_action_package.values())
