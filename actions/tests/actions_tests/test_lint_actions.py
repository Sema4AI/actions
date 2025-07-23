import os
from pathlib import Path
from typing import Any

import pytest


def test_lint_action_no_docstring(data_regression):
    from sema4ai.actions._lint_action import iter_lint_errors

    contents = """
@action
def my_action():
    pass
"""

    data_regression.check([x.to_lsp_diagnostic() for x in iter_lint_errors(contents)])


def test_lint_action_no_docstring_in_query_and_predict(data_regression):
    from sema4ai.actions._lint_action import iter_lint_errors

    contents = """
@query
def my_action():
    pass

@predict
def my_action():
    pass
"""

    data_regression.check([x.to_lsp_diagnostic() for x in iter_lint_errors(contents)])


def test_lint_action_docstring_not_matching(data_regression):
    from sema4ai.actions._lint_action import iter_lint_errors

    contents = """
@action
def my_action(param1: str) -> str:
    '''
    Empty docstring?
    '''
    return ''
"""

    data_regression.check([x.to_lsp_diagnostic() for x in iter_lint_errors(contents)])

    contents = """
@actions.action
def my_action(param1: str) -> str:
    '''
    Empty docstring?
    '''
    return ''
"""

    data_regression.check([x.to_lsp_diagnostic() for x in iter_lint_errors(contents)])


def test_lint_action_no_description(data_regression):
    from sema4ai.actions.api import collect_lint_errors

    contents = """
@action
def my_action(param1) -> str:
    '''
    Args:
        param1: Some value.
    '''
    return ''
"""

    data_regression.check(collect_lint_errors(contents))


def test_lint_action_argument_untyped(data_regression):
    from sema4ai.actions._lint_action import iter_lint_errors

    contents = """
@action
def my_action(param1) -> str:
    '''
    Some Action.

    Args:
        param1: Some value.
    '''
    return ''
"""

    data_regression.check([x.to_lsp_diagnostic() for x in iter_lint_errors(contents)])


def test_lint_action_with_is_consequential(data_regression):
    from sema4ai.actions._lint_action import iter_lint_errors

    contents = """
from sema4ai.actions import action

@action(is_consequential=True)
def my_action(param1: str) -> str:
    '''
    Some Action.
    '''
    return ''
"""

    data_regression.check([x.to_lsp_diagnostic() for x in iter_lint_errors(contents)])


def test_lint_action_big_description(data_regression, monkeypatch):
    from sema4ai.actions._lint_action import iter_lint_errors

    monkeypatch.setattr("sema4ai.actions._lint_action.MAX_DOCS_LENGTH", 300)

    contents = """
@action
def my_action() -> str:
    '''
    This description is too big. OpenAI just supports 300 hundred chars in desc.
    This description is too big. OpenAI just supports 300 hundred chars in desc.
    This description is too big. OpenAI just supports 300 hundred chars in desc.
    This description is too big. OpenAI just supports 300 hundred chars in desc.
    This description is too big. OpenAI just supports 300 hundred chars in desc.
    '''
    return ''
"""

    data_regression.check([x.to_lsp_diagnostic() for x in iter_lint_errors(contents)])


