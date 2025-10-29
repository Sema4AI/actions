from typing import Iterator

import pydantic

RowValue = str | int | float | bool | list | dict | None
Row = list[RowValue]


class Table(pydantic.BaseModel):
    """
    Table is a simple data structure that represents a table with columns and rows.

    It's meant to be used to represent the result of a table-like operation.
    """

    columns: list[str]
    rows: list[Row]
    name: str | None = None
    description: str | None = None

    def __init__(
        self,
        columns: list[str],
        rows: list[Row],
        name: str | None = None,
        description: str | None = None,
    ):
        """
        Args:
            columns: The columns of the table.
            rows: The rows of the table.
            name: Optional name for the table (e.g., "sales_data").
            description: Optional description (e.g., "Sales records for Q1 2024").
        """
        if not isinstance(columns, list):
            raise ValueError("'columns' passed to Table constructor must be a list")

        for column in columns:
            if not isinstance(column, str):
                raise ValueError(
                    f"'columns' passed to Table constructor must be a list of strings, got {column}"
                )

        if not isinstance(rows, list):
            raise ValueError("'rows' passed to Table constructor must be a list")

        for i in range(len(rows)):  # Validate all rows
            row = rows[i]
            if not isinstance(row, list):
                raise ValueError(f"Row {i} is not a list: {row}")

            if len(row) != len(columns):
                raise ValueError(
                    f"Row {i} has {len(row)} columns, expected {len(columns)}"
                )

        super().__init__(columns=columns, rows=rows, name=name, description=description)

    def iter_as_dicts(self) -> Iterator[dict[str, RowValue]]:
        """
        Iterate over the rows of the table as dictionaries.

        Returns:
            An iterator over the rows of the table as dictionaries.
        """
        for row in self.rows:
            yield dict(zip(self.columns, row))

    def __len__(self) -> int:
        """
        Get the number of rows in the table.

        Returns:
            The number of rows in the table.
        """
        return len(self.rows)

    def __getitem__(self, index: int) -> Row:
        """
        Get a row from the table.

        Args:
            index: The index of the row to get.

        Returns:
            The row at the given index.
        """
        return self.rows[index]

    def get_row_as_dict(self, index: int) -> dict[str, RowValue]:
        """
        Get a row from the table as a dictionary.

        Args:
            index: The index of the row to get.

        Returns:
            The row at the given index as a dictionary.
        """
        return dict(zip(self.columns, self.rows[index]))

    def __str__(self):
        """
        Return a string representation of the table as markdown.
        """
        # First calculate max width needed for each column
        col_widths = [len(str(col)) for col in self.columns]
        for row in self.rows:
            for i, val in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(val)))

        # Build header row with column names
        header = f'| {" | ".join(str(col).ljust(width) for col, width in zip(self.columns, col_widths))} |'

        # Build separator row with alignment indicators
        separator = f"| {' | '.join('-' * (width-1) + ':'for width in col_widths)} |"

        # Build table string
        ret = []
        ret.append(header)
        ret.append(separator)

        # Add data rows
        for row in self.rows:
            row_str = f"| {' | '.join(str(val).ljust(width) for val, width in zip(row, col_widths))} |"
            ret.append(row_str)

        return "\n".join(ret)

    def __repr__(self):
        import json

        return f"Table(columns={json.dumps(self.columns, indent=4)}, rows={json.dumps(self.rows, indent=4)})"

    def model_dump(self, **kwargs):
        if "exclude_none" not in kwargs:
            # i.e.: keep backward compatibility with old behavior by default
            # as name and description were added.
            kwargs["exclude_none"] = True
        return super().model_dump(**kwargs)

    def model_dump_json(self, **kwargs):
        if "exclude_none" not in kwargs:
            # i.e.: keep backward compatibility with old behavior by default
            # as name and description were added.
            kwargs["exclude_none"] = True
        return super().model_dump_json(**kwargs)
