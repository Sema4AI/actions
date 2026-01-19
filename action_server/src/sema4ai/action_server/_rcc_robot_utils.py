import json
import logging
import os
import subprocess
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class RobotPackageListItem(BaseModel):
    name: str
    path: Path
    version: Optional[str] = None
    description: Optional[str] = None
    is_zip: bool = False


class RobotTask(BaseModel):
    name: str
    docs: Optional[str] = Field(None, alias="documentation")  # RCC uses "documentation"


class RobotDetails(BaseModel):
    name: str
    path: Path
    yaml_contents: Optional[Dict] = None
    holotree_variables: Optional[Dict] = None
    tasks: List[RobotTask] = []


def _run_rcc_command(
    args: List[str], cwd: Optional[Path] = None
) -> Tuple[str, str, int]:
    """Helper to run an RCC command and return stdout, stderr, and exit code."""
    try:
        process = subprocess.run(
            ["rcc"] + args,
            capture_output=True,
            text=True,
            cwd=cwd,
            check=False,  # We handle non-zero exit codes manually
            timeout=300,  # 5 minutes timeout
        )
        return process.stdout, process.stderr, process.returncode
    except FileNotFoundError:
        logger.error("RCC command not found. Ensure RCC is installed and in PATH.")
        return "", "RCC command not found.", -1
    except subprocess.TimeoutExpired:
        logger.error(f"RCC command {' '.join(args)} timed out.")
        return "", "RCC command timed out.", -1
    except Exception as e:
        logger.error(f"Error running RCC command {' '.join(args)}: {e}")
        return "", str(e), -1


def list_robot_packages(robots_dir: Path) -> List[RobotPackageListItem]:
    """
    Scans robots_dir for valid robot packages (either robot.yaml present or a zip file).
    For each package, extracts basic metadata (name, path, maybe version from robot.yaml if present).
    """
    robot_packages: List[RobotPackageListItem] = []
    if not robots_dir.is_dir():
        logger.warning(f"Robots directory not found: {robots_dir}")
        return robot_packages

    for item in robots_dir.iterdir():
        package_name = item.stem
        package_path = item.resolve()
        version: Optional[str] = None
        description: Optional[str] = None
        is_zip = False

        if item.is_file() and item.suffix.lower() == ".zip":
            is_zip = True
            try:
                with zipfile.ZipFile(item, "r") as zf:
                    if "robot.yaml" in zf.namelist():
                        with zf.open("robot.yaml") as robot_yaml_file:
                            robot_yaml_content = yaml.safe_load(robot_yaml_file)
                            if isinstance(robot_yaml_content, dict):
                                package_name = robot_yaml_content.get(
                                    "name", package_name
                                )
                                version = robot_yaml_content.get("version")
                                description = robot_yaml_content.get("description")
                    else:
                        # If no robot.yaml, still list it as a potential (but perhaps incomplete) robot zip
                        logger.debug(
                            f"Zip file {item} does not contain a robot.yaml, using filename as name."
                        )
            except zipfile.BadZipFile:
                logger.warning(f"Could not read zip file: {item}")
                continue
            except Exception as e:
                logger.warning(f"Error processing robot zip {item}: {e}")
                continue

        elif item.is_dir():
            robot_yaml_path = item / "robot.yaml"
            if robot_yaml_path.exists():
                try:
                    with open(robot_yaml_path, "r", encoding="utf-8") as f:
                        robot_yaml_content = yaml.safe_load(f)
                        if isinstance(robot_yaml_content, dict):
                            package_name = robot_yaml_content.get("name", package_name)
                            version = robot_yaml_content.get("version")
                            description = robot_yaml_content.get("description")
                except Exception as e:
                    logger.warning(f"Error reading robot.yaml for {item}: {e}")
                    # Still add it, but with less info
            else:
                # If a directory doesn't have robot.yaml, we might not consider it a primary robot package
                # Or we could list it and let get_robot_details fail if it's not valid
                logger.debug(
                    f"Directory {item} does not contain a robot.yaml. Skipping for now."
                )
                continue  # Or decide to include it with minimal info

        else:
            continue  # Skip other file types

        robot_packages.append(
            RobotPackageListItem(
                name=package_name,
                path=package_path,
                version=version,
                description=description,
                is_zip=is_zip,
            )
        )
    return robot_packages


