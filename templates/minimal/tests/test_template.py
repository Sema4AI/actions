def test_actions() -> None:
    from actions import greet

    assert greet() == "Hello world!\n"
