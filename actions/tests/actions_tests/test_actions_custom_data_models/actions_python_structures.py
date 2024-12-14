from sema4ai.actions import Response, action


@action
def action_python_structures(lst: list[int]) -> list[str]:
    return [str(item) for item in lst]


@action
def action_python_structure_response() -> Response[dict[str, int]]:
    return Response(result={"a": 1, "b": 2})
