import inspect
import typing
from ast import FunctionDef
from typing import Any, Dict, Optional, Protocol, overload

if typing.TYPE_CHECKING:
    from sema4ai.actions._action_context import RequestContexts


class EPManagedParameters(Protocol):
    """
    The protocol for a class that describes the managed parameters when
    calling an action.
    """

    @overload
    def is_managed_param(self, param_name: str, *, node: FunctionDef) -> bool:
        """
        API to detect whether a given parameter is a managed parameter.

        Args:
            param_name: The name of the parameter.
            param: The FunctionDef to be checked (information in this case
                is gathered statically, when linting the action).

        Return: True if it's a managed parameter and False otherwise.
        """
        raise NotImplementedError()

    @overload
    def is_managed_param(self, param_name: str, *, param: inspect.Parameter) -> bool:
        """
        API to detect whether a given parameter is a managed parameter.

        Args:
            param_name: The name of the parameter.
            param: The inspect.Parameter to be checked (information in this case
                is gathered at runtime, when running the action).

        Return: True if it's a managed parameter and False otherwise.
        """
        raise NotImplementedError()

    def inject_managed_params(
        self,
        sig: inspect.Signature,
        request_contexts: Optional["RequestContexts"],
        new_kwargs: Dict[str, Any],
        original_kwargs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        This enables the addition of managed parameters into a call to the action.

        Args:
            sig: The signature of the function being called.
            request_contexts: The request contexts (may be None).
            new_kwargs: The new kwargs (where the parameters should be injected).
            original_kwargs: The original kwargs passed to the function.
        """
        raise NotImplementedError()

    @overload
    def get_managed_param_type(
        self, param_name: str, *, param: inspect.Parameter
    ) -> type:
        """
        Provides the type of the given managed parameter.

        Args:
            param_name: The parameter name for which the type is requested.
            param: The parameter for which the type is requested.

        Return: The type of the managed parameter.
        """
        raise NotImplementedError()

    @overload
    def get_managed_param_type(self, param_name: str, *, node: FunctionDef) -> str:
        """
        Provides the type (as a string) of the given managed parameter.

        Args:
            param_name: The parameter name for which the type is requested.
            node: The function definition node of the requested parameter

        Return: The type (string) of the managed parameter.
        """
        raise NotImplementedError()
