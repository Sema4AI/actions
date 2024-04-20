import json
import os
from pathlib import Path

try:
    from sema4ai.actions import IAction, teardown
except ImportError:
    # old
    from robocorp.actions import IAction, teardown  # type:ignore


@teardown
def on_teardown_save_result(action: IAction):
    S4_ACTION_RESULT_LOCATION = os.environ.get("S4_ACTION_RESULT_LOCATION", "")

    if S4_ACTION_RESULT_LOCATION:
        result = action.result
        p = Path(S4_ACTION_RESULT_LOCATION)
        p.parent.mkdir(parents=True, exist_ok=True)
        if hasattr(result, "model_dump_json"):
            # Support for pydantic
            p.write_text(result.model_dump_json())
        else:
            p.write_text(json.dumps(result))
