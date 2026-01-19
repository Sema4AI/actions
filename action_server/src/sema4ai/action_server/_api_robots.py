import logging
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

import fastapi
import yaml
from fastapi import File, Form, UploadFile
from fastapi.routing import APIRouter
from pydantic import BaseModel

from sema4ai.action_server._database import datetime_to_str
from sema4ai.action_server._models import Run, RunStatus
from sema4ai.action_server._runs_state_cache import get_global_runs_state
from sema4ai.action_server._settings import get_settings
from sema4ai.action_server._rcc import get_rcc_robots

log = logging.getLogger(__name__)

# Directory where imported robots are stored
ROBOTS_DIR = Path.home() / ".robots"

robots_api_router = APIRouter(prefix="/api/robots")


# Catalog Response Models
class RobotTaskInfoAPI(BaseModel):
    name: str
    docs: str = ""


class RobotPackageDetailAPI(BaseModel):
    name: str
    description: Optional[str] = None
    path: str
    environment_hash: str = ""
    tasks: List[RobotTaskInfoAPI] = []


class RobotCatalogResponseAPI(BaseModel):
    robots: List[RobotPackageDetailAPI]


def _get_robot_yaml_file(package_dir: Path) -> Optional[Path]:
    """
    Get the robot configuration file from a package directory.

    Supports both:
    - robot.yaml (older RCC format)
    - package.yaml with tasks (newer format)

    Returns the path to the config file, or None if not found.
    """
    # Check for robot.yaml first (older format)
    robot_yaml = package_dir / "robot.yaml"
    if robot_yaml.exists():
        return robot_yaml

    # Check for package.yaml with tasks (newer format)
    package_yaml = package_dir / "package.yaml"
    if package_yaml.exists():
        try:
            with open(package_yaml, "r") as f:
                pkg_data = yaml.safe_load(f)
            if pkg_data and pkg_data.get("tasks"):
                return package_yaml
        except Exception:
            pass

    return None


def _discover_robots_in_dir(base_dir: Path) -> List[RobotPackageDetailAPI]:
    """
    Discover robot packages in a directory.

    Looks for either:
    - robot.yaml (older RCC format with conda.yaml for deps)
    - package.yaml with tasks defined (newer format)
    """
    robots = []

    if not base_dir.exists():
        return robots

    # Track discovered directories to avoid duplicates
    discovered_dirs = set()

    # Look for robot.yaml files (older format)
    for robot_yaml in base_dir.rglob("robot.yaml"):
        package_dir = robot_yaml.parent
        if package_dir in discovered_dirs:
            continue
        discovered_dirs.add(package_dir)

        try:
            with open(robot_yaml, "r") as f:
                robot_data = yaml.safe_load(f)

            if not robot_data:
                continue

            # Parse tasks from robot.yaml format
            tasks_data = robot_data.get("tasks", {})
            if not tasks_data:
                continue

            tasks = []
            for task_name, task_info in tasks_data.items():
                docs = ""
                if isinstance(task_info, dict):
                    docs = task_info.get("documentation", task_info.get("docs", task_info.get("description", "")))
                tasks.append(RobotTaskInfoAPI(name=task_name, docs=docs))

            robot = RobotPackageDetailAPI(
                name=robot_data.get("name", package_dir.name),
                description=robot_data.get("description"),
                path=str(package_dir.absolute()),
                environment_hash="",
                tasks=tasks,
            )
            robots.append(robot)

        except Exception as e:
            log.warning(f"Error parsing {robot_yaml}: {e}")
            continue

    # Look for package.yaml files with tasks (newer format)
    for package_yaml in base_dir.rglob("package.yaml"):
        package_dir = package_yaml.parent
        if package_dir in discovered_dirs:
            continue
        discovered_dirs.add(package_dir)

        try:
            with open(package_yaml, "r") as f:
                pkg_data = yaml.safe_load(f)

            if not pkg_data:
                continue

            # Check if this is a robot (has tasks defined)
            tasks_data = pkg_data.get("tasks", {})
            if not tasks_data:
                continue

            # Parse tasks
            tasks = []
            for task_name, task_info in tasks_data.items():
                docs = ""
                if isinstance(task_info, dict):
                    docs = task_info.get("docs", task_info.get("description", ""))
                tasks.append(RobotTaskInfoAPI(name=task_name, docs=docs))

            robot = RobotPackageDetailAPI(
                name=pkg_data.get("name", package_dir.name),
                description=pkg_data.get("description"),
                path=str(package_dir.absolute()),
                environment_hash="",  # Will be populated when env is created
                tasks=tasks,
            )
            robots.append(robot)

        except Exception as e:
            log.warning(f"Error parsing {package_yaml}: {e}")
            continue

    return robots