def get_robot_details(robot_package_path: Path) -> Optional[RobotDetails]:
    """
    Uses `rcc holotree variables --json ...` and `rcc task list --json ...` for the given robot_package_path.
    Returns a dictionary containing package name, path, environment details, and a list of tasks.
    """
    if not robot_package_path.exists():
        logger.error(f"Robot package path does not exist: {robot_package_path}")
        return None

    robot_name = robot_package_path.stem
    yaml_contents: Optional[Dict] = None

    # Determine if it's a directory or a zip file for RCC commands
    # RCC generally expects a path to a directory containing robot.yaml or the zip file itself.
    rcc_target_path_str = str(robot_package_path)

    # Try to read robot.yaml for name and other details first
    if robot_package_path.is_dir():
        robot_yaml_file = robot_package_path / "robot.yaml"
        if robot_yaml_file.exists():
            try:
                with open(robot_yaml_file, "r", encoding="utf-8") as f:
                    yaml_contents = yaml.safe_load(f)
                    if isinstance(yaml_contents, dict):
                        robot_name = yaml_contents.get("name", robot_name)
            except Exception as e:
                logger.warning(
                    f"Could not parse robot.yaml in {robot_package_path}: {e}"
                )
    elif robot_package_path.is_file() and robot_package_path.suffix.lower() == ".zip":
        try:
            with zipfile.ZipFile(robot_package_path, "r") as zf:
                if "robot.yaml" in zf.namelist():
                    with zf.open("robot.yaml") as ry_file:
                        yaml_contents = yaml.safe_load(ry_file)
                        if isinstance(yaml_contents, dict):
                            robot_name = yaml_contents.get("name", robot_name)
        except Exception as e:
            logger.warning(
                f"Could not read robot.yaml from zip {robot_package_path}: {e}"
            )

    # Get holotree variables
    # For zip files, RCC might need to extract it first or operate on it directly.
    # `rcc holotree variables` usually takes `--robot path/to/robot.yaml` or `--zip path/to/robot.zip`
    # Let's assume rcc handles zip paths correctly for these commands.
    # If `robot_package_path` is a directory, `rcc ... --robot path/to/dir` should work.
    # If `robot_package_path` is a zip, `rcc ... --robot path/to/robot.zip` should work.

    args_vars = ["holotree", "variables", "--json", "--robot", rcc_target_path_str]
    stdout_vars, stderr_vars, retcode_vars = _run_rcc_command(args_vars)

    holotree_vars_data: Optional[Dict] = None
    if retcode_vars == 0 and stdout_vars:
        try:
            holotree_vars_data = json.loads(stdout_vars)
        except json.JSONDecodeError:
            logger.error(
                f"Failed to parse JSON from rcc holotree variables for {robot_package_path}. Output: {stdout_vars}"
            )
            # Optionally return or raise here depending on strictness
    else:
        logger.error(
            f"RCC holotree variables failed for {robot_package_path} (code: {retcode_vars}): {stderr_vars}"
        )
        # If holotree fails, we might not be able to proceed meaningfully.

    # Get task list
    args_tasks = ["task", "list", "--json", "--robot", rcc_target_path_str]
    stdout_tasks, stderr_tasks, retcode_tasks = _run_rcc_command(args_tasks)

    tasks_data: List[RobotTask] = []
    if retcode_tasks == 0 and stdout_tasks:
        try:
            parsed_tasks = json.loads(stdout_tasks)
            if isinstance(
                parsed_tasks, list
            ):  # RCC task list --json returns a list of task objects
                tasks_data = [RobotTask(**task_info) for task_info in parsed_tasks]
            else:
                logger.error(
                    f"RCC task list for {robot_package_path} did not return a list. Output: {stdout_tasks}"
                )

        except json.JSONDecodeError:
            logger.error(
                f"Failed to parse JSON from rcc task list for {robot_package_path}. Output: {stdout_tasks}"
            )
        except Exception as e:  # Catch Pydantic validation errors too
            logger.error(
                f"Error processing task list for {robot_package_path}: {e}. Output: {stdout_tasks}"
            )
    else:
        logger.error(
            f"RCC task list failed for {robot_package_path} (code: {retcode_tasks}): {stderr_tasks}"
        )
        # If task list fails, we might still return what we have, or None.
        # For now, let's return with an empty task list if this specific command fails.

    return RobotDetails(
        name=robot_name,
        path=robot_package_path,
        yaml_contents=yaml_contents,
        holotree_variables=holotree_vars_data,
        tasks=tasks_data,
    )


