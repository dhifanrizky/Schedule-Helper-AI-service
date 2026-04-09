# mcp_client.py
import asyncio

from fastmcp import Client


async def main():
    async with Client("http://localhost:8000/mcp") as client:
        result = await client.call_tool(
            "query_database", {"query": "SELECT * FROM users"}
        )
        print(result)


asyncio.run(main())
