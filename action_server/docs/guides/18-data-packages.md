# Data Packages

## Data Package Structure and Concepts

A `Data Package` structure is very similar to an `Action Package`.

Both have a `package.json` which describes the dependencies and how to bootstrap the environment and
can contain `@action`s.

The main difference from a `Data Package` to an `Action Package` is that a `Data Package` makes use of `sema4ai-data` to define
`Data Sources` and it can define `@query`s (besides regular `@action`s) and the usage of `sema4ai-data`,
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
