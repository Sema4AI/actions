"""Tests for agent dataframe API functions."""

import pytest


def test_list_data_frames_api():
    """Test list_data_frames with mocked API client."""
    from unittest.mock import MagicMock, patch

    from sema4ai.actions.agent import list_data_frames

    # Mock the _AgentAPIClient
    with patch("sema4ai.actions.agent._AgentAPIClient") as MockClient:
        mock_instance = MagicMock()
        MockClient.return_value = mock_instance

        # Mock the response
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "name": "sales_data",
                "description": "Q1 sales records",
                "num_rows": 100,
                "num_columns": 5,
                "column_headers": ["date", "product", "quantity", "price", "total"],
            },
            {
                "name": "customer_data",
                "description": None,
                "num_rows": 50,
                "num_columns": 3,
                "column_headers": ["id", "name", "email"],
            },
        ]
        mock_instance.request.return_value = mock_response

        # Mock get_thread_id to return a test thread ID
        with patch(
            "sema4ai.actions.agent.get_thread_id", return_value="test-thread-123"
        ):
            # Call list_data_frames
            result = list_data_frames()

            # Verify the request was made correctly
            mock_instance.request.assert_called_once_with(
                "data-frames",
                method="GET",
                query_params={"thread_id": "test-thread-123"},
            )

            # Verify the response
            assert len(result) == 2
            assert result[0]["name"] == "sales_data"
            assert result[0]["num_rows"] == 100
            assert result[1]["name"] == "customer_data"
            assert result[1]["num_rows"] == 50


def test_get_data_frame_api():
    """Test get_data_frame with mocked API client."""
    from unittest.mock import MagicMock, patch

    from sema4ai.actions.agent import get_data_frame

    # Mock the _AgentAPIClient
    with patch("sema4ai.actions.agent._AgentAPIClient") as MockClient:
        mock_instance = MagicMock()
        MockClient.return_value = mock_instance

        # Mock the response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "columns": ["product", "sales"],
            "rows": [["Widget", 100], ["Gadget", 200]],
            "name": "q1_sales",
            "description": "Q1 sales data",
        }
        mock_instance.request.return_value = mock_response

        # Mock get_thread_id
        with patch(
            "sema4ai.actions.agent.get_thread_id", return_value="test-thread-456"
        ):
            # Call get_data_frame
            result = get_data_frame("q1_sales", limit=5000)

            # Verify the request was made correctly
            mock_instance.request.assert_called_once_with(
                "data-frames/q1_sales",
                method="GET",
                query_params={"thread_id": "test-thread-456", "limit": 5000},
            )

            # Verify the response is a Table
            assert result.columns == ["product", "sales"]
            assert result.rows == [["Widget", 100], ["Gadget", 200]]
            assert result.name == "q1_sales"
            assert result.description == "Q1 sales data"


def test_get_data_frame_not_found():
    """Test get_data_frame raises ValueError when dataframe not found (404)."""
    from unittest.mock import MagicMock, patch

    from sema4ai.actions.agent import get_data_frame
    from sema4ai.actions.agent._client import AgentApiClientException

    # Mock the _AgentAPIClient
    with patch("sema4ai.actions.agent._AgentAPIClient") as MockClient:
        mock_instance = MagicMock()
        MockClient.return_value = mock_instance

        # Mock a 404 error
        mock_instance.request.side_effect = AgentApiClientException(
            "HTTP 404: Not Found"
        )

        # Mock get_thread_id
        with patch(
            "sema4ai.actions.agent.get_thread_id", return_value="test-thread-789"
        ):
            # Call get_data_frame - should raise ValueError
            with pytest.raises(ValueError) as exc_info:
                get_data_frame("nonexistent_df")

            # Verify the error message
            assert "Data frame 'nonexistent_df' not found" in str(exc_info.value)
            assert "test-thread-789" in str(exc_info.value)


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


def test_data_frame_api_with_limit():
    """Test get_data_frame respects the limit parameter."""
    from unittest.mock import MagicMock, patch

    from sema4ai.actions.agent import get_data_frame

    # Mock the _AgentAPIClient
    with patch("sema4ai.actions.agent._AgentAPIClient") as MockClient:
        mock_instance = MagicMock()
        MockClient.return_value = mock_instance

        # Mock the response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "columns": ["id", "value"],
            "rows": [[i, i * 10] for i in range(100)],  # 100 rows
            "name": "test_data",
            "description": "Test dataset",
        }
        mock_instance.request.return_value = mock_response

        # Mock get_thread_id
        with patch(
            "sema4ai.actions.agent.get_thread_id", return_value="test-thread-limit"
        ):
            # Call get_data_frame with custom limit
            result = get_data_frame("test_data", limit=100)

            # Verify the limit was passed in the request
            mock_instance.request.assert_called_once_with(
                "data-frames/test_data",
                method="GET",
                query_params={"thread_id": "test-thread-limit", "limit": 100},
            )

            # Verify the response
            assert result.name == "test_data"
            assert len(result.rows) == 100
