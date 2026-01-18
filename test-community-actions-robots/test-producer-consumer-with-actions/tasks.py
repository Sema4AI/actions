from pathlib import Path
from robocorp import log, workitems
from robocorp.tasks import get_output_dir, task
import shutil
import os
from git import Repo
from git.exc import GitCommandError
import json
import time

TimeoutException = Exception  # type: ignore

# Import utility functions and fixtures from tools module
from scripts.tools import task_context, get_org_name, repos


@task
def producer():
    """Fetches repositories from GitHub org and creates work items."""
    # Process input work items to get organization name
    for item in workitems.inputs:
        try:
            payload = item.payload
            if not isinstance(payload, dict):
                item.fail(
                    "APPLICATION",
                    code="INVALID_PAYLOAD",
                    message="Payload must be a dictionary",
                )
                continue

            org_name = payload.get("org")
            if not org_name:
                org_name = get_org_name()

            if not org_name:
                item.fail(
                    "APPLICATION",
                    code="MISSING_ORG_NAME",
                    message="Organization name is required in work item payload 'org' field or ORG_NAME environment variable.",
                )
                continue

            log.info(f"Processing organization: {org_name}")

            # Get the DataFrame from repos() function with retry logic
            try:
                df = repos(org_name)
            except Exception as e:
                error_msg = f"Failed to fetch repositories for {org_name}: {str(e)}"
                log.exception(error_msg)
                item.fail("BUSINESS", code="FETCH_ERROR", message=error_msg)
                continue

            if df is not None and not df.empty:
                log.info(f"Processing {len(df)} repositories from DataFrame")
                rows = df.to_dict(orient="records")
                created_count = 0

                for row in rows:
                    try:
                        repo_payload = {
                            "org": org_name,
                            "Name": row.get("Name"),
                            "URL": row.get("URL"),
                            "Description": row.get("Description"),
                            "Created": row.get("Created"),
                            "Last Updated": row.get("Last Updated"),
                            "Language": row.get("Language"),
                            "Stars": row.get("Stars"),
                            "Is Fork": row.get("Is Fork"),
                        }

                        # Validate required fields
                        if not repo_payload.get("URL") or not repo_payload.get("Name"):
                            log.warn(
                                f"Skipping repository with missing URL or Name: {repo_payload}"
                            )
                            continue

                        # Create work item
                        workitems.outputs.create(repo_payload)
                        created_count += 1

                    except Exception as e:
                        log.critical(
                            f"Error creating work item for repository {row.get('Name', 'unknown')}: {str(e)}"
                        )
                        # Continue processing other repositories
                        continue

                log.info(
                    f"Created {created_count} work items out of {len(rows)} repositories"
                )

                # Mark the input item as done only after all work items are created
                item.done()
            else:
                log.warn("No data received from repos() function")
                item.fail(
                    "BUSINESS",
                    code="NO_DATA",
                    message="No repositories found for organization",
                )

        except Exception as e:
            error_msg = f"Unexpected error in producer task: {str(e)}"
            log.exception(error_msg)
            item.fail("APPLICATION", code="UNEXPECTED_ERROR", message=error_msg)


