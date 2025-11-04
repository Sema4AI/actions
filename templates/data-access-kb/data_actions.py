from sema4ai.actions import Response, ActionError
from sema4ai.data import query, get_connection
from typing import Dict, Any, List
from models import (
    KnowledgeBaseInsertRequest,
    SearchRequest,
    AdvancedSearchRequest,
    RecordFilter,
    ListRequest,
    SearchResult,
)
from data_sources import KnowledgeBaseDataSource
import json


@query
def list_records(
    data_source: KnowledgeBaseDataSource, req: ListRequest
) -> Response[List[Dict[str, Any]]]:
    """
    List records in a knowledge base with optional filtering.

    Args:
        data_source: The knowledge base data source
        req: ListRequest containing filter and limit parameters

    Returns:
        Response containing list of records with their IDs, content,
        and metadata
    """
    # Build WHERE conditions if filters are specified
    where_conditions = []
    params = {"limit": req.limit}

    if req.filter:
        # Add record IDs filter if specified
        if req.filter.record_ids:
            placeholders = ", ".join([f"'{rid}'" for rid in req.filter.record_ids])
            where_conditions.append(f"id IN ({placeholders})")

        # Add metadata filters if specified
        if req.filter.metadata_filters:
            for column, value in req.filter.metadata_filters.items():
                where_conditions.append(f"{column} = ${column}")
                params[column] = value

    # Build the SQL query
    where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""

    sql = f"""
    SELECT *
    FROM sema4ai.{data_source.datasource_name}
    {where_clause}
    ORDER BY id
    LIMIT $limit
    """

    result = get_connection().query(sql, params=params)
    return Response(result=result.to_dict_list())


@query
def delete_records(
    data_source: KnowledgeBaseDataSource, req: RecordFilter
) -> Response[bool]:
    """
    Delete specific records from a knowledge base by their IDs and/or metadata.

    Args:
        data_source: The knowledge base data source
        req: RecordFilter containing list of record IDs and/or metadata
             filters to delete

    Returns:
        Response indicating success of the delete operation
    """
    # Build WHERE conditions based on available filters
    where_conditions = []
    params = {}

    # Add record IDs filter if specified
    if req.record_ids:
        placeholders = ", ".join([f"'{rid}'" for rid in req.record_ids])
        where_conditions.append(f"id IN ({placeholders})")

    # Add metadata filters if specified
    if req.metadata_filters:
        for column, value in req.metadata_filters.items():
            where_conditions.append(f"{column} = ${column}")
            params[column] = value

    # Ensure at least one filter is provided
    if not where_conditions:
        raise ActionError("No record IDs or metadata filters provided for deletion")

    where_clause = " AND ".join(where_conditions)

    sql = f"""
    DELETE FROM sema4ai.{data_source.datasource_name}
    WHERE {where_clause}
    """

    if params:
        get_connection().execute_sql(sql, params=params)
    else:
        get_connection().execute_sql(sql)

    return Response(result=True)


@query
def search(
    data_source: KnowledgeBaseDataSource, req: SearchRequest
) -> Response[List[SearchResult]]:
    """
    Search across the entire knowledge base.

    Args:
        data_source: The knowledge base data source
        req: SearchRequest containing query and search parameters

    Returns:
        Response containing search results with relevance scores
    """
    sql = f"""
    SELECT *
    FROM sema4ai.{data_source.datasource_name}
    WHERE content = $query
    AND relevance >= $relevance_threshold
    ORDER BY relevance DESC
    LIMIT $top_k
    """

    params = {
        "query": req.query,
        "relevance_threshold": req.relevance_threshold,
        "top_k": req.top_k,
    }

    result = get_connection().query(sql, params=params)
    # Convert the raw results to SearchResult objects
    search_results = [SearchResult(**row) for row in result.to_dict_list()]
    return Response(result=search_results)


