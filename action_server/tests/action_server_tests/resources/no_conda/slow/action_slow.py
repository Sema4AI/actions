from sema4ai.actions import action


@action
def long_running(duration: float) -> str:
    """A tool that takes some time to execute.

    Args:
        duration: How long to sleep in seconds.

    Returns:
        A message indicating completion.
    """
    import time

    time.sleep(duration)
    return f"Completed after {duration} seconds"
