import pytest

from sema4ai.action_server._selftest import ActionServerClient, ActionServerProcess

# Used in test so that the information is static (no random key or iv).
USE_STATIC_INFO = False


@pytest.mark.integration_test
def test_secrets_simple(
    action_server_process: ActionServerProcess, client: ActionServerClient, tmpdir
):
    from pathlib import Path

    from sema4ai.action_server._selftest import check_secrets_simple

    check_secrets_simple(Path(tmpdir), action_server_process, client, verbose=False)


@pytest.mark.integration_test
def test_secrets_encrypted(
    action_server_process: ActionServerProcess,
    client: ActionServerClient,
    datadir,
):
    import base64
    import json

    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    pack = datadir / "pack_encryption"

    keys = [AESGCM.generate_key(256), AESGCM.generate_key(256)]
    if USE_STATIC_INFO:
        keys = [b"a" * len(keys[0])]

    # ACTION_SERVER_DECRYPT_INFORMATION: Contains information on what is passed
    # encrypted.
    # Note: x-action-context is "special" in that it's a header that can be sent to
    # the action server over multiple parts (x-action-context-1, x-action-context-2, ...)
    # the result of all the parts will be decoded.
    #
    # ACTION_SERVER_DECRYPT_KEYS: The keys that can be used to decrypt (base-64
    # version of the actual bytes used to encrypt).
    env = dict(
        ACTION_SERVER_DECRYPT_INFORMATION=json.dumps(["header:x-action-context"]),
        ACTION_SERVER_DECRYPT_KEYS=json.dumps(
            [base64.b64encode(k).decode("ascii") for k in keys]
        ),
    )

    action_server_process.start(
        cwd=pack,
        actions_sync=True,
        db_file="server.db",
        lint=True,
        env=env,
    )

    from sema4ai.action_server._encryption import make_encrypted_data_envelope

    ctx_info = make_encrypted_data_envelope(
        keys[0], {"secrets": {"private_info": "my-secret-value"}}
    )

    found = client.post_get_str(
        "api/actions/pack-encryption/get-private/run",
        {"name": "Foo"},
        headers={"x-action-context": ctx_info},
    )
    assert "my-secret-value" == json.loads(found)


@pytest.mark.integration_test
def test_secrets_not_encrypted(
    action_server_process: ActionServerProcess,
    client: ActionServerClient,
    datadir,
):
    import json

    # Verify that things work if the X-Action-Context is not encrypted.
    from sema4ai.action_server._encryption import make_unencrypted_data_envelope

    pack = datadir / "pack_encryption"

    action_server_process.start(
        cwd=pack,
        actions_sync=True,
        db_file="server.db",
        lint=True,
    )

    secrets_in_base64 = make_unencrypted_data_envelope(
        {"secrets": {"private_info": "my-secret-value"}}
    )

    found = client.post_get_str(
        "api/actions/pack-encryption/get-private/run",
        {"name": "Foo"},
        headers={"x-action-context": secrets_in_base64},
    )
    assert "my-secret-value" == json.loads(found)


@pytest.mark.integration_test
def test_secrets_unencrypted_set_through_separate_post_request(
    action_server_process: ActionServerProcess,
    client: ActionServerClient,
    datadir,
):
    import base64
    import json

    pack = datadir / "pack_encryption"

    action_server_process.start(
        cwd=pack,
        actions_sync=True,
        db_file="server.db",
        lint=True,
    )

    data: str = json.dumps(
        {
            "secrets": {"private_info": "my-secret-value"},
            "scope": {"action-package": "pack_encryption"},
        }
    )
    ctx_info: str = base64.b64encode(data.encode("utf-8")).decode("ascii")

    found = client.post_get_str(
        "api/secrets",
        {"data": ctx_info},
    )
    assert json.loads(found) == "ok"

    found = client.post_get_str(
        "api/actions/pack-encryption/get-private/run",
        {"name": "Foo"},
    )
    assert "my-secret-value" == json.loads(found)

    data = json.dumps(
        {
            "secrets": {"private_info": "my-secret-value"},
            "scope": {"action-package": "bad-name"},
        }
    )
    ctx_info = base64.b64encode(data.encode("utf-8")).decode("ascii")

    found = client.post_error(
        "api/secrets",
        500,
        {"data": ctx_info},
    )


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "scenario",
    [
        "regular",
        "header-encrypted",
        "env-encrypted",
        "header-unencrypted",
        "env-unencrypted",
    ],
)
def test_secrets_encrypted_set_through_separate_post_request_env_var_or_header(
    action_server_process: ActionServerProcess,
    client: ActionServerClient,
    datadir,
    scenario,
):
    import base64
    import json

    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    from sema4ai.action_server._encryption import make_encrypted_data_envelope

    pack = datadir / "pack_encryption"

    keys = [AESGCM.generate_key(256), AESGCM.generate_key(256)]
    if USE_STATIC_INFO:
        keys = [b"a" * len(keys[0])]

    env = dict(
        ACTION_SERVER_DECRYPT_KEYS=json.dumps(
            [base64.b64encode(k).decode("ascii") for k in keys]
        ),
    )

    if scenario == "env-encrypted":
        env["PRIVATE_INFO"] = make_encrypted_data_envelope(keys[0], "my-secret-value")
    elif scenario == "env-unencrypted":
        env["PRIVATE_INFO"] = "my-secret-value"

    action_server_process.start(
        cwd=pack,
        actions_sync=True,
        db_file="server.db",
        lint=True,
        env=env,
    )

    if scenario == "regular":
        ctx_info: str = make_encrypted_data_envelope(
            keys[0],
            {
                "secrets": {"private_info": "my-secret-value"},
                "scope": {"action-package": "pack_encryption"},
            },
        )
        set_result = client.post_get_str(
            "api/secrets",
            {"data": ctx_info},
        )
        assert json.loads(set_result) == "ok"

        found = client.post_get_str(
            "api/actions/pack-encryption/get-private/run",
            {"name": "Foo"},
        )

    elif scenario == "header-unencrypted":
        found = client.post_get_str(
            "api/actions/pack-encryption/get-private/run",
            {"name": "Foo"},
            headers={"x-private-info": "my-secret-value"},
        )

    elif scenario == "header-encrypted":
        # Send as a header
        found = client.post_get_str(
            "api/actions/pack-encryption/get-private/run",
            {"name": "Foo"},
            headers={
                "x-private-info": make_encrypted_data_envelope(
                    keys[0], "my-secret-value"
                )
            },
        )
    elif scenario in ["env-encrypted", "env-unencrypted"]:
        # Sent in the env already.
        found = client.post_get_str(
            "api/actions/pack-encryption/get-private/run",
            {"name": "Foo"},
        )

    assert json.loads(found) == "my-secret-value"


