import json
import os
import sys
from pathlib import Path

if __name__ == "__main__":
    args = sys.argv[1:]
    output_json = Path(args[0])
    base_artifacts_dir = args[1]
    run_artifacts_dir = args[2]
    run_id = args[3]
    agent_id = args[4]

    thread_id = os.environ.get("SEMA4AI_ACTION_SERVER_POST_RUN_THREAD_ID")
    action_name = os.environ.get("SEMA4AI_ACTION_SERVER_POST_RUN_ACTION_NAME")

    output_json.write_text(
        json.dumps(
            dict(
                run_id=run_id,
                base_artifacts_dir=base_artifacts_dir,
                run_artifacts_dir=run_artifacts_dir,
                agent_id=agent_id,
                thread_id=thread_id,
                action_name=action_name,
            )
        )
    )
