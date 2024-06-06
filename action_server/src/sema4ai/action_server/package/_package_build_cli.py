import json
import os
import sys
import time
import typing
from logging import getLogger
from pathlib import Path

from sema4ai.action_server._protocols import (
    ArgumentsNamespace,
    ArgumentsNamespacePackage,
    ArgumentsNamespacePackageBuild,
    ArgumentsNamespacePackageChangelog,
    ArgumentsNamespacePackageExtract,
    ArgumentsNamespacePackageMetadata,
    ArgumentsNamespacePackagePublish,
    ArgumentsNamespacePackagePush,
    ArgumentsNamespacePackageStatus,
    ArgumentsNamespacePackageUpdate,
)

log = getLogger(__name__)


PUBLISH_PACKAGE_POLL_TIME_S = 3

VALID_PUBLISH_STATUSES = ["completed", "published"]


def __wait_until_package_validated(
    organization_id: str,
    package_id: str,
    access_credentials: str,
    hostname: str,
) -> None:
    from sema4ai.action_server._errors_action_server import ActionServerValidationError
    from sema4ai.action_server.package._package_publish import (
        ActionPackageEntity,
        get_package_status,
    )

    need_line_change = False

    package = ActionPackageEntity(
        id="",
        name="",
        status="unknown",
        changes=None,
        error=None,
        url="",
        version=None,
    )
    while package.status not in VALID_PUBLISH_STATUSES:
        last_status = package

        package = get_package_status(
            organization_id,
            package_id,
            access_credentials,
            hostname,
        )

        if last_status.status == "unknown":
            log.info(f"Control Room link: {package.url}")

        if package.error:
            raise ActionServerValidationError(
                f"Failed to get package status: {package.error}"
            )

        if package.status == last_status.status:
            # Show user that we are polling for the status, so that user doesn't think the executable is stuck
            sys.stdout.write(".")
            sys.stdout.flush()
            need_line_change = True
        else:
            if need_line_change:
                log.info("")  # Add line change
            log.info(f"Publish status: {package.status}")
            need_line_change = False

        if package.status == "failed":
            raise ActionServerValidationError(f"Package validation failed: {package}")

        time.sleep(PUBLISH_PACKAGE_POLL_TIME_S)