@pytest.mark.integration_test
def test_secrets_encrypted_oauth2(
    action_server_process: ActionServerProcess,
    client: ActionServerClient,
    datadir,
):
    import base64
    import json

    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    pack = datadir / "pack_encryption_oauth2"

    keys = [AESGCM.generate_key(256), AESGCM.generate_key(256)]
    if USE_STATIC_INFO:
        keys = [b"a" * len(keys[0])]

    # ACTION_SERVER_DECRYPT_INFORMATION: Contains information on what is passed
    # encrypted.
    # Note: x-action-context is "special" in that it's a header that can be sent to
    # the action server over multiple parts (x-action-context-1, x-action-context-2, ...)
    # the result of all the parts will be decoded.
    #
    # ACTION_SERVER_DECRYPT_KEYS: The keys that can be used to decrypt (base-64
    # version of the actual bytes used to encrypt).
    env = dict(
        ACTION_SERVER_DECRYPT_INFORMATION=json.dumps(["header:x-action-context"]),
        ACTION_SERVER_DECRYPT_KEYS=json.dumps(
            [base64.b64encode(k).decode("ascii") for k in keys]
        ),
    )

    action_server_process.start(
        cwd=pack,
        actions_sync=True,
        db_file="server.db",
        lint=True,
        env=env,
    )

    from sema4ai.action_server._encryption import make_encrypted_data_envelope

    ctx_info = make_encrypted_data_envelope(
        keys[0],
        {
            "secrets": {
                "oauth2_secret": {
                    "provider": "google",
                    "scopes": ["https://scope:read", "https://scope:write"],
                    "access_token": "foobar",
                }
            }
        },
    )

    found = client.post_get_str(
        "api/actions/pack-encryption-oauth2/hello-greeting/run",
        {"name": "foo"},
        headers={"x-action-context": ctx_info},
    )
    assert "Hello foo. Access token: foobar" == json.loads(found)


@pytest.mark.integration_test
def test_secrets_oauth2_encrypted_set_through_separate_post_request(
    action_server_process: ActionServerProcess,
    client: ActionServerClient,
    datadir,
):
    import base64
    import json

    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    from sema4ai.action_server._encryption import make_encrypted_data_envelope

    pack = datadir / "pack_encryption_oauth2"

    keys = [AESGCM.generate_key(256), AESGCM.generate_key(256)]
    if USE_STATIC_INFO:
        keys = [b"a" * len(keys[0])]

    env = dict(
        ACTION_SERVER_DECRYPT_KEYS=json.dumps(
            [base64.b64encode(k).decode("ascii") for k in keys]
        ),
    )

    action_server_process.start(
        cwd=pack,
        actions_sync=True,
        db_file="server.db",
        lint=True,
        env=env,
    )

    ctx_info: str = make_encrypted_data_envelope(
        keys[0],
        {
            "secrets": {
                "oauth2_secret": {
                    "provider": "google",
                    "scopes": ["https://scope:read", "https://scope:write"],
                    "access_token": "foobar",
                }
            },
            "scope": {"action-package": "pack_encryption_oauth2"},
        },
    )

    found = client.post_get_str(
        "api/secrets",
        {"data": ctx_info},
    )
    assert json.loads(found) == "ok"

    found = client.post_get_str(
        "api/actions/pack-encryption-oauth2/hello-greeting/run",
        {"name": "foo"},
    )
    assert "Hello foo. Access token: foobar" == json.loads(found)
