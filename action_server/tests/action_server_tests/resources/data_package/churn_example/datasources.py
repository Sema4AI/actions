"""
The datasources.py is used to define both the datasources as well as the data server bootstrap.

The __action_server_metadata__.json (also obtained with the `action-server package metadata`)
will provide the data source specs as well as the data server bootstrap SQL commands so that
a separate tool can manage the database and make the current definitions active.

Expected commands in development:

<tool> bootstrap apply [--force] [--json] --metadata=<metadata.json path or stdin to use stdin to load metadata.json>

    Check if all the required datasources are setup already
        If some required datasource is not setup in mindsdb: error saying what is not properly setup
            (setup of required external datasources must be done externally through some UI)
    If required datasources are there:
        Goes through the bootstrap commands one by one.
            If it doesn't define the datasources it creates, just run the SQL as is.
            If the created datasource already exists, skip, unless the '--force' flag was passed
                If --force was passed, drops the generated datasource
            If the datasource is not there, run the SQL related to it.
                In each step the tool must check if there are no pending operations before proceeding to the next step
                    (ideally it should show progress output in stderr)

<tool> bootstrap drop [--json] --metadata=<metadata.json path or stdin to use stdin to load metadata.json>

    Drops all the "generated" datasources from the database.

"""

from typing import Annotated

from sema4ai.data import DataSource, DataSourceSpec

FileChurnDataSource = Annotated[
    DataSource,
    DataSourceSpec(
        created_table="churn",
        file="files/customer-churn.csv",  # Path relative to the data package root
        engine="files",  # Special use case: files engine == files name!
        description="Datasource which provides a table named 'churn' with customer churn data.",
    ),
]

ProjectDataSource = Annotated[
    DataSource,
    DataSourceSpec(
        name="simple_data_package_v1",
        engine="custom",
        description="Datasource which provides a project named `simple_data_package_v1`.",
        setup_sql="CREATE PROJECT IF NOT EXISTS simple_data_package_v1",
    ),
]


ChurnPredictionDataSource = Annotated[
    DataSource,
    DataSourceSpec(
        name="simple_data_package_v1",
        model_name="customer_churn_predictor",
        engine="prediction:lightwood",
        description="Datasource which provides a project named `simple_data_package_v1` along with a table named `customer_churn_predictor`.",
        setup_sql="""
            CREATE MODEL IF NOT EXISTS simple_data_package_v1.customer_churn_predictor
            FROM files
            (SELECT * FROM churn)
            PREDICT Churn;
    """,
    ),
]
