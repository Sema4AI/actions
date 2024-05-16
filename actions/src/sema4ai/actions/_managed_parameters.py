import inspect
from ast import FunctionDef
from typing import Any, Dict, Optional, overload

from sema4ai.actions._customization._extension_points import EPManagedParameters


class ManagedParameters:
    """
    Default implementation of EPManagedParameters.

    The idea is that in the constructor it receives the parameter names and
    the actual instance mapped from the parameter name.
    """

    def __init__(self, param_name_to_instance: Dict[str, Any]):
        self._param_name_to_instance = param_name_to_instance

    @overload
    def is_managed_param(self, param_name: str, *, node: FunctionDef) -> bool:
        raise NotImplementedError()

    @overload
    def is_managed_param(self, param_name: str, *, param: inspect.Parameter) -> bool:
        raise NotImplementedError()

    def is_managed_param(
        self,
        param_name: str,
        *,
        node: Optional[FunctionDef] = None,
        param: Optional[inspect.Parameter] = None,
    ) -> bool:
        from sema4ai.actions._secret import (
            is_oauth2_secret_subclass,
            is_secret_subclass,
        )

        if param_name in self._param_name_to_instance:
            return True

        if node is not None:
            assert (
                param is None
            ), "Either node or param is expected, but not both at the same time."
            return self._is_secret_node(param_name, node)

        elif param is not None:
            if param.annotation:
                if is_secret_subclass(param.annotation):
                    return True
                if is_oauth2_secret_subclass(param.annotation):
                    return True

        else:
            raise AssertionError("Either node or param must be passed.")

        return False

    def _is_secret_node(self, param_name: str, node: FunctionDef) -> bool:
        import ast

        args: ast.arguments = node.args
        for arg in args.args:
            if arg.arg == param_name:
                if arg.annotation:
                    unparsed = ast.unparse(arg.annotation)
                    if unparsed in (
                        "Secret",
                        "actions.Secret",
                        "sema4ai.actions.Secret",
                    ):
                        return True

                return False

        return False

    def inject_managed_params(
        self,
        sig: inspect.Signature,
        new_kwargs: Dict[str, Any],
        original_kwargs: Dict[str, Any],
    ) -> Dict[str, Any]:
        from sema4ai.actions._action_context import ActionContext
        from sema4ai.actions._request import Request
        from sema4ai.actions._secret import (
            OAuth2Secret,
            Secret,
            is_oauth2_secret_subclass,
            is_secret_subclass,
        )

        use_kwargs = new_kwargs.copy()

        request = new_kwargs.get("request")
        if request is None:
            req = original_kwargs.get("request")
            if req is not None:
                request = Request.model_validate(req)
        if request is None:
            request = self._param_name_to_instance.get("request")

        x_action_context = ActionContext.from_request(request)

        for param in sig.parameters.values():
            if (
                param.name not in use_kwargs
                and param.name in self._param_name_to_instance
            ):
                use_kwargs[param.name] = self._param_name_to_instance[param.name]

            elif param.annotation:
                use_class: Optional[Any] = None
                if is_secret_subclass(param.annotation):
                    use_class = Secret

                elif is_oauth2_secret_subclass(param.annotation):
                    use_class = OAuth2Secret

                if use_class is not None:
                    # Handle a secret
                    secret_value = original_kwargs.get(param.name)

                    if secret_value is not None:
                        # Gotten directly from the input.json (or command line)
                        # as a value in the root.
                        use_kwargs[param.name] = use_class.model_validate(secret_value)

                    elif x_action_context is not None:
                        use_kwargs[param.name] = use_class.from_action_context(
                            x_action_context, f"secrets/{param.name}"
                        )

        return use_kwargs

    @overload
    def get_managed_param_type(
        self, param_name: str, *, param: inspect.Parameter
    ) -> type:
        raise NotImplementedError()

    @overload
    def get_managed_param_type(self, param_name: str, *, node: FunctionDef) -> str:
        raise NotImplementedError()

    def get_managed_param_type(
        self,
        param_name: str,
        *,
        param: Optional[inspect.Parameter] = None,
        node: Optional[FunctionDef] = None,
    ) -> type | str:
        from sema4ai.actions._request import Request
        from sema4ai.actions._secret import (
            OAuth2Secret,
            Secret,
            is_oauth2_secret_subclass,
            is_secret_subclass,
        )

        if param_name == "request":
            return Request

        if node is None and param is None:
            raise ValueError("Either node or param are required.")
        if node is not None and param is not None:
            raise ValueError(
                "Either node or param is expected, but not both at the same time."
            )

        if param is not None:
            if param.annotation:
                if is_secret_subclass(param.annotation):
                    return Secret

                if is_oauth2_secret_subclass(param.annotation):
                    return OAuth2Secret
        else:
            assert node is not None
            if self._is_secret_node(param_name, node):
                return "Secret"

        raise RuntimeError(
            f"Unable to get managed parameter type for parameter: {param}"
        )

    def __typecheckself__(self) -> None:
        from sema4ai.actions._protocols import check_implements

        _: EPManagedParameters = check_implements(self)


def _get_secret_header_name(secret_name: str) -> str:
    secret_name = secret_name.replace("_", "-")
    return f"x-secret-{secret_name}"
