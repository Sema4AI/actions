from pathlib import Path
from typing import List, Literal, Optional
from urllib.parse import urlparse

from ._package_publish_api import ConfiguredBaseModel


class Organization(ConfiguredBaseModel):
    id: str
    name: str


class ActionPackageEntityError(ConfiguredBaseModel):
    code: str
    message: str


class ActionPackageEntity(ConfiguredBaseModel):
    id: str
    name: str
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
    error: Optional[ActionPackageEntityError]


def list_organizations(access_credentials: str, hostname: str) -> List[Organization]:
    from sema4ai.action_server._errors_action_server import ActionServerValidationError
    from sema4ai.action_server.package._package_publish_api import (
        LIST_ORGANIZATIONS_URL,
        request_organizations,
    )

    url = LIST_ORGANIZATIONS_URL.substitute(HOSTNAME=hostname)

    organizations = []
    has_more = True

    while has_more:
        organizations_response = request_organizations(url, access_credentials)
        validated_organizations = [
            Organization.model_validate(org.model_dump())
            for org in organizations_response.data
        ]
        organizations += validated_organizations

        has_more = organizations_response.has_more

        if organizations_response.has_more:
            if not organizations_response.next:
                raise ActionServerValidationError(
                    f"Invalid response from list organization API, there should be more listings but the URL is not populated: {organizations_response}"
                )
            url = organizations_response.next

    return organizations


def upload_package(
    organization_id: str,
    package_path: Path,
    package_name: str,
    access_credentials: str,
    hostname: str,
) -> ActionPackageEntity:
    from sema4ai.action_server.package._package_publish_api import (
        create_package,
        get_upload_url,
        mark_upload_completed,
        upload_file,
    )

    package = create_package(
        organization_id, package_name, access_credentials, hostname
    )
    url = get_upload_url(organization_id, package.id, access_credentials, hostname)
    upload_file(url, package_path)
    s3_object_key = urlparse(url).path
    mark_upload_completed(
        organization_id, package.id, access_credentials, hostname, s3_object_key
    )
    return ActionPackageEntity.model_validate(package.model_dump(mode="json"))


def get_package_status(
    organization_id: str, package_id: str, access_credentials: str, hostname: str
) -> ActionPackageEntity:
    from sema4ai.action_server.package._package_publish_api import (
        request_package_status,
    )

    package = request_package_status(
        organization_id, package_id, access_credentials, hostname
    )

    return ActionPackageEntity.model_validate(package.model_dump(mode="json"))


def update_package_changelog(
    organization_id: str,
    package_id: str,
    access_credentials: str,
    hostname: str,
    changelog: str,
) -> ActionPackageEntity:
    from sema4ai.action_server.package._package_publish_api import (
        request_package_changelog_update,
    )

    package = request_package_changelog_update(
        organization_id, package_id, access_credentials, changelog, hostname
    )

    return ActionPackageEntity.model_validate(package.model_dump(mode="json"))
