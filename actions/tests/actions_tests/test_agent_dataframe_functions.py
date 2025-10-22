"""Tests for agent dataframe API functions."""

import os

import pytest
from actions_tests.agent_dummy_server import AgentDummyServer


@pytest.fixture
def agent_dummy_server():
    server = AgentDummyServer()
    server.start()
    yield server
    server.stop()


def test_list_data_frames_api(agent_dummy_server):
    """Test list_data_frames with dummy server."""
    from sema4ai.actions.agent import list_data_frames

    # Set the environment variable to point to our dummy server
    os.environ[
        "SEMA4AI_AGENTS_SERVICE_URL"
    ] = f"http://localhost:{agent_dummy_server.get_port()}"

    # Mock get_thread_id to return a test thread ID
    from unittest.mock import patch

    with patch("sema4ai.actions.agent.get_thread_id", return_value="test-thread-123"):
        # Call list_data_frames
        result = list_data_frames()

        # Verify the request was made correctly
        assert agent_dummy_server.last_request is not None
        assert agent_dummy_server.last_request["thread_id"] == "test-thread-123"
        assert (
            agent_dummy_server.last_request["path"]
            == "/api/v2/data-frames?thread_id=test-thread-123"
        )
        assert agent_dummy_server.last_request["method"] == "GET"

        # Verify the response
        assert len(result) == 2
        assert result[0]["name"] == "sales_data"
        assert result[0]["num_rows"] == 100
        assert result[1]["name"] == "customer_data"
        assert result[1]["num_rows"] == 50


def test_get_data_frame_api(agent_dummy_server):
    """Test get_data_frame with dummy server."""
    from unittest.mock import patch

    from sema4ai.actions.agent import get_data_frame

    # Set the environment variable to point to our dummy server
    os.environ[
        "SEMA4AI_AGENTS_SERVICE_URL"
    ] = f"http://localhost:{agent_dummy_server.get_port()}"

    # Mock PyArrow as unavailable to force JSON format
    with patch("sema4ai.actions.agent._is_pyarrow_available", return_value=False):
        with patch(
            "sema4ai.actions.agent.get_thread_id", return_value="test-thread-456"
        ):
            # Call get_data_frame
            result = get_data_frame("q1_sales", limit=5000)

            # Verify the request was made correctly
            assert agent_dummy_server.last_request is not None
            assert agent_dummy_server.last_request["thread_id"] == "test-thread-456"
            assert agent_dummy_server.last_request["dataframe_name"] == "q1_sales"
            assert agent_dummy_server.last_request["limit"] == 5000
            assert agent_dummy_server.last_request["offset"] == 0
            assert agent_dummy_server.last_request["method"] == "GET"

            # Verify the response is a Table
            assert result.columns == ["product", "sales"]
            assert result.rows == [["Widget", 100], ["Gadget", 200]]
            assert result.name == "q1_sales"
            assert result.description == "Data for q1_sales"


def test_get_data_frame_not_found(agent_dummy_server):
    """Test get_data_frame raises ValueError when dataframe not found (404)."""
    from sema4ai.actions.agent import get_data_frame

    # Set the environment variable to point to our dummy server
    os.environ[
        "SEMA4AI_AGENTS_SERVICE_URL"
    ] = f"http://localhost:{agent_dummy_server.get_port()}"

    # Mock get_thread_id
    from unittest.mock import patch

    with patch("sema4ai.actions.agent.get_thread_id", return_value="test-thread-789"):
        # Call get_data_frame - should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            get_data_frame("nonexistent_df")

        # Verify the error message
        assert "Data frame 'nonexistent_df' not found" in str(exc_info.value)
        assert "test-thread-789" in str(exc_info.value)

        # Verify the request was made correctly
        assert agent_dummy_server.last_request is not None
        assert agent_dummy_server.last_request["dataframe_name"] == "nonexistent_df"
        assert agent_dummy_server.last_request["thread_id"] == "test-thread-789"


def test_get_data_frame_outside_context():
    """Test get_data_frame raises ActionError when called outside action context."""
    from unittest.mock import patch

    from sema4ai.actions._response import ActionError
    from sema4ai.actions.agent import get_data_frame

    # Mock get_thread_id to raise ActionError (simulating no context)
    with patch(
        "sema4ai.actions.agent.get_thread_id",
        side_effect=ActionError("Unable to get the thread_id"),
    ):
        # Call get_data_frame - should raise ActionError
        with pytest.raises(ActionError) as exc_info:
            get_data_frame("some_df")

        # Verify the error message
        assert "Unable to get the thread_id" in str(exc_info.value)


