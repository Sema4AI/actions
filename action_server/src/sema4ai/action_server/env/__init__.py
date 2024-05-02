import logging

from sema4ai.action_server._protocols import ArgumentsNamespace, ArgumentsNamespaceEnv

log = logging.getLogger(__name__)


def handle_env_command(env_args: ArgumentsNamespace):
    import typing

    env_command = typing.cast(ArgumentsNamespaceEnv, env_args).env_command
    if not env_command:
        log.critical("Command for env operation not specified.")
        return 1

    if env_command == "clean-tools-caches":
        log.info("Clearing tools caches, please wait...")
        from sema4ai.action_server._download_rcc import download_rcc
        from sema4ai.action_server._rcc import initialize_rcc

        robocorp_home = None

        with initialize_rcc(download_rcc(force=False), robocorp_home) as rcc:
            rcc.clean_tools_caches()

        return 0

    log.critical(f"Env command not recognized: {env_command}.")
    return 1
