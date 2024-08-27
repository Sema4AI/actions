import logging
import typing
from pathlib import Path

from ._protocols import ArgumentsNamespace, ArgumentsNamespaceOAuth2, ArgumentsNamespaceOAuth2UserConfigPath

USER_CONFIG_FILE_NAME = "oauth2_config.yaml"

log = logging.getLogger(__name__)


def get_sema4ai_oauth2_config() -> int:
    from ._oauth2_config import FILE_CONTENTS

    contents = FILE_CONTENTS["sema4ai_config"]
    print(contents)

    return 0


def get_user_oauth2_config_path(output_json: bool = False) -> int:
    from ._settings import get_default_settings_dir

    config_path: Path = get_default_settings_dir() / USER_CONFIG_FILE_NAME

    try:
        if not config_path.exists():
            with open(config_path, "w+") as f:
                from ._oauth2_config import FILE_CONTENTS

                f.write(FILE_CONTENTS["default_user_config"])

        if output_json:
            import json

            print(json.dumps({"path": str(config_path)}))
        else:
            print(config_path)

        return 0

    except Exception as e:
        from sema4ai.action_server.vendored_deps.termcolors import bold_red

        log.critical(bold_red(f"\nError retrieving user OAuth config path: {e}"))

        return 1


def handle_get_sema4ai_oauth_config_command() -> int:
    return get_sema4ai_oauth2_config()


def handle_oauth2_command(base_args: ArgumentsNamespace) -> int:
    oauth2_args: ArgumentsNamespaceOAuth2 = typing.cast(
        ArgumentsNamespaceOAuth2, base_args
    )
    
    oauth2_command = oauth2_args.oauth2_command
    if not oauth2_command:
        log.critical("Command for oauth2 operation not specified.")
        return 1
    
    if oauth2_command == "sema4ai-config":
        return get_sema4ai_oauth2_config()
    
    if oauth2_command == "user-config-path":
        user_config_path_args: ArgumentsNamespaceOAuth2UserConfigPath = typing.cast(
            ArgumentsNamespaceOAuth2UserConfigPath, base_args
        )
        
        return get_user_oauth2_config_path(user_config_path_args.json)
    
    return 1