@task
def consumer():
    """Clones all the repositories from the input Work Items and zips them and saves them to the output directory."""
    output = get_output_dir() or Path("output")

    # Get the managed directory from the fixture via context
    repos_dir = task_context.get("repos_dir")
    if not repos_dir:
        raise RuntimeError("Consumer directory not set up by fixture.")

    # Get shard ID for unique naming
    shard_id = os.getenv("SHARD_ID", "0")
    filename = f"repos-shard-{shard_id}.zip"
    output_path = output / filename

    processed_repos = []
    git_repos = []  # Track successfully cloned repo paths

    # Define report path before use
    report_path = output / f"report-shard-{shard_id}.json"

    # Extract org name from first work item or environment variable
    org_name = get_org_name()

    for item in workitems.inputs:
        try:
            payload = item.payload
            if not isinstance(payload, dict):
                log.debug(f"Skipping item with non-dict payload: {payload}")
                item.fail(
                    "APPLICATION",
                    code="INVALID_PAYLOAD",
                    message="Payload is not a dict.",
                )
                continue

            # Extract org name if not already set
            if org_name is None:
                org_name = payload.get("org")

            url = payload.get("URL")
            repo_name = payload.get("Name")

            if not url:
                log.debug(f"Skipping item with missing URL: {payload}")
                item.fail(
                    "APPLICATION",
                    code="MISSING_URL",
                    message="URL is missing in payload.",
                )
                continue

            if not repo_name:
                # Fallback: extract repo name from URL
                repo_name = url.split("/")[-1].replace(".git", "")

            repo_path = repos_dir / repo_name
            log.info(f"[Shard {shard_id}] {org_name}/{repo_name} - cloning...")

            # Check if repo already exists (idempotency check)
            if repo_path.exists():
                log.info(
                    f"[Shard {shard_id}] {org_name}/{repo_name} - already exists, skipping"
                )
                processed_repos.append(
                    {"name": repo_name, "url": url, "status": "already_exists"}
                )
                workitems.outputs.create(
                    {
                        "name": repo_name,
                        "url": url,
                        "org": org_name,
                        "status": "already_exists",
                    }
                )
                item.done()
                continue

            try:
                # If a GitHub token is provided, and the clone URL is HTTPS, inject the token
                # into the URL so private repositories can be cloned:
                # https://github.com/owner/repo.git -> https://<token>@github.com/owner/repo.git
                token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
                clone_url = url
                if token and url.startswith("https://"):
                    # Insert token after scheme and before the host. Do not log token.
                    try:
                        scheme, rest = url.split("//", 1)
                        clone_url = f"{scheme}//{token}@{rest}"
                    except ValueError:
                        clone_url = url

                # Clone with GitPython, with timeout and better error handling
                repo = Repo.clone_from(
                    clone_url, repo_path, depth=1
                )  # Shallow clone for efficiency
                log.info(f"[Shard {shard_id}] {org_name}/{repo_name} - ✓")
                processed_repos.append(
                    {
                        "name": repo_name,
                        "url": url,
                        "status": "success",
                        "commit_hash": (
                            repo.head.commit.hexsha[:8]
                            if repo.head.commit
                            else "unknown"
                        ),
                    }
                )
                git_repos.append(repo_path)  # Add to cleanup list

                # Create output work item for success
                workitems.outputs.create(
                    {
                        "name": repo_name,
                        "url": url,
                        "org": org_name,
                        "status": "success",
                        "commit_hash": (
                            repo.head.commit.hexsha[:8]
                            if repo.head.commit
                            else "unknown"
                        ),
                    }
                )
                item.done()

            except GitCommandError as git_err:
                error_msg = f"Git error while cloning {repo_name} from org {org_name}: {str(git_err)}"
                log.critical(
                    f"[Shard {shard_id}] {org_name}/{repo_name} - ✗ {str(git_err)}"
                )

                # Clean up partial clone on failure
                if repo_path.exists():
                    try:
                        shutil.rmtree(repo_path)
                    except OSError:
                        pass

                if (
                    "could not resolve host" in str(git_err).lower()
                    or "network" in str(git_err).lower()
                ):
                    log.warn(
                        f"[Shard {shard_id}] {org_name}/{repo_name} - network error, releasing for retry"
                    )
                    processed_repos.append(
                        {
                            "name": repo_name,
                            "url": url,
                            "status": "released",
                            "error": error_msg,
                        }
                    )
                    # Create output work item for released
                    workitems.outputs.create(
                        {
                            "name": repo_name,
                            "url": url,
                            "org": org_name,
                            "status": "released",
                            "error": error_msg,
                        }
                    )
                    # Do not mark as done or failed, so it can be retried if supported
                else:
                    processed_repos.append(
                        {
                            "name": repo_name,
                            "url": url,
                            "status": "failed",
                            "error": error_msg,
                        }
                    )
                    # Create output work item for failure
                    workitems.outputs.create(
                        {
                            "name": repo_name,
                            "url": url,
                            "org": org_name,
                            "status": "failed",
                            "error": error_msg,
                        }
                    )
                    item.fail("BUSINESS", code="GIT_ERROR", message=error_msg)
                continue

        except Exception as e:
            error_msg = f"Unexpected error processing work item: {str(e)}"
            log.exception(error_msg)
            item.fail("APPLICATION", code="UNEXPECTED_ERROR", message=error_msg)
            continue

    # Create a summary report (idempotent - overwrites existing)
    report = {
        "shard_id": shard_id,
        "org_name": org_name,
        "total_processed": len(processed_repos),
        "successful_clones": len(
            [r for r in processed_repos if r["status"] == "success"]
        ),
        "failed_clones": len([r for r in processed_repos if r["status"] == "failed"]),
        "released_items": len(
            [r for r in processed_repos if r["status"] == "released"]
        ),
        "already_existing": len(
            [r for r in processed_repos if r["status"] == "already_exists"]
        ),
        "repositories": processed_repos,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
    }

    try:
        with open(report_path, "w") as f:
            json.dump(report, f, indent=4)
        log.info(f"[Shard {shard_id}] Consumer task finished. Report at: {report_path}")
    except Exception as e:
        log.warn(f"Warning: Could not write report to {report_path}: {e}")

    # Only create zip if we have successfully cloned repos
    if git_repos:
        try:
            # Remove existing zip file for idempotency
            if output_path.exists():
                output_path.unlink()

            # Zip the cloned repositories directory
            log.info(
                f"[Shard {shard_id}] Zipping {len(git_repos)} cloned repositories..."
            )
            shutil.make_archive(
                str(output_path.with_suffix("")), "zip", root_dir=repos_dir
            )
            log.info(f"[Shard {shard_id}] Zipped repositories to: {output_path}")
        except Exception as e:
            log.critical(f"Error creating zip archive: {e}")
    else:
        log.info(f"[Shard {shard_id}] No repositories to zip")

    # Cleanup is now handled by the manage_consumer_directory fixture.


