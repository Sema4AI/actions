import datetime
import json
import logging
import time
import typing
from typing import Any, Callable, Dict, Tuple

from fastapi import HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from starlette.concurrency import run_in_threadpool

if typing.TYPE_CHECKING:
    from ._models import Action, ActionPackage, Run

log = logging.getLogger(__name__)


# Note: for pydantic models, the following APIs are used:
# cls.model_validate(dict)
# cls.model_json_schema(by_alias=False)
# obj.model_dump(mode="json")
#
# Besides pydantic, the following basic types are accepted:
_spec_api_type_to_python_type = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
}


def _create_run_artifacts_dir(action: "Action", run_id: str) -> str:
    """
    Returns:
        The path, relative to the settings.artifacts_dir which should be used
        to store the output of the given run.
    """
    from ._settings import get_settings

    settings = get_settings()
    artifacts_dir = settings.artifacts_dir
    path = run_id
    target_dir = artifacts_dir / path
    target_dir.mkdir(parents=True, exist_ok=False)
    return path


def _create_run(
    action: "Action",
    run_id: str,
    inputs: dict,
    relative_artifacts_dir: str,
    request_id: str,
) -> "Run":
    from sema4ai.action_server._models import RUN_ID_COUNTER, Counter

    from ._database import datetime_to_str
    from ._models import Run, RunStatus, get_db
    from ._runs_state_cache import get_global_runs_state

    db = get_db()
    run_kwargs: Dict[str, Any] = dict(
        id=run_id,
        status=RunStatus.NOT_RUN,
        action_id=action.id,
        start_time=datetime_to_str(datetime.datetime.now(datetime.timezone.utc)),
        run_time=None,
        inputs=json.dumps(inputs),
        result=None,
        error_message=None,
        relative_artifacts_dir=relative_artifacts_dir,
        request_id=request_id,
    )
    with db.transaction():
        if not db.in_transaction():
            db.execute("BEGIN")
        try:
            with db.cursor() as cursor:
                db.execute_update_returning(
                    cursor,
                    "UPDATE counter SET value=value+1 WHERE id=? RETURNING value",
                    [RUN_ID_COUNTER],
                )
                counter_record = cursor.fetchall()
                if not counter_record:
                    raise RuntimeError(
                        f"Error. No counter found for run_id. Counters in db: {db.all(Counter)}"
                    )
                run_kwargs["numbered_id"] = counter_record[0][0]

            run = Run(**run_kwargs)
            db.insert(run)
            db.execute("COMMIT")
        except Exception:
            db.execute("ROLLBACK")
            raise

    # Ok, transaction finished properly. Let's add it to our in-memory cache.
    global_runs_state = get_global_runs_state()
    global_runs_state.on_run_inserted(run)

    return run


def _update_run(run: "Run", initial_time: float, run_finished: bool, **changes):
    from ._models import get_db
    from ._runs_state_cache import get_global_runs_state

    if run_finished:
        changes["run_time"] = time.monotonic() - initial_time

    db = get_db()
    for k, v in changes.items():
        setattr(run, k, v)
    fields_changed = tuple(changes.keys())
    log.info(f"Updating run {run.id} with changes: {json.dumps(changes, indent=2)}")
    with db.transaction():
        db.update(run, *fields_changed)

    # Ok, transaction finished properly. Let's update our in-memory cache.
    global_runs_state = get_global_runs_state()
    global_runs_state.on_run_changed(run, changes)


def _set_run_as_finished_ok(run: "Run", result: str, initial_time: float) -> int:
    from ._models import RunStatus

    _update_run(run, initial_time, True, result=result, status=RunStatus.PASSED)
    return RunStatus.PASSED


def _set_run_as_finished_failed_with_response(
    run: "Run", result: str, initial_time: float
) -> int:
    from ._models import RunStatus

    _update_run(run, initial_time, True, status=RunStatus.FAILED, result=result)
    return RunStatus.FAILED


def _set_run_as_finished_cancelled(
    run: "Run", error_message: str, initial_time: float
) -> int:
    from ._models import RunStatus

    _update_run(
        run, initial_time, True, status=RunStatus.CANCELLED, error_message=error_message
    )
    return RunStatus.CANCELLED


def _set_run_as_finished_failed(
    run: "Run", error_message: str, initial_time: float
) -> int:
    from ._models import RunStatus

    _update_run(
        run, initial_time, True, status=RunStatus.FAILED, error_message=error_message
    )
    return RunStatus.FAILED


def _set_run_as_running(run: "Run", initial_time: float) -> int:
    from ._models import RunStatus

    _update_run(run, initial_time, False, status=RunStatus.RUNNING)
    return RunStatus.RUNNING


