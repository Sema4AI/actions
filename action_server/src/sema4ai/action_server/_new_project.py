import logging
import os

log = logging.getLogger(__name__)


def create_new_project(directory: str = ".", template_name: str = "") -> int:
    """Creates a new project under the specified directory.

    Args:
        directory: The directory to create the project in.
        template_name: Template to use for the new project.
    """
    from sema4ai.action_server.vendored_deps.termcolors import (
        bold_red,
        bold_yellow,
        colored,
    )

    from ._new_project_helpers import (
        _ensure_latest_templates,
        _get_local_templates_metadata,
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
            for index, template in enumerate(metadata.templates, start=1):
                log.info(colored(f" > {index}. {template.description}", "cyan"))

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
