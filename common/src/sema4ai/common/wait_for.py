DEFAULT_TIMEOUT = 10


def wait_for_condition(condition, msg=None, timeout=DEFAULT_TIMEOUT, sleep=1 / 20.0):
    """
    Note: wait_for_non_error_condition or wait_for_expected_func_return are usually a better APIs
    to use as the error message is automatically built.

    Args:
        condition: A function that returns True or False.
        msg: A message to be displayed if the condition is not met.
        timeout: The maximum time to wait for the condition to be met.
        sleep: The time to sleep between each check.

    Example:
        wait_for_condition(lambda: x == 1, msg="X did not become 1", timeout=10, sleep=1/20.0)
    """
    import time

    curtime = time.monotonic()

    while True:
        if condition():
            break
        if timeout is not None and (time.monotonic() - curtime > timeout):
            error_msg = f"Condition not reached in {timeout} seconds"
            if msg is not None:
                error_msg += "\n"
                if callable(msg):
                    error_msg += msg()
                else:
                    error_msg += str(msg)

            raise TimeoutError(error_msg)
        time.sleep(sleep)


def wait_for_non_error_condition(
    generate_error_or_none, timeout=DEFAULT_TIMEOUT, sleep=1 / 20.0
):
    """
    Args:
        generate_error_or_none: A function that returns an error message or None.
        timeout: The maximum time to wait for the condition to be met.
        sleep: The time to sleep between each check.

    Example:
        def generate_error_or_none():
            return "X is not 1" if x != 1 else None
        wait_for_non_error_condition(generate_error_or_none, timeout=10, sleep=1/20.0)
    """
    import time

    curtime = time.monotonic()

    while True:
        try:
            error_msg = generate_error_or_none()
        except Exception as e:
            error_msg = str(e)

        if error_msg is None:
            break

        if timeout is not None and (time.monotonic() - curtime > timeout):
            raise TimeoutError(
                f"Condition not reached in {timeout} seconds\n{error_msg}"
            )
        time.sleep(sleep)


def wait_for_expected_func_return(
    func, expected_return, timeout=DEFAULT_TIMEOUT, sleep=1 / 20.0
):
    """
    Args:
        func: A function that returns a value.
        expected_return: The expected return value.
        timeout: The maximum time to wait for the condition to be met.
        sleep: The time to sleep between each check.

    Example:
        wait_for_expected_func_return(lambda: x, 1, timeout=10, sleep=1/20.0)
    """

    def check():
        found = func()
        if found != expected_return:
            return "Expected: %s. Found: %s" % (expected_return, found)

        return None

    wait_for_non_error_condition(check, timeout, sleep)


__all__ = [
    "wait_for_condition",
    "wait_for_non_error_condition",
    "wait_for_expected_func_return",
    "DEFAULT_TIMEOUT",
]
