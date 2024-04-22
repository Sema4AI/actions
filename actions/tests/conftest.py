import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

pytest_plugins = [
    "devutils.fixtures",
    "actions_core_tests.fixtures",
]