@robots_api_router.get("/catalog", response_model=RobotCatalogResponseAPI)
async def get_robot_catalog():
    """
    Get catalog of available robot packages.

    Scans configured directories for robot packages (package.yaml with tasks).
    """
    settings = get_settings()
    robots = []

    # Scan the datadir for robots
    if settings.datadir:
        robots.extend(_discover_robots_in_dir(Path(settings.datadir)))

    # Also check for a dedicated robots directory
    robots_dir = Path.home() / ".robots"
    if robots_dir.exists():
        robots.extend(_discover_robots_in_dir(robots_dir))

    # Deduplicate by path
    seen_paths = set()
    unique_robots = []
    for robot in robots:
        if robot.path not in seen_paths:
            seen_paths.add(robot.path)
            unique_robots.append(robot)

    return RobotCatalogResponseAPI(robots=unique_robots)


# Import Response Model
class RobotImportResponseAPI(BaseModel):
    success: bool
    message: str
    robot_path: Optional[str] = None
    robot_name: Optional[str] = None


def _validate_robot_package(package_dir: Path) -> tuple[bool, str, Optional[str]]:
    """
    Validate that a directory contains a valid robot package.

    Supports both:
    - robot.yaml (older RCC format with conda.yaml for deps)
    - package.yaml with tasks (newer format)

    Returns: (is_valid, message, robot_name)
    """
    robot_yaml = package_dir / "robot.yaml"
    package_yaml = package_dir / "package.yaml"

    # Try robot.yaml first (older format)
    if robot_yaml.exists():
        try:
            with open(robot_yaml, "r") as f:
                robot_data = yaml.safe_load(f)

            if not robot_data:
                return False, "robot.yaml is empty", None

            # Check for tasks
            tasks = robot_data.get("tasks", {})
            if not tasks:
                return False, "No tasks defined in robot.yaml", None

            robot_name = robot_data.get("name", package_dir.name)
            return True, f"Valid robot package (robot.yaml) with {len(tasks)} task(s)", robot_name

        except yaml.YAMLError as e:
            return False, f"Invalid YAML in robot.yaml: {e}", None
        except Exception as e:
            return False, f"Error reading robot.yaml: {e}", None

    # Try package.yaml (newer format)
    if package_yaml.exists():
        try:
            with open(package_yaml, "r") as f:
                pkg_data = yaml.safe_load(f)

            if not pkg_data:
                return False, "package.yaml is empty", None

            # Check for tasks (robot packages have tasks)
            tasks = pkg_data.get("tasks", {})
            if not tasks:
                return False, "No tasks defined in package.yaml - this may be an action package, not a robot", None

            robot_name = pkg_data.get("name", package_dir.name)
            return True, f"Valid robot package (package.yaml) with {len(tasks)} task(s)", robot_name

        except yaml.YAMLError as e:
            return False, f"Invalid YAML in package.yaml: {e}", None
        except Exception as e:
            return False, f"Error reading package.yaml: {e}", None

    return False, "No robot.yaml or package.yaml found in the package", None


def _extract_zip_to_robots(zip_path: Path, robot_name: Optional[str] = None) -> tuple[bool, str, Optional[Path]]:
    """
    Extract a zip file to the robots directory.

    Returns: (success, message, extracted_path)
    """
    ROBOTS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Get the list of files in the zip
            namelist = zip_ref.namelist()

            if not namelist:
                return False, "Zip file is empty", None

            # Check if there's a single root directory
            root_dirs = set()
            for name in namelist:
                parts = name.split('/')
                if parts[0]:
                    root_dirs.add(parts[0])

            # Create a temp directory for extraction
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                zip_ref.extractall(temp_path)

                # Determine the package directory
                if len(root_dirs) == 1:
                    # Single root directory in zip
                    package_dir = temp_path / list(root_dirs)[0]
                else:
                    # Multiple files/dirs at root - treat temp_dir as package
                    package_dir = temp_path

                # Validate the package
                is_valid, message, extracted_name = _validate_robot_package(package_dir)
                if not is_valid:
                    return False, message, None

                # Determine final name
                final_name = robot_name or extracted_name or package_dir.name

                # Sanitize name for filesystem
                final_name = "".join(c for c in final_name if c.isalnum() or c in "._- ").strip()
                if not final_name:
                    final_name = "imported_robot"

                # Check if target already exists
                target_dir = ROBOTS_DIR / final_name
                if target_dir.exists():
                    # Add suffix to make unique
                    import uuid
                    suffix = str(uuid.uuid4())[:8]
                    final_name = f"{final_name}_{suffix}"
                    target_dir = ROBOTS_DIR / final_name

                # Move the package to robots directory
                shutil.copytree(package_dir, target_dir)

                return True, f"Successfully imported robot '{final_name}'", target_dir

    except zipfile.BadZipFile:
        return False, "Invalid zip file", None
    except Exception as e:
        log.exception("Error extracting robot package")
        return False, f"Error extracting package: {e}", None


