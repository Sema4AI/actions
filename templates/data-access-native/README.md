# Template: Data Access Native Queries

This template shows Sema4.ai Data Access in action using Native Queries. It contains necessary files, data sources and follows the required structure to get started with queries against external data sources.

In the Sema4.ai Data Server, you can execute native SQL queries specific to your database engine, providing flexibility and control over your data operations and bypassing the federeted query engine.This allows you to run more complex queries using platform specific features. Rear more about Native Queries in [docs](https://sema4.ai/docs/solutions/data-access/queries#native-queries).

## Explainer

The key to running native queries are the following lines in the `data_action.py` file. This is a query that would not work with Data Server's federated SQL dialect due to string comparison `~*` used in the WHERE clause - that's Postgres specific syntax.

```python
    sql = """
    SELECT *
    FROM demo_customers
    WHERE country ~* $search_string;
    """

    result = datasource.native_query(sql, params={"search_string": search_string})
```

This example uses the give `sql` statement, and looks at the active `datasource`. As in our example it's called `public_demo`, effectively this query will be executed assuming that `search_string` is `er`:

```sql
SELECT * FROM public_demo (
    SELECT *
    FROM demo_customers
    WHERE country ~* 'er'
);
```

With native queries is important to remember that you always execute queries in the namespace of the datasource, so in this case adding database name `public_demo` to your FROM clause is not needed - and it would not even work.

## Demo PostgreSQL connection details

Template builds on a demo PostgreSQL database, which everyone can access (read only) using these details:

- **NAME**: public_demo
- **HOST**: data-access-public-demo-instance-1.chai8y6e2qqq.us-east-2.rds.amazonaws.com
- **PORT**: 5432
- **DATABASE**: postgres
- **USER**: demo_user
- **PASSWORD**: xyzxyzxyz

## Limitations

The named query creation tool include in the Data Access VS Code Extension does NOT yet support creating native named queries with the UI-based workflow. It means that you need to create the native queries by writing `@query` Python code manually (or AI assisted).