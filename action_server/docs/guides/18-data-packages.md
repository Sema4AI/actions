# Data Packages

## Data Package Structure and Concepts

A `Data Package` structure is very similar to an `Action Package`.

Both have a `package.json` which describes the dependencies and how to bootstrap the environment and
can contain `@action`s.

The main difference from a `Data Package` to an `Action Package` is that a `Data Package` makes use of `sema4ai-data` to define
`Data Sources` and it can define `@query`s and `@predict`s (besides regular `@action`s) and the usage of `sema4ai-data`,
which is a different package than `sema4ai-action`.

The first important concept is a `Data Source` (provided by `sema4ai-data`).

In practical terms there are 2 kinds of `Data Source`s:

1. **External** `Data Sources`: In this case the `Data Source` defines a name and engine and that `Data Source` name
   maps directly to an existing database (such as Oracle, Postgres, etc).

   In this case, the connection information to connect to the database is required (and the connection details
   in production are usually different from development).

   In `sema4ai-data`, we'll just define a `name` and an `engine` in this use case, the connection details are
   expected to be provided directly to the server on the client being used (for instance, in VSCode it's expected
   that the `Sema4ai Data Extension` is opened and the `Data Source` connection is done directly inside it, whereas
   when deploying in `Control Room`, the information will be added at deployment time).

Example defining an **External** Data Source:

In a `data_sources.py` file:

```python
from typing import Annotated
from sema4ai.data import DataSource, DataSourceSpec

UsersDataSource = Annotated[
    DataSource,
    DataSourceSpec(
        name="users_database",
        engine="postgres",
        description="Datasource with users information",
    ),
]
```

2. **Generated** `Data Sources`: In this case all the information related to the `Data Source` is actually expected
   to be provide in the `Data Source` itself and it'll actually end up creating either a `table` or a `model`
   in the `Data Server`.

   These `Data Sources` are usually `files` or `models`.

   When a file is used, the `created_table` will need to be defined and when a model is used the `model_name` will
   need to be defined.

Example defining a table from a file:

In a `data_sources.py` file:

```python
from typing import Annotated
from sema4ai.data import DataSource, DataSourceSpec

FileChurnDataSource = Annotated[
    DataSource,
    DataSourceSpec(
        # Note: name  does not need to be defined for files engine (because in this case the data source name is always files)
        created_table="churn",
        file="files/customer-churn.csv",  # Path relative to the data package root
        engine="files",
        description="Datasource which provides a table named 'churn' with customer churn data.",
    ),
]
```

Example defining a model created (which uses the file above):

In a `data_sources.py` file:

```python
from typing import Annotated
from sema4ai.data import DataSource, DataSourceSpec

ChurnPredictionDataSource = Annotated[
    DataSource,
    DataSourceSpec(
        name="models",  # Note: name does not need to be defined for models engine (when `model_name` is defined the data source is `models` by default)
        model_name="customer_churn_predictor",
        engine="prediction:lightwood",
        description="Datasource which will create a table named `customer_churn_predictor` in the `my_models` project.",
        # The `models` name still needs to be referenced in the sql so that `customer_churn_predictor` is created inside of the `models` data source.
        setup_sql="""
            CREATE MODEL IF NOT EXISTS models.customer_churn_predictor
            FROM files
            (SELECT * FROM churn)
            PREDICT Churn;
    """,
    ),
]
```

## Using Data Sources

After defining the `Data Sources`, the referenced `Data Sources` will be available in methods decorated with `@query` and `@predict`.

Below is an example of a `@predict` method which will receive a `datasource` parameter and return a typed model
built from that `ResultSet`.

Note that any the received `datasource` would have access to any Data Source defined
in the `data_sources.py`, not just the `churn` and `files`, although in this example we type it accordingly to
signal the expected datasources (so, typing it directly as `DataSource` would have the same effect).

```python
from typing import Annotated

import pydantic
from sema4ai.data import DataSource, predict
from sema4ai.action import Response

from .data_sources import ChurnPredictionDataSource, FileChurnDataSource


class ChurnPredictionResult(pydantic.BaseModel):
    customer_id: str
    contract: str
    monthly_charges: float
    churn: bool



@predict
def predict_churn(
    datasource: ChurnPredictionDataSource | FileChurnDataSource,
    limit: int = 10,
) -> Response[list[ChurnPredictionResult]]:
    """
    Predict churn.

    Args:
        datasource: The datasource to use for the prediction.
        limit: The limit of predictions to get.

    Returns:
        A list of churn predictions.
    """
    sql = """
    SELECT t.customerID AS customer_id, t.Contract AS contract, t.MonthlyCharges AS monthly_charges, m.Churn AS churn
    FROM files.churn AS t
    JOIN simple_data_package_v1.customer_churn_predictor AS m
    LIMIT $limit;
    """

    result_set = datasource.query(sql, params={"limit": limit})
    return Response(result=result_set.build_list(ChurnPredictionResult))
```

Alternatively, instead of using `build_list`, it's possible to iterate the `ResultSet` to filter items as needed:

```python
@predict
def predict_churn(datasource: DataSource) -> Response[list[ChurnPredictionResult]]
    sql = ...
    result_set = datasource.query(sql, params={"limit": limit})
    results = []
    for entry_as_dict in result_set:
        if ...:
            results.append(ChurnPredictionResult(**entry_as_dict))
    return Response(result=results)
```

Note that the `ResultSet` returned from `datasource.query` has also other interesting methods:

- `to_table()`: would create a `Table` model (which may be returned directly as the result of the `@predict` method).
  -- This is useful when the shape of result of the query isn't known beforehand or if it's not interesting to define a custom model.

Example:

```python
@predict
def predict_churn(datasource: DataSource) -> Response[Table]
    sql = ...
    result_set = datasource.query(sql, params={"limit": limit})
    return Response(result=result_set.to_table())
```

- `to_dataframe()`: would create a `pandas.DataFrame` object.

Example:

```python
@predict
def predict_churn(datasource: DataSource) -> ...
    sql = ...
    result_set = datasource.query(sql, params={"limit": limit})
    as_pandas = result_set.to_dataframe()
    # Do something with the pandas DataFrame
```