async def _download_from_url(url: str) -> tuple[bool, str, Optional[Path]]:
    """
    Download a robot package from a URL.

    Supports:
    - Direct .zip file URLs
    - GitHub repository URLs (converts to zip download)

    Returns: (success, message, downloaded_path)
    """
    import httpx

    parsed = urlparse(url)

    # Handle GitHub URLs
    if "github.com" in parsed.netloc:
        # Convert GitHub repo URL to zip download URL
        # https://github.com/owner/repo -> https://github.com/owner/repo/archive/refs/heads/main.zip
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) >= 2:
            owner, repo = path_parts[0], path_parts[1]
            # Remove .git suffix if present
            if repo.endswith('.git'):
                repo = repo[:-4]
            url = f"https://github.com/{owner}/{repo}/archive/refs/heads/main.zip"

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
            response = await client.get(url)
            response.raise_for_status()

            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_file:
                tmp_file.write(response.content)
                tmp_path = Path(tmp_file.name)

            return True, "Downloaded successfully", tmp_path

    except httpx.HTTPStatusError as e:
        return False, f"HTTP error: {e.response.status_code}", None
    except httpx.RequestError as e:
        return False, f"Request failed: {e}", None
    except Exception as e:
        log.exception("Error downloading robot package")
        return False, f"Download error: {e}", None


