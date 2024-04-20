import inspect
from functools import wraps
from typing import Callable, Literal, TypeVar, Union, overload

from ._protocols import IActionCallback, IActionsCallback

T = TypeVar("T")
Decorator = Callable[[T], T]


@overload
def setup(func: IActionCallback) -> IActionCallback:
    ...


@overload
def setup(*, scope: Literal["action"] = "action") -> Decorator[IActionCallback]:
    ...


@overload
def setup(*, scope: Literal["session"]) -> Decorator[IActionsCallback]:
    ...


def setup(
    *args, **kwargs
) -> Union[IActionCallback, Decorator[IActionCallback], Decorator[IActionsCallback]]:
    """Run code before any actions start, or before each separate action.

    Receives as an argument the action or actions that will be run.

    Can be used as a decorator without arguments:

    ```python
    from sema4ai.actions import setup

    @setup
    def my_fixture(action):
        print(f"Before action: {action.name}")
    ```

    Alternatively, can be called with a `scope` argument to decide when
    the fixture is run:

    ```python
    from sema4ai.actions import setup

    @setup(scope="action")
    def before_each(action):
        print(f"Running action '{action.name}'")

    @setup(scope="session")
    def before_all(actions):
        print(f"Running {len(actions)} action(s)")
    ```

    By default, runs setups in `action` scope.

    The `setup` fixture also allows running code after the execution,
    if it `yield`s the execution to the action(s):

    ```python
    import time
    from sema4ai.actions import setup

    @setup
    def measure_time(action):
        start = time.time()
        yield  # Action executes here
        duration = time.time() - start
        print(f"Action took {duration} seconds")

    @action
    def my_long_action():
        ...
    ```

    **Note:** If fixtures are defined in another file, they need to be imported
     in the main actions file to be taken into use
    """
    from sema4ai.actions._hooks import (
        after_action_run,
        after_all_actions_run,
        before_action_run,
        before_all_actions_run,
    )

    def _register_callback(before, after, func):
        if inspect.isgeneratorfunction(func):

            @wraps(func)
            def generator(*args, **kwargs):
                gen = func(*args, **kwargs)
                next(gen)

                def teardown(*args, **kwargs):
                    try:
                        next(gen)
                    except StopIteration:
                        pass
                    finally:
                        after.unregister(teardown)

                after.register(teardown)

            before.register(generator)
            return generator
        else:
            before.register(func)
            return func

    if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
        return _register_callback(before_action_run, after_action_run, args[0])

    scope = kwargs.get("scope", "action")
    if scope == "action":

        def wrapped_action(func):
            return _register_callback(before_action_run, after_action_run, func)

        return wrapped_action
    elif scope == "session":

        def wrapped_session(func):
            return _register_callback(
                before_all_actions_run, after_all_actions_run, func
            )

        return wrapped_session
    else:
        raise ValueError(f"Unknown scope '{scope}', expected 'action' or 'session'")


@overload
def teardown(func: IActionCallback) -> IActionCallback:
    ...


@overload
def teardown(*, scope: Literal["action"] = "action") -> Decorator[IActionCallback]:
    ...


@overload
def teardown(*, scope: Literal["session"]) -> Decorator[IActionsCallback]:
    ...


def teardown(
    *args, **kwargs
) -> Union[IActionCallback, Decorator[IActionCallback], Decorator[IActionsCallback]]:
    """Run code after actions have been run, or after each separate action.

    Receives as an argument the action or actions that were executed, which
    contain (among other things) the resulting status and possible error message.

    Can be used as a decorator without arguments:

    ```python
    from sema4ai.actions import teardown

    @teardown
    def my_fixture(action):
        print(f"After action: {action.name})
    ```

    Alternatively, can be called with a `scope` argument to decide when
    the fixture is run:

    ```python
    from sema4ai.actions import teardown

    @teardown(scope="action")
    def after_each(action):
        print(f"Action '{action.name}' status is '{action.status}'")

    @teardown(scope="session")
    def after_all(actions):
        print(f"Executed {len(actions)} action(s)")
    ```

    By default, runs teardowns in `action` scope.

    **Note:** If fixtures are defined in another file, they need to be imported
     in the main actions file to be taken into use
    """
    from sema4ai.actions._hooks import after_action_run, after_all_actions_run

    if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
        func: IActionCallback = args[0]
        after_action_run.register(func)
        return func

    scope = kwargs.get("scope", "action")
    if scope == "action":

        def wrapped_action(func: IActionCallback):
            after_action_run.register(func)
            return func

        return wrapped_action
    elif scope == "session":

        def wrapped_session(func: IActionsCallback):
            after_all_actions_run.register(func)
            return func

        return wrapped_session
    else:
        raise ValueError(f"Unknown scope '{scope}', expected 'action' or 'session'")
