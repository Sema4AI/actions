from sema4ai.data import query

from .datasources import SqliteTestDbDataSource


@query
def query_userinfo(name: str, datasource: SqliteTestDbDataSource) -> str:
    """
    Query the user information for a user with the given name.

    Args:
        name: The name of the user to query.
        datasource: foobar

    Returns:
        The user information as a markdown table.
    """
    result = datasource.query("select * from user_info where name = ?", [name])
    return result.to_markdown()
