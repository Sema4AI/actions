"""
Important: 

sema4ai.action_server.cli.main() 

is the only public API supported from the action-server.

Everything else is considered private and can be broken/changed without
being considered a backward-incompatible change!
"""
import logging
from typing import Optional

# Important: main() is the only public API supported from the action-server.
# Everything else is considered private and can be broken/changed without
# being considered a backward-incompatible change!
__all__ = ["main"]

log = logging.getLogger(__name__)


def main(args: Optional[list[str]] = None, *, exit=True) -> int:  # noqa
    import os
    import sys

    from ._cli_impl import _main_retcode

    if args is None:
        args = sys.argv[1:]

    if not args:
        # Note this is not to be relied by clients. Added for the build.
        if os.environ.get(
            "RC_ACTION_SERVER_FORCE_DOWNLOAD_RCC", ""
        ).strip().lower() in (
            "1",
            "true",
        ):
            log.info(
                "As RC_ACTION_SERVER_FORCE_DOWNLOAD_RCC is set and no arguments were "
                "passed, rcc will be downloaded."
            )

            from sema4ai.action_server._download_rcc import download_rcc

            download_rcc(force=True)

        if os.environ.get("RC_ACTION_SERVER_DO_SELFTEST", "").strip().lower() in (
            "1",
            "true",
        ):
            # Note this is not to be relied by clients. Added for the build.
            from . import _selftest

            log.info(
                "As RC_ACTION_SERVER_DO_SELFTEST is set and no arguments were passed, "
                "a selftest will be run."
            )

            sys.exit(_selftest.do_selftest())

    retcode = _main_retcode(args)
    if exit:
        sys.exit(retcode)
    return retcode


if __name__ == "__main__":
    main()
