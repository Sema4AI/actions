import json
import sys
from pathlib import Path

if __name__ == "__main__":
    args = sys.argv[1:]
    output_json = Path(args[0])
    base_artifacts_dir = args[1]
    run_artifacts_dir = args[2]
    run_id = args[3]

    output_json.write_text(
        json.dumps(
            dict(
                run_id=run_id,
                base_artifacts_dir=base_artifacts_dir,
                run_artifacts_dir=run_artifacts_dir,
            )
        )
    )
