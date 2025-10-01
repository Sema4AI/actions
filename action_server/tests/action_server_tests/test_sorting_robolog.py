from pathlib import Path


def test_sorting_robolog():
    """Test the sorting of robolog files."""

    from sema4ai.action_server._api_run import _sort_robolog_files

    # Create test file paths
    test_files = [
        Path("output_2.robolog"),
        Path("output.robolog"),
        Path("output_1.robolog"),
        Path("output_10.robolog"),
        Path("other_3.robolog"),
        Path("other.robolog"),
        Path("other_1.robolog"),
        Path("output_3.robolog"),
        Path("complex_name_5.robolog"),
        Path("complex_name.robolog"),
        Path("complex_name_1.robolog"),
    ]

    sorted_files = _sort_robolog_files(test_files)

    expected_order = [
        "complex_name.robolog",
        "complex_name_1.robolog",
        "complex_name_5.robolog",
        "other.robolog",
        "other_1.robolog",
        "other_3.robolog",
        "output.robolog",
        "output_1.robolog",
        "output_2.robolog",
        "output_3.robolog",
        "output_10.robolog",
    ]

    actual_order = [f.name for f in sorted_files]

    assert actual_order == expected_order
