from sema4ai.actions import Response, Table, action


@action
def action_with_table_result() -> Table:
    table = Table(columns=["a", "b"], rows=[["1", "2"], ["3", "4"]])
    assert table.columns == ["a", "b"]
    for row in table.rows:
        assert len(row) == 2

    for dct in table.iter_as_dicts():
        assert dct["a"] in ("1", "3")
        assert dct["b"] in ("2", "4")

    return table


@action
def action_table_in_out(table: Table) -> Table:
    assert table.columns == ["a", "b"]
    for row in table.rows:
        assert len(row) == 2

    for dct in table.iter_as_dicts():
        assert dct["a"] in (1, 3)
        assert dct["b"] in ("2", "4")

    return table


@action
def action_table_response() -> Response[Table]:
    table = Table(columns=["a", "b"], rows=[["1", "2"], ["3", "4"]])

    return Response(result=table)
