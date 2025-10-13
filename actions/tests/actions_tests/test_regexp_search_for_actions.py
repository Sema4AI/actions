import re

from sema4ai.actions._constants import REGEXP_TO_LOAD_FOR_DEFINITIONS


def test_should_match_decorators_with_parameters():
    """Test that the regex matches decorators that have parameters."""
    pattern = re.compile(REGEXP_TO_LOAD_FOR_DEFINITIONS)

    # Test with parentheses and parameters
    assert pattern.search("@action()")
    assert pattern.search("@tool(name='test')")
    assert pattern.search("@prompt(description='test prompt')")
    assert pattern.search("@resource(type='file')")
    assert pattern.search("@query(sql='SELECT * FROM table')")

    # Test namespaced decorators with parameters
    assert pattern.search("@actions.query(sql='SELECT * FROM table')")
    assert pattern.search("@actions.action(name='test')")
    assert pattern.search("@mcp.tool(name='test')")
    assert pattern.search("@mcp.prompt(description='test')")
    assert pattern.search("@mcp.resource(type='file')")

    assert pattern.search("DataSourceSpec(name='test')")


def test_should_not_match_invalid_patterns():
    """Test that the regex doesn't match invalid patterns."""
    pattern = re.compile(REGEXP_TO_LOAD_FOR_DEFINITIONS)

    # Test invalid decorators
    assert not pattern.search("@invalid")
    assert not pattern.search("@mcp.invalid")
    assert not pattern.search("@mcp")
    assert not pattern.search("@mcp.tooling")

    # Test similar but invalid patterns
    assert not pattern.search("@action_tool")

    # Test without @ symbol
    assert not pattern.search("action")
    assert not pattern.search("tool")
    assert not pattern.search("actions.query")
    assert not pattern.search("mcp.tool")


def test_should_match_all_expected_patterns():
    """Test that all expected decorator patterns are matched."""
    pattern = re.compile(REGEXP_TO_LOAD_FOR_DEFINITIONS)

    expected_decorators = [
        "@action",
        "@tool",
        "@prompt",
        "@resource",
        "@query",
        "@actions.query",
        "@actions.action",
        "@mcp.tool",
        "@mcp.prompt",
        "@mcp.resource",
    ]

    for decorator in expected_decorators:
        assert pattern.search(decorator), f"Failed to match: {decorator}"


def test_should_find_multiple_matches():
    """Test that the regex can find multiple matches in a string."""
    pattern = re.compile(REGEXP_TO_LOAD_FOR_DEFINITIONS)

    code_with_multiple = """
    @action
    def action1():
        pass
        
    @tool
    def tool1():
        pass
        
    @prompt
    def prompt1():
        pass
    """

    matches = pattern.findall(code_with_multiple)
    assert len(matches) == 3
    assert "action" in matches
    assert "tool" in matches
    assert "prompt" in matches
