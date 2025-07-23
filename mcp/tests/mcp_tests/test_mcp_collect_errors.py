def test_errors(datadir):
    from devutils.fixtures import sema4ai_actions_run

    result = sema4ai_actions_run(
        [
            "metadata",
            "--skip-lint",
        ],
        cwd=str(datadir),
        returncode="error",
    )
    errors = result.stderr.decode("utf-8")
    output = result.stdout.decode("utf-8")
    assert (
        "When collecting @resource, the parameters in the uri (found: ['foo']) and the function parameters (found: []) must match."
        in errors
    ), f"errors: {errors} - output: {output}"
    assert (
        "When collecting @resource, parameter 'foo' has type 'list[str]' but only basic types (str, int, float, bool) are supported."
        in errors
    ), f"errors: {errors} - output: {output}"
    assert (
        "When collecting @prompt, parameter 'text' has type 'list[str]' but only basic types (str, int, float, bool) and their Unions with None are supported."
        in errors
    ), f"errors: {errors} - output: {output}"
    assert (
        "Found 3 errors on collect:" in errors
    ), f"errors: {errors} - output: {output}"
