import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from logging import getLogger
from pathlib import Path
from string import Template
from typing import List, Literal, Optional, Tuple
from urllib.parse import ParseResult, urlparse, urlsplit, urlunsplit

import requests
from pydantic import BaseModel, ConfigDict, ValidationError

from sema4ai.action_server._errors_action_server import ActionServerValidationError

log = getLogger(__name__)

CREATE_PACKAGE_URL = Template(
    "$HOSTNAME/api/v1/organizations/$ORG_ID/action-package-uploads"
)

UPLOAD_PACKAGE_URL = Template(
    "$HOSTNAME/api/v1/organizations/$ORG_ID/action-package-uploads/$ACTION_PACKAGE_ID"
)

GET_PACKAGE_URL = Template(
    "$HOSTNAME/api/v1/organizations/$ORG_ID/action-package-uploads/$ACTION_PACKAGE_ID"
)

LIST_ORGANIZATIONS_URL = Template("$HOSTNAME/api/v1/organizations")

UPLOAD_COMPLETED_URL = Template(
    "$HOSTNAME/api/v1/organizations/$ORG_ID/action-package-uploads/$ACTION_PACKAGE_ID/upload-complete"
)

UPDATE_CHANGELOG_URL = Template(
    "$HOSTNAME/api/v1/organizations/$ORG_ID/action-package-uploads/$ACTION_PACKAGE_ID/publish"
)


class ConfiguredBaseModel(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )


class OrganizationResponseData(ConfiguredBaseModel):
    id: str
    name: str


class OrganizationsResponse(ConfiguredBaseModel):
    data: List[OrganizationResponseData]
    has_more: bool
    next: Optional[str]


class ActionPackageEntityResponsePublic(ConfiguredBaseModel):
    name: str
    # verified: bool # dropped from spec?
    # category: str # dropped from spec?


class ActionPackageEntityResponseError(ConfiguredBaseModel):
    code: str
    message: str


class ActionPackageEntityResponse(ConfiguredBaseModel):
    id: str
    name: str
    # public: Optional[ActionPackageEntityResponsePublic] # dropped from spec?
    url: str
    version: Optional[str]
    changes: Optional[str]
    status: (
        Literal["unknown"]
        | Literal["pending"]
        | Literal["validating"]
        | Literal["failed"]
        | Literal["completed"]
        | Literal["published"]
    )
    error: Optional[ActionPackageEntityResponseError]


class PackageUploadResponse(ConfiguredBaseModel):
    type: str
    upload_url: str


@dataclass
class HMACPayload:
    body: str
    path: str
    timestamp: str
    http_method: str
    content_type: str


def parse_url(url: str) -> ParseResult:
    parts = urlsplit(url)
    normalized_path = "/".join(part for part in parts.path.split("/") if part)
    fixed = urlunsplit(
        (parts.scheme, parts.netloc, normalized_path, parts.query, parts.fragment)
    )
    return urlparse(fixed)


def split_access_credentials(access_credentials: str) -> Tuple[str, str]:
    try:
        key_id, secret = access_credentials.split(":")
        return key_id, secret
    except ValueError as e:
        raise ActionServerValidationError(
            f"Invalid access credentials, should be in format: keyid:secret\n{e}"
        )


def calculate_hmac(payload: HMACPayload, secret: str) -> str:
    # Create SHA-256 hash of the body
    body = payload.body.encode("utf-8")
    body_hash = base64.b64encode(hashlib.sha256(body).digest()).decode("utf-8")

    # Prepare data string
    data = "\n".join(
        [
            payload.http_method,
            payload.path,
            payload.content_type,
            payload.timestamp,
            body_hash,
        ]
    )

    # Create HMAC
    return base64.b64encode(
        hmac.new(secret.encode("utf-8"), data.encode("utf-8"), hashlib.sha256).digest()
    ).decode("utf-8")


def get_nonce() -> str:
    return str(int(time.time() * 1000))


