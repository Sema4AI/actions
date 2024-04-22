import sys
import typing
from typing import Optional

if typing.TYPE_CHECKING:
    # Don't add to public API here.
    from sema4ai.actions._customization._plugin_manager import (
        PluginManager as _PluginManager,
    )


def _inject_truststore():
    # Use certificates from the native storage.
    try:
        import truststore  # type: ignore
    except ModuleNotFoundError:
        pass
    else:
        truststore.inject_into_ssl()


_inject_truststore()

if sys.platform == "win32":
    # Apply workaround where `asyncio` would halt forever when windows UIAutomation.dll
    # is used with comtypes.
    # see: https://github.com/python/cpython/issues/111604
    _COINIT_MULTITHREADED = 0x0
    sys.coinit_flags = _COINIT_MULTITHREADED  # type:ignore


def main(
    args=None, exit: bool = True, plugin_manager: Optional["_PluginManager"] = None
) -> int:
    """
    Entry point for running actions from sema4ai-actions.

    Args:
        args: The command line arguments.

        exit: Determines if the process should exit right after executing the command.

        plugin_manager:
            Provides a way to customize internal functionality (should not
            be used by external clients in general).

    Returns:
        The exit code for the process.
    """
    if args is None:
        args = sys.argv[1:]

    if plugin_manager is None:
        # If not provided, let's still add the 'request' as a managed parameter
        # (without any actual data).
        from sema4ai.actions._customization._extension_points import EPManagedParameters
        from sema4ai.actions._customization._plugin_manager import PluginManager
        from sema4ai.actions._managed_parameters import ManagedParameters
        from sema4ai.actions._request import Request

        plugin_manager = PluginManager()
        plugin_manager.set_instance(
            EPManagedParameters,
            ManagedParameters({"request": Request.model_validate({})}),
        )

    from sema4ai.actions._args_dispatcher import _ActionsArgDispatcher

    if args is None:
        args = sys.argv[1:]

    dispatcher = _ActionsArgDispatcher()

    returncode = dispatcher.process_args(args, pm=plugin_manager)
    if exit:
        sys.exit(returncode)
    return returncode
