#!/usr/bin/env python3
"""Test MCP SSE transport with authentication"""

import asyncio
import logging
import httpx
from mcp.client.sse import sse_client
from mcp_business_agent.oauth_manager import oauth_manager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_mcp_sse_with_auth():
    """Test MCP SSE transport with OAuth authentication"""
    try:
        # Get OAuth session cookies and access token
        logger.info("Getting OAuth authentication...")
        cookies = await oauth_manager.get_valid_session_cookies()
        
        if not cookies:
            logger.error("Failed to get OAuth session cookies")
            return
        
        access_token = cookies.get('mcp_access_token')
        if not access_token:
            logger.error("No access token found in cookies")
            return
        
        logger.info("✅ Got OAuth credentials")
        
        # Create HTTPX Auth handler for Bearer token
        class BearerAuth(httpx.Auth):
            def __init__(self, token: str):
                self.token = token
            
            def auth_flow(self, request):
                request.headers["Authorization"] = f"Bearer {self.token}"
                request.headers["User-Agent"] = "MCP-Business-Agent/1.0"
                yield request
        
        auth_handler = BearerAuth(access_token)
        server_url = "http://localhost:8792/sse"
        logger.info(f"Connecting to MCP server at {server_url}")
        
        # Use SSE client with proper authentication
        async with sse_client(server_url, auth=auth_handler) as (read, write):
            logger.info("✅ Connected to MCP server via SSE!")
            logger.info(f"SSE client returned: {type((read, write))}")
            
            # Create a client session from the SSE transport
            from mcp import ClientSession
            
            async with ClientSession(read, write) as session:
                logger.info("✅ MCP Client Session created!")
                
                # Initialize the session
                await session.initialize()
                logger.info("✅ MCP Session initialized!")
                
                # List available tools
                try:
                    result = await session.list_tools()
                    logger.info(f"Available tools: {[tool.name for tool in result.tools]}")
                    
                    # Try to call crawlWebsite tool
                    if any(tool.name == "crawlWebsite" for tool in result.tools):
                        logger.info("Calling crawlWebsite tool...")
                        
                        response = await session.call_tool(
                            "crawlWebsite",
                            {
                                "url": "https://www.contiweb.com",
                                "limit": 1
                            }
                        )
                        
                        logger.info("✅ Tool call successful!")
                        logger.info(f"Response: {response}")
                        
                    else:
                        logger.warning("crawlWebsite tool not found")
                        
                except Exception as e:
                    logger.error(f"Error during tool operations: {e}")
                    import traceback
                    traceback.print_exc()
                
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_sse_with_auth())