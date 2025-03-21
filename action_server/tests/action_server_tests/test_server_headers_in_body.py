import pytest

from sema4ai.action_server._selftest import ActionServerClient, ActionServerProcess


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "scenario",
    [
        "context-in-body",
        "regular",
    ],
)
def test_server_headers_in_body(
    action_server_process: ActionServerProcess,
    client: ActionServerClient,
    datadir,
    scenario: str,
):
    import base64
    import json

    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    key = AESGCM.generate_key(256)

    from sema4ai.action_server._encryption import make_encrypted_data_envelope

    env = dict(
        ACTION_SERVER_DECRYPT_KEYS=json.dumps([base64.b64encode(key).decode("ascii")]),
    )

    action_server_process.start(
        actions_sync=True,
        cwd=datadir / "my_package",
        db_file="server.db",
        reuse_processes=True,
        min_processes=1,
        max_processes=1,
        env=env,
    )
    ctx_info = make_encrypted_data_envelope(
        key, {"secrets": {"private_info": "my-secret-value"}}
    )

    if scenario == "context-in-body":
        args = [{"body": {"arg": "10"}, "x-action-context": ctx_info}]
        kwargs: dict = dict(headers={"x-action-invocation-context": json.dumps({})})
    elif scenario == "regular":
        args = [{"arg": "10"}]
        kwargs = dict(headers={"x-action-context": ctx_info})
    else:
        raise ValueError(f"Unknown scenario: {scenario}")

    found = client.post_get_str(
        "api/actions/my-package/my-action/run",
        *args,
        **kwargs,
    )
    print(found)
    assert found == '"Ok"'
