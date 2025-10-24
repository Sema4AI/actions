"""Utility functions for flattening JSON data into DataFrame format."""

import json
import math

import pandas as pd


def _find_array_field(data: dict) -> str | None:
    """Find the largest array field containing objects in the data."""
    object_arrays = [
        (key, len(value))
        for key, value in data.items()
        if isinstance(value, list)
        and value
        and all(isinstance(item, dict) for item in value)
    ]
    return max(object_arrays, key=lambda x: x[1])[0] if object_arrays else None


def _clean_and_convert_dataframe(df: pd.DataFrame) -> dict[str, list]:
    """Clean and convert a pandas DataFrame to a dictionary with columns and rows."""
    if df.empty:
        return {"columns": [], "rows": []}

    # Clean in one pass: handle all problematic values
    df_cleaned = df.copy()

    # Handle complex objects and NaN values in one pass
    def clean_value(x):
        # Handle complex objects first (before pd.isna check)
        if isinstance(x, dict | list):
            return json.dumps(x, ensure_ascii=False)
        # Handle NaN values (including float('nan'), pd.NA, np.nan, etc.)
        elif pd.isna(x):
            return None
        # Handle inf/-inf values
        elif isinstance(x, float) and (math.isinf(x) or math.isnan(x)):
            return None
        else:
            return x

    df_cleaned = df_cleaned.map(clean_value)

    # Convert to list of lists without going through numpy to preserve None values
    rows = df_cleaned.values.tolist()
    # Clean any remaining NaN values that might have been reintroduced by numpy conversion
    cleaned_rows = []
    for row in rows:
        cleaned_row = [clean_value(val) for val in row]
        cleaned_rows.append(cleaned_row)

    return {"columns": df_cleaned.columns.tolist(), "rows": cleaned_rows}


def _find_target_array_from_schema(data: dict, schema_fields: list[str]) -> str | None:
    """
    Determine which array should be expanded based on schema fields.

    If schema contains fields like 'small_list.name', 'small_list.value',
    then 'small_list' should be the target array.
    """
    # Find all arrays in the data
    available_arrays = [
        key
        for key, value in data.items()
        if isinstance(value, list)
        and value
        and all(isinstance(item, dict) for item in value)
    ]

    # Count how many schema fields belong to each array
    array_field_counts = {}
    for schema_field in schema_fields:
        for array_name in available_arrays:
            if schema_field.startswith(f"{array_name}."):
                array_field_counts[array_name] = (
                    array_field_counts.get(array_name, 0) + 1
                )

    # Return the array with the most schema fields, or None if no array fields in schema
    if array_field_counts:
        return max(array_field_counts.items(), key=lambda x: x[1])[0]

    return None


def _flatten_with_auto_detection(data: dict) -> dict[str, list]:
    """
    Flatten data using the original auto-detection algorithm.
    """
    array_field = _find_array_field(data)

    if array_field:
        # Use pandas record_path for array-focused flattening
        scalar_fields = [k for k in data.keys() if k != array_field]
        try:
            df = pd.json_normalize(
                data,
                record_path=array_field,
                meta=scalar_fields,
                sep=".",
                errors="ignore",
                meta_prefix="root.",
            )
            # Add array field prefix to array columns
            array_cols = [col for col in df.columns if not col.startswith("root.")]
            df = df.rename(columns={col: f"{array_field}.{col}" for col in array_cols})
            # Remove "root." prefix from meta columns
            rename_map = {
                col: col.replace("root.", "")
                for col in df.columns
                if col.startswith("root.")
            }
            if rename_map:
                df = df.rename(columns=rename_map)
        except (KeyError, TypeError, ValueError):
            df = pd.json_normalize(data, sep=".")
    else:
        # No arrays - flatten everything
        df = pd.json_normalize(data, sep=".")

    return _clean_and_convert_dataframe(df)


def _extract_meta_fields(
    schema_fields: list[str], target_array: str, data: dict
) -> list:
    """Extract meta (scalar) fields from schema for json_normalize."""
    meta_fields = []
    for schema_field in schema_fields:
        if not schema_field.startswith(f"{target_array}."):
            field_parts = schema_field.split(".")
            if len(field_parts) > 1:
                meta_fields.append(field_parts)
            elif field_parts[0] in data and field_parts[0] != target_array:
                meta_fields.append(field_parts[0])
    return meta_fields


def _filter_and_rename_columns(
    df: pd.DataFrame, schema_fields: list[str]
) -> pd.DataFrame:
    """Filter DataFrame to schema fields and rename root.* columns."""
    available_cols = []
    for schema_field in schema_fields:
        if schema_field in df.columns:
            available_cols.append(schema_field)
        elif f"root.{schema_field}" in df.columns:
            available_cols.append(f"root.{schema_field}")

    if available_cols:
        result: pd.DataFrame = df[available_cols]  # type: ignore[assignment]
        rename_map: dict[str, str] = {
            col: col.replace("root.", "")
            for col in result.columns
            if col.startswith("root.")
        }
        if rename_map:
            result = result.rename(columns=rename_map)  # type: ignore[call-overload]
        return result
    return df


def _flatten_with_schema(data: dict, schema_fields: list[str]) -> dict[str, list]:
    """
    Flatten data using schema fields to determine which array to expand and which fields to include.
    """
    target_array = _find_target_array_from_schema(data, schema_fields)

    if target_array:
        meta_fields = _extract_meta_fields(schema_fields, target_array, data)
        try:
            df = pd.json_normalize(
                data,
                record_path=target_array,
                meta=meta_fields if meta_fields else None,
                sep=".",
                errors="ignore",
                meta_prefix="root.",
            )
            array_cols = [col for col in df.columns if not col.startswith("root.")]
            df = df.rename(columns={col: f"{target_array}.{col}" for col in array_cols})
        except (KeyError, TypeError, ValueError):
            df = pd.json_normalize(data, sep=".")
    else:
        df = pd.json_normalize(data, sep=".")

    df = _filter_and_rename_columns(df, schema_fields)
    return _clean_and_convert_dataframe(df)  # type: ignore[arg-type]
