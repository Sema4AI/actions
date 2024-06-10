import inspect
import json
import sys
from concurrent.futures.thread import ThreadPoolExecutor

from sema4ai.action_server._selftest import ActionServerClient, ActionServerProcess


def test_return_response_ok_action(
    action_server_process: ActionServerProcess,
    client: ActionServerClient,
    datadir,
):
    def case1():
        # ---------- case bad schema
        response = client.post_error(
            "api/actions/test-server-response/bad-schema/run",
            500,
            {},
        )
        found = json.loads(response.text)
        assert found == {
            "error_code": "internal-error",
            "message": "Inconsistent value returned from action: data must be object -- i.e.: the returned value (1) does not match the expected output schema ({'properties': {'result': {'anyOf': [{'type': 'string'}, {'type': 'null'}], 'default': None, 'description': 'The result for the action if it ran successfully', 'title': 'Result'}, 'error': {'anyOf': [{'type': 'string'}, {'type': 'null'}], 'default': None, 'description': 'The error message if the action failed for some reason', 'title': 'Error'}}, 'title': 'Response[str]', 'type': 'object'}).",
        }

    def case2():
        # ---------- case without response (action error)
        response = client.post_error(
            "api/actions/test-server-response/raise-action-error-action-not-response/run",
            500,
            {},
        )
        found = json.loads(response.text)
        assert found == {"error_code": "internal-error", "message": "Action error"}

    def case3():
        # ---------- case without response (other error)
        response = client.post_error(
            "api/actions/test-server-response/raise-action-error-other-not-response/run",
            500,
            {},
        )
        found = json.loads(response.text)
        assert found == {
            "error_code": "internal-error",
            "message": "Unexpected error (RuntimeError)",
        }

    def case4():
        # ---------- all ok
        found = client.post_get_str(
            "api/actions/test-server-response/return-response-ok-action/run",
            {},
        )
        found = json.loads(found)
        assert found == {"result": {"show": False}, "error": None}

    def case5():
        # ---------- return is a response with an error
        found = client.post_get_str(
            "api/actions/test-server-response/return-response-error-action/run",
            {},
        )
        found = json.loads(found)
        assert found == {"result": None, "error": "Something bad happened"}

    def case6():
        # ---------- unexpected exception raised
        found = client.post_get_str(
            "api/actions/test-server-response/raise-other-error-action/run",
            {},
        )
        found = json.loads(found)
        assert found == {"result": None, "error": "Unexpected error (RuntimeError)"}

    def case7():
        # ---------- exception raised with an 'Action error' message
        found = client.post_get_str(
            "api/actions/test-server-response/raise-action-error-action/run",
            {},
        )
        found = json.loads(found)
        assert found == {"result": None, "error": "Action error"}

    # Running all in parallel is faster
    check_cases = [
        val
        for name, val in sys._getframe().f_locals.items()
        if inspect.isfunction(val) and name.startswith("case")
    ]

    action_server_process.start(
        cwd=datadir,
        actions_sync=True,
        lint=False,
        db_file="server.db",
        reuse_processes=True,
        min_processes=1,
        max_processes=len(check_cases),
    )

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(func) for func in check_cases]

        for future in futures:
            assert future.result() is None

    executor.shutdown(wait=False)


def test_action_package_json(
    action_server_process: ActionServerProcess, client: ActionServerClient, tmpdir
):
    from pathlib import Path

    calculator = Path(tmpdir) / "calculator" / "action_calculator.py"
    calculator.parent.mkdir(parents=True, exist_ok=True)
    calculator.write_text(
        """
from sema4ai.actions import action, Response
from pydantic import BaseModel, Extra
from datetime import datetime

class Document(BaseModel, extra=Extra.ignore):
    title: str
    document_id: str
    date: datetime
    

@action
def calculator_sum(v1: float, v2: float) -> Response[Document]:
    return Response(result=Document(
        title="asd123", 
        document_id="Some Document ID", 
        date=datetime.now()))
"""
    )

    action_server_process.start(
        actions_sync=True, cwd=Path(tmpdir / "calculator"), db_file="server.db"
    )
    found = client.post_get_str(
        "api/actions/calculator/calculator-sum/run", {"v1": 1.0, "v2": 2.0}
    )
    print(found)