def test_data_frame_api_with_limit(agent_dummy_server):
    """Test get_data_frame respects the limit parameter."""
    from unittest.mock import patch

    from sema4ai.actions.agent import get_data_frame

    # Set the environment variable to point to our dummy server
    os.environ[
        "SEMA4AI_AGENTS_SERVICE_URL"
    ] = f"http://localhost:{agent_dummy_server.get_port()}"

    # Mock PyArrow as unavailable to force JSON format
    with patch("sema4ai.actions.agent._is_pyarrow_available", return_value=False):
        with patch(
            "sema4ai.actions.agent.get_thread_id", return_value="test-thread-limit"
        ):
            # Call get_data_frame with custom limit
            result = get_data_frame("test_data", limit=100)

            # Verify the limit was passed in the request
            assert agent_dummy_server.last_request is not None
            assert agent_dummy_server.last_request["thread_id"] == "test-thread-limit"
            assert agent_dummy_server.last_request["dataframe_name"] == "test_data"
            assert agent_dummy_server.last_request["limit"] == 100
            assert agent_dummy_server.last_request["offset"] == 0

            # Verify the response
            assert result.name == "test_data"
            assert result.description == "Data for test_data"


def test_get_data_frame_with_additional_parameters(agent_dummy_server):
    """Test get_data_frame with offset, column_names, and order_by parameters."""
    from unittest.mock import patch

    from sema4ai.actions.agent import get_data_frame

    # Set the environment variable to point to our dummy server
    os.environ[
        "SEMA4AI_AGENTS_SERVICE_URL"
    ] = f"http://localhost:{agent_dummy_server.get_port()}"

    # Mock PyArrow as unavailable to force JSON format
    with patch("sema4ai.actions.agent._is_pyarrow_available", return_value=False):
        with patch(
            "sema4ai.actions.agent.get_thread_id", return_value="test-thread-params"
        ):
            result = get_data_frame(
                "sales_data",
                limit=50,
                offset=10,
                column_names=["product", "revenue"],
                order_by="revenue",
            )

            # Verify the client was called with correct parameters
            assert agent_dummy_server.last_request is not None
            assert agent_dummy_server.last_request["thread_id"] == "test-thread-params"
            assert agent_dummy_server.last_request["dataframe_name"] == "sales_data"
            assert agent_dummy_server.last_request["limit"] == 50
            assert agent_dummy_server.last_request["offset"] == 10
            assert agent_dummy_server.last_request["column_names"] == "product,revenue"
            assert agent_dummy_server.last_request["order_by"] == "revenue"

            # Verify the response
            assert result.name == "sales_data"
            assert result.description == "Data for sales_data"
            assert result.columns == ["product", "sales"]
            assert len(result.rows) == 2


def test_get_data_frame_requests_json_format_when_pyarrow_unavailable(
    agent_dummy_server,
):
    """Test get_data_frame requests JSON format when PyArrow is not available."""
    from unittest.mock import patch

    from sema4ai.actions.agent import get_data_frame

    # Set the environment variable to point to our dummy server
    os.environ[
        "SEMA4AI_AGENTS_SERVICE_URL"
    ] = f"http://localhost:{agent_dummy_server.get_port()}"

    # Mock PyArrow as unavailable
    with patch("sema4ai.actions.agent._is_pyarrow_available", return_value=False):
        with patch(
            "sema4ai.actions.agent.get_thread_id", return_value="test-thread-json"
        ):
            result = get_data_frame("test_data")

            # Verify JSON format was requested
            assert agent_dummy_server.last_request is not None
            assert agent_dummy_server.last_request["format"] == "json"
            assert result.name == "test_data"


def test_get_data_frame_requests_parquet_format_when_pyarrow_available(
    agent_dummy_server,
):
    """Test get_data_frame requests Parquet format when PyArrow is available.

    Note: This test only verifies that the correct format is requested.
    The dummy server returns JSON, so we can't test actual Parquet parsing here.
    """
    from unittest.mock import patch

    from sema4ai.actions.agent import get_data_frame

    # Set the environment variable to point to our dummy server
    os.environ[
        "SEMA4AI_AGENTS_SERVICE_URL"
    ] = f"http://localhost:{agent_dummy_server.get_port()}"

    # Mock PyArrow as available and mock the parquet parsing function
    # to avoid trying to parse JSON as Parquet
    with patch("sema4ai.actions.agent._is_pyarrow_available", return_value=True):
        with patch(
            "sema4ai.actions.agent._parse_dataframe_response_from_parquet"
        ) as mock_parse:
            # Make the mock return valid data
            mock_parse.return_value = {
                "columns": ["product", "sales"],
                "rows": [["Widget", 100], ["Gadget", 200]],
                "name": "test_data",
                "description": "Data for test_data",
            }

            with patch(
                "sema4ai.actions.agent.get_thread_id",
                return_value="test-thread-parquet",
            ):
                result = get_data_frame("test_data")

                # Verify Parquet format was requested
                assert agent_dummy_server.last_request is not None
                assert agent_dummy_server.last_request["format"] == "parquet"

                # Verify the parquet parser was called
                assert mock_parse.called

                # Verify the result
                assert result.name == "test_data"
