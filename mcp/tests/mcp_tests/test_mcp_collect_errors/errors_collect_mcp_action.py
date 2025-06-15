from sema4ai.actions._secret import Secret

from sema4ai.mcp import resource


# Error: missing {foo} in the params.
@resource(uri="tickets://{foo}")
def get_foo() -> str:
    return "foo"


# Error: non-basic type.
@resource(uri="tickets://{foo}")
def get_foo2(foo: list[str]) -> str:
    return str(foo)


# Ok: managed params.
@resource(uri="tickets://{foo}/{untyped}")
def get_foo3(foo: str, untyped, secret: Secret) -> str:
    return foo
