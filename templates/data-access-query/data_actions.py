from typing import Annotated
from sema4ai.actions import ActionError, Response
from sema4ai.data import DataSource, query
from data_sources import FileSalesDataSource, PostgresCustomersDataSource

# The first query is simple select targeting only one data source and has one
# parameter for country.
#
@query
def get_customers_in_country(
    country: str,
    datasource: PostgresCustomersDataSource) -> Response[str]:
    """
    Get all customer names, their id's and account managers in a given country.

    Args:
        country: Name of the country in english, for example "France"
        datasource: The customer datasource.
    Returns:
        Customers in the country as markdown.
    """

    sql = """
        SELECT company_name, customer_id, account_manager
        FROM public_demo.demo_customers
        WHERE country = $country
        LIMIT 100;
    """

    result = datasource.query(sql, params={"country": country})
    return Response(result=result.to_markdown())


# The second query is more complex and shows a real-world scenario with data validation and error
# handling. It also joins two data sources together in one SQL statement. It first makes a query
# to see how many companies are returned with search criteria, and then based on the results
# return either an error, or continues to perform the actual data query for monthly sales.
@query
def get_customers_orders_per_month(
    company_name: str,
    datasource: Annotated[DataSource, FileSalesDataSource | PostgresCustomersDataSource]) -> Response[str]:
    """
    Get one customer's aggregated order totals (sales) for all historic months.

    Args:
        company_name: Company name or part of it like "GermanSys"
        datasource: The customer datasource.
    Returns:
        Customers historic orders (sales) per month as markdown.
        If more than one company is found with the name, the action returns the list of all found companies to choose from.
    """

    sql = """
        SELECT customer_id, company_name
        FROM public_demo.demo_customers
        WHERE company_name LIKE CONCAT('%', $company, '%')
        LIMIT 100;
    """

    result = datasource.query(sql, params={"company": company_name})

    number_of_rows = len(tuple(result.iter_as_tuples()))
    if number_of_rows == 0:
        raise ActionError("No companies found with our criteria")

    elif number_of_rows > 1:
        raise ActionError(f"More than one company found with your criteria, here are all the found companies:\n\n{result.to_markdown()}")

    else:
        sql = """
            SELECT 
                DATE_TRUNC('month', CAST(s.sale_date AS DATE)) as month,
                ROUND(SUM(s.quantity_sold * s.price_per_unit), 2) as total_sales
            FROM files.sales_data s
            JOIN public_demo.demo_customers c
                ON s.customer_id = c.customer_id
            WHERE c.company_name LIKE CONCAT('%', $company, '%')
            GROUP BY DATE_TRUNC('month', CAST(s.sale_date AS DATE))
            ORDER BY 1;
        """

        result = datasource.query(sql, params={"company": company_name})
        return Response(result=result.to_markdown())