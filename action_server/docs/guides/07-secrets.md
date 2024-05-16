## Secrets

**Important**: Requires `sema4ai-actions 0.3.1` onwards to work.

### Receiving a Secret

To receive secrets using actions, it's possible to add a parameter with a
'Secret' type so that it's automatically received by the action.

i.e.:

```
from sema4ai.actions import action, Secret

@action
def my_action(my_secret: Secret):
    login(my_secret.value)
```

### Passing Secrets (Development mode inside of VSCode)

In development mode a secret can be passed by using the `input.json` (which
is automatically created when an action is about to be run).

i.e.: in the case above a `my_secret` entry in the json will be automatically
used as the `my_secret.value`.

Example `input.json`:

```json
{
  "my_secret": "secret-value"
}
```

### Passing Secrets (Production mode)

In production secrets should be passed in the `X-Action-Context` header.

The expected format of that header is a base64(JSON.stringify(content))
where the content is a json object such as:

```
{
    "secrets": {
        "secret-name": "secret-value"
    }
}
```

In python code it'd be something as:

```python
payload = {
    'secrets': {'secret-name': 'secret-value'}
}
x_action_server_header = base64.b64encode(
    json.dumps(
        payload
    ).encode("utf-8")
).decode("ascii")
```

Note: the `X-Action-Context` header can also be passed encrypted with a
key shared with the action server in the environment variables.

In that case the `X-Action-Context` header contents should be something as:

```
base64({
    "cipher": base64(encrypted_data(JSON.stringify(content))),
    "algorithm": "aes256-gcm",
    "iv": base64(nonce),
    "auth-tag": base64(auth-tag),
})
```

In python code it'd be something as:

```python

payload = {
    'secrets': {'secret-name': 'secret-value'}
}
data: bytes = json.dumps(payload).encode("utf-8")

# def encrypt(...) implementation can be created using the cryptography library.

encrypted_data = encrypt(key, nonce, data, auth_tag)

action_server_context = {
    "cipher": base64.b64encode(encrypted_data).decode("ascii"),
    "algorithm": "aes256-gcm",
    "iv": base64.b64encode(nonce).decode("ascii"),
    "auth-tag": base64.b64encode(auth_tag).decode("ascii"),
}

x_action_server_header: str = base64.b64encode(
    json.dumps(action_server_context).encode("utf-8")
).decode("ascii")
```

The actual `key` used in the encryption should be set in `ACTION_SERVER_DECRYPT_KEYS`
in the environment variables such that it's a json with the keys in base64.

In python code:

```python
ACTION_SERVER_DECRYPT_KEYS=json.dumps(
    [base64.b64encode(k).decode("ascii") for k in keys]
)
```

Note: all the keys will be checked in order and the caller may use any of the
keys set to encrypt the data.

## OAuth2 Secrets

Starting with `Sema4.ai Action Server 0.9.0` and `sema4ai-actions 0.6.0`, OAuth2 secrets
may be passed to the action server (note: it's up to the client to actually manage
the user/tokens, the action server will just receive the `access_token` and related
information collected by the client).

### Receiving an OAuth2 Secret

To receive OAuth2 secrets using actions, it's possible to add a parameter with an
'OAuth2Secret' type (typed accordingly) so that it's automatically received by the action.

i.e.:

```python
from typing import Literal
from sema4ai.actions import OAuth2Secret, action

@action
def read_spreadsheet(
    name: str,
    google_secret: OAuth2Secret[
        Literal["google"],
        list[
            Literal[
                "https://www.googleapis.com/auth/spreadsheets.readonly",
                "https://www.googleapis.com/auth/drive.readonly",
            ]
        ],
    ],
) -> str:
    return do_read_spreadsheet(name, google_secret.access_token)
```

### Passing Secrets

The action server will receive an OAuth2 secret in the same way that a regular secret
is passed, the only difference is that the initial payload is different. Instead
of a payload where the value is just a string, the payload is a dict with the following
keys: `"provider", "scopes", "access_token", "metadata"`.

i.e.: While the payload for regular secrets is:

```json
{
  "my_secret": "secret-value"
}
```

The payload for OAuth2 secrets is:

```json
{
  "my_oauth2_secret": {
    "provider": "google",
    "scopes": ["scope1", "scope2"],
    "access_token": "<this-is-the-access-token>",
    "metadata": { "any": "additional info" }
  }
}
```