@robots_api_router.post("/import", response_model=RobotImportResponseAPI)
async def import_robot(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
):
    """
    Import a robot package from a file upload or URL.

    Either 'file' (a .zip upload) or 'url' (a URL to download from) must be provided.

    The robot package must contain a package.yaml with tasks defined.
    """
    if not file and not url:
        return RobotImportResponseAPI(
            success=False,
            message="Either a file upload or URL must be provided",
        )

    temp_zip_path: Optional[Path] = None

    try:
        if file:
            # Handle file upload
            if not file.filename or not file.filename.endswith('.zip'):
                return RobotImportResponseAPI(
                    success=False,
                    message="File must be a .zip archive",
                )

            # Save uploaded file to temp location
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_file:
                content = await file.read()
                tmp_file.write(content)
                temp_zip_path = Path(tmp_file.name)

        elif url:
            # Handle URL download
            success, message, downloaded_path = await _download_from_url(url)
            if not success:
                return RobotImportResponseAPI(
                    success=False,
                    message=message,
                )
            temp_zip_path = downloaded_path

        # Extract and validate the package
        success, message, robot_path = _extract_zip_to_robots(temp_zip_path)

        if success and robot_path:
            return RobotImportResponseAPI(
                success=True,
                message=message,
                robot_path=str(robot_path),
                robot_name=robot_path.name,
            )
        else:
            return RobotImportResponseAPI(
                success=False,
                message=message,
            )

    finally:
        # Clean up temp file
        if temp_zip_path and temp_zip_path.exists():
            try:
                temp_zip_path.unlink()
            except Exception:
                pass


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
        # Use robots RCC instance (uses ROBOTS_HOME / ~/.robots) to avoid holotree lock contention with actions
        rcc = get_rcc_robots()

        # Set up paths
        package_path = Path(request.robot_package_path)
        if not package_path.exists():
            raise RuntimeError(f"Robot package not found: {package_path}")

        # Detect which config format is used: robot.yaml (older) or package.yaml (newer)
        robot_yaml = package_path / "robot.yaml"
        package_yaml = package_path / "package.yaml"

        # Determine the config file for RCC task run and the env file for environment creation
        if robot_yaml.exists():
            # Older robot.yaml format - uses separate conda.yaml for dependencies
            robot_config_file = robot_yaml

            # Find conda.yaml for environment creation
            # It's typically in the same directory, referenced in environmentConfigs
            conda_yaml = package_path / "conda.yaml"
            if not conda_yaml.exists():
                # Try to find it from environmentConfigs in robot.yaml
                try:
                    with open(robot_yaml, "r") as f:
                        robot_data = yaml.safe_load(f)
                    env_configs = robot_data.get("environmentConfigs", [])
                    for env_config in env_configs:
                        if env_config.endswith("conda.yaml"):
                            potential_conda = package_path / env_config
                            if potential_conda.exists():
                                conda_yaml = potential_conda
                                break
                except Exception:
                    pass

            if not conda_yaml.exists():
                raise RuntimeError(f"conda.yaml not found in {package_path} (required for robot.yaml format)")

            env_config_file = conda_yaml
            log.info(f"Using robot.yaml format with conda.yaml for environment: {robot_config_file}")
        elif package_yaml.exists():
            # Newer package.yaml format - dependencies are inline
            robot_config_file = package_yaml
            env_config_file = package_yaml
            log.info(f"Using package.yaml format: {robot_config_file}")
        else:
            raise RuntimeError(f"No robot.yaml or package.yaml found in {package_path}")

        try:
            # Update run status to running
            run.status = RunStatus.RUNNING
            with db.transaction():
                db.update(run, "status")
            get_global_runs_state().on_run_changed(run, {"status": RunStatus.RUNNING})

            # Get environment variables for the robot task
            # Use env_config_file (conda.yaml or package.yaml) for environment creation
            env_result = rcc.create_env_and_get_vars(
                settings.datadir,
                env_config_file,
                package_yaml_hash=rcc.get_package_yaml_hash(env_config_file, devenv=False),
                devenv=False,
            )
            if not env_result.success:
                raise RuntimeError(f"Failed to create robot environment: {env_result.message}")

            # Update env hash
            run.robot_env_hash = env_result.result.env.get("CONDA_ENVIRONMENT_HASH", "")
            with db.transaction():
                db.update(run, "robot_env_hash")

            # Determine secrets file if requested
            # Note: secrets support requires secrets_dir to be configured
            secrets_file = None
            if request.use_secrets:
                # Look for secrets in datadir/secrets/ directory
                secrets_dir = settings.datadir / "secrets" if settings.datadir else None
                if secrets_dir and secrets_dir.exists():
                    robot_secrets = secrets_dir / f"{package_path.name}_secrets.json"
                    if robot_secrets.exists():
                        secrets_file = robot_secrets
                    else:
                        default_secrets = secrets_dir / "secrets.json"
                        if default_secrets.exists():
                            secrets_file = default_secrets

            # Set up RCC args
            # Use robot_config_file (robot.yaml or package.yaml) for the --robot argument
            # Note: RCC v18.x doesn't have --artifacts flag; artifacts go to the directory
            # specified in robot.yaml's artifactsDir (defaults to 'output')
            rcc_args = [
                "task",
                "run",
                "--robot", str(robot_config_file),
                "--task", request.task_name,
            ]

            # Only add --space if we have an env hash (for pre-built environments)
            if run.robot_env_hash:
                rcc_args.extend(["--space", run.robot_env_hash])

            if secrets_file and secrets_file.exists():
                rcc_args.extend(["--secrets", str(secrets_file)])

            # Output file for capturing robot logs
            output_file = artifacts_dir / "__action_server_output.txt"

            # Run the robot task
            result = rcc._run_rcc(
                rcc_args,
                timeout=3600,  # 1 hour timeout
                cwd=str(package_path),
                show_interactive_output=True,
            )

            # Save output to file for logs page
            try:
                output_content = result.result or ""
                if result.message and not result.success:
                    output_content += f"\n\n--- Error ---\n{result.message}"
                output_file.write_text(output_content, encoding="utf-8")
            except Exception as write_err:
                log.warning(f"Failed to write robot output file: {write_err}")

            # Copy robot output files to artifacts directory
            # RCC puts output in the robot's 'output' directory by default
            # This includes .robolog files (from robocorp-log) and RF output files
            robot_output_dir = package_path / "output"
            if robot_output_dir.exists():
                # Copy .robolog files for log.html generation
                for robolog_file in robot_output_dir.glob("*.robolog"):
                    try:
                        shutil.copy2(robolog_file, artifacts_dir / robolog_file.name)
                        log.debug(f"Copied {robolog_file.name} to artifacts")
                    except Exception as copy_err:
                        log.warning(f"Failed to copy {robolog_file.name}: {copy_err}")

                # Also copy Robot Framework output files if present
                for output_name in ["log.html", "output.xml", "report.html"]:
                    src_file = robot_output_dir / output_name
                    if src_file.exists():
                        try:
                            shutil.copy2(src_file, artifacts_dir / output_name)
                            log.debug(f"Copied {output_name} to artifacts")
                        except Exception as copy_err:
                            log.warning(f"Failed to copy {output_name}: {copy_err}")

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