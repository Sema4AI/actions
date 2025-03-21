import os


def make_error_message(message: str) -> str:
    return f"""Error: {message}.
Please set up the GitHub Actions environment variables in the failing step in the following format (to collect the version):
    - GITHUB_EVENT_NAME: ${{ github.event_name }}
    - GITHUB_REF_NAME: ${{ github.ref_name }}
    - GITHUB_PR_NUMBER: ${{ github.event.pull_request.number }}
"""


def get_version_from_github_actions() -> str:
    """
    Get the version and release channel from the GitHub Actions environment variables.

    # Original logic:
    #     version: >-
    #       ${{
    #         github.event_name == 'pull_request' && format('pr-{0}', github.event.pull_request.number) ||
    #         github.event_name == 'push' && startsWith(github.ref, 'refs/tags/') && github.ref_name ||
    #         github.event_name == 'push' && github.ref_name
    #       }}

    #     # Release channel logic remains the same
    #     release_channel: ${{ github.event_name == 'pull_request' && 'test' || (contains(github.ref_name, 'beta') && 'beta' || 'stable') }}

    A github action must pass as environment variables the following:
    - GITHUB_EVENT_NAME: ${{ github.event_name }}
    - GITHUB_REF_NAME: ${{ github.ref_name }}
    - GITHUB_PR_NUMBER: ${{ github.event.pull_request.number }}
    """
    from sema4ai.build_common.workflows import is_in_github_actions

    # Get environment variables from GitHub Actions
    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    ref_name = os.environ.get("GITHUB_REF_NAME", "")
    pr_number = os.environ.get("GITHUB_PR_NUMBER", "")

    # Version logic
    if not event_name:
        if not is_in_github_actions():
            raise RuntimeError(
                "Unable to automatically determine a version when not running in GitHub Actions. In this case, please specify --version."
            )

        raise ValueError(make_error_message("GITHUB_EVENT_NAME is not set."))
    if event_name == "pull_request":
        if not pr_number:
            raise ValueError(make_error_message("GITHUB_PR_NUMBER is not set"))
        version = f"pr-{pr_number}"
    elif event_name == "push":
        if not ref_name:
            raise ValueError(make_error_message("GITHUB_REF_NAME is not set"))
        version = ref_name

    return version


def get_release_channel_from_github_actions() -> str:
    from sema4ai.build_common.workflows import is_in_github_actions

    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    ref_name = os.environ.get("GITHUB_REF_NAME", "")

    if not event_name:
        if not is_in_github_actions():
            raise RuntimeError(
                "Unable to automatically determine a release channel when not running in GitHub Actions."
            )
        raise ValueError(make_error_message("GITHUB_EVENT_NAME is not set"))
    if not ref_name:
        raise ValueError(make_error_message("GITHUB_REF_NAME is not set"))

    # Release channel logic
    if event_name == "pull_request":
        release_channel = "test"
    elif "beta" in ref_name:
        release_channel = "beta"
    else:
        release_channel = "releases"

    return release_channel