def clean_filename_to_basename(obj: Any) -> Any:
    # Any dict with a key `file` will have the value of the key `file` replaced with the basename of the file.
    if isinstance(obj, dict):
        if "file" in obj:
            obj["file"] = os.path.basename(obj["file"])
        return {k: clean_filename_to_basename(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_filename_to_basename(x) for x in obj]
    return obj


def find_issues_in_actions_list(datadir: Path, contents: str) -> list:
    import json

    from devutils.fixtures import sema4ai_actions_run

    cwd = datadir / "cwd"
    os.makedirs(cwd)
    act = cwd / "act.py"
    act.write_text(contents)

    result = sema4ai_actions_run(["list"], returncode="any", cwd=str(cwd))
    try:
        found = json.loads(result.stdout)
    except Exception:
        raise RuntimeError(
            f"stdout: {result.stdout.decode('utf-8')}\nstderr: {result.stderr.decode('utf-8')}"
        )

    if isinstance(found, dict):
        lint_result = found.get("lint_result", [])
        return clean_filename_to_basename(lint_result)
    return []


def test_lint_action_integrated(datadir, data_regression):
    import json

    from devutils.fixtures import sema4ai_actions_run

    result = sema4ai_actions_run(["list"], returncode="error", cwd=str(datadir))
    try:
        found = json.loads(result.stdout)
    except Exception:
        raise RuntimeError(
            f"stdout: {result.stdout.decode('utf-8')}\nstderr: {result.stderr.decode('utf-8')}"
        )

    lint_result = found["lint_result"]
    new_dict = {}
    for k, v in lint_result.items():
        if k == "file":
            new_dict[k] = os.path.basename(v)
        else:
            new_dict[k] = v

    data_regression.check(new_dict)


def test_lint_action_secret(data_regression, datadir):
    from sema4ai.actions._customization._extension_points import EPManagedParameters
    from sema4ai.actions._customization._plugin_manager import PluginManager
    from sema4ai.actions._lint_action import iter_lint_errors
    from sema4ai.actions._managed_parameters import ManagedParameters

    contents = """
from sema4ai.actions import Secret, action
from sema4ai import actions

@action
def my_action(my_password: Secret, another: actions.Secret) -> str:
    '''
    This is an action.
    '''
    return ''
"""

    pm = PluginManager()
    pm.set_instance(EPManagedParameters, ManagedParameters({}))
    data_regression.check(
        [x.to_lsp_diagnostic() for x in iter_lint_errors(contents, pm=pm)]
    )

    issues = find_issues_in_actions_list(datadir, contents)
    data_regression.check(issues, basename="test_lint_action_secret_list_issues")


def test_lint_action_oauth2_secret(data_regression, datadir):
    from sema4ai.actions._customization._extension_points import EPManagedParameters
    from sema4ai.actions._customization._plugin_manager import PluginManager
    from sema4ai.actions._lint_action import iter_lint_errors
    from sema4ai.actions._managed_parameters import ManagedParameters

    contents = """
from typing import Literal

from sema4ai import actions
from sema4ai.actions import OAuth2Secret


@actions.action
def my_action(
    another: actions.OAuth2Secret[
        Literal["google"], list[Literal["readscope", "writescope"]]
    ],
) -> str:
    '''
    This is an action.
    '''
    return ""
"""

    pm = PluginManager()
    pm.set_instance(EPManagedParameters, ManagedParameters({}))
    data_regression.check(
        [x.to_lsp_diagnostic() for x in iter_lint_errors(contents, pm=pm)]
    )

    issues = find_issues_in_actions_list(datadir, contents)
    data_regression.check(issues, basename="test_lint_action_oauth2_secret_list_issues")


@pytest.mark.parametrize("scenario", ["simple", "inline", "union"])
def test_lint_data_source_docstring_not_required(data_regression, datadir, scenario):
    from sema4ai.actions._customization._extension_points import EPManagedParameters
    from sema4ai.actions._customization._plugin_manager import PluginManager
    from sema4ai.actions._lint_action import iter_lint_errors
    from sema4ai.actions._managed_parameters import ManagedParameters

    if scenario == "simple":
        contents = """
from typing import Literal

from sema4ai import actions
from typing import Annotated
from sema4ai.data import DataSource, DataSourceSpec, query

MyDataSource = Annotated[DataSource, DataSourceSpec(
    name="MyDataSourceSpec",
    engine="postgres",
    description="My Data Source"
)]


@query
def my_action(
    datasource: MyDataSource
) -> str:
    '''
    This is an action with a data source.
    '''
    return ""
"""
    elif scenario == "inline":
        contents = """
from typing import Literal

from sema4ai import actions
from typing import Annotated
from sema4ai.data import DataSource, DataSourceSpec, query

@query
def my_action(
    datasource: Annotated[DataSource, DataSourceSpec(
        name="MyDataSourceSpec",
        engine="postgres",
        description="My Data Source"
    )]
) -> str:
    '''
    This is an action with a data source.
    '''
    return ""
"""
    elif scenario == "union":
        contents = """
from typing import Literal

from sema4ai import actions
from typing import Annotated
from sema4ai.data import DataSource, DataSourceSpec, query

@query
def my_action(
    datasource: Annotated[DataSource, DataSourceSpec(
        name="MyDataSourceSpec",
        engine="postgres",
        description="My Data Source"
    )] | Annotated[DataSource, DataSourceSpec(
        name="MyDataSourceSpec",
        engine="postgres",
        description="My Data Source"
    )]
) -> str:
    '''
    This is an action with a data source.
    '''
    return ""
"""
    else:
        raise ValueError(f"Invalid scenario: {scenario}")

    pm = PluginManager()
    pm.set_instance(EPManagedParameters, ManagedParameters({}))
    data_regression.check(
        [x.to_lsp_diagnostic() for x in iter_lint_errors(contents, pm=pm)]
    )
