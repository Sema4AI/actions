import os

# Used in test so that the information is static (no random key or iv).
USE_STATIC_INFO = False


def encrypt(key: bytes, plaintext: bytes) -> tuple[bytes, bytes, bytes]:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    # Generate a random 96-bit IV.
    iv = os.urandom(12)
    if USE_STATIC_INFO:
        iv = b"b" * len(iv)

    # Construct an AES-GCM Cipher object with the given key and a
    # randomly generated IV.
    encryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(iv),
    ).encryptor()

    # Encrypt the plaintext and get the associated ciphertext.
    # GCM does not require padding.
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()

    return (iv, ciphertext, encryptor.tag)


def test_secrets_encryption_raw() -> None:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    from sema4ai.actions._action_context import _decrypt

    # Example usage
    key = AESGCM.generate_key(bit_length=256)
    plaintext = b"Your secret message"

    iv, ciphertext, tag = encrypt(key, plaintext)
    assert _decrypt(key, iv, ciphertext, tag) == plaintext


def test_action_context_predefined() -> None:
    import base64
    import json

    from sema4ai.actions._action_context import _decrypt

    encoded_payload = "eyJhbGdvcml0aG0iOiJhZXMyNTYtZ2NtIiwiYXV0aC10YWciOiJEN09qRkZYUVVMd2JndE9WRmtvWmx3PT0iLCJjaXBoZXIiOiJVdFBIajFEMExMME5BQVpLaEdGQnZKQ2dvL1lCeUM4a3Z4QmwwY2pZbE1ubzArLytyR2VjNlJGdE9rOUtqQlBTIiwiaXYiOiIvQVF4b1VaNUdOMlg3ZllsIn0="
    encoded_key = "TkgAGaN1mNKMHnD1ss/yf5f9CC39nCyuQyrpYRBksW4="
    payload = json.loads(base64.b64decode(encoded_payload))
    key = base64.b64decode(encoded_key)

    cipher: bytes = base64.b64decode(payload["cipher"])
    iv: bytes = base64.b64decode(payload["iv"])
    auth: bytes = base64.b64decode(payload["auth-tag"])

    decrypted = _decrypt(key, iv, cipher, auth)

    secret_payload = json.loads(decrypted)
    assert secret_payload == {"secrets": {"secret_message": "my_secret_value"}}


def test_action_context() -> None:
    import base64
    import json

    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    from sema4ai.actions._action_context import ActionContext, _decrypt

    keys = [AESGCM.generate_key(bit_length=256), AESGCM.generate_key(bit_length=256)]
    if USE_STATIC_INFO:
        keys = [b"a" * len(keys[0]) for k in keys]

    env = dict(
        ACTION_SERVER_DECRYPT_INFORMATION=json.dumps(["header:x-action-context"]),
        ACTION_SERVER_DECRYPT_KEYS=json.dumps(
            [base64.b64encode(k).decode("ascii") for k in keys]
        ),
    )

    data: bytes = json.dumps({"secrets": {"private_info": "my-secret-value"}}).encode(
        "utf-8"
    )

    nonce, encrypted_data, tag = encrypt(keys[0], data)

    action_server_context = {
        "cipher": base64.b64encode(encrypted_data).decode("ascii"),
        "algorithm": "aes256-gcm",
        "iv": base64.b64encode(nonce).decode("ascii"),
        "auth-tag": base64.b64encode(tag).decode("ascii"),  # Always required.
    }

    assert _decrypt(keys[0], nonce, encrypted_data, tag) == data

    ctx_info: str = base64.b64encode(
        json.dumps(action_server_context).encode("utf-8")
    ).decode("ascii")

    ctx = ActionContext(ctx_info, env=env)
    assert ctx.value == {"secrets": {"private_info": "my-secret-value"}}
