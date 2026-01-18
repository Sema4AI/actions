from pathlib import Path
from robocorp.tasks import get_output_dir, setup, teardown, session_cache
import shutil
import os
import time
from scripts.fetch_repos import fetch_github_repos

# A shared context to pass data from fixtures to tasks
task_context = {}


@setup
def manage_consumer_directory(task):
    """Set up and tear down the temporary directory for the consumer task."""
    if task.name == "consumer":
        output = get_output_dir() or Path("output")
        shard_id = os.getenv("SHARD_ID", "0")
        repos_dir = output / f"repos-shard-{shard_id}"

        # Clean up before task execution for a fresh start
        if repos_dir.exists():
            shutil.rmtree(repos_dir)
        repos_dir.mkdir(parents=True, exist_ok=True)

        task_context["repos_dir"] = repos_dir
        
        try:
            yield  # Task executes here
        finally:
            # Clean up after task execution
            print(f"[Shard {shard_id}] Cleaning up cloned repositories directory...")
            if repos_dir.exists():
                try:
                    shutil.rmtree(repos_dir)
                    print(f"[Shard {shard_id}] Cleanup complete.")
                except OSError as e:
                    print(f"Warning: Error removing directory {repos_dir}: {e}")
            # Clear context
            task_context.pop("repos_dir", None)
    else:
        yield # For other tasks, do nothing


@setup
def measure_task_time(task):
    """Measure execution time for each task."""
    start_time = time.time()
    print(f"Starting task: {task.name}")
    yield  # Task executes here
    duration = time.time() - start_time
    print(f"Task '{task.name}' completed in {duration:.2f} seconds")


@teardown
def handle_task_errors(task):
    """Handle any task failures and log errors."""
    if task.failed:
        print(f"❌ Task '{task.name}' failed: {task.message}")
        # Additional error handling could be added here
    else:
        print(f"✅ Task '{task.name}' completed successfully")


@session_cache
def get_org_name():
    """Cache organization name for the session to avoid repeated lookups."""
    # Try environment variable first
    org_name = os.getenv("ORG_NAME")
    if org_name:
        return org_name
    
    # If not in env, will be provided by work items
    return None


def repos(org_name):
    """Fetch the list of repositories from GitHub and return a DataFrame."""
    if not org_name:
        raise ValueError("Organization name is required.")
    print(f"Fetching repositories for organization: {org_name}")
    return fetch_github_repos(org_name)