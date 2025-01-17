"""
The data_sources.py is used to define both the data sources as well as the data server bootstrap.
When you add new named queries, the data sources will be automatically added to this file.

TIP! Remember that the agent will only have access to the data sources that are defined in this file,
even though you might have configured some other data souces in your local data server.
"""

from typing import Annotated
from sema4ai.data import DataSource, DataSourceSpec

FileEnergyDataSource = Annotated[
    DataSource,
    DataSourceSpec(
        created_table="energy_consumption",
        file="files/energy_consumption.csv",
        engine="files",
        description="Energy comsumption data for industrial and residential customers.",
    ),
]

EnergyConsumptionModelDataSource = Annotated[
    DataSource,
    DataSourceSpec(
        name="models",
        model_name="energy_consumption_model",
        engine="prediction:lightwood",
        description="Please provide a description for this model",
        setup_sql="CREATE MODEL models.energy_consumption_model FROM files (SELECT * FROM energy_consumption) PREDICT energy_consumption USING engine = 'lightwood';",
    ),
]

FileCustomerDataSource = Annotated[
    DataSource,
    DataSourceSpec(
        created_table="customer_classification",
        file="files/customer_classification.csv",
        engine="files",
        description="Customer classification dataset.",
    ),
]

CustomerClassificationModelDataSource = Annotated[
    DataSource,
    DataSourceSpec(
        name="models",
        model_name="customer_classification_model",
        engine="prediction:lightwood",
        description="Please provide a description for this model",
        setup_sql="CREATE MODEL models.customer_classification_model FROM files (SELECT * FROM customer_classification) PREDICT Segmentation USING engine = 'lightwood';",
    ),
]

HouseSalesDataSource = Annotated[
    DataSource,
    DataSourceSpec(
        created_table="house_sales",
        file="files/house_sales.csv",
        engine="files",
        description="Datasource which provides a table named house_sales with data from a file.",
    ),
]

HouseSalesModelDataSource = Annotated[
    DataSource,
    DataSourceSpec(
        name="models",
        model_name="house_sales_model",
        engine="prediction:lightwood",
        description="Please provide a description for this model",
        setup_sql="CREATE MODEL models.house_sales_model FROM files (SELECT * FROM house_sales) PREDICT MA ORDER BY saledate GROUP BY bedrooms, type -- as the data is quarterly, look back two years to forecast the next one year WINDOW 8 HORIZON 4 -- use the statsforecast engine for this model USING engine = 'statsforecast';",
    ),
]