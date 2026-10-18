import io
from unittest.mock import Mock

import pytest
import urllib3

from sema4ai_http import DownloadStatus, download_with_resume


def _response(status, body=b"not found", **headers):
    return urllib3.response.HTTPResponse(
        body=io.BytesIO(body),
        status=status,
        headers={"Content-Length": str(len(body)), **headers},
        preload_content=False,
    )


@pytest.mark.parametrize("status", [401, 403, 404, 429, 500, 503])
@pytest.mark.parametrize("resume", [False, True])
def test_error_response_never_saved_as_download(tmp_path, status, resume):
    target = tmp_path / "artifact"
    partial = tmp_path / "artifact.part"
    if resume:
        partial.write_bytes(b"original")
    pool = Mock()
    response = _response(status)
    pool.request.return_value = response

    with pytest.raises(urllib3.exceptions.HTTPError, match=str(status)):
        download_with_resume(
            "https://example.test/artifact",
            target,
            pool_manager=pool,
            max_retries=0,
            wait_interval=0,
        )

    assert not target.exists()
    assert response.closed
    if resume:
        assert partial.read_bytes() == b"original"
    else:
        assert not partial.exists()


def test_retry_success_does_not_include_error_body(tmp_path):
    target = tmp_path / "artifact"
    pool = Mock()
    pool.request.side_effect = [_response(503), _response(200, b"artifact")]

    result = download_with_resume(
        "https://example.test/artifact",
        target,
        pool_manager=pool,
        max_retries=1,
        wait_interval=0,
    )

    assert result.status == DownloadStatus.DONE
    assert target.read_bytes() == b"artifact"
    assert pool.request.call_count == 2


def test_successful_partial_response_still_resumes(tmp_path):
    target = tmp_path / "artifact"
    (tmp_path / "artifact.part").write_bytes(b"art")
    pool = Mock()
    pool.request.return_value = _response(
        206, b"ifact", **{"Content-Range": "bytes 3-7/8"}
    )

    result = download_with_resume(
        "https://example.test/artifact", target, pool_manager=pool, wait_interval=0
    )

    assert result.status == DownloadStatus.DONE
    assert target.read_bytes() == b"artifact"
    assert pool.request.call_args.kwargs["headers"]["Range"] == "bytes=3-"
