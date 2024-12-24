# Running Actions Asynchronously

## Usual (synchronous) execution

By default a call to run an action works synchronously
i.e.: the client has to wait for the action to finish before receiving a response.

Example:

Given an action package `greeter` with an action `greet` that returns a string:

```python
@action
def greet(name: str) -> str:
    return f"Hello {name}!"
```

A call to `/api/actions/greeter/greet/run` will wait for the action to finish and then
return the result of the action (as a json in the response body) and the `x-action-server-run-id`
header with the ID of the action run (which can be later used to get more information
from the action server regarding the run).

This works well for cases where the action is expected to finish quickly.

## Asynchronous execution

On the other hand, some actions can take a long time to finish. In this case,
the client can request an asynchronous execution of the action.

To run an action asynchronously, the client needs to set the following headers:

- `x-actions-async-timeout`: The maximum time to wait for the action to finish (in seconds).
- `x-actions-async-callback`: The URL to call when the action is finished.
- `x-actions-request-id`: The ID of the request. In case the return of the action
  is not received by the client, the client can use this ID to get the run id
  of the action (which may then be used to get more information from the action
  server regarding the run).

If the action is finished before the timeout, the client will receive a response
as usual (with the result of the action in the response body and the `x-action-server-run-id`
header).

If the action is not finished before the timeout, the client will receive a response (with a 200 status code)
as usual, but with the following headers:

- `x-action-async-completion: 1`: This header indicates that the action is not finished yet and is
  still running in the background.
- `x-action-server-run-id`: The ID of the action run.

The client can later use the `x-action-server-run-id` to get more information from the action server
regarding the run (to cancel the run, to get the result, get the current status, etc.).

Also, if the `x-actions-async-callback` header is set, the action server will call the callback URL
with the result of the action when it is finished.
