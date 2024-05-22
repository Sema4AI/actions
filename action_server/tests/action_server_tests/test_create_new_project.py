import os
import shutil
from unittest import mock

import requests

import sema4ai.action_server._new_project


@mock.patch(
    "sema4ai.action_server._new_project_helpers.requests.get",
    side_effect=requests.exceptions.HTTPError,
)
@mock.patch(
    "sema4ai.action_server._new_project.log.critical",
    wraps=sema4ai.action_server._new_project.log.critical,
)
@mock.patch(
    "sema4ai.action_server._new_project.log.warning",
    wraps=sema4ai.action_server._new_project.log.warning,
)
def test_create_new_project_download_metadata_fail(
    log_warning_mock: mock.MagicMock, log_critical_mock: mock.MagicMock, _, tmpdir
) -> None:
    from sema4ai.action_server._new_project import handle_new_project

    templates_path = tmpdir / "action-templates"
    project_path = tmpdir / "my_project"

    with mock.patch(
        "sema4ai.action_server._new_project_helpers._get_action_templates_dir_path",
    ) as mock_get_action_templates_dir_path:
        mock_get_action_templates_dir_path.return_value = templates_path

        retcode = handle_new_project(project_path, "minimal")
        log_critical_args = log_critical_mock.mock_calls[0].args
        log_warning_args = log_warning_mock.mock_calls[0].args

        assert retcode == 1
        assert os.path.isfile(project_path / "package.yaml") is False

        assert "Refreshing templates failed" in log_warning_args[0]
        assert "No cached or remote templates available" in log_critical_args[0]


@mock.patch(
    "sema4ai.action_server._new_project_helpers.requests.get",
    side_effect=requests.exceptions.HTTPError,
)
@mock.patch(
    "sema4ai.action_server._new_project.log.critical",
    wraps=sema4ai.action_server._new_project.log.critical,
)
@mock.patch(
    "sema4ai.action_server._new_project.log.warning",
    wraps=sema4ai.action_server._new_project.log.warning,
)
@mock.patch(
    "sema4ai.action_server._new_project.log.info",
    wraps=sema4ai.action_server._new_project.log.info,
)
def test_create_new_project_download_metadata_fail_with_cached_templates(
    log_info_mock: mock.MagicMock,
    log_warning_mock: mock.MagicMock,
    log_critical_mock: mock.MagicMock,
    _,
    tmpdir,
) -> None:
    from action_server_tests.fixtures import get_in_resources

    from sema4ai.action_server._new_project import handle_new_project

    templates_path = tmpdir / "action-templates"
    project_path = tmpdir / "my_project"

    resources_templates_dir = get_in_resources("sample_templates")

    # Simulating already cached templates.
    os.makedirs(templates_path)
    shutil.copyfile(
        resources_templates_dir / "action-templates.yaml",
        templates_path / "action-templates.yaml",
    )
    shutil.copyfile(
        resources_templates_dir / "minimal.zip", templates_path / "minimal.zip"
    )

    with mock.patch(
        "sema4ai.action_server._new_project_helpers._get_action_templates_dir_path",
    ) as mock_get_action_templates_dir_path:
        mock_get_action_templates_dir_path.return_value = templates_path

        retcode = handle_new_project(project_path, "minimal")
        log_info_args = log_info_mock.mock_calls[-1].args
        log_warning_args = log_warning_mock.mock_calls[0].args

        assert retcode == 0
        assert os.path.isfile(project_path / "package.yaml") is True

        assert "Refreshing templates failed" in log_warning_args[0]
        log_critical_mock.assert_not_called()

        assert "Project created" in log_info_args[0]


# It's important to mock the _ensure_latest_templates() here, so the test case does not attempt to
# download them to default storage directory.
@mock.patch(
    "sema4ai.action_server._new_project_helpers._ensure_latest_templates",
    side_effect=None,
)
@mock.patch(
    "sema4ai.action_server._new_project.log.info",
    wraps=sema4ai.action_server._new_project.log.info,
)
@mock.patch("builtins.print")
def test_list_templates_no_templates_available(
    print_mock: mock.MagicMock, log_info_mock: mock.MagicMock, _, tmpdir
) -> None:
    from sema4ai.action_server._new_project import handle_list_templates
    from sema4ai.action_server._new_project_helpers import ActionTemplatesMetadata

    with mock.patch(
        "sema4ai.action_server._new_project_helpers._get_local_templates_metadata"
    ) as mock_get_local_templates_metadata:
        mock_get_local_templates_metadata.return_value = ActionTemplatesMetadata(
            hash="test_hash",
            url="test_url",
            date=None,
            templates=[],
        )

        retcode = handle_list_templates()
        log_info_args = log_info_mock.mock_calls[-1].args

        assert retcode == 0
        assert "No templates available" in log_info_args[0]

        retcode = handle_list_templates(output_json=True)
        print_args = print_mock.mock_calls[-1].args

        assert retcode == 0
        assert print_args[0] == "[]"