def create_package(
    organization_id: str, name: str, access_credentials: str, hostname: str
) -> ActionPackageEntityResponse:
    from sema4ai.action_server._session import session

    log.debug(f"Creating action package entity: {name}")

    url = parse_url(
        CREATE_PACKAGE_URL.substitute(HOSTNAME=hostname, ORG_ID=organization_id)
    )
    api_key_id, secret = split_access_credentials(access_credentials)
    nonce = get_nonce()
    data = json.dumps({"name": name}, separators=(",", ":"))
    content_type = "application/json"

    hmac_payload = HMACPayload(
        body=data,
        path=url.path,
        content_type=content_type,
        http_method="POST",
        timestamp=nonce,
    )
    hmac_value = calculate_hmac(hmac_payload, secret)

    headers = {
        "Content-Type": content_type,
        "authorization-timestamp": nonce,
        "Authorization": f"Sema4UserHMAC {api_key_id} {hmac_value}",
    }

    try:
        r = session.post(url.geturl(), data=data, headers=headers)
    except requests.exceptions.ConnectionError as e:
        raise ActionServerValidationError(f"Failed to call Controm Room API: {e}")

    if r.ok:
        log.debug("Action package entity created successfully")
    else:
        raise ActionServerValidationError(f"{r.status_code} - {r.text}")

    content = r.json()

    try:
        validated_content = ActionPackageEntityResponse.model_validate(content)
    except ValidationError as e:
        raise ActionServerValidationError(f"Failed to parse response: {e}")

    return validated_content


def get_upload_url(
    organization_id: str, package_id: str, access_credentials: str, hostname: str
) -> str:
    from sema4ai.action_server._session import session

    log.debug(f"Getting upload URL for: {package_id}")

    url = parse_url(
        UPLOAD_PACKAGE_URL.substitute(
            HOSTNAME=hostname, ORG_ID=organization_id, ACTION_PACKAGE_ID=package_id
        )
    )
    api_key_id, secret = split_access_credentials(access_credentials)
    nonce = get_nonce()
    data = json.dumps({"type": "zip"}, separators=(",", ":"))
    content_type = "application/json"

    hmac_payload = HMACPayload(
        body=data,
        path=url.path,
        timestamp=nonce,
        content_type=content_type,
        http_method="POST",
    )
    hmac_value = calculate_hmac(hmac_payload, secret)

    headers = {
        "Content-Type": content_type,
        "authorization-timestamp": nonce,
        "Authorization": f"Sema4UserHMAC {api_key_id} {hmac_value}",
    }

    try:
        r = session.post(url.geturl(), data=data, headers=headers)
    except requests.exceptions.ConnectionError as e:
        raise ActionServerValidationError(f"Failed to call Controm Room API: {e}")

    if r.ok:
        log.debug("Upload URL received successfully")
    else:
        raise ActionServerValidationError(f"{r.status_code} - {r.text}")

    content = r.json()

    try:
        validated_content = PackageUploadResponse.model_validate(content)
    except ValidationError as e:
        raise ActionServerValidationError(f"Failed to parse response: {e}")

    return validated_content.upload_url


def upload_file(url: str, pkg_path: Path) -> None:
    from sema4ai.action_server._session import session

    log.debug(f"Uploading file: {pkg_path.resolve()}")

    with open(pkg_path, "rb") as f:
        r = session.put(url, data=f)

        if r.ok:
            log.debug("File uploaded successfully")
        else:
            raise ActionServerValidationError(
                f"Failed to upload file: {r.status_code} - {r.text}"
            )


def request_package_status(
    organization_id: str, package_id: str, access_credentials: str, hostname: str
) -> ActionPackageEntityResponse:
    from sema4ai.action_server._session import session

    log.debug(f"Getting action package publish status: {package_id}")

    url = parse_url(
        GET_PACKAGE_URL.substitute(
            HOSTNAME=hostname, ORG_ID=organization_id, ACTION_PACKAGE_ID=package_id
        )
    )
    api_key_id, secret = split_access_credentials(access_credentials)
    nonce = get_nonce()
    data = json.dumps({}, separators=(",", ":"))
    content_type = "application/json"

    hmac_payload = HMACPayload(
        body=data,
        path=url.path,
        content_type=content_type,
        http_method="GET",
        timestamp=nonce,
    )
    hmac_value = calculate_hmac(hmac_payload, secret)

    headers = {
        "Content-Type": content_type,
        "authorization-timestamp": nonce,
        "Authorization": f"Sema4UserHMAC {api_key_id} {hmac_value}",
    }

    try:
        r = session.get(url.geturl(), headers=headers)
    except requests.exceptions.ConnectionError as e:
        raise ActionServerValidationError(f"Failed to call Controm Room API: {e}")

    if r.ok:
        log.debug("Action package publish status successfully received")
    else:
        raise ActionServerValidationError(f"{r.status_code} - {r.text}")

    content = r.json()

    try:
        validated_content = ActionPackageEntityResponse.model_validate(content)
    except ValidationError as e:
        raise ActionServerValidationError(f"Failed to parse response: {e}")

    return validated_content


