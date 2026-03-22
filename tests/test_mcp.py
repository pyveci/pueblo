# MCP Alchemy Model Context Protocol Server for CrateDB
# https://github.com/runekaagaard/mcp-alchemy
#
# Derived from:
# https://github.com/modelcontextprotocol/python-sdk?tab=readme-ov-file#writing-mcp-clients

import pytest

pytest.importorskip("mcp")
pytest.importorskip("psycopg2")

import asyncio

import psycopg2
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from pueblo.mcp.client import McpConversation

pytestmark = pytest.mark.mcp

DB_URL = "postgresql://postgres@localhost:5432/postgres"


async def run():

    # Provision database content.
    try:
        conn = psycopg2.connect(DB_URL)
    except psycopg2.OperationalError as ex:
        if "Connection refused" in str(ex):
            raise pytest.skip(  # ty: ignore[invalid-argument-type]
                "Skipping MCP conversation with PostgreSQL, no server running on localhost"  # ty: ignore[too-many-positional-arguments]
            ) from ex
        raise

    with conn:
        with conn.cursor() as cursor:
            cursor.execute("CREATE TABLE IF NOT EXISTS mcp_alchemy (id INT, data TEXT)")
            cursor.execute("DELETE FROM mcp_alchemy")
            cursor.execute("INSERT INTO mcp_alchemy (id, data) VALUES (42, 'Hotzenplotz')")

    # Create server parameters for stdio connection.
    server_params = StdioServerParameters(
        command="uvx",
        args=["--with", "psycopg2-binary", "mcp-alchemy"],
        env={"DB_URL": DB_URL},
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection.
            await session.initialize()

            client = McpConversation(session)
            await client.inquire()

            print("## MCP server conversations")  # noqa: T201
            print()  # noqa: T201

            # Call a few tools.
            await client.call_tool("execute_query", arguments={"query": 'SELECT * FROM "mcp_alchemy";'})
            await client.call_tool("all_table_names", arguments={})
            await client.call_tool("filter_table_names", arguments={"q": "mcp"})
            await client.call_tool("schema_definitions", arguments={"table_names": ["mcp_alchemy"]})


def test_mcp(capsys):
    """
    Verify a typical conversation with an MCP server.
    """
    asyncio.run(asyncio.wait_for(run(), timeout=120))

    out, _ = capsys.readouterr()

    assert "# MCP server inquiry" in out
    assert "## Resources" in out
    assert "## Resource templates" in out
    assert "## Tools" in out
    assert "name: all_table_names" in out
    assert "name: filter_table_names" in out
    assert "name: schema_definitions" in out
    assert "name: execute_query" in out

    assert "## MCP server conversations" in out

    assert "Calling tool: execute_query with arguments" in out
    assert "id: 42" in out
    assert "data: Hotzenplotz" in out

    assert "Calling tool: all_table_names with arguments" in out
    assert "text: mcp_alchemy" in out

    assert "Calling tool: filter_table_names with arguments" in out
    assert "text: mcp_alchemy" in out

    assert "Calling tool: schema_definitions with arguments" in out
    assert "id: INTEGER, nullable" in out
    assert "data: TEXT, nullable" in out
