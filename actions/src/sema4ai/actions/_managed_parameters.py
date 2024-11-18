import inspect
import typing
from ast import FunctionDef
from typing import Any, Dict, Optional, overload

from sema4ai.actions._customization._extension_points import EPManagedParameters

if typing.TYPE_CHECKING:
    from sema4ai.actions._action_context import RequestContexts


class ManagedParameterHeuristic:
    def is_managed_node(self, param_name: str, *, node: FunctionDef) -> bool:
        return False

    def is_managed_param(self, param_name: str, *, param: inspect.Parameter) -> bool:
        return False

    def create_managed_param(
        self,
        request_contexts: Optional["RequestContexts"],
        annotation: type,
        original_kwargs: Dict[str, Any],
        param_name: str,
    ) -> Any:
        return None

    def get_managed_param_type_from_annotation(self, annotation: type) -> type | None:
        return None

    def get_managed_param_type_from_node(
        self, param_name: str, node: FunctionDef
    ) -> type | None:
        return None


class ManagedParameterHeuristicRequest(ManagedParameterHeuristic):
    """
    Note: the rquest heuristic is special: it's actually managed
    using the parameter name instead of the annotation.
    """


class ManagedParameterHeuristicSecret(ManagedParameterHeuristic):
    def create_managed_param(
        self,
        request_contexts: Optional["RequestContexts"],
        annotation: type,
        original_kwargs: Dict[str, Any],
        param_name: str,
    ) -> Any:
        from sema4ai.actions._secret import Secret, is_secret_subclass

        use_class: Optional[Any] = None
        if is_secret_subclass(annotation):
            use_class = Secret

        if use_class is not None:
            # Handle a secret
            secret_value = original_kwargs.get(param_name)

            if secret_value is not None:
                # Gotten directly from the input.json (or command line)
                # as a value in the root.
                return use_class.model_validate(secret_value)

            elif request_contexts is not None:
                return use_class.from_action_context(
                    request_contexts.action_context, f"secrets/{param_name}"
                )
        return None

    def is_managed_node(self, param_name: str, *, node: FunctionDef) -> bool:
        return self._is_secret_node(param_name, node)

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

    def is_managed_param(self, param_name: str, *, param: inspect.Parameter) -> bool:
        from sema4ai.actions._secret import is_secret_subclass

        if is_secret_subclass(param.annotation):
            return True
        return False

    def get_managed_param_type_from_annotation(self, annotation: type) -> type | None:
        from sema4ai.actions._secret import Secret, is_secret_subclass

        if is_secret_subclass(annotation):
            return Secret
        return None

    def get_managed_param_type_from_node(
        self, param_name: str, node: FunctionDef
    ) -> type | None:
        from sema4ai.actions._secret import Secret

        if self._is_secret_node(param_name, node):
            return Secret
        return None


class ManagedParameterHeuristicOAuth2Secret(ManagedParameterHeuristic):
    def create_managed_param(
        self,
        request_contexts: Optional["RequestContexts"],
        annotation: type,
        original_kwargs: Dict[str, Any],
        param_name: str,
    ) -> Any:
        from sema4ai.actions._secret import OAuth2Secret, is_oauth2_secret_subclass

        use_class: Optional[Any] = None
        if is_oauth2_secret_subclass(annotation):
            use_class = OAuth2Secret

        if use_class is not None:
            # Handle a secret
            secret_value = original_kwargs.get(param_name)

            if secret_value is not None:
                # Gotten directly from the input.json (or command line)
                # as a value in the root.
                return use_class.model_validate(secret_value)

            elif request_contexts is not None:
                return use_class.from_action_context(
                    request_contexts.action_context, f"secrets/{param_name}"
                )
        return None

    def is_managed_param(self, param_name: str, *, param: inspect.Parameter) -> bool:
        from sema4ai.actions._secret import is_oauth2_secret_subclass

        if is_oauth2_secret_subclass(param.annotation):
            return True
        return False

    def get_managed_param_type_from_annotation(self, annotation: type) -> type | None:
        from sema4ai.actions._secret import OAuth2Secret, is_oauth2_secret_subclass

        if is_oauth2_secret_subclass(annotation):
            return OAuth2Secret

        return None


