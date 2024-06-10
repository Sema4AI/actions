import json
import logging
import os
import typing

from ._protocols import (
    ArgumentsNamespace,
    ArgumentsNamespaceNew,
    ArgumentsNamespaceNewTemplates,
)

log = logging.getLogger(__name__)


def handle_new_project(directory: str = ".", template_name: str = "") -> int:
    """Creates a new project under the specified directory.

    Args:
        directory: The directory to create the project in.
        template_name: Template to use for the new project.
    """
    from sema4ai.action_server.vendored_deps.termcolors import bold_red, bold_yellow

    from ._new_project_helpers import (
        _ensure_latest_templates,
        _get_local_templates_metadata,
        _print_templates_list,
        _unpack_template,
    )

    try:
        _ensure_latest_templates()
    except Exception as e:
        log.warning(
            bold_yellow(
                bold_yellow("Refreshing templates failed, reason: \n")
                + f"{e}\n"
                + "Already cached templates will be used if available."
            )
        )

    try:
        metadata = _get_local_templates_metadata()

        if not metadata:
            raise RuntimeError("No cached or remote templates available.")

        if not directory:
            directory = input("Name of the project: ")
            if not directory:
                raise RuntimeError("The name of the project was not given.")

        if directory != ".":
            if os.path.exists(directory) and os.listdir(directory):
                raise RuntimeError(
                    f"The folder: {directory} already exists and is not empty."
                )

        if not template_name:
            _print_templates_list(metadata.templates)

            # @TODO:
            # Make a reusable version once https://github.com/Sema4AI/actions/pull/3 is merged.
            while True:
                try:
                    choice = int(input("Enter the number of your choice: "))
                    if 1 <= choice <= len(metadata.templates):
                        template_name = metadata.templates[choice - 1].name
                        break
                    else:
                        log.error(bold_red("Invalid number, please try again."))
                except ValueError:
                    log.error(bold_red("Invalid input, please enter a number."))

        _unpack_template(template_name, directory)

        log.info("✅ Project created")
        return 0
    except KeyboardInterrupt:
        log.debug("Operation cancelled")
        return 0
    except Exception as e:
        log.critical(bold_red(f"\nError creating the project: {e}"))
        log.info(
            "If the problem persists, the list of available templates can be found here: "
            "https://github.com/Sema4AI/actions/tree/master/templates"
        )

        return 1


def handle_list_templates(output_json: bool = False) -> int:
    """Lists availabe templates.

    Args:
        output_json: If true, the output will be formatted as JSON.
    """
    from sema4ai.action_server.vendored_deps.termcolors import bold_red

    from ._new_project_helpers import (
        ActionTemplate,
        _ensure_latest_templates,
        _get_local_templates_metadata,
        _print_templates_list,
    )

    try:
        _ensure_latest_templates()
        metadata = _get_local_templates_metadata()

        templates: list[ActionTemplate] = metadata.templates if metadata else []

        if output_json:
            print(
                json.dumps([template.model_dump(mode="json") for template in templates])
            )
        else:
            if len(templates) == 0:
                log.info("No templates available.")
            else:
                _print_templates_list(templates)

        return 0
    except Exception as e:
        log.critical(bold_red(f"\nError listing templates: {e}"))

        return 1


def handle_new_command(base_args: ArgumentsNamespace) -> int:
    new_args: ArgumentsNamespaceNew = typing.cast(ArgumentsNamespaceNew, base_args)

    if new_args.new_command == "list-templates":
        list_templates_args: ArgumentsNamespaceNewTemplates = typing.cast(
            ArgumentsNamespaceNewTemplates, base_args
        )

        return handle_list_templates(output_json=list_templates_args.json)

    return handle_new_project(directory=new_args.name, template_name=new_args.template)
