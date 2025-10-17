def test_actions_table_list(datadir, data_regression):
    import json

    from devutils.fixtures import sema4ai_actions_run

    result = sema4ai_actions_run(
        ["list", "--skip-lint"], returncode=0, cwd=str(datadir)
    )
    found = json.loads(result.stdout)
    assert len(found) == 5
    data = {}
    for f in found:
        data[f["name"]] = {
            "input_schema": f["input_schema"],
            "managed_params_schema": f["managed_params_schema"],
            "output_schema": f["output_schema"],
        }

    data_regression.check(data)


def test_table_result(datadir, data_regression, tmpdir):
    import json

    from devutils.fixtures import sema4ai_actions_run

    from sema4ai.actions import Table

    table = Table(columns=["a", "b"], rows=[[1, "2"], [3, "4"]])
    use_input = table.model_dump()

    output_file = tmpdir.join("output.json")
    input_file = tmpdir.join("input.json")
    with open(input_file, "w") as f:
        json.dump({"table": use_input}, f)

    result = sema4ai_actions_run(
        [
            "run",
            "-a=action_table_in_out",
            "--print-result",
            f"--json-input={input_file}",
            f"--json-output={output_file}",
        ],
        returncode=0,
        cwd=str(datadir),
    )
    assert "PASS" in result.stdout.decode("utf-8")
    assert output_file.exists()
    with open(output_file, "r") as f:
        data = json.load(f)
    data_regression.check(data)


def test_table_with_response(datadir, data_regression, tmpdir):
    import json

    from devutils.fixtures import sema4ai_actions_run

    output_file = tmpdir.join("output.json")

    result = sema4ai_actions_run(
        [
            "run",
            "-a=action_table_response",
            "--print-result",
            f"--json-output={output_file}",
        ],
        returncode=0,
        cwd=str(datadir),
    )
    assert "PASS" in result.stdout.decode("utf-8")
    assert output_file.exists()
    with open(output_file, "r") as f:
        data = json.load(f)
    data_regression.check(data)


def test_table(file_regression):
    import pytest

    from sema4ai.actions import Table

    table = Table(
        columns=["a", "b"],
        rows=[
            ["1", "2"],
            ["3", "4"],
            ["5 abc ", 6.66],
            [{"a": 1}, {"b": 2}],
            [[10, 11], "4"],
        ],
    )
    assert table.columns == ["a", "b"]
    assert table.rows == [
        ["1", "2"],
        ["3", "4"],
        ["5 abc ", 6.66],
        [{"a": 1}, {"b": 2}],
        [[10, 11], "4"],
    ]
    assert table[0] == ["1", "2"]
    assert table[1] == ["3", "4"]

    assert table.get_row_as_dict(0)["a"] == "1"
    assert table.get_row_as_dict(0)["b"] == "2"
    assert table.get_row_as_dict(1)["a"] == "3"
    assert table.get_row_as_dict(1)["b"] == "4"

    file_regression.check(str(table), basename="test_table_str")
    file_regression.check(repr(table), basename="test_table_repr")

    # Mismatch between columns and rows
    with pytest.raises(ValueError) as e:
        Table(columns=["a"], rows=[["1", "2"]])
    assert "Row 0 has 2 columns, expected 1" in str(e.value), str(e.value)

    # Columns must be strings
    with pytest.raises(ValueError) as e:
        Table(columns=[1, 2], rows=[["1", "2"]])
    assert "'columns' passed to Table constructor must be a list of strings" in str(
        e.value
    ), str(e.value)

    # Bad values (pydantic verification)
    with pytest.raises(ValueError) as e:
        Table(columns=["1", "2"], rows=[[object(), object()]])
    assert "Input should be a valid " in str(e.value), str(e.value)


def test_table_validation_all_rows_valid():
    """Test that tables with many valid rows are accepted."""
    from sema4ai.actions import Table

    # Create a table with 100 rows, all valid
    columns = ["col1", "col2", "col3"]
    rows = [[f"val{i}_1", f"val{i}_2", f"val{i}_3"] for i in range(100)]

    table = Table(columns=columns, rows=rows)
    assert len(table) == 100
    assert table.columns == columns
    assert table[99] == ["val99_1", "val99_2", "val99_3"]


def test_table_validation_fails_on_row_50():
    """Test that validation catches errors beyond the first 5 rows."""
    import pytest

    from sema4ai.actions import Table

    # Create 100 rows where row 50 has wrong column count
    columns = ["col1", "col2", "col3"]
    rows = [[f"val{i}_1", f"val{i}_2", f"val{i}_3"] for i in range(100)]
    
    # Make row 50 invalid (only 2 columns instead of 3)
    rows[50] = ["bad_val1", "bad_val2"]

    with pytest.raises(ValueError) as e:
        Table(columns=columns, rows=rows)
    
    # Verify the error message specifically mentions row 50
    assert "Row 50 has 2 columns, expected 3" in str(e.value), str(e.value)


def test_table_validation_fails_on_last_row():
    """Test that validation catches errors on the very last row."""
    import pytest

    from sema4ai.actions import Table

    # Create 20 rows where the last row (row 19) has wrong column count
    columns = ["a", "b"]
    rows = [[f"val{i}_1", f"val{i}_2"] for i in range(20)]
    
    # Make last row invalid (3 columns instead of 2)
    rows[19] = ["last_val1", "last_val2", "extra_column"]

    with pytest.raises(ValueError) as e:
        Table(columns=columns, rows=rows)
    
    # Verify the error message mentions row 19
    assert "Row 19 has 3 columns, expected 2" in str(e.value), str(e.value)