class _ActionsRunner:
    """
    This is where the user actually runs something.

    Most methods run in a thread (so, be careful when talking to the database).

    We have to take care of making a run with the proper environment,
    creating the run, collecting output info, etc.
    """

    def __init__(
        self,
        action_package: "ActionPackage",
        action: "Action",
        input_schema_dict: dict,
        output_schema_dict: dict,
        input_validator: Callable[[dict], None],
        output_validator: Callable[[dict], None],
        inputs: dict,
        response: Response,
        headers: dict,
        cookies: dict,
    ) -> None:
        """
        Constructor. Still running in the main thread.
        """
        from concurrent.futures import Future
        from typing import Optional

        from sema4ai.action_server._gen_ids import gen_uuid
        from sema4ai.action_server._models import Run

        self.action_package = action_package
        self.action = action
        self.input_schema_dict = input_schema_dict
        self.output_schema_dict = output_schema_dict
        self.input_validator = input_validator
        self.output_validator = output_validator
        self.inputs = inputs
        self.response = response
        self.headers = headers
        self.cookies = cookies

        timeout = headers.get("x-actions-async-timeout", None)
        if timeout is not None:
            timeout = float(timeout)

        self.request_id: str = headers.get("x-actions-request-id", "")
        self.timeout: Optional[float] = timeout
        self.callback_url: Optional[str] = headers.get("x-actions-async-callback", None)
        self._future: Optional[Future] = None
        self._run_id = gen_uuid("run")
        self._returning_async_result = False
        self._run_status: Optional[int] = None

        self._relative_artifacts_path: str = _create_run_artifacts_dir(
            action, self._run_id
        )

        # The run is created right away so that new queries related to
        # this run will be able to find it (for instance, to cancel it
        # or get the run id from the request id).
        self._run: Run = _create_run(
            action,
            self._run_id,
            inputs,
            self._relative_artifacts_path,
            request_id=self.request_id,
        )

    def run_in_thread(self) -> Any:
        """
        This is where the action is actually run.

        This runs in a thread and spawns a new thread to actually run the
        action (this 2-thread approach is required because we need to be able
        to return to the client while the action is still running in the
        background).

        We have to take care of making a run with the proper environment,
        creating the run, collecting output info, etc.

        The return value is the result of the action (and is what will be
        returned to the client) or a return signalling that it's an async
        return (while the action is still running in the background).
        """
        assert self._future is None, "Future already set"
        from concurrent.futures import TimeoutError

        from sema4ai.action_server._robo_utils import run_in_thread

        self.response.headers["X-Action-Server-Run-Id"] = self._run_id

        fut = run_in_thread.run_in_thread(self._run_action)
        self._future = fut

        if self.timeout is None:
            # Wait for the future to be resolved.
            return fut.result()

        if self.timeout == 0:
            # Return immediately.
            return self._async_result()

        try:
            return fut.result(self.timeout)
        except TimeoutError:
            return self._async_result()

    def _async_result(self) -> Any:
        self._returning_async_result = True
        self.response.headers["x-action-async-completion"] = "1"
        return "async-return"

    def _run_action(self) -> Any:
        """
        This is where the action is actually run (to completion).

        If the action is async and the timeout for the async return
        was reached, this will call the callback url with the result.

        Returns:
            The result of the action.
        """
        # Before even running the action, validate the inputs.
        inputs: dict = self.inputs
        input_validator: Callable[[dict], None] = self.input_validator
        try:
            input_validator(inputs)
        except Exception as e:
            raise RequestValidationError(
                [
                    f"The received input arguments (sent in the body) do not conform to the expected API. Details: {e}"
                ]
            )

        result = self._run_action_impl()
        if self._returning_async_result:
            # We're returning an async result, so, we need to call the callback.
            if self.callback_url:
                post_result = None
                try:
                    import sema4ai_http

                    headers: dict[str, str] = {
                        "x-action-server-run-id": self._run_id,
                    }

                    if self.request_id:
                        headers["x-actions-request-id"] = self.request_id

                    for _i in range(3):  # Try up to 3 times before giving up.
                        post_result = sema4ai_http.post(
                            self.callback_url,
                            json=result,
                            headers=headers,
                        )
                        if post_result.status == 200:
                            break
                        time.sleep(0.5)
                    else:
                        log.critical(
                            f"Error posting callback to: {self.callback_url} for run id {self._run_id}.\nRequest id: {self.request_id}.\nResult: {post_result}"
                        )
                except Exception:
                    log.exception(
                        f"Error posting callback to: {self.callback_url} for run id {self._run_id}.\nRequest id: {self.request_id}.\nResult: {post_result}"
                    )
        return result

    def _run_action_impl(self) -> Any:
        from concurrent.futures import CancelledError
        from typing import Literal

        from sema4ai.action_server._actions_process_pool import (
            ActionsProcessPool,
            ProcessHandle,
        )
        from sema4ai.action_server._runs_state_cache import get_global_runs_state

        action_package: "ActionPackage" = self.action_package
        action: "Action" = self.action
        output_validator: Callable[[dict], None] = self.output_validator
        inputs: dict = self.inputs
        headers: dict = self.headers
        cookies: dict = self.cookies

        from sema4ai.action_server._settings import get_settings

        from ._actions_process_pool import get_actions_process_pool
        from ._models import get_db

        settings = get_settings()

        global_runs_state = get_global_runs_state()
        runtime_info = global_runs_state.create_run_runtime_info(self._run_id)

        db = get_db()
        with db.connect():  # Connection is per-thread, so, we need to create a new one.
            actions_process_pool: ActionsProcessPool = get_actions_process_pool()
            process_handle: ProcessHandle
            relative_artifacts_path = self._relative_artifacts_path
            run = self._run

            try:
                # This can take some time to complete if multiple actions are
                # running in parallel (i.e.: the process pool may be full).
                initial_time = time.monotonic()  # Initial time
                process_handle_ctx = actions_process_pool.obtain_process_for_action(
                    action, runtime_info
                )
                with process_handle_ctx as process_handle:
                    initial_time = time.monotonic()
                    input_json = (
                        settings.artifacts_dir
                        / relative_artifacts_path
                        / "__action_server_inputs.json"
                    )
                    input_json.write_bytes(json.dumps(inputs).encode("utf-8"))

                    run_artifacts_dir = settings.artifacts_dir / relative_artifacts_path

                    result_json = (
                        settings.artifacts_dir
                        / relative_artifacts_path
                        / "__action_server_result.json"
                    )

                    output_file = (
                        settings.artifacts_dir
                        / relative_artifacts_path
                        / "__action_server_output.txt"
                    )

                    returncode: int | Literal["<unset>"] = "<unset>"
                    _set_run_as_running(run, initial_time)

                    def on_cancel(*args, **kwargs):
                        log.info(
                            f"Killing process related to run {run.id} due to cancel request (pid: {process_handle.pid})."
                        )
                        process_handle.kill()

                    with runtime_info.on_cancel.register(on_cancel):
                        if runtime_info.is_canceled():
                            # Cancelled before the run was actually started.
                            raise CancelledError("Run canceled")

                        reuse_process = settings.reuse_processes
                        returncode = process_handle.run_action(
                            run,
                            action_package,
                            action,
                            input_json,
                            run_artifacts_dir,
                            output_file,
                            result_json,
                            headers,
                            cookies,
                            reuse_process,
                        )

                    error_msg = None
                    try:
                        run_result_str: str = result_json.read_text("utf-8", "replace")
                    except Exception:
                        error_msg = (
                            "It was not possible to collect the contents of the "
                            "result (json not created)."
                        )
                    else:
                        try:
                            result_contents = json.loads(run_result_str)
                        except Exception:
                            error_msg = f"Error loading the contents of {run_result_str} as json."

                    if error_msg is not None:
                        if runtime_info.is_canceled():
                            # When cancelled, these errors are expected (so, throw error that it's cancelled
                            # instead of the error message).
                            raise CancelledError(
                                f"Run cancelled, action: {action.name}"
                            )

                        raise RuntimeError(error_msg)

                    ret = result_contents.get("result")
                    result_str: str = json.dumps(ret, indent=4)
                    if ret is not None or returncode == 0:
                        try:
                            output_validator(ret)
                        except Exception as e:
                            show_str = result_str
                            if ret is None:
                                show_str = "None"
                            raise RuntimeError(
                                f"Inconsistent value returned from action.\ni.e.: the returned value: {show_str}\ndoes not match the expected output schema.\n"
                                f"Original error: {e}"
                            )

                    if returncode == 0:
                        _set_run_as_finished_ok(run, result_str, initial_time)
                        return ret

                    else:
                        if runtime_info.is_canceled():
                            raise CancelledError(
                                f"Run cancelled, action: {action.name}"
                            )

                        if ret:
                            # We have a return even with a failure. This means it's
                            # something as a Response(error=error_msg)
                            (
                                _set_run_as_finished_failed_with_response(
                                    run, result_str, initial_time
                                )
                            )
                            return ret

                    raise RuntimeError(  # Error in action itself.
                        result_contents.get(
                            "message",
                            f"Action {action.name} failed with returncode={returncode}",
                        )
                    )

            except BaseException as e:
                try:
                    if runtime_info.is_canceled() or isinstance(e, CancelledError):
                        log.exception(
                            f"Action {action.name} cancelled (run_id={run.id})"
                        )
                        _set_run_as_finished_cancelled(run, str(e), initial_time)
                    else:
                        log.exception(f"Action {action.name} failed (run_id={run.id})")
                        _set_run_as_finished_failed(run, str(e), initial_time)
                except Exception:
                    log.exception(
                        f"INTERNAL ERROR (unexpected) IN ACTION SERVER! Error setting run {run.id} as finished."
                    )

                raise HTTPException(status_code=500, detail=str(e))


