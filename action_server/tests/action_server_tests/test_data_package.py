def test_data_package_metadata(datadir, data_regression):
    import json

    from action_server_tests.fixtures import fix_metadata, get_in_resources

    from sema4ai.action_server._selftest import sema4ai_action_server_run

    data_package = get_in_resources("data_package")
    output = sema4ai_action_server_run(
        [
            "package",
            "metadata",
            "--input-dir",
            str(data_package),
            "--datadir",
            str(datadir / "data"),
        ],
        returncode=0,
        cwd=data_package,
    )
    data_regression.check(fix_metadata(json.loads(output.stdout)))
