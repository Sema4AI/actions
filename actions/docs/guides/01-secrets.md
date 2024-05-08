## Getting secrets in Actions

In `sema4ai-actions`, it's possible to receive secrets sent to the action server
as arguments in the `@action` (note that actually collecting the secrets is
responsibility of the client which will post a run to some action from the
action server).

The requisite for it to work is adding an argument and typing it with the `Secret` type.

### Example:

```
from robocorp.actions import action, Secret

@action
def my_action(my_secret: Secret):
    """
    Args:
        my_secret: This is the secret for the service used in my-action.
    """
    login(secret.value)

```

When developing, it's possible to specify the secret directly in the json input as a string
(to call it from VSCode for instance).

Note: backward-incompatible change on `sema4ai-actions 0.5.0`: secrets now need to 
be documented in the `Args`.