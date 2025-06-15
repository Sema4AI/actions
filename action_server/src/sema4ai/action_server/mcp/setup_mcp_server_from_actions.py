import logging
import re
import typing
from dataclasses import dataclass
from typing import Any, Callable

from pydantic.networks import AnyUrl

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
        from typing import Iterable

        from mcp.server import Server
        from mcp.server.lowlevel.helper_types import ReadResourceContents
        from mcp.types import (
            EmbeddedResource,
            ImageContent,
            Resource,
            ResourceTemplate,
            TextContent,
            Tool,
        )

        server: Server = Server("Action Server")
        self.server = server
        self._tools: list[Tool] = []
        self._tool_name_to_action_info: dict[str, ActionInfo] = {}

        self._resource_templates: list[ResourceTemplate] = []
        self._resource_template_to_action_info: dict[str, ActionInfo] = {}

        self._resources: list[Resource] = []
        self._resource_to_action_info: dict[str, ActionInfo] = {}

        @server.list_tools()
        async def list_tools() -> list[Tool]:
            return self._tools

        @server.list_resources()
        async def list_resources() -> list[Resource]:
            return self._resources

        @server.call_tool()
        async def call_tool(
            name: str, arguments: dict[str, Any]
        ) -> list[TextContent | ImageContent | EmbeddedResource]:
            import json

            try:
                from sema4ai.action_server._actions_run import IInternalFuncAPI

                action_info = self._tool_name_to_action_info[name]
                func: IInternalFuncAPI = action_info.func
                result = await func(
                    response_handler=McpResponseHandler(),
                    inputs=arguments,
                    headers={},
                    cookies={},
                )
                if isinstance(result, str):
                    return [TextContent(type="text", text=result)]
                else:
                    return [TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                log.exception("Error calling tool %s", name)
                raise e

        @server.read_resource()
        async def read_resource(
            uri: AnyUrl,
        ) -> Iterable[ReadResourceContents]:
            pass

    def _resource_template_matches(
        self, uri_template: str, uri: str
    ) -> dict[str, Any] | None:
        """Check if URI matches template and extract parameters."""

        # Same logic as https://github.com/modelcontextprotocol/python-sdk/blob/v1.9.4/src/mcp/server/fastmcp/resources/templates.py#L54

        # Convert template to regex pattern
        pattern = uri_template.replace("{", "(?P<").replace("}", ">[^/]+)")
        match = re.match(f"^{pattern}$", uri)
        if match:
            return match.groupdict()
        return None

    def register_action(
        self,
        func: Callable,
        action_package: "ActionPackage",
        action: "Action",
        display_name: str,
        doc_desc: str,
    ) -> None:
        import inspect
        import json

        from mcp.types import Resource, ResourceTemplate, Tool
        from pydantic.networks import AnyUrl

        use_name = action.name

        options = json.loads(action.options)
        kind = options.get("kind")

        if kind == "resource":
            # Resource may be regular or template resources depending on the uri.
            # If the URI follows the RFC 6570 template syntax, it's a template resource.
            uri = options.get("uri")
            if not uri:
                raise ValueError(f"Resource {use_name} has no URI")

            has_uri_params = "{" in uri and "}" in uri
            signature = inspect.signature(func)
            params = signature.parameters
            has_func_params = bool(params)

            if has_uri_params or has_func_params:
                uri_params: set[str] = set(re.findall(r"{(\w+)}", uri))

                self._resource_templates.append(
                    ResourceTemplate(
                        uriTemplate=uri, name=use_name, description=doc_desc
                    )
                )
                self._resource_template_to_action_info[uri] = ActionInfo(
                    func=func,
                    action=action,
                    display_name=display_name,
                    doc_desc=doc_desc,
                )
            else:
                self._resources.append(
                    Resource(
                        uri=AnyUrl(uri),
                        name=use_name,
                        description=doc_desc,
                        mimeType=options.get("mime_type"),
                        size=options.get("size"),
                    )
                )

        elif kind == "prompt":
            pass

        else:
            self._tools.append(
                Tool(
                    name=use_name,
                    description=doc_desc,
                    inputSchema=json.loads(action.input_schema),
                )
            )

            self._tool_name_to_action_info[use_name] = ActionInfo(
                func=func, action=action, display_name=display_name, doc_desc=doc_desc
            )

    def unregister_actions(self):
        self._tools = []
        self._tool_name_to_action_info = {}
        self._resources = []
