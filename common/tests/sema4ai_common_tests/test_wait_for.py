import pytest


class _Checker:
    def __init__(self, expected_value):
        self.x = 0
        self.expected_value = expected_value

    def generate_error_or_none(self):
        self.x += 1
        return (
            "X is not %s" % self.expected_value
            if self.x != self.expected_value
            else None
        )


def test_wait_for_non_error_condition():
    import sys

    from sema4ai.common.wait_for import wait_for_non_error_condition

    wait_for_non_error_condition(_Checker(10).generate_error_or_none)

    with pytest.raises(TimeoutError):
        wait_for_non_error_condition(
            _Checker(sys.maxsize).generate_error_or_none, timeout=0.5, sleep=1 / 30.0
        )


def test_wait_for_condition():
    import sys

    from sema4ai.common.wait_for import wait_for_condition

    checker = _Checker(10)

    def check():
        checker.x += 1
        return checker.x == checker.expected_value

    wait_for_condition(
        check,
        msg=lambda: "X (%s) is not %s" % (checker.x, checker.expected_value),
    )

    checker = _Checker(sys.maxsize)
    with pytest.raises(TimeoutError) as e:
        wait_for_condition(
            check,
            msg=lambda: "X (%s) is not %s" % (checker.x, checker.expected_value),
            timeout=0.3,
            sleep=1 / 20.0,
        )
    assert "X (%s) is not %s" % (checker.x, checker.expected_value) in str(e.value)
