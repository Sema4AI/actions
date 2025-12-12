import logging
from typing import Dict, Optional

import fastapi
from fastapi.routing import APIRouter
from pydantic import BaseModel

from sema4ai.action_server._database import datetime_to_str
from sema4ai.action_server._models import Run, RunStatus
from sema4ai.action_server._runs_state_cache import get_global_runs_state
from sema4ai.action_server._settings import get_settings
from sema4ai.action_server._rcc import get_rcc

log = logging.getLogger(__name__)

robots_api_router = APIRouter(prefix="/api/robots")


class RobotRunRequestAPI(BaseModel):
    robot_package_path: str  # Absolute path to the robot package
    task_name: str  # Name of the task to run
    inputs: Optional[Dict[str, str]] = None  # Optional task inputs
    use_secrets: bool = False  # Whether to pass secrets file to RCC


class RobotRunResponseAPI(BaseModel):
    run_id: str  # The assigned run ID 
    status: str  # Current run status
    message: Optional[str] = None  # Optional status message


@robots_api_router.post("/run", response_model=RobotRunResponseAPI)
async def run_robot_task(
    request: RobotRunRequestAPI,
    background_tasks: fastapi.BackgroundTasks,
):
    """
    Execute a robot task and track its execution.
    
    The task is executed asynchronously and the run status can be monitored
    via the /api/runs/{run_id} endpoint.
    """
    import uuid
    import datetime
    import json
    from pathlib import Path
    from sema4ai.action_server._models import RUN_ID_COUNTER, Run, RunStatus, Counter, get_db

    # Get settings for paths
    settings = get_settings()
    db = get_db()

    run_id = f"run-{uuid.uuid4()}"
    relative_artifacts_path = f"runs/{run_id}"
    artifacts_dir = settings.artifacts_dir / relative_artifacts_path

    # Ensure artifacts directory exists
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # Create initial run record
    run_kwargs = dict(
        id=run_id,
        status=RunStatus.NOT_RUN,
        action_id="",  # No action ID for robot runs
        start_time=datetime_to_str(datetime.datetime.now(datetime.timezone.utc)),
        run_time=None,
        inputs=json.dumps(request.inputs or {}),
        result=None,
        error_message=None,
        relative_artifacts_dir=relative_artifacts_path,
        request_id="",  # No request ID for robot runs yet
        run_type="robot",
        robot_package_path=request.robot_package_path,
        robot_task_name=request.task_name,
        robot_env_hash="",  # Will be populated when environment is created
    )

    # Insert the run record with an atomic numbered ID
    with db.transaction():
        with db.cursor() as cursor:
            db.execute_update_returning(
                cursor,
                "UPDATE counter SET value=value+1 WHERE id=? RETURNING value",
                [RUN_ID_COUNTER],
            )
            counter_record = cursor.fetchall()
            if not counter_record:
                raise RuntimeError(
                    f"Error. No counter found for run_id. Counters in db: {db.all(Counter)}"
                )
            run_kwargs["numbered_id"] = counter_record[0][0]
            run = Run(**run_kwargs)
            db.insert(run)

    # Notify run state listeners
    get_global_runs_state().on_run_inserted(run)

    # Schedule background task to execute the robot
    async def _execute_robot():
        rcc = get_rcc()

        # Set up paths
        package_path = Path(request.robot_package_path)
        if not package_path.exists():
            raise RuntimeError(f"Robot package not found: {package_path}")

        # Get environment hash from package.yaml
        package_yaml = package_path / "package.yaml" 
        if not package_yaml.exists():
            raise RuntimeError(f"package.yaml not found in {package_path}")
        
        try:
            # Update run status to running
            run.status = RunStatus.RUNNING
            with db.transaction():
                db.update(run, "status")
            get_global_runs_state().on_run_changed(run, {"status": RunStatus.RUNNING})

            # Get environment variables for the robot task
            env_result = rcc.create_env_and_get_vars(
                settings.datadir,
                package_yaml,
                package_yaml_hash=rcc.get_package_yaml_hash(package_yaml, devenv=False),
                devenv=False,
            )
            if not env_result.success:
                raise RuntimeError(f"Failed to create robot environment: {env_result.message}")

            # Update env hash
            run.robot_env_hash = env_result.result.env.get("CONDA_ENVIRONMENT_HASH", "")
            with db.transaction():
                db.update(run, "robot_env_hash")

            # Determine secrets file if requested
            secrets_file = None
            if request.use_secrets:
                secrets_file = settings.secrets_dir_path / f"{package_path.name}_secrets.json"
                if not secrets_file.exists():
                    # Fall back to default secrets
                    secrets_file = settings.secrets_dir_path / "secrets.json"

            # Set up RCC args
            rcc_args = [
                "task", 
                "run",
                "--space", run.robot_env_hash,
                "--robot", str(package_yaml),
                "--task", request.task_name,
                "--artifacts", str(artifacts_dir),
            ]

            if secrets_file and secrets_file.exists():
                rcc_args.extend(["--secrets", str(secrets_file)])

            # Run the robot task
            result = rcc._run_rcc(
                rcc_args,
                timeout=3600,  # 1 hour timeout
                cwd=str(package_path),
                show_interactive_output=True,
            )

            if result.success:
                run.status = RunStatus.PASSED
                run.result = json.dumps({
                    "output": result.result,
                    "artifacts_dir": str(artifacts_dir),
                })
            else:
                run.status = RunStatus.FAILED
                run.error_message = result.message

            with db.transaction():
                db.update(run, "status", "result", "error_message")

            get_global_runs_state().on_run_changed(
                run,
                {
                    "status": run.status,
                    "result": run.result,
                    "error_message": run.error_message,  
                }
            )

        except Exception as e:
            log.exception("Error executing robot task")
            run.status = RunStatus.FAILED
            run.error_message = str(e)
            with db.transaction():
                db.update(run, "status", "error_message")
            get_global_runs_state().on_run_changed(
                run, {"status": RunStatus.FAILED, "error_message": str(e)}
            )

    background_tasks.add_task(_execute_robot)

    return RobotRunResponseAPI(
        run_id=run_id,
        status="REQUESTED",
        message="Robot task execution requested",
    )