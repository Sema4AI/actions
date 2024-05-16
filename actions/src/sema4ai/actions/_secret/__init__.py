import typing
from typing import Generic, TypeVar

if typing.TYPE_CHECKING:
    from sema4ai.actions._action_context import ActionContext


def is_secret_subclass(cls: type) -> bool:
    try:
        return issubclass(cls, Secret)
    except TypeError:
        # This can happen if the first param is not a class
        # -- this is the case when using `Oauth2Secret[...]`
        return False


def is_oauth2_secret_subclass(cls: type) -> bool:
    from typing import get_origin

    try:
        # Case where we have the parametrized version of the class
        # i.e.: OAuth2Secret[Literal['google'], ...]
        origin = get_origin(cls)
        if origin is not None:
            if issubclass(origin, OAuth2Secret):
                return True
    except TypeError:
        pass

    try:
        return issubclass(cls, OAuth2Secret)
    except TypeError:
        # This can happen if the first param is not a class
        # -- this is the case when using `Oauth2Secret[...]`
        return False


class Secret:
    """
    This class should be used to receive secrets.

    The way to use it is by declaring a variable with the 'Secret' type
    in the @action.

    Example:

        ```
        from sema4ai.actions import action, Secret

        @action
        def my_action(password: Secret):
            login(password.value)
        ```

    Note: this class is abstract and is not meant to be instanced by clients.
        An instance can be created from one of the factory methods (`model_validate`
        or `from_action_context`).
    """

    @classmethod
    def model_validate(cls, value: str) -> "Secret":
        """
        Creates a secret given a string (expected when the user
        is passing the arguments using a json input).

        Args:
            value: The raw-text value to be used in the secret.

        Return: A Secret instance with the given value.

        Note: the model_validate method is used for compatibility with
            the pydantic API.
        """
        from sema4ai.actions._secret._secret import _RawSecret

        return _RawSecret(value)

    @classmethod
    def from_action_context(
        cls, action_context: "ActionContext", path: str
    ) -> "Secret":
        """
        Creates a secret given the action context (which may be encrypted
        in memory until the actual secret value is requested).

        Args:
            action_context: The action context which has the secret.

            path: The path inside of the action context for the secret data
            requested (Example: 'secrets/my_secret_name').

        Return: A Secret instance collected from the passed action context.
        """
        from sema4ai.actions._secret._secret import _SecretInActionContext

        return _SecretInActionContext(action_context, path)

    @property
    def value(self) -> str:
        raise NotImplementedError(
            "The Secret class is abstract and should not be directly used."
        )


ProviderT = TypeVar("ProviderT", bound=str)
ScopesT = TypeVar("ScopesT", bound=list)

JSONValue = dict[str, "JSONValue"] | list["JSONValue"] | str | int | float | bool | None


class OAuth2Secret(Generic[ProviderT, ScopesT]):
    """
    This class should be used to specify that OAuth2 secrets should be received.

    The way to use it is by declaring a variable with the 'OAuth2Secret' type
    in the @action along with its accepted provider and scope as Literals.

    Example:

        ```
        from sema4ai.actions import action, OAuth2Secret

        @action
        def add_column_to_spreadsheet(
            spreadsheet_name: str,
            google_oauth2_secret: OAuth2Secret[
                Literal["google"],
                list[
                    Literal[
                        "https://www.googleapis.com/auth/spreadsheets",
                    ]
                ],
            ]
        ):
            ...
            add_column(spreadsheet_name, google_oauth2_secret.access_token)
        ```

    Note: this class is abstract and is not meant to be instanced by clients.
        An instance can be created from one of the factory methods (`model_validate`
        or `from_action_context`).
    """

    @classmethod
    def model_validate(cls, value: dict) -> "OAuth2Secret":
        """
        Creates an OAuth2 Secret given a dict with the information
        (expected when the user is passing the arguments using a json input).

        Args:
            value: The dict containing the information to build the OAuth2 Secret.

        Return: An OAuth2Secret instance with the given value.

        Note: the model_validate method is used for compatibility with
            the pydantic API.
        """
        from sema4ai.actions._secret._oauth2_secret import _RawOauth2Secret

        if not isinstance(value, dict):
            raise TypeError(
                "To create an OAuth2Secret from input data, it's expected that a dict\n"
                "with 'provider', 'scopes' and 'access_token' values are passed.\n"
                f"Received: {value}({type(value)})"
            )

        return _RawOauth2Secret(value)

    @classmethod
    def from_action_context(
        cls, action_context: "ActionContext", path: str
    ) -> "OAuth2Secret":
        """
        Creates an OAuth2 Secret given the action context (which may be encrypted
        in memory until the actual secret value is requested).

        Args:
            action_context: The action context which has the secret.

            path: The path inside of the action context for the secret data
            requested (Example: 'secrets/my_secret_name').

        Return: An OAuth2Secret instance collected from the passed action context.
        """
        from sema4ai.actions._secret._oauth2_secret import _OAuth2SecretInActionContext

        return _OAuth2SecretInActionContext(action_context, path)

    @property
    def provider(self) -> str:
        raise NotImplementedError(
            "The OAuth2Secret class is abstract and should not be directly used."
        )

    @property
    def scopes(self) -> ScopesT:
        raise NotImplementedError(
            "The OAuth2Secret class is abstract and should not be directly used."
        )

    @property
    def access_token(self) -> str:
        raise NotImplementedError(
            "The OAuth2Secret class is abstract and should not be directly used."
        )

    @property
    def metadata(self) -> JSONValue:
        raise NotImplementedError(
            "The OAuth2Secret class is abstract and should not be directly used."
        )
