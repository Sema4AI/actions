"""
A simple AI Action template showcasing some more advanced configuration features

Please check out the base guidance on AI Actions in our main repository readme:
https://github.com/sema4ai/actions/blob/master/README.md

"""

import requests
from sema4ai.actions import ActionError, Response, Secret, action

from .models import RepositoryInfo


@action(is_consequential=False)
def get_repository_commits(
    github_access_token: Secret, repository_info: RepositoryInfo, limit: int = 10
) -> Response[list]:
    """
    Returns commit messages from given repository.

    Args:
        github_access_token: Your private GitHub access token.
        repository_info: Information needed to locate the repository.
        limit: The maximum number of commits to return (max 100).

    Returns:
        A list of commit messages.
    """
    if limit < 1 or limit > 100:
        raise ActionError("Limit must be between 1 and 100")

    response = requests.get(
        f"https://api.github.com/repos/{repository_info.owner_id}/{repository_info.name}/commits?per_page={limit}",
        headers={
            "Authorization": "Bearer " + github_access_token.value,
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )

    items = response.json()
    commit_messages = [item["commit"]["message"] for item in items]

    output = "\n".join(commit_messages)

    # Pretty print for log
    print(output)

    return Response(result=commit_messages)
