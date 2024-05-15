from pathlib import Path


def test_actions_oauth2_secret_run_with_request(datadir: Path):
    import base64
    import json

    from devutils.fixtures import sema4ai_actions_run

    # Specifies the request in the json input.
    json_output = datadir / "json.output"
    secret_data = {
        "provider": "google",
        "scopes": ["https://www.googleapis.com/auth/drive.file"],
        "access_token": "this-is-the-access-token",
        "metadata": {"anything": "goes here"},
    }
    json_input_contents = {
        "message": "some-message",
        "request": {
            "headers": {
                "x-action-context": base64.b64encode(
                    json.dumps({"secrets": {"google_secret": secret_data}}).encode(
                        "utf-8"
                    )
                ).decode("ascii")
            }
        },
    }

    input_json = datadir / "json.input"
    input_json.write_text(json.dumps(json_input_contents))

    args = [
        "run",
        "-a",
        "action_check_oauth2",
        datadir,
        f"--json-input={input_json}",
    ]

    sema4ai_actions_run(args, returncode=0, cwd=str(datadir))
    assert json.loads(json_output.read_text()) == secret_data
