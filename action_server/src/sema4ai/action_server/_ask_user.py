import typing
from getpass import getpass
from logging import getLogger

from sema4ai.action_server.package._package_publish import Organization

log = getLogger(__name__)


def ask_user_input_to_proceed(msg: str) -> bool:
    """
    Args:
        msg: The message to query user (should end with something as: "(y/n)\n").

    Returns:
        True to proceed and False otherwise.
    """
    try:
        while (c := input(msg).lower().strip()) not in ("y", "n"):
            continue
        if c == "n":
            return False
        # otherwise 'y' keep on going...
    except KeyboardInterrupt:
        return False

    return True


def ask_user_to_provide_access_credentials() -> str:
    """
    Returns:
        Control Room access credentials in valid form.
    """
    from sema4ai.action_server.vendored_deps.termcolors import bold_red

    while True:
        try:
            access_credentials = getpass("Enter Control Room access credentials: ")
            if access_credentials:
                _, _ = access_credentials.split(":")  # validate credentials form
                return access_credentials
            else:
                log.error(
                    bold_red(
                        "Invalid credentials, please try again with form: <keyid:secret>."
                    )
                )
        except (ValueError, EOFError):
            log.error(
                bold_red(
                    "Invalid access credentials, please try again with form: <keyid:secret>."
                )
            )


def ask_user_to_choose_organization(
    organizations: typing.List[Organization],
) -> str:
    """
    Args:
        organizations: List of organizations with name and ID.

    Returns:
        Organization ID.
    """
    from sema4ai.action_server.vendored_deps.termcolors import bold_red, colored

    for index, name in enumerate(
        [organization.name for organization in organizations], start=1
    ):
        log.info(colored(f" > {index}. {name}", "cyan"))

    while True:
        try:
            choise = int(input("Enter the number of your choice: "))
            if 1 <= choise <= len(organizations):
                return organizations[choise - 1].id
            else:
                log.error(bold_red("Invalid number, please try again."))
        except ValueError:
            log.error(bold_red("Invalid input, please enter a number."))


def ask_user_for_hostname() -> str:
    """
    Returns:
        Control Room hostname.
    """
    from urllib.parse import urlparse

    from sema4ai.action_server._storage import get_hostname
    from sema4ai.action_server.vendored_deps.termcolors import bold_red

    while True:
        default_hostname = get_hostname()

        try:
            hostname = input(f"Enter Control Room hostname ({default_hostname}): ")
            if not hostname:
                return default_hostname
            else:
                url = urlparse(hostname)
                if url.hostname:
                    return hostname
                else:
                    log.error(bold_red("Invalid input, please enter a valid hostname."))
        except ValueError:
            log.error(bold_red("Invalid input, please enter a valid hostname."))
