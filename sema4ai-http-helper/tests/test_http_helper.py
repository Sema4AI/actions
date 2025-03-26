def test_http_helper_basic():
    import sema4ai_http

    response = sema4ai_http.get("https://google.com")
    assert response.status == 200
    assert response.status_code == 200

    assert response.raise_for_status() is None
    assert response.text is not None


def test_http_helper_download_with_resume(tmpdir):
    import os
    import subprocess
    import sys
    from pathlib import Path

    import sema4ai_http
    from sema4ai_http import _PartialDownloader

    if sys.platform == "win32":
        url = "https://github.com/Sema4AI/actions/releases/download/sema4ai-action_server-0.23.2/sema4ai-action_server-0.23.2-windows64"
    elif sys.platform == "linux":
        url = "https://github.com/Sema4AI/actions/releases/download/sema4ai-action_server-0.23.2/sema4ai-action_server-0.23.2-linux64"
    elif sys.platform == "darwin":
        url = "https://github.com/Sema4AI/actions/releases/download/sema4ai-action_server-0.23.2/sema4ai-action_server-0.23.2-macos64"

    executable = "action-server"
    if sys.platform == "win32":
        executable += ".exe"

    target = Path(tmpdir) / executable
    result = sema4ai_http.download_with_resume(url, target, make_executable=True)
    assert result.status == sema4ai_http.DownloadStatus.DONE

    assert target.is_file()
    # Just check that it runs to check whether the download was successful
    subprocess.check_output([target, "--help"])

    target.write_text("some-data", "utf-8")
    result = sema4ai_http.download_with_resume(
        url, target, make_executable=True, overwrite_existing=False
    )
    assert result.status == sema4ai_http.DownloadStatus.ALREADY_EXISTS

    assert target.read_text("utf-8") == "some-data"
    result = sema4ai_http.download_with_resume(
        url, target, make_executable=True, overwrite_existing=True
    )
    assert result.status == sema4ai_http.DownloadStatus.DONE

    assert target.is_file()
    subprocess.check_output([target, "--help"])

    os.remove(target)

    partial_target = _PartialDownloader.get_partial_target(target)
    partial_target.write_text("some-data", "utf-8")

    result = sema4ai_http.download_with_resume(
        url, target, make_executable=True, resume_from_existing_part_file=False
    )
    assert result.status == sema4ai_http.DownloadStatus.DONE

    assert target.is_file()
    # Just check that it runs to check whether the download was successful
    subprocess.check_output([target, "--help"])
