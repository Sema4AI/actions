# Note: besides the types supported here, pydantic is also supported
# by checking duck-typing for the APIs below:
#
# `cls.model_validate(dict)`
# `cls.model_json_schema(by_alias=False)`
# `obj.model_dump(mode="json")`
SUPPORTED_TYPES_IN_SCHEMA = (str, int, float, bool)

# Search for all files by default now (and filter based on the contents of the regexp below)
DEFAULT_ACTION_SEARCH_GLOB = "*"

# Search (with regexp) for `@action`,  `@query`, `@tool`, `@prompt`, `@resource`,
# `@actions.query`, `@actions.action`,
# `@mcp.tool`, `@mcp.prompt`, `@mcp.resource`
# DataSourceSpec
REGEXP_TO_LOAD_FOR_DEFINITIONS = (
    r"@("
    # Actions:
    r"\baction\b|"
    r"\bquery\b|"
    # MCP:
    r"\btool\b|"
    r"\bprompt\b|"
    r"\bresource\b|"
    # Actions with dot notation:
    r"\bactions\.query\b|"
    r"\bactions\.action\b|"
    # MCP with dot notation:
    r"\bmcp\.tool\b|"
    r"\bmcp\.prompt\b|"
    r"\bmcp\.resource\b|"
    # Data source definitions:
    r"\bDataSourceSpec\b"
    r")"
)

MODULE_ENTRY_POINT = "sema4ai.actions"
