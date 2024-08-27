import json
import os
from pathlib import Path
from unittest import mock


@mock.patch("builtins.print")
def test_get_user_oauth_config_path(print_mock: mock.MagicMock, tmpdir) -> None:
    from sema4ai.action_server._get_oauth_config import (
        USER_CONFIG_FILE_NAME,
        get_user_oauth_config_path,
    )

    mock_settings_dir: Path = tmpdir / "action-server"
    mock_config_path: Path = mock_settings_dir / USER_CONFIG_FILE_NAME

    # Make sure all the directories in the mocked config path exist.
    os.makedirs(mock_settings_dir)

    with mock.patch(
        "sema4ai.action_server._settings.get_default_settings_dir"
    ) as mock_get_default_settings_dir:
        mock_get_default_settings_dir.return_value = mock_settings_dir

        assert mock_config_path.exists() is False

        retcode = get_user_oauth_config_path(output_json=False)

        assert retcode == 0
        assert mock_config_path.exists() is True

        # Get latest print args
        print_args = print_mock.mock_calls[-1].args

        assert print_args[0] == mock_config_path

        retcode = get_user_oauth_config_path(output_json=True)

        assert retcode == 0
        assert mock_config_path.exists() is True

        print_args = print_mock.mock_calls[-1].args

        json_data = json.loads(print_args[0])

        assert json_data["oauth_config_path"] == mock_config_path