def add_package_command(command_subparser, defaults):
    from sema4ai.action_server._cli_helpers import (
        add_data_args,
        add_json_output_args,
        add_login_args,
        add_organization_args,
        add_package_args,
        add_publish_args,
        add_push_package_args,
        add_verbose_args,
    )

    # Package handling
    package_parser = command_subparser.add_parser(
        "package",
        help="Utilities to manage the action package",
    )

    package_subparsers = package_parser.add_subparsers(dest="package_command")

    ### Update

    update_parser = package_subparsers.add_parser(
        "update",
        help="Updates the structure of a previous version of an action package to the latest version supported by the action server",
    )
    update_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="If passed, changes aren't actually done, they'll just be printed",
        default=False,
    )
    update_parser.add_argument(
        "--no-backup",
        action="store_true",
        help="If passed, file may be directly removed or overwritten, otherwise, a '.bak' file will be created prior to the operation",
        default=False,
    )
    add_verbose_args(update_parser, defaults)

    ### Build

    build_parser = package_subparsers.add_parser(
        "build",
        help="Creates a .zip with the contents of the action package so that it can be deployed",
    )
    build_parser.add_argument(
        "--input-dir",
        dest="input_dir",
        help="The source directory for the action package",
        default=".",
    )
    build_parser.add_argument(
        "--output-dir",
        dest="output_dir",
        help="The output file for saving the action package built file",
        default=".",
    )
    build_parser.add_argument(
        "--override",
        action="store_true",
        help="If passed if the target .zip is already present it'll be overridden without asking",
        default=False,
    )
    add_data_args(build_parser, defaults)
    add_verbose_args(build_parser, defaults)
    add_json_output_args(build_parser)

    ### Extract

    extract_parser = package_subparsers.add_parser(
        "extract",
        help="Extracts a .zip previously created with `action-server package build` to a folder",
    )
    extract_parser.add_argument(
        "--output-dir",
        dest="output_dir",
        help="The output directory for saving the action package zip",
        default=".",
    )
    extract_parser.add_argument(
        "--override",
        action="store_true",
        help="If set, the contents will be extracted to a non-empty folder without prompting",
        default=False,
    )
    add_verbose_args(extract_parser, defaults)
    extract_parser.add_argument(
        "filename", help="The .zip file that should be extracted"
    )

    ### Metadata

    extract_parser = package_subparsers.add_parser(
        "metadata",
        help="Collects metadata from the action package in the current cwd and prints it to stdout",
    )
    extract_parser.add_argument(
        "--input-dir",
        dest="input_dir",
        help="The source directory for the action package",
        default=".",
    )
    extract_parser.add_argument(
        "--output-file",
        dest="output_file",
        help="The output file for saving the metadata (default is writing to stdout)",
        default="-",
    )
    add_data_args(extract_parser, defaults)
    add_verbose_args(extract_parser, defaults)

    push_parser = package_subparsers.add_parser(
        "upload",
        help="Upload action package to the Control Room",
    )
    add_json_output_args(push_parser)
    add_push_package_args(push_parser)
    add_organization_args(push_parser)
    add_login_args(push_parser)
    add_verbose_args(push_parser, defaults)

    publish_status_parser = package_subparsers.add_parser(
        "status",
        help="Get package publishing status from Control Room",
    )
    add_package_args(publish_status_parser)
    add_json_output_args(publish_status_parser)
    add_organization_args(publish_status_parser)
    add_login_args(publish_status_parser)
    add_verbose_args(publish_status_parser, defaults)

    publish_parser = package_subparsers.add_parser(
        "publish",
        help="Push action package to Control Room and wait until it has been validated",
    )
    publish_parser.add_argument(
        "-o",
        "--organization-name",
        type=str,
        help="The Control Room organization name",
        required=False,
    )
    publish_parser.add_argument(
        "-p",
        "--package-path",
        type=str,
        help="Path to the built action package (.zip) file",
        required=True,
    )
    add_publish_args(publish_parser)
    add_login_args(publish_parser)
    add_verbose_args(publish_parser, defaults)

    changelog_parser = package_subparsers.add_parser(
        "set-changelog", help="Update action package changelog in Control Room"
    )
    add_package_args(changelog_parser)
    add_publish_args(changelog_parser)
    add_json_output_args(changelog_parser)
    add_organization_args(changelog_parser)
    add_login_args(changelog_parser)
    add_verbose_args(changelog_parser, defaults)


