import datetime
import json
import logging
import time
import typing
from functools import partial
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
    action: "Action", run_id: str, inputs: dict, relative_artifacts_dir: str
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
    )
    with db.transaction():
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
    with db.transaction():
        db.update(run, *fields_changed)

    # Ok, transaction finished properly. Let's update our in-memory cache.
    global_runs_state = get_global_runs_state()
    global_runs_state.on_run_changed(run, changes)


def _set_run_as_finished_ok(run: "Run", result: str, initial_time: float):
    from ._models import RunStatus

    _update_run(run, initial_time, True, result=result, status=RunStatus.PASSED)


def _set_run_as_finished_failed_with_response(
    run: "Run", result: str, initial_time: float
):
    from ._models import RunStatus

    _update_run(run, initial_time, True, status=RunStatus.FAILED, result=result)


def _set_run_as_finished_failed(run: "Run", error_message: str, initial_time: float):
    from ._models import RunStatus

    _update_run(
        run, initial_time, True, status=RunStatus.FAILED, error_message=error_message
    )


def _set_run_as_running(run: "Run", initial_time: float):
    from ._models import RunStatus

    _update_run(run, initial_time, False, status=RunStatus.RUNNING)


def _run_action_in_thread(
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
):
    """
    This is where the user actually runs something.

    This runs in a thread (so, be careful when talking to the database).

    We have to take care of making a run with the proper environment,
    creating the run, collecting output info, etc.
    """
    from sema4ai.action_server._gen_ids import gen_uuid
    from sema4ai.action_server._settings import get_settings

    from ._actions_process_pool import get_actions_process_pool
    from ._models import Run, get_db

    settings = get_settings()

    try:
        input_validator(inputs)
    except Exception as e:
        raise RequestValidationError(
            [
                f"The received input arguments (sent in the body) do not conform to the expected API. Details: {e}"
            ]
        )

    timeout = headers.get("x-actions-async-timeout", 0)
    callback_url = headers.get("x-actions-async-callback", None)

    db = get_db()
    with db.connect():  # Connection is per-thread, so, we need to create a new one.
        actions_process_pool = get_actions_process_pool()

        with actions_process_pool.obtain_process_for_action(action) as process_handle:
            run_id = gen_uuid("run")
            response.headers["X-Action-Server-Run-Id"] = run_id
            relative_artifacts_path: str = _create_run_artifacts_dir(action, run_id)
            run: Run = _create_run(action, run_id, inputs, relative_artifacts_path)

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

            initial_time = time.monotonic()
            returncode = "<unset>"
            try:
                _set_run_as_running(run, initial_time)
                reuse_process = settings.reuse_processes
                generator = process_handle.run_action(
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

                queue = next(generator)
                result_msg = queue.get(block=True)
                try:
                    generator.send(result_msg)
                except StopIteration as e:
                    returncode = e.value

                try:
                    run_result_str: str = result_json.read_text("utf-8", "replace")
                except Exception:
                    raise RuntimeError(
                        "It was not possible to collect the contents of the "
                        "result (json not created)."
                    )

                try:
                    result_contents = json.loads(run_result_str)
                except Exception:
                    raise RuntimeError(
                        f"Error loading the contents of {run_result_str} as json."
                    )

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
                    if ret:
                        # We have a return even with a failure. This means it's
                        # something as a Response(error=error_msg)
                        _set_run_as_finished_failed_with_response(
                            run, result_str, initial_time
                        )
                        return ret

                raise RuntimeError(
                    result_contents.get(
                        "message",
                        f"Internal error running action (action={action.name}, returncode={returncode})",
                    )
                )

            except BaseException as e:
                log.exception(f"Internal error running action (action={action.name})")
                _set_run_as_finished_failed(run, str(e), initial_time)
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

        return await run_in_threadpool(
            partial(
                _run_action_in_thread,
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
        )

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
