
# Structuring a simple action.

When doing a small action which will not have any code reused anywhere, it's
usually fine to create an `action.py` with a few decorated `@action`s and a `package.yaml`.

Example:

```
/action.py
/package.yaml
```

`action.py` contents:

```python
from sema4ai.actions import action


@action
def greet(name: str, title: str = "Mr.") -> str:
    """
    Greet someone.

    Args:
        name: The name of the person to greet.
        title: The title to be used.

    Returns:
        The greeting to be shown.
    """

    return f"Hello {title} {name}!"

```


# Structuring a bigger action.

When an action starts to grow or code inside the action can be reused
in other places a bit of structure is usually welcome. To do that there are
a few things to keep in mind:

1. Actions are searched recursively in any file that matches the `*action*.py` pattern.
2. Actions can be found inside a python package.

Given that, an action with a bit more structure could be created as:

```
/package.yaml
/greeter_action
    /__init__.py
    /greet_one_person_action.py
    /greet_multiple_people_action.py
    /_common.py
```

The `/greeter_action/greet_one_person_action.py` and `/greeter_action/greet_multiple_people_action.py`
modules would be loaded to search for `@action` and those could import other things
from the package.

Note: in general it's not recommended to have multiple `.py` modules in the 
root directory of the action package (as that raises the possibility of having
clashes with other standard library modules). 

# Using `Response` and `ActionError`

`sema4ai-actions 0.8.0` introduced 2 new classes: 
`sema4ai.actions.Response` and `sema4ai.actions.ActionError`.

These classes can be used to have more control of what's returned to an LLM and 
can be used to give error messages that are more meaningful to the LLM.

Without using these classes, an `@action` would usually just provide the direct
value and any exception raised would be converted to an http error with a `500`
error response, yet, when a `Response[T]` is set as the return type for an `@action`, only
internal errors from the action server would return a `500` response and any other 
error that happens inside the `@action` would actually return a response 
in a structure returning either a `result` or an `error` set.

The example below shows an example and explains what is expected to happen in different
circumstances.


```python
from sema4ai.actions import ActionError, Response, action


@action
def greet(name: str, title: str = "Mr.") -> Response[str]:
    """
    Greet someone.

    Args:
        name: The name of the person to greet.
        title: The title to be used.

    Returns:
        A response with the greeting result or an error.
    """
    if title not in ("Mr.", "Mrs."):
        # A regular return which signals an error condition with a custom message.
        return Response(
            error=f"Invalid title: {title}. It's only possible to greet with `Mr.` or `Mrs.`"
        )

    if not name:
        # This has the same effect as 
        # `return Response(error="The name of the person to greet is empty.")`.
        raise ActionError("The name of the person to greet is empty.")

    list_of_people_that_can_be_greeted = [...]
    if name in list_of_people_that_can_be_greeted:
        # This has the same effect as a `return Response(error="Unexpected error (ValueError)")`.
        raise ValueError("This person is not in the list of greetable people.")

    # A successful result making a greeting.
    return Response(result=f"Hello {title} {name}!")
```