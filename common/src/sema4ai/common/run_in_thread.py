import asyncio.futures
from concurrent import futures
from typing import Callable, TypeVar

T = TypeVar("T")


def run_in_thread(target: Callable[[], T], **kwargs) -> futures.Future[T]:
    """
    Runs a given target in a thread returning a Future which can be used to
    track its result.

    Args:
        target: The target to run in a thread. Will be called with no arguments.
        kwargs: Additional arguments to pass to the thread creation function.

    Returns:
        A Future which can be used to track the result of the thread.

    Example:
        future = run_in_thread(lambda: 1 + 1, daemon=True)
        result = future.result()
        print(result)
    """
    fut: futures.Future[T] = futures.Future()
    if "name" not in kwargs:
        kwargs["name"] = f"run_in_thread:{target}"

    def new_target():
        try:
            result = target()
        except BaseException as e:
            fut.set_exception(e)
        else:
            fut.set_result(result)

    import threading

    t = threading.Thread(target=new_target, **kwargs)
    t.start()
    return fut


def run_in_thread_asyncio(
    target: Callable[[], T],
    **kwargs,
) -> asyncio.futures.Future[T]:
    """
    Runs a given target in a thread returning an asyncio Future which can be
    awaited in an asyncio loop.

    Args:
        target: The target to run in a thread. Will be called with no arguments.
        kwargs: Additional arguments to pass to the thread creation function.

    Returns:
        An asyncio Future which can be awaited in an asyncio loop.

    Example:
        future = run_in_thread_asyncio(lambda: 1 + 1)
        result = await future
        print(result)
    """
    from asyncio.futures import wrap_future

    fut = run_in_thread(target, **kwargs)
    return wrap_future(fut)
