"""
Tests for JSON to DataFrame flattening using json_to_dataframe.

This tests the flattening logic that converts hierarchical JSON data into tabular format.
"""

import numpy as np
import pandas as pd
import pytest
from sema4ai.actions.dataframe import json_to_dataframe
from sema4ai.actions.dataframe._utils import _clean_and_convert_dataframe


class TestJsonToDataFrame:
    """Test the json_to_dataframe function."""

    def test_array_of_objects(self):
        """Test: Array of objects should become rows in DataFrame."""
        data = {
            "transactions": [
                {"date": "2023-01-01", "amount": 100, "type": "credit"},
                {"date": "2023-01-02", "amount": 50, "type": "debit"},
                {"date": "2023-01-03", "amount": 200, "type": "credit"},
            ]
        }

        result = json_to_dataframe(data)

        assert "columns" in result
        assert "rows" in result
        assert len(result["rows"]) == 3  # 3 transactions
        assert "transactions.amount" in result["columns"]
        assert "transactions.date" in result["columns"]
        assert "transactions.type" in result["columns"]

    def test_nested_objects(self):
        """Test: Nested objects should be flattened with dot notation."""
        data = {
            "person": {
                "name": "John Doe",
                "age": 30,
                "address": {
                    "street": "123 Main St",
                    "city": "Anytown",
                    "zipcode": "12345",
                },
            },
            "company": "ACME Corp",
        }

        result = json_to_dataframe(data)

        assert "person.name" in result["columns"]
        assert "person.age" in result["columns"]
        assert "person.address.street" in result["columns"]
        assert "person.address.city" in result["columns"]
        assert "company" in result["columns"]
        assert len(result["rows"]) == 1  # Single flattened row

    def test_mixed_structure_with_broadcasting(self):
        """Test: Mixed structure with array + scalar data should broadcast scalars."""
        data = {
            "document_info": {
                "title": "Invoice #12345",
                "date": "2023-01-01",
                "total": 350.00,
            },
            "line_items": [
                {"description": "Widget A", "quantity": 2, "price": 150.00},
                {"description": "Widget B", "quantity": 1, "price": 50.00},
            ],
        }

        result = json_to_dataframe(data)

        # Should prioritize the array and broadcast the scalar data
        assert len(result["rows"]) == 2  # 2 line items
        assert "line_items.description" in result["columns"]
        assert "line_items.quantity" in result["columns"]
        assert "line_items.price" in result["columns"]

        # Scalar data should be broadcast to each row
        assert any(
            "title" in col or "document_info" in col for col in result["columns"]
        )

        for col in result["columns"]:
            assert not col.startswith("root."), (
                f"Column {col!r} should not have 'root.' prefix"
            )

    def test_simple_key_values(self):
        """Test: Simple key-value pairs become single row."""
        data = {
            "invoice_number": "INV-12345",
            "total_amount": 1500.00,
            "due_date": "2023-02-01",
            "customer": "ABC Company",
        }

        result = json_to_dataframe(data)

        assert len(result["rows"]) == 1
        assert len(result["columns"]) == 4
        assert all(
            col in result["columns"]
            for col in ["invoice_number", "total_amount", "due_date", "customer"]
        )

    def test_empty_data(self):
        """Test: Empty data should return empty DataFrame."""
        data = {}
        result = json_to_dataframe(data)

        assert result["columns"] == []
        assert result["rows"] == []

    def test_with_schema_fields(self):
        """Test: Field paths should prioritize schema-defined arrays."""
        data = {
            "metadata": {"doc_id": "DOC-001"},
            "scalar_field": "scalar_value",
            "scalar_list": ["scalar_list_1", "scalar_list_2"],
            "scalar_dict": {"key1": "value1", "key2": "value2"},
            "small_array": [{"x": 1}],
            "large_array": [{"a": 1}, {"a": 2}, {"a": 3}],
        }

        # Field paths indicate small_array is the important one (despite being smaller)
        schema_fields = [
            "small_array.x",
            "metadata.doc_id",
            "scalar_field",
            "scalar_list",
            "scalar_dict",
        ]

        result = json_to_dataframe(data, schema_fields)

        # Should use small_array as it has fields in schema_fields
        assert len(result["rows"]) == 1
        assert "small_array.x" in result["columns"]
        assert (
            "metadata.doc_id" in result["columns"]
        )  # Scalar fields should be broadcast
        assert "scalar_field" in result["columns"]
        assert "scalar_list" in result["columns"]
        assert "scalar_dict" in result["columns"]

        # Check scalar_list value (lists are converted to JSON strings)
        scalar_list_idx = result["columns"].index("scalar_list")
        assert (
            result["rows"][0][scalar_list_idx] == '["scalar_list_1", "scalar_list_2"]'
        )

        # Check scalar_dict value (dicts/objects are converted to JSON strings)
        scalar_dict_idx = result["columns"].index("scalar_dict")
        assert (
            result["rows"][0][scalar_dict_idx] == '{"key1": "value1", "key2": "value2"}'
        )

    def test_complex_real_world_invoice(self):
        """Test: Complex invoice-like document structure."""
        data = {
            "company_info": {
                "name": "ACME Corporation",
                "address": "123 Business St, Suite 100",
                "phone": "555-0123",
            },
            "invoice_details": {
                "number": "INV-2023-001",
                "date": "2023-01-15",
                "due_date": "2023-02-15",
            },
            "items": [
                {
                    "product": "Professional Services",
                    "hours": 40,
                    "rate": 150.00,
                    "total": 6000.00,
                },
                {
                    "product": "Software License",
                    "hours": None,
                    "rate": 500.00,
                    "total": 500.00,
                },
            ],
            "summary": {"subtotal": 6500.00, "tax": 520.00, "grand_total": 7020.00},
        }

        result = json_to_dataframe(data)

        # Should focus on the items array as the primary table
        assert len(result["rows"]) == 2  # 2 items
        assert "items.product" in result["columns"]
        assert "items.hours" in result["columns"]
        assert "items.rate" in result["columns"]
        assert "items.total" in result["columns"]

        # Other data should be broadcast
        assert any("company_info" in col or "name" in col for col in result["columns"])

    def test_empty_array(self):
        """Test: Empty array should fall back to scalar flattening."""
        data = {
            "info": {"title": "Test"},
            "items": [],  # Empty array
        }

        result = json_to_dataframe(data)

        # Empty array is ignored, falls back to flattening scalar fields
        assert len(result["rows"]) == 1  # Single row with scalar data
        assert "info.title" in result["columns"]
        assert result["rows"][0][result["columns"].index("info.title")] == "Test"

    def test_nested_array_fields_with_schema(self):
        """Test: Nested fields in arrays should be properly flattened with schema fields."""
        data = {
            "items": [
                {
                    "name": "Item 1",
                    "details": {"color": "red", "size": "large"},
                    "tags": ["new", "popular"],
                },
                {
                    "name": "Item 2",
                    "details": {"color": "blue", "size": "small"},
                    "tags": ["sale"],
                },
            ]
        }

        # Use schema fields to specify exactly which nested fields to extract
        schema_fields = [
            "items.name",
            "items.details.color",
            "items.details.size",
        ]
        result = json_to_dataframe(data, schema_fields)

        # Should have the specified columns
        for col in schema_fields:
            assert col in result["columns"], f"Missing column: {col}"

        # Check values
        name_idx = result["columns"].index("items.name")
        color_idx = result["columns"].index("items.details.color")
        size_idx = result["columns"].index("items.details.size")

        assert result["rows"][0][name_idx] == "Item 1"
        assert result["rows"][0][color_idx] == "red"
        assert result["rows"][0][size_idx] == "large"
        assert result["rows"][1][color_idx] == "blue"

    def test_column_prefixing_with_array_field_names(self):
        """Test: Array field names should be properly prefixed in column names."""
        data = {
            "document_metadata": {"id": "DOC-123", "type": "invoice"},
            "line_items": [
                {"product": "Widget A", "price": 10.0},
                {"product": "Widget B", "price": 20.0},
            ],
            "payment_terms": {"due_days": 30, "discount": 0.02},
        }

        result = json_to_dataframe(data)

        # Line item fields should have "line_items." prefix
        assert "line_items.product" in result["columns"]
        assert "line_items.price" in result["columns"]

        # Other fields should not have the prefix (they're broadcast)
        metadata_cols = [
            col
            for col in result["columns"]
            if "document_metadata" in col or "id" in col
        ]
        payment_cols = [
            col
            for col in result["columns"]
            if "payment_terms" in col or "due_days" in col
        ]

        assert len(metadata_cols) > 0
        assert len(payment_cols) > 0


