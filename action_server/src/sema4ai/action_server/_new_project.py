import logging
import os

log = logging.getLogger(__name__)


def create_new_project(directory: str = ".", template_name: str = "") -> None:
    """Creates a new project under the specified directory.

    Args:
        directory (str): The directory to create the project in.
        template_name (str): Temple to use for the new project.
    """
    from ._new_project_helpers import (
        _ensure_latest_templates,
        _get_local_templates_metadata,
        _unpack_template
    )
    from sema4ai.action_server.vendored_deps.termcolors import bold_red, colored
    
    try:
        _ensure_latest_templates()
    except Exception as e:
        log.warning(
            f"Refreshing templates failed, reason: {e}\n"
            "Already cached templates will be used if available."
        )

    try:
        metadata = _get_local_templates_metadata()
        
        if not metadata:
            raise RuntimeError("No templates available")

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
    except KeyboardInterrupt:
        log.debug("Operation cancelled")
    except Exception as e:
        log.critical(f"Error creating the project: {e}")
