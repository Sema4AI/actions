import logging
import typing
from pathlib import Path

from ._protocols import ArgumentsNamespace, ArgumentsNamespaceGetUserOAuthConfigPath

USER_CONFIG_FILE_NAME = "oauth_config.yaml"

log = logging.getLogger(__name__)


def get_sema4ai_oauth_config() -> int:
    from sema4ai.action_server import _oauth_config

    contents = _oauth_config.FILE_CONTENTS["sema4ai_config"]
    print(contents)

    return 0


def get_user_oauth_config_path(output_json: bool = False) -> int:
    from ._settings import get_default_settings_dir

    config_path: Path = get_default_settings_dir() / USER_CONFIG_FILE_NAME

    try:
        if not config_path.exists():
            with open(config_path, "w+") as f:
                from ._oauth_config import FILE_CONTENTS

                f.write(FILE_CONTENTS["default_user_config"])

        if output_json:
            import json

            print(json.dumps({"oauth_config_path": str(config_path)}))
        else:
            print(config_path)

        return 0

    except Exception as e:
        from sema4ai.action_server.vendored_deps.termcolors import bold_red

        log.critical(bold_red(f"\nError retrieving user OAuth config path: {e}"))

        return 1


def handle_get_sema4ai_oauth_config_command() -> int:
    return get_sema4ai_oauth_config()


def handle_get_user_oauth_config_path_command(base_args: ArgumentsNamespace) -> int:
    args: ArgumentsNamespaceGetUserOAuthConfigPath = typing.cast(
        ArgumentsNamespaceGetUserOAuthConfigPath, base_args
    )

    return get_user_oauth_config_path(output_json=args.json)
