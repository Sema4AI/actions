from sema4ai.actions import Response, Table
from sema4ai.data import query
from data_sources import PostgresCustomersDataSource


@query
def search_customers_per_country_substring(
    search_string: str, datasource: PostgresCustomersDataSource
) -> Response[Table]:
    """
    Search for customers in a country containing the search string.

    Args:
        search_string: The substring to search for in the country name, for example "er"

    Returns:
        List of all customers and their data
    """

    sql = """
    SELECT *
    FROM demo_customers
    WHERE country ~* $search_string;
    """

    result = datasource.native_query(sql, params={"search_string": search_string})
    return Response(result=result.to_table())
