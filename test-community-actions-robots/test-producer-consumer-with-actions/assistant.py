from pathlib import Path
from robocorp import workitems
from robocorp.tasks import get_output_dir, task
import shutil
import os
from git import Repo
from git.exc import GitCommandError
import json
import time
import subprocess
from typing import Dict, List, Optional, Tuple
import sys
from types import SimpleNamespace

try:
    # Assistant is optional at runtime; import guarded to avoid breaking existing tasks if dependency missing.
    from RPA.Assistant import Assistant  # Provided by rpaframework-assistant
    from RPA.Assistant.flet_client import TimeoutException
except ImportError:  # pragma: no cover - defensive
    Assistant = None  # type: ignore
    TimeoutException = Exception  # type: ignore

# Import utility functions and fixtures from tools module
from scripts.tools import (
    task_context,
    manage_consumer_directory,
    measure_task_time,
    handle_task_errors,
    get_org_name,
    repos,
)

HEADLESS_FLAGS = {"1", "true", "yes", "on"}


def is_headless_environment() -> bool:
    """Detect whether the assistant should skip launching a UI."""

    forced = os.environ.get("ASSISTANT_HEADLESS") or os.environ.get(
        "RC_ASSISTANT_HEADLESS"
    )
    if forced and forced.strip().lower() in HEADLESS_FLAGS:
        return True

    # CI environments often set CI=1
    if os.environ.get("CI", "").strip().lower() in HEADLESS_FLAGS:
        return True

    # If no display is available on Unix-like systems, assume headless
    if os.name != "nt" and not os.environ.get("DISPLAY"):
        return True

    return False