@task
def reporter():
    """Generate comprehensive reports on work item processing status."""
    summary_stats = {
        "total_items_processed": 0,
        "successful_items": 0,
        "failed_items": 0,
        "released_items": 0,
        "organizations": set(),
        "repositories": [],
    }

    for item in workitems.inputs:
        try:
            payload = item.payload
            if not isinstance(payload, dict):
                log.warn(f"Skipping item with non-dict payload: {payload}")
                item.fail(
                    "APPLICATION",
                    code="INVALID_PAYLOAD",
                    message="Payload is not a dict.",
                )
                continue

            org_name = payload.get("org")
            if not org_name:
                org_name = get_org_name()

            if not org_name:
                log.critical(
                    "Organization name is required in work item payload 'org' field or ORG_NAME environment variable."
                )
                item.fail(
                    "APPLICATION",
                    code="MISSING_ORG_NAME",
                    message="Organization name is missing.",
                )
                continue

            log.info(f"Processing report for organization: {org_name}")

            # Collect statistics from work item
            status = payload.get("status", "unknown")
            repo_name = payload.get("name") or payload.get("Name", "unknown")

            summary_stats["total_items_processed"] += 1
            summary_stats["organizations"].add(org_name)

            # Count by status
            if status == "success":
                summary_stats["successful_items"] += 1
            elif status == "failed":
                summary_stats["failed_items"] += 1
            elif status == "released":
                summary_stats["released_items"] += 1

            # Add repository details
            summary_stats["repositories"].append(
                {
                    "name": repo_name,
                    "org": org_name,
                    "status": status,
                    "url": payload.get("url") or payload.get("URL"),
                    "error": payload.get("error"),
                }
            )

            item.done()

        except Exception as e:
            error_msg = f"Error processing report item: {str(e)}"
            log.critical(error_msg)
            item.fail("APPLICATION", code="UNEXPECTED_ERROR", message=error_msg)

    # Generate final summary
    summary_stats["organizations"] = list(summary_stats["organizations"])
    success_rate = (
        (
            summary_stats["successful_items"]
            / summary_stats["total_items_processed"]
            * 100
        )
        if summary_stats["total_items_processed"] > 0
        else 0
    )

    log.info("=" * 50)
    log.info("FINAL PROCESSING REPORT")
    log.info("=" * 50)
    log.info(f"Organizations processed: {len(summary_stats['organizations'])}")
    log.info(f"Total repositories: {summary_stats['total_items_processed']}")
    log.info(f"✅ Successful: {summary_stats['successful_items']}")
    log.info(f"❌ Failed: {summary_stats['failed_items']}")
    log.info(f"🔄 Released (for retry): {summary_stats['released_items']}")
    log.info(f"📊 Success rate: {success_rate:.1f}%")
    log.info("=" * 50)

    # Save detailed report
    output_dir = get_output_dir() or Path("output")
    report_file = (
        output_dir
        / f"final_report_{time.strftime('%Y%m%d-%H%M%S', time.gmtime())}.json"
    )

    try:
        with open(report_file, "w") as f:
            json.dump(
                {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                    "summary": summary_stats,
                    "success_rate_percent": success_rate,
                },
                f,
                indent=4,
            )
        log.info(f"📄 Detailed report saved to: {report_file}")
    except Exception as e:
        log.warn(f"Warning: Could not save detailed report: {e}")
