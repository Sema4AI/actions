from sema4ai.actions import Response, Table, action


@action
def action_with_table_result() -> Table:
    table = Table(
        columns=["a", "b", "c", "d"],
        rows=[
            ["1", "2", [1, 2, 3], {"key": "value"}],
            ["3", "4", [4, 5, 6], {"key": "another_value"}],
        ],
    )
    assert table.columns == ["a", "b", "c", "d"]
    for row in table.rows:
        assert len(row) == 4

    for dct in table.iter_as_dicts():
        assert dct["a"] in ("1", "3")
        assert dct["b"] in ("2", "4")
        assert isinstance(dct["c"], list)
        assert isinstance(dct["d"], dict)

    return table


@action
def action_table_in_out(table: Table) -> Table:
    assert table.columns == ["a", "b", "c", "d"]
    for row in table.rows:
        assert len(row) == 4

    for dct in table.iter_as_dicts():
        assert dct["a"] in (1, 3)
        assert dct["b"] in ("2", "4")
        assert isinstance(dct["c"], list)
        assert isinstance(dct["d"], dict)

    return table


@action
def action_table_response() -> Response[Table]:
    table = Table(
        columns=["a", "b", "c", "d"],
        rows=[
            ["1", "2", [1, 2, 3], {"key": "value"}],
            ["3", "4", [4, 5, 6], {"key": "another_value"}],
        ],
    )

    return Response(result=table)