def request_organizations(url: str, access_credentials: str) -> OrganizationsResponse:
    from sema4ai.action_server._session import session

    parsed_url = parse_url(url)

    api_key_id, secret = split_access_credentials(access_credentials)
    nonce = get_nonce()
    data = json.dumps({}, separators=(",", ":"))
    content_type = "application/json"

    hmac_payload = HMACPayload(
        body=data,
        path=parsed_url.path,
        content_type=content_type,
        http_method="GET",
        timestamp=nonce,
    )
    hmac_value = calculate_hmac(hmac_payload, secret)

    headers = {
        "Content-Type": content_type,
        "authorization-timestamp": nonce,
        "Authorization": f"Sema4UserHMAC {api_key_id} {hmac_value}",
    }

    try:
        r = session.get(parsed_url.geturl(), headers=headers)
    except requests.exceptions.ConnectionError as e:
        raise ActionServerValidationError(f"Failed to call Controm Room API: {e}")

    if r.ok:
        log.debug("Organizations list successfully received")
    else:
        raise ActionServerValidationError(f"{r.status_code} - {r.text}")

    content = r.json()

    try:
        validated_content = OrganizationsResponse.model_validate(content)
    except ValidationError as e:
        raise ActionServerValidationError(f"Failed to parse response: {e}")

    return validated_content


def mark_upload_completed(
    organization_id: str,
    package_id: str,
    access_credentials: str,
    hostname: str,
    s3_object_key: str,
) -> None:
    from sema4ai.action_server._session import session

    url = parse_url(
        UPLOAD_COMPLETED_URL.substitute(
            HOSTNAME=hostname, ORG_ID=organization_id, ACTION_PACKAGE_ID=package_id
        )
    )

    api_key_id, secret = split_access_credentials(access_credentials)
    nonce = get_nonce()
    data = json.dumps({"s3_object_key": s3_object_key}, separators=(",", ":"))
    content_type = "application/json"

    hmac_payload = HMACPayload(
        body=data,
        path=url.path,
        content_type=content_type,
        http_method="POST",
        timestamp=nonce,
    )
    hmac_value = calculate_hmac(hmac_payload, secret)

    headers = {
        "Content-Type": content_type,
        "authorization-timestamp": nonce,
        "Authorization": f"Sema4UserHMAC {api_key_id} {hmac_value}",
    }

    try:
        r = session.post(url.geturl(), data=data, headers=headers)
    except requests.exceptions.ConnectionError as e:
        raise ActionServerValidationError(f"Failed to call Controm Room API: {e}")

    if r.ok:
        log.debug("Package push marked as completed")
    else:
        raise ActionServerValidationError(f"{r.status_code} - {r.text}")


def request_package_changelog_update(
    organization_id: str,
    package_id: str,
    access_credentials: str,
    changelog: str,
    hostname: str,
) -> ActionPackageEntityResponse:
    from sema4ai.action_server._session import session

    url = parse_url(
        UPDATE_CHANGELOG_URL.substitute(
            HOSTNAME=hostname, ORG_ID=organization_id, ACTION_PACKAGE_ID=package_id
        )
    )

    api_key_id, secret = split_access_credentials(access_credentials)
    nonce = get_nonce()
    data = json.dumps({"changes": changelog}, separators=(",", ":"))
    content_type = "application/json"

    hmac_payload = HMACPayload(
        body=data,
        path=url.path,
        content_type=content_type,
        http_method="POST",
        timestamp=nonce,
    )
    hmac_value = calculate_hmac(hmac_payload, secret)

    headers = {
        "Content-Type": content_type,
        "authorization-timestamp": nonce,
        "Authorization": f"Sema4UserHMAC {api_key_id} {hmac_value}",
    }

    try:
        r = session.post(url.geturl(), data=data, headers=headers)
    except requests.exceptions.ConnectionError as e:
        raise ActionServerValidationError(f"Failed to call Controm Room API: {e}")

    if r.ok:
        log.debug("Package changelog updated successfully")
    else:
        raise ActionServerValidationError(f"{r.status_code} - {r.text}")

    content = r.json()

    try:
        validated_content = ActionPackageEntityResponse.model_validate(content)
    except ValidationError as e:
        raise ActionServerValidationError(f"Failed to parse response: {e}")

    return validated_content
