import pydantic
from sema4ai.data import predict

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
    datasource: ChurnPredictionDataSource | FileChurnDataSource,
    limit: int = 10,
) -> ChurnPredictionResultSet:
    """
    This is a simple query that joins the churn predictor with the churn data.

    Args:
        limit: The number of results to return.

    Returns:
        A list of churn predictions.
    """
    sql = """
    SELECT t.customerID AS customer_id, t.Contract AS contract, t.MonthlyCharges AS monthly_charges, m.Churn AS churn
    FROM files.churn AS t
    JOIN simple_data_package_v1.customer_churn_predictor AS m
    LIMIT $limit;
    """

    result = datasource.query(sql, params={"limit": limit})
    return ChurnPredictionResultSet(results=result.build_list(ChurnPredictionResult))
