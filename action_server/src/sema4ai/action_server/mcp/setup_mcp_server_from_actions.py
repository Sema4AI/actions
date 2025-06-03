import logging
import typing
from dataclasses import dataclass
from typing import Any, Callable

if typing.TYPE_CHECKING:
    from sema4ai.action_server._models import Action, ActionPackage

log = logging.getLogger(__name__)


@dataclass
class ActionInfo:
    func: Callable
    action: "Action"
    display_name: str
    doc_desc: str


class McpResponseHandler:
    def __init__(self):
        pass

    def set_run_id(self, run_id: str):
        pass

    def set_async_completion(self):
        pass


class McpServerSetupHelper:
    def __init__(self) -> None:
        from mcp.server import Server
        from mcp.types import EmbeddedResource, ImageContent, TextContent, Tool

        server: Server = Server("Action Server")
        self.server = server
        self._tools: list[Tool] = []
        self._action_name_to_action_info: dict[str, ActionInfo] = {}

        @server.list_tools()
        async def list_tools() -> list[Tool]:
            return self._tools

        @server.call_tool()
        async def call_tool(
            name: str, arguments: dict[str, Any]
        ) -> list[TextContent | ImageContent | EmbeddedResource]:
            try:
                from sema4ai.action_server._actions_run import IInternalFuncAPI

                action_info = self._action_name_to_action_info[name]
                func: IInternalFuncAPI = action_info.func
                result = await func(
                    response_handler=McpResponseHandler(),
                    inputs=arguments,
                    headers={},
                    cookies={},
                )
                return [TextContent(type="text", text=result)]
            except Exception as e:
                log.exception("Error calling tool %s", name)
                raise e

    def register_action(
        self,
        func: Callable,
        action_package: "ActionPackage",
        action: "Action",
        display_name: str,
        doc_desc: str,
    ):
        import json

        from mcp.types import Tool

        use_name = f"{action_package.name}/{action.name}"

        self._tools.append(
            Tool(
                name=use_name,
                description=doc_desc,
                inputSchema=json.loads(action.input_schema),
            )
        )
        self._action_name_to_action_info[use_name] = ActionInfo(
            func=func, action=action, display_name=display_name, doc_desc=doc_desc
        )
