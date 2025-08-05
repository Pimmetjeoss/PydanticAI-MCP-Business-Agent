#!/usr/bin/env python3
"""Test script using the official MCP Python SDK"""

import asyncio
import logging
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_mcp_sdk():
    """Test MCP SDK with our server"""
    try:
        # Try to connect to the SSE endpoint
        server_url = "http://localhost:8792/sse"
        
        logger.info(f"Connecting to MCP server at {server_url}")
        
        # Use SSE client to connect to our Cloudflare Workers MCP server
        async with sse_client(server_url) as session:
            logger.info("✅ Connected to MCP server!")
            
            # List available tools
            result = await session.list_tools()
            logger.info(f"Available tools: {[tool.name for tool in result.tools]}")
            
            # Try to call a tool
            if result.tools:
                tool_name = "crawlWebsite"  # Try our crawlWebsite tool
                logger.info(f"Calling tool: {tool_name}")
                
                response = await session.call_tool(
                    tool_name,
                    {
                        "url": "https://www.contiweb.com",
                        "limit": 1
                    }
                )
                
                logger.info(f"Tool response: {response}")
            else:
                logger.warning("No tools available")
                
    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp_sdk())