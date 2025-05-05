import json
from pathlib import Path

import pytest
from robocorp.log._log_formatting import pretty_format_logs_from_log_html_contents

from sema4ai.action_server._selftest import ActionServerClient, ActionServerProcess


@pytest.mark.integration_test
def test_logs_dont_contain_secrets(
    action_server_process: ActionServerProcess, client: ActionServerClient, tmpdir
):
    """Test to verify that logs don't contain secrets or sensitive information."""
    # Create a simple action that receives a secret password
    action_file = Path(tmpdir) / "secret_action" / "secret_action.py"
    action_file.parent.mkdir(parents=True, exist_ok=True)

    action_file.write_text(
        """
from sema4ai.actions import action

@action
def handle_secret(username: str, password: str) -> str:
    '''Test action that handles sensitive information'''
    print(f"Processing request for user: {username}")
    # We deliberately don't log the password
    # but we use it in the action logic
    return f"User {username} authenticated successfully"
"""
    )

    # Start the action server
    action_server_process.start(
        actions_sync=True,
        cwd=action_file.parent,
        db_file="server.db",
    )

    # Run the action with a username and a secret password
    username = "testuser"
    password = "supersecretpassword123!"

    response = client.post_get_response(
        "api/actions/secret-action/handle-secret/run",
        {"username": username, "password": password},
    )

    # Verify that the action ran successfully
    assert response.status_code == 200
    assert json.loads(response.text) == f"User {username} authenticated successfully"

    # Get the run ID from the response headers
    run_id = response.headers["x-action-server-run-id"]

    # Retrieve and check the log content
    log_html_contents = client.get_str(
        f"api/runs/{run_id}/artifacts/binary-content",
        params={"artifact_name": "log.html"},
    )

    log_contents = pretty_format_logs_from_log_html_contents(log_html_contents)

    # Verify the logs include the username but not the password
    assert username in log_contents
    assert password not in log_contents

    assert "supersecretpassword123!" not in action_server_process.get_stdout()
    assert "supersecretpassword123!" not in action_server_process.get_stderr()

    # The result should not be logged either.
    assert "authenticated successfully" not in action_server_process.get_stdout()
    assert "authenticated successfully" not in action_server_process.get_stderr()
