import threading
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator, Optional


@dataclass
class ValidateAndConvertKwargsScope:
    param_name: str
    param_type: type


_thread_local_scope = threading.local()


@contextmanager
def create_validate_and_convert_kwargs_scope(
    param_name: str, param_type: type
) -> Iterator[ValidateAndConvertKwargsScope]:
    attr = "validate_and_convert"
    scope = ValidateAndConvertKwargsScope(param_name=param_name, param_type=param_type)
    assert get_validate_and_convert_kwargs_scope() is None, "A scope is already active!"
    setattr(_thread_local_scope, attr, scope)
    try:
        yield scope
    finally:
        setattr(_thread_local_scope, attr, None)


def get_validate_and_convert_kwargs_scope() -> Optional[ValidateAndConvertKwargsScope]:
    """
    Enables getting the current registered scope during arg validation.

    This is a workaround for creating the OAuth2 instance getting the provider
    and scope from what is in the parameter type definition (ideally this'd have
    been passed in the OAuth2Secret.model_validate, but to maintain compatibility
    with the expected `model_validate` API, it was added as a thread-local,
    set during the argument validation/conversion).
    """
    return getattr(_thread_local_scope, "validate_and_convert", None)
