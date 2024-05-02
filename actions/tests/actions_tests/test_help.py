import sys

import pytest


@pytest.mark.parametrize("args", [["-h"], ["run", "-h"], ["list", "-h"]])
def test_help(args, str_regression):
    v = sys.version_info[:2]
    if v < (3, 10):
        return
    if v > (3, 10):
        raise RuntimeError(
            f"This test must be migrated to {v} (always the major version supported should be tested)"
        )
    from devutils.fixtures import sema4ai_actions_run

    str_regression.check(sema4ai_actions_run(args, returncode=0).stdout.decode("utf-8"))
