import os

from sema4ai.actions.cli import main

if __name__ == "__main__":
    os.environ["RC_TASKS_SKIP_SESSION_TEARDOWN"] = "1"
    returncode = main(["run", "-a", "reuse_task", "--console-colors=plain"], exit=False)
    assert returncode == 0

    import my_action  # type: ignore # @UnresolvedImport

    assert my_action.session_setup == 1
    assert my_action.session_teardown == 0

    assert my_action.task_executed == 1
    assert my_action.task_setup == 1
    assert my_action.task_teardown == 1

    os.environ["RC_TASKS_SKIP_SESSION_SETUP"] = "1"
    returncode = main(["run", "-a", "reuse_task", "--console-colors=plain"], exit=False)
    assert returncode == 0

    assert my_action.session_setup == 1
    assert my_action.session_teardown == 0

    assert my_action.task_executed == 2
    assert my_action.task_setup == 2
    assert my_action.task_teardown == 2

    os.environ["RC_TASKS_SKIP_SESSION_TEARDOWN"] = "0"
    returncode = main(["run", "-a", "reuse_task", "--console-colors=plain"], exit=False)
    assert returncode == 0

    assert my_action.session_setup == 1
    assert my_action.session_teardown == 1

    assert my_action.task_executed == 3
    assert my_action.task_setup == 3
    assert my_action.task_teardown == 3