def test_table_validation_performance():
    """Test that validation with 10k rows completes in reasonable time."""
    import time

    from sema4ai.actions import Table

    # Create a table with 10,000 rows
    columns = ["col1", "col2", "col3", "col4", "col5"]
    rows = [[f"val{i}_1", f"val{i}_2", f"val{i}_3", f"val{i}_4", f"val{i}_5"] 
            for i in range(10000)]

    start_time = time.time()
    table = Table(columns=columns, rows=rows)
    elapsed_time = time.time() - start_time

    assert len(table) == 10000
    # Validation should complete in under 1 second for 10k rows
    # (this is a generous limit; typical performance should be much faster)
    assert elapsed_time < 1.0, f"Validation took {elapsed_time:.3f}s, expected < 1.0s"


def test_table_with_name_and_description():
    """Test that tables can have optional name and description metadata."""
    from sema4ai.actions import Table

    # Create table with name and description
    table = Table(
        columns=["product", "sales"],
        rows=[["Widget", 100], ["Gadget", 200]],
        name="q1_sales",
        description="Sales data for Q1 2024",
    )

    assert table.name == "q1_sales"
    assert table.description == "Sales data for Q1 2024"
    assert len(table) == 2
    assert table.columns == ["product", "sales"]


def test_table_backward_compatibility():
    """Test that tables without name/description still work (backward compatibility)."""
    from sema4ai.actions import Table

    # Create table without name/description (old way)
    table = Table(
        columns=["a", "b"],
        rows=[["1", "2"], ["3", "4"]],
    )

    # Fields should default to None
    assert table.name is None
    assert table.description is None
    assert len(table) == 2
    assert table.columns == ["a", "b"]


def test_table_serialization():
    """Test that Table with name/description can be serialized and deserialized."""
    import json

    from sema4ai.actions import Table

    # Test 1: Table WITH metadata
    with_metadata = Table(
        columns=["x", "y"],
        rows=[[1, 2], [3, 4]],
        name="test_data",
        description="Test dataset",
    )

    # Serialize using pydantic
    serialized = with_metadata.model_dump()
    assert serialized["name"] == "test_data"
    assert serialized["description"] == "Test dataset"
    assert serialized["columns"] == ["x", "y"]
    assert serialized["rows"] == [[1, 2], [3, 4]]

    # Can also serialize to JSON
    json_str = with_metadata.model_dump_json()
    data = json.loads(json_str)
    assert data["name"] == "test_data"
    assert data["description"] == "Test dataset"

    # Deserialize
    reconstructed = Table(**serialized)
    assert reconstructed.name == with_metadata.name
    assert reconstructed.description == with_metadata.description
    assert reconstructed.columns == with_metadata.columns
    assert reconstructed.rows == with_metadata.rows

    # Test 2: Table WITHOUT metadata (backward compatibility)
    without_metadata = Table(
        columns=["a", "b"],
        rows=[[1, 2]],
    )

    # Serialize - fields are present but set to None
    serialized_old = without_metadata.model_dump()
    assert serialized_old["name"] is None  # Fields present but None
    assert serialized_old["description"] is None  # Fields present but None
    assert serialized_old["columns"] == ["a", "b"]
    assert serialized_old["rows"] == [[1, 2]]

    # JSON serialization includes null values
    json_str_old = without_metadata.model_dump_json()
    data_old = json.loads(json_str_old)
    assert data_old["name"] is None
    assert data_old["description"] is None


def test_custom_pydantic_type():
    from sema4ai.actions._raw_types_handler import _obtain_raw_types_handler

    NewClass = _obtain_raw_types_handler("lst", list[int])

    lst = NewClass.model_validate([1, 2, 3])
    assert lst == [1, 2, 3]

    assert NewClass.model_json_schema() == {
        "items": {"type": "integer"},
        "title": "Lst",
        "type": "array",
    }

    assert NewClass.model_validate([1, 2, 3]) == [1, 2, 3]


def test_list_in_input_output(datadir, data_regression, tmpdir):
    import json

    from devutils.fixtures import sema4ai_actions_run

    use_input = [1, 2, 3]

    output_file = tmpdir.join("output.json")
    input_file = tmpdir.join("input.json")
    with open(input_file, "w") as f:
        json.dump({"lst": use_input}, f)

    result = sema4ai_actions_run(
        [
            "run",
            "-a=action_python_structures",
            "--print-result",
            f"--json-input={input_file}",
            f"--json-output={output_file}",
        ],
        returncode=0,
        cwd=str(datadir),
    )
    assert "PASS" in result.stdout.decode("utf-8")
    assert output_file.exists()
    with open(output_file, "r") as f:
        data = json.load(f)
    data_regression.check(data)


def test_list_with_response(datadir, data_regression, tmpdir):
    import json

    from devutils.fixtures import sema4ai_actions_run

    output_file = tmpdir.join("output.json")

    result = sema4ai_actions_run(
        [
            "run",
            "-a=action_python_structure_response",
            "--print-result",
            f"--json-output={output_file}",
        ],
        returncode=0,
        cwd=str(datadir),
    )
    assert "PASS" in result.stdout.decode("utf-8")
    assert output_file.exists()
    with open(output_file, "r") as f:
        data = json.load(f)
    data_regression.check(data)
