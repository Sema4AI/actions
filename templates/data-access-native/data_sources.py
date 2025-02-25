"""
The data_sources.py is used to define both the datasources as well as the data server bootstrap.
"""

from typing import Annotated
from sema4ai.data import DataSource, DataSourceSpec

PostgresCustomersDataSource = Annotated[
    DataSource,
    DataSourceSpec(
        name="public_demo",
        engine="postgres",
        description="Contains DEMO customer information", # This will be visible for other configuring the connection
    )
]

# DEMO POSTGRES CONNECTION DETAILS
# 
# NAME:     public_demo
# HOST:     data-access-public-demo-instance-1.chai8y6e2qqq.us-east-2.rds.amazonaws.com
# PORT:     5432
# DATABASE: postgres
# USER:     demo_user
# PASSWORD: xyzxyzxyz
