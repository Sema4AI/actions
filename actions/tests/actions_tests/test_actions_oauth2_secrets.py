from pathlib import Path


def test_actions_oauth2_secret_run_with_request(datadir: Path):
    import base64
    import json

    from devutils.fixtures import sema4ai_actions_run

    datadir = datadir / "good"

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


def test_actions_oauth2_secret_run_with_input(datadir: Path):
    import json

    from devutils.fixtures import sema4ai_actions_run

    datadir = datadir / "good"

    # Specifies the request in the json input.
    json_output = datadir / "json.output"
    secret_data = {
        "provider": "google",
        "scopes": ["https://www.googleapis.com/auth/drive.file"],
        "access_token": "this-is-the-access-token",
        "metadata": {"anything": "goes here"},
    }
    json_input_contents = {"message": "some-message", "google_secret": secret_data}

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


def test_actions_oauth2_secret_list(datadir, data_regression):
    import json

    from devutils.fixtures import sema4ai_actions_run

    datadir = datadir / "good"

    result = sema4ai_actions_run(
        ["list", "--skip-lint"], returncode=0, cwd=str(datadir)
    )
    found = json.loads(result.stdout)
    assert len(found) == 1
    # # Note: the secret does not appear in the schema!
    # print(json.dumps(found, indent=4))
    data = {}
    for f in found:
        data[f["name"]] = {
            "input_schema": f["input_schema"],
            "managed_params_schema": f["managed_params_schema"],
            "output_schema": f["output_schema"],
        }
    data_regression.check(data)


def test_actions_oauth2_secret_list_bad(datadir):
    from devutils.fixtures import sema4ai_actions_run

    datadir = datadir / "bad"

    result = sema4ai_actions_run(
        ["list", "--skip-lint"], returncode=1, cwd=str(datadir)
    )
    assert "Invalid OAuth2Secret annotation found." in result.stderr.decode("utf-8")
