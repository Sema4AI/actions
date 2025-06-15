def test_errors(datadir):
    from devutils.fixtures import sema4ai_actions_run

    result = sema4ai_actions_run(
        [
            "metadata",
        ],
        cwd=str(datadir),
        returncode="error",
    )
    errors = result.stderr.decode("utf-8")
    assert (
        "When collecting @resources, the parameters in the uri (found: ['foo']) and the function parameters (found: []) must match."
        in errors
    ), f"errors: {errors}"
    assert (
        "When collecting @resources, parameter 'foo' has type 'list' but only basic types (str, int, float, bool) are supported."
        in errors
    ), f"errors: {errors}"
    assert "Found 3 errors on collect:" in errors, f"errors: {errors}"