class ManagedParameterHeuristicDataSource(ManagedParameterHeuristic):
    def create_managed_param(
        self,
        request_contexts: Optional["RequestContexts"],
        annotation: type,
        original_kwargs: Dict[str, Any],
        param_name: str,
    ) -> Any:
        try:
            from sema4ai.data import DataSource  # type: ignore
        except Exception:
            return None

        use_class: Optional[Any] = None
        datasource_name = self._get_datasource_name(annotation)
        if datasource_name is not None:
            use_class = DataSource

        if use_class is not None:
            # Handle a datasource
            connection_value = original_kwargs.get(param_name)

            if connection_value is not None:
                # Gotten directly from the input.json (or command line)
                # as a value in the root.
                use_class.setup_connection_from_input_json(connection_value)
                return use_class.model_validate(datasource_name=datasource_name)

            elif request_contexts is not None:
                use_class.setup_connection_from_data_context(
                    request_contexts.data_context
                )
                return use_class.model_validate(datasource_name=datasource_name)

            else:
                use_class.setup_connection_from_env_vars()
                return use_class.model_validate(datasource_name=datasource_name)

        return None

    def _is_data_source_annotation(self, cls: type) -> bool:
        return self._get_datasource_name(cls) is not None

    def _get_type_and_first_arg(self, annotation: type) -> Optional[tuple[type, type]]:
        from typing import get_origin

        origin = get_origin(annotation)
        if origin is not None:
            args = typing.get_args(annotation)
            if len(args) > 0:
                return origin, args[0]
        return None

    def _get_datasource_name(self, cls: type) -> Optional[str]:
        """
        Args:
            cls: The class to check.

        Returns:
            The datasource name if the class is a DataSource, otherwise None.
            If the datasource is a union of DataSources, returns an empty string.
        """
        from typing import Annotated

        try:
            from sema4ai.data import DataSource, DataSourceSpec  # type: ignore
        except Exception:
            return None

        try:
            if issubclass(cls, DataSource):
                return ""  # i.e. DataSource is not bound to a namespace as it's not annotated.
        except TypeError:
            pass

        try:
            type_and_first_arg = self._get_type_and_first_arg(cls)
            if type_and_first_arg is not None:
                # Handle Annotated[DataSource, DataSourceSpec(...)]
                found_type, first_arg = type_and_first_arg
                try:
                    if issubclass(found_type, DataSource):
                        raise ValueError(
                            'DataSource should not be parametrized, it must be annotated with a DataSourceSpec. i.e.: `Annotated[DataSource, DataSourceSpec(name="datasource_name", engine="postgres")]`.\nFound: `{cls}`'
                        )
                except TypeError:
                    pass

                if found_type == Annotated:
                    if issubclass(first_arg, DataSource):
                        args = typing.get_args(cls)

                        if len(args) <= 1:
                            raise ValueError(
                                'DataSource must be always Annotated with DataSourceSpec. i.e.: `Annotated[DataSource, DataSourceSpec(name="datasource_name", engine="postgres")]`.\nFound: `{cls}`'
                            )

                        if len(args) > 2:
                            raise ValueError(
                                f'DataSource must just be Annotated with DataSourceSpec. i.e.: `Annotated[DataSource, DataSourceSpec(name="datasource_name", engine="postgres")]`.\nFound: `{cls}`'
                            )

                        datasource_spec = args[1]
                        if not isinstance(datasource_spec, DataSourceSpec):
                            if typing.get_origin(datasource_spec) == typing.Union:
                                return ""  # Union means that more than one DataSource is being queried (thus it's not bound to a namespace)

                            raise ValueError(
                                f'DataSource must be Annotated with DataSourceSpec. i.e.: `Annotated[DataSource, DataSourceSpec(name="datasource_name", engine="postgres")]`.\nFound: `{cls}`'
                            )
                        return datasource_spec.name

        except TypeError:
            pass

        return None

    def is_managed_param(self, param_name: str, *, param: inspect.Parameter) -> bool:
        return self._is_data_source_annotation(param.annotation)

    def get_managed_param_type_from_annotation(self, annotation: type) -> type | None:
        try:
            from sema4ai.data import DataSource  # type: ignore
        except Exception:
            return None

        if self._is_data_source_annotation(annotation):
            return DataSource

        return None


class ManagedParameters:
    """
    Default implementation of EPManagedParameters.

    The idea is that in the constructor it receives the parameter names and
    the actual instance mapped from the parameter name.
    """

    def __init__(self, param_name_to_instance: Dict[str, Any]):
        self._param_name_to_instance = param_name_to_instance
        self._heuristics: list[ManagedParameterHeuristic] = [
            ManagedParameterHeuristicRequest(),
            ManagedParameterHeuristicSecret(),
            ManagedParameterHeuristicOAuth2Secret(),
            ManagedParameterHeuristicDataSource(),
        ]

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
        if param_name in self._param_name_to_instance:
            return True

        if node is not None:
            assert (
                param is None
            ), "Either node or param is expected, but not both at the same time."

            for heuristic in self._heuristics:
                if heuristic.is_managed_node(param_name, node=node):
                    return True

            return False

        elif param is not None:
            if param.annotation:
                for heuristic in self._heuristics:
                    if heuristic.is_managed_param(param_name, param=param):
                        return True

        else:
            raise AssertionError("Either node or param must be passed.")

        return False

    def get_request_contexts(
        self,
        new_kwargs: Dict[str, Any],
        original_kwargs: Dict[str, Any],
    ) -> Optional["RequestContexts"]:
        """
        Returns the action context or None if the context wasn't really set.
        """
        from sema4ai.actions._action_context import RequestContexts
        from sema4ai.actions._request import Request

        request = new_kwargs.get("request")
        if request is None:
            req = original_kwargs.get("request")
            if req is not None:
                request = Request.model_validate(req)
        if request is None:
            request = self._param_name_to_instance.get("request")

        if request is None:
            return None

        request_contexts = RequestContexts(request)
        return request_contexts

    def inject_managed_params(
        self,
        sig: inspect.Signature,
        request_contexts: Optional["RequestContexts"],
        new_kwargs: Dict[str, Any],
        original_kwargs: Dict[str, Any],
    ) -> Dict[str, Any]:
        use_kwargs = new_kwargs.copy()

        for param in sig.parameters.values():
            if (
                param.name not in use_kwargs
                and param.name in self._param_name_to_instance
            ):
                use_kwargs[param.name] = self._param_name_to_instance[param.name]

            elif param.annotation:
                for heuristic in self._heuristics:
                    instance = heuristic.create_managed_param(
                        request_contexts, param.annotation, original_kwargs, param.name
                    )
                    if instance is not None:
                        use_kwargs[param.name] = instance
                        break

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
                for heuristic in self._heuristics:
                    param_type = heuristic.get_managed_param_type_from_annotation(
                        param.annotation
                    )
                    if param_type is not None:
                        return param_type

        else:
            assert node is not None

            for heuristic in self._heuristics:
                param_type = heuristic.get_managed_param_type_from_node(
                    param_name, node
                )
                if param_type is not None:
                    return param_type

        raise ValueError(f"Unable to get managed parameter type for parameter: {param}")

    def __typecheckself__(self) -> None:
        from sema4ai.actions._protocols import check_implements

        _: EPManagedParameters = check_implements(self)
