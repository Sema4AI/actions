"""
The data_sources.py is used to define both the datasources as well as the data server bootstrap.
"""

from typing import Annotated
from sema4ai.data import DataSource, DataSourceSpec

KnowledgeBaseStorageDataSource = Annotated[
    DataSource,
    DataSourceSpec(
        name="my_kb_storage",  # Change this to your PGVector Database name
        engine="pgvector",
        description="Data source for storing knowledge base content embeddings",
    )
]

KnowledgeBaseDataSource = Annotated[
    DataSource,
    DataSourceSpec(
        name="my_kb",  # Change this to your knowledge Base name
        engine="sema4_knowledge_base",
        description="Data source for knowledge base."
    )
]
########################################################
# To add the knowledge base data source, you need to 
# provide the following information:
# 1. The embedding model to use for generating the content embeddings
# 2. The reranking model to use for determining the relevance of the 
#    serach results
# 3. The pgvctor table to use for storing knowledge base content embeddings.
#    The table name should be prefixed with pgvector data source name.
#    Example: my_kb_storage.my_kb_embeddings.
# 4. The metadata columns for filtering the search results.
#    Example: src, category
# 5. The content column for generating the content embeddings.
#    Example: content
# 6. The id column for uniquely identifying the knowledge base records.
#    Example: id
########################################################
