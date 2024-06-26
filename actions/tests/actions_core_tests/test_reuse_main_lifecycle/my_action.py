from typing import Sequence

from sema4ai.actions import IAction, action, setup, teardown

session_setup = 0
task_setup = 0

task_executed = 0

session_teardown = 0
task_teardown = 0


@setup
def my_task_setup(task: IAction):
    global task_setup
    task_setup += 1
    print("task setup", task_setup)


@setup(scope="session")
def my_session_setup(actions: Sequence[IAction]):
    global session_setup
    session_setup += 1
    print("session setup", session_setup)


@teardown
def my_task_teardown(task: IAction):
    global task_teardown
    task_teardown += 1
    print("task teardown", task_teardown)


@teardown(scope="session")
def my_session_teardown(actions: Sequence[IAction]):
    global session_teardown
    session_teardown += 1
    print("session teardown", session_setup)


@action
def reuse_task():
    global task_executed
    task_executed += 1
    print("task executed", task_executed)
