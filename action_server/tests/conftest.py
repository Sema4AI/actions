pytest_plugins = [
    "devutils.fixtures",
    "action_server_tests.fixtures",
]


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration_test: mark test to run only on integration test"
    )