def run_robot_task(
    robot_package_path: Path,
    task_name: str,
    inputs: Optional[Dict] = None,
    run_id: Optional[str] = None,  # For potential future use with RCC logs
    secrets_file: Optional[Path] = None,  # For passing secrets if needed
) -> Tuple[str, str, int]:
    """
    Executes `rcc task run --robot <robot_package_path> --task <task_name>`
    (potentially with --json inputs if applicable).
    Captures and returns stdout, stderr, and the exit code of the subprocess.
    Handles potential errors during subprocess execution.
    """
    if not robot_package_path.exists():
        msg = f"Robot package path does not exist: {robot_package_path}"
        logger.error(msg)
        return "", msg, -1

    # RCC task run expects the path to the robot.yaml or the zip file.
    # Using the direct path to the package (dir or zip) should work with `--robot`
    rcc_target_path_str = str(robot_package_path)

    args = ["task", "run", "--robot", rcc_target_path_str, "--task", task_name]

    # Handling inputs: RCC can take inputs via environment variables.
    # A common way is to set them prefixed, e.g., RC_INPUT_my_var=value
    # Or, if the robot uses a library like Robocorp.WorkItems, inputs can be passed
    # via a work item JSON. RCC doesn't have a direct `--json-inputs` flag for `task run`.
    # For now, we'll assume inputs are handled by the robot itself via env vars or work items
    # that might be configured through `holotree variables` or `robot.yaml` `env` section.
    # If direct input passing is needed, it would typically involve setting environment variables
    # for the subprocess.

    _env_vars = os.environ.copy()  # Reserved for future use in subprocess calls
    if inputs:
        # This is a simplistic way; robots might expect specific env var formats
        # or a work-items.json file. For now, just logging.
        logger.info(
            f"Inputs provided for task {task_name}: {inputs}. These are not directly passed via CLI args by this function yet."
        )
        # Example of setting env vars if needed:
        # for key, value in inputs.items():
        #     env_vars[f"RC_INPUT_{key.upper()}"] = str(value)

    # TODO: Explore how to pass `inputs` to `rcc task run`.
    # This might involve creating a temporary input work-item JSON and passing its path,
    # or setting environment variables if the robot is designed to pick them up.
    # For now, `inputs` are not directly used in the command.

    if run_id:
        # RCC can associate logs with a run ID if the environment is set up for it
        # (e.g. when running in Control Room). For local runs, this might be less relevant
        # unless specific RCC features are used.
        # env_vars["RC_ACTION_SERVER_RUN_ID"] = run_id # Example
        pass

    if secrets_file and secrets_file.exists():
        args.extend(["--secrets", str(secrets_file)])

    logger.info(f"Running RCC command: rcc {' '.join(args)}")

    # `_run_rcc_command` uses `cwd=None` by default, which means it runs from the action server's CWD.
    # This should be fine as `--robot` takes an absolute or relative path to the robot.
    stdout, stderr, exit_code = _run_rcc_command(
        args
    )  # env=env_vars if passing custom env

    if exit_code != 0:
        logger.error(
            f"RCC task run failed for robot {robot_package_path}, task {task_name} (code: {exit_code})."
            f"\\nSTDOUT:\\n{stdout}\\nSTDERR:\\n{stderr}"
        )
    else:
        logger.info(
            f"RCC task run succeeded for robot {robot_package_path}, task {task_name}."
            f"\\nSTDOUT:\\n{stdout}"
        )
        if stderr:
            logger.info(f"STDERR:\\n{stderr}")

    return stdout, stderr, exit_code


