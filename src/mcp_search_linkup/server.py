import asyncio
from linkup import LinkupClient
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
from pydantic import AnyUrl
import logging

import os
# Initialize the LinkupClient

server = Server("mcp-search-linkup")
logger = logging.getLogger("mcp-search-linkup")
logger.setLevel(logging.INFO)

## Logging
@server.set_logging_level()
async def set_logging_level(level: types.LoggingLevel) -> types.EmptyResult:
    logger.setLevel(level.upper())
    await server.request_context.session.send_log_message(
        level="info",
        data=f"Log level set to {level}",
        logger="mcp-search-linkup"
    )
    return types.EmptyResult()

## Resources
@server.list_resources()
async def list_resources() -> list[types.Resource]:
    return [
        types.Resource(
            uri=AnyUrl("https://www.thebridgechronicle.com/media"),
            name="The Bridge Chronicle",
            mimeType="text/html"
        )
    ]

@server.read_resource()
async def read_resource(uri: AnyUrl) -> str:
    if str(uri) == "https://www.thebridgechronicle.com/media":
        page = client.content(url="https://www.thebridgechronicle.com/news/capgemini-employees-walk-together-in-celebration-of-indias-independence")
        return page.content


    raise ValueError("Resource not found")

## Tools
@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available search tools.
    """
    return [
        types.Tool(
            name="search-web",
            description="Perform a web search query using Linkup. This tool is helpful for finding information on the web.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query to search the web with. This should be a question, no need to write in keywords."
                    },
                    "depth": {
                        "type": "string",
                        "enum": ["standard", "deep"],
                        "default": "standard",
                        "description": "The depth of the search. Standard is a basic search while deep takes more time to complete but can answer more complex questions."
                    },
                    "output_type": {
                        "type": "string",
                        "enum": ["searchResults", "sourcedAnswer", "structured"],
                        "default": "searchResults",
                        "description": "The type of output to return"
                    }
                },
                "required": ["query"],
            },
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle search tool execution requests.
    """
    if name != "search-web":
        raise ValueError(f"Unknown tool: {name}")

    if not arguments:
        raise ValueError("Missing arguments")

    query = arguments.get("query")
    depth = arguments.get("depth", "standard")
    output_type = arguments.get("output_type", "searchResults")

    if not query:
        raise ValueError("Missing query")

    client = LinkupClient()
    # Perform the search using LinkupClient
    search_response = client.search(
        query=query,
        depth=depth,
        output_type=output_type,
    )

    return [
        types.TextContent(
            type="text",
            text=str(search_response),
        )
    ]

async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp-search-linkup",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())