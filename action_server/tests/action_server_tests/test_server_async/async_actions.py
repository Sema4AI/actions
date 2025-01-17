from sema4ai.actions import action


@action
def sleep_action(time_to_sleep: float) -> float:
    """
    Args:
        time_to_sleep: The number of seconds to sleep.

    Returns:
        The number of seconds that were slept.
    """
    import time

    time.sleep(time_to_sleep)
    return time_to_sleep
