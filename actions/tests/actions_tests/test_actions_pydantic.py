def test_pydantic_models(datadir):
    """
    Test that pydantic can be used properly wherever needed.
    """

    import json

    from devutils.fixtures import sema4ai_actions_run

    # Specifies the request in the json input.
    json_input_contents = {}

    input_json = datadir / "json.input"
    input_json.write_text(json.dumps(json_input_contents))
    output_json = datadir / "json.output"

    args = [
        "run",
        "-a",
        "add_rows",
        datadir,
        f"--json-input={input_json}",
        "--print-input",
        "--print-result",
        f"--json-output={output_json}",
    ]

    result = sema4ai_actions_run(args, returncode=0, cwd=str(datadir))
    output = result.stdout.decode("utf-8")
    loaded = json.loads(output_json.read_text())
    assert loaded == {
        "result": {"result": {"ok": True, "document_id": "doc-id"}, "error": None},
        "message": "",
        "status": "PASS",
    }
    assert '"ok": true' in output  # i.e.: it's printed


def _fix_file(entry):
    import os.path

    entry["file"] = os.path.basename(entry["file"])


def test_pydantic_models_list(datadir, data_regression):
    import json

    from devutils.fixtures import sema4ai_actions_run

    result = sema4ai_actions_run(
        ["list", "--skip-lint"], returncode=0, cwd=str(datadir)
    )
    found = json.loads(result.stdout)
    for entry in found:
        _fix_file(entry)
    data_regression.check(
        sorted(found, key=lambda entry: (entry["name"], entry["line"]))
    )
