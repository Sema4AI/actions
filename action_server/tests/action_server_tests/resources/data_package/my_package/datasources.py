from typing import Annotated

from sema4ai.data import DataSource, DataSourceSpec

SqliteTestDbDataSource = Annotated[
    DataSource,
    DataSourceSpec(
        name="sqlite-test-db",
        engine="sqlite",
        description="Datasource which provides a table named 'user_info' with information about users.",
    ),
]
