import sys
from pathlib import Path

# Add build-binary directory to Python path for test imports
# The build system modules are in build-binary/ (not a standard Python package)
action_server_root = Path(__file__).parent.parent
build_binary_path = action_server_root / "build-binary"
if build_binary_path.exists() and str(build_binary_path) not in sys.path:
    sys.path.insert(0, str(build_binary_path))

# Add devutils to Python path
repo_root = action_server_root.parent
devutils_src_path = repo_root / "devutils" / "src"
if devutils_src_path.exists() and str(devutils_src_path) not in sys.path:
    sys.path.insert(0, str(devutils_src_path))

pytest_plugins = [
    "devutils.fixtures",
    "action_server_tests.fixtures",
]


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration_test: mark test to run only on integration test"
    )
