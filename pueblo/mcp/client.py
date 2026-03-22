# ruff: noqa: T201
import io
import json
import logging
import typing as t

import mcp.types as types
import pydantic_core
import yaml
from mcp import ClientSession, McpError
from pydantic import AnyUrl

logger = logging.getLogger(__name__)


class McpConversation:
    """
    Wrap conversation to MCP server.
    """

    def __init__(self, session: ClientSession):
        self.session = session

    @staticmethod
    def decode_json_text(thing):
        if not thing.content:
            return None
        return json.loads(thing.content[0].text)

    def decode_items(self, items):
        return list(map(self.decode_item, json.loads(pydantic_core.to_json(items))))

    @staticmethod
    def decode_item(item):
        try:
            item["text"] = json.loads(item["text"])
        except (KeyError, TypeError, json.JSONDecodeError):
            logger.warning("Unable to decode text from JSON or missing 'text' key: %s", item)
        return item

    def list_items(self, items):
        buffer = io.StringIO()
        if items:
            data = self.decode_items(items)
            buffer.write("```yaml\n")
            buffer.write(yaml.dump(data, sort_keys=False, width=100))
            buffer.write("```\n")
        return buffer.getvalue()

    async def entity_info(self, fun, attribute):
        try:
            return self.list_items(getattr(await fun(), attribute))
        except McpError as e:
            logger.error("Not implemented on this server: %s", e)
        return ""

    @staticmethod
    def dump_info(results):
        if results:
            print(results)
        print()

    async def inquire(self):
        print("# MCP server inquiry")
        print()

        # List available prompts
        print("## Prompts")
        self.dump_info(await self.entity_info(self.session.list_prompts, "prompts"))

        # List available resources and resource templates
        print("## Resources")
        self.dump_info(await self.entity_info(self.session.list_resources, "resources"))

        print("## Resource templates")
        self.dump_info(await self.entity_info(self.session.list_resource_templates, "resourceTemplates"))

        # List available tools
        print("## Tools")
        self.dump_info(await self.entity_info(self.session.list_tools, "tools"))

    async def call_tool(self, name: str, arguments: t.Union[t.Dict[str, t.Any], None] = None) -> types.CallToolResult:
        print(f"Calling tool: {name} with arguments: {arguments}")
        result = await self.session.call_tool(name, arguments)
        print(self.list_items(result.content))
        print()
        return result

    async def get_prompt(self, name: str, arguments: t.Union[t.Dict[str, str], None] = None) -> types.GetPromptResult:
        print(f"Getting prompt: {name} with arguments: {arguments}")
        result = await self.session.get_prompt(name, arguments)
        print(self.list_items(result.messages))
        print()
        return result

    async def read_resource(self, uri: AnyUrl) -> types.ReadResourceResult:
        print(f"Reading resource: {uri}")
        result = await self.session.read_resource(uri)
        print(self.list_items(result.contents))
        print()
        return result