if __name__ == "__main__":
    # Example Usage (for testing this module directly)
    # Create dummy robot directories/zips for testing
    # Ensure RCC is installed and accessible in your PATH.

    logging.basicConfig(level=logging.INFO)
    current_dir = Path(__file__).parent
    test_robots_dir = current_dir / "test_robots_temp"
    test_robots_dir.mkdir(exist_ok=True)

    # Create a dummy robot.yaml for a directory-based robot
    dummy_robot_dir = test_robots_dir / "MyFirstRobot"
    dummy_robot_dir.mkdir(exist_ok=True)
    robot_yaml_content_dict = {
        "name": "My First Robot",
        "description": "A simple robot for testing.",
        "version": "0.1.0",
        "tasks": {
            "Echo Message": {
                "command": ["python", "-m", "robot_code", "echo"],
                "documentation": "Echoes a message provided as an environment variable 'MESSAGE'.",
            },
            "List Files": {
                "command": ["python", "-m", "robot_code", "ls"],
                "documentation": "Lists files in the current directory.",
            },
        },
        "condaConfigFile": "conda.yaml",  # RCC needs a valid config
    }
    with open(dummy_robot_dir / "robot.yaml", "w") as f:
        yaml.dump(robot_yaml_content_dict, f)

    # Dummy conda.yaml
    with open(dummy_robot_dir / "conda.yaml", "w") as f:
        f.write("channels:\\n  - conda-forge\\ndependencies:\\n  - python=3.9\\n")

    # Dummy robot_code.py
    robot_code_py_content = """
import os, sys, argparse

def echo_message():
    message = os.environ.get("MESSAGE", "No message provided!")
    print(f"Robot says: {message}")

def list_files_in_cwd():
    print("Files in CWD:")
    for item in os.listdir("."):
        print(item)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("task_name", help="Name of the task to run: echo or ls")
    args = parser.parse_args()

    if args.task_name == "echo":
        echo_message()
    elif args.task_name == "ls":
        list_files_in_cwd()
    else:
        print(f"Unknown task: {args.task_name}", file=sys.stderr)
        sys.exit(1)
"""
    (dummy_robot_dir / "robot_code.py").write_text(robot_code_py_content)

    # Create a dummy zip robot
    dummy_zip_path = test_robots_dir / "MyZippedRobot.zip"
    with zipfile.ZipFile(dummy_zip_path, "w") as zf:
        zf.writestr(
            "robot.yaml",
            yaml.dump(
                {
                    "name": "My Zipped Robot",
                    "version": "1.1",
                    "description": "A robot from a zip.",
                    "tasks": {
                        "Greet": {"command": ["echo", "Hello from Zipped Robot"]}
                    },
                    "condaConfigFile": "conda.yaml",
                }
            ),
        )
        zf.writestr(
            "conda.yaml",
            "channels:\\n  - conda-forge\\ndependencies:\\n  - python=3.9\\n",
        )

    print(f"--- Listing robots in {test_robots_dir} ---")
    robots = list_robot_packages(test_robots_dir)
    for robot in robots:
        print(robot.model_dump_json(indent=2))

    if robots:
        print(f"\\n--- Getting details for {robots[0].name} ({robots[0].path}) ---")
        details = get_robot_details(robots[0].path)
        if details:
            print(details.model_dump_json(indent=2, exclude_none=True))

            if details.tasks:
                task_to_run = details.tasks[0].name
                print(f"\\n--- Running task '{task_to_run}' for {details.name} ---")
                # Set environment variable for the echo task
                os.environ["MESSAGE"] = "Hello from RCC Robot Utils Test!"
                stdout, stderr, retcode = run_robot_task(details.path, task_to_run)
                print(f"Exit Code: {retcode}")
                print(f"STDOUT:\\n{stdout}")
                print(f"STDERR:\\n{stderr}")
                del os.environ["MESSAGE"]  # Clean up env var

        # Test zip robot details
        zipped_robot_item = next((r for r in robots if r.is_zip), None)
        if zipped_robot_item:
            print(
                f"\\n--- Getting details for ZIPPED robot {zipped_robot_item.name} ({zipped_robot_item.path}) ---"
            )
            zip_details = get_robot_details(zipped_robot_item.path)
            if zip_details:
                print(zip_details.model_dump_json(indent=2, exclude_none=True))
                if zip_details.tasks:
                    zip_task_to_run = zip_details.tasks[0].name
                    print(
                        f"\\n--- Running task '{zip_task_to_run}' for {zip_details.name} ---"
                    )
                    stdout_zip, stderr_zip, retcode_zip = run_robot_task(
                        zip_details.path, zip_task_to_run
                    )
                    print(f"Exit Code: {retcode_zip}")
                    print(f"STDOUT:\\n{stdout_zip}")
                    print(f"STDERR:\\n{stderr_zip}")

    # Cleanup (optional)
    # import shutil
    # shutil.rmtree(test_robots_dir)
    # print(f"\\nCleaned up {test_robots_dir}")
