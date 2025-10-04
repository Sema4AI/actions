import logging
import re
import typing
from dataclasses import dataclass
from typing import Any, Callable

from mcp.types import (
    EmbeddedResource,
    GetPromptResult,
    ImageContent,
    Prompt,
    PromptArgument,
    PromptMessage,
    Resource,
    ResourceTemplate,
    TextContent,
    Tool,
)
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
    _tools: list[Tool]
    _tool_name_to_action_info: dict[str, ActionInfo]
    _resources: dict[AnyUrl, Resource]
    _resource_to_action_info: dict[str, ActionInfo]
    _resource_templates: list[ResourceTemplate]
    _resource_template_to_action_info: dict[str, ActionInfo]
    _prompts: list[Prompt]
    _prompt_name_to_action_info: dict[str, ActionInfo]

    def __init__(self) -> None:
        from mcp.server import Server
        from mcp.server.lowlevel.helper_types import ReadResourceContents

        server: Server = Server("Action Server")
        self.server = server
        self._init_state()

        def get_headers_and_cookies() -> tuple[dict[str, str], dict[str, str]]:
            headers: dict[str, str] = {}
            cookies: dict[str, str] = {}
            try:
                request_context = self.server.request_context
            except LookupError:
                return headers, cookies
            if request_context:
                request = request_context.request
                if request:
                    headers = dict(request.headers)
                    cookies = dict(request.cookies)
            return headers, cookies

        @server.list_tools()
        async def list_tools() -> list[Tool]:
            return self._tools

        @server.list_resources()
        async def list_resources() -> list[Resource]:
            return list(self._resources.values())

        @server.list_resource_templates()
        async def list_resource_templates() -> list[ResourceTemplate]:
            return self._resource_templates

        @server.call_tool()
        async def call_tool(
            name: str,
            arguments: dict[str, Any],
        ) -> list[TextContent | ImageContent | EmbeddedResource]:
            import json

            try:
                from sema4ai.action_server._actions_run import IInternalFuncAPI

                headers, cookies = get_headers_and_cookies()
                action_info = self._tool_name_to_action_info[name]
                func: IInternalFuncAPI = action_info.func
                result = await func(
                    response_handler=McpResponseHandler(),
                    inputs=arguments,
                    headers=headers,
                    cookies=cookies,
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
        ):
            from typing import Iterable

            try:
                params: dict[str, Any] = {}

                # First check if it matches any resource templates
                # If no template match, check if it's a direct resource
                action_info = self._resource_to_action_info.get(str(uri))
                if action_info:
                    resource = self._resources.get(uri)
                    default_mime_type = resource.mimeType if resource else None
                else:
                    for template in self._resource_templates:
                        found_params = self._resource_template_matches(
                            template.uriTemplate, str(uri)
                        )
                        if found_params:
                            default_mime_type = template.mimeType
                            params = found_params
                            action_info = self._resource_template_to_action_info[
                                template.uriTemplate
                            ]
                            break

                if action_info:
                    headers, cookies = get_headers_and_cookies()
                    func = action_info.func
                    result = await func(
                        response_handler=McpResponseHandler(),
                        inputs=params,
                        headers=headers,
                        cookies=cookies,
                    )

                    def gen() -> Iterable[ReadResourceContents]:
                        try:
                            mime_type = default_mime_type
                            if isinstance(result, (str, bytes)):
                                if not mime_type:
                                    if isinstance(result, str):
                                        mime_type = "text/plain"
                                    else:
                                        mime_type = "application/octet-stream"

                                yield ReadResourceContents(
                                    content=result, mime_type=mime_type
                                )
                            else:
                                import json

                                yield ReadResourceContents(
                                    content=json.dumps(result, indent=2),
                                    mime_type=mime_type or "application/json",
                                )
                                return
                        except Exception as e:
                            log.exception("Error converting resource %s to stream", uri)
                            raise e

                    return gen()

                # If we get here, no matching resource was found
                raise ValueError(f"No resource found for URI: {uri}")
            except Exception as e:
                log.exception("Error reading resource %s", uri)
                raise e

        @server.get_prompt()
        async def get_prompt(
            name: str,
            arguments: dict[str, Any] | None = None,
        ) -> GetPromptResult:
            try:
                action_info = self._prompt_name_to_action_info[name]
                func = action_info.func

                headers, cookies = get_headers_and_cookies()

                result = await func(
                    response_handler=McpResponseHandler(),
                    inputs=arguments or {},
                    headers=headers,
                    cookies=cookies,
                )
                # TODO: We could have a way for the user to customize more things in the prompt result,
                # right now it's just the direct result of the prompt as a string, but it could be:
                # TextContent | ImageContent | EmbeddedResource
                # and the user could also provide the description and an actual list of messages.
                # -- it's not really clear from the spec how that'd be used though.
                return GetPromptResult(
                    description=action_info.doc_desc,
                    messages=[
                        PromptMessage(
                            role="user", content=TextContent(type="text", text=result)
                        )
                    ],
                )
            except Exception as e:
                log.exception("Error getting prompt %s", name)
                raise e

        @server.list_prompts()
        async def list_prompts() -> list[Prompt]:
            return self._prompts

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
        import json

        from mcp.types import ToolAnnotations

        if not action.options:
            options = {}
        else:
            try:
                options = json.loads(action.options)
            except Exception:
                log.exception(
                    f"Error parsing options for action {action.name}: {action.options}"
                )
                raise

        kind = options.get("kind", "action")

        if kind == "resource":
            # Resource may be regular or template resources depending on the uri.
            # If the URI follows the RFC 6570 template syntax, it's a template resource.
            uri = options.get("uri")
            if not uri:
                raise ValueError(f"Resource {action.name} has no URI")

            has_uri_params = "{" in uri and "}" in uri

            if has_uri_params:
                self._resource_templates.append(
                    ResourceTemplate(
                        uriTemplate=uri,
                        name=action.name,
                        description=doc_desc,
                        mimeType=options.get("mime_type"),
                    )
                )
                self._resource_template_to_action_info[uri] = ActionInfo(
                    func=func,
                    action=action,
                    display_name=display_name,
                    doc_desc=doc_desc,
                )
            else:
                url = AnyUrl(uri)
                self._resources[url] = Resource(
                    uri=url,
                    name=action.name,
                    description=doc_desc,
                    mimeType=options.get("mime_type"),
                    size=options.get("size"),
                )

                self._resource_to_action_info[uri] = ActionInfo(
                    func=func,
                    action=action,
                    display_name=display_name,
                    doc_desc=doc_desc,
                )

        elif kind == "prompt":
            schema = json.loads(action.input_schema)
            arguments = schema.get("properties", {})
            required = schema.get("required", [])

            prompt_arguments = []
            for name, prop in arguments.items():
                prompt_arguments.append(
                    PromptArgument(
                        name=name,
                        description=prop.get("description", ""),
                        required=name in required,
                    )
                )
            self._prompts.append(
                Prompt(
                    name=action.name,
                    description=doc_desc,
                    arguments=prompt_arguments,
                )
            )
            self._prompt_name_to_action_info[action.name] = ActionInfo(
                func=func,
                action=action,
                display_name=display_name,
                doc_desc=doc_desc,
            )

        else:
            # action, tool, query end up here!
            title = options.get("title")
            if not title:
                title = display_name

            self._tools.append(
                Tool(
                    name=action.name,
                    description=doc_desc,
                    inputSchema=json.loads(action.input_schema),
                    annotations=ToolAnnotations(
                        title=title,
                        readOnlyHint=options.get("read_only_hint", False),
                        destructiveHint=options.get("destructive_hint", True),
                        idempotentHint=options.get("idempotent_hint", False),
                        openWorldHint=options.get("open_world_hint", True),
                    ),
                )
            )

            self._tool_name_to_action_info[action.name] = ActionInfo(
                func=func, action=action, display_name=display_name, doc_desc=doc_desc
            )

    def unregister_actions(self):
        self._init_state()

    def _init_state(self):
        self._tools = []
        self._tool_name_to_action_info = {}

        self._resources = {}
        self._resource_to_action_info = {}

        self._resource_templates = []
        self._resource_template_to_action_info = {}

        self._prompts = []
        self._prompt_name_to_action_info = {}
