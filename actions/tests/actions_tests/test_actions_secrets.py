import base64
import json
from pathlib import Path


def test_actions_secret_list(datadir, data_regression):
    from devutils.fixtures import sema4ai_actions_run

    result = sema4ai_actions_run(
        ["list", "--skip-lint"], returncode=0, cwd=str(datadir)
    )
    found = json.loads(result.stdout)
    assert len(found) == 4  # Updated to 4 actions (added type alias action)
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


def test_actions_secret_run_just_secret(datadir: Path):
    from devutils.fixtures import sema4ai_actions_run

    # Specifies the request in the json input.
    json_output = datadir / "json.output"
    json_input_contents = {
        "my_password": "this-is-the-secret",
    }

    input_json = datadir / "json.input"
    input_json.write_text(json.dumps(json_input_contents))

    args = [
        "run",
        "-a",
        "action_with_secret",
        datadir,
        f"--json-input={input_json}",
    ]

    sema4ai_actions_run(args, returncode=0, cwd=str(datadir))
    assert json_output.read_text() == "this-is-the-secret"


def test_actions_secret_run_with_annotated_secret(datadir: Path):
    from devutils.fixtures import sema4ai_actions_run

    # Specifies the request in the json input.
    json_output = datadir / "json.output"
    json_input_contents = {
        "config_secret": json.dumps({"value": "this-is-the-secret"}),
    }

    input_json = datadir / "json.input"
    input_json.write_text(json.dumps(json_input_contents))

    args = [
        "run",
        "-a",
        "action_with_secret_annotated",
        datadir,
        f"--json-input={input_json}",
    ]

    sema4ai_actions_run(args, returncode=0, cwd=str(datadir))
    assert json_output.read_text() == '{"value": "this-is-the-secret"}'


def test_actions_secret_run_with_request(datadir: Path):
    from devutils.fixtures import sema4ai_actions_run

    # Specifies the request in the json input.
    json_output = datadir / "json.output"
    json_input_contents = {
        "request": {
            "headers": {
                "x-action-context": base64.b64encode(
                    json.dumps(
                        {"secrets": {"my_password": "this-is-the-secret"}}
                    ).encode("utf-8")
                ).decode("ascii")
            }
        },
    }

    input_json = datadir / "json.input"
    input_json.write_text(json.dumps(json_input_contents))

    args = [
        "run",
        "-a",
        "action_with_secret_and_request",
        datadir,
        f"--json-input={input_json}",
    ]

    sema4ai_actions_run(args, returncode=0, cwd=str(datadir))
    assert json_output.read_text() == "this-is-the-secret"


def test_actions_secret_without_request_with_data_in_headers(datadir: Path):
    from devutils.fixtures import sema4ai_actions_run

    # Specifies the request in the json input.
    json_output = datadir / "json.output"
    json_input_contents = {
        "request": {
            "headers": {
                "x-action-context": base64.b64encode(
                    json.dumps(
                        {"secrets": {"my_password": "this-is-the-secret"}}
                    ).encode("utf-8")
                ).decode("ascii")
            }
        },
    }

    input_json = datadir / "json.input"
    input_json.write_text(json.dumps(json_input_contents))

    args = [
        "run",
        "-a",
        "action_with_secret",
        datadir,
        f"--json-input={input_json}",
    ]

    sema4ai_actions_run(args, returncode=0, cwd=str(datadir))
    assert json_output.read_text() == "this-is-the-secret"


def test_actions_secret_in_env(datadir: Path):
    from devutils.fixtures import sema4ai_actions_run

    # Specifies the request in the json input.
    json_output = datadir / "json.output"

    args = [
        "run",
        "-a",
        "action_with_secret",
    ]

    sema4ai_actions_run(
        args,
        returncode=0,
        cwd=str(datadir),
        additional_env={"MY_PASSWORD": "this-is-the-secret"},
    )
    assert json_output.read_text() == "this-is-the-secret"


def test_actions_secret_without_request_in_header_directly(datadir: Path):
    from devutils.fixtures import sema4ai_actions_run

    # Specifies the request in the json input.
    json_output = datadir / "json.output"
    json_input_contents = {
        "request": {"headers": {"x-my-password": "this-is-the-secret"}},
    }

    input_json = datadir / "json.input"
    input_json.write_text(json.dumps(json_input_contents))

    args = [
        "run",
        "-a",
        "action_with_secret",
        datadir,
        f"--json-input={input_json}",
    ]

    sema4ai_actions_run(args, returncode=0, cwd=str(datadir))
    assert json_output.read_text() == "this-is-the-secret"


def test_actions_secret_with_type_alias(datadir: Path):
    from devutils.fixtures import sema4ai_actions_run

    # Test with type alias (DocumentIntelligenceSecret)
    json_output = datadir / "json.output"
    json_input_contents = {
        "docint_secret": "this-is-the-docint-secret",
    }

    input_json = datadir / "json.input"
    input_json.write_text(json.dumps(json_input_contents))

    args = [
        "run",
        "-a",
        "action_with_secret_type_alias",
        datadir,
        f"--json-input={input_json}",
    ]

    sema4ai_actions_run(args, returncode=0, cwd=str(datadir))
    assert json_output.read_text() == "this-is-the-docint-secret"
