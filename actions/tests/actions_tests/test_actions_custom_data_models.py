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

    table = Table(columns=["a", "b"], rows=[["1", "2"], ["3", "4"], ["5 abc ", 6.66]])
    assert table.columns == ["a", "b"]
    assert table.rows == [["1", "2"], ["3", "4"], ["5 abc ", 6.66]]
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
