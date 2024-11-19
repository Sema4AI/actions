from typing import Annotated

import pydantic
from sema4ai.data import DataSource, predict

from .datasources import ChurnPredictionDataSource, FileChurnDataSource


class ChurnPredictionResult(pydantic.BaseModel):
    customer_id: str
    contract: str
    monthly_charges: float
    churn: bool


class ChurnPredictionResultSet(pydantic.BaseModel):
    results: list[ChurnPredictionResult]


@predict
def predict_churn(
    datasource: Annotated[DataSource, ChurnPredictionDataSource | FileChurnDataSource],
    limit: int = 10,
) -> ChurnPredictionResultSet:
    sql = """
    SELECT t.customerID AS customer_id, t.Contract AS contract, t.MonthlyCharges AS monthly_charges, m.Churn AS churn
    FROM files.churn AS t
    JOIN simple_data_package_v1.customer_churn_predictor AS m
    LIMIT $limit;
    """

    result = datasource.query(sql, params={"limit": limit})
    return ChurnPredictionResultSet(results=result.build_list(ChurnPredictionResult))
