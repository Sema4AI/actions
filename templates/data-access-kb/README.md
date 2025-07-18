# Template: Knowledge Base Access

This template provides a quick way to get started with Sema4.ai Knowledge Base operations. It contains all the necessary files, data sources, and actions to interact with knowledge bases for storing and retrieving content with semantic search capabilities.

## Prerequisites

1. A PostgreSQL database with the `pgvector` extension is required to use this template. This enables storage and search of vector embeddings for semantic search capabilities.
2. Embedding and LLM model from providers like OpenAI, Azure. This enables generation of vector embeddings for knowledge base content and search queries and filtering relevant results. 

## Getting Started

### 1. Configure Your Knowledge Base

Start by editing the PGVector data source name and knowledge base name in `data_sources.py`:

```python
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
```

### 2. Setting Up Data Sources in VS Code

Using the Sema4.ai SDK VS Code extension:

1. Expand `MyActions > Knowledge Base Access > Data Sources` in the extension sidebar.
2. Review the list of data sources use the `[+]` button to set up each data source as needed, following the prompts to configure connection details.

### 3. Available Actions

Review the actions available in `data_actions.py` to understand what operations you can perform:

#### Core Operations:
- **`list_records`** - Retrieve records from your knowledge base with optional filtering by record IDs, metadata, and limit
- **`insert_records`** - Add new records with content and metadata to your knowledge base
- **`delete_records`** - Remove records by their IDs and/or metadata filters

#### Search Operations:
- **`search`** - Basic semantic search across your knowledge base with relevance scoring
- **`advanced_search`** - Advanced search with filters for specific record IDs or metadata
- **`get_metadata_columns`** - Discover available metadata columns in your knowledge base

### 3. Usage Examples

The template includes Pydantic models in `models.py` that define the structure for:
- Knowledge base records with content and metadata
- Search requests with relevance thresholds
- Advanced search with filtering options
- List and Delete requests with filtering options

Also refer to devdata to see the sample inputs that can be provided to actions.

👉 Check [Action Server](https://github.com/Sema4AI/actions/tree/master/action_server/docs) and [Actions](https://github.com/Sema4AI/actions/tree/master/actions/docs) docs for more information.