import logging
import typing

from sema4ai.action_server._protocols import ArgumentsNamespace, ArgumentsNamespaceEnv

if typing.TYPE_CHECKING:
    from sema4ai.action_server._rcc import Rcc

log = logging.getLogger(__name__)


def handle_env_command(env_args: ArgumentsNamespace, rcc: "Rcc"):
    import typing

    env_command = typing.cast(ArgumentsNamespaceEnv, env_args).env_command
    if not env_command:
        log.critical("Command for env operation not specified.")
        return 1

    if env_command == "clean-tools-caches":
        log.info("Clearing tools caches, please wait...")
        rcc.clean_tools_caches()
        return 0

    log.critical(f"Env command not recognized: {env_command}.")
    return 1