def handle_package_command(base_args: ArgumentsNamespace):
    from sema4ai.action_server._ask_user import ask_user_input_to_proceed
    from sema4ai.action_server._errors_action_server import ActionServerValidationError
    from sema4ai.action_server._storage import get_access_credentials, get_hostname
    from sema4ai.action_server.vendored_deps.termcolors import bold_red

    package_args: ArgumentsNamespacePackage = typing.cast(
        ArgumentsNamespacePackage, base_args
    )
    package_command = package_args.package_command
    if not package_command:
        log.critical("Command for package operation not specified.")
        return 1

    if package_command == "update":
        package_update_args: ArgumentsNamespacePackageUpdate = typing.cast(
            ArgumentsNamespacePackageUpdate, base_args
        )

        from sema4ai.action_server.vendored_deps.action_package_handling import (
            update_package,
        )

        update_package(
            Path(".").absolute(),
            dry_run=package_update_args.dry_run,
            backup=not package_update_args.no_backup,
        )
        return 0

    elif package_command == "build":
        from sema4ai.action_server.package._package_build import build_package

        package_build_args: ArgumentsNamespacePackageBuild = typing.cast(
            ArgumentsNamespacePackageBuild, base_args
        )

        # action-server package build --output-dir=<zipfile> --datadir=<directory> <source-directory>:
        try:
            result = build_package(
                input_dir=Path(package_build_args.input_dir).absolute(),
                output_dir=package_build_args.output_dir,
                datadir=package_build_args.datadir,
                override=package_build_args.override,
            )

            if package_build_args.json:
                print(json.dumps({"package_path": result.package_path}))
        except ActionServerValidationError as e:
            log.critical(
                bold_red(
                    f"\nUnable to build action package. Please fix the error below and retry.\n{e}",
                )
            )
            return 1
        return result.return_code

    elif package_command == "extract":
        package_extract_args: ArgumentsNamespacePackageExtract = typing.cast(
            ArgumentsNamespacePackageExtract, base_args
        )

        zip_filename = package_extract_args.filename
        if not os.path.exists(zip_filename):
            log.critical(f"The target zip: {zip_filename} does not exist.")
            return 1

        target_dir = package_extract_args.output_dir
        if not package_extract_args.override:
            if os.path.exists(target_dir):
                if len(os.listdir(target_dir)) > 1:
                    if os.path.realpath(target_dir) == os.path.realpath("."):
                        msg = "the current directory is not empty"
                    else:
                        msg = f"{target_dir} already exists and is not empty"

                    # Check if we should override.
                    if not ask_user_input_to_proceed(
                        f"It seems that {msg}. Are you sure you want to extract to it? (y/n)\n"
                    ):
                        return 1

        import zipfile

        log.debug(f"Extracting {zip_filename} to {target_dir}")

        with zipfile.ZipFile(zip_filename, "r") as zip_ref:
            zip_ref.extractall(target_dir)
        return 0

    elif package_command == "metadata":
        from sema4ai.action_server.package._package_metadata import (
            collect_package_metadata,
        )

        package_metadata_args: ArgumentsNamespacePackageMetadata = typing.cast(
            ArgumentsNamespacePackageBuild, base_args
        )

        # action-server package metadata --datadir=<directory>
        retcode = 0
        try:
            package_metadata_or_returncode: str | int = collect_package_metadata(
                package_dir=Path(package_metadata_args.input_dir).absolute(),
                datadir=package_metadata_args.datadir,
            )
            if isinstance(package_metadata_or_returncode, str):
                if (
                    package_metadata_args.output_file
                    and package_metadata_args.output_file != "-"
                ):
                    with open(package_metadata_args.output_file, "wb") as stream:
                        stream.write(package_metadata_or_returncode.encode("utf-8"))
                else:
                    print(package_metadata_or_returncode)
                    sys.stdout.flush()
            else:
                assert package_metadata_or_returncode != 0
                retcode = package_metadata_or_returncode

        except ActionServerValidationError as e:
            log.critical(
                bold_red(
                    f"\nUnable to collect package metadata. Please fix the error below and retry.\n{e}",
                )
            )
            retcode = 1
        return retcode

    elif package_command == "upload":
        from sema4ai.action_server.package._package_publish import upload_package
        from sema4ai.action_server.package._package_reader import read_package_name

        package_push_args: ArgumentsNamespacePackagePush = typing.cast(
            ArgumentsNamespacePackagePush, base_args
        )

        package_path = Path(package_push_args.package_path)

        try:
            if not package_path.exists():
                log.critical(
                    bold_red(f"\nFile does not exists: {package_path.resolve()}")
                )
                return 1

            access_credentials = (
                package_push_args.access_credentials
                if package_push_args.access_credentials
                else get_access_credentials()
            )

            if not access_credentials:
                raise ActionServerValidationError(
                    "Access credentials not stored nor provided"
                )

            hostname = (
                package_push_args.hostname
                if package_push_args.hostname
                else get_hostname()
            )

            package_name = read_package_name(package_path)

            log.info(
                f"Publishing package: {package_name} - {package_push_args.package_path}"
            )

            package = upload_package(
                package_push_args.organization_id,
                package_path,
                package_name,
                access_credentials,
                hostname,
            )

            if package_push_args.json:
                print(package.model_dump_json())
            else:
                log.info(f"Package published, ID is: {package.id}")

        except ActionServerValidationError as e:
            log.critical(
                bold_red(
                    f"\nUnable to upload package to Control Room. Please fix the error below and retry.\n{e}",
                )
            )
            return 1

        return 0

    elif package_command == "status":
        from sema4ai.action_server.package._package_publish import get_package_status

        package_status_args: ArgumentsNamespacePackageStatus = typing.cast(
            ArgumentsNamespacePackageStatus, base_args
        )

        try:
            access_credentials = (
                package_status_args.access_credentials
                if package_status_args.access_credentials
                else get_access_credentials()
            )

            if not access_credentials:
                raise ActionServerValidationError(
                    "Access credentials not stored nor provided"
                )

            hostname = (
                package_status_args.hostname
                if package_status_args.hostname
                else get_hostname()
            )

            log.info(
                f"Getting package publish status: {package_status_args.package_id}"
            )

            package = get_package_status(
                package_status_args.organization_id,
                package_status_args.package_id,
                access_credentials,
                hostname,
            )

            if package_status_args.json:
                print(package.model_dump_json())
            else:
                log.info(f"Control Room URL: {package.url}")
                log.info(f"Package publish status is: {package.status}")

        except ActionServerValidationError as e:
            log.critical(
                bold_red(
                    f"\nUnable to get package publish status. Please fix the error below and retry.\n{e}",
                )
            )
            return 1

        return 0

    elif package_command == "set-changelog":
        from sema4ai.action_server.package._package_publish import (
            update_package_changelog,
        )
        from sema4ai.action_server.package._package_reader import read_package_name

        package_changelog_args: ArgumentsNamespacePackageChangelog = typing.cast(
            ArgumentsNamespacePackageChangelog, base_args
        )

        try:
            access_credentials = (
                package_changelog_args.access_credentials
                if package_changelog_args.access_credentials
                else get_access_credentials()
            )

            if not access_credentials:
                raise ActionServerValidationError(
                    "Access credentials not stored nor provided"
                )

            hostname = (
                package_changelog_args.hostname
                if package_changelog_args.hostname
                else get_hostname()
            )

            log.info("Publishing changelog update")

            package = update_package_changelog(
                package_changelog_args.organization_id,
                package_changelog_args.package_id,
                access_credentials,
                hostname,
                package_changelog_args.change_log,
            )

            if package_changelog_args.json:
                print(package.model_dump_json())
            else:
                log.info(
                    f"Package {package_changelog_args.package_id} changelog updated to Control Room successfully"
                )

        except ActionServerValidationError as e:
            log.critical(
                bold_red(
                    f"\nUnable to publish package changelog update. Please fix the error below and retry.\n{e}",
                )
            )
            return 1

        return 0

    elif package_command == "publish":
        from sema4ai.action_server._ask_user import (
            ask_user_to_choose_organization,
            ask_user_to_provide_access_credentials,
        )
        from sema4ai.action_server.package._package_publish import (
            list_organizations,
            update_package_changelog,
            upload_package,
        )
        from sema4ai.action_server.package._package_reader import read_package_name

        package_publish_args: ArgumentsNamespacePackagePublish = typing.cast(
            ArgumentsNamespacePackagePublish, base_args
        )

        try:
            access_credentials = (
                package_publish_args.access_credentials
                if package_publish_args.access_credentials
                else get_access_credentials()
            )

            if not access_credentials:
                access_credentials = ask_user_to_provide_access_credentials()

            hostname = (
                package_publish_args.hostname
                if package_publish_args.hostname
                else get_hostname()
            )

            log.debug("Finding organizations...")
            organizations = list_organizations(access_credentials, hostname)
            for organization in organizations:
                log.debug(organization)

            expected_org_name = package_publish_args.organization_name
            if expected_org_name:
                organization_id = next(
                    (o.id for o in organizations if o.name == expected_org_name),
                    None,
                )
                if not organization_id:
                    raise ActionServerValidationError(
                        f"{expected_org_name} is not a valid organization"
                    )
            else:
                organization_id = ask_user_to_choose_organization(organizations)

            package_path = Path(package_publish_args.package_path)

            if not package_path.exists():
                raise ActionServerValidationError(
                    f"Invalid action package path: {package_path.resolve()}"
                )

            package_name = read_package_name(package_path)

            log.info(f"\nPublishing package: {package_name} - {package_path}")

            package = upload_package(
                organization_id,
                package_path,
                package_name,
                access_credentials,
                hostname,
            )

            log.info(
                "Package pushed to Control Room, waiting for package to been validate, this may take minutes..."
            )

            __wait_until_package_validated(
                organization_id, package.id, access_credentials, hostname
            )

            update_package_changelog(
                organization_id,
                package.id,
                access_credentials,
                hostname,
                package_publish_args.change_log,
            )

            log.info(f"Package {package_name} published to Control Room successfully")

        except KeyboardInterrupt:
            log.info("\nAction was cancelled")
            return 1

        except ActionServerValidationError as e:
            log.critical(
                bold_red(
                    f"\nUnable to publish package. Please fix the error below and retry.\n{e}",
                )
            )
            return 1

        return 0

    log.critical(f"Invalid package command: {package_command}")
    return 1
