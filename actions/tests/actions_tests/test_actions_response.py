def test_actions_response_list(datadir, data_regression):
    import json

    from devutils.fixtures import sema4ai_actions_run

    result = sema4ai_actions_run(
        ["list", "--skip-lint"], returncode=0, cwd=str(datadir)
    )
    found = json.loads(result.stdout)
    # print(json.dumps(found, indent=4))
    assert len(found) == 5
    data = {}
    for f in found:
        data[f["name"]] = {
            "input_schema": f["input_schema"],
            "managed_params_schema": f["managed_params_schema"],
            "output_schema": f["output_schema"],
        }

    data_regression.check(data)


def test_actions_return_response_ok_action(datadir, data_regression):
    from devutils.fixtures import sema4ai_actions_run

    result = sema4ai_actions_run(
        ["run", "-a=return_response_ok_action", "--print-result"],
        returncode=0,
        cwd=str(datadir),
    )
    assert "PASS" in result.stdout.decode("utf-8")


def test_actions_return_response_error_action(datadir, data_regression):
    from devutils.fixtures import sema4ai_actions_run

    result = sema4ai_actions_run(
        ["run", "-a=return_response_error_action", "--print-result"],
        returncode=1,
        cwd=str(datadir),
    )
    assert "Something bad happened" in result.stdout.decode("utf-8")
    assert "FAIL" in result.stdout.decode("utf-8")


def test_actions_raise_other_error_action(datadir, data_regression):
    from devutils.fixtures import sema4ai_actions_run

    result = sema4ai_actions_run(
        ["run", "-a=raise_other_error_action", "--print-result"],
        returncode=1,
        cwd=str(datadir),
    )
    assert "Unexpected error (RuntimeError)" in result.stdout.decode("utf-8")
    assert "FAIL" in result.stdout.decode("utf-8")


def test_actions_raise_error_bad_schema(datadir, data_regression):
    from devutils.fixtures import sema4ai_actions_run

    result = sema4ai_actions_run(
        ["run", "-a=bad_schema", "--print-result"],
        returncode=0,
        cwd=str(datadir),
    )
    assert (
        "Although the action: 'bad_schema' ran properly, it returned a value of type <class 'int'> whereas the expected return type is <class 'sema4ai.actions._response.Response[str]'>."
        in result.stdout.decode("utf-8")
    )


def test_actions_raise_action_error_action(datadir, data_regression):
    from devutils.fixtures import sema4ai_actions_run

    result = sema4ai_actions_run(
        ["run", "-a=raise_action_error_action", "--print-result"],
        returncode=1,
        cwd=str(datadir),
    )
    assert "Action error" in result.stdout.decode("utf-8")
    assert "FAIL" in result.stdout.decode("utf-8")
