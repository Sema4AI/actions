def test_my_action_ok():
    import my_action  # type: ignore

    assert my_action.doit() == "Ok"


def test_my_action_fail():
    import my_action  # type: ignore

    assert my_action.doit() == "fail", "This will fail"
