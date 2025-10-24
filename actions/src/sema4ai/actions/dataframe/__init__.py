from ._utils import _flatten_with_auto_detection, _flatten_with_schema


def json_to_dataframe(
    data: dict, schema_fields: list[str] | None = None
) -> dict[str, list]:
    """
    Convert hierarchical JSON to DataFrame format (columns + rows).

    Uses pandas.json_normalize() for robust JSON flattening with:
    - Schema-driven field selection when schema is provided
    - Automatic array expansion (fallback behavior)
    - Nested object flattening (dot notation)
    - Scalar broadcasting (non-array fields repeated for each row)

    Args:
        data: The JSON data to flatten (extracted content)
        schema_fields: Optional list of field paths (in dot notation) to extract from json_data
            into the dataframe.
            Each string is a path to a field you want as a column in the resulting table.
            Use dot notation to access nested fields (e.g., 'customer.name', 'order.total').
            When field paths reference array elements ('transactions.amount', 'items.price'),
            that array will be expanded into multiple rows - one row per array item.
            All other fields will be repeated for each row.
            If multiple arrays exist in the data, the biggest array will be expanded.
            Examples:
            - ['seller', 'buyer', 'invoice_number', 'invoice_date']
                extracts 4 scalar fields from top level
            - ['customer.name', 'customer.email', 'order.total']
                extracts nested fields from objects
            - ['transactions.date', 'transactions.amount', 'invoice_number']
                expands 'transactions' array, repeats 'invoice_number' for each row
            - ['items.code', 'items.qty', 'items.price']
                expands 'items' array into rows with these 3 columns from each item".

    Returns:
        Dict with 'columns' and 'rows' keys suitable for DataFrame creation
    """
    if schema_fields:
        return _flatten_with_schema(data, schema_fields)
    else:
        return _flatten_with_auto_detection(data)


__all__ = [
    "json_to_dataframe",
]
