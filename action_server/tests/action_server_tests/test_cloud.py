import os


def test_cloud_list_organizations(data_regression):
    import json

    from sema4ai.action_server._selftest import robocorp_action_server_run

    access_credentials = os.environ.get("ACTION_SERVER_TEST_ACCESS_CREDENTIALS")
    assert (
        access_credentials
    ), "ACTION_SERVER_TEST_ACCESS_CREDENTIALS environment required for test."
    output = robocorp_action_server_run(
        [
            "cloud",
            "list-organizations",
            "--access-credentials",
            os.environ.get("ACTION_SERVER_TEST_ACCESS_CREDENTIALS"),
            "--hostname",
            os.environ.get("ACTION_SERVER_TEST_HOSTNAME", "https://ci.robocorp.dev"),
            "--json",
        ],
        returncode=0,
    )
    data_regression.check(json.loads(output.stdout))