class TestDataFrameCleaning:
    """Test the DataFrame cleaning functionality for Agent Platform compatibility."""

    def test_nan_values_converted_to_none(self):
        """Test: NaN values should be converted to None for PyArrow compatibility."""
        # Create DataFrame with NaN values
        df = pd.DataFrame(
            {
                "price": [1.5, float("nan"), 2.0],
                "quantity": [100, 200, float("nan")],
                "name": ["A", "B", "C"],
            }
        )

        result = _clean_and_convert_dataframe(df)

        # Check that NaN values became None
        assert result["rows"][0][0] == 1.5  # First price value unchanged
        assert (
            pd.isna(result["rows"][1][0]) or result["rows"][1][0] is None
        )  # NaN handled
        assert (
            pd.isna(result["rows"][2][1]) or result["rows"][2][1] is None
        )  # NaN handled
        assert result["rows"][0][2] == "A"  # String values unchanged

    def test_complex_objects_converted_to_json_strings(self):
        """Test: Complex objects (dicts, lists) should be converted to JSON strings."""
        df = pd.DataFrame(
            {
                "simple": ["text", 123, 45.6],
                "complex": [
                    {"name": "John", "age": 30},
                    ["item1", "item2", "item3"],
                    "simple_string",
                ],
            }
        )

        result = _clean_and_convert_dataframe(df)

        # Simple values unchanged
        assert result["rows"][0][0] == "text"
        assert result["rows"][1][0] == 123
        assert result["rows"][2][0] == 45.6

        # Complex objects converted to JSON strings
        assert result["rows"][0][1] == '{"name": "John", "age": 30}'
        assert result["rows"][1][1] == '["item1", "item2", "item3"]'
        assert result["rows"][2][1] == "simple_string"  # String unchanged

    def test_mixed_data_types_with_numpy_types(self):
        """Test: Mixed data types including numpy types should be normalized."""
        df = pd.DataFrame(
            {
                "numpy_int": [np.int64(100), np.int32(200), np.int16(300)],
                "numpy_float": [np.float64(1.5), np.float32(2.5), np.float64("nan")],
                "python_types": [1, 2.0, "text"],
                "mixed_complex": [{"key": "value"}, [1, 2, 3], None],
            }
        )

        result = _clean_and_convert_dataframe(df)

        # Numpy types should be converted to Python types
        assert isinstance(result["rows"][0][0], int | np.integer)
        assert isinstance(result["rows"][0][1], float | np.floating)
        assert (
            pd.isna(result["rows"][2][1]) or result["rows"][2][1] is None
        )  # numpy.nan handled

        # Complex objects should be JSON strings
        assert result["rows"][0][3] == '{"key": "value"}'
        assert result["rows"][1][3] == "[1, 2, 3]"
        assert result["rows"][2][3] is None  # None unchanged

    def test_edge_cases_and_error_handling(self):
        """Test: Edge cases and error handling in data cleaning."""
        df = pd.DataFrame(
            {
                "problematic": [
                    {"nested": {"deep": {"value": 123}}},  # Deeply nested
                    float("nan"),
                    float("inf"),
                    None,
                    {"valid": "data"},
                ]
            }
        )

        # Should not raise exceptions
        result = _clean_and_convert_dataframe(df)

        # Check that it handled the cases gracefully
        assert len(result["rows"]) == 5
        assert result["rows"][1][0] is None  # NaN -> None
        assert result["rows"][2][0] is None  # inf -> None
        assert result["rows"][3][0] is None  # None unchanged

        # First row should be JSON string (deeply nested dict)
        assert isinstance(result["rows"][0][0], str)
        assert "nested" in result["rows"][0][0]

    def test_energy_trading_invoice_data_structure(self):
        """Test: Energy trading invoice data structure with fictional data."""
        # Based on energy trading invoice structure but with fictional data
        data = {
            "bill_to": {
                "name": "Example Energy Corp",
                "address": "123 Business St, Suite 100, City, ST 12345",
                "contact_email": "billing@example-energy.com",
            },
            "statement_header": {
                "invoice_statement_amount": 50000,
                "due_date": "2024-08-15",
                "invoice_number": "INV-2024-001",
                "invoice_date": "2024-07-15",
                "delivery_period": "Jul-24",
                "contact_email": "invoices@fictional-energy.com",
                "contact_phone": "555-123-4567",
                "currency": "USD",
            },
            "payment_instructions": {
                "bank_name": "Example Bank",
                "aba_routing_number": "123456789",
                "account_number": "9876543210",
                "account_name": "Fictional Energy Trading LLC",
            },
            "line_items": [
                {
                    "section": "Group A",
                    "ae_reference_id": None,
                    "start_date": None,
                    "end_date": None,
                    "pipeline": None,
                    "location_or_description": None,
                    "quantity_mmbtu": 45000,
                    "price_per_mmbtu_usd": float("nan"),  # NaN value for testing
                    "amount_usd": 50000.0,
                },
                {
                    "section": "#1 - Energy Sale",
                    "ae_reference_id": None,
                    "start_date": None,
                    "end_date": None,
                    "pipeline": None,
                    "location_or_description": None,
                    "quantity_mmbtu": 35000,
                    "price_per_mmbtu_usd": float("nan"),  # NaN value for testing
                    "amount_usd": 70000.0,
                },
                {
                    "section": None,
                    "ae_reference_id": "TXN-001",
                    "start_date": "2024-07-01",
                    "end_date": "2024-07-31",
                    "pipeline": "Example Pipeline",
                    "location_or_description": "Test Location",
                    "quantity_mmbtu": 10000,
                    "price_per_mmbtu_usd": 2.0,
                    "amount_usd": 20000.0,
                },
            ],
            "totals": {"net_amount_usd": 50000, "net_quantity_mmbtu": None},
        }

        result = json_to_dataframe(data)

        # Should have 3 rows (one per line item)
        assert len(result["rows"]) == 3

        # Should have prefixed column names for line items
        line_item_columns = [
            col for col in result["columns"] if col.startswith("line_items.")
        ]
        assert len(line_item_columns) > 0

        # Check specific columns exist
        expected_line_item_cols = [
            "line_items.section",
            "line_items.ae_reference_id",
            "line_items.quantity_mmbtu",
            "line_items.price_per_mmbtu_usd",
            "line_items.amount_usd",
        ]
        for col in expected_line_item_cols:
            assert col in result["columns"], f"Missing column: {col}"

        # Complex objects should be JSON strings
        bill_to_cols = [col for col in result["columns"] if "bill_to" in col]
        assert len(bill_to_cols) > 0

        # Check that NaN values were handled properly
        price_col_idx = result["columns"].index("line_items.price_per_mmbtu_usd")
        # NaN values are handled (either as None or NaN)
        assert (
            pd.isna(result["rows"][0][price_col_idx])
            or result["rows"][0][price_col_idx] is None
        )
        assert (
            pd.isna(result["rows"][1][price_col_idx])
            or result["rows"][1][price_col_idx] is None
        )
        assert result["rows"][2][price_col_idx] == 2.0  # Normal value unchanged

    def test_none_values_not_converted_to_nan(self):
        """Test: None values in source data should remain None, not become NaN."""
        # Test with explicit None values in array
        data = {
            "items": [
                {"product": "Service A", "hours": 40, "rate": 150.0},
                {"product": "Service B", "hours": None, "rate": 200.0},  # Explicit None
                {"product": "Service C", "hours": 30, "rate": None},  # Another None
            ]
        }

        result = json_to_dataframe(data)

        # Find column indices
        hours_idx = result["columns"].index("items.hours")
        rate_idx = result["columns"].index("items.rate")

        # Verify None values are preserved as None, not NaN
        assert result["rows"][0][hours_idx] == 40.0
        assert result["rows"][1][hours_idx] is None  # Must be None, not NaN
        assert result["rows"][2][hours_idx] == 30.0

        assert result["rows"][0][rate_idx] == 150.0
        assert result["rows"][1][rate_idx] == 200.0
        assert result["rows"][2][rate_idx] is None  # Must be None, not NaN

        # Ensure we can serialize to JSON (would fail with NaN)
        import json

        json_str = json.dumps(result)  # Should not raise ValueError
        assert json_str is not None

    @pytest.mark.slow
    def test_performance_with_large_dataset(self):
        """Test: Performance with larger dataset similar to energy trading invoice."""
        # Create a dataset similar to energy trading invoice with many rows (fictional data)
        large_data = {
            "invoice_info": {
                "number": "INV-TEST-001",
                "amount": 100000.00,
                "date": "2024-07-15",
            },
            "transactions": [],
        }

        # Add 100 transactions with mixed data types (fictional data)
        for i in range(100):
            transaction = {
                "id": f"TXN-{1000 + i}",
                "date": f"2024-07-{(i % 30) + 1:02d}",
                "pipeline": ["Pipeline A", "Pipeline B", "Pipeline C"][i % 3],
                "quantity": 1000 + (i * 100),
                "price": round(1.5 + (i * 0.01), 4),
                "amount": round((1000 + i * 100) * (1.5 + i * 0.01), 2),
                "metadata": {
                    "processed": True,
                    "notes": f"Test Transaction {i}",
                    "tags": ["energy", "test"],
                },
            }
            # Add some NaN values randomly
            if i % 10 == 0:
                transaction["price"] = float("nan")
            large_data["transactions"].append(transaction)

        # This should complete without errors and in reasonable time
        result = json_to_dataframe(large_data)

        assert len(result["rows"]) == 100
        assert len(result["columns"]) > 5  # Should have multiple columns

        # Check that NaN values were handled
        price_col = None
        for col in result["columns"]:
            if "price" in col:
                price_col = result["columns"].index(col)
                break

        assert price_col is not None
        # Every 10th row should have NaN/None for price
        for i in range(0, 100, 10):
            assert (
                pd.isna(result["rows"][i][price_col])
                or result["rows"][i][price_col] is None
            )
