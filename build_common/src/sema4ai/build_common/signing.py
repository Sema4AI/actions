from pathlib import Path
from typing import Optional


class KeychainSetupError(Exception):
    """Raised when there is an error setting up the keychain for code signing."""


def setup_keychain(
    cert: Optional[str] = None,
    password: Optional[str] = None,
    keychain_name: str = "build.keychain",
) -> None:
    """
    Sets up the keychain for macOS code signing.

    This should be run before building if code signing is needed.
    """
    import base64
    import os
    import sys

    from .process_call import run

    if sys.platform != "darwin":
        return

    # Get certificate and password from environment if not provided
    signing_cert = cert or os.environ.get("MACOS_SIGNING_CERT")
    signing_password = password or os.environ.get("MACOS_SIGNING_CERT_PASSWORD")

    if not signing_cert:
        raise KeychainSetupError(
            "Unable to do keychain setup: certificate not provided (missing MACOS_SIGNING_CERT env variable)"
        )
    if not signing_password:
        raise KeychainSetupError(
            "Unable to do keychain setup: password not provided (missing MACOS_SIGNING_CERT_PASSWORD env variable)"
        )

    try:
        # Create and configure keychain
        run(["security", "create-keychain", "-p", signing_password, keychain_name])
        run(["security", "default-keychain", "-s", keychain_name])
        run(["security", "unlock-keychain", "-p", signing_password, keychain_name])

        # Import the certificate
        cert_path = Path("cert.p12")
        cert_path.write_bytes(base64.b64decode(signing_cert))
        try:
            run(["security", "import", str(cert_path), "-A", "-P", signing_password])
            run(
                [
                    "security",
                    "set-key-partition-list",
                    "-S",
                    "apple-tool:,apple:",
                    "-s",
                    "-k",
                    signing_password,
                    keychain_name,
                ],
            )
        finally:
            cert_path.unlink(missing_ok=True)
    except Exception as e:
        print(f"Error setting up keychain: {e}")
        # Clean up keychain if it exists
        try:
            run(["security", "delete-keychain", keychain_name])
        except Exception as cleanup_error:
            print(f"Warning: Failed to clean up keychain: {cleanup_error}")
        raise KeychainSetupError("Failed to set up keychain for code signing") from e


def sign_macos_executable(root_dir: Path, target_executable: Path) -> None:
    max_attempts = 3
    for i in range(max_attempts):
        try:
            _sign_macos_executable(root_dir, target_executable)
            break
        except Exception as e:
            print(f"Error signing executable: {e}")
            if i == max_attempts - 1:
                raise RuntimeError("Failed to sign executable after 3 attempts") from e


def _sign_macos_executable(root_dir: Path, target_executable: Path) -> None:
    """
    Sign the macOS executable.
    """

    from .process_call import run, run_and_capture_output

    # Sign the binary with the certificate
    print("Signing binary...")
    assert Path(
        "entitlements.mac.plist"
    ).exists(), f"Entitlements file not found in expected place: {Path('entitlements.mac.plist').absolute()}"
    print("======================= codesign output =============================")
    stdout, stderr = run_and_capture_output(
        [
            "codesign",
            "--verbose=4",
            "--entitlements=entitlements.mac.plist",
            "--deep",
            "--force",
            "--timestamp",
            "--options",
            "runtime",
            "--sign",
            get_from_env("MACOS_SIGNING_CERT_NAME"),
            str(target_executable),
        ]
    )
    print("stdout: ", stdout)
    print("stderr: ", stderr)

    # Verify the code signature and the contained executables
    print(
        "======================= codesign verify output ============================="
    )
    print("Verifying code signature...")
    stdout, stderr = run_and_capture_output(
        ["codesign", "--verify", "--verbose=2", "--deep", str(target_executable)]
    )
    print("stdout: ", stdout)
    print("stderr: ", stderr)

    # Display the signature information
    print(
        "======================= codesign display output ============================="
    )
    stdout, stderr = run_and_capture_output(
        ["codesign", "--verify", "--verbose=4", "--display", str(target_executable)]
    )
    print("stdout: ", stdout)
    print("stderr: ", stderr)

    # Notarize (zipped because notarization does not allow executable files)
    print("Submitting for notarization...")

    # Create temporary zip file
    import zipfile

    temp_zip = Path("temp_signing.zip")
    with zipfile.ZipFile(temp_zip, "w") as zf:
        zf.write(target_executable, target_executable.name)

    # Submit for notarization
    print("======================= notarytool output =============================")
    stdout, stderr = run_and_capture_output(
        [
            "xcrun",
            "notarytool",
            "submit",
            "--apple-id",
            get_from_env("APPLEID"),
            "--team-id",
            get_from_env("APPLETEAMID"),
            "--password",
            get_from_env("APPLEIDPASS"),
            str(temp_zip),
            "--wait",
        ]
    )
    print("stdout: ", stdout)
    print("stderr: ", stderr)

    if "status: Accepted" not in stdout:
        raise RuntimeError(
            "Notarization failed. Did not find `status: Accepted` in stdout (see above)."
        )

    print("======================= codesign -dvv output =============================")
    stdout, stderr = run_and_capture_output(
        ["codesign", "-dvv", str(target_executable)]
    )
    print("stdout: ", stdout)
    print("stderr: ", stderr)

    # Clean up
    temp_zip.unlink()

    print(f"Finished signing and notarizing executable: {target_executable}")


def get_from_env(key: str) -> str:
    import os

    value = os.environ.get(key)
    if not value:
        raise ValueError(f"Environment variable {key} is not set")
    return value


def sign_windows_executable(target_executable: Path) -> None:
    max_attempts = 3
    for i in range(max_attempts):
        try:
            _sign_windows_executable(target_executable)
            break
        except Exception as e:
            print(f"Error signing executable: {e}")
            if i == max_attempts - 1:
                raise RuntimeError("Failed to sign executable after 3 attempts") from e


installed_azure_sign_tool = False


def _sign_windows_executable(target_executable: Path) -> None:
    """
    Sign the Windows executable.
    """
    from .process_call import run

    global installed_azure_sign_tool

    # Install AzureSignTool if not already installed
    if not installed_azure_sign_tool:
        run(
            [
                "dotnet",
                "tool",
                "install",
                "--global",
                "AzureSignTool",
                "--version",
                "3.0.0",
            ]
        )
        installed_azure_sign_tool = True
    # Get environment variables
    vault_url = get_from_env("VAULT_URL")
    client_id = get_from_env("CLIENT_ID")
    tenant_id = get_from_env("TENANT_ID")
    client_secret = get_from_env("CLIENT_SECRET")
    certificate_name = get_from_env("CERTIFICATE_NAME")

    # Build command arguments
    run_in_powershell = [
        "azuresigntool",
        "sign",
        "--description-url",
        "https://sema4.ai",
        "--file-digest",
        "sha256",
        "--azure-key-vault-url",
        vault_url,
        "--azure-key-vault-client-id",
        client_id,
        "--azure-key-vault-tenant-id",
        tenant_id,
        "--azure-key-vault-client-secret",
        client_secret,
        "--azure-key-vault-certificate",
        certificate_name,
        "--timestamp-rfc3161",
        "http://timestamp.digicert.com",
        "--timestamp-digest",
        "sha256",
        str(target_executable),
    ]

    ps_command = " ".join(
        f'"{arg}"' if " " in arg else arg for arg in run_in_powershell
    )

    cmd = ["powershell", "-Command", ps_command]
    # Execute signing command
    run(cmd, shell=True)