def _name_as_class_name(name):
    return name.replace("_", " ").title().replace(" ", "")


def generate_func_from_action(
    action_package: "ActionPackage", action: "Action", display_name: str
) -> Tuple[Callable[[Response, Request], Any], dict[str, object]]:
    """
    This method generates the function which should be called from FastAPI.

    Initially it generated the function with the parameters required to build
    the openapi.json spec properly, but it was changed to deal with the body
    directly and provide the openapi.json bits needed as it's easier and more
    straightforward to deal with the json directly and validate it than to
    create an in-memory python method with the proper signature so that FastAPI
    will do the validation.

    Returns:
        Function/Open API spec for the function
    """
    input_schema_dict = json.loads(action.input_schema)
    output_schema_dict = json.loads(action.output_schema)

    openapi_extra = {
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": input_schema_dict,
                }
            },
            "required": True,
        },
        "responses": {
            "200": {
                "content": {
                    "application/json": {
                        "schema": {
                            **output_schema_dict,
                            **{"title": f"Response for {display_name}"},
                        }
                    }
                },
                "description": "Successful Response",
            },
            "422": {
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/HTTPValidationError"}
                    }
                },
                "description": "Validation Error",
            },
        },
    }

    try:
        input_validator = _get_json_validator(input_schema_dict)
    except Exception:
        raise RuntimeError(
            f"Error making validator for input schema: {input_schema_dict}"
        )
    try:
        output_validator = _get_json_validator(output_schema_dict)
    except Exception:
        raise RuntimeError(
            f"Error making validator for output schema: {output_schema_dict}"
        )

    # The returned function must be async because we have to request the `body`

    async def func(response: Response, request: Request):
        body = await request.body()
        try:
            inputs = json.loads(body)
        except Exception as e:
            raise RequestValidationError(
                [
                    f"The received input arguments (sent in the body) cannot be interpreted as json. Details: {e}"
                ]
            )

        headers = dict((x[0].lower(), x[1]) for x in request.headers.items())
        cookies = dict(request.cookies)

        # i.e.: if the `x-action-invocation-context` header is present, we
        # expect it to contain a data envelope (`base64(encrypted_data(JSON.stringify(content)))` or
        # `base64(JSON.stringify(content))`) with the invocation context.
        #
        # This also changes how the body is processed (in this case, each new entry
        # in the body will internally map to a header, whereas the `body` in it will
        # become the actual input).
        #
        # This is done because headers have a size restriction and we don't want to
        # hit it (so, we enable passing things that are conceptually headers, such as
        # `x-action-context` and `x-data-context`, in the body of the request)
        invocation_context = request.headers.get("x-action-invocation-context")
        if invocation_context:  # Anything there means we expect the body to contain the additional contexts.
            if isinstance(inputs, dict):
                if "body" not in inputs:
                    raise RequestValidationError(
                        [
                            "The received input arguments (sent in the body) do not contain the `body` key (which is expected when the `x-action-invocation-context` header is present)."
                        ]
                    )
                use_inputs = inputs.pop("body")
                headers.update(inputs)
                inputs = use_inputs

        runner = _ActionsRunner(
            action_package,
            action,
            input_schema_dict,
            output_schema_dict,
            input_validator,
            output_validator,
            inputs,
            response,
            headers,
            cookies,
        )
        return await run_in_threadpool(runner.run_in_thread)

    return func, openapi_extra


