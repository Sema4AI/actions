import json
import typing
from logging import getLogger

from sema4ai.action_server._protocols import ArgumentsNamespace
from sema4ai.action_server.vendored_deps.termcolors import bold_red

log = getLogger(__name__)


def handle_login_command(args: ArgumentsNamespace) -> int:
    from sema4ai.action_server._ask_user import (
        ask_user_for_hostname,
        ask_user_to_provide_access_credentials,
    )
    from sema4ai.action_server._protocols import ArgumentsNamespaceCloudlogin
    from sema4ai.action_server._storage import store

    cloud_login_args: ArgumentsNamespaceCloudlogin = typing.cast(
        ArgumentsNamespaceCloudlogin, args
    )

    try:
        access_credentials = (
            cloud_login_args.access_credentials
            if cloud_login_args.access_credentials
            else ask_user_to_provide_access_credentials()
        )

        hostname = (
            cloud_login_args.hostname
            if cloud_login_args.hostname
            else ask_user_for_hostname()
        )

        store(access_credentials, hostname)

    except Exception as e:
        log.critical(
            bold_red(
                f"\nUnable to store credentials. Please fix the error below and retry.\n{e}",
            )
        )
        return 1

    return 0


def handle_verify_login_command(base_args: ArgumentsNamespace) -> int:
    from sema4ai.action_server._protocols import ArgumentsNamespaceCloudVerifyLogin
    from sema4ai.action_server._storage import get_access_credentials, get_hostname

    verify_login_args: ArgumentsNamespaceCloudVerifyLogin = typing.cast(
        ArgumentsNamespaceCloudVerifyLogin, base_args
    )

    try:
        access_credentials = get_access_credentials()
        hostname = get_hostname()

        if verify_login_args.json:
            print(
                json.dumps(
                    {
                        "logged_in": True if access_credentials else False,
                        "hostname": hostname,
                    }
                )
            )
        else:
            if access_credentials:
                log.info(f"User has logged in using hostname: {hostname}")
            else:
                log.info("Not logged in")
    except Exception as e:
        log.critical(
            bold_red(
                f"\nUnable to verify credentials. Please fix the error below and retry.\n{e}",
            )
        )
        return 1

    return 0


def handle_list_organizations_command(base_args: ArgumentsNamespace) -> int:
    from sema4ai.action_server._errors_action_server import ActionServerValidationError
    from sema4ai.action_server._protocols import ArgumentsNamespaceCloudOrganizations
    from sema4ai.action_server._storage import get_access_credentials, get_hostname
    from sema4ai.action_server.package._package_publish import list_organizations

    cloud_organizations_args: ArgumentsNamespaceCloudOrganizations = typing.cast(
        ArgumentsNamespaceCloudOrganizations, base_args
    )

    try:
        access_credentials = (
            cloud_organizations_args.access_credentials
            if cloud_organizations_args.access_credentials
            else get_access_credentials()
        )

        if not access_credentials:
            raise ActionServerValidationError(
                "Access credentials not stored nor provided"
            )

        hostname = (
            cloud_organizations_args.hostname
            if cloud_organizations_args.hostname
            else get_hostname()
        )

        organizations = list_organizations(access_credentials, hostname)

        if cloud_organizations_args.json:
            print(json.dumps([org.model_dump(mode="json") for org in organizations]))
        else:
            for organization in organizations:
                log.info(f"Organization: {organization}")

            if len(organizations) == 0:
                log.info("No organizations found")

    except ActionServerValidationError as e:
        log.critical(
            bold_red(
                f"\nUnable to find organizations. Please fix the error below and retry.\n{e}",
            )
        )
        return 1

    return 0


def handle_cloud_command(base_args: ArgumentsNamespace) -> int:
    from sema4ai.action_server._protocols import ArgumentsNamespaceCloud

    cloud_args: ArgumentsNamespaceCloud = typing.cast(
        ArgumentsNamespaceCloud, base_args
    )

    cloud_command = cloud_args.cloud_command

    match cloud_command:
        case "login":
            return handle_login_command(cloud_args)
        case "verify-login":
            return handle_verify_login_command(cloud_args)
        case "list-organizations":
            return handle_list_organizations_command(cloud_args)
        case _:
            log.critical(f"Invalid cloud command: {cloud_command}")
            return 1
