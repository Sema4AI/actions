from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, List, Optional, Annotated


class KnowledgeBaseRecord(BaseModel):
    """Model for a single record in the knowledge base."""
    id: Annotated[str, Field(description="Unique identifier for the record")]
    content: Annotated[str, Field(description="Main content of the record")]
    metadata: Annotated[Optional[Dict[str, Any]], Field(
        description="Optional metadata for the record"
    )] = None


class KnowledgeBaseInsertRequest(BaseModel):
    """Model for inserting multiple records into the knowledge base."""
    records: Annotated[List[KnowledgeBaseRecord], Field(
        description="List of records to insert into the knowledge base"
    )]


class SearchRequest(BaseModel):
    """Model for search requests."""
    query: Annotated[str, Field(description="Search query text")]
    top_k: Annotated[int, Field(
        description="Number of results to return"
    )] = 10
    relevance_threshold: Annotated[float, Field(
        description="Minimum relevance score for results"
    )] = 0.5


class RecordFilter(BaseModel):
    """Model for filtering records by ID and/or metadata."""
    record_ids: Annotated[Optional[List[str]], Field(
        description="List of record IDs to filter (optional)"
    )] = None
    metadata_filters: Annotated[Optional[Dict[str, str]], Field(
        description="Metadata filters to apply (optional)"
    )] = None

    @field_validator('record_ids', 'metadata_filters', mode='before')
    @classmethod
    def convert_empty_strings_to_none(cls, v):
        """Convert empty strings to None for optional fields."""
        if v == "":
            return None
        return v


class ListRequest(BaseModel):
    """Model for listing records with optional filtering and limit."""
    filter: Annotated[Optional[RecordFilter], Field(
        description="Record filtering options (optional)"
    )] = None
    limit: Annotated[int, Field(
        description="Maximum number of records to return"
    )] = 100

    @field_validator('filter', mode='before')
    @classmethod
    def convert_empty_strings_to_none(cls, v):
        """Convert empty strings to None for optional fields."""
        if v == "":
            return None
        return v


class AdvancedSearchRequest(BaseModel):
    """Model for advanced search requests with filters."""
    search: Annotated[SearchRequest, Field(
        description="Basic search parameters"
    )]
    filter: Annotated[RecordFilter, Field(
        description="Record filtering options"
    )]

    @field_validator('filter', mode='before')
    @classmethod
    def convert_empty_strings_to_none(cls, v):
        """Convert empty strings to None for optional fields."""
        if v == "":
            return None
        return v


class SearchResult(BaseModel):
    """Model for search result items."""
    id: Annotated[str, Field(description="Unique identifier for the record")]
    chunk_id: Annotated[str, Field(description="Chunk identifier")]
    chunk_content: Annotated[str, Field(description="Content of the chunk")]
    metadata: Annotated[str, Field(description="Metadata as JSON string")]
    distance: Annotated[float, Field(description="Distance score from search")]
    relevance: Annotated[float, Field(description="Relevance score")] 