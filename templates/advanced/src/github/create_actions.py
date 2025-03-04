import requests
from sema4ai.actions import ActionError, Response, Secret, action

from .models import CreateIssueData, RepositoryInfo


@action(is_consequential=True)
def create_repository_issue(
    github_access_token: Secret,
    repository_info: RepositoryInfo,
    issue_data: CreateIssueData,
) -> Response[str]:
    """
    Creates a new issue in the specified repository.

    Args:
        github_access_token: Your private GitHub access token.
        repository_info: Information needed to locate the repository.
        issue_data: Information about the issue to create.
        limit: The maximum number of commits to return (max 100).

    Returns:
        A list of commit messages.
    """
    response = requests.post(
        f"https://api.github.com/repos/{repository_info.owner_id}/{repository_info.name}/issues",
        headers={
            "Authorization": "Bearer " + github_access_token.value,
            "Accept": "application/vnd.github.v3+json",
        },
        json={"title": issue_data.title, "body": issue_data.body},
    )

    if response.status_code != 201:
        raise ActionError(
            f"Error creating issue: {response.json().get('message', 'Unknown error')}"
        )

    return Response(result=f"Issue created: {response.json().get('html_url')}")