@query
def advanced_search(
    data_source: KnowledgeBaseDataSource, req: AdvancedSearchRequest
) -> Response[List[SearchResult]]:
    """
    Advanced search with specific criteria like record IDs or metadata filters.

    Args:
        data_source: The knowledge base data source
        req: AdvancedSearchRequest containing search and filter parameters

    Returns:
        Response containing filtered search results with relevance scores
    """
    # Validate that at least one filter criteria is provided
    if not req.filter.record_ids and not req.filter.metadata_filters:
        raise ActionError(
            "No record IDs or metadata filters provided for advanced search"
        )

    # Build WHERE conditions using search parameters
    where_conditions = ["content = $query", "relevance >= $relevance_threshold"]
    params = {
        "query": req.search.query,
        "relevance_threshold": req.search.relevance_threshold,
        "top_k": req.search.top_k,
    }

    # Add record IDs filter if specified
    if req.filter.record_ids:
        placeholders = ", ".join([f"'{rid}'" for rid in req.filter.record_ids])
        where_conditions.append(f"id IN ({placeholders})")

    # Add metadata filters if specified
    if req.filter.metadata_filters:
        for column, value in req.filter.metadata_filters.items():
            where_conditions.append(f"{column} = ${column}")
            params[column] = value

    where_clause = " AND ".join(where_conditions)

    sql = f"""
    SELECT *
    FROM sema4ai.{data_source.datasource_name}
    WHERE {where_clause}
    ORDER BY relevance DESC
    LIMIT $top_k
    """

    result = get_connection().query(sql, params=params)
    # Convert the raw results to SearchResult objects
    search_results = [SearchResult(**row) for row in result.to_dict_list()]
    return Response(result=search_results)


@query
def get_metadata_columns(
    data_source: KnowledgeBaseDataSource,
) -> Response[Dict[str, Any]]:
    """
    Get the available metadata columns for a knowledge base.

    Args:
        data_source: The knowledge base data source

    Returns:
        Response containing metadata column information including column names
        and types
    """
    # Query to get metadata columns from information_schema
    sql = """
    SELECT metadata_columns
    FROM information_schema.knowledge_bases
    WHERE name = $datasource_name
    """

    result = get_connection().query(
        sql, params={"datasource_name": data_source.datasource_name}
    )

    if not result.to_dict_list():
        raise ActionError(
            f"No metadata columns found for knowledge base: "
            f"{data_source.datasource_name}"
        )

    # Debug: Let's see what we're getting back
    first_row = result.to_dict_list()[0]
    metadata_columns_raw = first_row.get("metadata_columns", {})

    # Handle case where metadata_columns might be a JSON string
    if isinstance(metadata_columns_raw, str):
        try:
            parsed_columns = json.loads(metadata_columns_raw)
            # Handle both array and dictionary formats
            if isinstance(parsed_columns, list):
                # If it's a list of column names, convert to dictionary
                # with column names as keys
                metadata_columns = {col: "string" for col in parsed_columns}
            elif isinstance(parsed_columns, dict):
                metadata_columns = parsed_columns
            else:
                metadata_columns = {}
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract column names from
            # the string. This handles cases where the string might contain
            # column information in a different format
            metadata_columns = {}
    else:
        # Handle case where it's already parsed
        if isinstance(metadata_columns_raw, list):
            metadata_columns = {col: "string" for col in metadata_columns_raw}
        elif isinstance(metadata_columns_raw, dict):
            metadata_columns = metadata_columns_raw
        else:
            metadata_columns = {}

    return Response(
        result={
            "datasource_name": data_source.datasource_name,
            "metadata_columns": metadata_columns,
            "available_columns": (
                list(metadata_columns.keys()) if metadata_columns else []
            ),
            "debug_info": {
                "raw_type": type(metadata_columns_raw).__name__,
                "raw_value": (
                    str(metadata_columns_raw)[:100] if metadata_columns_raw else None
                ),
            },
        }
    )


@query
def insert_records(
    data_source: KnowledgeBaseDataSource, req: KnowledgeBaseInsertRequest
) -> Response[bool]:
    """
    Insert multiple records into a knowledge base.

    Args:
        data_source: The knowledge base data source
        req: KnowledgeBaseInsertRequest containing records to insert and
             specific metadata columns.

    Returns:
        Response indicating success of the insert operation
    """
    if not req.records:
        raise ActionError("No records provided for insertion")

    # First, get the available metadata columns for this knowledge base
    metadata_columns_result = get_metadata_columns(data_source)
    available_columns = metadata_columns_result.result.get("available_columns", [])

    # Build the column list for the INSERT statement
    # Always include id and content, then add available metadata columns
    columns = ["id", "content"] + available_columns

    # Build placeholders for the VALUES clause
    placeholders = ["$id", "$content"] + [f"${col}" for col in available_columns]

    # Build the SQL with dynamic columns
    sql = f"""
    INSERT INTO sema4ai.{data_source.datasource_name} ({", ".join(columns)}) 
    VALUES ({", ".join(placeholders)})
    """

    # Execute each record as a separate statement with parameters
    for record in req.records:
        params = {"id": record.id, "content": record.content}

        # Add metadata values to their respective columns
        if record.metadata:
            for column in available_columns:
                params[column] = record.metadata.get(column)

        get_connection().execute_sql(sql, params=params)

    return Response(result=True)
