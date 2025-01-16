def test_callback():
    from sema4ai.common.callback import Callback

    callback = Callback()

    called = []

    with callback.register(lambda x: called.append(x)):
        with callback.register(lambda x: called.append(x + 100)):
            callback(1)
            callback(2)
        callback(3)

    assert called == [1, 101, 2, 102, 3]


def test_callback_reverse():
    from sema4ai.common.callback import Callback

    callback = Callback(reversed=True)

    called = []

    with callback.register(lambda x: called.append(x)):
        with callback.register(lambda x: called.append(x + 100)):
            callback(1)
            callback(2)
        callback(3)
    assert called == [101, 1, 102, 2, 3]