@task
def assistant_org():
    """Interactive pipeline launcher using RPA.Assistant.

    Presents a single dialog that collects configuration, runs the pipeline,
    and streams progress updates without closing the window.
    """
    if Assistant is None:
        print(
            "Assistant library not available (rpaframework-assistant missing). Aborting."
        )
        return

    assistant = Assistant()
    stage_order = ["Producer", "Consumer", "Reporter", "Dashboard"]
    stage_dependencies = {
        "Producer": [],
        "Consumer": ["Producer"],
        "Reporter": ["Consumer"],
        "Dashboard": ["Reporter"],
    }
    last_form_data = {"org": "", "max_workers": "1"}

    def render_progress(
        completed: int,
        stage_status: Dict[str, object],
        stage_messages: Dict[str, str],
        org_name: str,
        max_workers_display: str,
        running_stage: Optional[str] = None,
        final: bool = False,
    ) -> None:
        assistant.clear_dialog()
        assistant.add_heading("Producer-Consumer-Pipeline", size="large")
        assistant.add_text(f"Organization: {org_name}")
        assistant.add_text(f"Max Workers: {max_workers_display}")

        progress_value = 0.0
        if stage_order:
            progress_value = min(max(completed / len(stage_order), 0.0), 1.0)

        assistant.add_loading_bar(
            "progress",
            value=progress_value,
            width=420,
            bar_height=18,
            tooltip=f"{int(progress_value * 100)}% complete",
        )

        if running_stage:
            assistant.add_text(f"⏳ Running {running_stage}…", size="medium")

        assistant.add_text("")
        for stage in stage_order:
            status = stage_status.get(stage)
            message = stage_messages.get(stage, "")

            if status is None:
                assistant.add_text(f"⏳ {stage}: Pending")
            elif status == "skipped":
                assistant.add_text(f"⏭️ {stage}: {message or 'Skipped'}")
            elif status is True:
                assistant.add_text(f"✅ {stage}: {message or 'Success'}")
            else:
                assistant.add_text(f"❌ {stage}: {message or 'Failed'}")

        if final:
            assistant.add_text("")
            assistant.add_button("Run Again", lambda: reset_form())
            # Use a plain close button to avoid triggering validation on now-missing form fields
            assistant.add_button("Close", lambda: assistant.close_dialog())

        assistant.refresh_dialog()

    def run_rcc_task(command: List[str]) -> Tuple[bool, str]:
        """Run an rcc task with a configurable timeout.

        Environment variables to tune behavior:
        - ASSISTANT_STAGE_TIMEOUT: seconds (float/int) per stage. Default 900 (15m).
        - ASSISTANT_PRODUCER_TIMEOUT / ASSISTANT_CONSUMER_TIMEOUT / ASSISTANT_REPORTER_TIMEOUT / ASSISTANT_DASHBOARD_TIMEOUT
          override per-stage when set (seconds).
        - ASSISTANT_KILL_GRACE_PERIOD: seconds to wait after sending SIGTERM before SIGKILL. Default 10.
        """
        # Decide timeout based on command (-t <TaskName> expected)
        stage_name = None
        if "-t" in command:
            try:
                stage_name = command[command.index("-t") + 1]
            except Exception:  # pragma: no cover - defensive
                stage_name = None

        base_timeout = float(os.getenv("ASSISTANT_STAGE_TIMEOUT", "900"))  # 15 minutes default
        per_stage_env = None
        if stage_name:
            per_stage_env = os.getenv(f"ASSISTANT_{stage_name.upper()}_TIMEOUT")
        if per_stage_env:
            try:
                timeout_seconds = float(per_stage_env)
            except ValueError:
                timeout_seconds = base_timeout
        else:
            timeout_seconds = base_timeout

        grace_period = float(os.getenv("ASSISTANT_KILL_GRACE_PERIOD", "10"))

        print(f"[assistant] Running: {' '.join(command)} (timeout={timeout_seconds}s stage={stage_name})")
        start_time = time.time()
        try:
            # Use Popen for streaming output; inherit stdout/stderr.
            proc = subprocess.Popen(command, stdout=None, stderr=None, text=True)
            while True:
                ret = proc.poll()
                if ret is not None:
                    success = ret == 0
                    elapsed = time.time() - start_time
                    return success, ("Success" if success else f"Exit code {ret} after {elapsed:.1f}s")
                elapsed = time.time() - start_time
                if elapsed > timeout_seconds:
                    print(f"[assistant] Stage {stage_name or command} exceeded timeout ({timeout_seconds}s). Sending SIGTERM...")
                    try:
                        proc.terminate()
                    except Exception:
                        pass
                    # Wait grace period
                    try:
                        proc.wait(timeout=grace_period)
                    except subprocess.TimeoutExpired:
                        print(f"[assistant] Process did not exit in grace period ({grace_period}s). Sending SIGKILL...")
                        try:
                            proc.kill()
                        except Exception:
                            pass
                    final_ret = proc.poll()
                    return False, f"Timeout after {elapsed:.1f}s (limit {timeout_seconds}s)"
                time.sleep(0.5)
        except FileNotFoundError:
            return (
                False,
                "rcc command not found. Install RCC CLI and ensure it is on PATH.",
            )
        except Exception as exc:  # pragma: no cover - defensive
            return False, str(exc)

    def run_pipeline(form_result) -> None:
        nonlocal last_form_data

        org_name = getattr(form_result, "org", "").strip()
        max_workers_raw = getattr(form_result, "max_workers", "").strip() or "1"
        last_form_data = {"org": org_name, "max_workers": max_workers_raw}

        if not org_name:
            reset_form("Organization name is required.")
            return

        try:
            max_workers_int = max(1, int(max_workers_raw))
        except ValueError:
            reset_form("Max Workers must be a positive integer.")
            return

        max_workers_display = str(max_workers_int)
        print(
            f"Starting pipeline for organization: {org_name} (max workers: {max_workers_display})"
        )

        # Prepare environment and input artifacts
        os.environ["ORG_NAME"] = org_name
        os.environ["SHARD_ID"] = "0"
        os.environ["MAX_WORKERS"] = max_workers_display

        work_items_dir = Path("devdata/work-items-in/input-for-producer")
        work_items_dir.mkdir(parents=True, exist_ok=True)
        work_items_path = work_items_dir / "work-items.json"
        with open(work_items_path, "w") as handle:
            json.dump([{"payload": {"org": org_name}}], handle, indent=4)

        producer_env = {
            "RC_WORKITEM_ADAPTER": "FileAdapter",
            "RC_WORKITEM_INPUT_PATH": str(work_items_path),
            "RC_WORKITEM_OUTPUT_PATH": "output/producer-to-consumer/work-items.json",
        }
        consumer_env = {
            "RC_WORKITEM_ADAPTER": "FileAdapter",
            "RC_WORKITEM_INPUT_PATH": "output/producer-to-consumer/work-items.json",
            "RC_WORKITEM_OUTPUT_PATH": "output/consumer-to-reporter/work-items.json",
        }
        reporter_env = {
            "RC_WORKITEM_ADAPTER": "FileAdapter",
            "RC_WORKITEM_INPUT_PATH": "output/consumer-to-reporter/work-items.json",
            "RC_WORKITEM_OUTPUT_PATH": "output/reporter-final/work-items.json",
        }

        stage_status: Dict[str, object] = {stage: None for stage in stage_order}
        stage_messages: Dict[str, str] = {}

        Path("devdata").mkdir(exist_ok=True)
        Path("output/reporter-final").mkdir(parents=True, exist_ok=True)

        def write_env(path: Path, data: dict) -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w") as env_handle:
                json.dump(data, env_handle, indent=4)

        render_progress(0, stage_status, stage_messages, org_name, max_workers_display)

        # Keep merged consumer items for summary display (list of dict payloads)
        consumer_merged_payloads: List[dict] = []

        for index, stage in enumerate(stage_order):
            dependencies = stage_dependencies.get(stage, [])
            if any(stage_status.get(dep) is not True for dep in dependencies):
                missing = ", ".join(
                    dep for dep in dependencies if stage_status.get(dep) is not True
                )
                stage_status[stage] = "skipped"
                stage_messages[stage] = f"Skipped because {missing} did not succeed."
                render_progress(
                    index + 1,
                    stage_status,
                    stage_messages,
                    org_name,
                    max_workers_display,
                )
                continue

            render_progress(
                index,
                stage_status,
                stage_messages,
                org_name,
                max_workers_display,
                running_stage=stage,
            )
            print(f"Running {stage} ({index + 1}/{len(stage_order)})…")

            if stage == "Producer":
                env_path = Path("devdata/env-for-producer.json")
                write_env(env_path, producer_env)
                success, message = run_rcc_task(
                    ["rcc", "run", "-t", "Producer", "-e", str(env_path)]
                )
            elif stage == "Consumer":
                # 1. Generate shards based on MAX_WORKERS
                try:
                    shard_gen_cmd = [
                        sys.executable,
                        "scripts/generate_shards_and_matrix.py",
                        max_workers_display,
                    ]
                    print(
                        f"[assistant] Generating shards with command: {' '.join(shard_gen_cmd)}"
                    )
                    shard_proc = subprocess.run(
                        shard_gen_cmd, capture_output=True, text=True
                    )
                    if shard_proc.returncode != 0:
                        print(shard_proc.stdout)
                        print(shard_proc.stderr)
                        raise RuntimeError(
                            f"Shard generation failed (exit {shard_proc.returncode})"
                        )
                    else:
                        print(shard_proc.stdout)
                except Exception as exc:
                    stage_status[stage] = False
                    stage_messages[stage] = f"Shard generation error: {exc}"
                    render_progress(
                        index + 1,
                        stage_status,
                        stage_messages,
                        org_name,
                        max_workers_display,
                    )
                    continue

                # 2. Discover shards
                shards_dir = Path("output/shards")
                shard_files = sorted(shards_dir.glob("work-items-shard-*.json"))
                if not shard_files:
                    print("[assistant] No shard files found; nothing to consume.")
                    success = True
                    message = "No shards"
                else:
                    all_outputs: List[str] = []
                    shard_success = True
                    for shard_idx, shard_file in enumerate(shard_files):
                        shard_env = consumer_env.copy()
                        shard_env["RC_WORKITEM_INPUT_PATH"] = str(shard_file)
                        shard_env["RC_WORKITEM_OUTPUT_PATH"] = (
                            f"output/consumer-to-reporter/work-items-shard-{shard_idx}.json"
                        )
                        os.environ["SHARD_ID"] = str(shard_idx)
                        env_path = Path(
                            f"devdata/env-for-consumer-shard-{shard_idx}.json"
                        )
                        write_env(env_path, shard_env)
                        print(
                            f"[assistant] Running Consumer shard {shard_idx} with {shard_file.name}"
                        )
                        shard_ok, shard_msg = run_rcc_task(
                            ["rcc", "run", "-t", "Consumer", "-e", str(env_path)]
                        )
                        print(
                            f"[assistant] Consumer shard {shard_idx} result: {shard_ok} {shard_msg}"
                        )
                        shard_success = shard_success and shard_ok
                        all_outputs.append(
                            f"output/consumer-to-reporter/work-items-shard-{shard_idx}.json"
                        )
                        # Early abort if one shard fails? Keep going to gather more results.

                    # 3. Merge shard outputs into consolidated file for Reporter stage
                    consolidated_path = Path(
                        "output/consumer-to-reporter/work-items.json"
                    )
                    merged_items: List[dict] = []
                    for output_fp in all_outputs:
                        p = Path(output_fp)
                        if p.exists():
                            try:
                                with open(p, "r") as f:
                                    data = json.load(f)
                                    if isinstance(data, list):
                                        # Items could be list of objects with 'payload' or raw dicts
                                        for entry in data:
                                            if isinstance(entry, dict):
                                                payload = entry.get("payload") if "payload" in entry else entry
                                                if isinstance(payload, dict):
                                                    merged_items.append(payload)
                                    else:
                                        print(
                                            f"[assistant] Skipping non-list output file {p}"
                                        )
                            except Exception as merge_exc:
                                print(
                                    f"[assistant] Error reading shard output {p}: {merge_exc}"
                                )
                        else:
                            print(
                                f"[assistant] Expected shard output file missing: {output_fp}"
                            )
                    try:
                        consolidated_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(consolidated_path, "w") as f:
                            json.dump(merged_items, f, indent=2)
                        print(
                            f"[assistant] Merged {len(merged_items)} items into {consolidated_path}"
                        )
                        consumer_merged_payloads = merged_items[:]  # copy for later summary
                    except Exception as write_exc:
                        shard_success = False
                        print(
                            f"[assistant] Failed writing consolidated consumer output: {write_exc}"
                        )

                    success = shard_success
                    message = (
                        f"Shards: {len(shard_files)} merged items: {len(merged_items)}"
                    )
            elif stage == "Reporter":
                env_path = Path("devdata/env-for-reporter.json")
                write_env(env_path, reporter_env)
                success, message = run_rcc_task(
                    ["rcc", "run", "-t", "Reporter", "-e", str(env_path)]
                )
            else:  # Dashboard
                success, message = run_rcc_task(
                    ["rcc", "run", "-t", "GenerateConsolidatedDashboard"]
                )

            stage_status[stage] = success
            stage_messages[stage] = message

            render_progress(
                index + 1, stage_status, stage_messages, org_name, max_workers_display
            )

    # After running all stages, attempt to build an enriched report view
        def build_detailed_report() -> None:
            nonlocal consumer_merged_payloads
            """Augment final dialog with detailed reporter/consumer outputs.

            Priority of data sources:
              1. Consumer merged payloads captured in-memory.
              2. Reporter final report JSON (final_report_*.json).
              3. Fallback: read consolidated consumer-to-reporter work-items.json.
            """
            repos_payloads: List[dict] = []
            if consumer_merged_payloads:
                repos_payloads = consumer_merged_payloads
            else:
                # Try reporter summary file
                reporter_dir = Path("output")
                final_reports = sorted(
                    reporter_dir.glob("final_report_*.json"), reverse=True
                )
                if final_reports:
                    try:
                        with open(final_reports[0], "r") as f:
                            data = json.load(f)
                            summary = data.get("summary", {})
                            repo_entries = summary.get("repositories", [])
                            for entry in repo_entries:
                                if isinstance(entry, dict):
                                    repos_payloads.append(entry)
                    except Exception as exc:  # pragma: no cover - defensive
                        print(
                            f"[assistant] Could not parse reporter final report: {exc}"
                        )
                # If still empty, read consolidated consumer output raw
                if not repos_payloads:
                    cons_file = Path(
                        "output/consumer-to-reporter/work-items.json"
                    )
                    if cons_file.exists():
                        try:
                            with open(cons_file, "r") as f:
                                data = json.load(f)
                                if isinstance(data, list):
                                    for entry in data:
                                        if isinstance(entry, dict):
                                            payload = (
                                                entry.get("payload")
                                                if "payload" in entry
                                                else entry
                                            )
                                            if isinstance(payload, dict):
                                                repos_payloads.append(payload)
                        except Exception as exc:
                            print(
                                f"[assistant] Failed reading consumer consolidated file: {exc}"
                            )

            if not repos_payloads:
                assistant.add_heading("Run Summary", size="medium")
                assistant.add_text("No repository payloads available to summarize.")
                return

            # Compute metrics
            total = len(repos_payloads)
            successes = sum(1 for r in repos_payloads if r.get("status") == "success")
            failures = sum(1 for r in repos_payloads if r.get("status") == "failed")
            released = sum(1 for r in repos_payloads if r.get("status") == "released")
            already = sum(
                1 for r in repos_payloads if r.get("status") == "already_exists"
            )
            other = total - successes - failures - released - already
            success_rate = (successes / total * 100) if total else 0.0

            assistant.add_heading("Run Summary", size="medium")
            assistant.add_text(
                "  |  ".join(
                    [
                        f"Total: {total}",
                        f"Success: {successes}",
                        f"Failed: {failures}",
                        f"Released: {released}",
                        f"Already: {already}",
                        f"Other: {other}",
                        f"Success Rate: {success_rate:.1f}%",
                    ]
                )
            )

            # Visual distribution bar
            if total:
                def blocks(count: int) -> int:
                    return int(round((count / total) * 40))  # 40 char bar

                bar = (
                    "▇" * blocks(successes)
                    + "▅" * blocks(failures)
                    + "▂" * blocks(released)
                    + "■" * blocks(already)
                    + "·" * max(
                        0,
                        40
                        - blocks(successes)
                        - blocks(failures)
                        - blocks(released)
                        - blocks(already),
                    )
                )
                legend = "▇ success  ▅ failed  ▂ released  ■ existing  · other"
                assistant.add_text(f"Distribution: {bar}", size="small")
                assistant.add_text(legend, size="small")

            # Prepare table rows (limit)
            limit = int(os.getenv("ASSISTANT_REPORT_ROWS", "50"))
            display_rows = []
            for r in repos_payloads[:limit]:
                display_rows.append(
                    [
                        r.get("org", org_name),
                        r.get("name") or r.get("Name"),
                        r.get("status"),
                        (r.get("url") or r.get("URL") or "")[:70],
                        (r.get("error") or "")[:50],
                    ]
                )

            if display_rows:
                headers = ["Org", "Repo", "Status", "URL", "Error"]
                try:
                    assistant.add_table(headers, display_rows, id="repos_table")
                except Exception:
                    assistant.add_text("Repository details:")
                    for row in display_rows:
                        assistant.add_text(" | ".join(str(c) for c in row), size="small")

            if len(repos_payloads) > limit:
                assistant.add_text(
                    f"(Showing first {limit} of {len(repos_payloads)} repositories)",
                    size="small",
                )

        render_progress(
            len(stage_order),
            stage_status,
            stage_messages,
            org_name,
            max_workers_display,
            final=True,
        )
        try:
            # Append additional details beneath the existing final view
            build_detailed_report()
            assistant.refresh_dialog()
        except Exception as exc:  # pragma: no cover - defensive
            print(f"[assistant] Failed building detailed report UI: {exc}")

        if stage_status.get("Dashboard") is True:
            print("Dashboard generated at output/consolidated_dashboard_jinja2.html")
        if stage_status.get("Reporter") is True:
            print("Reporter outputs stored under output/ directory.")

        print("Pipeline execution finished. You can close the assistant or run again.")

    def reset_form(
        error_message: Optional[str] = None, *, refresh: bool = True
    ) -> None:
        assistant.clear_dialog()
        assistant.add_heading("Fetch Repos Bot Pipeline", size="large")
        assistant.add_text(
            "Configure and run the complete repository fetching pipeline."
        )

        if error_message:
            assistant.add_text(f"⚠️ {error_message}", size="small")

        assistant.add_text_input(
            "org",
            label="GitHub Organization",
            placeholder="e.g. robocorp, microsoft, etc.",
            required=True,
            default=last_form_data.get("org", ""),
        )
        assistant.add_text_input(
            "max_workers",
            label="Max Workers (for sharding)",
            placeholder="4",
            default=last_form_data.get("max_workers", "1"),
        )

        assistant.add_next_ui_button("Run Pipeline", run_pipeline)
        assistant.add_submit_buttons(buttons="Close", default="Close")

        if refresh:
            assistant.refresh_dialog()

    reset_form(refresh=False)
    assistant.run_dialog(title="Fetch Repos Bot Assistant", width=640, height=520)
