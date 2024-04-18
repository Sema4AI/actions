from sema4ai.tasks import task


@task
def my_task() -> str:
    return "my_task_ran"