def _iter_jsonschema_specifications():
    from pathlib import Path

    import jsonschema_specifications  # type: ignore
    from referencing import Resource

    parent = Path(jsonschema_specifications._core.__file__).absolute().parent

    for version in (parent / "schemas").iterdir():
        if version.name.startswith("."):
            continue
        for child in version.iterdir():
            children = [child] if child.is_file() else child.iterdir()
            for path in children:
                if path.name.startswith("."):
                    continue
                contents = json.loads(path.read_text(encoding="utf-8"))
                yield Resource.from_contents(contents)


def _fix_jsonschema_specifications():
    import jsonschema_specifications  # type: ignore
    from referencing.jsonschema import EMPTY_REGISTRY as _EMPTY_REGISTRY

    REGISTRY = (_iter_jsonschema_specifications() @ _EMPTY_REGISTRY).crawl()
    jsonschema_specifications.REGISTRY = REGISTRY


def _get_json_validator(schema: dict):
    # Dirty hack to make jsonschema_specifications work with pyoxidizer.
    # see: https://github.com/python-jsonschema/jsonschema-specifications/issues/61
    _fix_jsonschema_specifications()

    from jsonschema.validators import validator_for

    cls = validator_for(schema)
    cls.check_schema(schema)
    instance = cls(schema)
    return instance.validate
